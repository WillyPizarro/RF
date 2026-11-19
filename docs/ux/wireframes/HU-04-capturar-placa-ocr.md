# Wireframes — HU-04: Capturar la placa con la cámara

## Proyecto / herramienta
- Herramienta: texto estructurado; prototipo vía `../bolt-prompt.md` (pendiente PA 14)
- Canal/formato: app móvil Android (referencia, ADR-0010), vertical

## Pantallas

| # | Pantalla / Estado | Escenario Gherkin | ID |
|---|---|---|---|
| 1 | Visor de cámara | E1 (When) | OCR-01 |
| 2 | Confirmar o corregir lectura | E1 (Then) | OCR-02 |
| 3 | Lectura fallida | E2 La placa no se puede leer | OCR-03 |
| 4 | Sin permiso de cámara | E3 El usuario negó el permiso | OCR-04 |

### OCR-01 — Visor de cámara
```
┌──────────────────────────────┐
│ ✕  Leer placa                │
├──────────────────────────────┤
│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│░░░░┌──────────────────┐░░░░░░│
│░░░░│   marco de placa │░░░░░░│
│░░░░└──────────────────┘░░░░░░│
│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│ Encuadre la placa y toque    │
│ Capturar                     │
│          ( ◉ CAPTURAR )      │
│   Ingresar manualmente       │
└──────────────────────────────┘
```
- Se lee **una sola** imagen, solo al tocar "Capturar". No hay lectura continua (fuera de alcance).

### OCR-02 — Confirmar o corregir
```
│ Placa leída                  │
│ [ ABC-123            ] ✎     │  ← campo editable
│ Confirme o corrija la placa  │
│ antes de consultar.          │
│                              │
│  [    USAR ESTA PLACA     ]  │  → PLA-01 con la placa cargada
│  [ Volver a capturar ]       │
```
- No muestra la foto de la placa (no se guarda, por el supuesto de minimización).
- "Usar esta placa" **no consulta**: devuelve al formulario PLA-01, donde falta el motivo y el toque en "Consultar".

### OCR-03 — Lectura fallida
```
│            ⚠                 │
│ No se pudo leer la placa.    │
│ Pruebe de frente y con más   │
│ luz.                         │
│  [   VOLVER A INTENTAR    ]  │
│  [ Ingresar manualmente ]    │
```
- No se envía ninguna consulta (E2).

### OCR-04 — Sin permiso de cámara
```
│            📷✕               │
│ La app no tiene permiso para │
│ usar la cámara.              │
│ Para darlo: Ajustes ›        │
│ Aplicaciones › Movil Buscador│
│ › Permisos › Cámara.         │
│  [     ABRIR AJUSTES      ]  │
│  [ Ingresar manualmente ]    │
```
- Ruta de ajustes de Android (ADR-0010: Android de referencia, provisional hasta el PA 12).

## Decisiones de diseño
- Disparo manual con botón grande, por la regla de no hacer lectura continua.
- "Ingresar manualmente" está siempre visible, como salida.

## Elementos no solicitados (aprobados el 2026-11-18)
- Botón "Abrir ajustes" (E3 dice "explica cómo"; el botón facilita hacerlo).

## Puntos abiertos que afectan el diseño
- PA 4: precisión mínima de la lectura.
- PA 16: conservar o no la imagen de la placa. Hoy no se guarda.
- PA 12: dispositivos (provisional: Android, ADR-0010).

## Fuera de alcance respetado
- Lectura continua o automática; carga desde galería.
