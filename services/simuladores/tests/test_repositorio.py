"""CONTRATO-HU-08 v1 §4 'Sin fotos en el repositorio' (AGENTS.md regla 8, decisión 6).

Solo anfitrión: recorre los archivos versionados (`git ls-files`) y busca imágenes por extensión
y por firma de bytes.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest

EXTENSIONES = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic", ".heif", ".tif",
               ".tiff", ".avif", ".jfif"}
FIRMAS = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a", b"BM")


def _versionados(raiz) -> list[str]:
    if shutil.which("git") is None:
        pytest.skip("git no está disponible")
    r = subprocess.run(["git", "ls-files", "-z"], cwd=raiz, capture_output=True)
    assert r.returncode == 0
    return [p for p in r.stdout.decode("utf-8").split("\0") if p]


def test_ninguna_imagen_versionada_por_extension(raiz_repo):
    imagenes = [p for p in _versionados(raiz_repo)
                if any(p.lower().endswith(e) for e in EXTENSIONES)]
    assert not imagenes, imagenes


def test_ninguna_imagen_versionada_por_firma(raiz_repo):
    sospechosos = []
    for p in _versionados(raiz_repo):
        f = raiz_repo / p
        if not f.is_file():
            continue
        with open(f, "rb") as fh:
            inicio = fh.read(16)
        if inicio.startswith(FIRMAS[:4]) or (inicio.startswith(b"BM") and f.suffix == ""):
            sospechosos.append(p)
        elif inicio[4:12] in (b"ftypheic", b"ftypavif", b"ftypmif1") or (
                inicio.startswith(b"RIFF") and inicio[8:12] == b"WEBP"):
            sospechosos.append(p)
    assert not sospechosos, sospechosos
