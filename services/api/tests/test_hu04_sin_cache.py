"""CONTRATO-HU-04 v4 §6 "Sin caché HTTP: la API" — toda respuesta de `/v1/*` (éxito o error,
autenticada o no) lleva `Cache-Control: no-store`.

Se prueba por la red interna (`http://api:8000`, desde el contenedor api) y por el proxy
(`--url-base` / `URL_BASE_PRUEBAS`, o el puerto alterno de infra/.env). Las del proxy se omiten
con el motivo de la M-8 de HU-01/02 si el proxy no responde (o fallan con PROXY_DISPONIBLE=1).
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request

import pytest

from ayudas_hu03 import PLACA_CON, RUTA_BITACORA, RUTA_MOTIVOS, RUTA_PLACA, consulta


def _no_store(valor: str | None) -> bool:
    directivas = {d.strip().lower() for d in (valor or "").split(",")}
    return "no-store" in directivas


# (nombre, quién, método, ruta, cuerpo, estado esperado)
CASOS = [
    ("salud-200", None, "GET", "/v1/salud", None, 200),
    ("login-200", "agente1", "POST", "/v1/auth/login", "LOGIN", 200),
    ("login-401", None, "POST", "/v1/auth/login", {"usuario": "noexiste-cache", "clave": "x"}, 401),
    ("login-422", None, "POST", "/v1/auth/login", {"usuario": "agente1"}, 422),
    ("me-200", "agente1", "GET", "/v1/me", None, 200),
    ("me-401", None, "GET", "/v1/me", None, 401),
    ("motivos-200", "agente1", "GET", RUTA_MOTIVOS, None, 200),
    ("motivos-403", "revisor1", "GET", RUTA_MOTIVOS, None, 403),
    ("placa-200", "agente1", "POST", RUTA_PLACA, consulta(PLACA_CON), 200),
    ("placa-422", "agente1", "POST", RUTA_PLACA, consulta("HOLA MUNDO"), 422),
    ("bitacora-200", "supervisor1", "GET", RUTA_BITACORA + "?limite=1", None, 200),
    ("bitacora-403", "agente1", "GET", RUTA_BITACORA, None, 403),
    ("no-existe-404", None, "GET", "/v1/no-existe", None, 404),
    ("salud-405", None, "POST", "/v1/salud", {}, 405),
]
IDS = [c[0] for c in CASOS]


# --- Red interna -----------------------------------------------------------------------------

@pytest.mark.parametrize("nombre,quien,metodo,ruta,cuerpo,estado", CASOS, ids=IDS)
def test_no_store_por_la_red_interna(config_defecto, clave, nombre, quien, metodo, ruta, cuerpo,
                                     estado):
    s = config_defecto
    s.modo_placas("normal")
    if cuerpo == "LOGIN":
        r = s.login(quien, clave)
    else:
        kw = {"json": cuerpo} if cuerpo is not None else {}
        r = s.pedir(metodo, ruta, token=s.token(quien) if quien else None, **kw)
    assert r.estado == estado, (nombre, r)
    assert _no_store(r.cabecera("Cache-Control")), \
        f"{nombre}: Cache-Control = {r.cabecera('Cache-Control')!r}"


# --- Proxy -----------------------------------------------------------------------------------

def _por_proxy(url_base: str, metodo: str, ruta: str, cuerpo=None, token: str | None = None):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # CA local de Caddy (entorno de pruebas)
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    cab = {"Content-Type": "application/json"} if datos is not None else {}
    if token:
        cab["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url_base.rstrip("/") + ruta, data=datos, method=metodo,
                                 headers=cab)
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            return r.status, r.headers.get("Cache-Control"), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Cache-Control"), e.read()


@pytest.mark.parametrize("nombre,quien,metodo,ruta,cuerpo,estado", CASOS, ids=IDS)
def test_no_store_por_el_proxy(cliente, config_defecto, clave, nombre, quien, metodo, ruta, cuerpo,
                               estado):
    """`cliente` omite la prueba con el motivo de la M-8 si el proxy no responde."""
    config_defecto.modo_placas("normal")
    token = None
    if quien and cuerpo != "LOGIN":
        token = config_defecto.token(quien)
    if cuerpo == "LOGIN":
        cuerpo = {"usuario": quien, "clave": clave}
    est, cache, texto = _por_proxy(cliente.url_base, metodo, ruta, cuerpo, token)
    assert est == estado, (nombre, est, texto[:200])
    assert _no_store(cache), f"{nombre} por el proxy: Cache-Control = {cache!r}"
