# HU-03: Consultar si una placa tiene requisitoria

## Historia de usuario
Como usuario autorizado (personal en campo)
Quiero ingresar una placa y el motivo de la consulta, y ver un resultado controlado
Para saber al instante si el vehículo tiene requisitoria

## Contexto
PRD › Alcance — Incluye › Componente 2 › Consulta de placas: "ingreso manual (…), consulta a la fuente habilitada o simulador y visualización controlada del resultado". Trazabilidad: "motivo de consulta" y "gestión de errores" (reglas transversales, validadas aquí como escenarios borde).

## Criterios de aceptación (Gherkin)

### Escenario 1 — Camino feliz
```gherkin
# language: es
Característica: Consulta de placa
  Escenario: Placa con requisitoria en el simulador
    Dado que un usuario en campo inició sesión
    Y que el simulador tiene la placa sintética "ABC-123" con requisitoria vigente
    Cuando ingresa la placa "ABC-123" y el motivo de consulta
    Entonces la app muestra que la placa tiene requisitoria
    Y la consulta queda registrada en la bitácora con usuario, fecha, hora, motivo y resultado
```

### Escenario 2 — Caso borde: sin motivo
```gherkin
  Escenario: El usuario no indica el motivo
    Dado que un usuario en campo ingresó una placa
    Cuando intenta consultar sin indicar el motivo
    Entonces la app no envía la consulta y pide el motivo
```

### Escenario 3 — Caso borde: fuente no disponible
```gherkin
  Escenario: El simulador o la fuente no responde
    Dado que la fuente de placas no responde
    Cuando el usuario envía una consulta válida
    Entonces la app muestra "No se pudo completar la consulta; intente nuevamente"
    Y no muestra "sin requisitoria"
    Y el error queda registrado en la bitácora
```

### Escenario 4 — Caso borde: formato inválido
```gherkin
  Escenario: La placa no tiene un formato válido
    Dado que un usuario ingresa un texto que no corresponde a una placa
    Cuando intenta consultar
    Entonces la app indica que el formato no es válido y no envía la consulta
```

### Escenario 5 — Caso borde: sin requisitoria registrada (agregado tras revisión UX, aprobado el 2026-11-18)
```gherkin
  Escenario: La placa no tiene requisitoria en la fuente consultada
    Dado que el simulador tiene la placa sintética "DEF-456" sin requisitoria
    Cuando el usuario consulta esa placa con motivo
    Entonces la app muestra "Sin requisitoria registrada en la fuente consultada"
    Y no usa colores ni íconos que se lean como "vehículo limpio"
    Y la consulta queda registrada en la bitácora
```

## Supuestos
- (MVP) La consulta va contra un simulador con placas sintéticas (integración real excluida del MVP).
- "ABC-123" es solo un ejemplo de placa sintética.

## Puntos abiertos
- PRD PA #15: ¿qué se muestra en la "visualización controlada": solo con/sin requisitoria, o también datos del propietario y del vehículo?
- ¿Qué formatos de placa debe aceptar la validación (vehículos particulares, motos, placas antiguas, diplomáticas, temporales)?
- ¿El motivo de consulta es texto libre o una lista cerrada de motivos? Si es lista, ¿cuáles?
- PRD PA #4: ¿cuál es el tiempo máximo de respuesta aceptable?

## Fuera de alcance (explícitamente excluido en el PRD)
- Integración con fuentes reales de placas o requisitorias (MVP con simuladores).
