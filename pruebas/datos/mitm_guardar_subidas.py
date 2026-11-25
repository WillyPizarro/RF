"""Complemento de mitmproxy para el nivel 2 de la verificación de red de ML Kit (DESPLIEGUE-01 M-3).

    mitmdump -s pruebas/datos/mitm_guardar_subidas.py --set salida=C:/Willy/Trabajo/MININTER/flutter-capturas/red/cuerpos

Por cada solicitud con cuerpo hacia un servidor que **no** sea el de la app (`localhost` o la IP
del proxy local), guarda el cuerpo **ya decodificado por mitmproxy** (sin el `Content-Encoding`)
en `<salida>/NNN.bin` y agrega una línea a `<salida>/resumen.tsv` con: número, hora, método,
**dominio**, ruta **sin** la consulta, `Content-Type`, `Content-Encoding` y tamaño. No guarda
cabeceras (pueden llevar identificadores o tokens), ni las respuestas, ni la consulta de la URL.

La carpeta va **fuera del repositorio** y se borra al terminar la sesión (guion, paso (e)). Los
cuerpos se revisan con `python -I pruebas/datos/revisar_datatransport.py --cuerpos <salida>` y con
`protoc --decode_raw`; al informe van **solo** dominios, categorías y conteos.

Lo escribió el TESTER con la API de complementos de mitmproxy (`request`, `load`); no usa nada más
que la biblioteca estándar y `mitmproxy`.
"""

from __future__ import annotations

import time
from pathlib import Path

from mitmproxy import ctx, http

LOCALES = {"localhost", "127.0.0.1", "::1"}


class GuardarSubidas:
    def __init__(self) -> None:
        self.n = 0

    def load(self, loader) -> None:
        loader.add_option("salida", str, "", "Carpeta (fuera del repositorio) donde guardar los cuerpos")

    def _carpeta(self) -> Path | None:
        if not ctx.options.salida:
            return None
        carpeta = Path(ctx.options.salida)
        carpeta.mkdir(parents=True, exist_ok=True)
        return carpeta

    def request(self, flow: http.HTTPFlow) -> None:
        carpeta = self._carpeta()
        host = flow.request.pretty_host
        cuerpo = flow.request.get_content(strict=False) or b""
        if carpeta is None or host in LOCALES or not cuerpo:
            return
        self.n += 1
        (carpeta / f"{self.n:03d}.bin").write_bytes(cuerpo)
        linea = "\t".join([
            f"{self.n:03d}", time.strftime("%H:%M:%S"), flow.request.method, host,
            flow.request.path.split("?", 1)[0],
            flow.request.headers.get("content-type", ""),
            flow.request.headers.get("content-encoding", ""), str(len(cuerpo)),
        ])
        with open(carpeta / "resumen.tsv", "a", encoding="utf-8") as f:
            f.write(linea + "\n")


addons = [GuardarSubidas()]
