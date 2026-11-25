# Wireframes — HU-05 (variante): Foto con varias personas, se elige un solo rostro

> **Estado: aprobado por el humano el 2026-11-20 (vía PM)**, junto con HU-05 E8 y E9. Base: PRD `2796632`. Escenarios del BA: HU-05 **E8** (elige un rostro), **E9** (sale sin elegir) y **E10** (más de 5 rostros); E2 ya no rechaza por más de un rostro. Supuestos de trabajo del humano del 2026-11-20, hasta que responda el MININTER: PA 33 (máximo 5 rostros; la bitácora guarda solo la cantidad) y ADR-0015 opción A (recorte en el celular; solo viaja el recorte). **No se desarrolla** hasta nueva orden del PM (sin contrato, código ni pruebas).

## Proyecto / herramienta
- Herramienta: texto estructurado + prototipo local `../prototipo/index.html` (panel de demo → "Personas en la foto").
- Canal/formato: app móvil Android (referencia, ADR-0010), vertical.

## Qué dice el PRD (y nada más)
- La captura puede incluir a más de una persona.
- La app marca los rostros detectados y el usuario elige **uno solo**, con su motivo de consulta.
- Solo ese rostro se compara. Los demás **no se comparan, no se guardan ni se registran**.
- No es identificación masiva: sigue siendo una consulta por persona.

## Pantallas

| # | Pantalla / Estado | Escenario Gherkin (HU-05) | ID |
|---|---|---|---|
| 1 | Captura: texto de ayuda ajustado | E8 (Dado) | ROS-02 (cambio) |
| 2 | Elegir un rostro (nada elegido) | E8 (Cuando); E9 sale sin elegir | ROS-10 |
| 3 | Elegir un rostro (uno elegido) | E8 (Entonces: solo ese se compara) | ROS-10 · elegido |
| 4 | Rostro elegido con mala calidad | E2 aplicado al rostro elegido | ROS-03 (reusa) |
| 5 | Comparando y resultados | Igual que HU-05 E1 y E3 a E5 | ROS-04 a ROS-08 (sin cambios) |
| 6 | Más de 5 rostros: se rechaza sin ofrecer elegir | E10 (PA 33, supuesto de trabajo) | ROS-03 · más de 5 |
| 7 | Rostros muy juntos para recortar el elegido | E8 + ADR-0015 (rechazo en el celular) | ROS-03 · rostros juntos |

Con **un solo** rostro detectado, el flujo es el de hoy (ROS-02 → ROS-04), sin pasar por ROS-10. Con **ninguno**, ROS-03 "No se detectó un rostro", como hoy. Con **más de 5**, ROS-03 · más de 5, sin pasar por ROS-10.

### ROS-03 · más de 5 (E10)
```
│            ⚠                 │
│ Hay más de 5 personas en la  │  ← motivo, grande
│ foto                         │
│ Acérquese a una sola persona │
│ y repita la captura. [PA 33] │
│ La captura no se envió a     │
│ comparar.                    │
│  [   REPETIR CAPTURA      ]  │
```
- No se marca ningún rostro ni se ofrece elegir. No se compara nada y no queda ninguna comparación en la bitácora (igual que E2).

### ROS-03 · rostros juntos (ADR-0015)
```
│            ⚠                 │
│ Los rostros están muy juntos │
│ Acérquese a la persona y     │
│ repita la captura.           │
│ La captura no se envió a     │
│ comparar.                    │
│  [   REPETIR CAPTURA      ]  │
```
- Aparece después de elegir, cuando el celular no puede recortar el rostro elegido sin incluir parte de otro. Como el recorte se hace en el celular (ADR-0015 opción A), no se envía nada.

### ROS-02 — Captura (cambia solo el texto de ayuda)
```
│░░░░░░░░╭──────────╮░░░░░░░░░░│
│░░░░░░░░│  óvalo   │░░░░░░░░░░│
│░░░░░░░░╰──────────╯░░░░░░░░░░│
│ Rostro de frente, buena luz. │
│ Si hay varias personas,      │
│ después elegirá una.         │
│ ┌ - - Aviso a la persona - ┐ │
│ │ por definir      [PA 25] │ │
│ └ - - - - - - - - - - - - -┘ │
│          ( ◉ CAPTURAR )      │
```
- Antes decía "una sola persona". El óvalo sigue como guía para encuadrar a la persona de interés.

### ROS-10 — Elija un rostro
```
┌──────────────────────────────┐
│ DATOS SINTÉTICOS · PROTOTIPO │
│ ←  Verificar rostro   2 de 2 │
├──────────────────────────────┤
│ Elija el rostro que quiere   │
│ verificar                    │
│ ┌──────────────────────────┐ │
│ │  ┌─┐     ┌─┐     ┌─┐     │ │  foto capturada, con un
│ │  │1│     │2│     │3│     │ │  recuadro numerado por
│ │  └─┘     └─┘     └─┘     │ │  rostro detectado
│ │   ▲       ▲       ▲      │ │
│ └──────────────────────────┘ │
│ [ Rostro 1 ][ Rostro 2 ][ 3 ]│  ← mismos rostros, como botones
│                              │
│ Solo se comparará el rostro  │
│ que elija. Los demás no se   │
│ comparan ni se guardan.      │
│                              │
│ [ COMPARAR ESTE ROSTRO ] gris│  ← desactivado hasta elegir
│ [ Repetir captura ]          │
└──────────────────────────────┘
```

