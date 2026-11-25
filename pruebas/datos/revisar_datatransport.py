"""Revisión de la cola de telemetría de ML Kit (`com.google.android.datatransport`) — HU-04, M-11.

    python -I pruebas/datos/revisar_datatransport.py <carpeta con la copia>

La carpeta tiene la copia de `databases/com.google.android.datatransport.events` (y, si existen,
`-wal` y `-shm`), sacada del teléfono con el paso 9 del guion. Está **fuera del repositorio** y
se borra al terminar. Este script no escribe nada: solo lee la copia e imprime un resumen.

Qué busca (M-11):
1. **Imágenes:** firmas JPEG (`FF D8 FF`) o PNG (`89 50 4E 47`), crudas o en base64 (`/9j/`,
   `iVBORw0KGgo`), en las celdas de todas las tablas y en los bytes crudos de los archivos
   (incluye el WAL y las páginas libres).
2. **Texto de placa leído:** `ZZ` + 1 alfanumérico + guion, espacio o punto opcional + 3 dígitos
   (las placas impresas de la prueba), en mayúsculas o minúsculas.
3. **Qué datos hay:** las tablas, la cantidad de filas, los nombres de transporte y backend, y las
   cadenas legibles de cada carga, para compararlas con la divulgación de Google. Las cadenas se
   recortan; no se vuelcan cargas binarias completas.

Sale con código 1 si encuentra una imagen o un texto de placa (la decisión se reabre, M-11).

**Modo red (DESPLIEGUE-01 M-3, nivel 2 de la verificación de red de ML Kit):**

    python -I pruebas/datos/revisar_datatransport.py --cuerpos <carpeta con los cuerpos>

La carpeta tiene los cuerpos de las subidas que guardó mitmproxy con el complemento
`pruebas/datos/mitm_guardar_subidas.py` (un archivo `.bin` por solicitud), **fuera del
repositorio** (`C:\\Willy\\Trabajo\\MININTER\\flutter-capturas\\red\\`). Para cada cuerpo:
lo descomprime si viene en gzip o zlib (también los flujos gzip incrustados en el protobuf) y le
pasa la misma búsqueda de imágenes y de texto de placa `ZZ…`. Imprime **solo** el nombre del
archivo, el tamaño, si estaba comprimido y los hallazgos; nunca el contenido ni identificadores.
Sale con código 1 si encuentra una imagen o un texto de placa.
"""

from __future__ import annotations

import re
import sqlite3
import sys
import zlib
from pathlib import Path

NOMBRE = "com.google.android.datatransport.events"
FIRMAS = {"JPEG": b"\xff\xd8\xff", "PNG": b"\x89PNG\r\n\x1a\n",
          "JPEG en base64": b"/9j/", "PNG en base64": b"iVBORw0KGgo"}
PLACA = re.compile(rb"zz[a-z0-9][-. ]?[0-9]{3}", re.IGNORECASE)
LEGIBLE = re.compile(rb"[\x20-\x7e]{4,}")


def buscar(datos: bytes, donde: str, hallazgos: list[str]) -> None:
    for nombre, firma in FIRMAS.items():
        if firma in datos:
            hallazgos.append(f"{donde}: firma {nombre}")
    for m in PLACA.finditer(datos):
        hallazgos.append(f"{donde}: texto de placa {m.group().decode('ascii', 'replace')!r}")


GZIP = b"\x1f\x8b\x08"


def descomprimidos(datos: bytes) -> list[tuple[str, bytes]]:
    """Las versiones legibles de un cuerpo: el original, el cuerpo entero descomprimido (gzip o
    zlib) y cada flujo gzip incrustado que se pueda descomprimir."""
    salida = [("original", datos)]
    for nombre, wbits in (("gzip", 16 + zlib.MAX_WBITS), ("zlib", zlib.MAX_WBITS)):
        try:
            salida.append((nombre, zlib.decompress(datos, wbits)))
        except zlib.error:
            pass
    inicio = datos.find(GZIP, 1)
    while inicio != -1:
        try:
            d = zlib.decompressobj(16 + zlib.MAX_WBITS)
            salida.append((f"gzip incrustado en {inicio}", d.decompress(datos[inicio:])))
        except zlib.error:
            pass
        inicio = datos.find(GZIP, inicio + 1)
    return salida


