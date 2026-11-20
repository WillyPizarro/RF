"""CONTRATO-DESPLIEGUE-01 v1 — Lo que se ve del VPS desde afuera (fase B).

Se omite entero si no está `URL_VPS` (por ejemplo `URL_VPS=https://demo.ejemplo.pe`). No depende
de `--integracion`: el arnés deja correr este archivo sin esa opción.

    URL_VPS=https://<DOMINIO> CLAVE_USUARIOS_PRUEBA=<clave del VPS> pytest services/api/tests/test_despliegue_vps.py

- Puertos (§1): 22, 80 y 443 responden; 8000, 8001 y 5432, no.
- Certificado (§2): se valida con las CA del sistema (`ssl.create_default_context()`, sin
  desactivar la verificación) y lo emite Let's Encrypt.
- Salud y rutas (§1): `/v1/salud` → 200 con `bd` y `simuladores` en `ok`; `/openapi.json` y `/`
  → 404.
- Flujo (§1 "Mismo comportamiento"): login de agente1, las 3 placas del demo, la bitácora del
  supervisor con esas consultas, y el 403 por rol.

La clave de los usuarios se lee SOLO de la variable de entorno `CLAVE_USUARIOS_PRUEBA` y nunca
se escribe: no va en mensajes de error, en archivos ni en la salida. Las pruebas no mandan claves
incorrectas, para no sumar intentos al bloqueo de usuarios que se comparten en el demo.
"""

from __future__ import annotations

import json
import os
import socket
import ssl
import urllib.error
import urllib.request
from urllib.parse import urlencode, urlparse

import pytest

URL_VPS = os.environ.get("URL_VPS", "").rstrip("/")

pytestmark = pytest.mark.skipif(not URL_VPS, reason="Sin URL_VPS: la prueba contra el VPS se omite")

PLACAS = {"ZZA-101": "con_requisitoria", "ZZB-201": "sin_requisitoria",
          "ZZZ-999": "placa_no_registrada"}


def _host() -> str:
    return urlparse(URL_VPS).hostname or ""


class Resp:
    def __init__(self, estado, cabeceras, cuerpo):
        self.estado, self.cabeceras, self.cuerpo = estado, cabeceras, cuerpo

    def json(self):
        return json.loads(self.cuerpo.decode("utf-8"))


