"""CONTRATO-HU-03 v3 §1 (motivos), §2 (consultar placa) y §3 (errores de la fuente).

Por la red interna (`http://api:8000`). Los modos de la fuente se fuerzan con
`PUT http://simuladores:8001/control/modos/placas` (CONTRATO-HU-08 §5); cada prueba deja la
fuente en `normal`. Cuántas veces se llamó a la fuente se cuenta con el log de acceso del
simulador (respuesta del LEAD); si el log no sirve, ese conteo queda NO VERIFICADO.
"""

from __future__ import annotations

import time

import pytest

from ayudas_hu01 import problemas_error, tipos
from ayudas_hu03 import (
    CATALOGO, FORMATO_DESCRIPCION, FORMATO_REGEX, MSG_FORMATO, MSG_OTRO_CORTO, MSG_SIN_MOTIVO, PLACA_CON,
    PLACA_NO_REG, PLACA_SIN, RUTA_MOTIVOS, RUTA_PLACA, consulta, problemas_resultado,
)


@pytest.fixture
def api(config_defecto):
    config_defecto.modo_placas("normal")
    yield config_defecto
    config_defecto.modo_placas("normal")


@pytest.fixture
def agente(api):
    return api.token("agente1")


def _consultar(s, token, cuerpo, **kw):
    return s.pedir("POST", RUTA_PLACA, json=cuerpo, token=token, **kw)


def _fila_consulta(s, consulta_id):
    filas = s.sql_json(f"select * from consulta where id::text = '{consulta_id}'")
    assert len(filas) == 1, f"consulta {consulta_id}: {filas}"
    return filas[0]


# --- §1 Catálogo de motivos ------------------------------------------------------------------

def test_catalogo(api, agente):
    """§1 'Catálogo' (v3): los 5 motivos iniciales, activos, con 'otro' al final, y
    formato_placa {regex, descripcion} con los valores por defecto."""
    r = api.pedir("GET", RUTA_MOTIVOS, token=agente)
    assert r.estado == 200, r
    d = r.json()
    assert [{"codigo": m["codigo"], "descripcion": m["descripcion"]} for m in d["motivos"]] == CATALOGO
    assert d["formato_placa"] == {"regex": FORMATO_REGEX, "descripcion": FORMATO_DESCRIPCION}


def test_catalogo_configurable(api, agente):
    """§1 'Configurable': agregar o desactivar un motivo en motivo_catalogo (columnas del TDD:
    codigo, descripcion, activo) cambia la respuesta sin tocar código; 'otro' sigue al final."""
    nuevo = "tester_prueba"
    try:
        r = api.psql(f"insert into motivo_catalogo (codigo, descripcion, activo) values "
                     f"('{nuevo}', 'Motivo de prueba', true);\n"
                     f"update motivo_catalogo set activo = false where codigo = 'denuncia';\n")
        assert r.returncode == 0, r.stderr
        codigos = [m["codigo"] for m in api.pedir("GET", RUTA_MOTIVOS, token=agente).json()["motivos"]]
        assert nuevo in codigos and "denuncia" not in codigos, codigos
        assert codigos[-1] == "otro", codigos
    finally:
        api.psql(f"delete from motivo_catalogo where codigo = '{nuevo}';\n"
                 "update motivo_catalogo set activo = true where codigo = 'denuncia';\n")
    codigos = [m["codigo"] for m in api.pedir("GET", RUTA_MOTIVOS, token=agente).json()["motivos"]]
    assert codigos == [m["codigo"] for m in CATALOGO]


# --- §2 Consultar placa ----------------------------------------------------------------------

@pytest.mark.parametrize("placa,resultado", [(PLACA_CON, "con_requisitoria"),
                                             (PLACA_SIN, "sin_requisitoria"),
                                             (PLACA_NO_REG, "placa_no_registrada")])
def test_resultados_y_registro(api, agente, placa, resultado):
    """§2 'Con requisitoria', 'Sin requisitoria' y 'Placa no registrada' (nunca
    sin_requisitoria): 200 con la forma del contrato; CONSULTA_PLACA con usuario, rol, motivo,
    parametros.placa, resultado y consulta_id; fila en consulta con estado completada."""
    r = _consultar(api, agente, consulta(placa))
    assert problemas_resultado(r, placa, resultado) == []
    d = r.json()
    ev = api.eventos(r.traza)
    assert tipos(ev) == ["CONSULTA_PLACA"], ev
    e = ev[0]
    assert e["rol"] == "agente" and e["usuario_id"]
    assert "control_vehicular" in str(e["motivo"])
    assert (e["parametros"] or {}).get("placa") == placa
    assert e["resultado"] == resultado
    assert str(e["consulta_id"]) == d["consulta_id"]
    assert e["es_sintetico"] is True
    fila = _fila_consulta(api, d["consulta_id"])
    assert fila["estado"] == "completada" and fila["placa"] == placa
    assert fila["resultado"] == resultado


