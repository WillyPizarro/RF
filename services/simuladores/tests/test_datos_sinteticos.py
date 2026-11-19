"""CONTRATO-HU-08 v1 §4 — Datos sintéticos.

El contrato no da una ruta para listar la base: el volumen se mide desde fuera recorriendo todo el
espacio de placas reservadas (`ZZ` + 1 alfanumérico + `-` + 3 dígitos = 36 000 placas) y los ids
`SIM-P-0001` a `SIM-P-0999`. Es caja negra pura; tarda del orden de un minuto.

El determinismo entre arranques y "al arrancar, todo en normal" están en test_reinicio.py.
"Datos versionados" (la semilla es un archivo de services/simuladores/) y "sin fotos en el
repositorio" se verifican desde el anfitrión en test_repositorio.py.
"""

import random
import string

import pytest

from ayudas_contrato import (
    PERSONA_EXISTE, PLACA_CON, PLACA_NO_EXISTE, PLACA_SIN, RE_PLACA, problemas_persona,
    problemas_placa,
)

pytestmark = pytest.mark.usefixtures("modos_limpios")

ALFANUM = string.ascii_uppercase + string.digits


@pytest.fixture(scope="module")
def placas(cliente) -> dict[str, dict]:
    """Todas las placas del espacio ZZ?-??? que responden 200, con su cuerpo."""
    cliente.todo_normal()
    rutas = [f"/placas/ZZ{c}-{n:03d}" for c in ALFANUM for n in range(1000)]
    halladas: dict[str, dict] = {}
    raros = []
    for ruta, r in zip(rutas, cliente.lote_get(rutas)):
        if r.estado == 200:
            halladas[ruta.rsplit("/", 1)[1]] = r.json()
        elif r.estado != 404:
            raros.append((ruta, r.estado, r.error))
    assert not raros, f"respuestas que no son 200 ni 404: {raros[:10]}"
    return halladas


@pytest.fixture(scope="module")
def personas(cliente) -> dict[str, dict]:
    cliente.todo_normal()
    rutas = [f"/personas/SIM-P-{n:04d}" for n in range(1, 1000)]
    return {
        ruta.rsplit("/", 1)[1]: r.json()
        for ruta, r in zip(rutas, cliente.lote_get(rutas)) if r.estado == 200
    }


def test_volumen_de_placas(placas):
    """§4 'Volumen de placas': ≥ 200 vehículos."""
    assert len(placas) >= 200, f"solo {len(placas)} placas en el espacio ZZ"


def test_placas_con_requisitoria(placas):
    """§4 'Volumen de placas': ≥ 20 con requisitoria vigente."""
    con = [p for p, d in placas.items() if d.get("requisitoria_vigente") is True]
    assert len(con) >= 20, f"solo {len(con)} con requisitoria vigente"


def test_cada_placa_cumple_la_forma(placas):
    """§1 + §4: cada registro cumple la forma del contrato y es_sintetico true."""
    malos = {p: e for p, d in placas.items() if (e := problemas_placa(d, p))}
    assert not malos, dict(list(malos.items())[:5])


def test_placas_reservadas(placas):
    """§4 'Placas reservadas': empiezan con ZZ y cumplen ^[A-Z0-9]{3}-[0-9]{3}$."""
    for p in placas:
        assert p.startswith("ZZ") and RE_PLACA.match(p), p


def test_muestra_fuera_de_zz_no_existe(cliente):
    """§4 'Placas reservadas' — lado negativo, por muestra: placas con forma válida que NO
    empiezan con ZZ dan 404. (Probar que no hay ninguna exigiría 36^3 * 1000 peticiones.)"""
    azar = random.Random(808)
    muestra = set()
    while len(muestra) < 1000:
        pre = "".join(azar.choice(ALFANUM) for _ in range(3))
        if not pre.startswith("ZZ"):
            muestra.add(f"{pre}-{azar.randrange(1000):03d}")
    muestra |= {"ABC-123", "AAA-000", "A1B-234", "XYZ-999", "B2C-100"}
    rutas = [f"/placas/{p}" for p in sorted(muestra)]
    existen = [ru for ru, r in zip(rutas, cliente.lote_get(rutas)) if r.estado != 404]
    assert not existen, f"placas fuera de ZZ que no dan 404: {existen[:10]}"


def test_placas_fijas(placas):
    """§4 'Placas fijas para pruebas'."""
    assert placas[PLACA_CON]["requisitoria_vigente"] is True
    assert placas[PLACA_SIN]["requisitoria_vigente"] is False
    assert PLACA_NO_EXISTE not in placas


def test_volumen_de_personas(personas):
    """§4 'Personas': entre 20 y 30, desde SIM-P-0001, SIM-P-0001 siempre existe."""
    assert 20 <= len(personas) <= 30, f"{len(personas)} personas"
    assert PERSONA_EXISTE in personas


def test_todas_las_personas_cumplen_la_forma(personas):
    """§2 + §4: todas con requisitoria, documento SIM-######## y es_sintetico true."""
    malos = {p: e for p, d in personas.items() if (e := problemas_persona(d, p))}
    assert not malos, dict(list(malos.items())[:5])
