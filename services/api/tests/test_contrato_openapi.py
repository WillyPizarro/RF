"""DoD criterio 9 — El contrato OpenAPI está publicado y al día (ADR-0007, M-1 G).

SPRINT0.md §5: `contratos/api/openapi.json` es idéntico al OpenAPI de la API, obtenido
dentro de la red (`http://api:8000/openapi.json`). El proxy NO expone `/openapi.json`;
solo enruta `/v1/*`.
(La parte "`npm run generar:api` genera los tipos sin errores" se verifica por comando:
ver el informe.)
"""

import json

import pytest

from conftest import RAIZ_REPO, RUTA_SALUD, URL_API_INTERNA

ARCHIVO_CONTRATO = RAIZ_REPO / "contratos" / "api" / "openapi.json"


@pytest.fixture(scope="module")
def contrato_publicado() -> dict:
    assert ARCHIVO_CONTRATO.exists(), "No existe contratos/api/openapi.json"
    return json.loads(ARCHIVO_CONTRATO.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def contrato_servido(compose) -> dict:
    r = compose.get_en_red(f"{URL_API_INTERNA}/openapi.json")
    assert r.estado == 200, f"http://api:8000/openapi.json respondió {r.estado}"
    return r.json()


def test_contrato_publicado_identico_al_servido(sistema_sano, contrato_publicado, contrato_servido):
    assert contrato_publicado == contrato_servido


def test_proxy_no_expone_openapi(sistema_sano):
    """M-1 G: el proxy solo enruta /v1/*."""
    r = sistema_sano.get("/openapi.json")
    assert r.estado != 200 or '"openapi"' not in r.texto, "El proxy expone /openapi.json"


def test_contrato_declara_salud(contrato_publicado):
    assert RUTA_SALUD in contrato_publicado.get("paths", {})
    assert "get" in contrato_publicado["paths"][RUTA_SALUD]


def test_contrato_sin_rutas_de_negocio(contrato_publicado):
    """SPRINT0.md §6 'NO se crea': ningún endpoint de auth, consultas, revisiones ni bitácora."""
    prohibidas = ("/v1/auth", "/v1/consultas", "/v1/revisiones", "/v1/bitacora")
    presentes = [r for r in contrato_publicado.get("paths", {}) if r.startswith(prohibidas)]
    assert not presentes, presentes