def test_minusculas_y_espacios(api, agente):
    """§2 'Minúsculas y espacios' (decisión 6): ' zza-101 ' igual que ZZA-101."""
    r = _consultar(api, agente, consulta(" zza-101 "))
    assert problemas_resultado(r, PLACA_CON, "con_requisitoria") == []


def test_motivo_otro_con_texto(api, agente):
    """§2 + HU-07 §2: 'otro' con texto de ≥ 10 caracteres → 200; el motivo lleva su texto."""
    texto = "Revisión por pedido de fiscalía"
    r = _consultar(api, agente, consulta(PLACA_SIN, "otro", texto))
    assert problemas_resultado(r, PLACA_SIN, "sin_requisitoria", "otro", texto) == []
    (e,) = api.eventos(r.traza)
    assert "otro" in str(e["motivo"]) and texto in str(e["motivo"])


def _sin_rastro(api, r):
    """No deja evento (decisión 7) ni consulta."""
    assert api.eventos(r.traza) == []


@pytest.mark.parametrize("cuerpo", [
    pytest.param({"placa": PLACA_CON, "motivo_texto": None}, id="falta-motivo"),
    pytest.param(consulta(PLACA_CON, ""), id="motivo-vacio"),
    pytest.param(consulta(PLACA_CON, None), id="motivo-null"),
    pytest.param(consulta(PLACA_CON, "inventado"), id="motivo-fuera-del-catalogo"),
])
def test_sin_motivo(api, agente, cuerpo):
    """§2 'Sin motivo' (Gherkin esc. 2): 422 MOTIVO_REQUERIDO 'Indique el motivo de la consulta',
    sin consultar la fuente y sin evento. Con la fuente en error_500, si la API la consultara
    respondería 503."""
    api.modo_placas("error_500")
    r = _consultar(api, agente, cuerpo)
    assert problemas_error(r, "MOTIVO_REQUERIDO") == []
    assert r.json()["mensaje"] == MSG_SIN_MOTIVO
    _sin_rastro(api, r)


@pytest.mark.parametrize("texto", [None, "", "corto", "   123456789   "])
def test_otro_corto(api, agente, texto):
    """§2 '"Otro" corto': texto recortado < 10 → 422 MOTIVO_REQUERIDO 'Describa el motivo
    (mínimo 10 caracteres)', sin consultar la fuente."""
    api.modo_placas("error_500")
    r = _consultar(api, agente, consulta(PLACA_CON, "otro", texto))
    assert problemas_error(r, "MOTIVO_REQUERIDO") == []
    assert r.json()["mensaje"] == MSG_OTRO_CORTO
    _sin_rastro(api, r)


@pytest.mark.parametrize("placa", ["HOLA MUNDO", "ABC123", "AB-1234"])
def test_formato_invalido(api, agente, placa):
    """§2 'Formato inválido' (Gherkin esc. 4): 422 PLACA_FORMATO_INVALIDO con la descripción
    configurada, sin consultar la fuente."""
    api.modo_placas("error_500")
    r = _consultar(api, agente, consulta(placa))
    assert problemas_error(r, "PLACA_FORMATO_INVALIDO") == []
    assert r.json()["mensaje"] == MSG_FORMATO + FORMATO_DESCRIPCION
    _sin_rastro(api, r)


def test_faltan_los_dos(api, agente):
    """§2 'Faltan los dos' (decisión 7): primero el motivo."""
    r = _consultar(api, agente, consulta("HOLA MUNDO", None))
    assert problemas_error(r, "MOTIVO_REQUERIDO") == []


@pytest.mark.parametrize("cuerpo", [
    pytest.param({"crudo": b'{"placa": "ZZA-101", '}, id="json-mal-formado"),
    pytest.param({"json": {"motivo_codigo": "control_vehicular", "motivo_texto": None}},
                 id="falta-placa"),
])
def test_cuerpo_mal_formado(api, agente, cuerpo):
    """§2 'Cuerpo mal formado' → 422 SOLICITUD_INVALIDA."""
    r = api.pedir("POST", RUTA_PLACA, token=agente, **cuerpo)
    assert problemas_error(r, "SOLICITUD_INVALIDA") == []


# --- §3 Errores de la fuente -----------------------------------------------------------------

def _evento_error(api, r, codigo, placa=PLACA_CON):
    ev = api.eventos(r.traza)
    assert tipos(ev) == ["ERROR_FUENTE"], ev
    e = ev[0]
    assert e["rol"] == "agente" and e["usuario_id"]
    assert "control_vehicular" in str(e["motivo"])
    assert (e["parametros"] or {}).get("placa") == placa
    assert (e["parametros"] or {}).get("fuente") == "placas"
    assert e["resultado"] == "error" and e["codigo_error"] == codigo
    assert e["id_traza"] == r.traza and e["consulta_id"]
    fila = _fila_consulta(api, e["consulta_id"])
    assert fila["resultado"] == "error" and fila["estado"] == "error"


def _llamadas(api, desde, esperadas):
    n = api.llamadas_a_la_fuente(PLACA_CON, desde)
    if n is None:
        pytest.skip("NO VERIFICADO (solo el conteo): el log del simulador no trae líneas de "
                    "acceso; el código y la bitácora sí se verificaron")
    assert n == esperadas, f"la API llamó {n} veces a la fuente (se esperaban {esperadas})"


