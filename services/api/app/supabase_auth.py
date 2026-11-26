"""Cliente de Supabase Auth (GoTrue), solo desde la API (ADR-0003 §3).

La API valida la clave con el grant `password` y cierra de inmediato la sesion de Supabase que
eso abre: la sesion de la app la emite y controla la API (inactividad, bloqueo, bitacora).
Los usuarios sinteticos se identifican en Supabase por un correo derivado del nombre de usuario.
"""

import logging
import os
import re
import time

import httpx
import jwt

from app.config import obtener_config
from app.errores import servicio_no_disponible

log = logging.getLogger("api.auth")

DOMINIO_CORREO = "usuarios.movil-buscador.test"
_USUARIO_VALIDO = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


def normalizar_usuario(usuario: str) -> str:
    return usuario.strip().lower()


def correo_de(usuario: str) -> str:
    return f"{normalizar_usuario(usuario)}@{DOMINIO_CORREO}"


def _cabeceras(token: str | None = None) -> dict[str, str]:
    config = obtener_config()
    cabeceras: dict[str, str] = {}
    if config.auth_apikey:
        cabeceras["apikey"] = config.auth_apikey
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    return cabeceras


async def clave_valida(usuario: str, clave: str) -> bool:
    """True si Supabase Auth acepta la clave. Un error de Supabase no es "clave incorrecta":
    lanza SERVICIO_NO_DISPONIBLE (AGENTS.md regla 7)."""
    config = obtener_config()
    if not _USUARIO_VALIDO.match(normalizar_usuario(usuario)):
        return False
    try:
        async with httpx.AsyncClient(timeout=config.timeout_auth_s) as cliente:
            respuesta = await cliente.post(
                f"{config.auth_url}/token",
                params={"grant_type": "password"},
                json={"email": correo_de(usuario), "password": clave},
                headers=_cabeceras(),
            )
            if respuesta.status_code == 200:
                token = respuesta.json().get("access_token")
                if token:
                    try:  # cierra la sesion de Supabase; la sesion de la app es de la API
                        await cliente.post(f"{config.auth_url}/logout", headers=_cabeceras(token))
                    except httpx.HTTPError:
                        log.warning("auth_logout_fallido")
                return True
    except httpx.HTTPError as exc:
        log.warning("auth_no_disponible", extra={"tipo": type(exc).__name__})
        raise servicio_no_disponible() from exc
    if respuesta.status_code in (400, 401, 403, 422):
        return False
    log.warning("auth_respuesta_inesperada", extra={"estado": respuesta.status_code})
    raise servicio_no_disponible()


# --- administracion (solo el script de carga) ---------------------------------------------------


def _token_servicio() -> str:
    """Token service_role firmado con AUTH_JWT_SECRETO: solo para el Auth local (GoTrue del compose)
    o un proyecto de Supabase con el JWT secret heredado."""
    config = obtener_config()
    if len(config.auth_jwt_secreto) < 32:
        raise RuntimeError(
            "Falta la credencial de administración de Auth: defina AUTH_ADMIN_CLAVE "
            "(o AUTH_JWT_SECRETO con 32 caracteres o más, para el Auth local)"
        )
    ahora = int(time.time())
    return jwt.encode(
        {"role": "service_role", "iss": "supabase", "iat": ahora, "exp": ahora + 300},
        config.auth_jwt_secreto,
        algorithm="HS256",
    )


def _cabeceras_admin() -> dict[str, str]:
    """Cabeceras de la API de administración de Auth (DESPLIEGUE-01, decisión 1).

    - AUTH_ADMIN_CLAVE: la "secret key" (`sb_secret_...`) o la clave `service_role` del proyecto de
      Supabase. Va en `apikey` y en `Authorization`. Se lee del entorno solo aquí, al correr
      app.cargar_usuarios: la API en marcha nunca la recibe.
    - Si falta, se firma un token service_role con AUTH_JWT_SECRETO (Auth local del compose).
    """
    clave_admin = os.environ.get("AUTH_ADMIN_CLAVE", "").strip()
    if clave_admin:
        return {"apikey": clave_admin, "Authorization": f"Bearer {clave_admin}"}
    return _cabeceras(_token_servicio())


def asegurar_usuario_auth(usuario: str, clave: str) -> str:
    """Crea o actualiza el usuario en Supabase Auth y devuelve su id."""
    config = obtener_config()
    correo = correo_de(usuario)
    with httpx.Client(timeout=config.timeout_auth_s, headers=_cabeceras_admin()) as cliente:
        existentes = cliente.get(f"{config.auth_url}/admin/users", params={"page": 1, "per_page": 1000})
        existentes.raise_for_status()
        for fila in existentes.json().get("users", []):
            if fila.get("email") == correo:
                actualizado = cliente.put(
                    f"{config.auth_url}/admin/users/{fila['id']}",
                    json={"password": clave, "email_confirm": True},
                )
                actualizado.raise_for_status()
                return fila["id"]
        creado = cliente.post(
            f"{config.auth_url}/admin/users",
            json={"email": correo, "password": clave, "email_confirm": True},
        )
        creado.raise_for_status()
        return creado.json()["id"]
