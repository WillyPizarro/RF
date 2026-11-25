"""Revisión de la caché en disco de la app Flutter — CONTRATO-HU-04 v6 §6 ("Sin caché HTTP en disco").

    python -I pruebas/datos/revisar_cache_app.py <copia.tar> [--apk <movil-buscador-debug.apk>]

`copia.tar` es la copia de `cache/`, `files/` y `app_flutter/` del almacenamiento privado de la app
(`pe.prototipo.movilbuscador`), sacada del teléfono con el paso 8 del guion
(`pruebas/datos/GUION-MIGRACION-FLUTTER-dispositivo.md`). Está **fuera del repositorio** y se
borra al terminar. Este script no escribe nada: solo lee la copia e imprime un resumen.

Qué busca (HU-04 v6 §6): ningún archivo que contenga `/v1/` ni una respuesta de la API, por
ejemplo `"resultado"`, `token_acceso`, `token_renovacion`, `consulta_id` o `formato_placa`.
Además (regla 8 y HU-04 §6, "La foto se borra"): ninguna imagen JPEG o PNG.
Desde CONTRATO-MIGRACION-FLUTTER v1.5 §6 ("Sin caché HTTP con OkHttp"): ningún directorio ni
archivo con `http-cache`, `http_cache` u `okhttp` en la ruta, y ningún diario de `DiskLruCache`
(`libcore.io.DiskLruCache`, la primera línea del `journal` de la caché de OkHttp).

`app_flutter/flutter_assets/` (M-15 del encargo): en el APK de depuración, Flutter copia ahí los
recursos del APK (`kernel_blob.bin` trae el código Dart compilado, con los textos `/v1/`, etc.).
Con `--apk`, un archivo de `app_flutter/flutter_assets/<ruta>` **se excluye solo si su SHA-256
es igual al de `assets/flutter_assets/<ruta>` dentro de ese APK** (es una copia del APK, no algo
que la app escribió). Si no coincide, o no está en el APK, o no se pasa `--apk`, se revisa como
cualquier otro archivo y se marca si tiene algo.

Sale con código 1 si encuentra algo. Imprime solo la ruta del archivo y qué marca encontró, nunca
el contenido.
"""

from __future__ import annotations

import hashlib
import sys
import tarfile
import zipfile
from pathlib import Path

MARCAS = [b"/v1/", b'"resultado"', b"token_acceso", b"token_renovacion", b"consulta_id", b"formato_placa"]
DISKLRU = b"libcore.io.DiskLruCache"
RUTAS_OKHTTP = ("http-cache", "http_cache", "okhttp")
IMAGENES = {"JPEG": b"\xff\xd8\xff", "PNG": b"\x89PNG\r\n\x1a\n"}
PREFIJO_ASSETS = "app_flutter/flutter_assets/"


def hashes_apk(apk: Path) -> dict[str, str]:
    """SHA-256 de cada `assets/flutter_assets/<ruta>` del APK, por `<ruta>`."""
    res = {}
    with zipfile.ZipFile(apk) as z:
        for info in z.infolist():
            if info.filename.startswith("assets/flutter_assets/") and not info.is_dir():
                h = hashlib.sha256()
                with z.open(info) as f:
                    for bloque in iter(lambda: f.read(1 << 20), b""):
                        h.update(bloque)
                res[info.filename[len("assets/flutter_assets/"):]] = h.hexdigest()
    return res


def argumentos(args: list[str]) -> tuple[Path, Path | None] | None:
    if len(args) == 1:
        return Path(args[0]), None
    if len(args) == 3 and args[1] == "--apk":
        return Path(args[0]), Path(args[2])
    return None


def main() -> int:
    a = argumentos(sys.argv[1:])
    if a is None:
        print(__doc__)
        return 2
    copia, apk = a
    for f in [copia] + ([apk] if apk else []):
        if not f.is_file():
            print(f"No existe: {f}")
            return 2
    del_apk = hashes_apk(apk) if apk else {}
    hallazgos: list[str] = []
    archivos = excluidos = 0
    with tarfile.open(copia) as tar:
        for miembro in tar.getmembers():
            ruta = miembro.name.lower()
            for parte in RUTAS_OKHTTP:
                if parte in ruta:
                    hallazgos.append(f"{miembro.name}: ruta con {parte} (caché de OkHttp)")
            if not miembro.isfile():
                continue
            archivos += 1
            f = tar.extractfile(miembro)
            if f is None:
                continue
            datos = f.read()
            nombre = miembro.name.lstrip("./")
            if nombre.startswith(PREFIJO_ASSETS):
                relativo = nombre[len(PREFIJO_ASSETS):]
                propio = hashlib.sha256(datos).hexdigest()
                if del_apk.get(relativo) == propio:
                    excluidos += 1
                    print(f"  {miembro.name} ({miembro.size} bytes) — igual al del APK (sha256 {propio[:8]}…), excluido")
                    continue
                if apk:
                    motivo = "no está en el APK" if relativo not in del_apk else "SHA-256 distinto del APK"
                    print(f"  {miembro.name}: {motivo}; se revisa")
            for marca in MARCAS:
                if marca in datos:
                    hallazgos.append(f"{miembro.name}: contiene {marca.decode()}")
            if datos.startswith(DISKLRU):
                hallazgos.append(f"{miembro.name}: diario de DiskLruCache (caché de OkHttp)")
            for nombre_img, firma in IMAGENES.items():
                if datos.startswith(firma):
                    hallazgos.append(f"{miembro.name}: es una imagen {nombre_img}")
            print(f"  {miembro.name} ({miembro.size} bytes)")
    print(f"Archivos revisados: {archivos} (excluidos por ser iguales al APK: {excluidos})")
    if hallazgos:
        print("ENCONTRADO:")
        for h in hallazgos:
            print(f"  {h}")
        return 1
    print("Ningún archivo con /v1/, respuestas de la API, caché de OkHttp ni imágenes en cache/, files/ ni app_flutter/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
