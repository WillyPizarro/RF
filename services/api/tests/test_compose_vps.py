"""CONTRATO-DESPLIEGUE-01 v1 §1, §3 y §4 — Configuración del compose del VPS, en local (fase A).

`docker compose -f infra/docker-compose.yml -f infra/docker-compose.vps.yml config` (no levanta
nada). El `.env` que se usa se arma desde `infra/.env.example` (solo nombres y valores de ejemplo,
ningún secreto): se quitan `PROXY_PUERTO_*` (el VPS no los tiene; publica 80 y 443) y las
variables vacías se rellenan con un valor de prueba. Se borra al terminar.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from conftest import RAIZ_REPO

COMPOSE_BASE = "infra/docker-compose.yml"
COMPOSE_VPS = "infra/docker-compose.vps.yml"
FUERA_DE_LA_API = ("AUTH_ADMIN_CLAVE", "AUTH_JWT_SECRETO", "MIGRACION_DATABASE_URL",
                   "API_APP_CLAVE", "CLAVE_USUARIOS_PRUEBA")


@pytest.fixture(scope="module")
def env_vps(tmp_path_factory):
    if RAIZ_REPO is None:
        pytest.skip("Correr desde el repositorio en el anfitrión")
    lineas = []
    for ln in (RAIZ_REPO / "infra" / ".env.example").read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        nombre, valor = s.split("=", 1)
        if nombre.startswith("PROXY_PUERTO_"):
            continue  # el VPS publica 80 y 443 (DESPLIEGUE-01 decisión 3)
        lineas.append(f"{nombre}={valor or 'valor-de-prueba'}")
    ruta = tmp_path_factory.mktemp("env-vps") / "env"
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ruta


def _config(env, *perfiles) -> dict:
    cmd = ["docker", "compose", "-f", COMPOSE_BASE, "-f", COMPOSE_VPS, "--env-file", str(env)]
    for p in perfiles:
        cmd += ["--profile", p]
    r = subprocess.run(cmd + ["config", "--format", "json"], cwd=RAIZ_REPO, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout)


def _publicados(servicio: dict) -> set[str]:
    return {str(p.get("published")) for p in servicio.get("ports") or [] if p.get("published")}


@pytest.fixture(scope="module")
def vps(env_vps) -> dict:
    return _config(env_vps)["services"]


def test_solo_api_simuladores_y_proxy(vps):
    """§1 'Servicios': en el VPS corren api, simuladores y proxy; db y auth quedan fuera."""
    assert set(vps) == {"api", "simuladores", "proxy"}, sorted(vps)


def test_proxy_publica_80_y_443(vps):
    """§1 'Puertos' y decisión 3: solo el proxy publica, en 80 y 443."""
    assert _publicados(vps["proxy"]) == {"80", "443"}, vps["proxy"].get("ports")
    for nombre in ("api", "simuladores"):
        assert _publicados(vps[nombre]) == set(), (nombre, vps[nombre].get("ports"))


@pytest.mark.parametrize("variable", FUERA_DE_LA_API)
def test_la_api_no_recibe_credenciales_de_administracion(vps, variable):
    """§3 'Credencial de administración solo para la carga' (decisión 1) y M-1: la API en marcha
    no recibe AUTH_ADMIN_CLAVE ni AUTH_JWT_SECRETO (ni la URL del dueño, la clave de api_app
    suelta ni la de los usuarios)."""
    entorno = vps["api"].get("environment") or {}
    assert variable not in entorno, f"api recibe {variable}"


def test_sin_fotos_ni_pruebas_montadas(vps):
    """§1 'No se usa docker-compose.fotos.yml' y §4 'Solo datos sintéticos': simuladores no monta
    ningún origen de fotos; tampoco se montan las carpetas de pruebas."""
    for nombre in ("api", "simuladores"):
        destinos = {v.get("target") for v in vps[nombre].get("volumes") or []}
        assert "/fotos-origen" not in destinos, (nombre, destinos)
        assert "/app/tests" not in destinos, (nombre, destinos)


def test_herramientas_solo_con_su_perfil(env_vps):
    """Decisión 1: la credencial de administración la recibe solo el servicio que se corre a mano
    para migrar y cargar usuarios; no arranca con `up` (tiene perfil)."""
    servicios = _config(env_vps, "herramientas")["services"]
    otros = {n: s for n, s in servicios.items() if n not in ("api", "simuladores", "proxy")}
    assert otros, "no hay un servicio aparte para migrar y cargar usuarios"
    for nombre, s in otros.items():
        assert s.get("profiles"), f"{nombre} arrancaría con `up` (sin perfil)"
        assert not _publicados(s), f"{nombre} publica puertos"


def test_tambien_con_el_env_local(vps, env_vps):
    """Con el `.env` real de esta máquina (si existe), la API del modo VPS tampoco recibe las
    credenciales de administración."""
    env_local = RAIZ_REPO / "infra" / ".env"
    if not env_local.is_file():
        pytest.skip("sin infra/.env en este worktree")
    entorno = _config(env_local)["services"]["api"].get("environment") or {}
    presentes = [v for v in FUERA_DE_LA_API if v in entorno]
    assert not presentes, presentes
