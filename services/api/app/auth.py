"""POST /v1/auth/login, /refresh y /logout (CONTRATO-HU-01 §1 a §3, ADR-0003, ADR-0011)."""

import logging
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy import text

from app.bd import obtener_motor
from app.bitacora import registrar
from app.config import obtener_config
from app.errores import ErrorApi, respuestas_error, servicio_no_disponible
from app.sesion import (
    UsuarioSesion,
    controlar_sesion,
    hash_token,
    nuevo_token_renovacion,
    respuesta_sesion,
    usuario_actual,
)
from app.supabase_auth import clave_valida, normalizar_usuario

log = logging.getLogger("api.auth")

router = APIRouter(prefix="/v1/auth", tags=["sesion"])

Texto = Annotated[str, StringConstraints(strict=True, min_length=1, pattern=r"\S")]
Rol = Literal["agente", "revisor", "supervisor"]


class SolicitudLogin(BaseModel):
    usuario: Texto
    clave: Texto

    # La clave nunca aparece en un repr ni en un log.
    def __repr__(self) -> str:
        return f"SolicitudLogin(usuario={self.usuario!r})"


class SolicitudRenovacion(BaseModel):
    token_renovacion: Texto


class Perfil(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"id": "…", "usuario": "agente1", "nombre": "A. Prueba", "rol": "agente"}})

    id: str
    usuario: str
    nombre: str
    rol: Rol


class RespuestaSesion(BaseModel):
    token_acceso: str
    token_renovacion: str
    expira_en: int
    inactividad_s: int
    usuario: Perfil


def _credenciales_invalidas() -> ErrorApi:
    return ErrorApi(401, "CREDENCIALES_INVALIDAS", "Usuario o clave incorrectos")


def _bloqueada(hasta: datetime) -> ErrorApi:
    iso = hasta.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    return ErrorApi(423, "CUENTA_BLOQUEADA", "Cuenta bloqueada temporalmente", bloqueado_hasta=iso)


