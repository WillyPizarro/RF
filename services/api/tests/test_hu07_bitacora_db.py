"""CONTRATO-HU-07 v2 §1 (solo inserción), §2 (contenido) y §3 (fail-closed), más el fail-closed
del login de CONTRATO-HU-01 §5 (pasó a HU-07).

La base se toca con `psql` dentro de `db`, como POSTGRES_USER (superusuario del Postgres local):
con `SET ROLE api_app` o `SET ROLE <dueño de bitacora>` para actuar como esos roles. Toda operación
destructiva va en una transacción que termina en ROLLBACK, para que ni siquiera un trigger ausente
pueda borrar datos. El REVOKE del fail-closed (decisión 3) se restaura siempre.
"""

from __future__ import annotations

import json
import re
import subprocess
import uuid

import pytest

from ayudas_hu01 import problemas_error, tipos
from ayudas_hu03 import COLUMNAS_BITACORA, PLACA_CON, RUTA_BITACORA, RUTA_PLACA, TIPOS_ITERACION, consulta
from red_interna import leer_env

MENSAJE_TRIGGER = "bitacora es de solo insercion"


@pytest.fixture
def s(config_defecto):
    config_defecto.modo_placas("normal")
    return config_defecto


def _un_id(s) -> int:
    filas = s.sql_json("select id from bitacora order by ocurrido_en desc, id desc limit 1")
    assert filas, "la bitácora está vacía"
    return filas[0]["id"]


def _foto(s, id_):
    return s.sql_json(f"select * from bitacora where id::text = '{id_}'")


def _dueno(s) -> str:
    return s.sql_json("select tableowner from pg_tables where tablename = 'bitacora'")[0]["tableowner"]


# --- §1 Solo inserción -----------------------------------------------------------------------

def test_la_api_usa_api_app(s):
    """§1 'La API usa api_app': las conexiones del contenedor api a Postgres son de api_app."""
    s.token("agente1")  # una solicitud que escribe en la bitácora
    ip = subprocess.run(
        ["docker", "inspect", "movil-buscador-api-1", "--format",
         "{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}"],
        capture_output=True, text=True).stdout.split()
    assert ip, "sin IP del contenedor api"
    lista = ",".join(f"'{x}'" for x in ip)
    filas = s.sql_json(f"select distinct usename from pg_stat_activity "
                       f"where host(client_addr) in ({lista})")
    usuarios = {f["usename"] for f in filas}
    assert usuarios == {"api_app"}, f"conexiones de la API: {usuarios}"
    assert _dueno(s) != "api_app"


def test_permisos_de_api_app(s):
    """§1 'Permisos': INSERT y SELECT sí; UPDATE, DELETE y TRUNCATE no."""
    privs = s.sql_json(
        "select " + ", ".join(f"has_table_privilege('api_app', 'bitacora', '{p}') as {p.lower()}"
                              for p in ("INSERT", "SELECT", "UPDATE", "DELETE", "TRUNCATE")))[0]
    assert privs == {"insert": True, "select": True, "update": False, "delete": False,
                     "truncate": False}, privs


SENTENCIAS = {
    "update": "update bitacora set motivo = 'x' where id::text = '{id}'",
    "delete": "delete from bitacora where id::text = '{id}'",
    "truncate": "truncate bitacora",
}


@pytest.mark.parametrize("op", sorted(SENTENCIAS))
def test_api_app_no_puede_modificar(s, op):
    """§1 'UPDATE / DELETE / TRUNCATE como api_app' (Gherkin esc. 2): error; el registro queda."""
    id_ = _un_id(s)
    antes = _foto(s, id_)
    total = s.sql_json("select count(*) as n from bitacora")[0]["n"]
    r = s.psql(f"begin;\nset role api_app;\n{SENTENCIAS[op].format(id=id_)};\nrollback;\n")
    assert r.returncode != 0, f"{op} como api_app no dio error"
    assert re.search(r"permission denied|permiso denegado", r.stderr, re.I), r.stderr
    assert _foto(s, id_) == antes
    assert s.sql_json("select count(*) as n from bitacora")[0]["n"] >= total


