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
    # Una URL por fuente (ADR-0006 §2, HU-08); si falta, se usa SIMULADORES_URL.
    fuente_placas_url: str
    fuente_requisitorias_url: str
    fuente_galeria_url: str
    fuente_timeout_s: float
    version: str


def _url(nombre: str, respaldo: str) -> str:
    valor = os.environ.get(nombre, "").strip()
    return (valor or respaldo).rstrip("/")


@lru_cache
def obtener_config() -> Config:
    simuladores_url = _url("SIMULADORES_URL", "http://simuladores:8001")
    return Config(
        database_url=os.environ.get("DATABASE_URL", ""),
        simuladores_url=simuladores_url,
        timeout_salud_s=float(os.environ.get("TIMEOUT_SALUD_S", "3")),
        fuente_placas_url=_url("FUENTE_PLACAS_URL", simuladores_url),
        fuente_requisitorias_url=_url("FUENTE_REQUISITORIAS_URL", simuladores_url),
        fuente_galeria_url=_url("FUENTE_GALERIA_URL", simuladores_url),
        fuente_timeout_s=float(os.environ.get("FUENTE_TIMEOUT_S", "").strip() or "3"),
        version=_version(),
    )