def test_fuente_caida(api, agente):
    """§3 'Fuente caída' (Gherkin esc. 3): error_500 → 503 FUENTE_NO_DISPONIBLE, ERROR_FUENTE,
    nunca sin_requisitoria; un solo reintento (2 llamadas, por el log del simulador)."""
    api.modo_placas("error_500")
    desde = api.ahora_docker()
    time.sleep(1)
    r = _consultar(api, agente, consulta(PLACA_CON))
    assert problemas_error(r, "FUENTE_NO_DISPONIBLE") == []
    assert "sin_requisitoria" not in r.texto
    _evento_error(api, r, "FUENTE_NO_DISPONIBLE")
    time.sleep(1)
    _llamadas(api, desde, 2)


def test_fuente_lenta(api, agente):
    """§3 'Fuente lenta': latencia 5000 ms > FUENTE_TIMEOUT_S=3 → 503 FUENTE_NO_DISPONIBLE tras
    un reintento, en ≤ 7 s. La duración se mide dentro del contenedor api (de la consulta a la
    solicitud siguiente del mismo lote): ~6 s son dos llamadas; una sola tardaría ~3 s. Además,
    el conteo por el log del simulador."""
    api.modo_placas("latencia", 5000)
    desde = api.ahora_docker()
    time.sleep(1)
    r, siguiente = api.lote([
        {"metodo": "POST", "ruta": RUTA_PLACA, "json": consulta(PLACA_CON), "token": agente},
        {"metodo": "GET", "ruta": "/v1/salud"},
    ])
    duracion = siguiente.enviada_en - r.enviada_en
    assert problemas_error(r, "FUENTE_NO_DISPONIBLE") == []
    assert "sin_requisitoria" not in r.texto
    _evento_error(api, r, "FUENTE_NO_DISPONIBLE")
    assert duracion <= 7.0, f"respondió en {duracion:.2f} s (> 7 s)"
    assert duracion >= 5.0, f"respondió en {duracion:.2f} s: parece una sola llamada"
    time.sleep(6)  # que terminen las llamadas lentas en el simulador antes de leer su log
    _llamadas(api, desde, 2)


def test_respuesta_fuera_de_contrato(api, agente):
    """§3 'Respuesta fuera de contrato' (decisión 8): malformada → 502
    FUENTE_RESPUESTA_INVALIDA sin reintento (1 llamada) y ERROR_FUENTE."""
    api.modo_placas("malformada")
    desde = api.ahora_docker()
    time.sleep(1)
    r = _consultar(api, agente, consulta(PLACA_CON))
    assert problemas_error(r, "FUENTE_RESPUESTA_INVALIDA") == []
    assert "sin_requisitoria" not in r.texto
    _evento_error(api, r, "FUENTE_RESPUESTA_INVALIDA")
    time.sleep(1)
    _llamadas(api, desde, 1)


def test_vuelve_la_fuente(api, agente):
    """§3 'Vuelve la fuente': tras un error, en normal la siguiente consulta funciona."""
    api.modo_placas("error_500")
    assert _consultar(api, agente, consulta(PLACA_CON)).estado == 503
    api.modo_placas("normal")
    assert problemas_resultado(_consultar(api, agente, consulta(PLACA_CON)),
                               PLACA_CON, "con_requisitoria") == []


# --- §7 Configuración del formato ------------------------------------------------------------

FORMATO_ALTERNO = {"PLACA_FORMATO_REGEX": "^ZZ[A-Z]-[0-9]{3}$",
                   "PLACA_FORMATO_DESCRIPCION": "ZZX-999 (formato de prueba)"}


@pytest.fixture
def config_formato(sistema):
    sistema.configurar(FORMATO_ALTERNO)
    sistema.modo_placas("normal")
    return sistema


def test_formato_configurable_sin_tocar_codigo(config_formato):
    """§7 'Formato de placa' y §1 'Formato de placa' (v3): con otra regex y otra descripción en
    el entorno, GET /v1/motivos las expone, el 422 usa la nueva descripción y la API valida con
    la nueva regex."""
    s = config_formato
    tok = s.token("agente1")
    fp = s.pedir("GET", RUTA_MOTIVOS, token=tok).json()["formato_placa"]
    assert fp == {"regex": FORMATO_ALTERNO["PLACA_FORMATO_REGEX"],
                  "descripcion": FORMATO_ALTERNO["PLACA_FORMATO_DESCRIPCION"]}
    # ZZ1-101 cumplía el formato por defecto y ya no cumple el nuevo.
    r = _consultar(s, tok, consulta("ZZ1-101"))
    assert problemas_error(r, "PLACA_FORMATO_INVALIDO") == []
    assert r.json()["mensaje"] == MSG_FORMATO + FORMATO_ALTERNO["PLACA_FORMATO_DESCRIPCION"]
    assert problemas_resultado(_consultar(s, tok, consulta(PLACA_CON)),
                               PLACA_CON, "con_requisitoria") == []
