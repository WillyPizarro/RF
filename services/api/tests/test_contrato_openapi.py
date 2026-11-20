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

ARCHIVO_CONTRATO = RAIZ_REPO / "contratos" / "api" / "openapi.json" if RAIZ_REPO else None


@pytest.fixture(scope="module")
def contrato_publicado() -> dict:
    assert ARCHIVO_CONTRATO is not None, "No se encontró la raíz del repositorio"
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


# Rutas vigentes tras HU-01 (§1, §3), HU-02 (§1), HU-03 (§1, §2) y HU-07 (§4). Reemplaza a la
# prueba del Sprint 0 "sin rutas de negocio" (veredicto HU-01/02, A3); HU-03/07 la amplía
# (veredicto HU-03/07, A1).
RUTAS_VIGENTES = {
    RUTA_SALUD: {"get"},
    "/v1/auth/login": {"post"},
    "/v1/auth/refresh": {"post"},
    "/v1/auth/logout": {"post"},
    "/v1/me": {"get"},
    "/v1/motivos": {"get"},
    "/v1/consultas/placa": {"post"},
    "/v1/bitacora": {"get"},
}
METODOS_HTTP = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


def test_contrato_rutas_vigentes(contrato_publicado):
    """El contrato publicado declara exactamente las rutas vigentes, con sus métodos: ninguna de
    menos y ninguna de una HU todavía no construida (rostro, revisiones)."""
    paths = contrato_publicado.get("paths", {})
    assert set(paths) == set(RUTAS_VIGENTES), sorted(paths)
    for ruta, metodos in RUTAS_VIGENTES.items():
        assert {m for m in paths[ruta] if m in METODOS_HTTP} == metodos, (ruta, sorted(paths[ruta]))
