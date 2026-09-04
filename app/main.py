"""Punto de entrada de ms-ficha-residente.

ANDAMIAJE: solo instancia la aplicacion FastAPI y expone Swagger-UI.
Este microservicio NO tiene base de datos: su unica responsabilidad es
consumir a ms-residentes, ms-pagos y ms-incidencias, y devolver la ficha
consolidada del residente.
"""

from fastapi import FastAPI

app = FastAPI(
    title="ms-ficha-residente",
    description=(
        "Microservicio consumidor. Sin base de datos: agrega la informacion "
        "de ms-residentes, ms-pagos y ms-incidencias en una ficha unica."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "ms-ficha-residente"}


# TODO: app.include_router(...) por cada router de app/routers/
# TODO: clientes httpx hacia los 3 microservicios en app/clients/
