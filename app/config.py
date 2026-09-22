"""Configuracion del microservicio.

Lee las variables de entorno una sola vez al arrancar. Este servicio no tiene
base de datos: lo unico que necesita saber es donde viven los otros tres.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ms-ficha-residente"
    app_env: str = "development"
    app_port: int = 8004
    log_level: str = "info"

    # Microservicios que consume
    ms_residentes_url: str = "http://localhost:9001"
    ms_pagos_url: str = "http://localhost:9002"
    ms_incidencias_url: str = "http://localhost:9003"

    http_timeout_seconds: float = 5.0
    http_max_retries: int = 2

    @property
    def dependencias(self) -> dict[str, str]:
        return {
            "ms-residentes": self.ms_residentes_url.rstrip("/"),
            "ms-pagos": self.ms_pagos_url.rstrip("/"),
            "ms-incidencias": self.ms_incidencias_url.rstrip("/"),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
