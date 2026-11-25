"""CONTRATO-DESPLIEGUE-01 v2.1 — NGINX en el compose local ("Qué prueba quién", primera fila).

Caja negra contra el proxy local (`--url-base`, por defecto `https://localhost:<PROXY_PUERTO_HTTPS>`,
y `http://localhost:<PROXY_PUERTO_HTTP>`) y la CLI de docker compose. Se corre con el sistema
arrancado:

    pytest services/api/tests/test_proxy_nginx.py --integracion

Qué cubre:
- §1 "Solo /v1/* y el APK": cualquier otra ruta → 404.
- §2: HTTP → HTTPS (301 o 308), solo TLS 1.2 y 1.3, `Strict-Transport-Security` y
  `X-Content-Type-Options: nosniff` en **toda** respuesta por HTTPS, `413` sobre 5 MB y un cuerpo
  menor que sí llega a la API, la imagen `nginx` con versión fijada y sin Caddy.
- §5: la ruta `/descargas/movil-buscador.apk` con un **archivo de prueba** (bytes aleatorios, no un
  APK; decisión 7): `401` con `WWW-Authenticate: Basic` sin credencial o con una incorrecta, `200`
  con el mismo SHA-256 con la credencial, `404` en el resto de `/descargas/` (también con
  credencial), la redirección por HTTP antes de pedir la credencial, el volumen de solo lectura y
  la credencial fuera de los logs del proxy.

La credencial se lee de `DESCARGA_APK_USUARIO` y `DESCARGA_APK_CLAVE` de `infra/.env` y **nunca**
se escribe: no va en mensajes, ni en archivos, ni en la salida. La carpeta del volumen sale de
`DESCARGA_APK_DIR` de `infra/.env` (relativa a `infra/` o absoluta); la prueba deja ahí
`movil-buscador.apk` y al terminar devuelve lo que había antes.
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import os
import re
import secrets
import socket
import ssl
from pathlib import Path
from urllib.parse import urlparse

import pytest

from conftest import CABECERA_TRAZA, ENV_FILE, RUTA_SALUD, _env_infra

RUTA_APK = "/descargas/movil-buscador.apk"
LIMITE_CUERPO = 5 * 1024 * 1024  # client_max_body_size 5m (§2)


# --- Cliente sin redirecciones ---------------------------------------------------------------

class Resp:
    def __init__(self, estado: int, cabeceras: dict[str, str], cuerpo: bytes) -> None:
        self.estado, self.cuerpo = estado, cuerpo
        self.cabeceras = {k.lower(): v for k, v in cabeceras.items()}

    def cab(self, nombre: str) -> str:
        return self.cabeceras.get(nombre.lower(), "")


def _contexto_local() -> ssl.SSLContext:
    """La CA local de NGINX no está en el almacén de esta PC: no se verifica (como `cliente`)."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def pedir(url: str, metodo: str = "GET", cabeceras: dict[str, str] | None = None,
          cuerpo: bytes | None = None, timeout: float = 30.0) -> Resp:
    """Una solicitud, sin seguir redirecciones."""
    u = urlparse(url)
    if u.scheme == "https":
        con = http.client.HTTPSConnection(u.hostname, u.port or 443, timeout=timeout,
                                          context=_contexto_local())
    else:
        con = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=timeout)
    try:
        con.request(metodo, u.path + (f"?{u.query}" if u.query else ""), body=cuerpo,
                    headers=cabeceras or {})
        r = con.getresponse()
        return Resp(r.status, dict(r.getheaders()), r.read())
    finally:
        con.close()


def basica(usuario: str, clave: str) -> dict[str, str]:
    return {"Authorization": "Basic " + base64.b64encode(f"{usuario}:{clave}".encode()).decode()}


# --- Fixtures --------------------------------------------------------------------------------

@pytest.fixture
def https(sistema_sano) -> str:
    return sistema_sano.url_base


@pytest.fixture(scope="module")
def http_base() -> str:
    puerto = _env_infra().get("PROXY_PUERTO_HTTP") or "80"
    return f"http://localhost:{puerto}"


