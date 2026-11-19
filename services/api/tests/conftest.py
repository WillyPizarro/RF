"""Arnés de pruebas de caja negra del esqueleto (Sprint 0).

Las pruebas de esta carpeta hablan con el sistema solo por su interfaz observable:
HTTP a través del proxy (https://localhost) y la CLI de docker compose. No importan
código de la API.

Se corren desde la raíz del repositorio, con el sistema arrancado:

    pytest services/api/tests --integracion

Sin `--integracion` (por ejemplo, dentro del contenedor con
`docker compose ... run --rm api pytest`) quedan omitidas: necesitan el sistema
completo y la CLI de docker del anfitrión.

Solo usa la biblioteca estándar más pytest, para no depender de lo que instale el DEV.
"""

from __future__ import annotations

import json
import os
import ssl
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import pytest

def _buscar_raiz_repo() -> Path | None:
    """Raíz del repositorio (carpeta con infra/docker-compose.yml), o None si no está.

    Dentro del contenedor (`/app/tests`) la estructura del repositorio no existe: el arnés
    debe cargar igual y omitir lo que la necesita.
    """
    for carpeta in Path(__file__).resolve().parents:
        if (carpeta / "infra" / "docker-compose.yml").is_file():
            return carpeta
    return None


RAIZ_REPO = _buscar_raiz_repo()
COMPOSE_FILE = RAIZ_REPO / "infra" / "docker-compose.yml" if RAIZ_REPO else None
ENV_FILE = RAIZ_REPO / "infra" / ".env" if RAIZ_REPO else None

# Nombres exactos de SPRINT0.md §5 y M-1 (no se negocian).
RUTA_SALUD = "/v1/salud"
CABECERA_TRAZA = "X-Id-Traza"
URL_API_INTERNA = "http://api:8000"  # M-1 E
URL_SIMULADORES_INTERNA = "http://simuladores:8001"  # M-1 E


def pytest_addoption(parser: pytest.Parser) -> None:
    grupo = parser.getgroup("esqueleto")
    grupo.addoption(
        "--integracion",
        action="store_true",
        default=False,
        help="Corre las pruebas contra el sistema arrancado (proxy + docker compose).",
    )
    grupo.addoption(
        "--url-base",
        default=os.environ.get("URL_BASE_PRUEBAS", "https://localhost"),
        help="URL pública del proxy (por defecto https://localhost).",
    )
    grupo.addoption(
        "--espera-max",
        type=float,
        default=90.0,
        help="Segundos máximos para esperar que un servicio vuelva a estar sano.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "disruptiva: detiene y vuelve a levantar servicios del compose"
    )


_ORDEN_CONFIG = {"config_defecto": 0, "config_corta": 1, "config_token_corto": 2}


def _orden_config(item: pytest.Item) -> int:
    nombres = getattr(item, "fixturenames", ())
    return max((v for k, v in _ORDEN_CONFIG.items() if k in nombres), default=0)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    # HU-01: agrupa por configuración de la API para recrearla las menos veces posible
    # (orden estable: dentro de cada grupo se respeta el orden de los archivos).
    items.sort(key=_orden_config)
    if config.getoption("--integracion"):
        return
    omitir = pytest.mark.skip(
        reason="Requiere el sistema arrancado y la CLI de docker: correr con --integracion"
    )
    for item in items:
        if Path(str(item.fspath)).resolve().is_relative_to(Path(__file__).parent):
            item.add_marker(omitir)


# --------------------------------------------------------------------------- HTTP


@dataclass
class Respuesta:
    estado: int
    cabeceras: dict[str, str]
    texto: str
    _json: object = field(default=None, repr=False)

    def cabecera(self, nombre: str) -> str | None:
        for clave, valor in self.cabeceras.items():
            if clave.lower() == nombre.lower():
                return valor
        return None

    def json(self) -> object:
        if self._json is None:
            self._json = json.loads(self.texto)
        return self._json


