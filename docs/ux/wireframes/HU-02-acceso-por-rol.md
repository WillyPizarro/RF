# Wireframes — HU-02: Acceder solo a las funciones de mi rol

## Proyecto / herramienta
- Herramienta: texto estructurado; prototipo vía `../bolt-prompt.md` (pendiente PA 14)
- Canal/formato: app móvil Android (referencia, ADR-0010), vertical

## Pantallas

| # | Pantalla / Estado | Escenario Gherkin | ID |
|---|---|---|---|
| 1 | Inicio del agente | E1 El usuario en campo ve solo sus funciones | HOME-01 |
| 2 | Acceso no autorizado | E2 Intento de usar una función de otro rol | ERR-01 |

Los inicios de los otros roles son pantallas de otras HUs: el revisor entra a REV-01 (HU-06, PA 2) y el supervisor a BIT-01 (HU-07, PA 24). Los tres roles (agente, revisor, supervisor) salen de ADR-0003.

### HOME-01 — Inicio agente
```
┌──────────────────────────────┐
│ DATOS SINTÉTICOS · PROTOTIPO │
├──────────────────────────────┤
│ Hola, J. Pérez     [Salir]   │
│ Rol: Agente        │
│                              │
│ ┌──────────────────────────┐ │
│ │  🚗  CONSULTAR PLACA     │ │
│ └──────────────────────────┘ │
│ ┌──────────────────────────┐ │
│ │  👤  VERIFICAR ROSTRO    │ │
│ └──────────────────────────┘ │
│                              │
│  Mis verificaciones (1 pend.)│  ← enlace secundario
└──────────────────────────────┘
```
- Solo aparecen "Consultar placa" y "Verificar rostro" como funciones principales (E1). No hay botones de revisión ni de bitácora.
- "Mis verificaciones" es un enlace secundario, no una función de otro rol: lo exige HU-06 (el agente ve el resultado). Aprobado el 2026-11-18.
- En la **variante B de PA 2** (el agente revisa) no se agrega nada aquí: la revisión se abre desde ROS-05. Esa variante **requiere reabrir ADR-0003**.

### ERR-01 — Acceso no autorizado
```
│                              │
│            ⛔                │
│   No tiene permiso para      │
│   usar esta función.         │
│                              │
│   El intento quedó           │
│   registrado.                │
│                              │
│  [    VOLVER AL INICIO    ]  │
```
- Se muestra cuando el servicio responde "no autorizado" a un enlace o llamada directa (E2). El control real está en el backend (supuesto de HU-02).
- No dice qué rol haría falta ni a quién pedir acceso (no está definido).

## Decisiones de diseño
- Dos botones grandes a todo el ancho, pensados para uso en la calle, con guantes o al sol.
- Nombre y rol visibles en el encabezado, para que el usuario sepa con qué perfil está operando.

## Elementos no solicitados (aprobados el 2026-11-18)
- Enlace "Mis verificaciones" (justificado por HU-06).
- Botón "Salir" (cierre manual de sesión).
- Texto "El intento quedó registrado" en ERR-01.

## Puntos abiertos que afectan el diseño
- PA 9: resuelto por ADR-0003 (agente, revisor y supervisor; un solo rol por usuario).
- PA 2: si el revisor es el mismo agente, el rol "revisor" desaparece y hay que reabrir ADR-0003.
- PA 3: sin pantalla de administración (conflicto C1).

## Fuera de alcance respetado
- Administración de usuarios y roles; directorio institucional.
