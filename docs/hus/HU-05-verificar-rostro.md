# HU-05: Verificar un rostro y recibir posibles coincidencias

## Historia de usuario
Como usuario autorizado (personal en campo)
Quiero capturar el rostro de una persona, con el motivo de la consulta, y recibir un resultado prudente
Para saber si debe revisarse una posible coincidencia con una persona con requisitoria

## Contexto
PRD › Alcance — Incluye › Componente 2 › Verificación biométrica facial: "captura del rostro con control de calidad, verificación contra (…) datos sintéticos de prueba y presentación de coincidencias para revisión humana". Componente 1: "manejo de resultados no concluyentes y prevención de falsos positivos".
Skill de referencia para el DEV/TESTER: `especialista-biometria`.

## Criterios de aceptación (Gherkin)

### Escenario 1 — Camino feliz
```gherkin
# language: es
Característica: Verificación facial
  Escenario: Captura válida con posible coincidencia
    Dado que un usuario en campo inició sesión e indicó el motivo de consulta
    Y que la galería de prueba contiene a la persona fotografiada
    Cuando captura un rostro que pasa el control de calidad
    Entonces la app muestra "Posible coincidencia — requiere revisión"
    Y en ningún caso muestra la palabra "identificado"
    Y la consulta queda registrada en la bitácora y enviada a revisión humana (HU-06)
```

### Escenario 2 — Caso borde: mala calidad
```gherkin
  Escenario: La captura no pasa el control de calidad
    Dado que la foto está borrosa, oscura, de perfil o con más de un rostro
    Cuando el usuario captura
    Entonces la app indica el motivo (por ejemplo "Mire de frente" o "Más luz") y pide repetir
    Y la captura no se envía a comparar
```

### Escenario 3 — Caso borde: no concluyente
```gherkin
  Escenario: El resultado queda en la banda intermedia
    Dado que la similitud está entre el umbral bajo y el umbral alto
    Cuando la app recibe el resultado
    Entonces muestra "No concluyente — verifique por otros medios"
```

### Escenario 4 — Caso borde: sin coincidencia
```gherkin
  Escenario: No hay coincidencia en la lista consultada
    Dado que la persona no está en la galería de prueba
    Cuando se compara una captura válida
    Entonces la app muestra "Sin coincidencia en la lista consultada"
    Y no muestra "persona sin requisitoria"
```

### Escenario 5 — Caso borde: error del servicio (agregado tras revisión UX, aprobado el 2026-11-18)
```gherkin
  Escenario: El servicio de comparación no responde
    Dado que el servicio de comparación facial no responde
    Cuando el usuario envía una captura válida con motivo
    Entonces la app muestra "No se pudo completar la verificación; intente nuevamente"
    Y no muestra ninguno de los tres resultados faciales
    Y el error queda registrado en la bitácora
```

### Escenario 6 — Caso borde: sin permiso de cámara (agregado a pedido de UX vía PM; aprobado el 2026-11-19)
```gherkin
  Escenario: El usuario negó el permiso de cámara
    Dado que un usuario en campo indicó el motivo de consulta
    Y que la app no tiene permiso de cámara
    Cuando continúa a la captura del rostro
    Entonces la app explica que sin permiso de cámara no se puede verificar el rostro y cómo dar el permiso
    Y no ofrece cargar una foto de la galería ni otra vía de captura
    Y no se envía nada a comparar
    Y no muestra ninguno de los tres resultados faciales ni "persona sin requisitoria"
    Y no se registra ninguna comparación en la bitácora
```

### Escenario 7 — Caso borde: permiso de cámara retirado (aprobado el 2026-11-19)
```gherkin
  Escenario: El permiso de cámara se retiró después de haberlo concedido
    Dado que el usuario había concedido el permiso de cámara
    Y que lo retiró desde los ajustes del teléfono antes de capturar el rostro
    Cuando vuelve a la captura del rostro
    Entonces la app muestra la misma explicación del Escenario 6
    Y no se envía nada a comparar
    Y no muestra ninguno de los tres resultados faciales ni "persona sin requisitoria"
    Y no se registra ninguna comparación en la bitácora
```

## Supuestos
- (MVP) Galería de referencia con fotos del equipo con consentimiento firmado o rostros sintéticos.
- Regla precisada por ADR-0008 (aprobado 2026-11-18): la captura se borra tras la comparación **o tras la revisión humana**. Si el resultado no es candidato, nunca se escribe en disco. Si es candidato, se guarda cifrada hasta la decisión del revisor o un máximo de 24 h, lo que ocurra primero. En la bitácora solo queda su identificador y el registro de su eliminación.
- El score no se muestra al usuario en campo; sí se guarda en la bitácora.
- Escenarios 6 y 7: a diferencia de la placa (HU-04 E3), el rostro no tiene vía alternativa. No hay ingreso manual equivalente, y la foto de galería no figura en el PRD (solo dice "captura del rostro") y el wireframe ROS-02 la excluye. Sin permiso no hay captura, y sin captura no hay comparación ni resultado (reglas 3 y 7 de `AGENTS.md`).
- Escenario 7 cubre el retiro del permiso **antes** de capturar. Si la captura ya se tomó y se envió, la comparación sigue su curso normal (escenarios 1 a 5).

## Puntos abiertos
- PRD PA #7: ¿la verificación es 1:1 (confirmar identidad declarada) o contra una lista acotada de personas requisitoriadas? Si es lista, ¿quién la define y de qué tamaño es? (cambia la pantalla y el flujo)
- PRD PA #4: ¿cuál es la tasa máxima aceptable de falsas coincidencias y de falsos rechazos?
- PRD PA #16: ¿se debe conservar alguna imagen del rostro? Si es así, ¿cuánto tiempo y quién autoriza su eliminación?
- ¿Cuántos candidatos como máximo se muestran en una posible coincidencia? (la skill sugiere 3; requiere confirmación)
- PRD PA #29 (escenarios 6 y 7): ¿Se registra en la bitácora un intento de verificación facial que no llegó a la captura por falta de permiso de cámara? Si se registra, ¿con qué datos (usuario, fecha, hora, motivo indicado) y qué figura como resultado (p. ej. "sin permiso de cámara — no se capturó")? El PRD pide registrar "motivo de consulta y resultado" y "gestión de errores", pero no dice si un intento sin captura cuenta como consulta. Mientras no se responda, lo único firme es que no se registra como comparación.
- PRD PA #30 (escenarios 6 y 7): Si el usuario da el permiso desde los ajustes y vuelve a la app, ¿se conserva el motivo que ya indicó o debe indicarlo de nuevo?

## Fuera de alcance (explícitamente excluido en el PRD)
- Identificación masiva por reconocimiento facial.
- Vigilancia indiscriminada (comparación sobre video continuo o sin motivo).
- Comparación contra fuentes biométricas reales (MVP con datos de prueba).
