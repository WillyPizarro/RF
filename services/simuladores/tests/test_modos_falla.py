"""CONTRATO-HU-08 v1 §5 — Modos de falla por fuente, en tiempo de ejecución.

`PUT /control/modos/{fuente}` body `{"modo", "latencia_ms"?}` · `GET /control/modos`.
Cada prueba deja todas las fuentes en `normal` (fixture `modos_limpios`).

v2 C4: un PUT válido → 200 `{"modo","latencia_ms"}` (latencia_ms null salvo en `latencia`, por
defecto 5000); `GET /control/modos` → 200 con una clave por fuente y valores `{"modo","latencia_ms"}`.
"""

import pytest

from ayudas_contrato import (
    PERSONA_EXISTE, PLACA_CON, problemas_error, problemas_galeria, problemas_persona,
    problemas_placa,
)

pytestmark = pytest.mark.usefixtures("modos_limpios")

FUENTES = ("placas", "requisitorias-personas", "galeria")

# Una ruta por cada ruta de la fuente (contrato §1 a §3).
RUTAS = {
    "placas": [f"/placas/{PLACA_CON}"],
    "requisitorias-personas": [f"/personas/{PERSONA_EXISTE}",
                               f"/personas/{PERSONA_EXISTE}/fotos/inexistente"],
    "galeria": ["/galeria"],
}
# Rutas de datos JSON y el verificador de forma de su fuente.
DATOS = {
    "placas": (f"/placas/{PLACA_CON}", lambda d: problemas_placa(d, PLACA_CON)),
    "requisitorias-personas": (f"/personas/{PERSONA_EXISTE}",
                               lambda d: problemas_persona(d, PERSONA_EXISTE)),
    "galeria": ("/galeria", problemas_galeria),
}


def _es_2xx(r):
    """v2 C4: un cambio válido responde exactamente 200."""
    return r.estado == 200


def _normal_ok(cliente, fuente):
    ruta, forma = DATOS[fuente]
    r = cliente.get(ruta)
    assert r.estado == 200, f"{fuente} {ruta}: {r.estado} {r.texto[:200]}"
    assert forma(r.json()) == [], f"{fuente} {ruta} no responde normal"
    return r


# --- Control ---------------------------------------------------------------------------------

def test_get_control_modos_lista_las_tres_fuentes(modos_limpios):
    """§5 'Lectura' (v2 C4): 200, una clave por fuente, valores {"modo","latencia_ms"}."""
    r = modos_limpios.get("/control/modos")
    assert r.estado == 200, r.texto
    d = r.json()
    assert set(d) == set(FUENTES)
    for f, v in d.items():
        assert v == {"modo": "normal", "latencia_ms": None}, f"{f}: {v}"


@pytest.mark.parametrize("fuente", FUENTES)
@pytest.mark.parametrize("modo,latencia_ms,esperada", [
    ("latencia", None, 5000),
    ("latencia", 1234, 1234),
    ("error_500", None, None),
    ("malformada", None, None),
    ("normal", None, None),
])
def test_put_modo_valido_responde_y_se_refleja_en_get(modos_limpios, fuente, modo, latencia_ms,
                                                       esperada):
    """§5 'Cambio válido' y 'Lectura' (v2 C4)."""
    r = modos_limpios.poner_modo(fuente, modo, latencia_ms)
    assert r.estado == 200, f"PUT {fuente} {modo}: {r.estado} {r.texto[:200]}"
    assert r.json() == {"modo": modo, "latencia_ms": esperada}
    g = modos_limpios.get("/control/modos")
    assert g.estado == 200
    assert g.json()[fuente] == {"modo": modo, "latencia_ms": esperada}


@pytest.mark.parametrize("fuente", ["otra", "personas", "PLACAS"])
def test_fuente_invalida(modos_limpios, fuente):
    """§5 'Fuente inválida' → 404 FUENTE_DESCONOCIDA."""
    r = modos_limpios.poner_modo(fuente, "error_500")
    assert problemas_error(r, 404, "FUENTE_DESCONOCIDA") == []


@pytest.mark.parametrize("cuerpo", [{"modo": "x"}, {"modo": "ERROR_500"}, {}, {"modo": None}])
def test_modo_invalido(modos_limpios, cuerpo):
    """§5 'Modo inválido' → 422 SOLICITUD_INVALIDA, y la fuente sigue como estaba."""
    r = modos_limpios.put("/control/modos/placas", cuerpo)
    assert problemas_error(r, 422, "SOLICITUD_INVALIDA") == []
    _normal_ok(modos_limpios, "placas")


# --- Efecto de cada modo ---------------------------------------------------------------------

