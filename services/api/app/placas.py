"""GET /v1/motivos y POST /v1/consultas/placa (CONTRATO-HU-03 v3, ADR-0005, ADR-0011, ADR-0014).

Orden de validacion: motivo, formato, fuente. Los rechazos 422 no consultan la fuente ni dejan
evento. La consulta y su evento se guardan en una sola transaccion: sin registro no hay resultado
(fail-closed, ADR-0005 §2).
"""

import logging
import re
from datetime import UTC
from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.bd import obtener_motor
from app.bitacora import registrar
from app.config import obtener_config
from app.errores import ErrorApi, respuestas_error, servicio_no_disponible
from app.fuente_placas import (
    FuenteNoDisponible,
    FuentePlacas,
    FuenteRespuestaInvalida,
    obtener_fuente_placas,
)
from app.sesion import UsuarioSesion, requiere_rol

log = logging.getLogger("api.placas")

router = APIRouter(prefix="/v1", tags=["placas"])

MOTIVO_OTRO = "otro"
MOTIVO_OTRO_MINIMO = 10
MENSAJE_FUENTE = "No se pudo completar la consulta; intente nuevamente"


# --- modelos ------------------------------------------------------------------------------------


class Motivo(BaseModel):
    codigo: str
    descripcion: str


class FormatoPlaca(BaseModel):
    regex: str
    descripcion: str


class RespuestaMotivos(BaseModel):
    motivos: list[Motivo]
    formato_placa: FormatoPlaca


class SolicitudConsultaPlaca(BaseModel):
    model_config = ConfigDict(strict=True)

    placa: str
    motivo_codigo: str | None = None
    motivo_texto: str | None = None


class MotivoConsulta(BaseModel):
    codigo: str
    texto: str | None


class RespuestaConsultaPlaca(BaseModel):
    consulta_id: str
    placa: str
    resultado: Literal["con_requisitoria", "sin_requisitoria", "placa_no_registrada"]
    motivo: MotivoConsulta
    consultado_en: str


# --- catalogo -----------------------------------------------------------------------------------

_MOTIVOS_ACTIVOS = text(
    "SELECT codigo, descripcion FROM motivo_catalogo WHERE activo "
    "ORDER BY codigo = 'otro', orden, codigo"
)


async def _motivos_activos(cx: AsyncConnection) -> list[dict[str, str]]:
    return [dict(fila) for fila in (await cx.execute(_MOTIVOS_ACTIVOS)).mappings()]


@router.get("/motivos", response_model=RespuestaMotivos, responses=respuestas_error(401, 403, 503))
async def listar_motivos(_: UsuarioSesion = Depends(requiere_rol("agente"))) -> dict:
    config = obtener_config()
    try:
        async with obtener_motor().connect() as cx:
            motivos = await _motivos_activos(cx)
    except Exception as exc:
        log.warning("motivos_no_leidos", extra={"tipo": type(exc).__name__})
        raise servicio_no_disponible() from exc
    return {
        "motivos": motivos,
        "formato_placa": {"regex": config.placa_formato_regex, "descripcion": config.placa_formato_descripcion},
    }


# --- consulta -----------------------------------------------------------------------------------


def _motivo_requerido(mensaje: str) -> ErrorApi:
    return ErrorApi(422, "MOTIVO_REQUERIDO", mensaje)


def _texto_motivo(codigo: str, texto: str | None) -> str:
    """Columna `motivo` de la bitacora: el codigo y, si es "Otro", su texto (CONTRATO-HU-07 §2)."""
    return f"{codigo}: {texto}" if codigo == MOTIVO_OTRO and texto else codigo


