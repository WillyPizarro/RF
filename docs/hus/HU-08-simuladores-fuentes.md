# HU-08: Consultar fuentes a través de servicios con simuladores documentados

## Historia de usuario
Como área técnica del MININTER
Quiero que la app consulte las fuentes a través de servicios con un contrato documentado, respaldados por simuladores
Para poder reemplazar después cada simulador por la fuente real sin rehacer la app

## Contexto
PRD › Alcance — Incluye › Componente 2 › Servicios e interoperabilidad: "servicios de consulta e integración con las fuentes autorizadas; simuladores documentados cuando no existan autorizaciones o ambientes". Componente 1: "matriz de fuentes de datos e interoperabilidad".
Conflicto C3 (ver índice): el alcance incluye integración con fuentes autorizadas, pero el MVP excluye la integración real.

## Criterios de aceptación (Gherkin)

### Escenario 1 — Camino feliz
```gherkin
# language: es
Característica: Servicios de consulta con simuladores
  Escenario: La app consulta a través del servicio
    Dado que el simulador de placas está activo con datos sintéticos
    Cuando la app hace una consulta de placa
    Entonces la respuesta llega por el servicio de consulta, con el formato definido en su contrato documentado
    Y la app no se conecta directo al simulador
```

### Escenario 2 — Caso borde: reemplazo del simulador
```gherkin
  Escenario: Se cambia el simulador por otra implementación
    Dado que existe una segunda implementación que cumple el mismo contrato
    Cuando se configura el servicio para usarla
    Entonces la app funciona sin cambios de código
```

### Escenario 3 — Caso borde: respuesta inválida
```gherkin
  Escenario: El simulador devuelve una respuesta fuera de contrato
    Dado que el simulador devuelve datos incompletos o con formato inválido
    Cuando el servicio los recibe
    Entonces el servicio responde un error controlado
    Y el error queda registrado en la bitácora
```

## Supuestos
- (MVP) Un simulador por cada fuente que el prototipo necesite (placas, requisitorias, galería biométrica), con datos sintéticos.
- Cada simulador tiene su contrato documentado (campos, errores, ejemplos), que se entrega al cierre.

## Puntos abiertos
- PRD PA #6: ¿qué fuentes concretas debe representar cada simulador, y alguna tiene convenio vigente?
- ¿Qué campos devuelve hoy cada fuente real? (pedido al MININTER: "campos que muestra hoy una consulta de requisitoria")
- PRD PA #17: ¿el MININTER acepta por escrito que el MVP se valide solo con simuladores?

## Fuera de alcance (explícitamente excluido en el PRD)
- Integración con fuentes reales en el MVP.