class ClienteHttp:
    """Cliente mínimo sobre urllib. El TLS local de Caddy usa una CA propia: no se verifica."""

    def __init__(self, url_base: str) -> None:
        self.url_base = url_base.rstrip("/")
        self._ssl = ssl.create_default_context()
        self._ssl.check_hostname = False
        self._ssl.verify_mode = ssl.CERT_NONE

    def get(self, ruta: str, timeout: float = 10.0) -> Respuesta:
        return self.pedir("GET", ruta, timeout=timeout)

    def pedir(
        self, metodo: str, ruta: str, cuerpo: bytes | None = None, timeout: float = 10.0
    ) -> Respuesta:
        cabeceras = {"Content-Type": "application/json"} if cuerpo is not None else {}
        pedido = urllib.request.Request(
            self.url_base + ruta, data=cuerpo, method=metodo, headers=cabeceras
        )
        try:
            with urllib.request.urlopen(pedido, timeout=timeout, context=self._ssl) as r:
                return Respuesta(r.status, dict(r.headers.items()), r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return Respuesta(e.code, dict(e.headers.items()), e.read().decode("utf-8"))


@pytest.fixture(scope="session")
def cliente(pytestconfig: pytest.Config) -> ClienteHttp:
    return ClienteHttp(pytestconfig.getoption("--url-base"))


# ------------------------------------------------------------------ docker compose


class Compose:
    def __init__(self, espera_max: float) -> None:
        self.espera_max = espera_max

    def _base(self) -> list[str]:
        cmd = ["docker", "compose", "-f", str(COMPOSE_FILE)]
        # ENCARGO-HU-01-02 regla 7: siempre con el montaje de fotos, para no recrear
        # `simuladores` sin él (lección del veredicto de HU-08).
        fotos = COMPOSE_FILE.parent / "docker-compose.fotos.yml"
        if fotos.is_file():
            cmd += ["-f", str(fotos)]
        if ENV_FILE is not None and ENV_FILE.exists():
            cmd += ["--env-file", str(ENV_FILE)]
        return cmd

    def correr(self, *args: str, timeout: float = 120.0) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            self._base() + list(args),
            cwd=RAIZ_REPO,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )

    def config_json(self) -> dict:
        r = self.correr("config", "--format", "json")
        assert r.returncode == 0, f"docker compose config falló:\n{r.stderr}"
        return json.loads(r.stdout)

    def detener(self, servicio: str) -> None:
        r = self.correr("stop", servicio)
        assert r.returncode == 0, f"No se pudo detener {servicio}:\n{r.stderr}"

    def iniciar(self, servicio: str) -> None:
        r = self.correr("start", servicio)
        assert r.returncode == 0, f"No se pudo iniciar {servicio}:\n{r.stderr}"

    def get_en_red(self, url: str, desde: str = "api") -> Respuesta:
        """GET dentro de la red de Docker, ejecutado en el contenedor `desde` con su Python."""
        script = (
            "import json,sys,urllib.request,urllib.error\n"
            "try:\n"
            f"    r=urllib.request.urlopen({url!r},timeout=10); s,h,b=r.status,dict(r.headers),r.read()\n"
            "except urllib.error.HTTPError as e:\n"
            "    s,h,b=e.code,dict(e.headers),e.read()\n"
            "sys.stdout.write(json.dumps({'s':s,'h':h,'b':b.decode('utf-8')}))\n"
        )
        r = self.correr("exec", "-T", desde, "python", "-c", script)
        assert r.returncode == 0, f"No se pudo hacer GET {url} desde {desde}:\n{r.stderr}"
        datos = json.loads(r.stdout)
        return Respuesta(datos["s"], datos["h"], datos["b"])

    def logs(self, servicio: str) -> str:
        r = self.correr("logs", "--no-color", "--no-log-prefix", servicio)
        assert r.returncode == 0, f"No se pudieron leer los logs de {servicio}:\n{r.stderr}"
        return r.stdout + r.stderr


@pytest.fixture(scope="session")
def compose(pytestconfig: pytest.Config) -> Compose:
    if COMPOSE_FILE is None:
        pytest.fail(
            "No se encontró infra/docker-compose.yml subiendo desde services/api/tests: "
            "correr desde el repositorio en el anfitrión"
        )
    return Compose(pytestconfig.getoption("--espera-max"))


def esperar_salud_ok(cliente: ClienteHttp, espera_max: float) -> Respuesta:
    """Espera hasta que GET /v1/salud responda 200. Devuelve la última respuesta."""
    limite = time.monotonic() + espera_max
    ultima: Respuesta | None = None
    while time.monotonic() < limite:
        try:
            ultima = cliente.get(RUTA_SALUD, timeout=5)
            if ultima.estado == 200:
                return ultima
        except OSError:
            pass
        time.sleep(2)
    pytest.fail(f"/v1/salud no volvió a 200 en {espera_max}s (última: {ultima})")


