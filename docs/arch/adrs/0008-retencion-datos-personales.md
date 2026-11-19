# ADR 0008: Retención de la captura facial, galería con consentimiento y retención de la bitácora

## Estado

Aceptado (2026-11-18)

## Contexto

- El rostro es un **dato sensible** (Ley N.º 29733 y su reglamento; cita *a validar* con el área legal del MININTER, sin fuente oficial consultada).
- Regla de negocio 3 del encargo: "la captura facial se borra tras comparar". HU-05 (supuestos): "La captura se borra después de la comparación; solo queda su identificador en la bitácora".
- HU-06 E1: el revisor ve "la captura y la foto de referencia lado a lado". La revisión puede ocurrir minutos u horas después de la comparación. **Esto choca con la regla 3:** si la captura se borra al comparar, la revisión humana no tiene qué comparar.
- Análisis de factibilidad: las fotos del equipo se quedan "fuera del repositorio y de cualquier servicio en la nube". Pero el demo se aloja en la nube del proveedor (PRD, PA #8), y la galería vive en el simulador y en la API (ADR-0004, ADR-0006). **Esto también choca.**
- PA #16: no está definido cuánto tiempo se conservan la bitácora y las imágenes, ni quién autoriza su eliminación. ADR-0005: la bitácora tiene un trigger que impide borrar registros.

## Decisión

1. **Captura facial: se retiene solo si hay un candidato.** La regla 3 se precisa como *"la captura se borra tras la comparación o tras la revisión humana, lo que ocurra primero según el resultado"*:
   - Si el resultado es `sin_coincidencia`, `no_concluyente` o `captura_rechazada`, la captura vive solo en memoria durante la solicitud y nunca se escribe en disco.
   - Si el resultado es `candidato`, la captura se guarda **cifrada en la aplicación** (AES-GCM con una llave del entorno, no versionada) en una tabla `captura_pendiente`, separada de la bitácora. **Se borra al registrar la decisión del revisor o a las 24 h**, lo que ocurra primero. Un proceso periódico de la API ejecuta el borrado a las 24 h. Cada borrado queda en la bitácora (`CAPTURA_ELIMINADA`, con su causa).
   - **Provisional (PA #23):** si la captura llega a las 24 h sin revisión, la revisión pasa al estado `vencida` y el agente ve "No concluyente — verifique por otros medios". El MININTER debe confirmar el plazo y el comportamiento.
   - La app nunca guarda la captura en el dispositivo: ni en la galería del celular, ni en caché, ni en disco.

2. **Galería del demo: fotos del equipo con consentimiento ampliado.** Se usan fotos de integrantes del equipo cuyo **consentimiento firmado cubra de forma explícita**: su uso en la galería del demo, su procesamiento en la nube del proveedor durante el proyecto, su uso en la evaluación biométrica y su borrado al cierre. Las fotos se guardan cifradas en el almacenamiento del simulador, **nunca en el repositorio**. El consentimiento se firma antes del día 6 (inicio de la prueba biométrica temprana). Sin consentimiento firmado, esa persona no entra en la galería.

3. **Bitácora: se conserva durante todo el proyecto y luego se borra el ambiente.** En el MVP, la bitácora (solo con datos sintéticos) se conserva mientras dure el proyecto. Al cierre se elimina todo el ambiente del proveedor (base de datos, almacenamiento, fotos de la galería, copias de respaldo) y se firma un **acta de eliminación**. No se construye un proceso de purga; el trigger del ADR-0005 queda intacto. La retención para producción la define el área legal del MININTER (PA #16) y queda en la política documentada.

4. **Lo que se documenta y no se construye** (enfoque MVP): la evaluación de impacto formal, la inscripción del banco de datos ante la ANPD si corresponde, la atención de derechos ARCO, la gestión de llaves de la entidad y MDM. Todo esto va en la sección de protección de datos del TDD y en el informe de brechas.

## Alternativas consideradas

- **Borrar la captura siempre al comparar.** Cumplía la regla 3 al pie de la letra. Se descartó porque HU-06 E1 deja de cumplirse y la revisión humana pierde su valor como control contra falsos positivos.
- **Revisión inmediata con la captura solo en memoria.** Nunca persistía la captura. Se descartó porque exige un revisor siempre disponible (PA #2 sin resolver) y estado en memoria en la API.
- **Rostros generados en el demo.** No ponía datos reales en la nube. Se descartó porque muchos generadores tienen licencias no comerciales y nadie del equipo podría probar con su propia cara en la demo en vivo.
- **Demo en una máquina local.** Las fotos nunca salían. Se descartó porque el demo no se podría usar desde fuera.
- **Retención fija con purga (por ejemplo, 90 días).** Demostraba el mecanismo. Se descartó porque obliga a abrir una excepción en el trigger de la bitácora y el plazo sería inventado, sin respaldo legal.

## Consecuencias

- HU-06 se puede cumplir y la captura de un no candidato nunca toca disco, lo que minimiza el dato sensible.
- **Costo:** la captura de un candidato vive en disco hasta 24 h. Es un dato sensible en reposo, cifrado con una llave del proveedor, y es el riesgo principal de la evaluación de impacto.
- **Costo:** hay un proceso periódico de borrado que hay que probar (TESTER: una captura con más de 24 h no existe; la bitácora tiene su `CAPTURA_ELIMINADA`).
- **Costo:** se suben datos biométricos reales (del equipo) a la nube del proveedor. El consentimiento debe redactarse con cuidado y el acta de eliminación es obligatoria al cierre.
- **Cambia una regla de negocio:** la regla 3 queda precisada. **Hay que avisar al BA (HU-05, supuestos) y al PM (PRD)** para que la redacción quede alineada.
- **Abierto:** PA #16 (retención en producción), PA #23 (vencimiento de la revisión) y la base legal del tratamiento biométrico (área legal).
