# Wireframes — HU-06: Revisar una posible coincidencia facial

## Proyecto / herramienta
- Herramienta: texto estructurado; prototipo vía `../bolt-prompt.md` (pendiente PA 14)
- Canal/formato: app móvil Android (referencia, ADR-0010), vertical

## Pantallas

| # | Pantalla / Estado | Escenario Gherkin | ID |
|---|---|---|---|
| 1 | Pendientes de revisión (revisor) | E1 (Dado) / E3 (sin alertas) | REV-01 |
| 2 | Captura vs. referencia + decisión | E1 | REV-02 |
| 3 | Falta motivo de la decisión | E2 Decisión sin motivo | REV-03 |
| 4 | Decisión registrada | E1 (Then) | REV-04 |
| 5 | Mis verificaciones (agente) | E1 "ve el resultado" / E3 "ve Pendiente" | VER-01 |
| 6 | Detalle de mi verificación | E1 / E3 | VER-02 |
| 7 | Revisión vencida | E4 Nadie revisa la coincidencia en 24 horas (provisional ADR-0008, PA 23) | VER-01/02 (agente); sale de REV-01; BIT-01/02 (supervisor) |

**PA 2.** Variante A: el revisor es un rol propio y entra a REV-01 al iniciar sesión. Variante B: el agente revisa su propia coincidencia desde ROS-05 → REV-02 (HU-05 y HU-06 se fusionan). **Requiere reabrir ADR-0003**, que prohíbe que un agente revise su propia consulta. El prototipo usa por defecto la variante A. REV-02, REV-03 y REV-04 son iguales en ambas variantes.

### REV-01 — Pendientes de revisión
```
┌──────────────────────────────┐
│ Pendientes de revisión [Salir│
│ Rol: Revisor          [PA 2] │
├──────────────────────────────┤
│ ┌──────────────────────────┐ │
│ │ ⏳ V-0007 · 18/11 10:51   │ │
│ │ Usuario: J. Pérez         │ │
│ │ Motivo: <texto>           │ │
│ └──────────────────────────┘ │
│ ┌──────────────────────────┐ │
│ │ ⏳ V-0009 · 18/11 11:03   │ │
│ └──────────────────────────┘ │
│  (vacío: "No hay coincidencias│
│   pendientes")               │
└──────────────────────────────┘
```
- Las más antiguas primero. Sin badges rojos, sonidos ni notificaciones (E3).
- Vencida (HU-06 E4, provisional ADR-0008, PA 23): a las 24 h sin revisión la coincidencia **sale de esta lista y no se muestra en ninguna parte de REV-01**, porque la captura ya se borró. El supervisor la ve en la bitácora (BIT-01/02). Sin estado "Escalada".

### REV-02 — Revisión
```
┌──────────────────────────────┐
│ ←  Revisar V-0007            │
├──────────────────────────────┤
│ Motivo de la consulta:       │
│ <texto> · J. Pérez · 10:51   │
│ ┌────────────┬─────────────┐ │
│ │  CAPTURA   │ REFERENCIA  │ │
│ │  [imagen]  │  [imagen]   │ │
│ └────────────┴─────────────┘ │
│ Candidato  ‹ 1 de 3 ›        │  ← PA 22 / PA 7 (1:1 = sin selector)
│ [Datos de la referencia PA15]│
│ [Score — por definir  PA 26] │
│                              │
│ Decisión *                   │
│ ( ) Confirmar coincidencia   │
│ ( ) Descartar                │
│ ( ) No concluyente           │
│ Motivo de la decisión *      │
│ [________________________]   │
│ [________________________]   │
│                              │
│  [   GUARDAR DECISIÓN     ]  │
└──────────────────────────────┘
```
- Captura y referencia del mismo tamaño, lado a lado (E1), con el motivo original arriba.
- Las imágenes del prototipo son siluetas o rostros sintéticos. Nunca personas reales.
- Ninguna opción está preseleccionada.

### REV-03 — Falta motivo
```
│ Motivo de la decisión *      │
│ [________________________]   │  ← borde rojo
│ ⚠ Escriba el motivo de su    │
│   decisión.                  │
```
- La decisión no se guarda (E2). Si tampoco eligió una opción: "Elija una decisión".

### REV-04 — Decisión registrada
```
│            ✓                 │
│ Decisión registrada          │
│ V-0007 · Descartar · 11:10   │
│  [ VOLVER A PENDIENTES ]     │
```
- El ✓ confirma que se guardó la acción, no es un resultado sobre la persona.

### VER-01 — Mis verificaciones (agente)
```
│ ←  Mis verificaciones        │
│ ⏳ V-0007 · Pendiente de      │
│    revisión                  │
│ ● V-0005 · Revisada          │
│ ● V-0003 · Revisada          │
│ ⌛ V-0002 · No concluyente —  │
│    verifique por otros medios│  ← PA 23
```
- Solo las verificaciones del propio usuario que terminaron en posible coincidencia.
- Vencida (24 h sin revisión, ADR-0008): el agente ve "No concluyente — verifique por otros medios", con la marca PA 23.

### VER-02 — Detalle
```
│ V-0005 · 18/11 09:30         │
│ Resultado inicial:           │
│ Posible coincidencia —       │
│ requiere revisión            │
│ Revisión: coincidencia       │
│ confirmada por el revisor    │  ← o "descartada" / "no concluyente"
│                     [PA 28]  │
│ 18/11 09:45                  │
│ [Motivo del revisor   PA 27] │
```
- Si sigue pendiente: "Estado: Pendiente de revisión" (E3).
- Si venció: en lugar del resultado de la revisión muestra "No concluyente — verifique por otros medios", con la marca PA 23 (ADR-0008, provisional).
- PA 28: la redacción tras la revisión es provisional y no debe leerse como "identificado".
- PA 27: el motivo del revisor no se muestra al agente hasta que se decida.

## Decisiones de diseño
- Radio + motivo + un solo botón "Guardar". Evita guardar por un toque accidental en botones grandes de decisión.
- "Confirmar coincidencia" en lugar de solo "Confirmar", para que se entienda qué se confirma.

## Elementos no solicitados (aprobados el 2026-11-18)
- VER-01 / VER-02 como ubicación del resultado para el agente.
- Selector de candidatos (solo si PA 7 = lista y PA 22 > 1).
- Mensaje de estado vacío en REV-01.

## Puntos abiertos que afectan el diseño
- PA 2: quién revisa y si es en tiempo real.
- PA 23: vencimiento a las 24 h (provisional, ADR-0008; HU-06 E4). La vencida sale de la lista de pendientes (E4). No aparece en REV-01 (decisión del BA, 2026-11-18). Si el área usuaria pide verlas en la validación, se abre como elemento nuevo.
- PA 2: el PRD lista también las opciones C (autorrevisión en modo operativo con ratificación posterior) y D (central en tiempo real). No se diseñan hasta que el MININTER decida.
- PA 15: datos de la persona de referencia visibles para el revisor.
- PA 22 / PA 7: número de candidatos.
- PA 26: score visible para el revisor (REV-02).
- PA 27: motivo del revisor visible para el agente (VER-02).
- PA 28: redacción de una coincidencia confirmada (VER-02).

## Fuera de alcance respetado
- Acciones automáticas a partir de una coincidencia.
