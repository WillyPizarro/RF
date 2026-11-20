"""GET /v1/bitacora: consulta de la bitacora por el supervisor (CONTRATO-HU-07 §4, ADR-0005 §3).

- Filtros por usuario, rango de fechas (desde <= ocurrido_en < hasta), tipo y resultado; se combinan
  con Y.
- Orden: ocurrido_en y luego id, descendentes. Paginacion por cursor (keyset): el cursor guarda el
  ultimo (ocurrido_en, id) entregado, asi que los registros nuevos no corren las paginas.
- Cada consulta exitosa deja CONSULTA_BITACORA con los filtros usados, en la misma transaccion
  (sin registro no hay resultado). El evento se escribe despues de leer, asi no aparece en su
  propia respuesta.
- No hay rutas para modificar ni borrar: PUT, PATCH, DELETE o POST sobre /v1/bitacora* → 405.
"""

import base64
import binascii
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import text

from app.bd import obtener_motor
from app.bitacora import registrar
from app.errores import ErrorApi, respuestas_error, servicio_no_disponible
from app.sesion import UsuarioSesion, requiere_rol

log = logging.getLogger("api.consulta_bitacora")

router = APIRouter(prefix="/v1", tags=["bitacora"])

LIMITE_POR_DEFECTO = 50
LIMITE_MAXIMO = 100

# Tipos de evento del TDD (incluye los que llegan con HU-05 y HU-06).
TipoEvento = Literal[
    "LOGIN_OK",
    "LOGIN_FALLIDO",
    "CUENTA_BLOQUEADA",
    "LOGOUT",
    "SESION_VENCIDA",
    "ACCESO_DENEGADO",
    "CONSULTA_PLACA",
    "CONSULTA_ROSTRO",
    "CAPTURA_RECHAZADA",
    "DECISION_REVISION",
    "REVISION_VENCIDA",
    "CAPTURA_ELIMINADA",
    "ERROR_FUENTE",
    "CONSULTA_BITACORA",
]


class Registro(BaseModel):
    id: str
    ocurrido_en: str
    usuario: str | None
    rol: str | None
    tipo_evento: str
    motivo: str | None
    parametros: dict[str, Any] | None
    resultado: str | None
    score: float | None
    captura_id: str | None
    consulta_id: str | None
    codigo_error: str | None
    es_sintetico: bool


class RespuestaBitacora(BaseModel):
    registros: list[Registro]
    siguiente_cursor: str | None


def _solicitud_invalida() -> ErrorApi:
    return ErrorApi(422, "SOLICITUD_INVALIDA", "La solicitud no es valida.")


def _utc(fecha: datetime) -> datetime:
    # Una fecha sin zona se toma como UTC (la bitacora guarda UTC).
    return fecha.replace(tzinfo=UTC) if fecha.tzinfo is None else fecha.astimezone(UTC)


def _iso(fecha: datetime) -> str:
    return fecha.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _codificar_cursor(ocurrido_en: datetime, registro_id: uuid.UUID) -> str:
    crudo = json.dumps([_iso(ocurrido_en), str(registro_id)]).encode()
    return base64.urlsafe_b64encode(crudo).decode().rstrip("=")


def _decodificar_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        relleno = "=" * (-len(cursor) % 4)
        fecha, registro_id = json.loads(base64.urlsafe_b64decode(cursor + relleno))
        return _utc(datetime.fromisoformat(fecha)), str(uuid.UUID(registro_id))
    except (binascii.Error, ValueError, TypeError, UnicodeDecodeError) as exc:
        raise _solicitud_invalida() from exc


_SELECT = """
    SELECT b.id, b.ocurrido_en, p.usuario, b.rol, b.tipo_evento, b.motivo, b.parametros, b.resultado,
           b.score, b.captura_id, b.consulta_id, b.codigo_error, b.es_sintetico
    FROM bitacora b LEFT JOIN usuario_perfil p ON p.id = b.usuario_id
    WHERE {condiciones}
    ORDER BY b.ocurrido_en DESC, b.id DESC
    LIMIT :limite
"""


