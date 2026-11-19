"""Formas y nombres de CONTRATO-HU-01 v2 y CONTRATO-HU-02 v2 (escritas desde el contrato)."""

from __future__ import annotations

import base64
import json
import re
import uuid
from datetime import datetime, timezone

RUTA_LOGIN = "/v1/auth/login"
RUTA_REFRESH = "/v1/auth/refresh"
RUTA_LOGOUT = "/v1/auth/logout"
RUTA_ME = "/v1/me"

USUARIOS_ACTIVOS = {"agente1": "agente", "agente2": "agente", "revisor1": "revisor",
                    "supervisor1": "supervisor"}
USUARIO_INACTIVO = "inactivo1"

ERRORES = {
    "CREDENCIALES_INVALIDAS": (401, "Usuario o clave incorrectos"),
    "CUENTA_BLOQUEADA": (423, "Cuenta bloqueada temporalmente"),
    "NO_AUTENTICADO": (401, "Inicie sesión nuevamente"),
    "SESION_VENCIDA": (401, "Su sesión se cerró por inactividad"),
    "SOLICITUD_INVALIDA": (422, None),
    "SERVICIO_NO_DISPONIBLE": (503, "No se pudo completar la operación; intente nuevamente"),
    "SIN_PERMISO": (403, "No tiene permiso para usar esta función"),
}
CAMPOS_EVENTO = ("id", "ocurrido_en", "usuario_id", "rol", "tipo_evento", "parametros",
                 "codigo_error", "id_traza", "es_sintetico")
PALABRA_PROHIBIDA = "identificad"  # AGENTS.md regla 1


def usuario_falso() -> str:
    """Un `usuario` que no existe; único por prueba (el bloqueo cuenta por texto)."""
    return "noexiste-" + uuid.uuid4().hex[:10]


def clave_mala() -> str:
    """Clave incorrecta con una marca única, para buscarla en logs y bitácora."""
    return "ClaveMala-" + uuid.uuid4().hex


def problemas_error(r, codigo: str) -> list[str]:
    """Formato estándar {codigo, mensaje, id_traza} con id_traza = X-Id-Traza (ADR-0007)."""
    estado, mensaje = ERRORES[codigo]
    p: list[str] = []
    if r.estado != estado:
        p.append(f"estado {r.estado}, se esperaba {estado}")
    try:
        d = r.json()
    except ValueError:
        return p + [f"el cuerpo no es JSON: {r.texto[:200]!r}"]
    if not isinstance(d, dict):
        return p + [f"el cuerpo no es un objeto: {d!r}"]
    if d.get("codigo") != codigo:
        p.append(f"codigo {d.get('codigo')!r}, se esperaba {codigo!r}")
    if mensaje is not None and d.get("mensaje") != mensaje:
        p.append(f"mensaje {d.get('mensaje')!r}, se esperaba {mensaje!r}")
    if not isinstance(d.get("mensaje"), str) or not d["mensaje"].strip():
        p.append("mensaje vacío")
    if not r.traza or d.get("id_traza") != r.traza:
        p.append(f"id_traza {d.get('id_traza')!r} distinto de X-Id-Traza {r.traza!r}")
    if PALABRA_PROHIBIDA in r.texto.lower():
        p.append("contiene la palabra prohibida")
    return p


def firma_error(r) -> tuple:
    """Lo que debe ser idéntico entre respuestas 'indistinguibles' (todo menos id_traza)."""
    d = r.json()
    return r.estado, {k: v for k, v in d.items() if k != "id_traza"}


def problemas_login_ok(r, usuario: str, rol: str, expira_en: int = 900,
                       inactividad_s: int = 600) -> list[str]:
    p: list[str] = []
    if r.estado != 200:
        return [f"estado {r.estado}: {r.texto[:300]}"]
    d = r.json()
    for c in ("token_acceso", "token_renovacion"):
        if not isinstance(d.get(c), str) or not d[c]:
            p.append(f"{c} vacío o ausente")
    if d.get("expira_en") != expira_en:
        p.append(f"expira_en {d.get('expira_en')!r}, se esperaba {expira_en}")
    if d.get("inactividad_s") != inactividad_s:
        p.append(f"inactividad_s {d.get('inactividad_s')!r}, se esperaba {inactividad_s}")
    u = d.get("usuario")
    if not isinstance(u, dict):
        return p + ["usuario ausente"]
    if not isinstance(u.get("id"), str) or not u["id"]:
        p.append("usuario.id vacío")
    if u.get("usuario") != usuario:
        p.append(f"usuario.usuario {u.get('usuario')!r}")
    if u.get("rol") != rol:
        p.append(f"usuario.rol {u.get('rol')!r}, se esperaba {rol!r}")
    if not isinstance(u.get("nombre"), str) or not u["nombre"].strip():
        p.append("usuario.nombre vacío")
    if PALABRA_PROHIBIDA in r.texto.lower():
        p.append("contiene la palabra prohibida")
    return p


def iso_utc(texto: str) -> datetime:
    """Interpreta un ISO 8601 con zona; exige que la zona sea UTC."""
    t = texto.replace("Z", "+00:00")
    dt = datetime.fromisoformat(t)
    assert dt.tzinfo is not None, f"{texto!r} no trae zona horaria"
    assert dt.utcoffset().total_seconds() == 0, f"{texto!r} no está en UTC"
    return dt


def instante(texto: str) -> datetime:
    """Instante absoluto de un timestamptz leído de la base (exige zona horaria)."""
    dt = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    assert dt.tzinfo is not None, f"ocurrido_en {texto!r} sin zona: no es un instante UTC"
    return dt


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


def tipos(eventos: list[dict]) -> list[str]:
    return [e.get("tipo_evento") for e in eventos]


def jwt_con_rol(token: str, rol: str) -> str:
    """Token con el payload cambiado (rol declarado) y la firma original: no debe validar."""
    partes = token.split(".")
    assert len(partes) == 3, "el token de acceso no tiene forma de JWT"

    def dec(s: str) -> dict:
        return json.loads(base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)))

    def enc(d: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")

    carga = dec(partes[1])
    for k in list(carga):
        if re.search(r"rol|role", k, re.I):
            carga[k] = rol
    carga.setdefault("rol", rol)
    carga.setdefault("role", rol)
    return ".".join([partes[0], enc(carga), partes[2]])
