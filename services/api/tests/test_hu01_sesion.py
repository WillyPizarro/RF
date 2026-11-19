"""CONTRATO-HU-01 v3 §3 — Renovación, cierre e inactividad (provisional, PA #18).

Ruta autenticada usada: `GET /v1/me` (CONTRATO-HU-02). Tiempos cortos por configuración (§6):
- `config_corta`: SESION_INACTIVIDAD_S=12, TOKEN_ACCESO_VIGENCIA_S=120.
- `config_token_corto`: TOKEN_ACCESO_VIGENCIA_S=6, SESION_INACTIVIDAD_S=600.
"""

from __future__ import annotations

import pytest

from ayudas_hu01 import (
    RUTA_LOGOUT, RUTA_ME, RUTA_REFRESH, problemas_error, problemas_login_ok, tipos,
)

USUARIO, ROL = "supervisor1", "supervisor"


def _sesion(s, clave):
    r = s.login(USUARIO, clave)
    assert r.estado == 200, r
    return r.json()


def _refresh(token_renovacion, **kw):
    return {"metodo": "POST", "ruta": RUTA_REFRESH,
            "json": {"token_renovacion": token_renovacion}, **kw}


def _me(token, **kw):
    return {"metodo": "GET", "ruta": RUTA_ME, "token": token, **kw}


def test_renovar(config_corta, clave):
    """§3 'Renovar': token_renovacion válido dentro de la inactividad → 200, misma forma que el
    login; el token nuevo sirve."""
    ses = _sesion(config_corta, clave)
    (r,) = config_corta.lote([_refresh(ses["token_renovacion"], esperar_s=3)])
    assert problemas_login_ok(r, USUARIO, ROL, expira_en=120, inactividad_s=12) == []
    assert config_corta.me(r.json()["token_acceso"]).estado == 200


def test_sin_token(config_defecto):
    """§3 'Sin token' → 401 NO_AUTENTICADO."""
    assert problemas_error(config_defecto.me(None), "NO_AUTENTICADO") == []


@pytest.mark.parametrize("token", ["no-es-un-token", "a.b.c"])
def test_token_basura(config_defecto, token):
    """§3 'firma inválida' → 401 NO_AUTENTICADO."""
    assert problemas_error(config_defecto.me(token), "NO_AUTENTICADO") == []


def test_firma_invalida(config_defecto, clave):
    """§3 'Token de acceso … firma inválida' → 401 NO_AUTENTICADO."""
    tok = _sesion(config_defecto, clave)["token_acceso"]
    cabeza, carga, firma = tok.rsplit(".", 2) if tok.count(".") == 2 else (tok, "", "")
    alterado = f"{cabeza}.{carga}.{firma[:-2]}{'AA' if not firma.endswith('AA') else 'BB'}"
    assert problemas_error(config_defecto.me(alterado), "NO_AUTENTICADO") == []


def test_token_vencido(config_token_corto, clave):
    """§3 'Token de acceso vencido' → 401 NO_AUTENTICADO (no SESION_VENCIDA)."""
    tok = _sesion(config_token_corto, clave)["token_acceso"]
    (r,) = config_token_corto.lote([_me(tok, esperar_s=9)])
    assert problemas_error(r, "NO_AUTENTICADO") == []


def test_logout_sin_token(config_defecto):
    """§3: logout es una ruta autenticada; sin token → 401 NO_AUTENTICADO."""
    r = config_defecto.pedir("POST", RUTA_LOGOUT)
    assert problemas_error(r, "NO_AUTENTICADO") == []


def test_inactividad_en_una_solicitud(config_corta, clave):
    """§3 'Inactividad en el servidor' (decisión 6, v3): una solicitud autenticada más de
    SESION_INACTIVIDAD_S después de la última solicitud autenticada o renovación → 401 SESION_VENCIDA, evento SESION_VENCIDA, y la
    sesión queda invalidada (renovar después también da 401)."""
    ses = _sesion(config_corta, clave)
    ok, vencida, renovar = config_corta.lote([
        _me(ses["token_acceso"]),
        _me(ses["token_acceso"], esperar_s=16),
        _refresh(ses["token_renovacion"]),
    ])
    assert ok.estado == 200, ok
    assert problemas_error(vencida, "SESION_VENCIDA") == []
    assert "SESION_VENCIDA" in tipos(config_corta.eventos(vencida.traza))
    assert renovar.estado == 401, renovar


def test_inactividad_en_la_renovacion(config_corta, clave):
    """§3 'Inactividad en el servidor': una renovación tras la inactividad → 401 SESION_VENCIDA
    con su evento; el token de acceso de esa sesión tampoco sirve."""
    ses = _sesion(config_corta, clave)
    renovar, me = config_corta.lote([
        _refresh(ses["token_renovacion"], esperar_s=16),
        _me(ses["token_acceso"]),
    ])
    assert problemas_error(renovar, "SESION_VENCIDA") == []
    assert "SESION_VENCIDA" in tipos(config_corta.eventos(renovar.traza))
    assert me.estado == 401, me


def test_la_actividad_mantiene_la_sesion(config_corta, clave):
    """§3: la inactividad cuenta desde la última solicitud autenticada. Con una solicitud cada
    6 s, la sesión sigue viva pasados 30 s (más del doble de SESION_INACTIVIDAD_S=12)."""
    ses = _sesion(config_corta, clave)
    rs = config_corta.lote([_me(ses["token_acceso"], esperar_s=6) for _ in range(5)]
                           + [_refresh(ses["token_renovacion"], esperar_s=6)])
    assert [r.estado for r in rs] == [200] * 6, rs


def test_cerrar_sesion(config_defecto, clave):
    """§3 'Cerrar sesión': 204, evento LOGOUT, y el token_renovacion deja de servir (401)."""
    ses = _sesion(config_defecto, clave)
    salir, renovar = config_defecto.lote([
        {"metodo": "POST", "ruta": RUTA_LOGOUT, "token": ses["token_acceso"]},
        _refresh(ses["token_renovacion"]),
    ])
    assert salir.estado == 204, salir
    assert salir.cuerpo == b""
    ev = config_defecto.eventos(salir.traza)
    assert tipos(ev) == ["LOGOUT"], ev
    assert ev[0]["usuario_id"] == ses["usuario"]["id"] and ev[0]["rol"] == ROL
    assert renovar.estado == 401, renovar


def test_la_renovacion_cuenta_como_actividad(config_corta, clave):
    """§3 v3: una renovación exitosa cuenta como actividad en el servidor. Solo renovando cada
    8 s (sin otras solicitudes autenticadas), la sesión sigue viva pasados 24 s (el doble de
    SESION_INACTIVIDAD_S=12), y el último token de acceso sirve 8 s después de su renovación."""
    ses = _sesion(config_corta, clave)
    renov = ses["token_renovacion"]
    acceso = None
    for _ in range(3):
        (r,) = config_corta.lote([_refresh(renov, esperar_s=8)])
        assert r.estado == 200, r
        renov, acceso = r.json()["token_renovacion"], r.json()["token_acceso"]
    (me,) = config_corta.lote([_me(acceso, esperar_s=8)])
    assert me.estado == 200, me
