"""CONTRATO-HU-08 v2 §4 bis — Carga de las fotos (C1), y §2/§3 con fotos cargadas.

Solo anfitrión, con el sistema arrancado CON el montaje de fotos:
    docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml \
        --env-file infra/.env up -d --build
    pytest services/simuladores/tests --integracion

La prueba escribe en `SIM_FOTOS_ORIGEN` (carpeta del anfitrión, fuera del repositorio) una imagen
PNG generada en tiempo de ejecución: unos píxeles de colores, NO es un rostro (decisión 6). Nunca
se versiona y se borra al terminar. JPEG no se prueba: generarlo exige una biblioteca de imágenes.
"""

from __future__ import annotations

import json
import random
import struct
import uuid
import zlib
from pathlib import Path

import pytest

from conftest import RAIZ_REPO, compose, leer_env_infra
from ayudas_contrato import (
    PERSONA_EXISTE, PERSONA_NO_EXISTE, buscar_dir_contratos, cargar_yaml, errores_contra_yaml,
    problemas_error,
)

FUENTE_FOTOS_DENTRO = "/fotos-origen"  # v2 C1


def png_sintetico(semilla: int, marca: str) -> bytes:
    """PNG 8x8 RGB válido con píxeles de colores y un trozo tEXt con una marca única."""
    azar = random.Random(semilla)
    filas = b"".join(b"\x00" + bytes(azar.randrange(256) for _ in range(8 * 3)) for _ in range(8))

    def trozo(tipo: bytes, datos: bytes) -> bytes:
        return (struct.pack(">I", len(datos)) + tipo + datos
                + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + trozo(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 2, 0, 0, 0))
            + trozo(b"tEXt", b"Comment\x00" + marca.encode("ascii"))
            + trozo(b"IDAT", zlib.compress(filas))
            + trozo(b"IEND", b""))


@pytest.fixture(scope="module")
def origen(solo_anfitrion) -> Path:
    ruta = leer_env_infra().get("SIM_FOTOS_ORIGEN", "")
    if not ruta:
        pytest.skip("SIM_FOTOS_ORIGEN no está definida (infra/.env o entorno): NO VERIFICADO")
    p = Path(ruta)
    if not p.is_dir():
        pytest.skip(f"SIM_FOTOS_ORIGEN={ruta} no es una carpeta del anfitrión: NO VERIFICADO")
    assert RAIZ_REPO is not None
    assert RAIZ_REPO.resolve() not in [p.resolve(), *p.resolve().parents], (
        "SIM_FOTOS_ORIGEN está dentro del repositorio (decisión 6 / AGENTS.md regla 8)"
    )
    # El simulador en marcha tiene que tener el origen montado (si se recreó sin
    # docker-compose.fotos.yml, las fotos nunca llegan y todo daría 404 sin explicar por qué).
    r = compose("exec", "-T", "simuladores", "python", "-c",
                f"import os,sys; sys.exit(0 if os.path.isdir({FUENTE_FOTOS_DENTRO!r}) else 3)")
    assert r.returncode == 0, (
        f"El contenedor simuladores no tiene {FUENTE_FOTOS_DENTRO} montado: arrancarlo con "
        "-f infra/docker-compose.yml -f infra/docker-compose.fotos.yml (entorno, no código)"
    )
    return p


@pytest.fixture
def fotos(origen, modos_limpios):
    """Escribe archivos en el origen y los borra al terminar."""
    creados: list[Path] = []

    def escribir(nombre: str, datos: bytes) -> Path:
        f = origen / nombre
        assert not f.exists() or f in creados, f"{f} ya existía: no la piso"
        f.write_bytes(datos)
        if f not in creados:
            creados.append(f)
        return f

    yield escribir
    for f in creados:
        f.unlink(missing_ok=True)


def _n_libre(origen: Path) -> int:
    usados = {f.stem for f in origen.iterdir()}
    for n in range(900, 1000):
        if f"{PERSONA_EXISTE}__{n}" not in usados:
            return n
    pytest.skip("no hay número libre para la foto de prueba")


def _estado(cliente):
    p = cliente.get(f"/personas/{PERSONA_EXISTE}")
    g = cliente.get("/galeria")
    assert p.estado == 200 and g.estado == 200
    return p.json(), g.json()


