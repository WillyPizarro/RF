# Wireframes — HU-03: Consultar si una placa tiene requisitoria

## Proyecto / herramienta
- Herramienta: texto estructurado; prototipo vía `../bolt-prompt.md` (pendiente PA 14)
- Canal/formato: app móvil Android (referencia, ADR-0010), vertical

## Pantallas

| # | Pantalla / Estado | Escenario Gherkin | ID |
|---|---|---|---|
| 1 | Formulario placa + motivo | E1 (When) | PLA-01 |
| 2 | Falta motivo | E2 El usuario no indica el motivo | PLA-02 |
| 3 | Formato no válido | E4 La placa no tiene un formato válido | PLA-03 |
| 4 | Consultando | Transición | PLA-04 |
| 5 | Placa con requisitoria | E1 (Then) | PLA-05 |
| 6 | Sin requisitoria registrada | E5 La placa no tiene requisitoria en la fuente consultada | PLA-06 |
| 7 | No se pudo completar | E3 Fuente no disponible | PLA-07 |

### PLA-01 — Consultar placa
```
┌──────────────────────────────┐
│ ←  Consultar placa           │
├──────────────────────────────┤
│ Placa              [PA 20]   │
│ [ ABC-123            ] [📷]  │  ← 📷 = "Leer con cámara" (HU-04)
│                              │
│ Motivo de consulta * [PA 21] │
│ [Seleccione ▾]               │
│   Opción 1 (por definir)     │
│   Opción 2 (por definir)     │
│   Opción 3 (por definir)     │
│   Otro                       │
│ si elige "Otro":             │
│ Describa el motivo *         │
│ [texto, mín. 10 caracteres]  │
│                              │
│  [       CONSULTAR        ]  │
└──────────────────────────────┘
```
- La placa se muestra en mayúsculas y con fuente monoespaciada, para leerla bien.
- El componente de motivo es el mismo que en ROS-01: catálogo configurable más "Otro" (ADR-0011, provisional). Las opciones siguen "por definir": el catálogo inicial de ARCH se valida con el área usuaria y no se muestra como decidido.

### PLA-02 — Falta motivo
```
│ Motivo de consulta *         │
│ [________________________]   │  ← borde rojo
│ ⚠ Indique el motivo de la    │
│   consulta.                  │
```
- No se envía nada (E2). El foco se mueve al campo de motivo.
- Si eligió "Otro" con menos de 10 caracteres: "Describa el motivo (mínimo 10 caracteres)." Tampoco se envía (ADR-0011).

### PLA-03 — Formato no válido
```
│ Placa                        │
│ [ HOLA MUNDO          ]      │  ← borde rojo
│ ⚠ El formato de placa no es  │
│   válido. Formato esperado:  │
│   ABC-123 (3 letras o        │
│   números, guion, 3 números) │
│                  [PA 20]     │
```
- No se envía nada (E4). El mensaje muestra el formato esperado mientras el PA 20 siga abierto (ADR-0011). Si faltan el motivo y el formato a la vez, se muestran los dos mensajes juntos.

### PLA-04 — Consultando
```
│        ◌  Consultando…       │
│   Placa ABC-123              │
```
- El botón se desactiva para que no se envíe dos veces.

### PLA-05 — Placa con requisitoria
```
┌──────────────────────────────┐
│ ←  Resultado                 │
├──────────────────────────────┤
│ ┌──────────────────────────┐ │
│ │ ■ ROJO                    │ │
│ │  ABC-123                  │ │
│ │  TIENE REQUISITORIA       │ │
│ └──────────────────────────┘ │
│ ┌ - - - - - - - - - - - - -┐ │
│ │ Datos adicionales  PA 15 │ │
│ │ (campos por definir)     │ │
│ └ - - - - - - - - - - - - -┘ │
│ Motivo: <texto ingresado>    │
│ Consultado: 18/11/2026 10:42 │
│                              │
│  [     NUEVA CONSULTA     ]  │
└──────────────────────────────┘
```
- El bloque PA 15 se ve solo en la variante "Estado + datos". En "Solo estado" no aparece.
- No hay botones de acción operativa (llamar, alertar, etc.).

### PLA-06 — Sin requisitoria registrada (E5)
```
│ ┌──────────────────────────┐ │
│ │ ■ GRIS NEUTRO            │ │
│ │  DEF-456                 │ │
│ │  Sin requisitoria        │ │
│ │  registrada en la fuente │ │
│ │  consultada              │ │
│ └──────────────────────────┘ │
│ [Datos adicionales — PA 15]  │
│ Motivo / fecha-hora          │
│  [     NUEVA CONSULTA     ]  │
```
- Sin verde ni ✓ (E5: nada que se lea como "vehículo limpio"). Texto literal de E5. La consulta queda en la bitácora.

### PLA-07 — No se pudo completar
```
│            ⚠                 │
│ No se pudo completar la      │
│ consulta; intente nuevamente │
│                              │
│  [       REINTENTAR       ]  │  ← conserva placa y motivo
│  [ Volver ]                  │
```
- Texto literal de E3. Nunca dice "sin requisitoria". Ícono y color distintos a los de un resultado.
- El error queda en la bitácora (backend).

## Decisiones de diseño
- Placa y motivo en el mismo formulario (E2 parte de "ingresó una placa").
- "Reintentar" conserva lo escrito, para no obligar a repetir el motivo.

## Elementos no solicitados (aprobados el 2026-11-18)
- PLA-06 y su redacción.
- "Nueva consulta" en los resultados.
- Placas sintéticas `DEF-456` y `GHI-789`.

## Puntos abiertos que afectan el diseño
- PA 15: datos visibles en el resultado (bloque marcado).
- PA 20: formatos de placa. Validación provisional `AAA-999` (ADR-0011, no verificada contra la normativa).
- PA 21: motivo, provisional según ADR-0011 (catálogo configurable + "Otro").
- PA 4: tiempo máximo de respuesta. No hay timeout visual definido; el simulador responde en unos 1,5 s.

## Fuera de alcance respetado
- Fuentes reales; consultas en lote.