@pytest.mark.parametrize("op", sorted(SENTENCIAS))
def test_el_dueno_tampoco_por_el_trigger(s, op):
    """§1 'Mismo intento como dueño' (decisión 2): error del trigger con
    'bitacora es de solo insercion'; los registros quedan iguales."""
    id_ = _un_id(s)
    antes = _foto(s, id_)
    dueno = _dueno(s)
    r = s.psql(f'begin;\nset role "{dueno}";\n{SENTENCIAS[op].format(id=id_)};\nrollback;\n')
    assert r.returncode != 0, f"{op} como dueño ({dueno}) no dio error"
    assert MENSAJE_TRIGGER in r.stderr, r.stderr
    assert _foto(s, id_) == antes


def test_base_recien_migrada(s):
    """§1 'Base recién migrada' (v2): `run --rm api alembic upgrade head` con
    MIGRACION_DATABASE_URL apuntando a una base vacía deja la tabla, los permisos y los
    triggers listos."""
    env = leer_env(s.env_base)
    base_url = env.get("MIGRACION_DATABASE_URL") or env.get("DATABASE_URL")
    assert base_url, "sin MIGRACION_DATABASE_URL ni DATABASE_URL en infra/.env"
    nueva = "tester_migr_" + uuid.uuid4().hex[:8]
    url = re.sub(r"/[^/?]+(\?|$)", f"/{nueva}\\1", base_url.rsplit("@", 1)[1], count=1)
    url = base_url.rsplit("@", 1)[0] + "@" + url
    assert s.psql(f"create database {nueva};\n").returncode == 0
    try:
        r = s.compose("run", "--rm", "--no-deps", "-T", "-e", f"MIGRACION_DATABASE_URL={url}",
                      "api", "alembic", "upgrade", "head", timeout=600)
        assert r.returncode == 0, f"la migración falló:\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}"
        clave_url = base_url.rsplit("@", 1)[0].rsplit(":", 1)[-1]
        if len(clave_url) >= 6:
            assert clave_url not in r.stdout + r.stderr, "la migración imprime la clave de la base"
        q = lambda sql: [json.loads(x) for x in s.psql(  # noqa: E731
            f"select row_to_json(t) from ({sql}) t;\n", db=nueva).stdout.splitlines() if x]
        assert q("select 1 as x from pg_tables where tablename = 'bitacora'"), "sin bitacora"
        cols = {f["column_name"] for f in q(
            "select column_name from information_schema.columns where table_name = 'bitacora'")}
        assert set(COLUMNAS_BITACORA) <= cols, set(COLUMNAS_BITACORA) - cols
        privs = q("select " + ", ".join(
            f"has_table_privilege('api_app', 'bitacora', '{p}') as {p.lower()}"
            for p in ("INSERT", "SELECT", "UPDATE", "DELETE", "TRUNCATE")))[0]
        assert privs == {"insert": True, "select": True, "update": False, "delete": False,
                         "truncate": False}, privs
        dueno = q("select tableowner from pg_tables where tablename = 'bitacora'")[0]["tableowner"]
        prueba = s.psql(f'begin;\nset role "{dueno}";\ntruncate bitacora;\nrollback;\n', db=nueva)
        assert prueba.returncode != 0 and MENSAJE_TRIGGER in prueba.stderr, prueba.stderr
    finally:
        s.psql(f"drop database if exists {nueva} with (force);\n")


