"""Simuladores de fuentes (ADR-0006, contrato HU-08 v1).

Fuentes: placas, requisitorias-personas y galeria, con datos sinteticos. Ruta de control
/control/modos para los modos de falla. Solo alcanzable desde la red interna (ADR-0009).
"""

import asyncio
import json

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.datos import obtener_datos
from app.fotos import almacen_fotos, fotos_por_persona, version_galeria
from app.modos import FUENTES, CambioModo, modos

app = FastAPI(
    title="Movil Buscador Simuladores",
    version="0.2.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


# --- errores {codigo, mensaje} (contrato HU-08, decision 2) -------------------------------------


class ErrorSimulador(Exception):
    def __init__(self, estado: int, codigo: str, mensaje: str) -> None:
        self.estado, self.codigo, self.mensaje = estado, codigo, mensaje


def _error(estado: int, codigo: str, mensaje: str) -> JSONResponse:
    return JSONResponse(status_code=estado, content={"codigo": codigo, "mensaje": mensaje})


_GENERICOS = {
    404: ("NO_ENCONTRADO", "El recurso solicitado no existe."),
    405: ("METODO_NO_PERMITIDO", "El método no está permitido para este recurso."),
    422: ("SOLICITUD_INVALIDA", "La solicitud no es válida."),
}


@app.exception_handler(ErrorSimulador)
async def _manejar_simulador(_: Request, exc: ErrorSimulador) -> JSONResponse:
    return _error(exc.estado, exc.codigo, exc.mensaje)


@app.exception_handler(StarletteHTTPException)
async def _manejar_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    codigo, mensaje = _GENERICOS.get(exc.status_code, ("ERROR_INTERNO", "Ocurrió un error interno."))
    respuesta = _error(exc.status_code if exc.status_code in _GENERICOS else 500, codigo, mensaje)
    if exc.status_code == 405 and exc.headers:
        respuesta.headers.update(exc.headers)
    return respuesta


@app.exception_handler(RequestValidationError)
async def _manejar_validacion(_: Request, __: RequestValidationError) -> JSONResponse:
    return _error(422, *_GENERICOS[422])


@app.exception_handler(Exception)
async def _manejar_interno(_: Request, __: Exception) -> JSONResponse:
    return _error(500, "ERROR_INTERNO", "Ocurrió un error interno.")


# --- modos de falla -----------------------------------------------------------------------------


async def _modo(fuente: str) -> str:
    """Aplica latencia o error_500 de la fuente. Devuelve el modo para que la ruta trate 'malformada'."""
    estado = modos.obtener(fuente)
    if estado.modo == "latencia":
        await asyncio.sleep((estado.latencia_ms or 0) / 1000)
    elif estado.modo == "error_500":
        raise ErrorSimulador(500, "ERROR_SIMULADO", "Falla simulada de la fuente")
    return estado.modo


async def _fotos() -> dict:
    return await run_in_threadpool(almacen_fotos.sincronizar, set(obtener_datos().personas))


# --- salud --------------------------------------------------------------------------------------


@app.get("/salud")
async def salud() -> dict[str, str]:
    return {"estado": "ok"}


# --- fuente placas ------------------------------------------------------------------------------


@app.get("/placas/{placa}")
async def consultar_placa(placa: str) -> JSONResponse:
    if await _modo("placas") == "malformada":
        # Falta marca, modelo, color, tipo y requisitoria; requisitoria_vigente no es booleano.
        return JSONResponse({"placa": placa, "requisitoria_vigente": "desconocido", "es_sintetico": True})
    vehiculo = obtener_datos().vehiculos.get(placa)
    if vehiculo is None:
        raise ErrorSimulador(404, "PLACA_NO_REGISTRADA", "La placa no está registrada en la fuente")
    return JSONResponse({**vehiculo, "es_sintetico": True})


# --- fuente requisitorias-personas --------------------------------------------------------------


@app.get("/personas/{persona_id}")
async def consultar_persona(persona_id: str) -> JSONResponse:
    if await _modo("requisitorias-personas") == "malformada":
        # Faltan nombres, apellidos, documento, requisitoria y foto_ids.
        return JSONResponse({"persona_id": persona_id, "es_sintetico": True})
    persona = obtener_datos().personas.get(persona_id)
    if persona is None:
        raise ErrorSimulador(404, "PERSONA_NO_REGISTRADA", "La persona no está registrada en la fuente")
    foto_ids = fotos_por_persona(await _fotos()).get(persona_id, [])
    return JSONResponse({**persona, "foto_ids": foto_ids, "es_sintetico": True})


@app.get("/personas/{persona_id}/fotos/{foto_id}")
async def obtener_foto(persona_id: str, foto_id: str) -> Response:
    if await _modo("requisitorias-personas") == "malformada":
        # 200 que no es una imagen: no valida contra el contrato.
        return JSONResponse({"foto_id": foto_id, "es_sintetico": "no_booleano"})
    if persona_id not in obtener_datos().personas:
        raise ErrorSimulador(404, "PERSONA_NO_REGISTRADA", "La persona no está registrada en la fuente")
    foto = (await _fotos()).get(foto_id)
    if foto is None or foto.persona_id != persona_id:
        raise ErrorSimulador(404, "FOTO_NO_DISPONIBLE", "La foto no está disponible")
    contenido = await run_in_threadpool(almacen_fotos.leer, foto)
    return Response(content=contenido, media_type=foto.tipo, headers={"Cache-Control": "no-store"})


# --- fuente galeria -----------------------------------------------------------------------------


@app.get("/galeria")
async def consultar_galeria() -> JSONResponse:
    modo = await _modo("galeria")
    fotos = await _fotos()
    version = version_galeria(fotos)
    if modo == "malformada":
        # personas no es una lista.
        return JSONResponse({"version": version, "personas": "no_es_lista", "es_sintetico": True})
    personas = [
        {"persona_id": persona_id, "foto_ids": foto_ids}
        for persona_id, foto_ids in fotos_por_persona(fotos).items()
    ]
    return JSONResponse({"version": version, "personas": personas, "es_sintetico": True})


# --- control de modos (fuera de los contratos de las fuentes) -----------------------------------


@app.get("/control/modos")
async def listar_modos() -> dict[str, dict]:
    return modos.todos()


@app.put("/control/modos/{fuente}")
async def cambiar_modo(fuente: str, request: Request) -> dict:
    if fuente not in FUENTES:
        raise ErrorSimulador(404, "FUENTE_DESCONOCIDA", "La fuente no existe en el simulador")
    try:
        cambio = CambioModo.model_validate(json.loads(await request.body()))
    except (ValueError, ValidationError) as exc:
        raise ErrorSimulador(422, *_GENERICOS[422]) from exc
    return modos.cambiar(fuente, cambio).model_dump()
