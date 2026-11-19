"""CONTRATO-HU-08 v1 §8 — Aislamiento (Gherkin esc. 1: la app no se conecta directo al simulador).

Solo anfitrión. "Salud intacta" (`GET /v1/salud`) la cubren las pruebas del Sprint 0 de la API:
`docker compose -f infra/docker-compose.yml run --rm api pytest`.
"""

from __future__ import annotations

import json

import pytest

from conftest import compose
from ayudas_contrato import PLACA_CON, problemas_placa


def test_simuladores_sin_puerto_publicado(solo_anfitrion):
    """§8 'Sin puerto publicado': `docker compose config` no publica puertos de simuladores."""
    r = compose("config", "--format", "json")
    assert r.returncode == 0, r.stderr[-2000:]
    servicio = json.loads(r.stdout)["services"]["simuladores"]
    assert not servicio.get("ports"), f"simuladores publica: {servicio.get('ports')}"
    assert servicio.get("network_mode") != "host"


def test_caddyfile_no_enruta_a_simuladores(raiz_repo):
    """§8 'Ni el proxy': el Caddyfile no menciona simuladores ni 8001."""
    texto = (raiz_repo / "infra" / "Caddyfile").read_text(encoding="utf-8")
    assert "simuladores" not in texto.lower()
    assert "8001" not in texto


def test_app_no_conoce_el_simulador(raiz_repo):
    """§8 'Ni la app' (v4 C7): apps/movil/src/ no contiene ninguno de los textos exactos
    `//simuladores`, `simuladores:8001`, `:8001` ni `/placas/`. El campo `simuladores` de
    GET /v1/salud está permitido."""
    src = raiz_repo / "apps" / "movil" / "src"
    assert src.is_dir(), "no existe apps/movil/src/"
    hallazgos = []
    for f in src.rglob("*"):
        if f.is_file():
            texto = f.read_text(encoding="utf-8", errors="ignore")
            for patron in ("//simuladores", "simuladores:8001", ":8001", "/placas/"):
                if patron in texto:
                    hallazgos.append(f"{f.relative_to(raiz_repo)}: {patron}")
    assert not hallazgos, hallazgos


def test_desde_la_api_si(solo_anfitrion, cliente, modos_limpios):
    """§8 'Desde la API sí': desde el contenedor api, GET http://simuladores:8001/placas/ZZA-101
    → 200. Con --integracion el cliente hace la petición dentro del contenedor api."""
    assert cliente.via_api
    r = cliente.get(f"/placas/{PLACA_CON}")
    assert r.estado == 200 and problemas_placa(r.json(), PLACA_CON) == []
