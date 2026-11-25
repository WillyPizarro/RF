"""Ninguna CA de desarrollo dentro de un APK — CONTRATO-MIGRACION-FLUTTER v1.5 §6.

    python -I pruebas/datos/revisar_ca_apk.py <ca.crt> <app.apk> [<otro.apk> ...]

`ca.crt` es la copia de la CA de Caddy que está **fuera del repositorio**
(`C:\\Willy\\Trabajo\\MININTER\\ca-local\\caddy-root.crt`). Este script no escribe nada ni
imprime el certificado: solo dice, por APK, si lo encontró y dónde.

Qué busca en cada APK (un zip): en cada entrada, ya descomprimida, y en el archivo crudo,
- el certificado en DER (los bytes del certificado);
- el cuerpo en base64 del PEM (sin saltos de línea) y una línea suelta del PEM;
- además, lista las entradas con extensión de certificado (`.crt`, `.pem`, `.der`, `.cer`,
  `.p12`, `.pfx`, `.bks`), que no deberían existir.

Sale con código 1 si algún APK lleva la CA o un archivo de certificado; 0 si ninguno; 2 si
faltan argumentos o archivos.
"""

from __future__ import annotations

import base64
import re
import sys
import zipfile
from pathlib import Path

EXT_CERT = (".crt", ".pem", ".der", ".cer", ".p12", ".pfx", ".bks")


def marcas_de(ca: bytes) -> dict[str, bytes]:
    m = re.search(rb"-----BEGIN CERTIFICATE-----(.+?)-----END CERTIFICATE-----", ca, re.S)
    if m:
        cuerpo = b"".join(m.group(1).split())
        der = base64.b64decode(cuerpo)
        lineas = [l.strip() for l in m.group(1).splitlines() if len(l.strip()) >= 40]
    else:
        der = ca
        cuerpo = base64.b64encode(der)
        lineas = []
    marcas = {"DER": der, "base64": cuerpo}
    if lineas:
        marcas["línea PEM"] = lineas[len(lineas) // 2]
    return marcas


def revisar(apk: Path, marcas: dict[str, bytes]) -> list[str]:
    hallazgos = []
    crudo = apk.read_bytes()
    for nombre, marca in marcas.items():
        if marca in crudo:
            hallazgos.append(f"(archivo crudo): {nombre}")
    with zipfile.ZipFile(apk) as z:
        for info in z.infolist():
            if info.filename.lower().endswith(EXT_CERT):
                hallazgos.append(f"{info.filename}: archivo de certificado")
            datos = z.read(info)
            for nombre, marca in marcas.items():
                if marca in datos:
                    hallazgos.append(f"{info.filename}: {nombre}")
    return hallazgos


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    ca, apks = Path(sys.argv[1]), [Path(a) for a in sys.argv[2:]]
    for f in [ca, *apks]:
        if not f.is_file():
            print(f"No existe: {f}")
            return 2
    marcas = marcas_de(ca.read_bytes())
    codigo = 0
    for apk in apks:
        h = revisar(apk, marcas)
        if h:
            codigo = 1
            print(f"{apk.name}: ENCONTRADO")
            for x in h:
                print(f"  {x}")
        else:
            print(f"{apk.name}: sin la CA ni archivos de certificado.")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
