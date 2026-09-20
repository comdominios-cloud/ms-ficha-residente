"""Endpoints de la ficha consolidada.

Este microservicio no tiene base de datos: su unico trabajo es preguntarle a
ms-residentes, ms-pagos y ms-incidencias, y juntar las respuestas en un solo
JSON.

Las llamadas salen **en paralelo** con `asyncio.gather`. Si se hicieran una
detras de otra, la ficha tardaria la suma de las tres; asi tarda lo que tarde
la mas lenta.
"""

import asyncio

from fastapi import APIRouter, HTTPException, Path, status

from app.clients import crear_cliente, incidencias, pagos, residentes
from app.clients.base import Respuesta
from app.schemas import Bloque, FichaResidente, FichaUnidad, ResumenResidente

router = APIRouter(tags=["ficha"])


def _unidad_de(residente: dict | None) -> int | None:
    if not isinstance(residente, dict):
        return None
    return residente.get("unidad_id")


def _contar(respuesta: Respuesta, **filtros) -> int | None:
    """Cuenta elementos de una lista, opcionalmente filtrando por campo."""
    if not respuesta.ok or not isinstance(respuesta.datos, list):
        return None
    if not filtros:
        return len(respuesta.datos)
    return sum(
        1
        for x in respuesta.datos
        if isinstance(x, dict) and all(x.get(k) in v for k, v in filtros.items())
    )


@router.get(
    "/ficha/{residente_id}",
    response_model=FichaResidente,
    summary="Ficha consolidada de un residente",
)
async def ficha_residente(
    residente_id: int = Path(gt=0, description="Id del residente en ms-residentes"),
) -> FichaResidente:
    async with crear_cliente() as cliente:
        # Primero hay que saber en que unidad vive: todo lo demas se consulta
        # por unidad.
        r_residente = await residentes.obtener_residente(cliente, residente_id)

        if not r_residente.ok and "no encontrado" in (r_residente.error or ""):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe el residente {residente_id}",
            )

        unidad_id = _unidad_de(r_residente.datos)

        if unidad_id is None:
            # Sin unidad no se puede consultar lo demas, pero devolvemos lo que hay.
            vacio = Bloque(
                disponible=False,
                error="no se pudo determinar la unidad del residente",
            )
            return FichaResidente(
                residente_id=residente_id,
                unidad_id=None,
                completa=False,
                residente=Bloque.desde(r_residente),
                estado_cuenta=vacio,
                cuotas=vacio,
                pagos=vacio,
                incidencias=vacio,
                reservas=vacio,
            )

        # Las cinco consultas restantes salen a la vez.
        r_estado, r_cuotas, r_pagos, r_incid, r_reservas = await asyncio.gather(
            pagos.estado_cuenta(cliente, unidad_id),
            pagos.listar_cuotas(cliente, unidad_id),
            pagos.listar_pagos(cliente, unidad_id),
            incidencias.listar_incidencias(cliente, unidad_id),
            incidencias.listar_reservas(cliente, unidad_id),
        )

    bloques = {
        "residente": Bloque.desde(r_residente),
        "estado_cuenta": Bloque.desde(r_estado),
        "cuotas": Bloque.desde(r_cuotas),
        "pagos": Bloque.desde(r_pagos),
        "incidencias": Bloque.desde(r_incid),
        "reservas": Bloque.desde(r_reservas),
    }

    return FichaResidente(
        residente_id=residente_id,
        unidad_id=unidad_id,
        completa=all(b.disponible for b in bloques.values()),
        **bloques,
    )