async def _validar_motivo(codigo: str | None, texto: str | None) -> tuple[str, str | None]:
    codigo = (codigo or "").strip()
    if not codigo:
        raise _motivo_requerido("Indique el motivo de la consulta")
    try:
        async with obtener_motor().connect() as cx:
            activos = {m["codigo"] for m in await _motivos_activos(cx)}
    except Exception as exc:
        log.warning("motivos_no_leidos", extra={"tipo": type(exc).__name__})
        raise servicio_no_disponible() from exc
    if codigo not in activos:
        raise _motivo_requerido("Indique el motivo de la consulta")
    if codigo == MOTIVO_OTRO:
        texto = (texto or "").strip()
        if len(texto) < MOTIVO_OTRO_MINIMO:
            raise _motivo_requerido("Describa el motivo (mínimo 10 caracteres)")
        return codigo, texto
    return codigo, None


def _validar_formato(placa: str) -> None:
    config = obtener_config()
    if not re.fullmatch(config.placa_formato_regex, placa):
        raise ErrorApi(
            422,
            "PLACA_FORMATO_INVALIDO",
            f"El formato de placa no es válido. Formato esperado: {config.placa_formato_descripcion}",
        )


_INSERTAR_CONSULTA = text(
    """
    INSERT INTO consulta (tipo, agente_id, motivo_codigo, motivo_texto, placa, resultado, estado)
    VALUES ('placa', :agente_id, :motivo_codigo, :motivo_texto, :placa, :resultado, :estado)
    RETURNING id, creada_en
    """
)


@router.post(
    "/consultas/placa",
    response_model=RespuestaConsultaPlaca,
    responses=respuestas_error(401, 403, 422, 502, 503),
)
async def consultar_placa(
    cuerpo: SolicitudConsultaPlaca,
    request: Request,
    usuario: UsuarioSesion = Depends(requiere_rol("agente")),
    fuente: FuentePlacas = Depends(obtener_fuente_placas),
) -> dict:
    placa = cuerpo.placa.strip().upper()
    motivo_codigo, motivo_texto = await _validar_motivo(cuerpo.motivo_codigo, cuerpo.motivo_texto)
    _validar_formato(placa)

    error: ErrorApi | None = None
    try:
        resultado: str = await fuente.consultar(placa)
    except FuenteNoDisponible:
        error = ErrorApi(503, "FUENTE_NO_DISPONIBLE", MENSAJE_FUENTE)
    except FuenteRespuestaInvalida:
        error = ErrorApi(502, "FUENTE_RESPUESTA_INVALIDA", MENSAJE_FUENTE)
    if error:
        resultado = "error"

    motivo = _texto_motivo(motivo_codigo, motivo_texto)
    try:
        async with obtener_motor().begin() as cx:
            fila = (
                await cx.execute(
                    _INSERTAR_CONSULTA,
                    {
                        "agente_id": usuario.id,
                        "motivo_codigo": motivo_codigo,
                        "motivo_texto": motivo_texto,
                        "placa": placa,
                        "resultado": resultado,
                        "estado": "error" if error else "completada",
                    },
                )
            ).mappings().one()
            if error:
                await registrar(
                    cx, request, "ERROR_FUENTE", usuario_id=usuario.id, rol=usuario.rol, motivo=motivo,
                    parametros={"placa": placa, "fuente": "placas"}, resultado="error",
                    codigo_error=error.codigo, consulta_id=fila["id"],
                )
            else:
                await registrar(
                    cx, request, "CONSULTA_PLACA", usuario_id=usuario.id, rol=usuario.rol, motivo=motivo,
                    parametros={"placa": placa}, resultado=resultado, consulta_id=fila["id"],
                )
    except Exception as exc:  # sin registro no hay resultado (ADR-0005 §2)
        log.warning("consulta_no_registrada", extra={"tipo": type(exc).__name__})
        raise servicio_no_disponible() from exc

    if error:
        raise error
    consultado_en = fila["creada_en"].astimezone(UTC)
    return {
        "consulta_id": str(fila["id"]),
        "placa": placa,
        "resultado": resultado,
        "motivo": {"codigo": motivo_codigo, "texto": motivo_texto},
        "consultado_en": consultado_en.isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
