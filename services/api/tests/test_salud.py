"""DoD criterio 2 — La API responde salud a través del proxy, con TLS.

SPRINT0.md §5: `GET /v1/salud` → 200 con
`{"estado": "ok", "bd": "ok", "simuladores": "ok", "version": "<semver>"}`
y toda respuesta de la API lleva `X-Id-Traza`.
"""

import re

from conftest import CABECERA_TRAZA, RUTA_SALUD

# SemVer 2.0.0 (https://semver.org), expresión oficial.
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def test_salud_por_proxy_https_responde_200(sistema_sano):
    # Given: sistema arrancado (fixture) / When:
    r = sistema_sano.get(RUTA_SALUD)
    # Then:
    assert sistema_sano.url_base.startswith("https://"), "El criterio exige TLS"
    assert r.estado == 200


def test_salud_cuerpo_exacto(sistema_sano):
    cuerpo = sistema_sano.get(RUTA_SALUD).json()
    assert isinstance(cuerpo, dict)
    assert set(cuerpo) == {"estado", "bd", "simuladores", "version"}, cuerpo
    assert cuerpo["estado"] == "ok"
    assert cuerpo["bd"] == "ok"
    assert cuerpo["simuladores"] == "ok"
    assert isinstance(cuerpo["version"], str)
    assert SEMVER.match(cuerpo["version"]), f"version no es semver: {cuerpo['version']!r}"


def test_salud_responde_json(sistema_sano):
    r = sistema_sano.get(RUTA_SALUD)
    assert "application/json" in (r.cabecera("Content-Type") or "")


def test_salud_lleva_cabecera_traza(sistema_sano):
    r = sistema_sano.get(RUTA_SALUD)
    traza = r.cabecera(CABECERA_TRAZA)
    assert traza, f"Falta la cabecera {CABECERA_TRAZA}"
    assert traza.strip() == traza and len(traza) > 0
