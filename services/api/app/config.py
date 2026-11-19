"""Configuracion por variables de entorno (ADR-0009). Nunca se registra en logs."""

import os
from dataclasses import dataclass
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version


def _version() -> str:
    try:
        return version("movil-buscador-api")
    except PackageNotFoundError:
        return "0.0.0"


@dataclass(frozen=True)
class Config:
    database_url: str
    simuladores_url: str
    timeout_salud_s: float
    version: str


@lru_cache
def obtener_config() -> Config:
    return Config(
        database_url=os.environ.get("DATABASE_URL", ""),
        simuladores_url=os.environ.get("SIMULADORES_URL", "http://simuladores:8001").rstrip("/"),
        timeout_salud_s=float(os.environ.get("TIMEOUT_SALUD_S", "3")),
        version=_version(),
    )
