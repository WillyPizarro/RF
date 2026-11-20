"""DoD criterio 5 — Los simuladores no son accesibles desde fuera.

SPRINT0.md §5: `docker compose -f infra/docker-compose.yml config` no publica puertos
para `simuladores`, `api` ni `db`; solo `proxy` publica 80 y 443 (o los alternos de
PROXY_PUERTO_HTTP / PROXY_PUERTO_HTTPS, ENCARGO-HU-03-07).
"""

import pytest

SERVICIOS_ESPERADOS = {"api", "simuladores", "proxy", "db"}


def _publicados(servicio: dict) -> set[str]:
    puertos = set()
    for p in servicio.get("ports") or []:
        if isinstance(p, dict):
            if p.get("published") not in (None, ""):
                puertos.add(str(p["published"]))
        else:  # sintaxis corta, por si la CLI no normaliza
            partes = str(p).split("/")[0].split(":")
            if len(partes) >= 2:
                puertos.add(partes[-2])
    return puertos


@pytest.fixture(scope="module")
def servicios(compose) -> dict:
    return compose.config_json()["services"]


def test_existen_los_cuatro_servicios(servicios):
    assert SERVICIOS_ESPERADOS <= set(servicios), sorted(servicios)


@pytest.mark.parametrize("nombre", ["simuladores", "api", "db"])
def test_servicio_interno_no_publica_puertos(servicios, nombre):
    assert nombre in servicios, f"No existe el servicio {nombre}"
    assert _publicados(servicios[nombre]) == set(), servicios[nombre].get("ports")


def test_proxy_publica_solo_sus_dos_puertos(servicios):
    """El proxy publica solo HTTP y HTTPS: PROXY_PUERTO_HTTP / PROXY_PUERTO_HTTPS de infra/.env
    si están definidos (puerto alterno, ENCARGO-HU-03-07), 80 y 443 si no."""
    from conftest import _env_infra

    env = _env_infra()
    esperados = {env.get("PROXY_PUERTO_HTTP") or "80", env.get("PROXY_PUERTO_HTTPS") or "443"}
    assert _publicados(servicios["proxy"]) == esperados, servicios["proxy"].get("ports")


def test_proxy_sin_variables_publica_80_y_443(compose, tmp_path):
    """ENCARGO-HU-03-07: sin PROXY_PUERTO_HTTP ni PROXY_PUERTO_HTTPS se publican 80 y 443 (VPS)."""
    from conftest import ENV_FILE

    lineas = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    sin = [ln for ln in lineas if not ln.strip().startswith(("PROXY_PUERTO_HTTP=",
                                                             "PROXY_PUERTO_HTTPS="))]
    env = tmp_path / "env-sin-puertos"
    env.write_text("\n".join(sin) + "\n", encoding="utf-8")
    cmd = [a for a in compose._base() if a != str(ENV_FILE)]
    if "--env-file" in cmd:
        cmd.remove("--env-file")
    import json
    import subprocess

    r = subprocess.run(cmd + ["--env-file", str(env), "config", "--format", "json"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stderr[-1500:]
    proxy = json.loads(r.stdout)["services"]["proxy"]
    assert _publicados(proxy) == {"80", "443"}, proxy.get("ports")


def test_solo_el_proxy_publica_puertos(servicios):
    con_puertos = {n for n, s in servicios.items() if _publicados(s)}
    assert con_puertos == {"proxy"}, con_puertos


def test_simuladores_no_responde_desde_el_anfitrion(cliente):
    """Por el proxy (único punto publicado), /salud de los simuladores no es alcanzable."""
    r = cliente.get("/salud")
    assert not (r.estado == 200 and r.texto.strip().replace(" ", "") == '{"estado":"ok"}'), (
        "El proxy expone el /salud de los simuladores"
    )


def test_api_alcanza_simuladores_por_la_red_interna(compose):
    """Contraparte: dentro de la red, http://simuladores:8001/salud sí responde (M-1 E)."""
    from conftest import URL_SIMULADORES_INTERNA

    r = compose.get_en_red(f"{URL_SIMULADORES_INTERNA}/salud", desde="api")
    assert r.estado == 200
    assert r.json() == {"estado": "ok"}
