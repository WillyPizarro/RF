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

## Supuestos
- La lectura se hace en el dispositivo; la foto de la placa no se guarda (minimización del enfoque MVP).
- Nunca se consulta sin que el usuario confirme el texto leído.

## Puntos abiertos
- PRD PA #4: ¿qué precisión mínima de lectura se exige y en qué condiciones se mide (día/noche, distancia)?
- PRD PA #16: ¿se debe conservar la imagen de la placa? Si es así, ¿cuánto tiempo?
- PRD PA #12: ¿qué dispositivos se usarán (afecta la calidad de cámara)?

## Fuera de alcance (explícitamente excluido en el PRD)
- Lectura continua de placas sin acción del usuario (sería vigilancia indiscriminada).
