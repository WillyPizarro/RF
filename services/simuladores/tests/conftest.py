"""Arnés de pruebas de caja negra de los simuladores (Sprint 0 + HU-08).

Interfaz observable: el API HTTP de `http://simuladores:8001`, solo dentro de la red de Docker
(SPRINT0 §5, M-1 E; CONTRATO-HU-08 v1, "Interfaz observable").

Tres formas de correr:

1. Dentro de la red (lo que pide el encargo):
       docker compose -f infra/docker-compose.yml run --rm simuladores pytest
   Peticiones directas a http://simuladores:8001. Las pruebas que leen archivos del repositorio
   (yaml de contratos, compose, Caddyfile, .env.example) se omiten: el contenedor no los tiene.

2. Desde el anfitrión, con el sistema arrancado (cubre TODO el contrato):
       pip install -r services/simuladores/tests/requirements-pruebas.txt
       pytest services/simuladores/tests --integracion
   Las peticiones salen desde DENTRO del contenedor `api` (`docker compose exec -T api python`),
   que es justo el camino que el contrato permite (sección 8, "Desde la API sí").

3. Igual que 2 más `--reinicio`: además reinicia `simuladores` para probar el determinismo de la
   semilla y que todas las fuentes arrancan en `normal`. Interrumpe el simulador unos segundos.

Solo biblioteca estándar más pytest en el contenedor; en el anfitrión, además, lo de
requirements-pruebas.txt (pyyaml, jsonschema, openapi-spec-validator).
"""

from __future__ import annotations

import base64
import json
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import pytest


def _buscar_raiz_repo() -> Path | None:
    """Raíz del repositorio (carpeta con infra/docker-compose.yml), o None dentro del contenedor."""
    for carpeta in Path(__file__).resolve().parents:
        if (carpeta / "infra" / "docker-compose.yml").is_file():
            return carpeta
    return None


RAIZ_REPO = _buscar_raiz_repo()
URL_SIMULADORES = "http://simuladores:8001"  # M-1 E
RUTA_SALUD = "/salud"
FUENTES = ("placas", "requisitorias-personas", "galeria")


def pytest_addoption(parser: pytest.Parser) -> None:
    g = parser.getgroup("simuladores")
    g.addoption(
        "--integracion",
        action="store_true",
        default=False,
        help="Hace las peticiones desde el anfitrión vía `docker compose exec api`.",
    )
    g.addoption(
        "--reinicio",
        action="store_true",
        default=False,
        help="Permite reiniciar el contenedor simuladores (determinismo y modos al arrancar).",
    )


# ---------------------------------------------------------------------------------------------
# Cliente HTTP. El mismo código corre local (red de Docker) o dentro del contenedor api.
# ---------------------------------------------------------------------------------------------

_TRABAJADOR = r'''
import base64, json, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

def _una(p):
    datos = None
    cab = {}
    if p.get("json") is not None:
        datos = json.dumps(p["json"]).encode("utf-8")
        cab["Content-Type"] = "application/json"
    req = urllib.request.Request(p["url"], data=datos, method=p.get("metodo", "GET"), headers=cab)
    t0 = time.monotonic()
    try:
        r = urllib.request.urlopen(req, timeout=p.get("timeout", 15))
        s, h, b = r.status, dict(r.headers.items()), r.read()
    except urllib.error.HTTPError as e:
        s, h, b = e.code, dict(e.headers.items()), e.read()
    except Exception as e:
        return {"s": None, "h": {}, "b": "", "t": time.monotonic() - t0, "error": repr(e)}
    t = time.monotonic() - t0
    if p.get("solo_200") and s != 200:
        b = b""
    return {"s": s, "h": h, "b": base64.b64encode(b).decode("ascii"), "t": t}

def ejecutar(peticiones, hilos=1):
    if hilos <= 1:
        return [_una(p) for p in peticiones]
    with ThreadPoolExecutor(max_workers=hilos) as ex:
        return list(ex.map(_una, peticiones))
'''

_ns: dict = {}
exec(_TRABAJADOR, _ns)  # noqa: S102 - código propio, el mismo que se manda al contenedor api


@dataclass
class Respuesta:
    estado: int | None
    cabeceras: dict[str, str]
    cuerpo: bytes
    segundos: float = 0.0
    error: str | None = None

    @property
    def texto(self) -> str:
        return self.cuerpo.decode("utf-8", errors="replace")

    def cabecera(self, nombre: str) -> str | None:
        return next((v for k, v in self.cabeceras.items() if k.lower() == nombre.lower()), None)

    def json(self) -> object:
        return json.loads(self.texto)


def _a_respuesta(d: dict) -> Respuesta:
    return Respuesta(d["s"], d["h"], base64.b64decode(d["b"]), d.get("t", 0.0), d.get("error"))


def _compose_base() -> list[str]:
    assert RAIZ_REPO is not None
    cmd = ["docker", "compose", "-f", str(RAIZ_REPO / "infra" / "docker-compose.yml")]
    env_file = RAIZ_REPO / "infra" / ".env"
    if env_file.exists():
        cmd += ["--env-file", str(env_file)]
    return cmd


def _ejecutar_en_api(peticiones: list[dict], hilos: int) -> list[dict]:
    if RAIZ_REPO is None:
        pytest.fail("--integracion necesita el repositorio: correr desde el anfitrión")
    script = (
        _TRABAJADOR
        + "\nps = json.loads(sys.stdin.read())\n"
        + f"sys.stdout.write(json.dumps(ejecutar(ps, {int(hilos)})))\n"
    )
    r = subprocess.run(
        _compose_base() + ["exec", "-T", "api", "python", "-c", script],
        input=json.dumps(peticiones), cwd=RAIZ_REPO, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=900,
    )
    assert r.returncode == 0, f"No se pudo ejecutar las peticiones desde api:\n{r.stderr[-2000:]}"
    return json.loads(r.stdout)