@pytest.mark.parametrize("metodo", ["PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize("ruta", [RUTA_BITACORA, RUTA_BITACORA + "/1"])
def test_sin_ruta_de_edicion(s, metodo, ruta):
    """§1 'Sin ruta de edición': PUT, PATCH o DELETE sobre /v1/bitacora* → 405."""
    r = s.pedir(metodo, ruta, token=s.token("supervisor1"), json={})
    assert problemas_error(r, "METODO_NO_PERMITIDO") == []


# --- §2 Contenido ----------------------------------------------------------------------------

def test_columnas(s):
    """§2 'Columnas'."""
    cols = {f["column_name"] for f in s.sql_json(
        "select column_name from information_schema.columns where table_name = 'bitacora'")}
    assert set(COLUMNAS_BITACORA) <= cols, set(COLUMNAS_BITACORA) - cols
    assert s.sql_json("select count(*) as n from bitacora where es_sintetico is not true")[0]["n"] == 0


def test_eventos_de_la_iteracion(al_final, inicio_sesion_pruebas):
    """§2 'Eventos de esta iteración': cada tipo se generó en al menos una prueba de esta
    sesión (corre al final de la suite)."""
    filas = al_final.sql_json(
        "select distinct tipo_evento from bitacora "
        f"where ocurrido_en >= '{inicio_sesion_pruebas}'::timestamptz")
    vistos = {f["tipo_evento"] for f in filas}
    faltan = set(TIPOS_ITERACION) - vistos
    assert not faltan, f"tipos no generados en la sesión: {sorted(faltan)}"


FIRMAS_B64 = ("iVBORw0KGgo", "/9j/", "R0lGOD", "UklGR")  # PNG, JPEG, GIF, WEBP en base64


def test_sin_imagen_ni_clave(al_final):
    """§2 'Sin imagen ni clave': ningún registro tiene la clave de un login ni datos de imagen
    (firmas base64 de imagen o tiras base64 de 255 o más caracteres; 255 es el máximo de
    repeticiones de las expresiones de Postgres, veredicto HU-03/07 A3)."""
    s = al_final
    assert s.bitacora_contiene(s.clave_pruebas()) == 0
    for firma in FIRMAS_B64:
        assert s.bitacora_contiene(firma) == 0, f"hay un registro con {firma}"
    largas = s.sql_json("select id from bitacora where parametros::text ~ '[A-Za-z0-9+/=]{255,}'")
    assert largas == [], f"registros con una tira base64 larga: {largas[:5]}"


# --- §3 Fail-closed --------------------------------------------------------------------------

@pytest.fixture
def sin_insert(s):
    """Decisión 3: REVOKE INSERT ON bitacora FROM api_app, restaurado siempre. El token se pide
    antes, porque el login también escribe en la bitácora."""
    token = s.token("agente1")
    r = s.psql("revoke insert on bitacora from api_app;\n")
    assert r.returncode == 0, r.stderr
    try:
        yield s, token
    finally:
        r = s.psql("grant insert on bitacora to api_app;\n")
        assert r.returncode == 0, f"NO SE PUDO RESTAURAR EL INSERT: {r.stderr}"


def test_fail_closed_consulta(sin_insert):
    """§3 'Falla la escritura' y HU-03 §5: consulta válida → 503 SERVICIO_NO_DISPONIBLE, sin el
    resultado."""
    s, token = sin_insert
    r = s.pedir("POST", RUTA_PLACA, json=consulta(PLACA_CON), token=token)
    assert problemas_error(r, "SERVICIO_NO_DISPONIBLE") == []
    assert "resultado" not in r.json() and "requisitoria" not in r.texto


def test_fail_closed_login(sin_insert):
    """§3 'Lo mismo en el login' y CONTRATO-HU-01 §5: login válido → 503
    SERVICIO_NO_DISPONIBLE, sin tokens."""
    s, _ = sin_insert
    r = s.login("agente1", s.clave_pruebas())
    assert problemas_error(r, "SERVICIO_NO_DISPONIBLE") == []
    assert "token_acceso" not in r.texto and "token_renovacion" not in r.texto


def test_al_restaurar_vuelve_a_la_normalidad(s):
    """§3: al restaurar el permiso, todo vuelve a la normalidad."""
    assert s.psql("revoke insert on bitacora from api_app;\n").returncode == 0
    assert s.psql("grant insert on bitacora to api_app;\n").returncode == 0
    tok = s.token("agente1")
    r = s.pedir("POST", RUTA_PLACA, json=consulta(PLACA_CON), token=tok)
    assert r.estado == 200, r
    assert tipos(s.eventos(r.traza)) == ["CONSULTA_PLACA"]
