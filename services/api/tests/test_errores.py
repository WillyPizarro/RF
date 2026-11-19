"""DoD criterio 7 — Formato de error e id de traza (ADR-0007, ADR-0014, M-1 B, M-2).

SPRINT0.md §5: error estándar `{"codigo", "mensaje", "id_traza"}` con `id_traza` igual a
`X-Id-Traza`. El criterio 7 prueba el 404 `NO_ENCONTRADO` (M-2: el 422 se prueba con HU-01).
El 405 `METODO_NO_PERMITIDO` (M-1 B, vigente) se prueba aquí como caso adicional del
contrato de §5, fuera del criterio 7, porque es observable con la única ruta existente.
"""

import pytest

from conftest import CABECERA_TRAZA, RUTA_SALUD

CASOS = [
    # (id, método, ruta, cuerpo, estado, código)
    ("404-no-existe", "GET", "/v1/no-existe", None, 404, "NO_ENCONTRADO"),
    ("404-anidada", "GET", "/v1/otra/ruta/que/no/existe", None, 404, "NO_ENCONTRADO"),
    ("404-bajo-salud", "GET", "/v1/salud/no-existe", None, 404, "NO_ENCONTRADO"),
    ("405-post-salud", "POST", RUTA_SALUD, b"{}", 405, "METODO_NO_PERMITIDO"),
]

PARAMS = [pytest.param(*c[1:], id=c[0]) for c in CASOS]


@pytest.mark.parametrize(("metodo", "ruta", "cuerpo", "estado", "codigo"), PARAMS)
def test_error_estado_y_codigo(sistema_sano, metodo, ruta, cuerpo, estado, codigo):
    r = sistema_sano.pedir(metodo, ruta, cuerpo)
    assert r.estado == estado
    assert r.json()["codigo"] == codigo


@pytest.mark.parametrize(("metodo", "ruta", "cuerpo", "estado", "codigo"), PARAMS)
def test_error_formato_estandar(sistema_sano, metodo, ruta, cuerpo, estado, codigo):
    r = sistema_sano.pedir(metodo, ruta, cuerpo)
    assert "application/json" in (r.cabecera("Content-Type") or "")
    cuerpo_resp = r.json()
    assert isinstance(cuerpo_resp, dict)
    assert set(cuerpo_resp) == {"codigo", "mensaje", "id_traza"}, cuerpo_resp
    assert isinstance(cuerpo_resp["mensaje"], str) and cuerpo_resp["mensaje"].strip()


@pytest.mark.parametrize(("metodo", "ruta", "cuerpo", "estado", "codigo"), PARAMS)
def test_id_traza_del_error_igual_a_la_cabecera(sistema_sano, metodo, ruta, cuerpo, estado, codigo):
    r = sistema_sano.pedir(metodo, ruta, cuerpo)
    cabecera = r.cabecera(CABECERA_TRAZA)
    assert cabecera, f"Falta la cabecera {CABECERA_TRAZA} en el {estado}"
    assert r.json()["id_traza"] == cabecera


def test_id_traza_distinto_por_solicitud(sistema_sano):
    """ADR-0014: un id_traza por solicitud."""
    trazas = [sistema_sano.get(RUTA_SALUD).cabecera(CABECERA_TRAZA) for _ in range(3)]
    trazas += [sistema_sano.get("/v1/no-existe").cabecera(CABECERA_TRAZA) for _ in range(2)]
    assert None not in trazas
    assert len(set(trazas)) == 5, f"Se repitió un id_traza: {trazas}"


def test_mensaje_de_error_no_usa_palabra_prohibida(sistema_sano):
    """AGENTS.md regla 1: la palabra "identificado" no existe en la API."""
    texto = sistema_sano.get("/v1/no-existe").texto.lower()
    assert "identificad" not in texto
