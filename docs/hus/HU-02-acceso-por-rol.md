# HU-02: Acceder solo a las funciones de mi rol

## Historia de usuario
Como responsable del servicio en el MININTER
Quiero que cada usuario vea y use solo las funciones permitidas para su rol
Para que nadie consulte o revise información que no le corresponde

## Contexto
PRD › Alcance — Incluye › Componente 2 › Seguridad y acceso: "control de acceso por roles". Componente 1: "perfiles de acceso". Enfoque MVP: "2 o 3 roles" en versión mínima.

## Criterios de aceptación (Gherkin)

### Escenario 1 — Camino feliz
```gherkin
# language: es
Característica: Control de acceso por rol
  Escenario: El usuario en campo ve solo sus funciones
    Dado que un usuario con rol "usuario en campo" inició sesión
    Cuando abre el menú principal
    Entonces ve las opciones "Consultar placa" y "Verificar rostro"
    Y no ve las opciones reservadas a otros roles
```

### Escenario 2 — Caso borde: acceso directo no autorizado
```gherkin
  Escenario: Intento de usar una función de otro rol
    Dado que un usuario sin permiso de revisión inició sesión
    Cuando intenta abrir la revisión de coincidencias por un enlace o llamada directa al servicio
    Entonces el servicio rechaza la solicitud
    Y el intento queda registrado en la bitácora
```

## Supuestos
- (Conflicto C1, ver índice) Para cumplir el alcance mínimo, los roles se asignan a usuarios sintéticos en la carga inicial de datos; no se construye pantalla de administración de usuarios hasta que se confirme el PA #3.
- El control se aplica en el servicio (backend), no solo ocultando botones en la app.

## Puntos abiertos
- PRD PA #9: ¿qué perfiles de acceso debe tener el prototipo además del usuario en campo?
- PRD PA #2: ¿el revisor de coincidencias es un rol distinto del usuario en campo?
- PRD PA #3: ¿existe un rol de administrador que cree usuarios y asigne roles dentro del prototipo?

## Fuera de alcance (explícitamente excluido en el PRD)
- Integración con el directorio institucional (se documenta, no se construye).
