"""DoD criterios 3 y 4 — La API depende de Postgres y de los simuladores.

SPRINT0.md §5 + M-1 A: si la base o los simuladores no responden, `/v1/salud` → `503`
con la MISMA forma que el 200 y el valor `"error"` en lo que falla, p. ej.
`{"estado": "error", "bd": "error", "simuladores": "ok", "version": "0.1.0"}`.
Sin cuerpo de error estándar; con `X-Id-Traza`. Con el servicio arriba → `200`.

Estas pruebas DETIENEN servicios del compose y los vuelven a levantar al final,
aunque fallen. No correr contra un ambiente compartido.
"""

import pytest

from conftest import CABECERA_TRAZA, esperar_salud, esperar_salud_ok
from test_salud import SEMVER

pytestmark = pytest.mark.disruptiva

CASOS = [
    # (servicio que se detiene, campo que pasa a "error", campo que sigue "ok")
    ("db", "bd", "simuladores"),
    ("simuladores", "simuladores", "bd"),
]
IDS = ["criterio3-bd", "criterio4-simuladores"]


@pytest.fixture
def caido(request, compose, cliente, pytestconfig, sistema_sano):
    """Given: el servicio indicado está detenido. Siempre se restablece al final."""
    servicio, campo_caido, campo_sano = request.param
    espera = pytestconfig.getoption("--espera-max")
    compose.detener(servicio)
    try:
        # When
        r = esperar_salud(cliente, 503, espera)
        yield r, campo_caido, campo_sano
    finally:
        compose.iniciar(servicio)
        esperar_salud_ok(cliente, espera)


@pytest.mark.parametrize("caido", CASOS, indirect=True, ids=IDS)
def test_salud_503_misma_forma_con_error_en_lo_que_falla(caido):
    r, campo_caido, campo_sano = caido
    cuerpo = r.json()
    assert isinstance(cuerpo, dict)
    assert set(cuerpo) == {"estado", "bd", "simuladores", "version"}, cuerpo
    assert cuerpo["estado"] == "error"
    assert cuerpo[campo_caido] == "error"
    assert cuerpo[campo_sano] == "ok"
    assert isinstance(cuerpo["version"], str) and SEMVER.match(cuerpo["version"])


@pytest.mark.parametrize("caido", CASOS, indirect=True, ids=IDS)
def test_salud_503_no_usa_formato_de_error_estandar(caido):
    r, _, _ = caido
    cuerpo = r.json()
    assert not ({"codigo", "mensaje", "id_traza"} & set(cuerpo)), cuerpo


@pytest.mark.parametrize("caido", CASOS, indirect=True, ids=IDS)
def test_salud_503_lleva_cabecera_traza(caido):
    r, _, _ = caido
    assert r.cabecera(CABECERA_TRAZA), "El 503 de salud lleva X-Id-Traza (M-1 A)"


@pytest.mark.parametrize("servicio", ["db", "simuladores"], ids=IDS)
def test_salud_vuelve_a_200_cuando_la_dependencia_vuelve(
    servicio, compose, cliente, pytestconfig, sistema_sano
):
    espera = pytestconfig.getoption("--espera-max")
    compose.detener(servicio)
    try:
        esperar_salud(cliente, 503, espera)
    finally:
        compose.iniciar(servicio)
    cuerpo = esperar_salud_ok(cliente, espera).json()
    assert cuerpo["estado"] == "ok" and cuerpo["bd"] == "ok" and cuerpo["simuladores"] == "ok"
