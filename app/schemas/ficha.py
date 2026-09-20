"""Contratos de salida de la ficha consolidada.

Cada bloque lleva su propio `disponible` y `error`. Eso permite devolver la
ficha aunque alguno de los microservicios este caido: el consumidor sabe que
parte falto y por que, en vez de recibir un error entero.
"""

from typing import Any

from pydantic import BaseModel, Field


class Bloque(BaseModel):
    """Una seccion de la ficha, con el resultado de consultar a un servicio."""

    disponible: bool
    error: str | None = None
    datos: Any = None

    @classmethod
    def desde(cls, respuesta) -> "Bloque":
        if respuesta.ok:
            return cls(disponible=True, datos=respuesta.datos)
        return cls(disponible=False, error=respuesta.error)


class FichaResidente(BaseModel):
    residente_id: int
    unidad_id: int | None = None
    completa: bool = Field(
        description="True si los tres microservicios respondieron correctamente"
    )
    residente: Bloque
    estado_cuenta: Bloque
    cuotas: Bloque
    pagos: Bloque
    incidencias: Bloque
    reservas: Bloque


class FichaUnidad(BaseModel):
    unidad_id: int
    completa: bool
    unidad: Bloque
    residentes: Bloque
    estado_cuenta: Bloque
    incidencias: Bloque
    reservas: Bloque


class ResumenResidente(BaseModel):
    """Version reducida, para tarjetas y listados del frontend."""

    residente_id: int
    nombre: str | None = None
    unidad: str | None = None
    edificio: str | None = None
    deuda_total: float | None = None
    cuotas_pendientes: int | None = None
    incidencias_abiertas: int | None = None
    reservas_proximas: int | None = None
    completa: bool
    advertencias: list[str] = []


class EstadoDependencia(BaseModel):
    servicio: str
    url: str
    disponible: bool
    detalle: str | None = None


class EstadoDependencias(BaseModel):
    todas_disponibles: bool
    dependencias: list[EstadoDependencia]
