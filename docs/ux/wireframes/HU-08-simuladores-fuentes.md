# Wireframes — HU-08: Consultar fuentes a través de servicios con simuladores

## Proyecto / herramienta
- Herramienta: texto estructurado; prototipo vía `../bolt-prompt.md` (pendiente PA 14)

## Pantallas

HU-08 es técnica y **no tiene pantallas propias para el usuario final**. Sus escenarios se ven así:

| Escenario Gherkin | Cómo se refleja en la UI |
|---|---|
| E1 La app consulta a través del servicio | Sin cambio visible. Los resultados PLA-05/06 y ROS-05/06/07 llegan del servicio. |
| E2 Reemplazo del simulador | Sin cambio visible (es la condición de éxito). |
| E3 Respuesta fuera de contrato | El servicio devuelve un error controlado, que se ve como PLA-07 o ROS-08 y queda en la bitácora (BIT-01, tipo "Error"). |

## Panel de demo (solo prototipo, no es parte del producto)

Botón flotante discreto "⚙ Demo", visible en todas las pantallas. Permite al facilitador de la validación:

```
┌──────────────────────────────┐
│ Panel de demo (prototipo)    │
├──────────────────────────────┤
│ Respuesta de placa           │
│ (•) Según placa sintética    │
│ ( ) Forzar fuente caída      │
│ ( ) Forzar respuesta inválida│
│ Respuesta de rostro          │
│ [Posible coincidencia     ▾] │
│  Calidad: Mire de frente /   │
│  Más luz / Borrosa / Varias  │
│  personas / Sin rostro       │
│  No concluyente / Sin coinc. │
│  / Error                     │
│ Cámara: [Permiso concedido ▾]│
│ OCR:    [Lee ABC-123       ▾]│  (Lee ABC-123 / DEF-456 / Falla)
│ ── Variantes de PA ──        │
│ PA 2  [Revisor separado   ▾] │  (separado / mismo usuario:
│                              │   requiere reabrir ADR-0003)
│ PA 7  [Lista acotada      ▾] │  (lista / 1:1)
│ PA 15 [Solo estado        ▾] │  (solo estado / estado + datos)
│ [ Vencer pendientes (24 h) ] │  PA 23 (ADR-0008)
│ [ ] Mostrar marcas de PA     │
│ [ Cerrar sesión por inactiv.]│
│ [ Bloquear cuenta (5 int.) ] │  PA 19 → AUTH-04
│ [ Desbloquear cuentas      ] │
└──────────────────────────────┘
```

## Elementos no solicitados (aprobados el 2026-11-18)
- El panel de demo completo (herramienta de validación).

## Puntos abiertos
- PA 6, PA 17: fuentes reales y aceptación de simuladores. Sin impacto visual.
