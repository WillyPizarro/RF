"""Genera la hoja A4 imprimible con placas SINTÉTICAS de prueba para HU-04 (ENCARGO-HU-04, M-1).

    python pruebas/datos/generar_hoja_placas.py

Lee las placas de la semilla de HU-08 (`services/simuladores/app/datos/semilla.json`); no las
copia a mano. Escribe `pruebas/datos/hoja-placas-prueba.html`.

Qué contiene la hoja (CONTRATO-HU-04 §7, decisión 4; M-1):
- 8 placas: las fijas de HU-08 (`ZZA-101` con requisitoria, `ZZB-201` sin ella y `ZZZ-999`, que a
  propósito NO está en la semilla y sirve para probar PLA-08) y 5 más de la semilla (3 con
  requisitoria y 2 sin ella, en el orden de la semilla), todas con prefijo `ZZ`.
- Una placa por página, A4 horizontal, al 90 % del tamaño real (30 × 15 cm → 27 × 13,5 cm).
- Fondo blanco, texto negro grueso, formato `ZZA-101`.
- La leyenda "PRUEBA — NO VÁLIDA" va FUERA del recuadro de los caracteres.
- Ninguna imagen: solo HTML y CSS.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SEMILLA = RAIZ / "services" / "simuladores" / "app" / "datos" / "semilla.json"
SALIDA = Path(__file__).resolve().parent / "hoja-placas-prueba.html"

FIJAS = ["ZZA-101", "ZZB-201", "ZZZ-999"]  # CONTRATO-HU-08, datos fijos
FORMATO = re.compile(r"^ZZ[A-Z0-9]-[0-9]{3}$")
ESCALA = 0.90
ANCHO_CM, ALTO_CM = 30 * ESCALA, 15 * ESCALA  # 27 × 13,5 cm


def elegir_placas() -> list[tuple[str, str]]:
    """(placa, nota) para la hoja. Lanza si la semilla no cumple lo que se espera de HU-08."""
    vehiculos = json.loads(SEMILLA.read_text(encoding="utf-8"))["vehiculos"]
    en_semilla = {v["placa"]: v for v in vehiculos}
    assert "ZZA-101" in en_semilla and en_semilla["ZZA-101"]["requisitoria_vigente"] is True
    assert "ZZB-201" in en_semilla and en_semilla["ZZB-201"]["requisitoria_vigente"] is False
    assert "ZZZ-999" not in en_semilla
    otras = [v for v in vehiculos if v["placa"] not in FIJAS]
    con = [v["placa"] for v in otras if v["requisitoria_vigente"] is True][:3]
    sin = [v["placa"] for v in otras if v["requisitoria_vigente"] is False][:2]
    placas = [
        ("ZZA-101", "fija HU-08 · con requisitoria"),
        ("ZZB-201", "fija HU-08 · sin requisitoria"),
        ("ZZZ-999", "fija HU-08 · no registrada en la fuente (PLA-08)"),
        *[(p, "semilla · con requisitoria") for p in con],
        *[(p, "semilla · sin requisitoria") for p in sin],
    ]
    for p, _ in placas:
        assert FORMATO.match(p), f"{p} no es una placa sintética ZZ válida"
    assert 6 <= len(placas) <= 8
    return placas


def html_hoja(placas: list[tuple[str, str]]) -> str:
    paginas = []
    instruccion = ('<p class="instruccion"><b>Para imprimir:</b> abra este archivo en el navegador '
                   'e imprima en A4 horizontal al 100 % (sin "ajustar a la página"). Una placa por '
                   'hoja. Solo placas sintéticas <b>ZZ</b>, nunca placas de vehículos reales.</p>')
    for n, (placa, nota) in enumerate(placas, 1):
        paginas.append(f"""
  <section class="pagina">
    {instruccion if n == 1 else ""}
    <p class="cabecera">Hoja de prueba HU-04 · placa {n} de {len(placas)} · escala {int(ESCALA * 100)} %
      ({ANCHO_CM:g} × {ALTO_CM:g} cm; real 30 × 15 cm) · {html.escape(nota)}</p>
    <div class="placa"><span class="caracteres">{html.escape(placa)}</span></div>
    <p class="leyenda">PRUEBA — NO VÁLIDA · placa sintética para pruebas del prototipo</p>
  </section>""")
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Placas de prueba HU-04</title>
<!-- Generado por pruebas/datos/generar_hoja_placas.py desde la semilla de HU-08. No editar a mano.
     Para imprimir: abrir en el navegador, imprimir en A4 horizontal al 100 % (sin "ajustar a la
     página") y con márgenes "Ninguno" o "Predeterminado". -->
<style>
  @page {{ size: A4 landscape; margin: 1cm; }}
  html, body {{ margin: 0; background: #fff; color: #000; }}
  body {{ font-family: Arial, Helvetica, sans-serif; }}
  .instruccion {{ font-size: 10pt; margin: 0 0 0.3cm; text-align: center; }}
  .pagina {{ page-break-after: always; break-after: page; height: 18cm;
            display: flex; flex-direction: column; align-items: center; justify-content: center; }}
  .pagina:last-child {{ page-break-after: auto; break-after: auto; }}
  .cabecera {{ font-size: 9pt; margin: 0 0 0.4cm; color: #444; }}
  .placa {{ box-sizing: border-box; width: {ANCHO_CM}cm; height: {ALTO_CM}cm; background: #fff;
           border: 0.45cm solid #000; border-radius: 0.6cm; display: flex;
           align-items: center; justify-content: center; }}
  .caracteres {{ font-family: "Arial Black", "Helvetica Neue", Arial, sans-serif; font-weight: 900;
                font-size: 5.2cm; letter-spacing: 0.1cm; line-height: 1; color: #000;
                white-space: nowrap; }}
  .leyenda {{ font-size: 12pt; font-weight: bold; margin: 0.4cm 0 0; letter-spacing: 0.05cm; }}
  @media screen {{ .pagina {{ border-bottom: 1px dashed #999; padding: 1cm 0; }} }}
</style>
</head>
<body>
{"".join(paginas)}
</body>
</html>
"""


def main() -> None:
    placas = elegir_placas()
    SALIDA.write_text(html_hoja(placas), encoding="utf-8")
    print(f"{SALIDA.relative_to(RAIZ)}: {len(placas)} placas -> {', '.join(p for p, _ in placas)}")


if __name__ == "__main__":
    main()
