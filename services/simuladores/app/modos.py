"""Modos de falla por fuente, en tiempo de ejecucion (ADR-0006 §4, contrato HU-08 §5)."""

import threading
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

FUENTES = ("placas", "requisitorias-personas", "galeria")
LATENCIA_POR_DEFECTO_MS = 5000

Modo = Literal["normal", "latencia", "error_500", "malformada"]


class CambioModo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modo: Modo
    latencia_ms: StrictInt | None = Field(default=None, ge=0)


class EstadoModo(BaseModel):
    modo: Modo = "normal"
    latencia_ms: int | None = None


class Modos:
    def __init__(self) -> None:
        self._candado = threading.Lock()
        self._estado = {fuente: EstadoModo() for fuente in FUENTES}

    def obtener(self, fuente: str) -> EstadoModo:
        with self._candado:
            return self._estado[fuente]

    def todos(self) -> dict[str, dict]:
        with self._candado:
            return {fuente: estado.model_dump() for fuente, estado in self._estado.items()}

    def cambiar(self, fuente: str, cambio: CambioModo) -> EstadoModo:
        latencia = None
        if cambio.modo == "latencia":
            latencia = cambio.latencia_ms if cambio.latencia_ms is not None else LATENCIA_POR_DEFECTO_MS
        nuevo = EstadoModo(modo=cambio.modo, latencia_ms=latencia)
        with self._candado:
            self._estado[fuente] = nuevo
        return nuevo


modos = Modos()
