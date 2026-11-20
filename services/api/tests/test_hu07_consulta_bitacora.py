"""CONTRATO-HU-07 v2 §4 — Consultar la bitácora (`GET /v1/bitacora`, rol supervisor).

Los 403 de agente y revisor están en test_hu03_mock_y_roles.py (matriz de CONTRATO-HU-02 §2).
La "verdad" para comparar filtros y paginación se lee directamente de la tabla `bitacora`.
"""

from __future__ import annotations

import json
from urllib.parse import urlencode

import pytest

from ayudas_hu01 import instante, problemas_error, tipos
from ayudas_hu03 import (
    CAMPOS_REGISTRO_API, PLACA_CON, PLACA_SIN, RUTA_BITACORA, RUTA_PLACA, consulta,
)


@pytest.fixture
def s(config_defecto):
    config_defecto.modo_placas("normal")
    return config_defecto


@pytest.fixture
def sup(s):
    return s.token("supervisor1")


def _get(s, tok, **params):
    q = urlencode({k: v for k, v in params.items() if v is not None})
    return s.pedir("GET", RUTA_BITACORA + (f"?{q}" if q else ""), token=tok)


def _orden(registros):
    claves = [(instante(r["ocurrido_en"]), r["id"]) for r in registros]
    return claves == sorted(claves, reverse=True)


def _consultas(s, n_con=2, n_sin=1):
    tok = s.token("agente1")
    rs = s.lote([{"metodo": "POST", "ruta": RUTA_PLACA, "json": consulta(PLACA_CON), "token": tok}
                 for _ in range(n_con)]
                + [{"metodo": "POST", "ruta": RUTA_PLACA, "json": consulta(PLACA_SIN), "token": tok}
                   for _ in range(n_sin)])
    assert all(r.estado == 200 for r in rs), rs
    return rs


def test_lista_forma_orden_y_limite_por_defecto(s, sup):
    """§4 'Lista' y 'Forma de un registro': 200 {registros, siguiente_cursor}; del más reciente al
    más antiguo; limite por defecto 50; cada registro con exactamente los campos del contrato."""
    _consultas(s)
    total = s.sql_json("select count(*) as n from bitacora")[0]["n"]
    r = _get(s, sup)
    assert r.estado == 200, r
    d = r.json()
    assert set(d) == {"registros", "siguiente_cursor"}, set(d)
    regs = d["registros"]
    assert len(regs) == min(50, total)
    if total > 50:
        assert isinstance(d["siguiente_cursor"], str) and d["siguiente_cursor"]
    for reg in regs:
        assert set(reg) == CAMPOS_REGISTRO_API, set(reg) ^ CAMPOS_REGISTRO_API
        assert reg["es_sintetico"] is True
    assert _orden(regs), "no está ordenado del más reciente al más antiguo"
    assert "identificad" not in r.texto.lower()


def test_usuario_es_el_nombre_de_usuario(s, sup):
    """§4 'Forma de un registro': `usuario` es el nombre de usuario (o null)."""
    _consultas(s, 1, 0)
    regs = _get(s, sup, tipo="CONSULTA_PLACA", limite=5).json()["registros"]
    assert regs and all(r["usuario"] == "agente1" for r in regs[:1]), regs[:1]
    nulos = _get(s, sup, tipo="LOGIN_FALLIDO", limite=100).json()["registros"]
    for reg in nulos:
        assert reg["usuario"] is None or isinstance(reg["usuario"], str)


@pytest.mark.parametrize("limite,esperado", [(1, 1), (100, 100)])
def test_limite(s, sup, limite, esperado):
    """§4 'Lista': limite entre 1 y 100."""
    total = s.sql_json("select count(*) as n from bitacora")[0]["n"]
    r = _get(s, sup, limite=limite)
    assert r.estado == 200, r
    assert len(r.json()["registros"]) == min(esperado, total)


def test_filtro_por_usuario(s, sup):
    _consultas(s, 1, 0)
    regs = _get(s, sup, usuario="agente1", limite=100).json()["registros"]
    assert regs and all(r["usuario"] == "agente1" for r in regs)


def test_filtro_por_tipo(s, sup):
    regs = _get(s, sup, tipo="CONSULTA_PLACA", limite=100).json()["registros"]
    assert regs and all(r["tipo_evento"] == "CONSULTA_PLACA" for r in regs)


