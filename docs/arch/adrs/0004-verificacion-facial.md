# ADR 0004: Verificación facial contra lista acotada, motor dentro de la API y umbrales calibrados

## Estado

Aceptado (2026-11-18)

## Contexto

- El encargo pide la verificación facial "sin identificación masiva ni vigilancia indiscriminada" (PRD › No incluye).
- HU-05: captura con control de calidad; resultado "Posible coincidencia — requiere revisión", "No concluyente" o "Sin coincidencia en la lista consultada"; la palabra "identificado" nunca aparece; la captura se borra después de comparar.
- HU-06: revisión humana obligatoria con Confirmar, Descartar o No concluyente, y un motivo.
- PA #7: ¿la verificación es 1:1 o contra una lista? PA #22: ¿cuántos candidatos se muestran? C4 / PA #4: los criterios no tienen umbrales medibles.
- Regla de negocio 6 del encargo: los modelos deben tener una licencia apta para un servicio contratado (nada de InsightFace).
- La skill `especialista-biometria` fija los principios que se aplican sin discusión: sin búsqueda masiva, rechazar las capturas malas antes de comparar, una banda de "no concluyente" y todo umbral documentado.
- ADR-0001: la API FastAPI es el único punto de entrada.

## Decisión

1. **Modo: lista acotada.** La captura se compara solo contra una **galería cerrada de personas con requisitoria simulada** (unas 20 personas sintéticas o del equipo con consentimiento firmado). Nunca se compara contra una base general ni contra video. Cada búsqueda parte de una consulta con motivo registrado. La API devuelve **como máximo 3 candidatos** con score igual o mayor al umbral alto (respuesta provisional al PA #22).

2. **Motor dentro de la API.** YuNet (detección y alineación) y SFace (embedding y similitud coseno) corren como un módulo Python del proceso FastAPI, detrás de una interfaz `MotorBiometrico` (`comparar(captura) -> ResultadoComparacion`). Esa interfaz permite separar el motor en un servicio propio o cambiarlo por un proveedor comercial sin tocar los endpoints.
   - Se fijan la versión de OpenCV y los archivos `.onnx` de opencv_zoo con su hash SHA-256. Antes de usarlos se verifica el LICENSE de cada modelo y se anota en el TDD (según la skill, al momento de redactarla YuNet tenía licencia MIT y SFace Apache 2.0).
   - Los embeddings de la galería se calculan una vez y se guardan; no se reprocesan las fotos en cada consulta.

3. **Calidad en dos pasos.** En el dispositivo, ML Kit verifica un solo rostro, el ángulo, los ojos abiertos y el tamaño mínimo (ADR-0002). En el servidor, YuNet debe detectar exactamente un rostro; además se mide la nitidez (varianza del Laplaciano) y la exposición. Si alguno falla, la respuesta es "captura rechazada" con su motivo y no se compara.

4. **Bandas y umbrales:**

   | Banda | Condición | Texto en la app |
   |---|---|---|
   | `candidato` | score ≥ umbral alto | "Posible coincidencia — requiere revisión" |
   | `no_concluyente` | umbral bajo ≤ score < umbral alto | "No concluyente — verifique por otros medios" |
   | `sin_coincidencia` | score < umbral bajo | "Sin coincidencia en la lista consultada" |
   | `captura_rechazada` | no pasó la calidad | Motivo y opción de repetir |

   **Cómo se fijan (metas provisionales hasta que se responda el PA #4):**
   - **Umbral alto:** el menor valor de coseno con **FMR ≤ 0,1 %** sobre los pares impostores del set de calibración.
   - **Umbral bajo:** el valor con **FNMR ≤ 5 %** sobre los pares genuinos del set de calibración. Si el umbral bajo resulta mayor o igual que el alto, la banda de "no concluyente" queda vacía y se reporta como hallazgo; no se fuerza.
   - Se calibran en la prueba biométrica temprana (días 6 a 10) con un set separado del que se usa para la evaluación final. El punto de partida de referencia es coseno 0,363 (muestra oficial de OpenCV), pero ese valor no se usa sin calibrar.
   - Cada umbral queda versionado (`version_umbral`) y se registra en la bitácora junto con la versión del modelo.

5. **Lo que no se muestra ni se dispara.** El score crudo no se muestra al agente, pero sí se guarda en la bitácora. Ningún resultado dispara alertas ni acciones automáticas antes de la decisión del revisor (HU-06 E3).

## Alternativas consideradas

- **Solo 1:1 con el documento declarado.** Era la opción con menos riesgo de falso positivo. Se descartó porque no responde "¿tiene requisitoria esta persona?" cuando la persona miente sobre su identidad, y obligaba a reescribir HU-05.
- **Ambos modos (1:1 y lista).** Cubría los dos casos. Se descartó porque duplica flujos, pantallas y pruebas en el módulo con más riesgo dentro del plazo.
- **Motor como servicio separado.** Aislaba la carga de CPU y se podía escalar. Se descartó porque es una pieza más que desplegar y asegurar, y la captura haría un salto de red adicional. La interfaz `MotorBiometrico` deja abierta esta opción.
- **Usar el umbral por defecto de OpenCV más un margen.** Era inmediato. Se descartó porque no tiene sustento en datos propios.
- **Dejar las metas al TESTER.** Se descartó porque el DEV construiría sin un criterio de aceptación verificable (C4).

## Consecuencias

- El diseño cumple "sin identificación masiva": la galería es cerrada, cada búsqueda tiene un motivo, hay un máximo de 3 candidatos y la revisión humana es obligatoria.
- Los criterios biométricos se pueden verificar con números (FMR, FNMR, FTA, porcentaje de resultados no concluyentes).
- **Costo / riesgo:** en una lista de N personas, la probabilidad de que una búsqueda de alguien que no está en la lista produzca algún candidato falso es de alrededor de N × FMR. Con N = 20 y FMR = 0,1 %, eso es alrededor del 2 % de las búsquedas. Este número se reporta tal cual en la evaluación. Si la galería crece, el umbral debe ser más estricto.
- **Costo:** para afirmar FMR ≤ 0,1 % con la regla de 3 hacen falta al menos 3.000 pares impostores. Con 20 personas y unas 10 fotos cada una hay alrededor de 19.000 pares, así que alcanza, pero con menos personas o fotos la meta no se puede demostrar y hay que reportar el límite superior real.
- **Costo:** con OpenCV y los modelos dentro de la API, la imagen del contenedor pesa más, y una comparación ocupa un worker. Hay que medir el p95 de la comparación en las pruebas de desempeño.
- **Límite declarado:** el prototipo no incluye prueba de vida ni protección contra suplantación (foto de una foto). Queda en el informe de brechas para producción.
- **Abierto:** si el MININTER responde el PA #7 con "1:1", hay que volver a abrir este ADR y HU-05.
