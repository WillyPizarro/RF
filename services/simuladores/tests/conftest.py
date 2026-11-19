"""Arnés de pruebas de caja negra de los simuladores (Sprint 0).

Interfaz observable (SPRINT0.md §5 + M-1 E): `GET /salud` en `http://simuladores:8001`,
solo dentro de la red de Docker.

Dos formas de correr:

1. Dentro de la red (criterio 11):
       docker compose -f infra/docker-compose.yml run --rm simuladores pytest
   Hace GET directo a http://simuladores:8001/salud. Si el nombre `simuladores` no
   resuelve (no se está en la red de Docker) la prueba se omite con el motivo.

2. Desde el anfitrión, con el sistema arrancado:
       pytest services/simuladores/tests --integracion
   Hace el GET desde dentro del contenedor `api` con `docker compose exec`.

Solo biblioteca estándar más pytest.
"""

from __future__ import annotations

import json
import socket
import subprocess
import urllib.error
import urllib.request
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


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.getgroup("esqueleto").addoption(
        "--integracion",
        action="store_true",
        default=False,
        help="Hace el GET desde el anfitrión vía `docker compose exec api`.",
    )


@dataclass
class Respuesta:
    estado: int
    cabeceras: dict[str, str]
    texto: str

    def cabecera(self, nombre: str) -> str | None:
        return next((v for k, v in self.cabeceras.items() if k.lower() == nombre.lower()), None)

    def json(self) -> object:
        return json.loads(self.texto)


def _get_directo(url: str) -> Respuesta:
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return Respuesta(r.status, dict(r.headers.items()), r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return Respuesta(e.code, dict(e.headers.items()), e.read().decode("utf-8"))


def _get_via_compose(url: str) -> Respuesta:
    if RAIZ_REPO is None:
        pytest.fail(
            "--integracion necesita el repositorio (infra/docker-compose.yml): "
            "correr desde el anfitrión"
        )
    env_file = RAIZ_REPO / "infra" / ".env"
    cmd = ["docker", "compose", "-f", str(RAIZ_REPO / "infra" / "docker-compose.yml")]
    if env_file.exists():
        cmd += ["--env-file", str(env_file)]
    script = (
        "import json,sys,urllib.request,urllib.error\n"
        "try:\n"
        f"    r=urllib.request.urlopen({url!r},timeout=10); s,h,b=r.status,dict(r.headers),r.read()\n"
        "except urllib.error.HTTPError as e:\n"
        "    s,h,b=e.code,dict(e.headers),e.read()\n"
        "sys.stdout.write(json.dumps({'s':s,'h':h,'b':b.decode('utf-8')}))\n"
    )
    r = subprocess.run(
        cmd + ["exec", "-T", "api", "python", "-c", script],
        cwd=RAIZ_REPO, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=60,
    )
    assert r.returncode == 0, f"No se pudo hacer GET {url} desde api:\n{r.stderr}"
    d = json.loads(r.stdout)
    return Respuesta(d["s"], d["h"], d["b"])


@pytest.fixture(scope="session")
def get_simuladores(pytestconfig: pytest.Config):
    """Devuelve una función `get(ruta) -> Respuesta` contra los simuladores."""
    if pytestconfig.getoption("--integracion"):
        return lambda ruta: _get_via_compose(URL_SIMULADORES + ruta)
    try:
        socket.getaddrinfo(urlparse(URL_SIMULADORES).hostname, None)
    except OSError:
        pytest.skip(
            "El nombre 'simuladores' no resuelve: no se está en la red de Docker. "
            "Correr con docker compose run, o desde el anfitrión con --integracion."
        )
    return lambda ruta: _get_directo(URL_SIMULADORES + ruta)
