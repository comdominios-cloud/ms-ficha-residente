"""Health check y estado de las dependencias."""

import asyncio

from fastapi import APIRouter

from app.clients import crear_cliente
from app.clients.base import pedir
from app.config import get_settings
from app.schemas import EstadoDependencia, EstadoDependencias

router = APIRouter(tags=["salud"])
settings = get_settings()

# Ruta de cada servicio que sirve para saber si esta vivo. Se usa una ruta real
# porque el balanceador solo enruta las que tienen regla: /health no la tiene.
SONDAS = {
    "ms-residentes": "/edificios",
    "ms-pagos": "/cuotas",
    "ms-incidencias": "/incidencias",
}


@router.get("/health", summary="Health check del servicio")
def health() -> dict:
    """Este microservicio no tiene base de datos, asi que responder ya alcanza."""
    return {"status": "ok", "service": settings.app_name}


@router.get(
    "/dependencias/estado",
    response_model=EstadoDependencias,
    summary="Estado de los tres microservicios que consume",
)
async def estado_dependencias() -> EstadoDependencias:
    async with crear_cliente() as cliente:
        resultados = await asyncio.gather(
            *[
                pedir(cliente, nombre, f"{settings.dependencias[nombre]}{ruta}")
                for nombre, ruta in SONDAS.items()
            ]
        )

    dependencias = [
        EstadoDependencia(
            servicio=nombre,
            url=settings.dependencias[nombre],
            disponible=r.ok,
            detalle=r.error,
        )
        for nombre, r in zip(SONDAS, resultados)
    ]

    return EstadoDependencias(
        todas_disponibles=all(d.disponible for d in dependencias),
        dependencias=dependencias,
    )
