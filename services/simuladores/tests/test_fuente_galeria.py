"""CONTRATO-HU-08 v1 §3 — Fuente `galeria`: `GET /galeria`."""

import pytest

from ayudas_contrato import PALABRA_PROHIBIDA, problemas_galeria

pytestmark = pytest.mark.usefixtures("modos_limpios")


def _galeria(cliente):
    r = cliente.get("/galeria")
    assert r.estado == 200, r.texto
    assert "application/json" in (r.cabecera("Content-Type") or "")
    return r.json()


def test_galeria_forma(cliente):
    """§3 'Galería': version, personas[{persona_id, foto_ids}], es_sintetico."""
    assert problemas_galeria(_galeria(cliente)) == []


def test_solo_personas_con_foto(cliente):
    """§3 'Solo personas con foto': cada persona listada tiene ≥ 1 foto y figura igual en la fuente
    de personas; las personas sin fotos no aparecen; sin fotos cargadas, personas == []."""
    g = _galeria(cliente)
    en_galeria = {e["persona_id"]: e["foto_ids"] for e in g["personas"]}
    assert len(en_galeria) == len(g["personas"]), "persona repetida en la galería"

    fuente: dict[str, list[str]] = {}
    for r in cliente.lote_get([f"/personas/SIM-P-{n:04d}" for n in range(1, 100)]):
        if r.estado == 200:
            d = r.json()
            fuente[d["persona_id"]] = d.get("foto_ids") or []

    for pid, fotos in en_galeria.items():
        assert fotos, f"{pid} está en la galería sin fotos"
        assert pid in fuente, f"{pid} está en la galería pero no en requisitorias-personas"
        assert sorted(fotos) == sorted(fuente[pid]), f"{pid}: foto_ids distintos entre fuentes"
    for pid, fotos in fuente.items():
        if fotos:
            assert pid in en_galeria, f"{pid} tiene fotos y no está en la galería"
        else:
            assert pid not in en_galeria, f"{pid} no tiene fotos y está en la galería"
    if not any(fuente.values()):
        assert g["personas"] == []


def test_version_estable(cliente):
    """§3 'Versión estable': dos GET sin cambiar fotos → la misma version."""
    assert _galeria(cliente)["version"] == _galeria(cliente)["version"]


def test_sin_palabra_prohibida(cliente):
    """AGENTS.md regla 1."""
    assert PALABRA_PROHIBIDA not in cliente.get("/galeria").texto.lower()
