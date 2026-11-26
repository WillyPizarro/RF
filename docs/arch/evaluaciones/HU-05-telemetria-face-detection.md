# Evaluación ARCH — Telemetría de ML Kit Face Detection (HU-05)

- **Fecha:** 2026-11-25
- **Pedido por:** PM, con aprobación del humano. Responde la pregunta 3 de CONTRATO-HU-05 v1 (rama `hu-05`, `36a0bac`), y revisa el borrador del aviso de la decisión 12.
- **Tipo:** evaluación corta, sin código. **No cambia ningún ADR**. Las propuestas las decide el humano.
- **Antecedente:** la [evaluación de Text Recognition](HU-04-telemetria-mlkit.md) (2026-11-20, actualizada el 24 y el 25-nov). El humano decidió el 2026-11-20 que la opción A (mantener ML Kit, documentar y avisar) vale también para Face Detection, **con una condición**: que el ARCH confirme con la fuente oficial que Face Detection no envía la imagen del rostro ni los datos de la detección (`docs/contratos/PENDIENTES.md`).

## Resumen

1. **La imagen y los resultados: confirmado por la fuente oficial**, como declaración del proveedor y en términos generales. Los términos de ML Kit dicen que las API corren en el dispositivo, que el procesamiento de los datos de entrada ocurre por completo ahí y que ML Kit no envía a Google **esos datos ni los resultados** (*resultant outputs*). Los contornos, los *landmarks*, los ángulos y las probabilidades son resultados de la detección. Ninguna página nombra a Face Detection como excepción (la única API con términos aparte es GenAI).
2. **Los eventos de telemetría son del mismo tipo que los de Text Recognition.** La página de divulgación de datos de Android trae una sola lista para todas las funciones. Face Detection **no** está entre las funciones que envían datos adicionales ni entre las que usan Firebase Remote Config o Installations. Para la variante empaquetada, que es la del contrato, el único identificador es uno por instalación.
3. **Lo que la fuente no dice:** ninguna página menciona Face Detection por su nombre en relación con la privacidad. La confirmación es **genérica** (vale para "las API de ML Kit") y es la **palabra del proveedor**. No se comprobó en la red.
4. **El borrador del aviso de la decisión 12 es correcto** respecto de la fuente. Hay dos ajustes opcionales en la sección 4.
5. **Recomendación ARCH:** la condición del humano se da por cumplida en el nivel de la fuente oficial. La opción A vale para el rostro y no hace falta reabrir la decisión antes de ROS-02. Como el rostro es un dato sensible, propongo además una verificación corta en la sesión del bloque HU-05 + HU-06 (sección 5).

## 1. Fuentes oficiales consultadas (2026-11-25)

| Fuente | Fecha de la página | Qué dice, en lo que importa |
|---|---|---|
| **Términos de ML Kit**, <https://developers.google.com/ml-kit/terms> | "Last modified: May 14, 2025" | "ML Kit APIs run on-device." · "processing of the input data (e.g. images, video, text) fully happens on-device" · "ML Kit does not send that data and the resultant outputs to Google servers" · "The ML Kit APIs also send metrics about the performance and utilization of the APIs in your app to Google" · "You are responsible for informing users of your app about Google's processing of ML Kit metrics data" (*as required by applicable law*). No menciona rostros, biometría ni Face Detection. La única API con términos propios es GenAI |
| **Divulgación de datos en Android**, <https://developers.google.com/ml-kit/android-data-disclosure> | "Last modified: May 14, 2025" | Lista "Data collected in all features": información del dispositivo (fabricante, modelo, versión y build del sistema, aceleradores), de la app (paquete y versión), identificadores, métricas de rendimiento (latencia), configuración de la API ("such as image format and resolution"), tamaño de la entrada y de la salida, versión de la función, tipo de evento y códigos de error. Identificadores para las funciones **empaquetadas**: solo "Per-installation identifiers that are not intended to uniquely identify a user or physical device". Las funciones *thin* (por Google Play services) agregan "Device identifier". "ML Kit encrypts the data in transit using HTTPS" y "does not transfer this data to third-parties". **Face Detection no aparece** en la sección de datos adicionales por función (sí aparecen detección de objetos y de poses, Smart Reply, Translate, códigos de barras con auto zoom, entre otras). **Text Recognition tampoco aparece**: las dos están solo en la lista común. La página aclara que describe "only the latest version of each ML Kit Android SDK" |
| **Face Detection, visión general**, <https://developers.google.com/ml-kit/vision/face-detection> | Sin fecha visible | "Face detection is performed on the device". "the API *detects faces*, it does not *recognize people*". No trae ningún enlace ni texto sobre privacidad |
| **Face Detection en Android**, <https://developers.google.com/ml-kit/vision/face-detection/android> | Sin fecha visible | Variante empaquetada `com.google.mlkit:face-detection:16.1.7` ("bundle the model with your app", unos 6,9 MB) y no empaquetada `com.google.android.gms:play-services-mlkit-face-detection:17.1.0` (modelo descargado por Google Play services). Resultados: recuadro, *landmarks*, contornos (solo del rostro más prominente), probabilidades de sonrisa y de ojos abiertos, ángulos de Euler e id de seguimiento. No trae nada sobre privacidad |

