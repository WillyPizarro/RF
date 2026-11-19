"""CONTRATO-HU-08 v1 §7 — Reemplazo del simulador (Gherkin esc. 2, mitad del simulador).

Solo anfitrión. El mock de Prism necesita Node (npx) y descarga `@stoplight/prism-cli` la primera
vez. La prueba de punta a punta (la API apuntando al mock) es de HU-03.
"""

from __future__ import annotations

import re
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request

import pytest

from ayudas_contrato import PLACA_CON

VARIABLES_URL = ("FUENTE_PLACAS_URL", "FUENTE_REQUISITORIAS_URL", "FUENTE_GALERIA_URL")
PRISM = "@stoplight/prism-cli@5"


def _env_example(raiz) -> list[str]:
    return (raiz / "infra" / ".env.example").read_text(encoding="utf-8").splitlines()


def _linea_de(lineas: list[str], var: str) -> int | None:
    for i, ln in enumerate(lineas):
        if re.match(rf"^\s*{var}\s*=", ln):
            return i
    return None


@pytest.mark.parametrize("var", VARIABLES_URL)
def test_url_por_fuente_en_env_example_con_comentario(raiz_repo, var):
    """§7 'URL por fuente': las tres figuran en infra/.env.example con un comentario."""
    lineas = _env_example(raiz_repo)
    i = _linea_de(lineas, var)
    assert i is not None, f"{var} no figura en infra/.env.example"
    comentario_arriba = i > 0 and lineas[i - 1].strip().startswith("#")
    comentario_en_linea = "#" in lineas[i].split("=", 1)[1]
    assert comentario_arriba or comentario_en_linea, f"{var} sin comentario"


def test_timeout_por_defecto_3(raiz_repo):
    """§7 'Timeout configurable': FUENTE_TIMEOUT_S, valor por defecto 3, en .env.example."""
    lineas = _env_example(raiz_repo)
    i = _linea_de(lineas, "FUENTE_TIMEOUT_S")
    assert i is not None, "FUENTE_TIMEOUT_S no figura en infra/.env.example"
    valor = lineas[i].split("=", 1)[1].split("#", 1)[0].strip().strip('"').strip("'")
    assert float(valor) == 3, f"FUENTE_TIMEOUT_S={valor!r}"


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def mock_placas(raiz_repo):
    """`prism mock contratos/fuentes/placas.yaml`: una implementación generada SOLO del yaml."""
    npx = shutil.which("npx")
    if npx is None:
        pytest.skip("npx no está en el anfitrión: no se puede levantar Prism")
    pytest.importorskip("yaml", reason="falta pyyaml (requirements-pruebas.txt)")
    pytest.importorskip("jsonschema", reason="falta jsonschema (requirements-pruebas.txt)")
    puerto = _puerto_libre()
    proc = subprocess.Popen(
        [npx, "--yes", PRISM, "mock", "-h", "127.0.0.1", "-p", str(puerto),
         str(raiz_repo / "contratos" / "fuentes" / "placas.yaml")],
        cwd=raiz_repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    base = f"http://127.0.0.1:{puerto}"
    limite = time.monotonic() + 180
    try:
        while time.monotonic() < limite:
            if proc.poll() is not None:
                salida = proc.stdout.read().decode("utf-8", "replace")
                pytest.fail(f"Prism terminó (¿yaml inválido?):\n{salida[-2000:]}")
            try:
                urllib.request.urlopen(base + f"/placas/{PLACA_CON}", timeout=2)
                break
            except urllib.error.HTTPError:
                break
            except OSError:
                time.sleep(1)
        else:
            pytest.fail("Prism no arrancó en 180 s")
        yield base
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_mock_desde_el_yaml_cumple_el_mismo_contrato(raiz_repo, mock_placas):
    """§7 'Segunda implementación': el mock responde GET /placas/{placa} con un cuerpo que valida
    contra el mismo contrato que el simulador."""
    from conftest import Respuesta
    from ayudas_contrato import cargar_yaml, errores_contra_yaml

    ruta = f"/placas/{PLACA_CON}"
    req = urllib.request.Request(mock_placas + ruta, headers={"Prefer": "code=200"})
    with urllib.request.urlopen(req, timeout=10) as r:
        resp = Respuesta(r.status, dict(r.headers.items()), r.read())
    assert resp.estado == 200
    assert errores_contra_yaml(cargar_yaml(raiz_repo, "placas"), ruta, "GET", resp) == []