def pedir(metodo: str, ruta: str, cuerpo=None, token: str | None = None) -> Resp:
    """HTTPS con las CA del sistema (sin desactivar la verificación)."""
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    cab = {"Content-Type": "application/json"} if datos is not None else {}
    if token:
        cab["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(URL_VPS + ruta, data=datos, method=metodo, headers=cab)
    try:
        with urllib.request.urlopen(req, timeout=30, context=ssl.create_default_context()) as r:
            return Resp(r.status, dict(r.headers.items()), r.read())
    except urllib.error.HTTPError as e:
        return Resp(e.code, dict(e.headers.items()), e.read())


@pytest.fixture(scope="module")
def clave() -> str:
    valor = os.environ.get("CLAVE_USUARIOS_PRUEBA")
    if not valor:
        pytest.skip("Sin CLAVE_USUARIOS_PRUEBA en el entorno: el flujo con usuarios se omite")
    return valor


def _token(usuario: str, clave: str) -> str:
    r = pedir("POST", "/v1/auth/login", {"usuario": usuario, "clave": clave})
    # El mensaje de error nunca incluye la clave.
    assert r.estado == 200, f"login de {usuario}: {r.estado} {r.cuerpo[:200]!r}"
    return r.json()["token_acceso"]


# --- §1 Puertos ------------------------------------------------------------------------------

def _abierto(puerto: int) -> bool:
    try:
        with socket.create_connection((_host(), puerto), timeout=5):
            return True
    except OSError:
        return False


@pytest.mark.parametrize("puerto", [22, 80, 443])
def test_puertos_abiertos(puerto):
    """§1 'Puertos': responden 22 (SSH), 80 y 443."""
    assert _abierto(puerto), f"el puerto {puerto} no responde"


@pytest.mark.parametrize("puerto", [8000, 8001, 5432])
def test_puertos_cerrados(puerto):
    """§1 'Puertos': 8000 (api), 8001 (simuladores) y 5432 (Postgres) no responden."""
    assert not _abierto(puerto), f"el puerto {puerto} responde desde internet"


# --- §2 Certificado público ------------------------------------------------------------------

def test_certificado_valido_con_las_ca_del_sistema():
    """§2 'Verificación desde afuera': conecta con ssl.create_default_context() y el nombre del
    certificado coincide con el dominio; lo emite Let's Encrypt."""
    ctx = ssl.create_default_context()
    with socket.create_connection((_host(), 443), timeout=10) as s:
        with ctx.wrap_socket(s, server_hostname=_host()) as tls:
            cert = tls.getpeercert()
    emisor = {k: v for par in cert.get("issuer", ()) for k, v in par}
    assert "Let's Encrypt" in emisor.get("organizationName", ""), emisor


def test_http_80_lleva_a_https():
    """§2: el puerto 80 lo usa Caddy para Let's Encrypt y para redirigir a HTTPS."""
    url = URL_VPS.replace("https://", "http://", 1) + "/v1/salud"

    class SinSeguir(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    abridor = urllib.request.build_opener(SinSeguir)
    try:
        r = abridor.open(url, timeout=15)
        estado, destino = r.status, r.headers.get("Location", "")
    except urllib.error.HTTPError as e:
        estado, destino = e.code, e.headers.get("Location", "")
    assert estado in (301, 302, 307, 308) and destino.startswith("https://"), (estado, destino)


# --- §1 Salud y solo /v1/* -------------------------------------------------------------------

def test_salud():
    """§1 'Salud': 200 con bd y simuladores en ok."""
    r = pedir("GET", "/v1/salud")
    assert r.estado == 200, r.cuerpo[:300]
    d = r.json()
    assert d.get("bd") == "ok" and d.get("simuladores") == "ok", d


@pytest.mark.parametrize("ruta", ["/openapi.json", "/"])
def test_solo_v1(ruta):
    """§1 'Solo /v1/*': /openapi.json y / → 404."""
    assert pedir("GET", ruta).estado == 404


# --- §1 Mismo comportamiento: el flujo del demo ----------------------------------------------

def test_flujo_del_demo(clave):
    """Login de agente1; las 3 placas con motivo dan su resultado (nunca sin_requisitoria para
    ZZZ-999); el supervisor ve esas consultas en la bitácora."""
    tok = _token("agente1", clave)
    ids = {}
    for placa, resultado in PLACAS.items():
        r = pedir("POST", "/v1/consultas/placa",
                  {"placa": placa, "motivo_codigo": "control_vehicular", "motivo_texto": None}, tok)
        assert r.estado == 200, (placa, r.estado, r.cuerpo[:300])
        assert r.json()["resultado"] == resultado, (placa, r.json())
        ids[placa] = r.json()["consulta_id"]
    sup = _token("supervisor1", clave)
    q = urlencode({"usuario": "agente1", "tipo": "CONSULTA_PLACA", "limite": 100})
    r = pedir("GET", f"/v1/bitacora?{q}", token=sup)
    assert r.estado == 200, r.cuerpo[:300]
    vistos = {str(reg.get("consulta_id")) for reg in r.json()["registros"]}
    faltan = {p for p, i in ids.items() if str(i) not in vistos}
    assert not faltan, f"la bitácora no muestra las consultas de {sorted(faltan)}"


@pytest.mark.parametrize("usuario,metodo,ruta,cuerpo", [
    ("revisor1", "POST", "/v1/consultas/placa",
     {"placa": "ZZA-101", "motivo_codigo": "control_vehicular", "motivo_texto": None}),
    ("agente1", "GET", "/v1/bitacora", None),
])
def test_403_por_rol(clave, usuario, metodo, ruta, cuerpo):
    """CONTRATO-HU-02 §2 en el VPS: una ruta de otro rol → 403 SIN_PERMISO."""
    r = pedir(metodo, ruta, cuerpo, _token(usuario, clave))
    assert r.estado == 403, (r.estado, r.cuerpo[:300])
    assert r.json().get("codigo") == "SIN_PERMISO"