@pytest.mark.parametrize("fuente", FUENTES)
def test_normal_sin_latencia_artificial(modos_limpios, fuente):
    """§5 `normal`: responde según §1 a §3, sin latencia artificial (holgura: < 1 s)."""
    r = _normal_ok(modos_limpios, fuente)
    assert r.segundos < 1.0, f"{fuente} tardó {r.segundos:.2f} s en modo normal"


@pytest.mark.parametrize("fuente", FUENTES)
def test_error_500_en_cada_ruta(modos_limpios, fuente):
    """§5 `error_500` → 500 {"codigo":"ERROR_SIMULADO","mensaje":"Falla simulada de la fuente"}."""
    assert _es_2xx(modos_limpios.poner_modo(fuente, "error_500"))
    for ruta in RUTAS[fuente]:
        r = modos_limpios.get(ruta)
        assert problemas_error(r, 500, "ERROR_SIMULADO") == [], ruta


@pytest.mark.parametrize("fuente", FUENTES)
def test_malformada(modos_limpios, fuente):
    """§5 `malformada` → 200 con un cuerpo que no cumple la forma del contrato de su fuente.
    (La validación contra el yaml está en test_contratos_yaml.py, desde el anfitrión.)"""
    assert _es_2xx(modos_limpios.poner_modo(fuente, "malformada"))
    ruta, forma = DATOS[fuente]
    r = modos_limpios.get(ruta)
    assert r.estado == 200, f"{ruta}: {r.estado}"
    try:
        cuerpo = r.json()
    except ValueError:
        return  # ni siquiera es JSON: tampoco valida
    assert forma(cuerpo) != [], f"{ruta} en modo malformada devolvió un cuerpo válido: {cuerpo}"


def test_malformada_placas_falta_campo_o_vigente_no_booleano(modos_limpios):
    """§5 `malformada`, el ejemplo del contrato para placas."""
    assert _es_2xx(modos_limpios.poner_modo("placas", "malformada"))
    d = modos_limpios.get(f"/placas/{PLACA_CON}").json()
    obligatorios = ("placa", "marca", "modelo", "color", "tipo", "requisitoria_vigente",
                    "requisitoria", "es_sintetico")
    falta = [c for c in obligatorios if c not in d]
    assert falta or not isinstance(d.get("requisitoria_vigente"), bool), d


@pytest.mark.parametrize("fuente", FUENTES)
def test_latencia_configurable(modos_limpios, fuente):
    """§5 `latencia` con latencia_ms: responde lo normal tras esa latencia."""
    assert _es_2xx(modos_limpios.poner_modo(fuente, "latencia", latencia_ms=1500))
    ruta, forma = DATOS[fuente]
    r = modos_limpios.get(ruta)
    assert r.estado == 200 and forma(r.json()) == []
    assert r.segundos >= 1.5, f"{fuente} respondió en {r.segundos:.2f} s (< 1,5 s)"


def test_latencia_por_defecto_5000(modos_limpios):
    """§5 `latencia` sin latencia_ms → 5000 ms por defecto (por encima del timeout de 3 s)."""
    assert _es_2xx(modos_limpios.poner_modo("placas", "latencia"))
    r = modos_limpios.get(f"/placas/{PLACA_CON}", timeout=20)
    assert r.estado == 200 and problemas_placa(r.json(), PLACA_CON) == []
    assert r.segundos >= 5.0, f"respondió en {r.segundos:.2f} s (< 5 s)"


# --- Aislamiento -----------------------------------------------------------------------------

@pytest.mark.parametrize("fuente", FUENTES)
@pytest.mark.parametrize("modo", ["error_500", "malformada"])
def test_un_modo_no_altera_las_otras_fuentes(modos_limpios, fuente, modo):
    """§5 'Aislamiento': el modo de una fuente no altera las otras."""
    assert _es_2xx(modos_limpios.poner_modo(fuente, modo))
    for otra in FUENTES:
        if otra != fuente:
            _normal_ok(modos_limpios, otra)


@pytest.mark.parametrize("modo", ["error_500", "malformada", "latencia"])
def test_salud_200_en_cualquier_modo(modos_limpios, modo):
    """§5 'Aislamiento': GET /salud responde 200 en cualquier modo."""
    for f in FUENTES:
        assert _es_2xx(modos_limpios.poner_modo(f, modo))
    r = modos_limpios.get("/salud")
    assert r.estado == 200 and r.json() == {"estado": "ok"}


def test_volver_a_normal(modos_limpios):
    """Configurable 'sin reiniciar': error_500 → normal restituye la respuesta normal."""
    assert _es_2xx(modos_limpios.poner_modo("placas", "error_500"))
    assert modos_limpios.get(f"/placas/{PLACA_CON}").estado == 500
    assert _es_2xx(modos_limpios.poner_modo("placas", "normal"))
    _normal_ok(modos_limpios, "placas")
