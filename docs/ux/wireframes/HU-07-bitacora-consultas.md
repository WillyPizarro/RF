# Wireframes — HU-07: Registrar cada consulta en una bitácora

## Proyecto / herramienta
- Herramienta: texto estructurado; prototipo vía `../bolt-prompt.md` (pendiente PA 14)
- Canal/formato: app móvil Android (referencia, ADR-0010), vertical. **Si se ve en app o en web está pendiente (PA 24).**

## Pantallas

| # | Pantalla / Estado | Escenario Gherkin | ID |
|---|---|---|---|
| 1 | Bitácora (lista, solo lectura) | E1 Una consulta queda registrada; E2 (sin controles de edición) | BIT-01 |
| 2 | Detalle de registro | E3 Datos sensibles; E2 | BIT-02 |

E1 y E2 se cumplen sobre todo en el backend: la bitácora solo admite inserciones. La UI acompaña sin ofrecer controles para editar o borrar.

### BIT-01 — Bitácora
```
┌──────────────────────────────┐
│ Bitácora               [Salir│
│ Rol: Supervisor      [PA 24] │
├──────────────────────────────┤
│ ┌ - - - - - - - - - - - - -┐ │
│ │ Filtros [PA 24]          │ │
│ │ [Fecha ▾][Usuario ▾][Tipo▾│ │
│ └ - - - - - - - - - - - - -┘ │
│ 18/11 11:10 · revisor1       │
│  Revisión · V-0007 · Descart.│
│ 18/11 10:51 · jperez         │
│  Rostro · Motivo… · Posible  │
│  coincidencia                │
│ 18/11 10:42 · jperez         │
│  Placa ABC-123 · Motivo… ·   │
│  Tiene requisitoria          │
│ 18/11 10:40 · jperez         │
│  Inicio de sesión            │
│ 18/11 10:39 · jperez         │
│  Intento fallido             │
│ 18/11 10:35 · jperez         │
│  Acceso denegado · Revisión  │
│ 18/11 10:30 · sistema        │
│  Error · Fuente de placas    │
│ 18/11 09:12 · sistema        │
│  Revisión vencida · V-0002 · │
│  24 h sin revisión  [PA 23]  │
│ 18/11 09:12 · sistema        │
│  Captura eliminada · V-0002 ·│
│  causa: vencimiento 24 h     │
│ [SINTÉTICO] en cada registro │
└──────────────────────────────┘
```
- Tipos que se ven en el prototipo: inicio de sesión, intento fallido, cuenta bloqueada, consulta de placa, verificación de rostro, decisión de revisión, revisión vencida, captura eliminada (`CAPTURA_ELIMINADA`, ADR-0008, con su causa: decisión del revisor o vencimiento de 24 h), acceso denegado, error.
- Las revisiones vencidas solo se ven aquí (HU-06 E4: salen de la cola del revisor). Llevan la marca PA 23.
- Sin botones de editar, borrar ni exportar.

### BIT-02 — Detalle
```
│ ←  Registro #000123          │
│ 🔒 Registro de solo lectura   │
│ Usuario: jperez              │
│ Fecha y hora: 18/11/2026     │
│   10:51:22                   │
│ Tipo: Verificación de rostro │
│ Motivo: <texto>              │
│ Resultado: Posible           │
│   coincidencia               │
│ ID de captura: CAP-7f3a…     │
│ Score: 0.71                  │
│ Imagen: no almacenada        │
│ Origen: datos sintéticos     │
```
- E3: se ven el ID de captura y el score. La imagen nunca aparece.
- En un registro de placa no hay ID de captura ni score.

## Decisiones de diseño
- Lista cronológica inversa con una tarjeta por registro, legible en el teléfono.
- El candado y el texto "solo lectura" hacen visible la regla de E2.

## Elementos no solicitados (aprobados el 2026-11-18)
- Toda la pantalla de consulta: HU-07 define qué se registra, no quién lo consulta (PA 24). Se diseñó porque el encargo pide "bitácora" en el prototipo navegable.
- Filtros (marcados PA 24).

## Puntos abiertos que afectan el diseño
- PA 24: quién la consulta, desde dónde y con qué filtros.
- PA 9: resuelto por ADR-0003 (rol supervisor).
- PA 16: tiempo de conservación. Sin UI.

## Fuera de alcance respetado
- Firma y sellado de tiempo; exportación.
