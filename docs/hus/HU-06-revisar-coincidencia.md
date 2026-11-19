# HU-06: Revisar una posible coincidencia facial

## Historia de usuario
Como revisor humano de coincidencias
Quiero comparar lado a lado la captura con la referencia y registrar mi decisión con un motivo
Para que ninguna coincidencia del sistema se tome como identificación sin una persona que la valide

## Contexto
PRD › Alcance — Incluye › Componente 2 › Verificación biométrica facial: "presentación de coincidencias para revisión humana". Componente 1: "revisión humana de coincidencias (…) y prevención de falsos positivos". Enfoque MVP: "pantalla de revisión humana de coincidencias" se construye.

## Criterios de aceptación (Gherkin)

### Escenario 1 — Camino feliz
```gherkin
# language: es
Característica: Revisión humana de coincidencias
  Escenario: El revisor confirma una coincidencia
    Dado que existe una posible coincidencia pendiente de revisión
    Cuando el revisor la abre
    Entonces ve la captura y la foto de referencia lado a lado, con el motivo de la consulta original
    Cuando elige "Confirmar" y escribe el motivo de su decisión
    Entonces la decisión queda registrada en la bitácora con revisor, fecha, hora y motivo
    Y el usuario en campo ve el resultado de la revisión
```

### Escenario 2 — Caso borde: decisión sin motivo
```gherkin
  Escenario: El revisor intenta decidir sin motivo
    Dado que el revisor abrió una coincidencia pendiente
    Cuando elige "Confirmar", "Descartar" o "No concluyente" sin escribir el motivo
    Entonces la app no guarda la decisión y pide el motivo
```

### Escenario 3 — Caso borde: nada automático antes de revisar
```gherkin
  Escenario: Coincidencia aún sin revisar
    Dado que una posible coincidencia está pendiente
    Cuando nadie la ha revisado
    Entonces el sistema no dispara ninguna alerta ni acción automática
    Y el usuario en campo ve el estado "Pendiente de revisión"
```

### Escenario 4 — Caso borde: revisión vencida (provisional por ADR-0008 / PA #23; aprobado el 2026-11-18)
```gherkin
  Escenario: Nadie revisa la coincidencia en 24 horas
    Dado que una posible coincidencia lleva 24 horas pendiente de revisión
    Cuando se cumple el plazo
    Entonces la revisión pasa al estado "Vencida" y sale de la cola del revisor
    Y el agente ve "No concluyente — verifique por otros medios"
    Y la captura se borra y su eliminación queda registrada en la bitácora
```

## Supuestos
- (ADR-0008) La captura de un candidato se conserva cifrada solo hasta la decisión del revisor o 24 h; después se borra y el borrado queda en la bitácora.
- (ADR-0003, provisional mientras no se responda el PA #2) El revisor es un rol distinto del agente, y nadie decide sobre su propia consulta.
- (ADR-0008, provisional mientras no se responda el PA #23) Si pasan 24 h sin revisión, la revisión pasa a "vencida" y el agente ve "No concluyente — verifique por otros medios".
- Las opciones de decisión son Confirmar, Descartar y No concluyente (tomadas de la skill `especialista-biometria`, pendientes de validación con el área usuaria).

## Puntos abiertos
- PRD PA #2: ¿el revisor es el mismo usuario en campo, un supervisor o una central? ¿Debe revisar en tiempo real? (si es el mismo usuario, esta HU se fusiona con HU-05)
- ¿Qué pasa si una coincidencia no se revisa en un tiempo determinado? ¿Vence, escala o queda pendiente?
- PRD PA #15 (aplicado a personas): ¿qué datos de la persona de referencia puede ver el revisor?

## Fuera de alcance (explícitamente excluido en el PRD)
- Acciones automáticas a partir de una coincidencia (no estaban en el alcance).
