"""Formas que exige CONTRATO-HU-08 v1, escritas desde el contrato (no desde el código).

Cada función devuelve la lista de problemas encontrados; lista vacía = cumple la forma.
También: validación de respuestas contra los yaml de `contratos/fuentes/` (solo anfitrión).
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from urllib.parse import quote

# --- Nombres que no se negocian -------------------------------------------------------------

CAMPOS_PLACA = ("placa", "marca", "modelo", "color", "tipo", "requisitoria_vigente",
                "requisitoria", "es_sintetico")
CAMPOS_REQUISITORIA = ("codigo", "motivo", "autoridad", "fecha_emision")
CAMPOS_PERSONA = ("persona_id", "nombres", "apellidos", "documento", "requisitoria",
                  "foto_ids", "es_sintetico")
CAMPOS_GALERIA = ("version", "personas", "es_sintetico")

PLACA_CON = "ZZA-101"
PLACA_SIN = "ZZB-201"
PLACA_NO_EXISTE = "ZZZ-999"
PERSONA_EXISTE = "SIM-P-0001"
PERSONA_NO_EXISTE = "SIM-P-9999"

RE_PLACA = re.compile(r"^[A-Z0-9]{3}-[0-9]{3}$")
RE_DOCUMENTO = re.compile(r"^SIM-[0-9]{8}$")
RE_FECHA = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

ERRORES = {
    "PLACA_NO_REGISTRADA": "La placa no está registrada en la fuente",
    "PERSONA_NO_REGISTRADA": "La persona no está registrada en la fuente",
    "FOTO_NO_DISPONIBLE": "La foto no está disponible",
    "ERROR_SIMULADO": "Falla simulada de la fuente",
    "FUENTE_DESCONOCIDA": None,   # el contrato no fija el texto ("…")
    "SOLICITUD_INVALIDA": None,   # el contrato no fija el texto ("…")
}

PALABRA_PROHIBIDA = "identificado"  # AGENTS.md regla 1


def _texto_no_vacio(d: dict, campo: str, problemas: list[str]) -> None:
    v = d.get(campo)
    if not isinstance(v, str) or not v.strip():
        problemas.append(f"{campo} debe ser texto no vacío, vino {v!r}")


def problemas_requisitoria(r: object, donde: str = "requisitoria") -> list[str]:
    if not isinstance(r, dict):
        return [f"{donde} debe ser un objeto, vino {r!r}"]
    p: list[str] = []
    for c in CAMPOS_REQUISITORIA:
        if c not in r:
            p.append(f"{donde}.{c} falta")
        else:
            _texto_no_vacio(r, c, p)
    f = r.get("fecha_emision")
    if isinstance(f, str):
        if not RE_FECHA.match(f):
            p.append(f"{donde}.fecha_emision no es AAAA-MM-DD: {f!r}")
        else:
            try:
                date.fromisoformat(f)
            except ValueError:
                p.append(f"{donde}.fecha_emision no es una fecha válida: {f!r}")
    return p


def problemas_placa(d: object, placa_pedida: str | None = None) -> list[str]:
    if not isinstance(d, dict):
        return [f"el cuerpo debe ser un objeto, vino {type(d).__name__}"]
    p = [f"falta {c}" for c in CAMPOS_PLACA if c not in d]
    for c in ("placa", "marca", "modelo", "color", "tipo"):
        if c in d:
            _texto_no_vacio(d, c, p)
    if placa_pedida is not None and d.get("placa") != placa_pedida:
        p.append(f"placa {d.get('placa')!r} no es la pedida {placa_pedida!r}")
    vig = d.get("requisitoria_vigente")
    if "requisitoria_vigente" in d and not isinstance(vig, bool):
        p.append(f"requisitoria_vigente debe ser booleano, vino {vig!r}")
    if vig is True:
        p += problemas_requisitoria(d.get("requisitoria"))
    elif vig is False and d.get("requisitoria") is not None:
        p.append("con requisitoria_vigente false, requisitoria debe ser null")
    if d.get("es_sintetico") is not True:
        p.append(f"es_sintetico debe ser true, vino {d.get('es_sintetico')!r}")
    return p


def problemas_persona(d: object, persona_pedida: str | None = None) -> list[str]:
    if not isinstance(d, dict):
        return [f"el cuerpo debe ser un objeto, vino {type(d).__name__}"]
    p = [f"falta {c}" for c in CAMPOS_PERSONA if c not in d]
    for c in ("persona_id", "nombres", "apellidos", "documento"):
        if c in d:
            _texto_no_vacio(d, c, p)
    if persona_pedida is not None and d.get("persona_id") != persona_pedida:
        p.append(f"persona_id {d.get('persona_id')!r} no es la pedida {persona_pedida!r}")
    doc = d.get("documento")
    if isinstance(doc, str) and not RE_DOCUMENTO.match(doc):
        p.append(f"documento no es SIM- + 8 dígitos: {doc!r}")
    # Toda persona de esta fuente tiene requisitoria (contrato §2, ADR-0004).
    if "requisitoria" in d:
        p += problemas_requisitoria(d.get("requisitoria"))
    f = d.get("foto_ids")
    if "foto_ids" in d and (not isinstance(f, list) or not all(isinstance(x, str) and x for x in f)):
        p.append(f"foto_ids debe ser una lista de textos, vino {f!r}")
    if d.get("es_sintetico") is not True:
        p.append(f"es_sintetico debe ser true, vino {d.get('es_sintetico')!r}")
    return p


def problemas_galeria(d: object) -> list[str]:
    if not isinstance(d, dict):
        return [f"el cuerpo debe ser un objeto, vino {type(d).__name__}"]
    p = [f"falta {c}" for c in CAMPOS_GALERIA if c not in d]
    if "version" in d:
        _texto_no_vacio(d, "version", p)
    personas = d.get("personas")
    if "personas" in d and not isinstance(personas, list):
        p.append(f"personas debe ser una lista, vino {personas!r}")
    for i, e in enumerate(personas if isinstance(personas, list) else []):
        if not isinstance(e, dict):
            p.append(f"personas[{i}] debe ser un objeto")
            continue
        for c in ("persona_id", "foto_ids"):
            if c not in e:
                p.append(f"personas[{i}].{c} falta")
        if "persona_id" in e:
            _texto_no_vacio(e, "persona_id", p)
        f = e.get("foto_ids")
        if "foto_ids" in e and (not isinstance(f, list)
                                or not all(isinstance(x, str) and x for x in f)):
            p.append(f"personas[{i}].foto_ids debe ser una lista de textos, vino {f!r}")
    if d.get("es_sintetico") is not True:
        p.append(f"es_sintetico debe ser true, vino {d.get('es_sintetico')!r}")
    return p


def problemas_error(r, estado: int, codigo: str) -> list[str]:
    """Formato de error del simulador: {"codigo", "mensaje"} (contrato, decisión 2)."""
    p: list[str] = []
    if r.estado != estado:
        p.append(f"estado {r.estado}, se esperaba {estado}")
    if "application/json" not in (r.cabecera("Content-Type") or ""):
        p.append(f"Content-Type {r.cabecera('Content-Type')!r} no es JSON")
        return p
    try:
        d = r.json()
    except ValueError:
        return p + [f"el cuerpo no es JSON: {r.texto[:200]!r}"]
    if not isinstance(d, dict):
        return p + [f"el cuerpo debe ser un objeto, vino {d!r}"]
    if d.get("codigo") != codigo:
        p.append(f"codigo {d.get('codigo')!r}, se esperaba {codigo!r}")
    esperado = ERRORES.get(codigo)
    if not isinstance(d.get("mensaje"), str) or not d["mensaje"].strip():
        p.append(f"mensaje debe ser texto no vacío, vino {d.get('mensaje')!r}")
    elif esperado is not None and d["mensaje"] != esperado:
        p.append(f"mensaje {d['mensaje']!r}, se esperaba {esperado!r}")
    if PALABRA_PROHIBIDA in r.texto.lower():
        p.append("el cuerpo contiene la palabra prohibida")
    return p


# --- Imagen generada en tiempo de ejecución (contrato, decisión 6) ----------------------------

FIRMAS_IMAGEN = {
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
}


# --- Contratos yaml (solo anfitrión) ---------------------------------------------------------

YAMLS = {
    "placas": "placas.yaml",
    "requisitorias-personas": "requisitorias-personas.yaml",
    "galeria": "galeria.yaml",
}


def buscar_dir_contratos(raiz_repo: Path | None) -> Path | None:
    """Carpeta con los yaml de las fuentes: variable CONTRATOS_FUENTES_DIR (v3 C6, dentro del
    contenedor) o contratos/fuentes del repositorio (anfitrión)."""
    import os  # noqa: PLC0415
    candidatos = [os.environ.get("CONTRATOS_FUENTES_DIR")]
    if raiz_repo is not None:
        candidatos.append(str(raiz_repo / "contratos" / "fuentes"))
    for c in candidatos:
        if c and Path(c).is_dir():
            return Path(c)
    return None


def cargar_yaml(dir_fuentes: Path, fuente: str) -> dict:
    import yaml  # noqa: PLC0415
    with open(dir_fuentes / YAMLS[fuente], encoding="utf-8") as f:
        return yaml.safe_load(f)


def plantilla_de(doc: dict, ruta: str) -> str | None:
    """Plantilla de `paths` del yaml que corresponde a una ruta concreta (sin query)."""
    partes = ruta.strip("/").split("/")
    for plantilla in (doc.get("paths") or {}):
        pp = plantilla.strip("/").split("/")
        if len(pp) == len(partes) and all(
            a == b or (a.startswith("{") and a.endswith("}")) for a, b in zip(pp, partes)
        ):
            return plantilla
    return None


def _ptr(tokens: list[str]) -> str:
    return "#/" + "/".join(quote(t.replace("~", "~0").replace("/", "~1"), safe="~") for t in tokens)


def _resolver(doc: dict, obj: object, tokens: list[str]) -> tuple[object, list[str]]:
    """Sigue `$ref` locales a nivel de objeto (respuestas por componente)."""
    vistos = 0
    while isinstance(obj, dict) and "$ref" in obj and vistos < 10:
        ref = obj["$ref"]
        assert ref.startswith("#/"), f"$ref no local no soportado: {ref}"
        tokens = [t.replace("~1", "/").replace("~0", "~") for t in ref[2:].split("/")]
        obj = doc
        for t in tokens:
            obj = obj[t]
        vistos += 1
    return obj, tokens


def respuesta_documentada(doc: dict, ruta: str, metodo: str, estado: int):
    """(objeto de respuesta del yaml, tokens de su ubicación) o (None, motivo)."""
    plantilla = plantilla_de(doc, ruta)
    if plantilla is None:
        return None, f"{ruta} no tiene plantilla en paths"
    op = (doc["paths"][plantilla] or {}).get(metodo.lower())
    if op is None:
        return None, f"{metodo} {plantilla} no está documentado"
    respuestas = op.get("responses") or {}
    for clave in (str(estado), f"{str(estado)[0]}XX", "default"):
        if clave in respuestas:
            toks = ["paths", plantilla, metodo.lower(), "responses", clave]
            return _resolver(doc, respuestas[clave], toks)
    return None, f"{metodo} {plantilla} no documenta la respuesta {estado}"


def errores_contra_yaml(doc: dict, ruta: str, metodo: str, r) -> list[str]:
    """Valida estado, tipo de contenido y cuerpo JSON de una respuesta contra el yaml."""
    from jsonschema import Draft202012Validator  # noqa: PLC0415
    from referencing import Registry, Resource  # noqa: PLC0415
    from referencing.jsonschema import DRAFT202012  # noqa: PLC0415

    resp, toks = respuesta_documentada(doc, ruta, metodo, r.estado)
    if resp is None:
        return [toks]
    contenido = resp.get("content") or {}
    tipo = (r.cabecera("Content-Type") or "").split(";")[0].strip()
    if tipo not in contenido:
        return [f"Content-Type {tipo!r} no documentado para {r.estado} (hay {list(contenido)})"]
    media = contenido[tipo] or {}
    if "schema" not in media or not tipo.endswith("json"):
        return []
    uri = "urn:contrato-fuente"
    registro = Registry().with_resource(
        uri, Resource.from_contents(doc, default_specification=DRAFT202012)
    )
    esquema = {"$ref": uri + _ptr(toks + ["content", tipo, "schema"])}
    validador = Draft202012Validator(esquema, registry=registro)
    try:
        cuerpo = r.json()
    except ValueError:
        return ["el cuerpo no es JSON"]
    return [f"{'/'.join(map(str, e.absolute_path)) or '(raíz)'}: {e.message}"
            for e in validador.iter_errors(cuerpo)]