def _fotos_en_galeria(g, persona_id):
    return next((e["foto_ids"] for e in g["personas"] if e["persona_id"] == persona_id), [])


def test_origen_montado_en_fotos_origen(solo_anfitrion, origen):
    """§4 bis 'Origen': con docker-compose.fotos.yml, SIM_FOTOS_DIR=/fotos-origen y el origen del
    anfitrión montado ahí."""
    r = compose("-f", str(RAIZ_REPO / "infra" / "docker-compose.fotos.yml"),
                "config", "--format", "json")
    assert r.returncode == 0, r.stderr[-2000:]
    sim = json.loads(r.stdout)["services"]["simuladores"]
    assert sim["environment"].get("SIM_FOTOS_DIR") == FUENTE_FOTOS_DENTRO
    destinos = {v.get("target"): v for v in sim.get("volumes", [])}
    assert FUENTE_FOTOS_DENTRO in destinos, destinos
    assert Path(destinos[FUENTE_FOTOS_DENTRO]["source"]).resolve() == origen.resolve()


def test_agregar_cambiar_y_quitar_una_foto(origen, fotos, modos_limpios):
    """§4 bis 'Nombre', 'foto_id', 'Cuándo se carga' y 'Versión'; §2 'Foto cargada' (bytes
    descifrados); §3 'Solo personas con foto' y 'Versión estable'."""
    c = modos_limpios
    n = _n_libre(origen)
    foto_id = f"{PERSONA_EXISTE}__{n}"
    _, g0 = _estado(c)
    v0 = g0["version"]

    # Agregar: aparece en la siguiente respuesta de las tres rutas, sin reiniciar.
    datos1 = png_sintetico(1, "prueba-" + uuid.uuid4().hex)
    fotos(f"{foto_id}.png", datos1)
    p1, g1 = _estado(c)
    assert foto_id in p1["foto_ids"]
    assert foto_id in _fotos_en_galeria(g1, PERSONA_EXISTE)
    assert g1["version"] != v0, "agregar una foto no cambió version"
    r = c.get(f"/personas/{PERSONA_EXISTE}/fotos/{foto_id}")
    assert r.estado == 200, r.texto[:200]
    assert (r.cabecera("Content-Type") or "").split(";")[0].strip() == "image/png"
    assert r.cuerpo == datos1, "los bytes servidos no son los de la foto cargada"
    assert _estado(c)[1]["version"] == g1["version"], "version cambia sin cambiar fotos"

    # Cambiar: se sirve el contenido nuevo y version cambia.
    datos2 = png_sintetico(2, "prueba-" + uuid.uuid4().hex)
    fotos(f"{foto_id}.png", datos2)
    _, g2 = _estado(c)
    assert g2["version"] != g1["version"], "cambiar una foto no cambió version"
    assert c.get(f"/personas/{PERSONA_EXISTE}/fotos/{foto_id}").cuerpo == datos2

    # Quitar: desaparece de las tres rutas y version cambia.
    (origen / f"{foto_id}.png").unlink()
    p3, g3 = _estado(c)
    assert foto_id not in p3["foto_ids"]
    assert foto_id not in _fotos_en_galeria(g3, PERSONA_EXISTE)
    assert g3["version"] != g2["version"], "quitar una foto no cambió version"
    r = c.get(f"/personas/{PERSONA_EXISTE}/fotos/{foto_id}")
    assert problemas_error(r, 404, "FOTO_NO_DISPONIBLE") == []


