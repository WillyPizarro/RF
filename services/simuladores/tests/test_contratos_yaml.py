"""CONTRATO-HU-08 v1 §6 — Contratos documentados (`contratos/fuentes/*.yaml`).

Contrato v3 C5/C6: el contenedor `simuladores` trae pyyaml y jsonschema y monta los yaml en
CONTRATOS_FUENTES_DIR. En el anfitrión se usan los del repositorio. Si faltan, las pruebas se
omiten con el motivo; que C5 y C6 se cumplan lo verifica test_herramientas.py.
La validación OpenAPI 3.1 completa usa openapi-spec-validator si está instalado (anfitrión,
requirements-pruebas.txt); si no, se omite solo esa prueba.
"""

from __future__ import annotations

import re

import pytest

yaml = pytest.importorskip("yaml", reason="falta pyyaml (requirements-pruebas.txt)")
pytest.importorskip("jsonschema", reason="falta jsonschema (requirements-pruebas.txt)")

from conftest import RAIZ_REPO  # noqa: E402
from ayudas_contrato import (  # noqa: E402
    buscar_dir_contratos, CAMPOS_PERSONA, CAMPOS_PLACA, CAMPOS_REQUISITORIA, PALABRA_PROHIBIDA, PERSONA_EXISTE,
    PERSONA_NO_EXISTE, PLACA_CON, PLACA_NO_EXISTE, PLACA_SIN, YAMLS, cargar_yaml,
    errores_contra_yaml,
)

FUENTES = tuple(YAMLS)

RUTAS_CONTRATO = {
    "placas": {"/placas/{placa}"},
    "requisitorias-personas": {"/personas/{persona_id}", "/personas/{persona_id}/fotos/{foto_id}"},
    "galeria": {"/galeria"},
}
CAMPOS = {
    "placas": set(CAMPOS_PLACA) | set(CAMPOS_REQUISITORIA),
    "requisitorias-personas": set(CAMPOS_PERSONA) | set(CAMPOS_REQUISITORIA),
    "galeria": {"version", "personas", "persona_id", "foto_ids", "es_sintetico"},
}
CODIGOS = {
    "placas": {"PLACA_NO_REGISTRADA"},
    "requisitorias-personas": {"PERSONA_NO_REGISTRADA", "FOTO_NO_DISPONIBLE"},
    "galeria": set(),  # §3 no define errores propios de la galería
}
# Respuestas del simulador en modo normal (200 y 404) que deben validar contra su yaml.
MUESTRAS = {
    "placas": [f"/placas/{PLACA_CON}", f"/placas/{PLACA_SIN}", f"/placas/{PLACA_NO_EXISTE}",
               f"/placas/{PLACA_CON.lower()}"],
    "requisitorias-personas": [f"/personas/{PERSONA_EXISTE}", f"/personas/{PERSONA_NO_EXISTE}",
                               f"/personas/{PERSONA_EXISTE}/fotos/inexistente"],
    "galeria": ["/galeria"],
}


@pytest.fixture(scope="module")
def dir_fuentes():
    d = buscar_dir_contratos(RAIZ_REPO)
    if d is None:
        pytest.skip("No se encuentran los yaml (ni CONTRATOS_FUENTES_DIR ni el repositorio)")
    return d


def _texto(dir_fuentes, fuente):
    return (dir_fuentes / YAMLS[fuente]).read_text(encoding="utf-8")