def test_filtro_por_resultado(s, sup):
    _consultas(s, 1, 1)
    regs = _get(s, sup, resultado="con_requisitoria", limite=100).json()["registros"]
    assert regs and all(r["resultado"] == "con_requisitoria" for r in regs)


def test_filtro_por_fechas(s, sup):
    """§4 'Filtro por fechas': desde ≤ ocurrido_en < hasta. Se usan instantes de registros reales:
    el de `desde` entra; el de `hasta`, no."""
    _consultas(s, 3, 0)
    filas = s.sql_json("select id, ocurrido_en from bitacora order by ocurrido_en desc, id desc "
                       "limit 3")
    hasta, desde = filas[0]["ocurrido_en"], filas[2]["ocurrido_en"]
    regs = _get(s, sup, desde=desde, hasta=hasta, limite=100).json()["registros"]
    ids = {r["id"] for r in regs}
    esperados = {f["id"] for f in s.sql_json(
        f"select id from bitacora where ocurrido_en >= '{desde}'::timestamptz "
        f"and ocurrido_en < '{hasta}'::timestamptz")}
    assert ids == esperados
    assert filas[2]["id"] in ids and filas[0]["id"] not in ids


def test_filtros_combinados(s, sup):
    """§4 'Filtros combinados': se combinan con Y."""
    _consultas(s, 1, 1)
    regs = _get(s, sup, usuario="agente1", tipo="CONSULTA_PLACA", resultado="sin_requisitoria",
                limite=100).json()["registros"]
    assert regs
    assert all(r["usuario"] == "agente1" and r["tipo_evento"] == "CONSULTA_PLACA"
               and r["resultado"] == "sin_requisitoria" for r in regs)


def test_paginacion_sin_repetir_ni_saltar(s, sup):
    """§4 'Paginación': siguiendo siguiente_cursor hasta null se recorren todos los registros del
    filtro, sin repetir ni saltar, aunque entren registros nuevos mientras se pagina."""
    _consultas(s, 4, 3)
    verdad = [f["id"] for f in s.sql_json(
        "select id from bitacora where tipo_evento = 'CONSULTA_PLACA' "
        "order by ocurrido_en desc, id desc")]
    vistos: list[int] = []
    cursor = None
    paginas = 0
    while True:
        d = _get(s, sup, tipo="CONSULTA_PLACA", limite=3, cursor=cursor).json()
        vistos += [r["id"] for r in d["registros"]]
        cursor = d["siguiente_cursor"]
        paginas += 1
        if paginas == 2:
            _consultas(s, 2, 0)  # entran registros nuevos mientras se pagina
        if cursor is None:
            break
        assert paginas < 10000
    assert len(vistos) == len(set(vistos)), "se repitió un registro"
    faltan = set(verdad) - set(vistos)
    assert not faltan, f"se saltaron {len(faltan)} registros"
    assert [i for i in vistos if i in set(verdad)] == verdad, "el orden no es el del contrato"


@pytest.mark.parametrize("params", [
    {"desde": "ayer"}, {"hasta": "2026-13-45"}, {"tipo": "DESCONOCIDO"},
    {"limite": 0}, {"limite": 101}, {"limite": "x"}, {"cursor": "no-es-un-cursor"},
], ids=["desde", "hasta", "tipo", "limite-0", "limite-101", "limite-texto", "cursor"])
def test_parametro_invalido(s, sup, params):
    """§4 'Parámetro inválido' → 422 SOLICITUD_INVALIDA."""
    assert problemas_error(_get(s, sup, **params), "SOLICITUD_INVALIDA") == []


def test_la_consulta_se_registra(s, sup):
    """§4 'La consulta se registra': CONSULTA_BITACORA con los filtros usados en parametros."""
    r = _get(s, sup, usuario="agente1", tipo="CONSULTA_PLACA", resultado="con_requisitoria",
             limite=7)
    assert r.estado == 200, r
    ev = s.eventos(r.traza)
    assert tipos(ev) == ["CONSULTA_BITACORA"], ev
    params = json.dumps(ev[0]["parametros"])
    for valor in ("agente1", "CONSULTA_PLACA", "con_requisitoria"):
        assert valor in params, ev[0]["parametros"]
    assert ev[0]["rol"] == "supervisor"
