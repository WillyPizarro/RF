"""Revisión de la caché en disco de la app Flutter — CONTRATO-HU-04 v6 §6 ("Sin caché HTTP en disco").

    python -I pruebas/datos/revisar_cache_app.py <copia.tar>

`copia.tar` es la copia de `cache/`, `files/` y `app_flutter/` del almacenamiento privado de la app
(`pe.prototipo.movilbuscador`), sacada del teléfono con el paso 8 del guion
(`pruebas/datos/GUION-MIGRACION-FLUTTER-dispositivo.md`). Está **fuera del repositorio** y se
borra al terminar. Este script no escribe nada: solo lee la copia e imprime un resumen.

Qué busca (HU-04 v6 §6): ningún archivo que contenga `/v1/` ni una respuesta de la API, por
ejemplo `"resultado"`, `token_acceso`, `token_renovacion`, `consulta_id` o `formato_placa`.
Además (regla 8 y HU-04 §6, "La foto se borra"): ninguna imagen JPEG o PNG.

Sale con código 1 si encuentra algo. Imprime solo la ruta del archivo y qué marca encontró, nunca
el contenido.
"""

from __future__ import annotations

import sys
import tarfile
from pathlib import Path

MARCAS = [b"/v1/", b'"resultado"', b"token_acceso", b"token_renovacion", b"consulta_id", b"formato_placa"]
IMAGENES = {"JPEG": b"\xff\xd8\xff", "PNG": b"\x89PNG\r\n\x1a\n"}


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    copia = Path(sys.argv[1])
    if not copia.is_file():
        print(f"No existe la copia: {copia}")
        return 2
    hallazgos: list[str] = []
    archivos = 0
    with tarfile.open(copia) as tar:
        for miembro in tar.getmembers():
            if not miembro.isfile():
                continue
            archivos += 1
            f = tar.extractfile(miembro)
            if f is None:
                continue
            datos = f.read()
            for marca in MARCAS:
                if marca in datos:
                    hallazgos.append(f"{miembro.name}: contiene {marca.decode()}")
            for nombre, firma in IMAGENES.items():
                if datos.startswith(firma):
                    hallazgos.append(f"{miembro.name}: es una imagen {nombre}")
            print(f"  {miembro.name} ({miembro.size} bytes)")
    print(f"Archivos revisados: {archivos}")
    if hallazgos:
        print("ENCONTRADO:")
        for h in hallazgos:
            print(f"  {h}")
        return 1
    print("Ningún archivo con /v1/, respuestas de la API ni imágenes en cache/, files/ ni app_flutter/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