Las páginas se leyeron el 2026-11-25. Las citas son textuales; lo demás es resumen del ARCH.

## 2. Respuesta a la pregunta 3 del contrato

| Qué se pregunta | Respuesta | Base |
|---|---|---|
| ¿Envía la **imagen** del rostro? | **No**, según Google | Términos: el procesamiento de la entrada ocurre por completo en el dispositivo y ML Kit no la envía |
| ¿Envía los **contornos**, los ***landmarks*** o los **resultados** de la detección (ángulos, probabilidad de ojos abiertos, recuadro)? | **No**, según Google | Términos: tampoco envía *the resultant outputs*. Son resultados de la API |
| ¿Los eventos son del **mismo tipo** que los de Text Recognition? | **Sí**, según Google | Divulgación: una sola lista común. Ninguna de las dos funciones tiene datos adicionales. Con la variante empaquetada, el identificador es solo por instalación |
| ¿Hay algo que se parezca a un resultado dentro de la telemetría? | **Solo metadatos**: "API configuration (such as image format and resolution)" y "Feature input and output size". El tamaño de la salida podría reflejar, por ejemplo, cuántos rostros se detectaron. Qué contiene exactamente es **NO VERIFICADO** | Divulgación |

**Matices que hay que dejar escritos:**

- **Es una afirmación del proveedor**, igual que para Text Recognition. La cola `datatransport` del S23 (2026-11-25) coincidió con lo declarado para Text Recognition: 5 eventos sin imagen ni placa. Para Face Detection todavía no se vio nada en el teléfono, porque no está construido.
- **La confirmación es genérica.** Ninguna página habla de Face Detection y privacidad juntas. Que no figure entre las funciones con datos adicionales es evidencia **por omisión**. Lo refuerza que la página diga que lista lo que recoge "la última versión de cada SDK".
- **Dependencia transitiva.** Según el DEV (2026-11-24), la variante empaquetada `face-detection:16.1.7` trae por el POM de Google dependencias `play-services-mlkit-*`, igual que Text Recognition. Qué hacen en la red sigue **NO VERIFICADO** (ADR-0017 punto 3). La verificación de red de nivel 1 de la sesión 1 de DESPLIEGUE-01 responde esto para Text Recognition, no para Face Detection.
- **Versión.** La divulgación vale para la última versión de cada SDK. El contrato fija la versión exacta del plugin (`google_mlkit_face_detection`), y el DEV tiene que confirmar que use la variante **empaquetada** `com.google.mlkit:face-detection` y no la de Google Play services. Con la variante *thin* se agregaría un identificador del dispositivo, y esta evaluación no la cubre.

## 3. Recomendaciones de minimización para el DEV (las fija el LEAD en el contrato)

El contrato usa solo el número de rostros, el ancho del rostro, los ángulos y la probabilidad de ojos abiertos (§5). Lo que no se usa no se pide:

- **Sin contornos** (`enableContours: false`, el valor por defecto). Ningún caso de §5 los usa.
- **Sin seguimiento** (`enableTracking: false`). Con una foto por toque no hay nada que seguir, y el id de seguimiento es un dato más sobre una persona.
- **Clasificación activada** (`enableClassification: true`), porque §5 la usa para los ojos. **Landmarks** solo si el recorte del margen los necesita; si alcanza con el recuadro, apagados.
- Ningún resultado de la detección se registra en `logcat`, en la bitácora ni en la API. A la API viaja solo el recorte JPEG (§5, "Pasa").

No es una exigencia de la fuente, sino minimización (ADR-0008 y Ley N.º 29733, a validar por Legal).

## 4. Revisión del borrador del aviso (decisión 12)

> "Antes de capturar el rostro" · "Para revisar la calidad de la foto, la app usa ML Kit, una herramienta de Google que funciona en este teléfono. Según Google, ML Kit no le envía la foto del rostro ni los datos de la detección, pero sí le envía datos técnicos de uso y un código de esta instalación." · "Entendido"

