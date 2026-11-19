"""CONTRATO-HU-08 v1 §1 — Fuente `placas`: `GET /placas/{placa}`."""

import pytest

from ayudas_contrato import (
    PALABRA_PROHIBIDA, PLACA_CON, PLACA_NO_EXISTE, PLACA_SIN, problemas_error, problemas_placa,
)

pytestmark = pytest.mark.usefixtures("modos_limpios")


def test_placa_con_requisitoria(cliente):
    """§1 'Placa con requisitoria' (Gherkin esc. 1, mitad del simulador)."""
    r = cliente.get(f"/placas/{PLACA_CON}")
    assert r.estado == 200, r.texto
    assert "application/json" in (r.cabecera("Content-Type") or "")
    d = r.json()
    assert problemas_placa(d, PLACA_CON) == []
    assert d["requisitoria_vigente"] is True
    assert isinstance(d["requisitoria"], dict)


def test_placa_sin_requisitoria(cliente):
    """§1 'Placa sin requisitoria': misma forma, vigente false y requisitoria null."""
    r = cliente.get(f"/placas/{PLACA_SIN}")
    assert r.estado == 200, r.texto
    d = r.json()
    assert problemas_placa(d, PLACA_SIN) == []
    assert d["requisitoria_vigente"] is False
    assert "requisitoria" in d and d["requisitoria"] is None


def test_misma_forma_con_y_sin_requisitoria(cliente):
    """§1: 'con la misma forma' — los mismos campos en los dos casos."""
    con = cliente.get(f"/placas/{PLACA_CON}").json()
    sin = cliente.get(f"/placas/{PLACA_SIN}").json()
    assert set(con) == set(sin)


def test_placa_no_registrada(cliente):
    """§1 'Placa no registrada' → 404 PLACA_NO_REGISTRADA (decisión 3: no es 'sin requisitoria')."""
    r = cliente.get(f"/placas/{PLACA_NO_EXISTE}")
    assert problemas_error(r, 404, "PLACA_NO_REGISTRADA") == []
    assert "requisitoria_vigente" not in r.texto


def test_minusculas_no_se_normalizan(cliente):
    """§1 'Minúsculas' → 404 PLACA_NO_REGISTRADA (el simulador no normaliza)."""
    r = cliente.get(f"/placas/{PLACA_CON.lower()}")
    assert problemas_error(r, 404, "PLACA_NO_REGISTRADA") == []


def test_formato_invalido_no_se_valida_en_el_simulador(cliente):
    """§1: 'El simulador no valida el formato … Si la placa no está en la base, responde 404'."""
    r = cliente.get("/placas/NOPLACA")
    assert problemas_error(r, 404, "PLACA_NO_REGISTRADA") == []


@pytest.mark.parametrize("placa", [PLACA_CON, PLACA_SIN, PLACA_NO_EXISTE])
def test_sin_palabra_prohibida(cliente, placa):
    """AGENTS.md regla 1 en las respuestas de la fuente."""
    assert PALABRA_PROHIBIDA not in cliente.get(f"/placas/{placa}").texto.lower()