def esperar_salud(cliente: ClienteHttp, estado: int, espera_max: float) -> Respuesta:
    """Espera hasta que GET /v1/salud responda el estado pedido."""
    limite = time.monotonic() + espera_max
    ultima: Respuesta | None = None
    while time.monotonic() < limite:
        try:
            ultima = cliente.get(RUTA_SALUD, timeout=10)
            if ultima.estado == estado:
                return ultima
        except OSError:
            pass
        time.sleep(2)
    pytest.fail(f"/v1/salud no respondió {estado} en {espera_max}s (última: {ultima})")


@pytest.fixture
def sistema_sano(cliente: ClienteHttp, pytestconfig: pytest.Config) -> ClienteHttp:
    """Precondición (Given): el sistema completo responde salud 200."""
    esperar_salud_ok(cliente, pytestconfig.getoption("--espera-max"))
    return cliente


# ------------------------------------------------------------------- secretos


PALABRAS_SECRETAS = ("PASSWORD", "SECRET", "KEY", "TOKEN", "DATABASE_URL", "PASS", "JWT")


def valores_secretos() -> dict[str, str]:
    """Valores de infra/.env cuyos nombres indican un secreto (más DATABASE_URL)."""
    if ENV_FILE is None or not ENV_FILE.exists():
        return {}
    secretos: dict[str, str] = {}
    for linea in ENV_FILE.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        nombre, valor = linea.split("=", 1)
        nombre = nombre.strip().removeprefix("export ").strip()
        valor = valor.strip().strip('"').strip("'")
        if len(valor) < 6:
            continue  # valores triviales generan falsos positivos
        if any(p in nombre.upper() for p in PALABRAS_SECRETAS):
            secretos[nombre] = valor
    # La contraseña embebida en DATABASE_URL también es secreta por sí sola.
    url = secretos.get("DATABASE_URL")
    if url and "://" in url and "@" in url:
        credenciales = url.split("://", 1)[1].rsplit("@", 1)[0]
        if ":" in credenciales:
            clave = credenciales.split(":", 1)[1]
            if len(clave) >= 6:
                secretos["DATABASE_URL (contraseña)"] = clave
    return secretos


# ------------------------------------------------------ HU-01 / HU-02 (red interna)

# Configuraciones cortas para probar tiempos sin esperar 10 o 15 minutos. Los valores por
# defecto del contrato (600/900/5/900) se prueban con infra/.env sin cambios.
CONFIG_CORTA = {  # inactividad y bloqueo cortos; el token dura más que la inactividad
    "SESION_INACTIVIDAD_S": "12",
    "TOKEN_ACCESO_VIGENCIA_S": "120",
    "BLOQUEO_INTENTOS": "5",
    "BLOQUEO_DURACION_S": "12",
}
CONFIG_TOKEN_CORTO = {  # el token de acceso vence antes que la inactividad
    "SESION_INACTIVIDAD_S": "600",
    "TOKEN_ACCESO_VIGENCIA_S": "6",
    "BLOQUEO_INTENTOS": "5",
    "BLOQUEO_DURACION_S": "900",
}


@pytest.fixture(scope="session")
def sistema(pytestconfig: pytest.Config):
    """API por la red interna + bitácora + configuración. Al final vuelve a infra/.env."""
    from red_interna import Sistema

    if RAIZ_REPO is None:
        pytest.fail("Correr desde el anfitrión: pytest services/api/tests --integracion")
    s = Sistema(RAIZ_REPO, pytestconfig.getoption("--espera-max"))
    s.esperar_api()
    yield s
    if s.overrides_actuales:
        s.configurar({})


@pytest.fixture
def config_defecto(sistema):
    sistema.configurar({})
    return sistema


@pytest.fixture
def config_corta(sistema):
    sistema.configurar(CONFIG_CORTA)
    return sistema


@pytest.fixture
def config_token_corto(sistema):
    sistema.configurar(CONFIG_TOKEN_CORTO)
    return sistema


@pytest.fixture(scope="session")
def clave(sistema) -> str:
    return sistema.clave_pruebas()
