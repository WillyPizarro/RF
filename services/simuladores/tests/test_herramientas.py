"""CONTRATO-HU-08 v3 — Herramientas de prueba (C5) y montaje de los yaml (C6).

C5: el contenedor `simuladores` trae un lector de YAML y un validador de JSON Schema.
C6: `infra/docker-compose.yml` monta `../contratos/fuentes` (solo lectura) en
`/app/contratos/fuentes` y define `CONTRATOS_FUENTES_DIR=/app/contratos/fuentes`.
"""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import pytest

from conftest import RAIZ_REPO, compose
from ayudas_contrato import YAMLS

DIR_DENTRO = "/app/contratos/fuentes"

dentro_del_contenedor = pytest.mark.skipif(
    RAIZ_REPO is not None, reason="Se verifica dentro del contenedor (docker compose run)"
)


@dentro_del_contenedor
@pytest.mark.parametrize("modulo", ["yaml", "jsonschema"])
def test_c5_dependencias_de_prueba_en_el_contenedor(modulo):
    importlib.import_module(modulo)


@dentro_del_contenedor
def test_c6_variable_y_yaml_montados():
    assert os.environ.get("CONTRATOS_FUENTES_DIR") == DIR_DENTRO
    for archivo in YAMLS.values():
        assert (Path(DIR_DENTRO) / archivo).is_file(), archivo


@dentro_del_contenedor
def test_c6_montaje_de_solo_lectura():
    prueba = Path(DIR_DENTRO) / ".escritura-tester"
    with pytest.raises(OSError):
        prueba.write_text("x")


def test_c6_en_el_compose(solo_anfitrion):
    r = compose("config", "--format", "json")
    assert r.returncode == 0, r.stderr[-2000:]
    sim = json.loads(r.stdout)["services"]["simuladores"]
    assert sim["environment"].get("CONTRATOS_FUENTES_DIR") == DIR_DENTRO
    vol = next((v for v in sim.get("volumes", []) if v.get("target") == DIR_DENTRO), None)
    assert vol is not None, sim.get("volumes")
    assert vol.get("read_only") is True
    assert Path(vol["source"]).resolve() == (RAIZ_REPO / "contratos" / "fuentes").resolve()
