# HU-09: Avisar al 105 (simulado) tras una placa con requisitoria o una coincidencia confirmada

## Historia de usuario
Como usuario autorizado (personal en campo)
Quiero ver, en mi propio celular, el mensaje que se enviaría a la central 105 cuando una placa tiene requisitoria o el revisor confirmó una posible coincidencia facial
Para que el MININTER evalúe cómo sería ese aviso, sin que se envíe nada a una central real

## Contexto
PRD › Alcance — Incluye › Componente 2 › Aviso simulado al 105 (decisión del humano, 2026-11-20): "cuando una placa tiene requisitoria o el revisor confirma una posible coincidencia facial, el usuario puede pulsar 'Avisar al 105 (simulado)'. La app muestra en el mismo celular el mensaje que se enviaría: ubicación del dispositivo, placa o código de requisitoria, nombre (sintético) de la persona con la redacción 'Posible coincidencia — requiere revisión' e ID de la consulta; nunca la foto. No se construye una aplicación del 105 ni se llama ni se envía nada a una central real. El envío nunca es automático y queda en la bitácora. Si no hay permiso de ubicación, el aviso lo dice y no inventa una ubicación." Ver PRD PA #32.

Depende de HU-03 (placa con requisitoria, pantalla PLA-05), HU-06 (decisión "Confirmar" del revisor, que el agente ve en VER-02) y HU-07 (bitácora).

**Estado:** **aprobada por el humano el 2026-11-20**, junto con la propuesta de UX (vista previa con confirmación y fecha y hora en el mensaje). Sigue **sin desarrollo** (sin contrato, código ni pruebas) hasta que el PM lo autorice.

## Criterios de aceptación (Gherkin)

### Escenario 1 — Camino feliz: placa con requisitoria
```gherkin
# language: es
Característica: Aviso simulado al 105
  Escenario: El usuario avisa por una placa con requisitoria
    Dado que un usuario en campo consultó la placa sintética "ABC-123" con su motivo
    Y que la app muestra que la placa tiene requisitoria
    Y que la app tiene permiso de ubicación
    Cuando el usuario pulsa "Avisar al 105 (simulado)"
    Entonces la app muestra en el mismo celular el mensaje que se enviaría, con la ubicación del dispositivo, la placa o el código de requisitoria y el ID de la consulta
    Y la app indica que no se envió nada a ninguna central
    Y no se hace ninguna llamada, mensaje de texto ni envío a una central o servicio del 105
    Y el aviso simulado queda registrado en la bitácora con usuario, fecha, hora e ID de la consulta
```

### Escenario 2 — Camino feliz: coincidencia facial confirmada por el revisor
```gherkin
  Escenario: El usuario avisa por una coincidencia confirmada
    Dado que el revisor eligió "Confirmar" en una posible coincidencia de una consulta del usuario (HU-06)
    Y que el usuario ve esa decisión en el detalle de su verificación
    Cuando pulsa "Avisar al 105 (simulado)"
    Entonces la app muestra el mensaje que se enviaría, con la ubicación del dispositivo, el código de requisitoria, el nombre sintético de la persona con la redacción "Posible coincidencia — requiere revisión" y el ID de la consulta
    Y el mensaje no incluye la captura ni la foto de referencia
    Y en ningún caso usa la palabra "identificado"
    Y no se envía nada a ninguna central
    Y el aviso simulado queda registrado en la bitácora
```

### Escenario 3 — Caso borde: sin permiso de ubicación
```gherkin
  Escenario: La app no tiene permiso de ubicación
    Dado que la placa tiene requisitoria o el revisor confirmó la coincidencia
    Y que la app no tiene permiso de ubicación
    Cuando el usuario pulsa "Avisar al 105 (simulado)"
    Entonces el mensaje dice que la ubicación no está disponible por falta de permiso
    Y no muestra una ubicación aproximada, anterior ni inventada
    Y el resto del mensaje se muestra igual
    Y el aviso simulado queda registrado en la bitácora
```

