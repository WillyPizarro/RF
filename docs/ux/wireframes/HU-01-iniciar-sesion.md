# Wireframes — HU-01: Iniciar sesión y mantener una sesión segura

## Proyecto / herramienta
- Herramienta: texto estructurado; prototipo vía `../bolt-prompt.md` (pendiente PA 14)
- Canal/formato: app móvil Android (referencia, ADR-0010), vertical

## Pantallas

| # | Pantalla / Estado | Escenario Gherkin | ID |
|---|---|---|---|
| 1 | Login | E1 Usuario autorizado inicia sesión | AUTH-01 |
| 2 | Login con error | E2 Credenciales incorrectas | AUTH-02 |
| 3 | Login tras cierre por inactividad | E3 La sesión vence por inactividad | AUTH-03 |
| 4 | Cuenta bloqueada temporalmente | E4 Demasiados intentos fallidos (provisional ADR-0011, PA 19) | AUTH-04 |

### AUTH-01 — Login
```
┌──────────────────────────────┐
│ DATOS SINTÉTICOS · PROTOTIPO │
├──────────────────────────────┤
│                              │
│        Movil Buscador        │
│   Acceso solo para personal  │
│          autorizado          │
│                              │
│  Usuario                     │
│  [________________________]  │
│  Clave                       │
│  [________________________]  │
│                              │
│  [        INGRESAR        ]  │
│                              │
└──────────────────────────────┘
```
- Al ingresar, va al inicio de su rol (HOME-01, REV-01 o BIT-01, ver HU-02).
- El inicio de sesión se registra en la bitácora (lo hace el backend; no se ve en pantalla).
- Sin "¿Olvidó su clave?" ni "Recordarme": la HU no los pide.

### AUTH-02 — Usuario o clave incorrectos
```
│  ┌────────────────────────┐  │
│  │ ⚠ Usuario o clave      │  │
│  │   incorrectos          │  │
│  └────────────────────────┘  │
│  Usuario                     │
│  [jperez__________________]  │
│  Clave                       │
│  [________________________]  │  ← clave vaciada
│  [        INGRESAR        ]  │
```
- El mensaje es único y no dice cuál de los dos campos falló (E2).
- El usuario queda escrito; la clave se borra.
- No muestra cuántos intentos quedan antes del bloqueo (no pedido). Al quinto fallo seguido se pasa a AUTH-04.

### AUTH-03 — Sesión cerrada por inactividad
```
│  ┌────────────────────────┐  │
│  │ ⓘ Su sesión se cerró   │  │
│  │   por inactividad.     │  │
│  │   Ingrese de nuevo.    │  │
│  └────────────────────────┘  │
│  Usuario  [______________]   │
│  Clave    [______________]   │
│  [        INGRESAR        ]  │
│        [PA 18 — tiempo]      │
```
- Al vencer la sesión, la app descarta la pantalla en la que estaba (resultado, formulario, captura) y no la muestra al volver (E3). El botón "atrás" no regresa a ella.
- Sin cuenta regresiva previa (no pedida).

### AUTH-04 — Cuenta bloqueada temporalmente
```
│  ┌────────────────────────┐  │
│  │ 🔒 Cuenta bloqueada     │  │
│  │   temporalmente.       │  │
│  │   Podrá volver a       │  │
│  │   intentar a las 10:57 │  │
│  │   (en 15 min).         │  │
│  └────────────────────────┘  │
│                    [PA 19]   │
│  Usuario                     │
│  [jperez__________________]  │
│  Clave                       │
│  [________________________]  │
│  [        INGRESAR        ]  │
```
- Provisional (ADR-0011 / PA 19): 5 intentos fallidos seguidos → bloqueo de 15 min. Los valores son configurables.
- Muestra la **hora exacta** en la que podrá volver a intentar y, entre paréntesis, los minutos que faltan.
- **No indica si la clave era correcta** (E4): mientras dure el bloqueo, cualquier intento, con clave correcta o incorrecta, muestra este mismo mensaje y deja la clave vacía.
- "Ingresar" sigue activo, para no dar pistas visuales distintas según la clave. Cada intento repite el mensaje.
- No dice cuántos intentos causaron el bloqueo ni ofrece "desbloquear" o "contactar a…" (no está definido).
- El bloqueo queda en la bitácora (backend).
- Tono de advertencia (ámbar), no de error rojo: no es un fallo del usuario en este intento.

## Decisiones de diseño
- Mensaje de cierre informativo (azul), no de error, para que no parezca una falla.
- Al volver a ingresar se va al inicio del rol, no a la pantalla anterior (E3: "ninguna consulta previa queda visible").

## Elementos no solicitados (aprobados el 2026-11-18)
- Franja "DATOS SINTÉTICOS · PROTOTIPO".
- "Cerrar sesión" en los inicios por rol (HU-02).

## Puntos abiertos que afectan el diseño
- PA 18: tiempo de inactividad.
- PA 19: 5 intentos / 15 min, provisional (ADR-0011). Si cambian, solo cambia la configuración; el texto de AUTH-04 usa la hora calculada.
- Observación para ARCH: si el backend responde "bloqueada" solo para usuarios que existen, la pantalla revela qué usuarios existen. Conviene que la respuesta no permita distinguirlo (sin impacto visual).
- PA 3: origen de las identidades en producción (no cambia el login del MVP).

## Fuera de alcance respetado
- Integración con el directorio institucional, 2FA y gestión de dispositivos.