### ROS-10 · elegido
```
│ ┌──────────────────────────┐ │
│ │  ┌─┐     ┏━┓     ┌─┐     │ │  el elegido: borde grueso azul
│ │  ░1░     ┃2┃     ░3░     │ │  los demás: atenuados
│ │  └─┘     ┗━┛     └─┘     │ │
│ └──────────────────────────┘ │
│ [ Rostro 1 ][■Rostro 2■][ 3 ]│
│ Rostro 2 elegido.            │
│ [  COMPARAR ESTE ROSTRO   ]  │  → ROS-04 (o ROS-03 si el rostro
│ [ Repetir captura ]          │     elegido no pasa la calidad)
```

## Reglas de pantalla
- **Nada se compara antes de elegir.** ROS-10 no muestra puntajes, colores ni orden de "más probable": todos los recuadros se ven iguales hasta que el usuario toca uno (regla 4 y regla 6).
- **Se elige uno solo.** Tocar otro recuadro cambia la elección; no hay selección múltiple ni "comparar todos".
- **El motivo es el de ROS-01**, indicado antes de abrir la cámara (regla 2). ROS-10 no lo vuelve a pedir.
- **Control de calidad solo del rostro elegido** (regla 3). Si falla, ROS-03 con su motivo ("Mire de frente", "Más luz", "Imagen borrosa") y "Repetir captura", que vuelve a ROS-02. Los otros rostros no se evalúan.
- **"Solo debe aparecer una persona" deja de ser un motivo de rechazo** en ROS-03 (HU-05 E2, confirmado por el BA). Se agregan "Hay más de 5 personas en la foto" (E10) y "Los rostros están muy juntos" (ADR-0015).
- **Salir sin elegir descarta la foto completa (E9):** "←", Atrás de Android, "Repetir captura" o cerrar la sesión. No se compara nada y no queda nada en la bitácora.
- **Un solo rostro por foto.** Después de comparar, el resultado no ofrece "elegir otro rostro de esta foto": otra persona es otra consulta, con su motivo y su captura (regla del BA).
- **Solo se envía el rostro elegido.** El celular lo recorta y solo viaja el recorte (ADR-0015 opción A). Si resulta candidato, se guarda solo ese recorte, y el revisor (REV-02) ve en "CAPTURA" solo ese rostro, nunca la foto completa con los demás (regla del BA; ver HU-06).
- **Bitácora:** un único registro "Verificación de rostro", como hoy, con el dato **"Rostros en la foto: N"** (PA 33, supuesto de trabajo: solo la cantidad, sin ningún dato de las otras personas). Solo lo lleva la verificación que se compara; los rechazos (E2, E10) no registran comparación.
- **Accesibilidad:** cada rostro es un botón de al menos 48 × 48 con etiqueta "Rostro N de M". La fila de botones debajo de la foto existe para quien no puede tocar con precisión un recuadro chico. El orden es de izquierda a derecha.

## Decisiones de diseño aplicadas
- **Paso dentro de la captura, no un paso nuevo:** el indicador sigue en "2 de 2". Elegir el rostro es parte de capturar.
- **Elección en dos toques** (elegir y luego "Comparar este rostro"), para que un toque accidental sobre la foto no envíe a nadie a comparar.
- **Los no elegidos se atenúan** al elegir, para que quede claro cuál se envía; no se difuminan antes, porque el usuario necesita verlos para elegir.
- **Sin zoom ni recorte manual:** si la persona de interés no fue detectada, el usuario repite la captura. No se dibujan recuadros a mano.

## Elementos no solicitados por el PRD (aprobados por el humano el 2026-11-20)
1. La fila de botones "Rostro 1 / 2 / 3" bajo la foto (accesibilidad).
2. El texto "Solo se comparará el rostro que elija. Los demás no se comparan ni se guardan."
3. El paso de confirmación "Comparar este rostro" después de elegir.

## Puntos abiertos de negocio que afectan el diseño
1. **PA 33** (supuesto de trabajo del humano, 2026-11-20, hasta que responda el MININTER): máximo 5 rostros, con rechazo en ROS-03 · más de 5; la bitácora guarda solo la cantidad. Si el MININTER fija otro número, cambian el texto de ROS-03 y el umbral, no el flujo.
2. ~~¿Recorte en el teléfono?~~ **Resuelto:** ADR-0015 opción A (recorte en el celular; solo viaja el recorte).
3. Si un rostro detectado es muy pequeño para la calidad mínima, ¿se marca igual (y falla al elegirlo) o no se marca? El diseño lo marca y deja que la calidad lo rechace con su motivo.
4. PA 25 (aviso a la persona fotografiada): con varias personas en la foto, ¿el aviso alcanza también a las que no se eligen?

## Fuera de alcance respetado
- Comparar varios rostros a la vez, en lote o "todos".
- Video continuo, ráfaga o carga desde galería.
- Detección o marcado de rostros en vivo sobre el visor (solo se marcan en la foto ya tomada, tras tocar "Capturar").
