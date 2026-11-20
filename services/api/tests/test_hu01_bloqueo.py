"""CONTRATO-HU-01 v5 §2 — Bloqueo por intentos (provisional, PA #19), y §1 "Éxito reinicia el
contador" / "Cuerpo inválido no cuenta como intento".

Con usuarios reales se usa la configuración corta (BLOQUEO_DURACION_S=12): cambiarla sin tocar
código es parte del contrato (§6). Los valores por defecto (5 intentos, 900 s) se prueban con un
usuario inexistente, que no deja ninguna cuenta real bloqueada.
"""

from __future__ import annotations

import time
from datetime import timedelta

import pytest

from ayudas_hu01 import (
    RUTA_LOGIN, ahora_utc, clave_mala, firma_error, iso_utc, problemas_error,
    problemas_login_ok, tipos, usuario_falso,
)

USUARIO = "agente2"  # el resto de las pruebas usa agente1, revisor1 y supervisor1


def _login(usuario, clave):
    return {"metodo": "POST", "ruta": RUTA_LOGIN, "json": {"usuario": usuario, "clave": clave}}


def _desbloqueado(s, usuario, clave, espera=40):
    """Precondición: la cuenta no está bloqueada y su contador está en 0 (un acierto)."""
    limite = time.monotonic() + espera
    while True:
        r = s.login(usuario, clave)
        if r.estado == 200:
            return
        assert r.estado == 423 and time.monotonic() < limite, f"no se pudo desbloquear: {r}"
        time.sleep(3)


def _fallos(s, usuario, n):
    return s.lote([_login(usuario, clave_mala()) for _ in range(n)])


@pytest.fixture
def cuenta(config_corta, clave):
    _desbloqueado(config_corta, USUARIO, clave)
    yield config_corta
    _desbloqueado(config_corta, USUARIO, clave)


def test_quinto_fallo_bloquea(cuenta):
    """§2 '5.º fallo seguido' (Gherkin esc. 4): 423 CUENTA_BLOQUEADA con bloqueado_hasta en
    ISO 8601 UTC; bitácora LOGIN_FALLIDO y CUENTA_BLOQUEADA."""
    rs = _fallos(cuenta, USUARIO, 5)
    for r in rs[:4]:
        assert problemas_error(r, "CREDENCIALES_INVALIDAS") == [], r
    r5 = rs[4]
    assert problemas_error(r5, "CUENTA_BLOQUEADA") == []
    hasta = iso_utc(r5.json()["bloqueado_hasta"])
    esperado = ahora_utc() + timedelta(seconds=12)
    assert abs((hasta - esperado).total_seconds()) < 15, f"bloqueado_hasta {hasta}"
    assert sorted(tipos(cuenta.eventos(r5.traza))) == ["CUENTA_BLOQUEADA", "LOGIN_FALLIDO"]


def test_durante_el_bloqueo_clave_correcta_o_incorrecta_identicas(cuenta, clave):
    """§2 'Clave correcta durante el bloqueo' y 'Clave incorrecta durante el bloqueo': el mismo
    423 con el mismo bloqueado_hasta (no se alarga); LOGIN_FALLIDO con codigo_error
    CUENTA_BLOQUEADA; nunca LOGIN_OK."""
    r5 = _fallos(cuenta, USUARIO, 5)[4]
    assert r5.estado == 423, r5
    buena, mala = cuenta.lote([_login(USUARIO, clave), _login(USUARIO, clave_mala())])
    for r in (buena, mala):
        assert problemas_error(r, "CUENTA_BLOQUEADA") == []
        assert r.json()["bloqueado_hasta"] == r5.json()["bloqueado_hasta"]
        ev = cuenta.eventos(r.traza)
        assert tipos(ev) == ["LOGIN_FALLIDO"], ev
        assert ev[0]["codigo_error"] == "CUENTA_BLOQUEADA"
    assert firma_error(buena) == firma_error(mala)
    assert "token_acceso" not in buena.texto


def test_fin_del_bloqueo(cuenta, clave):
    """§2 'Fin del bloqueo': clave correcta después de bloqueado_hasta → 200, contador en 0."""
    r5 = _fallos(cuenta, USUARIO, 5)[4]
    assert r5.estado == 423, r5
    falta = (iso_utc(r5.json()["bloqueado_hasta"]) - ahora_utc()).total_seconds()
    time.sleep(max(0.0, falta) + 2)
    assert problemas_login_ok(cuenta.login(USUARIO, clave), USUARIO, "agente",
                              expira_en=120, inactividad_s=12) == []
    # Contador en 0: otros 4 fallos no bloquean.
    for r in _fallos(cuenta, USUARIO, 4):
        assert problemas_error(r, "CREDENCIALES_INVALIDAS") == [], r