### Escenario 4 — Caso borde: nunca automático ni fuera de los dos casos
```gherkin
  Escenario: Resultados que no habilitan el aviso
    Dado que el resultado es "Sin requisitoria registrada en la fuente consultada", un error de consulta,
      "Posible coincidencia — requiere revisión" pendiente de revisión, "No concluyente — verifique por otros medios",
      "Sin coincidencia en la lista consultada", una coincidencia descartada o una revisión vencida
    Cuando el usuario ve ese resultado
    Entonces la app no ofrece "Avisar al 105 (simulado)"
    Y no se genera ni se registra ningún aviso
```

### Escenario 5 — Caso borde: el usuario no confirma el aviso
```gherkin
  Escenario: El usuario cancela en la vista previa del mensaje
    Dado que el usuario pulsó "Avisar al 105 (simulado)" y ve la vista previa del mensaje
    Cuando elige "Cancelar"
    Entonces no se registra ningún aviso en la bitácora
    Y vuelve al resultado de su consulta
```

## Supuestos
- El aviso lo pulsa el usuario en campo que hizo la consulta. Para la placa, desde el resultado "tiene requisitoria" (PLA-05); para el rostro, desde el detalle de su verificación ya confirmada (VER-02), no desde ROS-05. Quién más puede pulsarlo es el PA #34.
- Para la placa, el mensaje no lleva nombre de persona: el PRD dice "placa o código de requisitoria", y el nombre aplica a la coincidencia facial.
- Escenario 5 y la vista previa con "Registrar aviso simulado" o "Cancelar" (AVI-01, AVI-02) son una propuesta de UX (2026-11-20). El PRD no pide un paso de confirmación; se adopta porque refuerza "nunca automático". El aviso se registra al confirmar. Elemento no solicitado por el PRD, **aprobado por el humano el 2026-11-20**, igual que la fecha y hora en el mensaje.
- Mientras no se responda el PA #32, la ubicación es la del dispositivo, con permiso, y se muestra solo en el celular (supuesto de trabajo del PRD). Mientras no se responda el PA #34, se muestra como coordenadas: una dirección pediría un servicio externo de geocodificación.
- La redacción del nombre sigue siendo "Posible coincidencia — requiere revisión" aunque el revisor haya confirmado (decisión del 2026-11-20). La redacción de la coincidencia confirmada en sí sigue abierta (PA #28).
- El aviso simulado no cambia el estado de la consulta ni de la revisión.

## Conflictos con otras fuentes (documentados, no resueltos)
- **PA #15 (qué datos muestra el resultado):** el mensaje incluye el código de requisitoria y el nombre sintético, pero el PA #15 sigue sin decidir si el resultado de placa muestra algo más que "con/sin requisitoria", ni qué datos de la persona de referencia se ven. Con datos sintéticos no hay riesgo en el MVP. Si el MININTER responde "solo estado", hay que confirmar si el aviso es la excepción.
- **HU-06, "Fuera de alcance: acciones automáticas a partir de una coincidencia":** no hay choque, porque el aviso es manual y solo aparece después de la decisión humana (regla 4 de `AGENTS.md`).

## Puntos abiertos
- PRD PA #32: ¿el MININTER acepta el aviso simulado en el prototipo, y con qué redacción y datos (ubicación, nombre, código de requisitoria)? ¿Se usa la ubicación GPS del dispositivo (pide un permiso nuevo y es un dato personal del agente) o se ingresa a mano?
- PRD PA #34: (a) En la coincidencia facial, ¿el aviso lo pulsa solo el agente que hizo la consulta o también el revisor que la confirmó? (b) ¿La ubicación se muestra como coordenadas o como dirección? Una dirección requiere un servicio externo de geocodificación. (c) ¿La ubicación se guarda en la bitácora o solo se muestra en el celular? (d) ¿Se puede registrar más de un aviso simulado por la misma consulta? (e) Con la revisión en una cola (PA #2, opción A), la confirmación puede llegar horas después: ¿la ubicación es la del momento en que se pulsa el aviso o la del momento de la captura?
- PRD PA #28: ¿con qué redacción se comunica una coincidencia confirmada, para que no se lea como "identificado"?

## Fuera de alcance (explícitamente excluido en el PRD)
- Una aplicación o central del 105, y cualquier llamada, mensaje o envío real a una central.
- El envío automático del aviso, o cualquier aviso antes de la revisión humana en el caso facial.
- La foto (la captura o la referencia) dentro del aviso.
