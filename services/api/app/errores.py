"""Formato de error unico {codigo, mensaje, id_traza} (ADR-0007, SPRINT0 M-1 B).

ErrorApi lleva un codigo propio (CREDENCIALES_INVALIDAS, CUENTA_BLOQUEADA, ...) y campos extra
cuando el contrato los pide (bloqueado_hasta).
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorRespuesta(BaseModel):
    codigo: str
    mensaje: str
    id_traza: str


class ErrorBloqueo(ErrorRespuesta):
    bloqueado_hasta: str


# Codigos estables por estado HTTP. Lo que no esta aqui se trata como error interno.
_CODIGOS: dict[int, tuple[str, str]] = {
    404: ("NO_ENCONTRADO", "El recurso solicitado no existe."),
    405: ("METODO_NO_PERMITIDO", "El metodo no esta permitido para este recurso."),
    422: ("SOLICITUD_INVALIDA", "La solicitud no es valida."),
    500: ("ERROR_INTERNO", "Ocurrio un error interno."),
}

MENSAJE_NO_DISPONIBLE = "No se pudo completar la operación; intente nuevamente"


class ErrorApi(Exception):
    """Error de negocio con codigo y mensaje del contrato."""

    def __init__(self, estado: int, codigo: str, mensaje: str, **extra: Any) -> None:
        super().__init__(codigo)
        self.estado, self.codigo, self.mensaje, self.extra = estado, codigo, mensaje, extra


def no_autenticado() -> ErrorApi:
    return ErrorApi(401, "NO_AUTENTICADO", "Inicie sesión nuevamente")


def sesion_vencida() -> ErrorApi:
    return ErrorApi(401, "SESION_VENCIDA", "Su sesión se cerró por inactividad")


def servicio_no_disponible() -> ErrorApi:
    return ErrorApi(503, "SERVICIO_NO_DISPONIBLE", MENSAJE_NO_DISPONIBLE)


def respuesta_error(estado: int, id_traza: str) -> JSONResponse:
    if estado not in _CODIGOS:
        estado = 500
    codigo, mensaje = _CODIGOS[estado]
    cuerpo = ErrorRespuesta(codigo=codigo, mensaje=mensaje, id_traza=id_traza)
    return JSONResponse(status_code=estado, content=cuerpo.model_dump())


def _id_traza(request: Request) -> str:
    return getattr(request.state, "id_traza", "")


async def _manejar_api(request: Request, exc: ErrorApi) -> JSONResponse:
    cuerpo = {"codigo": exc.codigo, "mensaje": exc.mensaje, "id_traza": _id_traza(request), **exc.extra}
    cabeceras = {"WWW-Authenticate": "Bearer"} if exc.estado == 401 else None
    return JSONResponse(status_code=exc.estado, content=cuerpo, headers=cabeceras)


async def _manejar_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    respuesta = respuesta_error(exc.status_code, _id_traza(request))
    if exc.status_code == 405 and exc.headers:
        respuesta.headers.update(exc.headers)  # conserva la cabecera Allow
    return respuesta


async def _manejar_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    return respuesta_error(422, _id_traza(request))


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(ErrorApi, _manejar_api)
    app.add_exception_handler(StarletteHTTPException, _manejar_http)
    app.add_exception_handler(RequestValidationError, _manejar_validacion)


def respuestas_error(*estados: int) -> dict[int | str, dict[str, Any]]:
    """Documenta en el OpenAPI las respuestas de error de una ruta."""
    descripciones = {
        401: "No autenticado, credenciales invalidas o sesion vencida",
        403: "El rol del usuario no tiene permiso para esta funcion",
        422: "Solicitud invalida",
        423: "Cuenta bloqueada temporalmente",
        503: "No se pudo completar la operacion",
    }
    return {
        estado: {"model": ErrorBloqueo if estado == 423 else ErrorRespuesta, "description": descripciones[estado]}
        for estado in estados
    }
