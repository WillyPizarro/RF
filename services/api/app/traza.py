"""Middleware de id_traza: cada respuesta lleva X-Id-Traza y Cache-Control: no-store, y genera una
linea de log JSON."""

import logging
import time
import uuid

from fastapi import FastAPI, Request, Response

from app.errores import respuesta_error
from app.registro import id_traza_actual

CABECERA_TRAZA = "X-Id-Traza"

log = logging.getLogger("api.solicitud")


def registrar_middleware_traza(app: FastAPI) -> None:
    @app.middleware("http")
    async def middleware_traza(request: Request, call_next) -> Response:
        id_traza = str(uuid.uuid4())
        request.state.id_traza = id_traza
        token = id_traza_actual.set(id_traza)
        inicio = time.perf_counter()
        try:
            try:
                respuesta = await call_next(request)
            except Exception:
                log.exception("error_no_controlado")
                respuesta = respuesta_error(500, id_traza)
            respuesta.headers[CABECERA_TRAZA] = id_traza
            # Ninguna respuesta de la API se guarda en caches HTTP (CONTRATO-HU-04 v4, ADR-0013),
            # tampoco las de error.
            respuesta.headers["Cache-Control"] = "no-store"
            log.info(
                "solicitud",
                extra={
                    "metodo": request.method,
                    "ruta": request.url.path,
                    "estado": respuesta.status_code,
                    "duracion_ms": round((time.perf_counter() - inicio) * 1000, 1),
                },
            )
            return respuesta
        finally:
            id_traza_actual.reset(token)
