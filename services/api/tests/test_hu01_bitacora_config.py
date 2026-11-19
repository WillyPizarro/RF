"""CONTRATO-HU-01 v2 §5 (bitácora y seguridad) y §6 (configuración y usuarios de prueba).

"Sin registro no hay sesión" (503 fail-closed): su prueba se hace en HU-07 (decisión 2), así que
aquí queda NO VERIFICADO.
"""

from __future__ import annotations

import re
import subprocess

import pytest

from ayudas_hu01 import (
    CAMPOS_EVENTO, RUTA_LOGOUT, USUARIO_INACTIVO, USUARIOS_ACTIVOS, clave_mala,
    problemas_error, problemas_login_ok,
)
from red_interna import leer_env

TIPOS = ("LOGIN_OK", "LOGIN_FALLIDO", "CUENTA_BLOQUEADA", "SESION_VENCIDA", "LOGOUT")


# --- §5 Bitácora y seguridad -----------------------------------------------------------------

def test_campos_de_cada_evento(config_defecto, clave):
    """§5 'Campos de cada evento': todas las filas de los eventos de HU-01 tienen id,
    ocurrido_en, usuario_id, rol, tipo_evento, parametros, codigo_error, id_traza y
    es_sintetico = true; id_traza no vacío."""
    ses = config_defecto.login("agente1", clave)
    config_defecto.pedir("POST", RUTA_LOGOUT, token=ses.json()["token_acceso"])
    config_defecto.login("agente1", clave_mala())
    filas = config_defecto.sql_json(
        "select * from bitacora where tipo_evento in ("
        + ",".join(f"'{t}'" for t in TIPOS) + ") order by id desc limit 500")
    assert filas, "no hay eventos de HU-01 en la bitácora"
    for f in filas:
        faltan = [c for c in CAMPOS_EVENTO if c not in f]
        assert not faltan, f"faltan columnas {faltan}"
        assert f["es_sintetico"] is True, f
        assert f["id_traza"], f
        assert f["ocurrido_en"], f
    vistos = {f["tipo_evento"] for f in filas}
    assert {"LOGIN_OK", "LOGIN_FALLIDO", "LOGOUT"} <= vistos


def test_id_traza_del_evento_igual_a_la_cabecera(config_defecto, clave):
    """§5: id_traza del evento = X-Id-Traza de la respuesta."""
    r = config_defecto.login("revisor1", clave)
    (e,) = config_defecto.eventos(r.traza)
    assert e["id_traza"] == r.traza


def test_la_clave_no_queda_en_la_bitacora(config_defecto, clave):
    """§5 'La clave no queda en ningún lado': ni la clave incorrecta (con marca única) ni la
    correcta aparecen en ninguna fila de la bitácora (parametros incluido)."""
    marca = clave_mala()
    config_defecto.login("agente1", marca)
    config_defecto.login("noexiste-x", marca)
    config_defecto.login("agente1", clave)
    assert config_defecto.bitacora_contiene(marca) == 0
    assert config_defecto.bitacora_contiene(clave) == 0


def test_la_clave_no_queda_en_los_logs_de_la_api(config_defecto, clave):
    """§5: el valor de `clave` no aparece en los logs de la API."""
    marca = clave_mala()
    config_defecto.login("agente1", marca)
    config_defecto.pedir("POST", "/v1/auth/login", json={"usuario": "agente1"},
                         cabeceras={"X-Marca": "x"})
    config_defecto.login("agente1", clave)
    r = config_defecto.compose("logs", "--no-color", "api")
    assert r.returncode == 0, r.stderr
    logs = r.stdout + r.stderr
    assert marca not in logs, "la clave incorrecta quedó en los logs de la API"
    assert clave not in logs, "la clave correcta quedó en los logs de la API"


def test_la_clave_no_queda_en_los_logs_del_proxy(config_defecto, clave):
    """§5: tampoco en los logs del proxy. Solo tiene sentido si el tráfico pasó por el proxy."""
    estado = config_defecto.compose("ps", "--format", "{{.Service}} {{.State}}", "proxy")
    if "running" not in estado.stdout:
        pytest.skip("NO VERIFICADO (entorno): el proxy no está corriendo (puerto 80 ocupado por "
                    "http.sys, ENCARGO-HU-01-02 regla 8)")
    logs = config_defecto.compose("logs", "--no-color", "proxy")
    assert clave not in logs.stdout + logs.stderr


