# ADR 0010: App solo en línea y Android como plataforma de referencia

## Estado

Aceptado (2026-11-18)

## Contexto

- PA #11: ¿la app debe funcionar con poca o ninguna conexión? El PRD lo deja abierto y no lo trata como exclusión.
- PA #12: ¿qué dispositivos usará el personal (Android o iOS, institucionales o personales)?
- PRD › Enfoque MVP: "no guardar fotos en el celular". ADR-0005: no se muestra un resultado sin su registro en la bitácora. ADR-0004: la comparación facial ocurre en el servidor. ADR-0008: el celular nunca guarda la captura.
- ADR-0002: el OCR y la calidad facial corren en el dispositivo (ML Kit) y funcionan sin red.

## Decisión

1. **Solo en línea.** Sin red, el OCR y el control de calidad funcionan, pero **las consultas exigen conexión**. Sin red, la app muestra "Sin conexión: no se puede consultar" y **no guarda nada** para enviar después: ni la consulta, ni la captura, ni el resultado. Los resultados ya mostrados no se guardan en caché fuera de la pantalla activa y se limpian al cerrar la sesión o al pasar a segundo plano por inactividad (HU-01 E3).

2. **Android primero.** El prototipo se construye, prueba y distribuye en **Android** (APK interno de EAS). Se fija **un celular Android de gama media como dispositivo de referencia** para las pruebas funcionales, de OCR, de calidad facial y de desempeño. El código sigue siendo multiplataforma (Expo), pero **iOS no se prueba ni se distribuye** hasta que el PA #12 lo confirme.

## Alternativas consideradas

- **Guardar las consultas en el celular y enviarlas al volver la red.** Daba algo de uso sin cobertura. Se descartó porque el agente no tiene la respuesta cuando la necesita y el celular termina guardando datos biométricos, lo que contradice el ADR-0008.
- **Descargar al celular una lista local de placas con requisitoria.** Daba respuestas sin cobertura. Se descartó porque pone un listado sensible en un dispositivo que se puede perder y la consulta sin red no quedaría en la bitácora en el momento (ADR-0005).
- **Android e iOS desde el inicio.** Cubría cualquier respuesta al PA #12. Se descartó porque duplica las pruebas de cámara y OCR, y exige una cuenta Apple Developer de pago dentro del plazo.

## Consecuencias

- El celular no guarda datos sensibles, lo que reduce el riesgo de que un dispositivo perdido exponga información, sin necesidad de construir MDM.
- Los criterios de OCR, calidad y desempeño se miden sobre un dispositivo concreto y quedan reproducibles.
- **Costo:** en zonas sin cobertura la app no sirve para consultar. Es un límite operativo real que va al informe de brechas, con el modo sin conexión como decisión para producción.
- **Costo:** si el PA #12 responde "iPhone", hay que sumar una ronda de pruebas en iOS, la cuenta Apple y los ajustes de permisos de cámara. Se estima de 2 a 3 días.
