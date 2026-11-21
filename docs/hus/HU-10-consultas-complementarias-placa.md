# HU-10: Consultar datos del vehículo y papeletas de una placa (simulado)

## Historia de usuario
Como usuario autorizado (personal en campo)
Quiero pedir, después del resultado de requisitoria, los datos registrados del vehículo y sus papeletas
Para comparar el vehículo que tengo delante con lo registrado y decidir por mí mismo si algo no coincide

## Contexto
PRD › Alcance — Incluye › Componente 2 › Consultas complementarias de placa, simuladas (decisión del humano, 2026-11-20): "después del resultado de requisitoria, el usuario puede pedir, una por una, 'Datos del vehículo (SUNARP, simulado)' —marca, modelo, color, año y estado registral, sin nombre ni DNI del propietario— y 'Papeletas (SAT Lima, simulado)' —cantidad, monto pendiente y si hay alguna grave; cubre solo Lima—. La app nunca concluye 'placa clonada': muestra las características registradas para que el usuario las compare con el vehículo y, si no coinciden, él marca 'No coincide con lo registrado'. Cada consulta y esa marca quedan en la bitácora con el mismo motivo. Un error de la fuente nunca se muestra como 'sin papeletas' ni 'sin observaciones'." Ver PRD PA #35.

Depende de HU-03 (resultado de requisitoria y motivo), HU-07 (bitácora) y HU-08 (servicios con simuladores). OSIGP-FR-01: RU009 / RF013.

**Estado:** **aprobada por el humano el 2026-11-20**, incluidos la confirmación previa de la marca (COM-03) y el Escenario 7. **No se desarrolla** hasta que el PM lo autorice: sin contrato, sin código y sin pruebas.

## Criterios de aceptación (Gherkin)

### Escenario 1 — Camino feliz: datos del vehículo
```gherkin
# language: es
Característica: Consultas complementarias de placa (simuladas)
  Escenario: El usuario pide los datos del vehículo
    Dado que un usuario en campo consultó la placa sintética "ABC-123" con su motivo
    Y que la app muestra el resultado de requisitoria
    Cuando pulsa "Datos del vehículo (SUNARP, simulado)"
    Entonces la app consulta el simulador de SUNARP y muestra marca, modelo, color, año y estado registral
    Y no muestra el nombre, el DNI ni ningún otro dato del propietario
    Y la consulta queda registrada en la bitácora con el mismo motivo de la consulta de placa
```

### Escenario 2 — Camino feliz: papeletas
```gherkin
  Escenario: El usuario pide las papeletas
    Dado que la app muestra el resultado de requisitoria de una placa sintética
    Cuando el usuario pulsa "Papeletas (SAT Lima, simulado)"
    Entonces la app consulta el simulador del SAT de Lima y muestra la cantidad de papeletas, el monto pendiente y si hay alguna grave
    Y indica que la información cubre solo Lima
    Y la consulta queda registrada en la bitácora con el mismo motivo
```

### Escenario 3 — Caso borde: la placa no tiene papeletas en la fuente
```gherkin
  Escenario: El SAT de Lima no tiene papeletas para la placa
    Dado que el simulador del SAT de Lima responde que la placa no tiene papeletas
    Cuando el usuario pidió las papeletas
    Entonces la app muestra "Sin papeletas pendientes registradas en SAT Lima", en un tono neutro, con la leyenda "Solo cubre papeletas de Lima Metropolitana"
    Y no lo presenta como "sin papeletas" en general, porque la fuente cubre solo Lima
```

### Escenario 4 — Caso borde: error de la fuente
```gherkin
  Escenario: El simulador de SUNARP o del SAT no responde
    Dado que el simulador consultado no responde o responde fuera de contrato
    Cuando el usuario pidió los datos del vehículo o las papeletas
    Entonces la app muestra "No se pudo completar la consulta a SUNARP (simulado); intente nuevamente" o el mismo texto para SAT Lima, con "Reintentar" y "Volver"
    Y no muestra "sin papeletas", "sin observaciones" ni ningún dato vacío como si fuera un resultado
    Y el error queda registrado en la bitácora
    Y el resultado de requisitoria ya mostrado no cambia
```

### Escenario 5 — El usuario marca que el vehículo no coincide
```gherkin
  Escenario: Las características registradas no coinciden con el vehículo
    Dado que la app muestra los datos registrados del vehículo
    Cuando el usuario pulsa "No coincide con lo registrado"
    Y confirma la marca en el aviso previo
    Entonces la marca queda registrada en la bitácora con el mismo motivo
    Y la app muestra "Marcado: No coincide con lo registrado · hh:mm"
    Y la app no muestra "placa clonada" ni ninguna conclusión sobre el vehículo
    Y no se dispara ninguna alerta ni acción automática
    Y el resultado de requisitoria no cambia
```