@router.get("/bitacora", response_model=RespuestaBitacora, responses=respuestas_error(401, 403, 422, 503))
async def consultar_bitacora(
    request: Request,
    usuario: Annotated[str | None, Query()] = None,
    desde: Annotated[datetime | None, Query()] = None,
    hasta: Annotated[datetime | None, Query()] = None,
    tipo: Annotated[TipoEvento | None, Query()] = None,
    resultado: Annotated[str | None, Query()] = None,
    limite: Annotated[int, Query(ge=1, le=LIMITE_MAXIMO)] = LIMITE_POR_DEFECTO,
    cursor: Annotated[str | None, Query()] = None,
    supervisor: UsuarioSesion = Depends(requiere_rol("supervisor")),
) -> dict:
    condiciones = ["true"]
    valores: dict[str, Any] = {"limite": limite + 1}
    filtros: dict[str, Any] = {}
    if usuario is not None:
        condiciones.append("p.usuario = :usuario")
        valores["usuario"] = filtros["usuario"] = usuario
    if desde is not None:
        condiciones.append("b.ocurrido_en >= :desde")
        valores["desde"] = _utc(desde)
        filtros["desde"] = _iso(valores["desde"])
    if hasta is not None:
        condiciones.append("b.ocurrido_en < :hasta")
        valores["hasta"] = _utc(hasta)
        filtros["hasta"] = _iso(valores["hasta"])
    if tipo is not None:
        condiciones.append("b.tipo_evento = :tipo")
        valores["tipo"] = filtros["tipo"] = tipo
    if resultado is not None:
        condiciones.append("b.resultado = :resultado")
        valores["resultado"] = filtros["resultado"] = resultado
    if cursor is not None:
        valores["cursor_fecha"], valores["cursor_id"] = _decodificar_cursor(cursor)
        condiciones.append("(b.ocurrido_en, b.id) < (:cursor_fecha, CAST(:cursor_id AS uuid))")
    filtros["limite"] = limite
    if cursor is not None:
        filtros["pagina_siguiente"] = True

    try:
        async with obtener_motor().begin() as cx:
            filas = (
                await cx.execute(text(_SELECT.format(condiciones=" AND ".join(condiciones))), valores)
            ).mappings().all()
            await registrar(
                cx, request, "CONSULTA_BITACORA", usuario_id=supervisor.id, rol=supervisor.rol, parametros=filtros
            )
    except Exception as exc:  # sin registro no hay resultado (ADR-0005 §2)
        log.warning("bitacora_no_consultada", extra={"tipo": type(exc).__name__})
        raise servicio_no_disponible() from exc

    pagina = filas[:limite]
    siguiente = (
        _codificar_cursor(pagina[-1]["ocurrido_en"], pagina[-1]["id"]) if len(filas) > limite and pagina else None
    )
    return {
        "registros": [
            {
                "id": str(f["id"]),
                "ocurrido_en": _iso(f["ocurrido_en"]),
                "usuario": f["usuario"],
                "rol": f["rol"],
                "tipo_evento": f["tipo_evento"],
                "motivo": f["motivo"],
                "parametros": f["parametros"],
                "resultado": f["resultado"],
                "score": f["score"],
                "captura_id": str(f["captura_id"]) if f["captura_id"] else None,
                "consulta_id": str(f["consulta_id"]) if f["consulta_id"] else None,
                "codigo_error": f["codigo_error"],
                "es_sintetico": f["es_sintetico"],
            }
            for f in pagina
        ],
        "siguiente_cursor": siguiente,
    }


@router.api_route("/bitacora/{registro}", methods=["GET"], include_in_schema=False)
async def registro_inexistente(registro: str) -> None:
    """Solo existe para que PUT, PATCH y DELETE sobre /v1/bitacora/<id> respondan 405 y no 404.
    No hay lectura individual: GET responde 404."""
    raise ErrorApi(404, "NO_ENCONTRADO", "El recurso solicitado no existe.")
