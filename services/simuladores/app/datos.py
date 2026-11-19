"""Datos sinteticos versionados (ADR-0006 §5). Se cargan una vez desde app/datos/semilla.json."""

import json
from functools import lru_cache
from pathlib import Path

_SEMILLA = Path(__file__).resolve().parent / "datos" / "semilla.json"


class Datos:
    def __init__(self, crudo: dict) -> None:
        self.vehiculos: dict[str, dict] = {v["placa"]: v for v in crudo["vehiculos"]}
        self.personas: dict[str, dict] = {p["persona_id"]: p for p in crudo["personas"]}


@lru_cache
def obtener_datos() -> Datos:
    return Datos(json.loads(_SEMILLA.read_text(encoding="utf-8")))
