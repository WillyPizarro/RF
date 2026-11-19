"""Sesiones de la API: tokens, inactividad en el servidor y control por rol (ADR-0003 §4,
ADR-0011, CONTRATO-HU-01 §3, CONTRATO-HU-02 §2).

- Token de acceso: JWT HS256 firmado con JWT_SECRETO (emisor, vencimiento y sesion). No lleva el
  rol: el rol se resuelve siempre en el servidor, desde usuario_perfil.
- Token de renovacion: valor aleatorio; en la base solo se guarda su sha256.
- Inactividad: cada solicitud autenticada y cada renovacion actualizan `ultima_actividad`. Si pasan
  mas de SESION_INACTIVIDAD_S, la sesion queda `vencida` y se registra SESION_VENCIDA una vez.
"""

import hashlib
import logging
import secrets
import time
import uuid
from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.bd import obtener_motor
from app.bitacora import registrar
from app.config import obtener_config
from app.errores import ErrorApi, no_autenticado, servicio_no_disponible, sesion_vencida

log = logging.getLogger("api.sesion")

EMISOR = "movil-buscador-api"
_portador = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class UsuarioSesion:
    id: str
    usuario: str
    nombre: str
    rol: str
    sesion_id: str

    def perfil(self) -> dict[str, str]:
        return {"id": self.id, "usuario": self.usuario, "nombre": self.nombre, "rol": self.rol}


# --- tokens -------------------------------------------------------------------------------------


def _secreto() -> str:
    secreto = obtener_config().jwt_secreto
    if len(secreto) < 32:
        raise RuntimeError("JWT_SECRETO falta o tiene menos de 32 caracteres")
    return secreto


def crear_token_acceso(usuario_id: str, sesion_id: str) -> str:
    ahora = int(time.time())
    return jwt.encode(
        {
            "iss": EMISOR,
            "sub": usuario_id,
            "sid": sesion_id,
            "iat": ahora,
            "exp": ahora + obtener_config().token_acceso_vigencia_s,
        },
        _secreto(),
        algorithm="HS256",
    )


def nuevo_token_renovacion() -> tuple[str, str]:
    token = secrets.token_urlsafe(48)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def respuesta_sesion(usuario: UsuarioSesion, token_renovacion: str) -> dict[str, Any]:
    config = obtener_config()
    return {
        "token_acceso": crear_token_acceso(usuario.id, usuario.sesion_id),
        "token_renovacion": token_renovacion,
        "expira_en": config.token_acceso_vigencia_s,
        "inactividad_s": config.sesion_inactividad_s,
        "usuario": usuario.perfil(),
    }


# --- carga y control de la sesion ---------------------------------------------------------------

_SESION = """
    SELECT s.id AS sesion_id, s.estado, s.token_renovacion_hash,
           now() - s.ultima_actividad > make_interval(secs => :inactividad) AS inactiva,
           p.id AS usuario_id, p.usuario, p.nombre, p.rol, p.activo
    FROM sesion s JOIN usuario_perfil p ON p.id = s.usuario_id
    WHERE {filtro}
    FOR UPDATE OF s
"""


async def controlar_sesion(
    conexion: AsyncConnection, request: Request, filtro: str, valor: str
) -> tuple[UsuarioSesion | None, ErrorApi | None]:
    """Valida la sesion y registra la actividad. Devuelve el usuario, o el error a lanzar despues
    de confirmar la transaccion (la sesion vencida y su evento deben quedar guardados)."""
    fila = (
        await conexion.execute(
            text(_SESION.format(filtro=filtro)),
            {"valor": valor, "inactividad": obtener_config().sesion_inactividad_s},
        )
    ).mappings().first()
    if fila is None or fila["estado"] == "cerrada":
        return None, no_autenticado()
    if fila["estado"] == "vencida":
        return None, sesion_vencida()
    if fila["inactiva"]:
        await conexion.execute(text("UPDATE sesion SET estado = 'vencida' WHERE id = :id"), {"id": fila["sesion_id"]})
        await registrar(
            conexion,
            request,
            "SESION_VENCIDA",
            usuario_id=fila["usuario_id"],
            rol=fila["rol"],
            parametros={"sesion_id": str(fila["sesion_id"])},
        )
        return None, sesion_vencida()
    if not fila["activo"]:
        await conexion.execute(text("UPDATE sesion SET estado = 'cerrada' WHERE id = :id"), {"id": fila["sesion_id"]})
        return None, no_autenticado()
    await conexion.execute(text("UPDATE sesion SET ultima_actividad = now() WHERE id = :id"), {"id": fila["sesion_id"]})
    return (
        UsuarioSesion(
            id=str(fila["usuario_id"]),
            usuario=fila["usuario"],
            nombre=fila["nombre"],
            rol=fila["rol"],
            sesion_id=str(fila["sesion_id"]),
        ),
        None,
    )


async def usuario_actual(
    request: Request, credenciales: HTTPAuthorizationCredentials | None = Depends(_portador)
) -> UsuarioSesion:
    """Dependencia de toda ruta autenticada: 401 si no hay token valido o la sesion no sirve."""
    if credenciales is None or credenciales.scheme.lower() != "bearer":
        raise no_autenticado()
    try:
        datos = jwt.decode(
            credenciales.credentials,
            _secreto(),
            algorithms=["HS256"],
            issuer=EMISOR,
            options={"require": ["exp", "iat", "iss", "sub", "sid"]},
        )
        sesion_id = str(uuid.UUID(str(datos["sid"])))
    except (jwt.PyJWTError, ValueError) as exc:
        raise no_autenticado() from exc
    try:
        async with obtener_motor().begin() as conexion:
            usuario, error = await controlar_sesion(conexion, request, "s.id = CAST(:valor AS uuid)", sesion_id)
    except ErrorApi:
        raise
    except Exception as exc:
        log.warning("sesion_no_verificada", extra={"tipo": type(exc).__name__})
        raise servicio_no_disponible() from exc
    if error:
        raise error
    assert usuario is not None
    if usuario.id != str(datos["sub"]):
        raise no_autenticado()
    request.state.usuario = usuario
    return usuario


def requiere_rol(*roles: str):
    """Dependencia para rutas reservadas a uno o mas roles (matriz de CONTRATO-HU-02 §2).

    Primero autentica (401). Si el rol no esta permitido: 403 SIN_PERMISO y ACCESO_DENEGADO en la
    bitacora, sin ejecutar la ruta.
    """

    async def _dependencia(request: Request, usuario: UsuarioSesion = Depends(usuario_actual)) -> UsuarioSesion:
        if usuario.rol in roles:
            return usuario
        try:
            async with obtener_motor().begin() as conexion:
                await registrar(
                    conexion,
                    request,
                    "ACCESO_DENEGADO",
                    usuario_id=usuario.id,
                    rol=usuario.rol,
                    parametros={"ruta": request.url.path, "metodo": request.method},
                    codigo_error="SIN_PERMISO",
                )
        except Exception as exc:
            log.warning("bitacora_no_escrita", extra={"tipo": type(exc).__name__})
            raise servicio_no_disponible() from exc
        raise ErrorApi(403, "SIN_PERMISO", "No tiene permiso para usar esta función")

    return _dependencia
