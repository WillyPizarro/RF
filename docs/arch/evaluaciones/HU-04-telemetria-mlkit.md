# Evaluación ARCH — Telemetría de ML Kit Text Recognition (HU-04)

- **Fecha:** 2026-11-20
- **Pedido por:** LEAD (encargo del 2026-11-20)
- **Rama:** `hu-04`
- **Tipo:** evaluación corta, sin código. **No cambia ningún ADR**: propone cambios que decide el humano.
- **Hallazgo de origen:** en la prueba física de HU-04 (dev build, Samsung S23 Ultra, Android 16), el PM encontró en el almacenamiento privado de la app `databases/com.google.android.datatransport.events` (y su `-journal`).

## Resumen

1. **Qué sale:** según Google, ML Kit envía **métricas de uso y rendimiento** con datos del dispositivo, de la app y un **identificador por instalación**. Según la misma fuente, **la imagen y el texto leído no salen del dispositivo**. La placa leída no está en la lista de datos que se envían.
2. **Si se puede apagar:** **no hay ninguna opción oficial**. Los términos y las páginas de divulgación no mencionan ninguna. Las alternativas son un bloqueo no oficial del transporte, cambiar de motor de OCR o quitar el OCR. Cada una tiene un costo.
3. **Contra el diseño:** no contradice la decisión de fondo del ADR-0002 (la foto de la placa nunca sale). **Sí contradice el texto** de tres documentos: el control "Dispositivo" de TECH-DESIGN ("nada en disco salvo el token"), la matriz de tratamiento (falta una fila) y el título de CONTRATO-HU-04 v3 §6 ("Nada se guarda ni sale del dispositivo"). Además, los términos de ML Kit **obligan a informar al usuario**, y eso hoy no está previsto.
4. **Recomendación ARCH:** opción A para el MVP (mantener ML Kit, documentar e informar) y llevar el tema a producción como brecha. La decisión es del humano (punto abierto al final).

## 1. Qué envía el transporte a Google

### Evidencia en el repositorio

| Afirmación | Evidencia |
|---|---|
| El wrapper incluye ML Kit Text Recognition **empaquetado** (*bundled*, modelo dentro del APK) | `apps/movil/node_modules/@react-native-ml-kit/text-recognition/android/build.gradle:65` → `com.google.mlkit:text-recognition:16.0.1` |
| También empaqueta los modelos chino, devanagari, japonés y coreano. Esto no tiene que ver con la telemetría, pero pesa en el APK | mismo archivo, líneas 67, 69, 71 y 73 |
| En iOS usa `GoogleMLKit/TextRecognition` 8.0.0 | `RNMLKitTextRecognition.podspec:25` |
| `expo-camera` **no** agrega ML Kit de códigos de barras: con `barcodeScannerEnabled: false` la dependencia queda como `compileOnly` | `apps/movil/app.json` (plugin `expo-camera`); `node_modules/expo-camera/android/build.gradle:45-48` |
| El transporte `com.google.android.datatransport` lo trae solo ML Kit Text Recognition | **NO VERIFICADO.** Es lo más probable por lo anterior, pero falta confirmarlo con `./gradlew :app:dependencies` (tarea del DEV si el humano la pide) |
| La base `datatransport.events` es una **cola local** de eventos pendientes. No es prueba de que algo se haya enviado | **NO VERIFICADO** en el dispositivo. No se inspeccionó su contenido ni el tráfico de red |

### Lo que dicen las fuentes oficiales (consultadas el 2026-11-20)

**Términos de ML Kit** — <https://developers.google.com/ml-kit/terms> (última modificación: 14 de mayo de 2025):

> "processing of the input data (e.g. images, video, text) fully happens on-device" … "ML Kit does not send that data and the resultant outputs to Google servers"

> "The ML Kit APIs also send metrics about the performance and utilization of the APIs in your app to Google." Google los usa para "measure performance, debug, maintain and improve the APIs, and detect misuse or abuse".

> "The ML Kit APIs may contact Google servers from time to time in order to receive things like bug fixes, updated models and hardware accelerator compatibility information."

> "You are responsible for informing users of your app about Google's processing of ML Kit metrics data as required by applicable law."

**Divulgación de datos en Android** — <https://developers.google.com/ml-kit/android-data-disclosure> (última modificación: 14 de mayo de 2025). Datos que envían todas las funciones, con fines de "diagnostics and usage analytics":