### Escenario 6 — Caso borde: nada automático ni sin resultado de requisitoria
```gherkin
  Escenario: Las consultas complementarias solo a pedido
    Dado que el usuario obtuvo el resultado de requisitoria de una placa
    Cuando no pulsa ninguna de las dos consultas complementarias
    Entonces la app no consulta SUNARP ni el SAT y no registra nada de ellas
    Y si la consulta de placa terminó en error, sin motivo o con un formato no válido, la app no ofrece las consultas complementarias
```

### Escenario 7 — Caso borde: placa no registrada en SUNARP (propuesta de UX, aprobada por el humano el 2026-11-20)
```gherkin
  Escenario: El simulador de SUNARP no tiene la placa
    Dado que el simulador de SUNARP responde que la placa no está registrada
    Cuando el usuario pidió los datos del vehículo
    Entonces la app muestra "Placa no registrada en SUNARP (simulado)" en un tono neutro, como PLA-08
    Y no lo presenta como error ni como "placa clonada"
    Y no ofrece "No coincide con lo registrado", porque no hay datos que comparar
    Y la consulta queda registrada en la bitácora con el mismo motivo
```

## Supuestos
- Pantallas coordinadas con UX (2026-11-20): sección "Consultas complementarias (simuladas)" en PLA-05 (tiene requisitoria) y PLA-06 (sin requisitoria registrada), porque el PRD dice "después del resultado de requisitoria"; no va en PLA-07 (error). COM-01 Consultando, COM-02 datos de SUNARP ("Compare estos datos con el vehículo que tiene delante", "No se muestra el propietario."), COM-03 confirmación de la marca, COM-04 papeletas ("Solo cubre papeletas de Lima Metropolitana."), COM-05 error. No hay botón "Sí coincide" (el PRD no lo pide).
- Mientras no se responda el PA #36, UX diseña la variante mínima, marcada "PA 36": no se ofrece en PLA-08, la marca no dice qué característica no coincide y no se deshace, y volver a abrir un resultado ya consultado lo muestra de nuevo sin otra consulta ni otro registro. Ninguno de estos puntos está decidido. Los dos elementos no solicitados, la confirmación previa de la marca (COM-03) y el estado "Placa no registrada en SUNARP (simulado)" (Escenario 7), fueron aprobados por el humano el 2026-11-20.
- Solo las pide el agente que hizo la consulta de placa, usando el mismo motivo: no se pide un motivo nuevo (el PRD dice "con el mismo motivo").
- Cada consulta complementaria es independiente: pedir una no pide la otra ("una por una").
- La marca "No coincide con lo registrado" es solo del usuario: la app no compara ni sugiere nada. Solo se ofrece cuando hay datos del vehículo a la vista.
- Vale para la placa ingresada a mano (HU-03) o leída con la cámara (HU-04), porque ambas llegan al mismo resultado.
- Sin datos reales: SUNARP y el SAT son simuladores con datos sintéticos (HU-08). La conexión con las fuentes reales y sus convenios queda fuera del MVP (PA #6 y #17).
- Decisiones del humano del 2026-11-20 (diseño): (1) dos fuentes simuladas separadas, registro vehicular y papeletas, con un esquema cerrado que no tiene campos del propietario; (2) la bitácora registra solo eventos (`CONSULTA_VEHICULO_REGISTRAL`, `CONSULTA_PAPELETAS` y `MARCA_NO_COINCIDE`, más los errores) con el mismo motivo, la placa y el ID de la consulta de origen; no hay tabla nueva y los datos que devuelven las fuentes no se guardan.

## Conflictos con otras fuentes (documentados, no resueltos)
- **PA #15 (qué datos muestra el resultado de placa):** sigue abierto si el resultado muestra algo más que "con/sin requisitoria". La decisión del 2026-11-20 permite mostrar datos del vehículo **solo a pedido** y nunca del propietario. Si el MININTER responde "solo estado", HU-10 queda en duda.

## Puntos abiertos
- PRD PA #35: ¿el MININTER acepta incluir estas consultas en el prototipo? ¿Qué campos de SUNARP y del SAT puede ver el personal en campo? ¿Es aceptable mostrar papeletas solo de Lima, o debe simularse una fuente nacional (municipalidades, SUTRAN)? Supuesto de trabajo: solo datos del vehículo, sin propietario, y papeletas solo de Lima.
- PRD PA #15: ¿qué datos se muestran en la visualización controlada del resultado de placa?
- PRD PA #36: (a) ¿Se ofrecen las consultas complementarias también cuando la placa no está registrada en la fuente de requisitorias (PLA-08)? (b) ¿La marca "No coincide con lo registrado" debe decir qué característica no coincide (marca, modelo, color, año) o admitir un comentario? ¿Se puede deshacer? (c) ¿Se puede repetir una consulta complementaria sobre la misma consulta de placa, y cada repetición queda en la bitácora?

## Fuera de alcance (explícitamente excluido en el PRD)
- Datos del propietario (nombre, DNI u otros).
- Cualquier conclusión automática sobre el vehículo, como "placa clonada".
- La integración con SUNARP, el SAT u otras fuentes reales (MVP con simuladores).
- La lectura automática de placas.
