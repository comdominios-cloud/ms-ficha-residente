"""Punto de entrada de ms-ficha-residente.

Microservicio **sin base de datos**. Su unica responsabilidad es consumir a
ms-residentes, ms-pagos y ms-incidencias, y devolver una ficha consolidada del
residente.

Cumple dos requisitos del curso a la vez: es el microservicio sin base de datos
y el que consume a otros microservicios.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import ficha, salud

settings = get_settings()

app = FastAPI(
    title="ms-ficha-residente",
    description=(
        "Microservicio consumidor, sin base de datos. Agrega en una sola "
        "respuesta la informacion de ms-residentes, ms-pagos y ms-incidencias.\n\n"
        "Las llamadas salen en paralelo y cada bloque de la respuesta indica si "
        "el servicio correspondiente estuvo disponible: si uno se cae, la ficha "
        "se devuelve igual con esa seccion marcada."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Sin esto el navegador bloquea las llamadas del frontend en Amplify.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(salud.router)
app.include_router(ficha.router)
