"""CONTRATO-HU-02 v2 §1 y §2 — Perfil (`GET /v1/me`) y rechazo por rol.

§2 (matriz de 403): en esta HU no existe ninguna ruta reservada a un rol; su prueba con rutas
reales viaja a HU-03 y HU-07 (decisión 3). Aquí queda NO VERIFICADO.
"""

from __future__ import annotations

import pytest

from ayudas_hu01 import (
    USUARIOS_ACTIVOS, jwt_con_rol, problemas_error, tipos,
)


@pytest.mark.parametrize("usuario,rol", sorted(USUARIOS_ACTIVOS.items()))
def test_perfil(config_defecto, clave, usuario, rol):
    """§1 'Perfil': 200 {id, usuario, nombre, rol}, el mismo usuario del login."""
    login = config_defecto.login(usuario, clave)
    assert login.estado == 200, login
    r = config_defecto.me(login.json()["token_acceso"])
    assert r.estado == 200, r
    d = r.json()
    assert set(d) == {"id", "usuario", "nombre", "rol"}, d
    assert d["id"] == login.json()["usuario"]["id"]
    assert d["usuario"] == usuario and d["rol"] == rol
    assert isinstance(d["nombre"], str) and d["nombre"].strip()
    assert "identificad" not in r.texto.lower()


def test_sin_token_401_sin_acceso_denegado(config_defecto):
    """§1 'Sin token' y §2 'Primero autenticación' (decisión 2): 401 NO_AUTENTICADO y ningún
    evento ACCESO_DENEGADO."""
    r = config_defecto.me(None)
    assert problemas_error(r, "NO_AUTENTICADO") == []
    assert "ACCESO_DENEGADO" not in tipos(config_defecto.eventos(r.traza))


@pytest.mark.parametrize("rol_declarado", ["supervisor", "revisor"])
def test_rol_manipulado_no_valida(config_defecto, clave, rol_declarado):
    """§1 'El rol sale del servidor': un token manipulado para declarar otro rol → 401."""
    tok = config_defecto.login("agente1", clave).json()["token_acceso"]
    r = config_defecto.me(jwt_con_rol(tok, rol_declarado))
    assert problemas_error(r, "NO_AUTENTICADO") == []


def test_rol_enviado_por_el_cliente_se_ignora(config_defecto, clave):
    """§1: el rol nunca se toma de lo que envía el cliente (ni cabeceras ni query)."""
    tok = config_defecto.login("agente1", clave).json()["token_acceso"]
    r = config_defecto.pedir("GET", "/v1/me?rol=supervisor", token=tok,
                             cabeceras={"X-Rol": "supervisor", "X-Role": "supervisor"})
    assert r.estado == 200 and r.json()["rol"] == "agente", r


@pytest.mark.skip(reason="NO VERIFICADO en HU-01/02: no existe ninguna ruta reservada a un rol; "
                         "la matriz de 403 se prueba en HU-03 y HU-07 (CONTRATO-HU-02 decisión 3)")
def test_matriz_403_sin_permiso():
    """§2 'Ruta de otro rol' → 403 SIN_PERMISO + ACCESO_DENEGADO; 'Sin efecto'."""