def test_exito_reinicia_el_contador(cuenta, clave):
    """§1 'Éxito reinicia el contador': 4 fallos + acierto → 200; hacen falta otros 5 fallos
    seguidos para bloquear."""
    rs = cuenta.lote([_login(USUARIO, clave_mala()) for _ in range(4)] + [_login(USUARIO, clave)]
                     + [_login(USUARIO, clave_mala()) for _ in range(5)])
    assert [r.estado for r in rs[:4]] == [401] * 4
    assert rs[4].estado == 200, rs[4]
    assert [r.estado for r in rs[5:9]] == [401] * 4, "el acierto no reinició el contador"
    assert problemas_error(rs[9], "CUENTA_BLOQUEADA") == []


def test_cuerpo_invalido_no_cuenta_como_intento(cuenta, clave):
    """§1 'Cuerpo inválido' (decisión 4): un 422 no cuenta como intento fallido."""
    invalidos = [
        {"metodo": "POST", "ruta": RUTA_LOGIN, "json": {"usuario": USUARIO}},
        {"metodo": "POST", "ruta": RUTA_LOGIN, "json": {"usuario": USUARIO, "clave": ""}},
        {"metodo": "POST", "ruta": RUTA_LOGIN, "crudo": b'{"usuario": "agente2",'},
    ]
    rs = cuenta.lote([_login(USUARIO, clave_mala()) for _ in range(4)] + invalidos
                     + [_login(USUARIO, clave)])
    assert [r.estado for r in rs[:4]] == [401] * 4
    assert [r.estado for r in rs[4:7]] == [422] * 3, rs[4:7]
    assert rs[7].estado == 200, f"los 422 contaron como intentos: {rs[7]}"


def test_usuario_inexistente_tambien_se_bloquea(config_corta):
    """§2 'Usuario inexistente' (decisión 5): 5 fallos seguidos → el mismo 423 con
    bloqueado_hasta, para no revelar qué usuarios existen."""
    falso = usuario_falso()
    rs = _fallos(config_corta, falso, 6)
    assert [r.estado for r in rs[:4]] == [401] * 4
    for r in rs[4:]:
        assert problemas_error(r, "CUENTA_BLOQUEADA") == []
        iso_utc(r.json()["bloqueado_hasta"])
    assert rs[5].json()["bloqueado_hasta"] == rs[4].json()["bloqueado_hasta"]


def test_valores_por_defecto_5_intentos_15_min(config_defecto):
    """ADR-0011 / §6: con infra/.env sin cambios, el 5.º fallo bloquea por 900 s."""
    falso = usuario_falso()
    rs = _fallos(config_defecto, falso, 5)
    assert [r.estado for r in rs[:4]] == [401] * 4
    assert problemas_error(rs[4], "CUENTA_BLOQUEADA") == []
    hasta = iso_utc(rs[4].json()["bloqueado_hasta"])
    assert abs((hasta - (ahora_utc() + timedelta(seconds=900))).total_seconds()) < 30, hasta


def _bloquear(s, usuario, clave_intento):
    """Lleva la cuenta a un bloqueo por un camino que fija el contrato (§2): intentos fallidos
    hasta recibir 423 (a lo sumo BLOQUEO_INTENTOS=5; si ya había uno vigente, el primero)."""
    for _ in range(5):
        r = s.login(usuario, clave_intento())
        if r.estado == 423:
            return r
        assert problemas_error(r, "CREDENCIALES_INVALIDAS") == [], r
    pytest.fail(f"{usuario}: 5 fallos seguidos no bloquearon")


@pytest.mark.parametrize("caso", ["clave-incorrecta", "inexistente", "inactivo"])
def test_fallo_despues_del_bloqueo_empieza_de_nuevo(config_corta, clave, caso):
    """§2 'Fallo después del bloqueo' (v5): un fallo después de bloqueado_hasta → 401
    CREDENCIALES_INVALIDAS (no 423) con LOGIN_FALLIDO; es el fallo 1, así que hacen falta otros
    5 seguidos para volver a bloquear."""
    s = config_corta
    if caso == "clave-incorrecta":
        usuario, intento = USUARIO, clave_mala
        _desbloqueado(s, USUARIO, clave)
    elif caso == "inexistente":
        usuario, intento = usuario_falso(), clave_mala
    else:
        usuario, intento = "inactivo1", (lambda: clave)

    bloqueo = _bloquear(s, usuario, intento)
    falta = (iso_utc(bloqueo.json()["bloqueado_hasta"]) - ahora_utc()).total_seconds()
    time.sleep(max(0.0, falta) + 2)

    rs = s.lote([_login(usuario, intento()) for _ in range(5)])
    assert problemas_error(rs[0], "CREDENCIALES_INVALIDAS") == [], rs[0]
    assert tipos(s.eventos(rs[0].traza)) == ["LOGIN_FALLIDO"]
    for r in rs[1:4]:
        assert problemas_error(r, "CREDENCIALES_INVALIDAS") == [], r
    assert problemas_error(rs[4], "CUENTA_BLOQUEADA") == [], "el 5.º fallo nuevo no volvió a bloquear"

    if caso == "clave-incorrecta":
        falta = (iso_utc(rs[4].json()["bloqueado_hasta"]) - ahora_utc()).total_seconds()
        time.sleep(max(0.0, falta) + 2)
        _desbloqueado(s, USUARIO, clave)