| Categoría | Dato |
|---|---|
| Información del dispositivo | Fabricante, modelo, versión y build del sistema, aceleradores de ML disponibles |
| Información de la app | Nombre del paquete (`pe.prototipo.movilbuscador`) y versión |
| Identificadores | Para funciones **empaquetadas** (nuestro caso): solo **identificadores por instalación** "not intended to uniquely identify a user or physical device". Las funciones *thin*, que usan Google Play services, agregan un identificador del dispositivo |
| Métricas de rendimiento | Por ejemplo, la latencia |
| Configuración de la API | Por ejemplo, el formato y la resolución de la imagen |
| Tamaño de la entrada y de la salida, versión de la función | — |
| Tipo de evento y códigos de error | Inicialización, detección, liberación de recursos |

En la misma página: "ML Kit encrypts the data in transit using HTTPS" y "ML Kit does not transfer this data to third-parties". Text Recognition **no** figura entre las funciones que agregan datos propios ni Firebase Remote Config o Installations. Esas son detección de objetos y de poses, Translate, Smart Reply, entre otras.

**Divulgación en iOS** — <https://developers.google.com/ml-kit/ios-data-disclosure> (no se encontró la fecha de modificación). Lista lo mismo: dispositivo, *bundle ID*, versión, identificadores por instalación, métricas, configuración, eventos y errores.

**Conclusión del punto 1.** Según Google, no salen imágenes ni el texto leído. Sí salen metadatos técnicos y un identificador por instalación hacia servidores de Google, que está fuera del Perú. Se trata de una **afirmación del proveedor**: no la verificamos con una captura de tráfico.

## 2. ¿Se puede desactivar?

**No hay ninguna opción oficial.** Ninguna de las tres páginas describe una forma de desactivarlo. La página de Android solo habla en general de "configurations or invocations you can control as the app developer", sin dar ninguna. Las fuentes comunitarias (por ejemplo, una pregunta de Stack Overflow, *"disable firebase logging for google ml kit library in android"*) coinciden en que el registro está fijo en la librería y solo proponen trucos por reflexión. Se descartan por frágiles.

