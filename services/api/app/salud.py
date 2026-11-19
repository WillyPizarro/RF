"""GET /v1/salud: estado de la API, la base y los simuladores (SPRINT0 seccion 5, M-1 A)."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.bd import bd_responde
from app.config import obtener_config
from app.simuladores import simuladores_responden

log = logging.getLogger("api.salud")

router = APIRouter(prefix="/v1", tags=["salud"])

Estado = Literal["ok", "error"]


class SaludRespuesta(BaseModel):
    estado: Estado
    bd: Estado
    simuladores: Estado
    version: str


async def _verificar(nombre: str, chequeo: Callable[[], Awaitable[None]]) -> Estado:
    timeout = obtener_config().timeout_salud_s
    try:
        await asyncio.wait_for(chequeo(), timeout=timeout + 1)
        return "ok"
    except Exception as exc:  # cualquier falla es "error", nunca "ok"
        log.warning("dependencia_caida", extra={"dependencia": nombre, "tipo": type(exc).__name__})
        return "error"


@router.get(
    "/salud",
    response_model=SaludRespuesta,
    responses={503: {"model": SaludRespuesta, "description": "La base o los simuladores no responden"}},
)
async def salud() -> JSONResponse:
    bd, simuladores = await asyncio.gather(
        _verificar("bd", bd_responde),
        _verificar("simuladores", simuladores_responden),
    )
    sano = bd == "ok" and simuladores == "ok"
    cuerpo = SaludRespuesta(
        estado="ok" if sano else "error",
        bd=bd,
        simuladores=simuladores,
        version=obtener_config().version,
    )
    return JSONResponse(status_code=200 if sano else 503, content=cuerpo.model_dump())
