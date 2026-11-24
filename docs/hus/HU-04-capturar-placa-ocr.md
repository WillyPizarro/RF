# HU-04: Capturar la placa con la cámara

## Historia de usuario
Como usuario autorizado (personal en campo)
Quiero apuntar la cámara a una placa y que la app la lea por mí
Para consultar más rápido y sin errores de digitación

## Contexto
PRD › Alcance — Incluye › Componente 2 › Consulta de placas: "captura de la placa con la cámara del dispositivo (OCR)". La consulta posterior sigue las reglas de HU-03.

## Criterios de aceptación (Gherkin)

### Escenario 1 — Camino feliz
```gherkin
# language: es
Característica: Lectura de placa por cámara
  Escenario: La cámara lee la placa y el usuario confirma
    Dado que un usuario en campo abrió la captura de placa
    Cuando apunta la cámara a una placa legible
    Entonces la app muestra el texto leído en un campo editable
    Y el usuario confirma o corrige la placa antes de consultar
```

### Escenario 2 — Caso borde: lectura fallida
```gherkin
  Escenario: La placa no se puede leer
    Dado que la placa está sucia, en ángulo o con poca luz
    Cuando la app no logra leerla
    Entonces la app ofrece reintentar o pasar al ingreso manual
    Y no envía ninguna consulta automática
```

### Escenario 3 — Caso borde: sin permiso de cámara
```gherkin
  Escenario: El usuario negó el permiso de cámara
    Dado que la app no tiene permiso de cámara
    Cuando el usuario elige capturar la placa
    Entonces la app explica cómo dar el permiso y ofrece el ingreso manual
```

### Escenario 4 — Aviso de datos técnicos de ML Kit (opción A del humano, 2026-11-20; propuesto por BA y UX; aprobado por el humano, 2026-11-20)
```gherkin
  Escenario: Primera lectura de placa en la sesión
    Dado que un usuario en campo inició sesión y la app tiene permiso de cámara
    Y que en esta sesión todavía no tocó "Entendido" en el aviso de datos técnicos
    Cuando abre la lectura de placa
    Entonces la app muestra el aviso "Antes de leer la placa" sobre el visor
    Y "Capturar" no funciona hasta que toque "Entendido"
    Y "Ingresar manualmente" sigue disponible
    Y la app no guarda en el teléfono que el aviso fue visto

  Escenario: El aviso ya se vio en la sesión
    Dado que en esta sesión el usuario ya tocó "Entendido"
    Cuando vuelve a abrir la lectura de placa
    Entonces la app no muestra el aviso
    Y al iniciar una nueva sesión lo vuelve a mostrar
```
El texto del aviso y el detalle para la guía de probadores están en `anexos/HU-04-aviso-telemetria-mlkit.md`. Si el usuario sale del aviso con "atrás" sin tocar "Entendido", el aviso se muestra de nuevo la próxima vez. No aparece en la pantalla sin permiso (Escenario 3), porque ahí no se lee nada.

## Supuestos
- La lectura se hace en el dispositivo; la foto de la placa no se guarda (minimización del enfoque MVP).
- Nunca se consulta sin que el usuario confirme el texto leído.
- (2026-11-20) Según Google, ML Kit procesa la foto en el teléfono y no envía a Google ni la foto ni el texto leído, pero sí envía métricas técnicas y un código por instalación. No hay opción oficial para apagarlo (evaluación ARCH). El equipo no lo verificó con tráfico de red.

## Puntos abiertos
- PRD PA #4: ¿qué precisión mínima de lectura se exige y en qué condiciones se mide (día/noche, distancia)?
- PRD PA #16: ¿se debe conservar la imagen de la placa? Si es así, ¿cuánto tiempo?
- PRD PA #12: ¿qué dispositivos se usarán (afecta la calidad de cámara)?
- ~~Validación legal del texto del aviso~~ — resuelto por el humano (vía PM, 2026-11-20): queda como brecha de producción en `docs/contratos/PENDIENTES.md`.
- ~~Constancia de "Entendido"~~ — resuelto por el humano (vía PM, 2026-11-20): en el MVP no se guarda en la bitácora; se decide en producción junto con la validación legal.

## Fuera de alcance (explícitamente excluido en el PRD)
- Lectura continua de placas sin acción del usuario (sería vigilancia indiscriminada).
