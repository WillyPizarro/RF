"""CONTRATO-HU-01 v2 §1 — Iniciar sesión (`POST /v1/auth/login`), con la configuración por
defecto de infra/.env. Por la red interna (ENCARGO-HU-01-02 regla 8).

Incluye la prueba pendiente del Sprint 0: 422 `SOLICITUD_INVALIDA` con el formato de error
estándar (docs/contratos/PENDIENTES.md, SPRINT0 M-2).
"""

import pytest

from ayudas_hu01 import (
    RUTA_LOGIN, USUARIO_INACTIVO, USUARIOS_ACTIVOS, ahora_utc, clave_mala, firma_error,
    instante, precondicion_sin_bloqueo_vigente, problemas_error, problemas_login_ok, tipos,
    usuario_falso,
)


@pytest.mark.parametrize("usuario,rol", sorted(USUARIOS_ACTIVOS.items()))
def test_camino_feliz(config_defecto, clave, usuario, rol):
    """§1 'Camino feliz' (Gherkin esc. 1): 200 con tokens, expira_en 900, inactividad_s 600."""
    r = config_defecto.login(usuario, clave)
    assert problemas_login_ok(r, usuario, rol) == []


def test_camino_feliz_deja_login_ok(config_defecto, clave):
    """§1 + §5: bitácora LOGIN_OK con usuario_id, rol, ocurrido_en (UTC, del servidor),
    id_traza = X-Id-Traza y es_sintetico true."""
    antes = ahora_utc()
    r = config_defecto.login("agente1", clave)
    assert r.estado == 200, r
    ev = config_defecto.eventos(r.traza)
    assert tipos(ev) == ["LOGIN_OK"], ev
    e = ev[0]
    assert e["usuario_id"] == r.json()["usuario"]["id"]
    assert e["rol"] == "agente"
    assert e["id_traza"] == r.traza
    assert e["es_sintetico"] is True
    assert e["codigo_error"] in (None, "")
    # timestamptz: se compara el instante absoluto (la zona de la sesión de psql no importa).
    ocurrido = instante(e["ocurrido_en"])
    assert abs((ocurrido - antes).total_seconds()) < 120, "ocurrido_en no es la hora del servidor"


def test_clave_incorrecta(config_defecto):
    """§1 'Clave incorrecta' (Gherkin esc. 2): 401 CREDENCIALES_INVALIDAS + LOGIN_FALLIDO."""
    r = config_defecto.login("revisor1", clave_mala())
    assert problemas_error(r, "CREDENCIALES_INVALIDAS") == []
    ev = config_defecto.eventos(r.traza)
    assert tipos(ev) == ["LOGIN_FALLIDO"], ev
    assert ev[0]["usuario_id"] is not None
    assert ev[0]["es_sintetico"] is True


def test_usuario_inexistente_identico(config_defecto):
    """§1 'Usuario inexistente': idéntico a clave incorrecta; LOGIN_FALLIDO con usuario_id
    nulo y el texto de `usuario` en parametros."""
    falso = usuario_falso()
    mala = config_defecto.login("revisor1", clave_mala())
    r = config_defecto.login(falso, clave_mala())
    assert problemas_error(r, "CREDENCIALES_INVALIDAS") == []
    assert firma_error(r) == firma_error(mala)
    ev = config_defecto.eventos(r.traza)
    assert tipos(ev) == ["LOGIN_FALLIDO"], ev
    assert ev[0]["usuario_id"] is None
    assert falso in str(ev[0]["parametros"])


def test_usuario_inactivo_identico(config_intentos_alto, clave):
    """§1 'Usuario inactivo' (decisión 3): idéntico a clave incorrecta, con clave correcta.
    Veredicto A2: con BLOQUEO_INTENTOS=1000 (§6) el contador de inactivo1 no puede llegar al
    bloqueo, sea cual sea su valor previo."""
    s = config_intentos_alto
    precondicion_sin_bloqueo_vigente(s.login(USUARIO_INACTIVO, clave), USUARIO_INACTIVO)
    mala = s.login("revisor1", clave_mala())
    r = s.login(USUARIO_INACTIVO, clave)
    assert problemas_error(r, "CREDENCIALES_INVALIDAS") == []
    assert firma_error(r) == firma_error(mala)
    assert tipos(s.eventos(r.traza)) == ["LOGIN_FALLIDO"]


CUERPOS_INVALIDOS = [
    pytest.param({"json": {"clave": "x"}}, id="falta-usuario"),
    pytest.param({"json": {"usuario": "agente1"}}, id="falta-clave"),
    pytest.param({"json": {"usuario": "", "clave": "x"}}, id="usuario-vacio"),
    pytest.param({"json": {"usuario": "agente1", "clave": ""}}, id="clave-vacia"),
    pytest.param({"json": {}}, id="objeto-vacio"),
    pytest.param({"crudo": b'{"usuario": "agente1", "clave": '}, id="json-mal-formado"),
]


@pytest.mark.parametrize("cuerpo", CUERPOS_INVALIDOS)
def test_cuerpo_invalido_422(config_defecto, cuerpo):
    """§1 'Cuerpo inválido' + PENDIENTES (Sprint 0): 422 SOLICITUD_INVALIDA con el formato
    estándar {codigo, mensaje, id_traza} e id_traza = X-Id-Traza; no deja evento."""
    r = config_defecto.pedir("POST", RUTA_LOGIN, **cuerpo)
    assert problemas_error(r, "SOLICITUD_INVALIDA") == []
    assert set(r.json()) == {"codigo", "mensaje", "id_traza"}, r.json()
    assert config_defecto.eventos(r.traza) == []


def test_sin_palabra_prohibida(config_defecto, clave):
    """AGENTS.md regla 1 en las respuestas de login."""
    for r in (config_defecto.login("agente1", clave), config_defecto.login("agente1", "x")):
        assert "identificad" not in r.texto.lower()