@router.get(
    "/ficha/unidad/{unidad_id}",
    response_model=FichaUnidad,
    summary="Ficha consolidada de una unidad y todos sus residentes",
)
async def ficha_unidad(
    unidad_id: int = Path(gt=0, description="Id de la unidad en ms-residentes"),
) -> FichaUnidad:
    async with crear_cliente() as cliente:
        r_unidad, r_residentes, r_estado, r_incid, r_reservas = await asyncio.gather(
            residentes.obtener_unidad(cliente, unidad_id),
            residentes.listar_residentes_de_unidad(cliente, unidad_id),
            pagos.estado_cuenta(cliente, unidad_id),
            incidencias.listar_incidencias(cliente, unidad_id),
            incidencias.listar_reservas(cliente, unidad_id),
        )

    if not r_unidad.ok and "no encontrado" in (r_unidad.error or ""):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe la unidad {unidad_id}",
        )

    bloques = {
        "unidad": Bloque.desde(r_unidad),
        "residentes": Bloque.desde(r_residentes),
        "estado_cuenta": Bloque.desde(r_estado),
        "incidencias": Bloque.desde(r_incid),
        "reservas": Bloque.desde(r_reservas),
    }

    return FichaUnidad(
        unidad_id=unidad_id,
        completa=all(b.disponible for b in bloques.values()),
        **bloques,
    )


@router.get(
    "/ficha/{residente_id}/resumen",
    response_model=ResumenResidente,
    summary="Version reducida de la ficha, para tarjetas del frontend",
)
async def resumen_residente(
    residente_id: int = Path(gt=0),
) -> ResumenResidente:
    async with crear_cliente() as cliente:
        r_residente = await residentes.obtener_residente(cliente, residente_id)

        if not r_residente.ok and "no encontrado" in (r_residente.error or ""):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe el residente {residente_id}",
            )

        unidad_id = _unidad_de(r_residente.datos)
        r_estado = r_incid = r_reservas = Respuesta(error="sin unidad asociada")
        r_unidad = Respuesta(error="sin unidad asociada")

        if unidad_id is not None:
            # La unidad se pide aparte porque `GET /residentes/{id}` la trae sin
            # el edificio anidado, y el resumen lo necesita.
            r_unidad, r_estado, r_incid, r_reservas = await asyncio.gather(
                residentes.obtener_unidad(cliente, unidad_id),
                pagos.estado_cuenta(cliente, unidad_id),
                incidencias.listar_incidencias(cliente, unidad_id),
                incidencias.listar_reservas(cliente, unidad_id),
            )

    datos = r_residente.datos if isinstance(r_residente.datos, dict) else {}
    unidad = datos.get("unidad") or {}
    if r_unidad.ok and isinstance(r_unidad.datos, dict):
        unidad = r_unidad.datos
    edificio = unidad.get("edificio") or {}

    nombre = None
    if datos.get("nombres"):
        nombre = f"{datos.get('nombres', '')} {datos.get('apellidos', '')}".strip()

    deuda = None
    pendientes = None
    if r_estado.ok and isinstance(r_estado.datos, dict):
        for clave in ("deuda_total", "total_deuda", "saldo", "total"):
            if clave in r_estado.datos:
                try:
                    deuda = float(r_estado.datos[clave])
                except (TypeError, ValueError):
                    pass
                break
        for clave in ("cuotas_pendientes", "pendientes", "cantidad_pendientes"):
            if clave in r_estado.datos:
                try:
                    pendientes = int(r_estado.datos[clave])
                except (TypeError, ValueError):
                    pass
                break

    advertencias = [
        r.error
        for r in (r_residente, r_estado, r_incid, r_reservas)
        if not r.ok and r.error
    ]

    return ResumenResidente(
        residente_id=residente_id,
        nombre=nombre,
        unidad=unidad.get("codigo"),
        edificio=edificio.get("nombre"),
        deuda_total=deuda,
        cuotas_pendientes=pendientes,
        incidencias_abiertas=_contar(
            r_incid, estado=("ABIERTA", "EN_PROCESO", "abierta", "en_proceso")
        ),
        reservas_proximas=_contar(
            r_reservas, estado=("SOLICITADA", "CONFIRMADA", "solicitada", "confirmada")
        ),
        completa=not advertencias,
        advertencias=advertencias,
    )
