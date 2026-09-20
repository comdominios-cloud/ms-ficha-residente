"""Cliente HTTP comun a los tres microservicios.

Dos decisiones que definen el comportamiento de este servicio:

1. **Nunca propaga la falla.** Si un microservicio no responde, `pedir` devuelve
   el error en vez de lanzarlo. El endpoint arma la ficha igual, con esa seccion
   marcada como no disponible. Asi la caida de un servicio no tumba a los otros
   dos: es lo que se llama degradacion controlada.

2. **Reintenta solo lo que tiene sentido.** Un timeout o un 5xx se reintentan
   (puede ser algo pasajero); un 404 o un 400 no, porque volver a preguntar da
   lo mismo.
"""

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()


@dataclass
class Respuesta:
    """Resultado de una llamada. O trae datos, o trae el motivo de la falla."""

    datos: Any = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


async def pedir(
    cliente: httpx.AsyncClient,
    servicio: str,
    url: str,
    params: dict | None = None,
) -> Respuesta:
    intentos = settings.http_max_retries + 1
    ultimo_error = "sin intentos"

    for intento in range(intentos):
        try:
            r = await cliente.get(url, params=params)
        except httpx.TimeoutException:
            ultimo_error = f"{servicio} no respondio a tiempo"
        except httpx.HTTPError:
            ultimo_error = f"no se pudo contactar a {servicio}"
        else:
            if r.status_code == 404:
                return Respuesta(error=f"{servicio}: no encontrado")
            if 400 <= r.status_code < 500:
                return Respuesta(error=f"{servicio}: respondio {r.status_code}")
            if r.is_success:
                try:
                    return Respuesta(datos=r.json())
                except ValueError:
                    return Respuesta(error=f"{servicio}: respuesta no es JSON")
            ultimo_error = f"{servicio}: respondio {r.status_code}"

        # Espera creciente entre reintentos, para no golpear un servicio caido.
        if intento < intentos - 1:
            await asyncio.sleep(0.3 * (intento + 1))

    return Respuesta(error=ultimo_error)


def crear_cliente() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=settings.http_timeout_seconds)
