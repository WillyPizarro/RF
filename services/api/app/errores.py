"""Formato de error unico {codigo, mensaje, id_traza} (ADR-0007, SPRINT0 M-1 B)."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorRespuesta(BaseModel):
    codigo: str
    mensaje: str
    id_traza: str


# Codigos estables por estado HTTP. Lo que no esta aqui se trata como error interno.
_CODIGOS: dict[int, tuple[str, str]] = {
    404: ("NO_ENCONTRADO", "El recurso solicitado no existe."),
    405: ("METODO_NO_PERMITIDO", "El metodo no esta permitido para este recurso."),
    422: ("SOLICITUD_INVALIDA", "La solicitud no es valida."),
    500: ("ERROR_INTERNO", "Ocurrio un error interno."),
}


def respuesta_error(estado: int, id_traza: str) -> JSONResponse:
    if estado not in _CODIGOS:
        estado = 500
    codigo, mensaje = _CODIGOS[estado]
    cuerpo = ErrorRespuesta(codigo=codigo, mensaje=mensaje, id_traza=id_traza)
    return JSONResponse(status_code=estado, content=cuerpo.model_dump())


def _id_traza(request: Request) -> str:
    return getattr(request.state, "id_traza", "")


async def _manejar_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    respuesta = respuesta_error(exc.status_code, _id_traza(request))
    if exc.status_code == 405 and exc.headers:
        respuesta.headers.update(exc.headers)  # conserva la cabecera Allow
    return respuesta


async def _manejar_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    return respuesta_error(422, _id_traza(request))


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, _manejar_http)
    app.add_exception_handler(RequestValidationError, _manejar_validacion)
