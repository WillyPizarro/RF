# ADR 0016: Ubicación del dispositivo para el aviso simulado al 105

## Estado

**Propuesto (2026-11-21).** Espera la aprobación del humano (vía PM) y las respuestas del MININTER a los PA #32 y #34. Es solo documental: HU-09 **no se desarrolla** hasta que el PM lo autorice.

## Contexto

- PRD › Aviso simulado al 105 (decisión del humano, 2026-11-20): la app muestra **en el mismo celular** el mensaje que se enviaría, con "ubicación del dispositivo, placa o código de requisitoria, nombre (sintético) … e ID de la consulta; nunca la foto". No se envía nada a una central real. El envío nunca es automático y queda en la bitácora. "Si no hay permiso de ubicación, el aviso lo dice y no inventa una ubicación."
- PA #32: ¿se usa la ubicación GPS del dispositivo, que exige un permiso nuevo y es un dato personal del agente, o se ingresa a mano? Supuesto de trabajo: ubicación del dispositivo con permiso, mostrada solo en el celular.
- PA #34: (b) ¿coordenadas o dirección?; (c) ¿la ubicación se guarda en la bitácora?; (e) ¿es la ubicación del momento del aviso o la de la captura?
- Hoy la app pide solo el permiso de cámara (ADR-0002) y no guarda nada en disco salvo el token y la cola de telemetría de ML Kit (TECH-DESIGN › Controles).
- La ubicación del agente en servicio es un **dato personal del agente**, a validar por Legal si además es sensible, y revela dónde está y qué hace el personal policial. Nota de seguridad: es información operativa.

## Decisión propuesta

1. **Permiso solo en primer plano y en el momento.** El permiso de ubicación "mientras se usa la app" se pide **la primera vez que el usuario pulsa** "Avisar al 105 (simulado)", nunca al abrir la app. Sin ubicación en segundo plano y sin seguimiento. En Android, `ACCESS_FINE_LOCATION` y `ACCESS_COARSE_LOCATION`, sin `ACCESS_BACKGROUND_LOCATION`. Librería de referencia: `expo-location` (la versión del SDK 58 la confirma el LEAD).
2. **Una sola lectura, al pulsar el aviso** (respuesta provisional al PA #34e). La app hace una lectura con un tiempo máximo (provisional: 10 s, a fijar en el ADR-0011) y muestra las coordenadas con su precisión ("±25 m"). No usa la última ubicación conocida si es antigua. Si no hay permiso, se agota el tiempo o el GPS está apagado, el mensaje dice "Ubicación no disponible" y no inventa ninguna. Es la regla 7 aplicada: ningún error se convierte en un dato.
3. **Coordenadas, sin dirección** (respuesta provisional al PA #34b). Convertir las coordenadas en dirección (geocodificación inversa) usa el servicio de la plataforma o de un tercero, y eso **envía la ubicación del agente fuera del sistema**. Se descarta en el MVP.
4. **Se queda en el celular.** Las coordenadas viven solo en la memoria de la app mientras el mensaje está en pantalla. No se escriben en disco ni se envían a la API en el MVP.
5. **Bitácora sin coordenadas** (respuesta provisional al PA #34c). La app llama a un endpoint de la API que **solo registra** el evento `AVISO_105_SIMULADO`: usuario, rol, fecha y hora del servidor, `consulta_id` y si hubo ubicación (`ubicacion_disponible: true/false`). No guarda las coordenadas. La API **no** tiene ninguna integración con el 105. El endpoint y su contrato los define el LEAD cuando se autorice HU-09.
6. **Matriz de tratamiento:** si se aprueba, se agrega la fila "Ubicación del dispositivo del agente (aviso al 105 simulado)". Categoría: personal del agente, con sensibilidad a validar por Legal. Finalidad: mostrar el mensaje simulado. Origen: GPS del celular, con permiso. Dónde: solo en la memoria de la app. Retención: mientras el mensaje está en pantalla. Acceso: el usuario.

## Alternativas consideradas

- **Ingreso manual de la ubicación** (la otra rama del PA #32). No pide permiso nuevo ni capta un dato del dispositivo. Se descarta como opción principal porque el humano pidió la "ubicación del dispositivo" y porque escribir en campo es lento y propenso a errores. Queda como **respaldo** si el MININTER no acepta el permiso: un campo libre opcional, rotulado como "ingresada por el usuario".
- **Guardar las coordenadas en la bitácora.** Da trazabilidad completa del aviso. Se descarta en el MVP porque convierte la bitácora en un registro de la ubicación del personal, que es un dato operativo sensible. El PRD dice "mostrada solo en el celular" y el PA #34c sigue abierto. Si el MININTER lo exige, se guardarían con precisión reducida (3 decimales, unos 110 m) y entraría en la retención del ADR-0008.
- **Ubicación del momento de la captura.** Para la coincidencia facial, la revisión puede llegar horas después (PA #2), y la ubicación de la captura obligaría a leerla y **conservarla** desde la captura, sin saber si habrá aviso. Se descarta por minimización.
- **Dirección con geocodificación.** Es más legible, pero se descarta por lo dicho en el punto 3.

## Consecuencias

- Un permiso nuevo y sensible para el usuario, que se pide solo si usa el aviso. La app tiene que funcionar completa si lo niega (HU-09: "el aviso lo dice").
- La bitácora prueba **que** hubo un aviso, pero no **dónde**. Si el MININTER necesita el dónde, este ADR se reabre.
- **Riesgo, NO VERIFICADO:** en Android, `expo-location` puede usar el proveedor de ubicación de Google Play services. Según la configuración del celular ("Precisión de la ubicación de Google"), el sistema operativo puede enviar datos de Wi-Fi y de antenas a Google. Eso depende del sistema y no de la app. El DEV lo confirma cuando se autorice HU-09 y, si aplica, se agrega a la brecha 10 de TECH-DESIGN (servicios de terceros) y al aviso al usuario.
- **Costo:** la lectura tarda (el primer *fix* del GPS en interiores puede pasar de 10 s), y el mensaje puede mostrar "Ubicación no disponible" en lugares cerrados. Es aceptable para un aviso simulado.
- Producción (brecha): si un día el aviso es real, hará falta un ADR nuevo (integración con la central, canal seguro, retención legal de la ubicación).

## Decisiones que pide al humano

1. ¿Se aprueba la ubicación del dispositivo con permiso en primer plano y una sola lectura al pulsar, o el ingreso manual?
2. PA #34b y #34c: ¿coordenadas sin dirección y bitácora sin coordenadas, como se propone?
3. PA #34e: ¿la ubicación del momento del aviso, como se propone?