| Opción | Qué es | Costo | Riesgo |
|---|---|---|---|
| **A. Mantener ML Kit, documentar e informar** | Sin cambios de código. Se agrega la fila a la matriz, se corrige el control "Dispositivo" y se informa al usuario (por ejemplo, una línea en la pantalla de permiso o en "Acerca de") | Bajo: documentos (ARCH, LEAD, UX, PM) y, si el humano lo pide, un texto en la app | Los metadatos y el ID por instalación siguen saliendo. En el MVP corresponden a dispositivos de prueba y datos sintéticos |
| **B. Bloquear el transporte en el manifest** (no oficial) | Un *config plugin* de Expo que quite con `tools:node="remove"` los componentes del transporte: `TransportBackendDiscovery` (el *backend* CCT) y los programadores de subida (`JobInfoSchedulerService`, `AlarmManagerSchedulerBroadcastReceiver`) | Medio: plugin del DEV en `apps/movil/plugins/`, un dev build nuevo de EAS y pruebas en el dispositivo (OCR sigue leyendo; ningún tráfico a dominios de Google) | **NO VERIFICADO** que ML Kit siga funcionando ni que deje de enviar. La cola local probablemente sigue escribiéndose. Puede romperse al actualizar ML Kit. Falta revisar si los términos de ML Kit lo permiten. Android solamente: iOS necesitaría otra solución |
| **C. Cambiar el motor de OCR** por uno sin telemetría | Tesseract (Apache-2.0) o un modelo abierto (por ejemplo, PaddleOCR con ONNX Runtime) en el dispositivo, con un módulo nativo propio. En iOS se podría usar Apple Vision (es del sistema, no de un tercero) | Alto: varios días de DEV y TESTER, módulo nativo nuevo, rehacer la prueba de precisión (§7, PA #4), y probablemente plataformas con código distinto. **No verificamos** que exista un wrapper mantenido y compatible con Expo SDK 58 | Menor precisión que ML Kit con fotos de cámara. Pone en riesgo el plazo de 30 a 40 días. Contradice la elección de ML Kit del ADR-0002, que habría que reemplazar con un ADR nuevo |
| **D. Quitar el OCR** del MVP (placa solo manual) | Se elimina la dependencia | Bajo en código, alto en alcance: HU-04 sale del MVP (decide el PM con el negocio) | Pierde una funcionalidad del alcance |
| **E. Control de red en producción** | MDM o firewall de la entidad bloquean los dominios de telemetría de Google en los equipos institucionales | Sin costo en el MVP. Se documenta como brecha | Hay que identificar los dominios (**NO VERIFICADO**) y confirmar que el OCR siga funcionando sin ellos |

## 3. Contraste con los ADRs, la matriz y la normativa

| Documento | ¿Se contradice? | Detalle | Qué habría que cambiar (si el humano aprueba) |
|---|---|---|---|
| **ADR-0002** (Expo + ML Kit en el dispositivo) | **No en la decisión. Incompleto en las consecuencias** | La decisión dice "la foto de la placa nunca sale del dispositivo", y eso se mantiene según Google. Pero la sección Consecuencias no menciona la telemetría ni la obligación de informar | Agregar una consecuencia o costo: "ML Kit envía a Google métricas técnicas y un identificador por instalación, sin imagen ni texto, y no se puede desactivar de forma oficial. Hay que informar al usuario". Las opciones B o C exigen un ADR nuevo |
| **ADR-0008** (retención de datos personales) | **No** | Trata la captura facial, la galería y la bitácora. La telemetría no toca ninguna de las tres | Nada. Nota para HU-05: si la calidad facial usa ML Kit Face Detection (ADR-0002), el mismo transporte enviará métricas de esa función, sin la imagen del rostro según Google. Conviene decidir ahora para las dos HUs |
| **TECH-DESIGN, matriz de tratamiento** | **Sí, por omisión** | No hay ninguna fila para los datos que salen a un tercero desde la app | Nueva fila: *Metadatos técnicos de uso de ML Kit* · Técnico (con un identificador por instalación) · Diagnóstico del proveedor del SDK · A validar · SDK en el dispositivo · Cola local en la app y servidores de Google (fuera del Perú) · La define Google · Google |
| **TECH-DESIGN, controles, fila "Dispositivo"** | **Sí, en el texto** | Dice "Nada en disco salvo el token", y la base `datatransport.events` está en el almacenamiento privado | "Nada en disco salvo el token y la cola de telemetría de ML Kit (sin imágenes ni texto)". Agregar la brecha de producción (opción E o C) |
| **CONTRATO-HU-04 v3 §6** (lo cambia el LEAD) | **Sí, en el título**. Las pruebas no fallan | El título dice "Nada se guarda ni sale del dispositivo", pero los casos solo prueban la foto (API, secure-store, archivos de imagen) | Precisar el título: "La foto y el texto no se guardan ni salen del dispositivo", y anotar la telemetría como excepción conocida |
| **PRD, PA #14** (lo cambia el PM) | **No directamente** | El PA #14 pregunta por herramientas de IA en la nube con *información del proyecto* durante el desarrollo, no por un SDK en tiempo de ejecución | Proponer un PA nuevo, o ampliar el #14: "¿El MININTER acepta que la app envíe a Google métricas técnicas de ML Kit (sin imágenes ni texto), o exige cero tráfico a terceros?" |
| **Normativa** (skill `datos-personales-peru`; Ley N.º 29733 y su reglamento, **a validar**, sin fuente oficial consultada) | **Posible brecha. La decide el área legal** | Un identificador por instalación ligado al celular de un agente podría considerarse dato personal, y su envío a servidores de Google fuera del país podría ser un **flujo transfronterizo**. Los principios en juego son finalidad, proporcionalidad y nivel de protección adecuado. En el MVP no hay titulares reales y los equipos son de prueba | Agregar a las brechas de producción: "Telemetría de SDK de terceros: base legal, flujo transfronterizo, información al usuario y control de red". Llevarlo como pregunta al área legal, nunca como certeza |

## Recomendación ARCH

**Opción A en el MVP.** Mantener ML Kit, aplicar los cambios de documentos de la tabla anterior e informar al usuario. Razones:

- Según la fuente oficial, no sale la imagen ni el texto: se mantiene lo que protege el ADR-0002.
- El MVP usa datos sintéticos y celulares de prueba (PA #17), así que la exposición real es mínima.
- B no es oficial y no está verificado. C pone en riesgo el plazo y la precisión. D quita alcance.

**Para producción:** dejarlo como brecha con E (control de red por MDM) y C como plan alternativo si el MININTER exige cero tráfico a terceros.

**Opcional, si el humano quiere cerrar la duda con evidencia:** antes de decidir, que el DEV confirme el origen (`gradlew :app:dependencies`) y que el TESTER inspeccione el contenido de `datatransport.events` en el dispositivo (`adb shell run-as pe.prototipo.movilbuscador`), sin sacar ningún dato del repositorio.

## Puntos abiertos (deciden el humano y el PM)

1. ¿Se acepta la opción A en el MVP, o el MININTER exige cero tráfico a terceros (B o C)?
2. ¿Se aplican los cambios propuestos a ADR-0002 y a TECH-DESIGN (ARCH), a CONTRATO-HU-04 §6 (LEAD) y al PRD (PM, PA nuevo o ampliación del #14)?
3. ¿Cómo se informa al usuario (texto y pantalla), si se elige A? Le corresponde a UX y BA.
4. ¿La misma decisión vale para ML Kit Face Detection en HU-05?
