"""DoD criterio 5 — Los simuladores no son accesibles desde fuera.

SPRINT0.md §5: `docker compose -f infra/docker-compose.yml config` no publica puertos
para `simuladores`, `api` ni `db`; solo `proxy` publica 80 y 443.
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


def test_proxy_publica_solo_80_y_443(servicios):
    assert _publicados(servicios["proxy"]) == {"80", "443"}, servicios["proxy"].get("ports")


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