| Frase | ¿Coincide con la fuente? | Comentario |
|---|---|---|
| "funciona en este teléfono" | **Sí** | "ML Kit APIs run on-device" y "Face detection is performed on the device" |
| "no le envía la foto del rostro ni los datos de la detección" | **Sí**, como declaración de Google | "does not send that data and the resultant outputs". "Según Google" hay que **mantenerlo**: no está verificado en la red |
| "sí le envía datos técnicos de uso" | **Sí, pero se queda corto** | La lista incluye datos **del teléfono** (fabricante, modelo, versión del sistema). Ajuste opcional: "datos técnicos del teléfono y de uso". Si se cambia, conviene cambiar también el aviso de OCR-01 (CONTRATO-HU-04), para que los dos digan lo mismo |
| "un código de esta instalación" | **Sí**, si la variante es la empaquetada | "Per-installation identifiers". Con la variante *thin* habría además un identificador del dispositivo y el aviso quedaría incompleto |
| — | — | Los términos piden informar "as required by applicable law". Si alcanza con este texto lo decide Legal (brecha 10). En el MVP los equipos son de prueba y los datos sintéticos |

**Conclusión del punto 4:** el borrador se puede aprobar tal como está. Los ajustes son opcionales y los deciden el UX y el BA (pregunta 4 del contrato).

## 5. ¿Hace falta una verificación de red para Face Detection?

**Propuesta ARCH: sí, corta, en la sesión del bloque HU-05 + HU-06.** El rostro es un dato sensible y la confirmación de la fuente es genérica. Además, la del S23 de hoy cubre solo Text Recognition.

| Paso | Qué | Tiempo estimado |
|---|---|---|
| **H7 (ya en el contrato)** | La cola `datatransport` después de capturar rostros, con `revisar_datatransport.py`: ninguna imagen. Además, para el ARCH: cuántos eventos nuevos hay, su `transport_name`, el tamaño de los payloads y las claves de los metadatos, para compararlos con los de Text Recognition (110 a 144 bytes, unas 15 claves). Si un payload de Face Detection fuera mucho más grande, se anota. Por ejemplo, los contornos de un rostro son más de 100 puntos y no caben en 150 bytes, mientras que unos pocos *landmarks* sí | Ya incluido |
| **Nivel 1 de red, reducido** (PCAPdroid, filtro por la app y por `com.google.android.gms`) | El mismo método de la propuesta del 2026-11-25 en la [evaluación de HU-04](HU-04-telemetria-mlkit.md), solo con capturas de rostro: a qué dominios se conecta y si Google Play services descarga o activa algo de `play-services-mlkit-face-detection` aunque la variante sea empaquetada. **Se espera:** solo `firebaselogging.googleapis.com` desde la app | Unos 20 minutos, porque PCAPdroid ya queda instalado y probado desde DESPLIEGUE-01 |
| **Nivel 2** (mitmproxy y `protoc --decode_raw`) | **Condicional**, con el mismo criterio de la M-6: solo si el nivel 1 muestra tráfico de la app hacia Google. Así se ve si el cuerpo lleva algo parecido a coordenadas | De 60 a 90 minutos, solo si se corre |

- **Quién:** igual que en DESPLIEGUE-01. El DEV corre los `adb` y la captura, el humano hace lo que requiere el teléfono, el TESTER suma los pasos al guion del bloque y el ARCH recibe el resultado y actualiza esta evaluación.
- **Hace falta el S23 y el humano**, pero no una sesión aparte: se suma a la del bloque. La captura se guarda fuera del repositorio y se borra al terminar. Solo se usan las fotos con consentimiento (ADR-0008) y en el repositorio no queda ningún valor identificador.
- **Si el resultado de hoy (Text Recognition) ya muestra algo inesperado**, por ejemplo tráfico de Google Play services ligado al OCR o una cola vaciada sin tráfico, esta propuesta pasa de recomendada a **necesaria antes de usar ML Kit en ROS-02**. Lo reviso cuando el LEAD me pase los resultados de la sesión 1.

**Qué reabre la decisión:** que aparezca una imagen, o algo que parezca contornos, *landmarks* o resultados, en la cola o en la red. También que el DEV no pueda usar la variante empaquetada.

## Puntos abiertos (deciden el humano y el PM)

1. ¿Se da por cumplida la condición del 2026-11-20 con la fuente oficial genérica, tal como recomienda el ARCH?
2. ¿Se suma el nivel 1 reducido (y el 2 condicional) a la sesión del bloque HU-05 + HU-06?
3. ¿Se aplican las recomendaciones de minimización de la sección 3 en el contrato (las fija el LEAD)?
4. ¿Se ajusta el aviso ("datos técnicos del teléfono y de uso") en HU-05 y en HU-04, o se aprueba como está? Lo deciden el UX y el BA.