class Cliente:
    """Cliente de caja negra del simulador. Todas las rutas son relativas a URL_SIMULADORES."""

    def __init__(self, via_api: bool) -> None:
        self.via_api = via_api

    def _correr(self, peticiones: list[dict], hilos: int = 1) -> list[Respuesta]:
        for p in peticiones:
            p["url"] = URL_SIMULADORES + p.pop("ruta")
        crudo = (
            _ejecutar_en_api(peticiones, hilos) if self.via_api
            else _ns["ejecutar"](peticiones, hilos)
        )
        return [_a_respuesta(d) for d in crudo]

    def get(self, ruta: str, timeout: float = 15) -> Respuesta:
        return self._correr([{"ruta": ruta, "timeout": timeout}])[0]

    def put(self, ruta: str, cuerpo: object) -> Respuesta:
        return self._correr([{"ruta": ruta, "metodo": "PUT", "json": cuerpo}])[0]

    def lote_get(self, rutas: list[str], solo_200: bool = True, hilos: int = 32) -> list[Respuesta]:
        """Muchos GET en paralelo (para recorrer el espacio de placas y personas)."""
        return self._correr(
            [{"ruta": r, "solo_200": solo_200} for r in rutas], hilos=hilos
        )

    # Modos de falla (sección 5)
    def poner_modo(self, fuente: str, modo: str, latencia_ms: int | None = None) -> Respuesta:
        cuerpo: dict = {"modo": modo}
        if latencia_ms is not None:
            cuerpo["latencia_ms"] = latencia_ms
        return self.put(f"/control/modos/{fuente}", cuerpo)

    def todo_normal(self) -> None:
        for f in FUENTES:
            self.poner_modo(f, "normal")


_CLIENTES: list[Cliente] = []


@pytest.fixture(scope="session")
def cliente(pytestconfig: pytest.Config) -> Cliente:
    if pytestconfig.getoption("--integracion"):
        _CLIENTES.append(Cliente(via_api=True))
        return _CLIENTES[-1]
    try:
        ips = {a[4][0] for a in socket.getaddrinfo(urlparse(URL_SIMULADORES).hostname, 8001)}
    except OSError:
        pytest.skip(
            "El nombre 'simuladores' no resuelve: no se está en la red de Docker. "
            "Correr con docker compose run, o desde el anfitrión con --integracion."
        )
    # Con `docker compose run simuladores`, el contenedor de pruebas también lleva el alias
    # `simuladores` y el nombre puede resolver a sí mismo (donde no corre el servidor). Se usa
    # la dirección del servicio, que es la que no es propia.
    try:
        propias = {a[4][0] for a in socket.getaddrinfo(socket.gethostname(), None)}
    except OSError:
        propias = set()
    otras = sorted(ips - propias)
    if otras and len(otras) < len(ips):
        globals()["URL_SIMULADORES"] = f"http://{otras[0]}:8001"
    _CLIENTES.append(Cliente(via_api=False))
    return _CLIENTES[-1]


@pytest.fixture(scope="session")
def get_simuladores(cliente: Cliente):
    """Compatibilidad con las pruebas del Sprint 0: `get(ruta) -> Respuesta`."""
    return cliente.get


@pytest.fixture
def modos_limpios(cliente: Cliente):
    """Deja todas las fuentes en `normal` antes y después de la prueba."""
    cliente.todo_normal()
    yield cliente
    cliente.todo_normal()


@pytest.fixture(scope="session", autouse=True)
def _normal_al_terminar():
    """Pase lo que pase, la sesión no deja ninguna fuente en modo de falla."""
    yield
    if _CLIENTES:
        try:
            _CLIENTES[0].todo_normal()
        except BaseException:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------------------------
# Repositorio y anfitrión
# ---------------------------------------------------------------------------------------------

@pytest.fixture(scope="session")
def raiz_repo() -> Path:
    if RAIZ_REPO is None:
        pytest.skip("Lee archivos del repositorio: correr desde el anfitrión (pytest --integracion)")
    return RAIZ_REPO


@pytest.fixture(scope="session")
def solo_anfitrion(pytestconfig: pytest.Config, raiz_repo: Path) -> Path:
    """Para pruebas que necesitan docker en el anfitrión."""
    if not pytestconfig.getoption("--integracion"):
        pytest.skip("Necesita docker en el anfitrión: correr con --integracion")
    return raiz_repo


def compose(*args: str, timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(
        _compose_base() + list(args), cwd=RAIZ_REPO, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )


def esperar_salud(cli: Cliente, segundos: int = 90) -> None:
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        try:
            if cli.get(RUTA_SALUD, timeout=3).estado == 200:
                return
        except AssertionError:
            pass
        time.sleep(2)
    pytest.fail(f"simuladores no volvió a responder /salud en {segundos} s")


def leer_env_infra() -> dict[str, str]:
    """Variables de infra/.env (las del entorno del proceso tienen prioridad)."""
    import os  # noqa: PLC0415

    valores: dict[str, str] = {}
    if RAIZ_REPO is not None and (RAIZ_REPO / "infra" / ".env").is_file():
        for ln in (RAIZ_REPO / "infra" / ".env").read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                valores[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("SIM_FOTOS_ORIGEN", "SIM_FOTOS_LLAVE"):
        if os.environ.get(k) is not None:
            valores[k] = os.environ[k]
    return valores
