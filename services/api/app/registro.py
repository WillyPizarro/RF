"""Logs estructurados en JSON con id_traza por solicitud (ADR-0014).

Nunca se registran claves, tokens, imagenes ni la configuracion.
"""

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime

id_traza_actual: ContextVar[str | None] = ContextVar("id_traza_actual", default=None)

_CAMPOS_ESTANDAR = set(vars(logging.makeLogRecord({}))) | {"message", "asctime", "taskName"}


class FormateadorJSON(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        datos: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "nivel": record.levelname,
            "logger": record.name,
            "mensaje": record.getMessage(),
        }
        traza = id_traza_actual.get()
        if traza:
            datos["id_traza"] = traza
        for clave, valor in vars(record).items():
            if clave not in _CAMPOS_ESTANDAR and not clave.startswith("_"):
                datos[clave] = valor
        if record.exc_info and record.exc_info[0] is not None:
            datos["excepcion"] = record.exc_info[0].__name__
        return json.dumps(datos, ensure_ascii=False, default=str)
