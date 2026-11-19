"""Salud de los simuladores (SPRINT0.md §5, ADR-0006, M-1 E).

`GET /salud` (solo en la red interna, puerto 8001) → `200` con `{"estado": "ok"}`.
La no exposición hacia fuera se prueba en services/api/tests/test_red.py (criterio 5).
"""


def test_salud_responde_200(get_simuladores):
    assert get_simuladores("/salud").estado == 200


def test_salud_cuerpo_exacto(get_simuladores):
    r = get_simuladores("/salud")
    assert "application/json" in (r.cabecera("Content-Type") or "")
    assert r.json() == {"estado": "ok"}


def test_sin_endpoints_de_fuentes(get_simuladores):
    """SPRINT0.md §6 'NO se crea': ningún simulador de fuentes en el Sprint 0."""
    for ruta in ("/placas", "/requisitorias-personas", "/galeria"):
        assert get_simuladores(ruta).estado == 404, f"{ruta} existe y no debería"
