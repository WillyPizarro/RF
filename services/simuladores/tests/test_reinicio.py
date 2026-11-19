"""CONTRATO-HU-08 v3 §4 'Datos versionados' (determinista: los mismos datos en cada arranque),
§4 bis 'Versión' (la misma entre reinicios si no cambian las fotos ni SIM_FOTOS_LLAVE) y
§5 'Al arrancar, todas las fuentes están en normal' (v2 C4).

Reinicia el contenedor `simuladores`: solo corre con `--integracion --reinicio`.
"""

from __future__ import annotations

import pytest

from conftest import FUENTES, compose, esperar_salud, leer_env_infra
from ayudas_contrato import PERSONA_EXISTE

RUTAS_FOTO = [f"/personas/SIM-P-{n:04d}" for n in range(1, 100)] + ["/galeria"]


@pytest.fixture
def reinicio(pytestconfig, solo_anfitrion):
    if not pytestconfig.getoption("--reinicio"):
        pytest.skip("Reinicia simuladores: correr con --integracion --reinicio")


def _foto(cliente) -> dict:
    """Todas las placas ZZ y personas que existen, con sus cuerpos (en modo normal)."""
    rutas = [f"/placas/ZZ{c}-{n:03d}" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
             for n in range(1000)] + RUTAS_FOTO
    return {
        ru: r.json() for ru, r in zip(rutas, cliente.lote_get(rutas)) if r.estado == 200
    }


def test_mismos_datos_y_modos_normales_tras_reiniciar(reinicio, cliente):
    cliente.todo_normal()
    antes = _foto(cliente)
    assert f"/personas/{PERSONA_EXISTE}" in antes
    for f in FUENTES:
        cliente.poner_modo(f, "error_500")

    r = compose("restart", "simuladores", timeout=180)
    assert r.returncode == 0, r.stderr[-2000:]
    esperar_salud(cliente)

    # §5: al arrancar, todas en normal (sin que la prueba las toque).
    modos = cliente.get("/control/modos").json()
    for f in FUENTES:
        assert modos[f] == {"modo": "normal", "latencia_ms": None}, modos

    despues = _foto(cliente)
    if not leer_env_infra().get("SIM_FOTOS_LLAVE"):
        # §4 bis: la version solo se exige estable si SIM_FOTOS_LLAVE no cambia; vacía = aleatoria.
        for d in (antes, despues):
            d.get("/galeria", {}).pop("version", None)
    assert set(antes) == set(despues), "cambió el conjunto de placas/personas"
    distintos = [ru for ru in antes if antes[ru] != despues[ru]]
    assert not distintos, f"datos distintos tras reiniciar: {distintos[:10]}"