@pytest.fixture(scope="module")
def credencial() -> tuple[str, str]:
    env = _env_infra()
    usuario, clave = env.get("DESCARGA_APK_USUARIO", ""), env.get("DESCARGA_APK_CLAVE", "")
    assert usuario and clave, ("infra/.env no define DESCARGA_APK_USUARIO y DESCARGA_APK_CLAVE "
                               "(§5, nombres que no se negocian)")
    return usuario, clave


@pytest.fixture(scope="module")
def carpeta_apk() -> Path:
    valor = _env_infra().get("DESCARGA_APK_DIR", "")
    assert valor, ("infra/.env no define DESCARGA_APK_DIR: la carpeta del volumen de la descarga "
                   "en local (decisión 7; contrato v2.1, anotación 1cb361a)")
    ruta = Path(valor)
    if not ruta.is_absolute():
        ruta = (ENV_FILE.parent / ruta).resolve()
    assert ruta.is_dir(), f"no existe la carpeta del volumen de la descarga: {ruta}"
    return ruta


@pytest.fixture(scope="module")
def archivo_de_prueba(carpeta_apk: Path):
    """Deja en el volumen un archivo de prueba (bytes aleatorios, no un APK) y devuelve su SHA-256.
    Al terminar, devuelve el volumen a como estaba."""
    destino = carpeta_apk / "movil-buscador.apk"
    previo = destino.read_bytes() if destino.exists() else None
    datos = b"ARCHIVO DE PRUEBA DEL TESTER - NO ES UN APK\n" + secrets.token_bytes(256 * 1024)
    destino.write_bytes(datos)
    try:
        yield hashlib.sha256(datos).hexdigest(), len(datos)
    finally:
        if previo is None:
            destino.unlink(missing_ok=True)
        else:
            destino.write_bytes(previo)


# --- §1 Solo /v1/* y el APK ------------------------------------------------------------------

FUERA = ["/", "/openapi.json", "/docs", "/v2/salud", "/salud", "/descargas", "/descargas/",
         "/descargas/otro.apk", "/descargas/movil-buscador.apk/", "/descargas/movil-buscador.APK",
         "/descargas/sub/movil-buscador.apk"]


@pytest.mark.parametrize("ruta", FUERA)
def test_rutas_fuera_de_v1_y_del_apk_dan_404(https, ruta):
    """§1 'Solo /v1/* y el APK' y §5 'Otras rutas' → 404."""
    r = pedir(https + ruta)
    assert r.estado == 404, (ruta, r.estado)


@pytest.mark.parametrize("ruta", [x for x in FUERA if x.startswith("/descargas")])
def test_otras_rutas_de_descargas_dan_404_tambien_con_credencial(https, credencial, ruta):
    """§5 'Otras rutas': 404 también con credencial (no se lista ni se sirve otra cosa)."""
    r = pedir(https + ruta, cabeceras=basica(*credencial))
    assert r.estado == 404, (ruta, r.estado)


def test_v1_sigue_llegando_a_la_api(https):
    """§1: `/v1/` → api. La salud responde 200 con la cabecera de traza de la API."""
    r = pedir(https + RUTA_SALUD)
    assert r.estado == 200
    assert r.cab(CABECERA_TRAZA), "la respuesta no trae la cabecera de traza de la API"


# --- §2 HTTP → HTTPS -------------------------------------------------------------------------

@pytest.mark.parametrize("ruta", [RUTA_SALUD, RUTA_APK])
def test_http_redirige_a_https(http_base, ruta):
    """§2 'HTTP → HTTPS' y §5 'Solo por HTTPS': 301 o 308 a https://, sin pedir la credencial
    por HTTP (no hay WWW-Authenticate en la respuesta por HTTP)."""
    r = pedir(http_base + ruta)
    assert r.estado in (301, 308), (ruta, r.estado)
    destino = r.cab("Location")
    assert destino.startswith("https://"), (ruta, destino)
    assert destino.endswith(ruta), (ruta, destino)
    assert not r.cab("WWW-Authenticate"), "la credencial se pide por HTTP"


# --- §2 Solo TLS 1.2 y 1.3 -------------------------------------------------------------------

