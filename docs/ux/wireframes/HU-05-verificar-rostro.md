# Wireframes — HU-05: Verificar un rostro y recibir posibles coincidencias

## Proyecto / herramienta
- Herramienta: texto estructurado; prototipo vía `../bolt-prompt.md` (pendiente PA 14)
- Canal/formato: app móvil Android (referencia, ADR-0010), vertical

## Pantallas

| # | Pantalla / Estado | Escenario Gherkin | ID |
|---|---|---|---|
| 1 | Motivo de la verificación | E1 (Dado: indicó el motivo) | ROS-01 |
| 2 | Captura de rostro | E1 (When) | ROS-02 |
| 3 | Captura rechazada con motivo | E2 No pasa el control de calidad | ROS-03 |
| 4 | Comparando | Transición | ROS-04 |
| 5 | Posible coincidencia — requiere revisión | E1 (Then) | ROS-05 |
| 6 | No concluyente | E3 Banda intermedia | ROS-06 |
| 7 | Sin coincidencia en la lista consultada | E4 | ROS-07 |
| 8 | No se pudo completar | E5 El servicio de comparación no responde (y HU-08 E3) | ROS-08 |

### ROS-01 — Motivo (paso 1 de 2)
```
┌──────────────────────────────┐
│ ←  Verificar rostro   1 de 2 │
├──────────────────────────────┤
│ Motivo de consulta * [PA 21] │
│ [ mismo componente PLA-01 ]  │
│                              │
│ ┌ - - - - - - - - - - - - -┐ │
│ │ PA 7 · solo variante 1:1 │ │
│ │ Identidad declarada      │ │
│ │ [______________________] │ │
│ │ (tipo de dato por definir│ │
│ └ - - - - - - - - - - - - -┘ │
│                              │
│  [  CONTINUAR A CÁMARA    ]  │
└──────────────────────────────┘
```
- Sin motivo: mismo error que PLA-02 y la cámara no se abre.

### ROS-02 — Captura (paso 2 de 2)
```
│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│░░░░░░░░╭──────────╮░░░░░░░░░░│
│░░░░░░░░│  óvalo   │░░░░░░░░░░│
│░░░░░░░░│  guía    │░░░░░░░░░░│
│░░░░░░░░╰──────────╯░░░░░░░░░░│
│ Rostro de frente, buena luz, │
│ una sola persona.            │
│ ┌ - - - - - - - - - - - - -┐ │
│ │ Aviso a la persona —     │ │
│ │ por definir      [PA 25] │ │
│ └ - - - - - - - - - - - - -┘ │
│          ( ◉ CAPTURAR )      │
```
- Cámara trasera. Una captura por toque. Sin video ni galería.
- PA 25: zona reservada para un posible aviso a la persona fotografiada. No se diseñó su contenido ni un paso de consentimiento. Si se decide que el aviso es un paso previo, iría entre ROS-01 y ROS-02.

### ROS-03 — Captura rechazada
```
│            ⚠                 │
│  Mire de frente              │  ← motivo concreto, grande
│                              │
│  La captura no se envió a    │
│  comparar.                   │
│  [   REPETIR CAPTURA      ]  │
```
- Motivos posibles (de E2 y de la skill de biometría): "Mire de frente", "Más luz", "Imagen borrosa", "Solo debe aparecer una persona", "No se detectó un rostro".
- No muestra la foto rechazada.

### ROS-04 — Comparando
```
│     ◌  Comparando con la     │
│        lista de prueba…      │
```

### ROS-05 — Posible coincidencia — requiere revisión
```
┌──────────────────────────────┐
│ ←  Resultado                 │
├──────────────────────────────┤
│ ┌──────────────────────────┐ │
│ │ ■ ÁMBAR                  │ │
│ │ Posible coincidencia —   │ │
│ │ requiere revisión        │ │
│ └──────────────────────────┘ │
│ Esto no es una identificación│
│ Un revisor debe validar la   │
│ coincidencia.                │
│                              │
│ Estado: ⏳ Pendiente de      │
│         revisión             │
│ [Datos del candidato PA 15/22│
│  — no se muestran por ahora] │
│ Motivo / fecha-hora / ID     │
│                              │
│ Var. A: [ VER EN MIS VERIF. ]│
│ Var. B: [  REVISAR AHORA   ] │  ← PA 2 · requiere reabrir ADR-0003
│  [   NUEVA VERIFICACIÓN   ]  │
└──────────────────────────────┘
```
- La palabra "identificado" no aparece. No se muestra el score. Sin alertas ni acciones automáticas.

### ROS-06 — No concluyente
```
│ ┌──────────────────────────┐ │
│ │ ■ GRIS/AZUL              │ │
│ │ No concluyente —         │ │
│ │ verifique por otros      │ │
│ │ medios                   │ │
│ └──────────────────────────┘ │
│  [   NUEVA VERIFICACIÓN   ]  │
```

### ROS-07 — Sin coincidencia en la lista consultada
```
│ ┌──────────────────────────┐ │
│ │ ■ GRIS NEUTRO            │ │
│ │ Sin coincidencia en la   │ │
│ │ lista consultada         │ │
│ └──────────────────────────┘ │
│ La comparación se hizo solo  │
│ contra la lista disponible.  │  ← propuesta
│                     [PA 7]   │
│  [   NUEVA VERIFICACIÓN   ]  │
```
- Nunca dice "persona sin requisitoria". Sin verde.

### ROS-08 — No se pudo completar
```
│            ⚠                 │
│ No se pudo completar la      │
│ verificación; intente        │
│ nuevamente                   │
│  [ REPETIR CAPTURA ] [Volver]│
```
- Texto literal de E5. No muestra ninguno de los tres resultados faciales. El error queda en la bitácora.

## Decisiones de diseño
- El motivo va antes de la cámara: no se fotografía a nadie sin un motivo registrado.
- Los tres textos de resultado son literales de la HU, en el tamaño más grande de la pantalla.
- Los colores no comunican "limpio" (sin verde).

## Elementos no solicitados (aprobados el 2026-11-18)
- Subtítulos de ROS-05 y ROS-07.
- ROS-08.
- Indicador de pasos "1 de 2 / 2 de 2".

## Puntos abiertos que afectan el diseño
- PA 7: 1:1 o lista (campo "Identidad declarada" y textos de ROS-05/07).
- PA 2: botón posterior en ROS-05. La variante A (revisor separado) es la de ADR-0003; la variante B requiere reabrir ADR-0003.
- PA 15 / PA 22: datos y número de candidatos visibles para el agente. Por defecto no se ven.
- PA 21: motivo (provisional, ADR-0011: catálogo + "Otro").
- PA 25: aviso a la persona fotografiada (zona reservada en ROS-02).
- PA 4 y PA 16: umbrales y conservación de imágenes. Sin impacto visual hoy.

## Fuera de alcance respetado
- Identificación masiva, video continuo, comparación sin motivo, fuentes biométricas reales.
