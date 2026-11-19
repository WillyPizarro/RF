# HU-01: Iniciar sesión y mantener una sesión segura

## Historia de usuario
Como usuario autorizado (personal en campo)
Quiero iniciar sesión en la app con mis credenciales y que mi sesión se cierre cuando corresponda
Para que solo personal autorizado pueda consultar placas y rostros desde el dispositivo

## Contexto
PRD › Alcance — Incluye › Componente 2 › Seguridad y acceso: "autenticación de usuarios autorizados (…) y gestión de sesiones". Enfoque MVP: inicio de sesión con usuario y clave en versión mínima.
Criterio de éxito: "Los cinco módulos del prototipo funcional operan con data sintética".

## Criterios de aceptación (Gherkin)

### Escenario 1 — Camino feliz
```gherkin
# language: es
Característica: Inicio de sesión
  Escenario: Usuario autorizado inicia sesión
    Dado que existe un usuario sintético activo con rol asignado
    Cuando ingresa su usuario y clave correctos
    Entonces accede a la pantalla principal de su rol
    Y el inicio de sesión queda registrado en la bitácora con usuario, fecha y hora
```

### Escenario 2 — Caso borde: credenciales inválidas
```gherkin
  Escenario: Credenciales incorrectas
    Dado que un usuario ingresa una clave incorrecta
    Cuando intenta iniciar sesión
    Entonces la app muestra "Usuario o clave incorrectos" sin indicar cuál de los dos falló
    Y el intento fallido queda registrado en la bitácora
```

### Escenario 3 — Caso borde: sesión expirada
```gherkin
  Escenario: La sesión vence por inactividad
    Dado que un usuario tiene una sesión abierta
    Cuando pasa el tiempo máximo de inactividad definido
    Entonces la app cierra la sesión y pide credenciales de nuevo
    Y ninguna consulta previa queda visible en pantalla
```

### Escenario 4 — Caso borde: cuenta bloqueada (provisional por ADR-0011 / PA #19; aprobado el 2026-11-18)
```gherkin
  Escenario: Demasiados intentos fallidos
    Dado que un usuario falló el inicio de sesión 5 veces seguidas
    Cuando intenta iniciar sesión otra vez, aunque la clave sea correcta
    Entonces la app muestra que la cuenta está bloqueada temporalmente y cuándo podrá volver a intentar
    Y no indica si la clave era correcta
    Y el bloqueo queda registrado en la bitácora
```

## Supuestos
- (MVP) Autenticación con usuario y clave; sin integración con el directorio institucional (excluida del MVP en el PRD).
- (MVP) Usuarios sintéticos creados por el equipo para pruebas.

## Puntos abiertos
- ¿Cuál es el tiempo máximo de inactividad antes de cerrar la sesión? (relacionado con PRD PA #4)
- ¿Cuántos intentos fallidos se permiten antes de bloquear temporalmente la cuenta, y por cuánto tiempo?
- PRD PA #3: ¿la gestión de identidades vendrá de un sistema institucional existente en producción?

## Fuera de alcance (explícitamente excluido en el PRD)
- Integración con el directorio institucional y políticas de seguridad avanzadas (se documentan, no se construyen).
