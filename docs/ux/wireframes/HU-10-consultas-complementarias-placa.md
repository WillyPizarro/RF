# Wireframes — HU-10: Consultas complementarias de placa (simuladas)

> **Estado: aprobado por el humano el 2026-11-20 (vía PM)**: HU-10 completa, incluidos COM-03 (confirmación de la marca) y E7 "Placa no registrada en SUNARP (simulado)". Base: PRD `c200dc9` (PA 35) y `docs/hus/HU-10-consultas-complementarias-placa.md` (BA, E1 a E7, PA 36). Decisiones del humano del mismo día:
> - dos fuentes simuladas separadas, registro vehicular y papeletas, sin propietario por esquema cerrado;
> - en la bitácora solo van eventos, sin tabla nueva ni datos devueltos guardados;
> - con cero papeletas queda el texto "Sin papeletas pendientes registradas en SAT Lima", con la leyenda "Solo cubre papeletas de Lima Metropolitana".
>
> **No se desarrolla** hasta nueva orden del PM (sin contrato, código ni pruebas).

## Proyecto / herramienta
- Herramienta: texto estructurado + prototipo local `../prototipo/index.html` (panel de demo → "Consultas complementarias").
- Canal/formato: app móvil Android (referencia, ADR-0010), vertical.

## Pantallas

| # | Pantalla / Estado | Escenario Gherkin (HU-10) | ID |
|---|---|---|---|
| 1 | Sección "Consultas complementarias (simuladas)" en el resultado | E1 y E2 (Dado / Cuando); E6 | PLA-05 y PLA-06 (cambio) |
| 2 | Consultando | Transición | COM-01 |
| 3 | Datos del vehículo, para comparar | E1 (Entonces) | COM-02 |
| 4 | Confirmar la marca | E5 (confirma en el aviso previo) | COM-03 |
| 5 | Datos del vehículo, marcado | E5 (Entonces) | COM-02 · marcado |
| 6 | Placa no registrada en SUNARP | E7 | COM-02 · no registrada |
| 7 | Papeletas | E2 (Entonces) | COM-04 |
| 8 | Sin papeletas pendientes en SAT Lima | E3 | COM-04 · sin papeletas |
| 9 | No se pudo completar la consulta | E4 | COM-05 |
| 10 | Sin la sección | E6 (error, sin motivo, formato no válido); PA 36 a | PLA-07, PLA-02/03, PLA-08 |

### PLA-05 / PLA-06 — Se agrega la sección (debajo del resultado, que no cambia)
```
│ ┌──────────────────────────┐ │
│ │ ABC-123                  │ │
│ │ TIENE REQUISITORIA       │ │  ← o "Sin requisitoria registrada…"
│ └──────────────────────────┘ │
│ Motivo / Consultado / ID     │
│ ┌──────────────────────────┐ │
│ │ Consultas complementarias│ │
│ │ (simuladas)      [PA 35] │ │
│ │ Usan el mismo motivo: …  │ │
│ │ [Datos del vehículo      │ │
│ │  (SUNARP, simulado)    ] │ │
│ │ [Papeletas (SAT Lima,    │ │
│ │  simulado)             ] │ │
│ └──────────────────────────┘ │
│ [ AVISAR AL 105 (SIMULADO) ] │  ← solo PLA-05 (HU-09)
│ [     NUEVA CONSULTA      ]  │
```
- Una consulta por toque, solo a pedido (E6). El motivo no se vuelve a pedir.
- Ya consultado, el botón muestra "· ✓ hh:mm" y vuelve a abrir el resultado **sin otra consulta ni otro registro** (PA 36 c, variante mínima).

### COM-02 — Datos del vehículo (SUNARP, simulado)
```
┌──────────────────────────────┐
│ ←  Datos del vehículo        │
├──────────────────────────────┤
│ ⓘ SIMULACIÓN. Datos          │
│   sintéticos de SUNARP       │
│   (simulado). No se consultó │
│   ninguna fuente real.       │
│ Placa: ABC-123               │
│ Características registradas  │
│ Marca            Toyota      │
│ Modelo           Yaris       │
│ Color            Plata       │
│ Año              2018        │
│ Estado registral Inscrito    │
│ No se muestra el propietario.│
│ 👁 Compare estos datos con el │  ← ámbar suave: es una tarea,
│   vehículo que tiene delante.│     no un resultado
│ Motivo / Consultado          │
│ [ NO COINCIDE CON LO         │
│   REGISTRADO ]               │  → COM-03
│ [  VOLVER AL RESULTADO    ]  │
```
- Sin nombre, DNI ni otro dato del propietario (E1). Nunca "placa clonada" ni otra conclusión.
- No hay botón "Sí coincide": el PRD no lo pide.

### COM-03 — Confirmar la marca
```
│ ┌──────────────────────────┐ │
│ │ ¿Marcar que el vehículo  │ │
│ │ no coincide con lo       │ │
│ │ registrado?              │ │
│ │ La marca queda en la     │ │
│ │ bitácora con el motivo   │ │
│ │ de la consulta y no se   │ │
│ │ puede quitar.   [PA 36b] │ │
│ │ [ Marcar ]               │ │
│ │ [ Cancelar ]             │ │  → COM-02, sin registrar nada
│ └──────────────────────────┘ │
```