def _propiedades(obj, acc=None):
    acc = set() if acc is None else acc
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "properties" and isinstance(v, dict):
                acc |= set(v)
            if k == "required" and isinstance(v, list):
                acc |= {x for x in v if isinstance(x, str)}
            _propiedades(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _propiedades(v, acc)
    return acc


# --- Existen y son OpenAPI 3.1 válidos ------------------------------------------------------

@pytest.mark.parametrize("fuente", FUENTES)
def test_existe(dir_fuentes, fuente):
    assert (dir_fuentes / YAMLS[fuente]).is_file()


@pytest.mark.parametrize("fuente", FUENTES)
def test_openapi_31_valido(dir_fuentes, fuente):
    pytest.importorskip("openapi_spec_validator",
                        reason="falta openapi-spec-validator (requirements-pruebas.txt)")
    from openapi_spec_validator import validate
    from openapi_spec_validator.validation import OpenAPIV31SpecValidator

    doc = cargar_yaml(dir_fuentes, fuente)
    assert str(doc.get("openapi", "")).startswith("3.1"), doc.get("openapi")
    validate(doc, cls=OpenAPIV31SpecValidator)


# --- Contenido -------------------------------------------------------------------------------

@pytest.mark.parametrize("fuente", FUENTES)
def test_rutas_del_contrato(dir_fuentes, fuente):
    paths = set(cargar_yaml(dir_fuentes, fuente).get("paths") or {})
    assert RUTAS_CONTRATO[fuente] <= paths, f"faltan {RUTAS_CONTRATO[fuente] - paths}"


@pytest.mark.parametrize("fuente", FUENTES)
def test_sin_ruta_de_control(dir_fuentes, fuente):
    """§6 'Ruta de control': /control/* no figura en los yaml."""
    paths = cargar_yaml(dir_fuentes, fuente).get("paths") or {}
    assert not [p for p in paths if p.startswith("/control")]
    assert "/control/" not in _texto(dir_fuentes, fuente)


@pytest.mark.parametrize("fuente", FUENTES)
def test_documenta_los_campos(dir_fuentes, fuente):
    faltan = CAMPOS[fuente] - _propiedades(cargar_yaml(dir_fuentes, fuente))
    assert not faltan, f"campos no documentados: {sorted(faltan)}"


@pytest.mark.parametrize("fuente", FUENTES)
def test_documenta_los_codigos_de_error(dir_fuentes, fuente):
    texto = _texto(dir_fuentes, fuente)
    faltan = {c for c in CODIGOS[fuente] if c not in texto}
    assert not faltan, f"códigos no documentados: {sorted(faltan)}"


@pytest.mark.parametrize("fuente", FUENTES)
def test_un_ejemplo_por_respuesta(dir_fuentes, fuente):
    """§6 'Contenido': un ejemplo por respuesta (en el tipo JSON de cada respuesta)."""
    doc = cargar_yaml(dir_fuentes, fuente)
    sin = []
    for ruta, ops in (doc.get("paths") or {}).items():
        for metodo, op in (ops or {}).items():
            if not isinstance(op, dict) or "responses" not in op:
                continue
            for estado, resp in op["responses"].items():
                if "$ref" in resp:
                    nombre = resp["$ref"].rsplit("/", 1)[1]
                    resp = doc["components"]["responses"][nombre]
                for tipo, media in (resp.get("content") or {}).items():
                    if not tipo.endswith("json"):
                        continue
                    media = media or {}
                    esquema = media.get("schema") or {}
                    if not ({"example", "examples"} & set(media)
                            or {"example", "examples"} & set(esquema)):
                        sin.append(f"{metodo.upper()} {ruta} {estado} {tipo}")
    assert not sin, f"respuestas sin ejemplo: {sin}"


@pytest.mark.parametrize("fuente", FUENTES)
def test_documenta_tiempo_de_respuesta(dir_fuentes, fuente):
    texto = _texto(dir_fuentes, fuente)
    assert "x-tiempo-respuesta-ms" in texto or re.search(r"tiempo de respuesta", texto, re.I)


@pytest.mark.parametrize("fuente", FUENTES)
def test_sin_palabra_prohibida(dir_fuentes, fuente):
    """§6 + AGENTS.md regla 1."""
    assert PALABRA_PROHIBIDA not in _texto(dir_fuentes, fuente).lower()


# --- Coinciden con lo desplegado (red de Docker o --integracion) -----------------------------------

@pytest.mark.parametrize("fuente,ruta", [(f, r) for f in FUENTES for r in MUESTRAS[f]])
def test_respuesta_normal_valida_contra_yaml(dir_fuentes, modos_limpios, fuente, ruta):
    """§6 'Coinciden con lo desplegado': 200 y 404 en modo normal validan contra el yaml."""
    doc = cargar_yaml(dir_fuentes, fuente)
    r = modos_limpios.get(ruta)
    assert r.estado in (200, 404), f"{ruta}: {r.estado}"
    assert errores_contra_yaml(doc, ruta, "GET", r) == []


def test_foto_cargada_valida_contra_yaml(dir_fuentes, modos_limpios):
    """§6 + §2 'Foto cargada': el tipo de contenido de la foto está documentado."""
    doc = cargar_yaml(dir_fuentes, "requisitorias-personas")
    for n in range(1, 100):
        r = modos_limpios.get(f"/personas/SIM-P-{n:04d}")
        if r.estado == 200 and r.json().get("foto_ids"):
            ruta = f"/personas/SIM-P-{n:04d}/fotos/{r.json()['foto_ids'][0]}"
            assert errores_contra_yaml(doc, ruta, "GET", modos_limpios.get(ruta)) == []
            return
    pytest.skip("Ninguna persona tiene fotos cargadas (carga de fotos: pendiente de contrato v2)")


@pytest.mark.parametrize("fuente", FUENTES)
def test_malformada_no_valida_contra_yaml(dir_fuentes, modos_limpios, fuente):
    """§5 `malformada`: 200 con un cuerpo que NO valida contra el contrato de su fuente."""
    doc = cargar_yaml(dir_fuentes, fuente)
    ruta = MUESTRAS[fuente][0]
    modos_limpios.poner_modo(fuente, "malformada")
    r = modos_limpios.get(ruta)
    assert r.estado == 200
    assert errores_contra_yaml(doc, ruta, "GET", r) != [], f"{ruta} malformada valida: {r.texto}"
