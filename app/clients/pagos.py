"""Cliente de ms-pagos (puerto 9002)."""

import httpx

from app.clients.base import Respuesta, pedir
from app.config import get_settings

BASE = get_settings().ms_pagos_url.rstrip("/")
SERVICIO = "ms-pagos"


async def estado_cuenta(cliente: httpx.AsyncClient, unidad_id: int) -> Respuesta:
    return await pedir(cliente, SERVICIO, f"{BASE}/unidades/{unidad_id}/estado-cuenta")


async def listar_cuotas(cliente: httpx.AsyncClient, unidad_id: int) -> Respuesta:
    return await pedir(
        cliente, SERVICIO, f"{BASE}/cuotas", params={"unidad_id": unidad_id}
    )


async def listar_pagos(cliente: httpx.AsyncClient, unidad_id: int) -> Respuesta:
    return await pedir(
        cliente, SERVICIO, f"{BASE}/pagos", params={"unidad_id": unidad_id}
    )