@router.post("/login", response_model=RespuestaSesion, responses=respuestas_error(401, 422, 423, 503))
async def login(cuerpo: SolicitudLogin, request: Request) -> dict:
    config = obtener_config()
    clave_usuario = normalizar_usuario(cuerpo.usuario)
    parametros = {"usuario": cuerpo.usuario}
    try:
        async with obtener_motor().begin() as cx:
            await cx.execute(
                text("INSERT INTO control_acceso (usuario) VALUES (:u) ON CONFLICT (usuario) DO NOTHING"),
                {"u": clave_usuario},
            )
            control = (
                await cx.execute(
                    text(
                        "SELECT intentos_fallidos, bloqueado_hasta, bloqueado_hasta > now() AS bloqueado "
                        "FROM control_acceso WHERE usuario = :u FOR UPDATE"
                    ),
                    {"u": clave_usuario},
                )
            ).mappings().one()
            perfil = (
                await cx.execute(
                    text("SELECT id, usuario, nombre, rol, activo FROM usuario_perfil WHERE usuario = :u"),
                    {"u": clave_usuario},
                )
            ).mappings().first()
            usuario_id = perfil["id"] if perfil else None
            rol = perfil["rol"] if perfil else None

            # Bloqueada: no se valida la clave y el bloqueo no se alarga (CONTRATO-HU-01 §2).
            if control["bloqueado"]:
                await registrar(
                    cx, request, "LOGIN_FALLIDO", usuario_id=usuario_id, rol=rol,
                    parametros=parametros, codigo_error="CUENTA_BLOQUEADA",
                )
                error: ErrorApi | None = _bloqueada(control["bloqueado_hasta"])
                exito = None
            else:
                intentos = control["intentos_fallidos"] if control["bloqueado_hasta"] is None else 0
                valida = await clave_valida(cuerpo.usuario, cuerpo.clave)
                if valida and perfil is not None and perfil["activo"]:
                    await cx.execute(
                        text(
                            "UPDATE control_acceso SET intentos_fallidos = 0, bloqueado_hasta = NULL, "
                            "usuario_id = :id WHERE usuario = :u"
                        ),
                        {"u": clave_usuario, "id": usuario_id},
                    )
                    token_renovacion, hash_renovacion = nuevo_token_renovacion()
                    sesion_id = (
                        await cx.execute(
                            text("INSERT INTO sesion (usuario_id, token_renovacion_hash) VALUES (:id, :h) RETURNING id"),
                            {"id": usuario_id, "h": hash_renovacion},
                        )
                    ).scalar_one()
                    await registrar(cx, request, "LOGIN_OK", usuario_id=usuario_id, rol=rol, parametros=parametros)
                    exito = (
                        UsuarioSesion(
                            id=str(usuario_id), usuario=perfil["usuario"], nombre=perfil["nombre"],
                            rol=perfil["rol"], sesion_id=str(sesion_id),
                        ),
                        token_renovacion,
                    )
                    error = None
                else:
                    intentos += 1
                    bloquear = intentos >= config.bloqueo_intentos
                    hasta = (
                        await cx.execute(
                            text(
                                "UPDATE control_acceso SET usuario_id = :id, "
                                "intentos_fallidos = CASE WHEN :bloquear THEN 0 ELSE :intentos END, "
                                "bloqueado_hasta = CASE WHEN :bloquear "
                                "  THEN date_trunc('second', now()) + make_interval(secs => :duracion) END "
                                "WHERE usuario = :u RETURNING bloqueado_hasta"
                            ),
                            {
                                "u": clave_usuario, "id": usuario_id, "bloquear": bloquear,
                                "intentos": intentos, "duracion": config.bloqueo_duracion_s,
                            },
                        )
                    ).scalar_one()
                    await registrar(
                        cx, request, "LOGIN_FALLIDO", usuario_id=usuario_id, rol=rol,
                        parametros=parametros, codigo_error="CREDENCIALES_INVALIDAS",
                    )
                    if bloquear:
                        await registrar(
                            cx, request, "CUENTA_BLOQUEADA", usuario_id=usuario_id, rol=rol,
                            parametros={**parametros, "bloqueado_hasta": hasta.isoformat()},
                            codigo_error="CUENTA_BLOQUEADA",
                        )
                        error = _bloqueada(hasta)
                    else:
                        error = _credenciales_invalidas()
                    exito = None
    except ErrorApi:
        raise
    except Exception as exc:  # sin registro no hay sesion (ADR-0005 §2)
        log.warning("login_no_completado", extra={"tipo": type(exc).__name__})
        raise servicio_no_disponible() from exc
    if error:
        raise error
    assert exito is not None
    return respuesta_sesion(*exito)


@router.post("/refresh", response_model=RespuestaSesion, responses=respuestas_error(401, 422, 503))
async def renovar(cuerpo: SolicitudRenovacion, request: Request) -> dict:
    try:
        async with obtener_motor().begin() as cx:
            usuario, error = await controlar_sesion(
                cx, request, "s.token_renovacion_hash = :valor", hash_token(cuerpo.token_renovacion)
            )
    except ErrorApi:
        raise
    except Exception as exc:
        log.warning("renovacion_no_completada", extra={"tipo": type(exc).__name__})
        raise servicio_no_disponible() from exc
    if error:
        raise error
    assert usuario is not None
    return respuesta_sesion(usuario, cuerpo.token_renovacion)


@router.post("/logout", status_code=204, response_class=Response, responses=respuestas_error(401, 503))
async def cerrar_sesion(request: Request, usuario: UsuarioSesion = Depends(usuario_actual)) -> Response:
    try:
        async with obtener_motor().begin() as cx:
            await cx.execute(text("UPDATE sesion SET estado = 'cerrada' WHERE id = :id"), {"id": usuario.sesion_id})
            await registrar(cx, request, "LOGOUT", usuario_id=usuario.id, rol=usuario.rol)
    except Exception as exc:
        log.warning("logout_no_completado", extra={"tipo": type(exc).__name__})
        raise servicio_no_disponible() from exc
    return Response(status_code=204)