def _saludo(https: str, version: ssl.TLSVersion) -> str | None:
    """Intenta el saludo TLS solo con `version`. None si completa; el error, si no."""
    u = urlparse(https)
    ctx = _contexto_local()
    ctx.minimum_version = ctx.maximum_version = version
    if version < ssl.TLSVersion.TLSv1_2:
        ctx.set_ciphers("DEFAULT:@SECLEVEL=0")  # que el cliente sí ofrezca la versión vieja
    try:
        with socket.create_connection((u.hostname, u.port or 443), timeout=10) as s:
            with ctx.wrap_socket(s, server_hostname=u.hostname):
                return None
    except ssl.SSLError as e:
        return str(e)


@pytest.mark.parametrize("version", [ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_3])
def test_tls_12_y_13_completan(https, version):
    """§2 'Solo TLS 1.2 y 1.3': las dos completan el saludo."""
    assert _saludo(https, version) is None, version


@pytest.mark.parametrize("version", [ssl.TLSVersion.TLSv1, ssl.TLSVersion.TLSv1_1])
def test_tls_10_y_11_no_completan(https, version):
    """§2: un cliente que fuerza TLS 1.0 o 1.1 no completa el saludo. Si el OpenSSL de esta PC
    no puede ni ofrecer esa versión, no se puede probar (no se da por verde)."""
    error = _saludo(https, version)
    if error and re.search(r"NO_PROTOCOLS_AVAILABLE|no protocols available", error, re.I):
        pytest.skip(f"NO VERIFICADO (entorno): el OpenSSL local no ofrece {version.name}")
    assert error is not None, f"el proxy aceptó {version.name}"


# --- §2 Cabeceras de seguridad en toda respuesta por HTTPS -----------------------------------

def _respuestas_variadas(https: str) -> dict[str, Resp]:
    return {
        "200 salud": pedir(https + RUTA_SALUD),
        "404 fuera de /v1": pedir(https + "/no-existe"),
        "401 descarga sin credencial": pedir(https + RUTA_APK),
        "error de la API": pedir(https + "/v1/auth/login", "POST",
                                 {"Content-Type": "application/json"}, b"{}"),
        "413 cuerpo grande": pedir(https + "/v1/auth/login", "POST",
                                   {"Content-Type": "application/json"},
                                   b" " * (LIMITE_CUERPO + 64 * 1024)),
    }


def test_cabeceras_de_seguridad_en_toda_respuesta(https):
    """§2 'Cabeceras de seguridad': Strict-Transport-Security y X-Content-Type-Options: nosniff
    en toda respuesta por HTTPS, también en los errores del proxy (404, 401, 413)."""
    faltan = []
    for nombre, r in _respuestas_variadas(https).items():
        if not r.cab("Strict-Transport-Security"):
            faltan.append(f"{nombre} ({r.estado}): sin Strict-Transport-Security")
        if r.cab("X-Content-Type-Options").strip().lower() != "nosniff":
            faltan.append(f"{nombre} ({r.estado}): X-Content-Type-Options={r.cab('X-Content-Type-Options')!r}")
    assert not faltan, faltan


# --- §2 Cuerpo máximo ------------------------------------------------------------------------

def test_cuerpo_de_mas_de_5_mb_recibe_413_del_proxy(https):
    """§2 'Cuerpo máximo': más de 5 MB → 413 del proxy (no llega a la API: sin traza)."""
    r = pedir(https + "/v1/auth/login", "POST", {"Content-Type": "application/json"},
              b" " * (LIMITE_CUERPO + 64 * 1024))
    assert r.estado == 413, r.estado
    assert not r.cab(CABECERA_TRAZA), "el 413 vino de la API, no del proxy"


def test_cuerpo_de_menos_de_5_mb_llega_a_la_api(https):
    """§2: un cuerpo de menos de 5 MB llega a la API (responde ella, con su traza)."""
    r = pedir(https + "/v1/auth/login", "POST", {"Content-Type": "application/json"},
              b" " * (LIMITE_CUERPO - 64 * 1024))
    assert r.estado != 413, "el proxy cortó un cuerpo de menos de 5 MB"
    assert r.cab(CABECERA_TRAZA), f"la respuesta ({r.estado}) no vino de la API"


# --- §5 Descarga del APK ---------------------------------------------------------------------

def test_descarga_sin_credencial_401_con_basic(https, archivo_de_prueba):
    """§5 'Sin credencial' → 401 con WWW-Authenticate: Basic."""
    r = pedir(https + RUTA_APK)
    assert r.estado == 401, r.estado
    assert r.cab("WWW-Authenticate").lower().startswith("basic"), r.cab("WWW-Authenticate")


