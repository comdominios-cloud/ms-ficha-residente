"""Cliente de ms-incidencias (puerto 9003)."""

import httpx

from app.clients.base import Respuesta, pedir
from app.config import get_settings

BASE = get_settings().ms_incidencias_url.rstrip("/")
SERVICIO = "ms-incidencias"


async def listar_incidencias(cliente: httpx.AsyncClient, unidad_id: int) -> Respuesta:
    return await pedir(
        cliente, SERVICIO, f"{BASE}/incidencias", params={"unidad_id": unidad_id}
    )


async def listar_reservas(cliente: httpx.AsyncClient, unidad_id: int) -> Respuesta:
    return await pedir(
        cliente, SERVICIO, f"{BASE}/reservas", params={"unidad_id": unidad_id}
    )