@pytest.mark.parametrize("nombre", [
    "basura.png",
    f"{PERSONA_NO_EXISTE}__1.png",          # persona que no existe en la semilla
    f"{PERSONA_EXISTE}_1.png",              # un solo guion bajo
    f"{PERSONA_EXISTE}__x.png",             # n no numérico
    f"{PERSONA_EXISTE}__1.gif",             # extensión no admitida
    f"{PERSONA_EXISTE.lower()}__1.png",     # persona_id en minúsculas
])
def test_nombres_que_no_cumplen_se_ignoran(origen, fotos, modos_limpios, nombre):
    """§4 bis 'Nombre de archivo': se ignoran los nombres que no cumplen el patrón y las personas
    que no existen en la semilla."""
    if (origen / nombre).exists():
        pytest.skip(f"{nombre} ya existe en el origen: no la piso")
    p0, g0 = _estado(modos_limpios)
    fotos(nombre, png_sintetico(3, "prueba-" + uuid.uuid4().hex))
    p1, g1 = _estado(modos_limpios)
    assert p1["foto_ids"] == p0["foto_ids"]
    assert g1 == g0, "la galería cambió por un archivo que debía ignorarse"
    r = modos_limpios.get(f"/personas/{PERSONA_NO_EXISTE}")
    assert problemas_error(r, 404, "PERSONA_NO_REGISTRADA") == []


_BUSCAR_MARCA = r'''
import os, sys
marca = sys.argv[1].encode("ascii")
fuera = ("/proc", "/sys", "/dev", "/fotos-origen", "/app/tests")
hallados = []
for raiz, dirs, archivos in os.walk("/", followlinks=False):
    if raiz.startswith(fuera):
        dirs[:] = []
        continue
    for a in archivos:
        p = os.path.join(raiz, a)
        try:
            if os.path.islink(p) or not os.path.isfile(p) or os.path.getsize(p) > 50_000_000:
                continue
            with open(p, "rb") as f:
                if marca in f.read():
                    hallados.append(p)
        except OSError:
            pass
print("\n".join(hallados))
'''


def test_foto_guardada_cifrada(origen, fotos, modos_limpios):
    """§4 bis 'Cifrado': fuera del origen de solo lectura, ningún archivo del contenedor
    simuladores contiene la foto en claro (se busca una marca única metida en el PNG)."""
    n = _n_libre(origen)
    foto_id = f"{PERSONA_EXISTE}__{n}"
    marca = "marca-en-claro-" + uuid.uuid4().hex
    datos = png_sintetico(4, marca)
    fotos(f"{foto_id}.png", datos)
    r = modos_limpios.get(f"/personas/{PERSONA_EXISTE}/fotos/{foto_id}")
    assert r.estado == 200 and r.cuerpo == datos  # ya cargada y guardada

    b = compose("exec", "-T", "simuladores", "python", "-c", _BUSCAR_MARCA, marca, timeout=600)
    assert b.returncode == 0, b.stderr[-2000:]
    hallados = [ln for ln in b.stdout.splitlines() if ln.strip()]
    assert not hallados, f"la foto está en claro en: {hallados}"


def test_foto_cargada_valida_contra_yaml(origen, fotos, modos_limpios):
    """§6 'Coinciden con lo desplegado' + §2 'Foto cargada' (veredicto A1, M-5): la respuesta 200
    de /personas/{id}/fotos/{foto_id}, con una foto que carga la propia prueba, valida contra
    requisitorias-personas.yaml (estado y tipo de contenido documentados)."""
    pytest.importorskip("yaml", reason="falta pyyaml (requirements-pruebas.txt)")
    pytest.importorskip("jsonschema", reason="falta jsonschema (requirements-pruebas.txt)")
    dir_fuentes = buscar_dir_contratos(RAIZ_REPO)
    assert dir_fuentes is not None, "no se encuentran los yaml de contratos/fuentes/"
    doc = cargar_yaml(dir_fuentes, "requisitorias-personas")

    foto_id = f"{PERSONA_EXISTE}__{_n_libre(origen)}"
    datos = png_sintetico(5, "prueba-" + uuid.uuid4().hex)
    fotos(f"{foto_id}.png", datos)
    ruta = f"/personas/{PERSONA_EXISTE}/fotos/{foto_id}"
    r = modos_limpios.get(ruta)
    assert r.estado == 200, r.texto[:200]
    assert r.cuerpo == datos
    assert errores_contra_yaml(doc, ruta, "GET", r) == []

    # La ficha de la persona, ya con la foto en foto_ids, también valida contra el yaml.
    rp = modos_limpios.get(f"/personas/{PERSONA_EXISTE}")
    assert foto_id in rp.json()["foto_ids"]
    assert errores_contra_yaml(doc, f"/personas/{PERSONA_EXISTE}", "GET", rp) == []
