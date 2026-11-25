"""El modelo de ML Kit va dentro del APK — CONTRATO-MIGRACION-FLUTTER v1.2 §7 (M-3 del encargo).

    python -I pruebas/datos/revisar_modelo_apk.py <app-release.apk>

Lista el contenido del APK (es un zip; equivale a `unzip -l`) y comprueba que vienen dentro:
- archivos del modelo en `assets/mlkit-google-ocr-models/`;
- `lib/<abi>/libmlkit_google_ocr_pipeline.so` en al menos un ABI.

Por la v1.2 (opción A del humano) **no** se marca en rojo la presencia de
`play-services-mlkit-*`: llega como dependencia transitiva del POM de Google y lo que haga en la
red queda NO VERIFICADO. El script solo lo informa si ve rastros en el APK.

Sale con código 1 si falta el modelo. No escribe nada ni descomprime el APK.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

MODELOS = "assets/mlkit-google-ocr-models/"
PIPELINE = "libmlkit_google_ocr_pipeline.so"


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    apk = Path(sys.argv[1])
    if not apk.is_file():
        print(f"No existe el APK: {apk}")
        return 2
    with zipfile.ZipFile(apk) as z:
        nombres = z.namelist()
        tamanos = {i.filename: i.file_size for i in z.infolist()}
    modelos = [n for n in nombres if n.startswith(MODELOS) and not n.endswith("/")]
    pipelines = [n for n in nombres if n.startswith("lib/") and n.endswith("/" + PIPELINE)]
    rastros_gms = [n for n in nombres if "play-services-mlkit" in n or "play_services_mlkit" in n]

    print(f"APK: {apk.name} ({apk.stat().st_size} bytes, {len(nombres)} entradas)")
    print(f"Modelo en {MODELOS}: {len(modelos)} archivos")
    for n in modelos:
        print(f"  {n} ({tamanos[n]} bytes)")
    print(f"{PIPELINE}: {len(pipelines)}")
    for n in pipelines:
        print(f"  {n} ({tamanos[n]} bytes)")
    print(f"Rastros de play-services-mlkit en el APK (solo informativo, v1.2): {len(rastros_gms)}")
    for n in rastros_gms[:20]:
        print(f"  {n}")

    if modelos and pipelines:
        print("El modelo de ML Kit está dentro del APK.")
        return 0
    print("FALTA el modelo de ML Kit dentro del APK (hueco del contrato: el DEV lo reporta, no fuerza nada).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
