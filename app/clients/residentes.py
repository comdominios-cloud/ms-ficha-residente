"""Cliente de ms-residentes (puerto 9001)."""

import httpx

from app.clients.base import Respuesta, pedir
from app.config import get_settings

BASE = get_settings().ms_residentes_url.rstrip("/")
SERVICIO = "ms-residentes"


async def obtener_residente(cliente: httpx.AsyncClient, residente_id: int) -> Respuesta:
    return await pedir(cliente, SERVICIO, f"{BASE}/residentes/{residente_id}")


async def obtener_unidad(cliente: httpx.AsyncClient, unidad_id: int) -> Respuesta:
    return await pedir(cliente, SERVICIO, f"{BASE}/unidades/{unidad_id}")


async def listar_residentes_de_unidad(
    cliente: httpx.AsyncClient, unidad_id: int
) -> Respuesta:
    return await pedir(
        cliente, SERVICIO, f"{BASE}/residentes", params={"unidad_id": unidad_id}
    )
