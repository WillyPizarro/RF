"""Salud de los simuladores (SPRINT0.md §5, ADR-0006, M-1 E).

`GET /salud` (solo en la red interna, puerto 8001) → `200` con `{"estado": "ok"}`.
La no exposición hacia fuera se prueba en services/api/tests/test_red.py (criterio 5) y en
test_aislamiento.py (HU-08 §8).

HU-08 reemplaza la prueba del Sprint 0 "sin endpoints de fuentes" (SPRINT0 §6 "NO se crea"):
desde CONTRATO-HU-08 v1 esas rutas existen.
"""


def test_salud_responde_200(get_simuladores):
    assert get_simuladores("/salud").estado == 200


def test_salud_cuerpo_exacto(get_simuladores):
    r = get_simuladores("/salud")
    assert "application/json" in (r.cabecera("Content-Type") or "")
    assert r.json() == {"estado": "ok"}