@pytest.mark.skip(reason="NO VERIFICADO en HU-01: la prueba del fail-closed (fallo de escritura "
                         "de LOGIN_OK → 503) se hace en HU-07 (CONTRATO-HU-01 decisión 2)")
def test_sin_registro_no_hay_sesion():
    """§5 'Sin registro no hay sesión' → 503 SERVICIO_NO_DISPONIBLE, sin tokens."""


# --- §6 Configuración ------------------------------------------------------------------------

DEFECTOS = {"SESION_INACTIVIDAD_S": "600", "TOKEN_ACCESO_VIGENCIA_S": "900",
            "BLOQUEO_INTENTOS": "5", "BLOQUEO_DURACION_S": "900"}


@pytest.mark.parametrize("var,valor", sorted(DEFECTOS.items()))
def test_parametros_en_env_example(sistema, var, valor):
    """§6 'Parámetros': en infra/.env.example con su valor por defecto y marcados como
    provisionales (un comentario de su bloque dice 'provisional')."""
    lineas = (sistema.raiz / "infra" / ".env.example").read_text(encoding="utf-8").splitlines()
    i = next((k for k, ln in enumerate(lineas) if re.match(rf"^\s*{var}\s*=", ln)), None)
    assert i is not None, f"{var} no figura en infra/.env.example"
    assert lineas[i].split("=", 1)[1].split("#", 1)[0].strip() == valor, lineas[i]
    j = i
    while j > 0 and not lineas[j - 1].strip() == "":
        j -= 1
    bloque = "\n".join(lineas[j:i + 1]) + lineas[i]
    assert re.search(r"provisional", bloque, re.I), f"{var} no está marcado como provisional"


def test_cambiar_parametros_no_toca_codigo(config_corta, clave):
    """§6: con otros valores en el entorno (sin tocar código), el login los informa."""
    r = config_corta.login("agente1", clave)
    assert problemas_login_ok(r, "agente1", "agente", expira_en=120, inactividad_s=12) == []


def test_valores_por_defecto_en_el_login(config_defecto, clave):
    """§1 / §6: con infra/.env, expira_en 900 e inactividad_s 600 (ADR-0011)."""
    r = config_defecto.login("agente1", clave)
    assert problemas_login_ok(r, "agente1", "agente") == []


# --- §6 Usuarios de prueba -------------------------------------------------------------------

def _ids(s, clave):
    ids = {}
    for u, rol in USUARIOS_ACTIVOS.items():
        r = s.login(u, clave)
        assert problemas_login_ok(r, u, rol) == [], (u, r)
        ids[u] = r.json()["usuario"]["id"]
    return ids


def test_carga_de_usuarios_idempotente(config_defecto, clave):
    """§6 'Carga de usuarios' y 'Usuarios fijos': `python -m app.cargar_usuarios` en el
    contenedor api corre dos veces sin error; después siguen los mismos usuarios (mismos id),
    con su rol, e inactivo1 sigue inactivo."""
    antes = _ids(config_defecto, clave)
    for _ in range(2):
        r = config_defecto.compose("run", "--rm", "--no-deps", "-T", "api",
                                   "python", "-m", "app.cargar_usuarios", timeout=600)
        assert r.returncode == 0, f"cargar_usuarios falló:\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}"
        assert clave not in r.stdout + r.stderr, "cargar_usuarios imprime la clave"
    assert _ids(config_defecto, clave) == antes
    inactivo = config_defecto.login(USUARIO_INACTIVO, clave)
    assert problemas_error(inactivo, "CREDENCIALES_INVALIDAS") == []


def test_clave_de_usuarios_desde_el_entorno(sistema):
    """§6 'Claves': CLAVE_USUARIOS_PRUEBA vive en infra/.env (no versionado) y no aparece en
    ningún archivo versionado."""
    clave = leer_env(sistema.raiz / "infra" / ".env").get("CLAVE_USUARIOS_PRUEBA")
    assert clave, "CLAVE_USUARIOS_PRUEBA no está en infra/.env"
    g = subprocess.run(["git", "grep", "-l", "-F", "-e", clave], cwd=sistema.raiz,
                       capture_output=True, text=True)
    assert g.stdout.strip() == "", f"la clave aparece versionada en: {g.stdout}"