### COM-02 · marcado
```
│ ⚑ Marcado: No coincide con   │
│   lo registrado · 14:40      │
│ Quedó en la bitácora. La app │
│ no saca ninguna conclusión:  │
│ verifique por otros medios.  │
│                   [PA 36 b]  │
│ [  VOLVER AL RESULTADO    ]  │
```
- Gris pizarra: no es una alerta. Ninguna acción automática (E5). El resultado de requisitoria no cambia.
- La marca no dice qué característica no coincide y no se deshace (PA 36 b, variante mínima).

### COM-02 · no registrada (E7)
```
│ ┌──────────────────────────┐ │
│ │ SUNARP (SIMULADO)        │ │
│ │ Placa no registrada en   │ │  ← neutro, como PLA-08
│ │ SUNARP (simulado).       │ │
│ │ Verifique la placa.      │ │
│ └──────────────────────────┘ │
│ [  VOLVER AL RESULTADO    ]  │
```
- Ni error ni conclusión. Sin "No coincide con lo registrado", porque no hay datos que comparar. Queda en la bitácora.

### COM-04 — Papeletas (SAT Lima, simulado)
```
│ ⓘ SIMULACIÓN. Datos          │
│   sintéticos de SAT Lima…    │
│ ┌──────────────────────────┐ │
│ │ SAT LIMA (SIMULADO)      │ │
│ │ 3 papeletas pendientes   │ │
│ └──────────────────────────┘ │
│ Monto pendiente  S/ 1,240.00 │
│ ¿Alguna grave?   Sí          │
│ Solo cubre papeletas de Lima │
│ Metropolitana.     [PA 35]   │
│ [  VOLVER AL RESULTADO    ]  │
```
- **COM-04 · sin papeletas (E3):** el recuadro dice "Sin papeletas pendientes registradas en SAT Lima", en gris y sin verde, y mantiene la nota "Solo cubre papeletas de Lima Metropolitana."

### COM-05 — No se pudo completar (E4)
```
│            ⚠                 │
│ No se pudo completar la      │
│ consulta a SUNARP (simulado);│  ← o "a SAT Lima (simulado)"
│ intente nuevamente           │
│ [ REINTENTAR ]  [ Volver ]   │
```
- Nunca "sin papeletas", "sin observaciones" ni un dato vacío (regla 7). El error va a la bitácora y el resultado de requisitoria no cambia.

## Reglas de pantalla
- **Dónde aparece:** solo en PLA-05 y PLA-06. No aparece en PLA-07, PLA-02/03 (E6) ni en PLA-08: ahí se ve una marca reservada "PA 36 a".
- **Simulación evidente:** la tarjeta "SIMULACIÓN" encabeza COM-02 y COM-04 (mismo patrón aprobado en HU-09).
- **Bitácora:** solo eventos (decisión del humano, 2026-11-20). No hay tabla nueva y no se guardan los datos devueltos (marca, color, papeletas…).
  - `CONSULTA_VEHICULO_REGISTRAL` y `CONSULTA_PAPELETAS`, con usuario, fecha y hora, **el mismo motivo**, la placa y la consulta de origen. En pantalla se leen "Consulta SUNARP (simulada)" y "Consulta de papeletas SAT Lima (simulada)".
  - `MARCA_NO_COINCIDE`, con los mismos datos. En pantalla: "Marca: No coincide con lo registrado".
  - Los errores, como "Error".
- **Accesibilidad:** el foco va al título; los botones miden al menos 48 × 48; los datos se leen como pares etiqueta-valor.

## Decisiones de diseño aplicadas
- La sección va debajo del resultado, que no cambia, y encima del aviso al 105: lo primero sigue siendo el resultado de requisitoria.
- La tarjeta "Compare estos datos…" usa el ámbar suave de aviso porque le pide una tarea al agente; los datos registrados van en negro neutro.
- La marca se muestra en gris pizarra, no en rojo, para que no se lea como una conclusión.

## Elementos no solicitados (aprobados por el humano el 2026-11-20)
1. COM-03, la confirmación previa de la marca.
2. COM-02 · no registrada, "Placa no registrada en SUNARP (simulado)" (E7).
3. La tarjeta "SIMULACIÓN", que ya estaba aprobada como patrón en HU-09.

## Puntos abiertos que afectan el diseño
- **PA 35:** ¿se aceptan las consultas? ¿Qué campos? ¿Basta con solo Lima o se simula una fuente nacional? Si cambian los campos, cambian las filas de COM-02 y COM-04, no el flujo.
- **PA 36 (variante mínima marcada "PA 36"):**
  - a) ¿se ofrecen en PLA-08? Hoy no;
  - b) ¿la marca dice qué característica no coincide, o se puede deshacer? Hoy no; si se pide, COM-03 suma una lista de características o un comentario;
  - c) ¿se repite la consulta con un nuevo registro? Hoy se vuelve a ver sin repetirla.
- **PA 15:** qué datos muestra el resultado (aquí se muestran características del vehículo, nunca del propietario).

## Fuera de alcance respetado
- Ningún dato del propietario (nombre, DNI, domicilio).
- Ninguna conclusión de "placa clonada", ni alerta o acción automática.
- Ninguna fuente real (SUNARP, SAT, SUTRAN, municipalidades): todo es simulado.
- Ninguna consulta complementaria sin un resultado de requisitoria ni sin que el usuario la pida.