@pytest.mark.parametrize("cual", ["usuario", "clave", "las dos"])
def test_descarga_con_credencial_incorrecta_401(https, credencial, archivo_de_prueba, cual):
    """§5 'Credencial incorrecta' → 401."""
    usuario, clave = credencial
    otra = "x-" + secrets.token_hex(8)
    u = otra if cual in ("usuario", "las dos") else usuario
    c = otra if cual in ("clave", "las dos") else clave
    r = pedir(https + RUTA_APK, cabeceras=basica(u, c))
    assert r.estado == 401, (cual, r.estado)
    assert hashlib.sha256(r.cuerpo).hexdigest() != archivo_de_prueba[0], "sirvió el archivo"


def test_descarga_con_credencial_200_y_mismo_sha256(https, credencial, archivo_de_prueba):
    """§5 'Con credencial' → 200 y el cuerpo es exactamente el archivo del volumen."""
    sha, tam = archivo_de_prueba
    r = pedir(https + RUTA_APK, cabeceras=basica(*credencial))
    assert r.estado == 200, r.estado
    assert len(r.cuerpo) == tam, (len(r.cuerpo), tam)
    assert hashlib.sha256(r.cuerpo).hexdigest() == sha, "el cuerpo no es el archivo publicado"


def test_volumen_de_la_descarga_es_de_solo_lectura(compose, carpeta_apk):
    """§5 'Ruta exacta': el archivo sale de un volumen de solo lectura del contenedor proxy."""
    proxy = compose.config_json()["services"]["proxy"]
    montajes = [v for v in proxy.get("volumes") or [] if isinstance(v, dict)
                and Path(str(v.get("source", ""))).resolve() == carpeta_apk]
    assert montajes, f"el proxy no monta {carpeta_apk}: {proxy.get('volumes')}"
    assert all(v.get("read_only") for v in montajes), montajes


def test_la_credencial_de_la_descarga_no_queda_en_los_logs_del_proxy(
        https, compose, credencial, archivo_de_prueba):
    """§5 'La clave no queda en los logs': después de descargar con credencial (y de un intento
    con una clave incorrecta), los logs del proxy no tienen la clave, ni la cabecera
    Authorization, ni el valor Basic codificado."""
    usuario, clave = credencial
    mala = "mala-" + secrets.token_hex(8)
    assert pedir(https + RUTA_APK, cabeceras=basica(*credencial)).estado == 200
    assert pedir(https + RUTA_APK, cabeceras=basica(usuario, mala)).estado == 401
    logs = compose.logs("proxy")
    problemas = []
    if clave in logs:
        problemas.append("la clave de la descarga")
    if mala in logs:
        problemas.append("la clave incorrecta")
    for valor in (basica(*credencial), basica(usuario, mala)):
        if valor["Authorization"].split(" ", 1)[1] in logs:
            problemas.append("el valor Basic codificado")
    if re.search(r"authorization\s*[:=]", logs, re.I):
        problemas.append("la cabecera Authorization")
    assert not problemas, f"en los logs del proxy aparece: {problemas}"  # sin imprimir valores


# --- §2 Caddy desaparece; imagen fijada -------------------------------------------------------

def test_proxy_es_nginx_con_version_fijada(compose):
    """§1 'Servicios': el proxy usa la imagen oficial nginx con una versión fijada (ni `latest`
    ni sin etiqueta); ningún servicio usa caddy."""
    servicios = compose.config_json()["services"]
    imagen = str(servicios["proxy"].get("image", ""))
    m = re.fullmatch(r"(?:docker\.io/)?(?:library/)?nginx:([^@\s]+)(?:@sha256:[0-9a-f]{64})?", imagen)
    assert m, f"el proxy no usa la imagen oficial nginx: {imagen!r}"
    assert m.group(1) not in ("latest", "stable", "mainline"), f"versión no fijada: {imagen}"
    con_caddy = [n for n, s in servicios.items() if "caddy" in str(s.get("image", "")).lower()]
    assert not con_caddy, con_caddy


def test_no_queda_el_caddyfile():
    """§2 'Caddy desaparece': infra/Caddyfile ya no existe."""
    assert not (ENV_FILE.parent / "Caddyfile").exists()