def revisar_cuerpos(carpeta: Path) -> int:
    if not carpeta.is_dir():
        print(f"No existe la carpeta {carpeta}")
        return 2
    archivos = sorted(p for p in carpeta.iterdir() if p.is_file() and p.suffix == ".bin")
    if not archivos:
        print(f"No hay cuerpos (.bin) en {carpeta}")
        return 2
    hallazgos: list[str] = []
    for archivo in archivos:
        datos = archivo.read_bytes()
        versiones = descomprimidos(datos)
        formas = [n for n, _ in versiones if n != "original"]
        print(f"cuerpo {archivo.name}: {len(datos)} bytes; descomprimido: {formas or 'no'}")
        for nombre, contenido in versiones:
            buscar(contenido, f"{archivo.name} ({nombre})", hallazgos)
    print(f"\n== Resultado: {len(archivos)} cuerpos revisados")
    if hallazgos:
        print("HALLAZGOS (la decisión de la M-11 se reabre):")
        for h in sorted(set(hallazgos)):
            print("  - " + h)
        return 1
    print("Ninguna imagen (JPEG/PNG, crudas o en base64) y ningún texto de placa ZZ en las subidas.")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) == 3 and sys.argv[1] == "--cuerpos":
        return revisar_cuerpos(Path(sys.argv[2]))
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    carpeta = Path(sys.argv[1])
    base = next((p for p in carpeta.iterdir() if p.name in (NOMBRE, "events.db")), None)
    if base is None:
        print(f"No está la copia de {NOMBRE} en {carpeta}")
        return 2
    hallazgos: list[str] = []

    # 1. Bytes crudos de la base, el WAL y el SHM (incluye páginas libres y lo no volcado).
    for archivo in sorted(carpeta.iterdir()):
        datos = archivo.read_bytes()
        print(f"archivo {archivo.name}: {len(datos)} bytes")
        buscar(datos, f"crudo {archivo.name}", hallazgos)

    # 2. Tablas y celdas.
    con = sqlite3.connect(f"file:{base}?mode=ro", uri=True)
    try:
        tablas = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
        print(f"\ntablas: {tablas}")
        for t in tablas:
            filas = con.execute(f'select * from "{t}"').fetchall()
            cols = [d[0] for d in con.execute(f'select * from "{t}" limit 0').description]
            print(f"\n== {t}: {len(filas)} filas; columnas {cols}")
            for i, fila in enumerate(filas):
                for col, valor in zip(cols, fila):
                    if valor is None:
                        continue
                    datos = valor if isinstance(valor, bytes) else str(valor).encode("utf-8")
                    buscar(datos, f"{t}[{i}].{col}", hallazgos)
                # Resumen legible de la fila (recortado): nombres de transporte, backend, etc.
                partes = []
                for col, valor in zip(cols, fila):
                    if isinstance(valor, bytes):
                        cadenas = [c.decode("ascii") for c in LEGIBLE.findall(valor)][:8]
                        partes.append(f"{col}=<{len(valor)} bytes; legible: {cadenas}>")
                    elif valor is not None:
                        partes.append(f"{col}={str(valor)[:80]}")
                if i < 50:
                    print("   " + " | ".join(partes))
            if len(filas) > 50:
                print(f"   … {len(filas) - 50} filas más (no se muestran)")
    finally:
        con.close()

    print("\n== Resultado")
    if hallazgos:
        print("HALLAZGOS (la decisión de la M-11 se reabre):")
        for h in sorted(set(hallazgos)):
            print("  - " + h)
        return 1
    print("Ninguna imagen (JPEG/PNG, crudas o en base64) y ningún texto de placa ZZ en la cola.")
    print("Revisar arriba los datos legibles contra la divulgación de Google (ARCH).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
