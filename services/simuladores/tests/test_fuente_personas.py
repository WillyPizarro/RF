"""CONTRATO-HU-08 v1 §2 — Fuente `requisitorias-personas`.

`GET /personas/{persona_id}` y `GET /personas/{persona_id}/fotos/{foto_id}`.
"""

import pytest

from ayudas_contrato import (
    FIRMAS_IMAGEN, PALABRA_PROHIBIDA, PERSONA_EXISTE, PERSONA_NO_EXISTE, problemas_error,
    problemas_persona,
)

pytestmark = pytest.mark.usefixtures("modos_limpios")


def test_persona_con_requisitoria(cliente):
    """§2 'Persona con requisitoria'."""
    r = cliente.get(f"/personas/{PERSONA_EXISTE}")
    assert r.estado == 200, r.texto
    assert "application/json" in (r.cabecera("Content-Type") or "")
    assert problemas_persona(r.json(), PERSONA_EXISTE) == []


def test_persona_no_registrada(cliente):
    """§2 'Persona no registrada' → 404 PERSONA_NO_REGISTRADA."""
    r = cliente.get(f"/personas/{PERSONA_NO_EXISTE}")
    assert problemas_error(r, 404, "PERSONA_NO_REGISTRADA") == []


def test_foto_no_cargada(cliente):
    """§2 'Foto no cargada' → 404 FOTO_NO_DISPONIBLE."""
    r = cliente.get(f"/personas/{PERSONA_EXISTE}/fotos/inexistente")
    assert problemas_error(r, 404, "FOTO_NO_DISPONIBLE") == []


def test_fotos_cargadas_se_sirven_como_imagen(cliente):
    """§2 'Foto cargada' → 200 image/jpeg o image/png con los bytes descifrados.

    Recorre las personas que ya tienen fotos. Si ninguna tiene, se omite: cómo cargar una foto de
    prueba depende de la v2 del contrato (pregunta del TESTER al LEAD, 2026-11-19).
    """
    con_fotos = []
    for r in cliente.lote_get([f"/personas/SIM-P-{n:04d}" for n in range(1, 100)]):
        if r.estado == 200:
            d = r.json()
            con_fotos += [(d["persona_id"], f) for f in d.get("foto_ids") or []]
    if not con_fotos:
        pytest.skip("Ninguna persona tiene fotos cargadas (carga de fotos: pendiente de contrato v2)")
    for persona_id, foto_id in con_fotos:
        r = cliente.get(f"/personas/{persona_id}/fotos/{foto_id}")
        assert r.estado == 200, f"{persona_id}/{foto_id}: {r.texto[:200]}"
        tipo = (r.cabecera("Content-Type") or "").split(";")[0].strip()
        assert tipo in FIRMAS_IMAGEN, f"Content-Type {tipo!r}"
        assert r.cuerpo.startswith(FIRMAS_IMAGEN[tipo]), (
            f"{persona_id}/{foto_id}: los bytes no son {tipo} (¿siguen cifrados?)"
        )


@pytest.mark.parametrize("ruta", [
    f"/personas/{PERSONA_EXISTE}",
    f"/personas/{PERSONA_NO_EXISTE}",
    f"/personas/{PERSONA_EXISTE}/fotos/inexistente",
])
def test_sin_palabra_prohibida(cliente, ruta):
    """AGENTS.md regla 1 en las respuestas de la fuente."""
    assert PALABRA_PROHIBIDA not in cliente.get(ruta).texto.lower()
