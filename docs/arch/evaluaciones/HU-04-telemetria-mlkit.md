# Evaluación ARCH — Telemetría de ML Kit Text Recognition (HU-04)

- **Fecha:** 2026-11-20
- **Pedido por:** LEAD (encargo del 2026-11-20)
- **Rama:** `hu-04`
- **Actualizada:** 2026-11-24 (app en Flutter) y 2026-11-25 (cola del S23, propuesta de verificación de red y su resultado, niveles 1 y 2).
- **Tipo:** evaluación corta, sin código. **No cambia ningún ADR**: propone cambios que decide el humano.
- **Hallazgo de origen:** en la prueba física de HU-04 (dev build, Samsung S23 Ultra, Android 16), el PM encontró en el almacenamiento privado de la app `databases/com.google.android.datatransport.events` (y su `-journal`).

## Resumen

1. **Qué sale:** según Google, ML Kit envía **métricas de uso y rendimiento** con datos del dispositivo, de la app y un **identificador por instalación**. Según la misma fuente, **la imagen y el texto leído no salen del dispositivo**. La placa leída no está en la lista de datos que se envían.
2. **Si se puede apagar:** **no hay ninguna opción oficial**. Los términos y las páginas de divulgación no mencionan ninguna. Las alternativas son un bloqueo no oficial del transporte, cambiar de motor de OCR o quitar el OCR. Cada una tiene un costo.
3. **Contra el diseño:** no contradice la decisión de fondo del ADR-0002 (la foto de la placa nunca sale). **Sí contradice el texto** de tres documentos: el control "Dispositivo" de TECH-DESIGN ("nada en disco salvo el token"), la matriz de tratamiento (falta una fila) y el título de CONTRATO-HU-04 v3 §6 ("Nada se guarda ni sale del dispositivo"). Además, los términos de ML Kit **obligan a informar al usuario**, y eso hoy no está previsto.
4. **Recomendación ARCH:** opción A para el MVP (mantener ML Kit, documentar e informar) y llevar el tema a producción como brecha. La decisión es del humano (punto abierto al final).

## Actualización 2026-11-24: app en Flutter y dependencia transitiva de Google Play services

Lo encontró el DEV en la migración a Flutter (ADR-0017). El humano lo aceptó (opción A, vía PM) y el LEAD lo recoge en CONTRATO-MIGRACION-FLUTTER v1.2 §7.

| Afirmación | Evidencia |
|---|---|
| `google_mlkit_text_recognition` 1.0.3 declara la variante **empaquetada** `com.google.mlkit:text-recognition:16.0.1`, y el modelo **sí viene dentro del APK** | Hallazgo del DEV en el árbol del APK (CONTRATO-MIGRACION-FLUTTER v1.2 §7). El ARCH no lo reprodujo |
| Según el POM que publica Google, ese artefacto empaquetado depende de `com.google.android.gms:play-services-mlkit-text-recognition:19.0.1` y de `play-services-mlkit-text-recognition-common:19.1.0`. La dependencia es **transitiva** y no se excluye | POM oficial del artefacto, según el DEV. El ARCH no lo reprodujo |
| `com.google.mlkit:face-detection:16.1.7` (HU-05) tiene la misma forma: variante empaquetada con dependencias transitivas de `play-services-mlkit-*` | Hallazgo del DEV. El ARCH no lo reprodujo |
| Qué hacen esas dependencias de Google Play services **en la red**: si agregan tráfico, si mandan otro identificador (la página de divulgación dice que las funciones *thin* agregan un identificador del dispositivo) o si quedan sin uso porque el modelo está empaquetado | **NO VERIFICADO.** No se capturó tráfico ni se revisó qué clases se cargan en tiempo de ejecución |

**Qué cambia:** nada en la decisión. Sigue la opción A: el aviso de OCR-01 y la revisión de la cola `datatransport` en el teléfono, que **se mantiene igual en la mini sesión del 4-dic** (CONTRATO-HU-04 v6 §6, fila "Cola de telemetría"). Lo único que cambia es el criterio del contrato: se pide que el modelo esté dentro del APK, no que falte `play-services-mlkit-*`. La tabla de identificadores de la sección 1 ("para funciones empaquetadas, solo identificadores por instalación") pasa a ser **lo que dice Google para la variante empaquetada**: con la dependencia transitiva presente, no hay evidencia de que no se sumen los datos de la variante *thin*. Para producción, esto se agrega a la brecha 10 de TECH-DESIGN (control de red, opción E).

## Actualización 2026-11-25: lo que había en la cola `datatransport` del S23 (app Flutter)

Fuente: la mini sesión física del 25-nov, sección 9 del registro de resultados (`resultados-s23.md`, **fuera del repositorio**, en la carpeta de capturas de MIGRACION-FLUTTER). El DEV y el PM corrieron la sección con el APK de depuración de la migración, después de leer una placa impresa `ZZ…`. La copia de la cola se revisó con `pruebas/datos/revisar_datatransport.py` y se borró al terminar (paso 9.6). Aquí **no se copia ningún valor identificador** (ni el UUID de la instalación ni la huella del build): solo las categorías.

| Afirmación | Evidencia |
|---|---|
| La cola existe en el almacenamiento privado de la app: `databases/com.google.android.datatransport.events` (40 960 bytes) y su `-journal` (vacío) | Pasos 9.2 y 9.4 |
| Hay **5 eventos**, todos con `transport_name = FIREBASE_ML_SDK`, con payload protobuf de **110 a 144 bytes** cada uno y `num_attempts = 0` | Paso 9.5 |
| El transporte usa el *backend* `cct`, y el destino que tiene configurado (extras en base64 de `transport_contexts`) es **`firebaselogging.googleapis.com/v0cc/log/batch`** | Paso 9.5 (2 filas en `transport_contexts`) |
| Datos legibles en los metadatos (75 filas en `event_metadata`, unas 15 por evento): el **paquete** de la app, dos **versiones de SDK** (`17.3.0` y `16.0.1`), un **identificador de instalación** (UUID) y **datos del equipo**: país, idioma, fabricante, modelo, nombre de dispositivo, hardware, nivel de API, huella del build, desfase horario y tipo de red | Paso 9.5 |
| **Ninguna imagen** (JPEG o PNG, crudas o en base64) y **ningún texto de placa** `ZZ…` en la cola. Tampoco se vieron tokens ni datos del usuario | Paso 9.5, código 0 del script |
| El OCR funciona **sin ninguna red**: con modo avión, Wi-Fi apagado y el cable USB desconectado, `ZZA-101` se leyó en el teléfono | Sección 10, repetición de 10.2 |

**Cómo se lee:**

1. **Coincide con lo que Google declara** para las funciones empaquetadas (sección 1): datos del dispositivo y de la app, versiones y un identificador **por instalación**. En la cola **no** apareció un identificador del dispositivo (Android ID o de publicidad) como el que la divulgación atribuye a las funciones *thin*.
2. **`num_attempts = 0` no prueba que no se envíe nada.** La cola guarda solo lo **pendiente**: el transporte borra los eventos que ya subió. Que haya 5 sin intento quiere decir que, cuando se copió, esos 5 no se habían intentado subir. Lo más probable es que la subida la programe el sistema más tarde (JobScheduler), cuando hay red, pero eso es **NO VERIFICADO**.
3. **El destino ya está identificado** para lo que pasa por la cola de la app: `firebaselogging.googleapis.com`. Es el primer dominio para la opción E (control de red en producción). No se sabe si hay **otros** destinos.
4. **El script solo ve lo legible.** Busca firmas de imagen y el texto `ZZ…` en bytes crudos y en base64, pero no descomprime ni decodifica el protobuf. Con payloads de 110 a 144 bytes no cabe una foto, pero el **contenido exacto del protobuf** (métricas, configuración de la imagen, códigos de evento) sigue **NO VERIFICADO**.
5. **Lo que no cubre la cola:** las dependencias transitivas `play-services-mlkit-*` (actualización del 2026-11-24) corren, si es que corren, en el proceso de Google Play services, que tiene su propia red y sus propias colas, fuera del almacenamiento de la app. La cola de la app **no dice nada** sobre ese tráfico. Sigue **NO VERIFICADO**.
6. **Dos versiones de SDK:** `16.0.1` coincide con `com.google.mlkit:text-recognition:16.0.1`. Que `17.3.0` sea el núcleo común de ML Kit (por ejemplo, `vision-common`) es lo más probable, pero **NO VERIFICADO**. Este APK solo tiene Text Recognition: Face Detection (HU-05) no está construido.
7. **El OCR no necesita red** (sección 10). Si en producción se bloquean los dominios de telemetría (opción E), la lectura de la placa debería seguir funcionando. Falta comprobar que el SDK no falle ni se quede esperando cuando la red está presente pero el dominio bloqueado.

**Qué cambia:** **nada en la decisión.** La condición del contrato para reabrirla (que aparezca una imagen o un texto `ZZ…`) **no se cumplió**, así que sigue la opción A del 2026-11-20. El aviso de OCR-01 ("código de esta instalación") describe bien lo que se vio. Se actualizan el punto 3 del ADR-0017 y la brecha 10 de TECH-DESIGN con el dominio y con lo que sigue sin verificar.

## Propuesta 2026-11-25: verificación de red pendiente

**Pregunta:** ¿la app con ML Kit empaquetado se conecta a servicios de Google y, si lo hace, qué envía? Interesa la red **del proceso de la app** (la cola `datatransport`) y la de **Google Play services** mientras la app usa el OCR (las dependencias `play-services-mlkit-*`).

**Propuesta ARCH: dos niveles en una sola sesión con el S23, y un tercero opcional.** La decisión es del humano y del PM.

| Nivel | Qué responde | Método | Requisitos |
|---|---|---|---|
| **1. A quién se conecta** (recomendado) | Qué dominios contacta la app y cuántos bytes envía; si Google Play services abre conexiones nuevas mientras se usa el OCR | **PCAPdroid** en el S23 (captura sin root por una VPN local de Android; GPL-3.0; se instala desde F-Droid o Google Play y se desinstala al terminar). Se filtra por la app `pe.prototipo.movilbuscador` y, en una segunda corrida, por `com.google.android.gms`. Muestra el DNS y el nombre del servidor TLS (SNI) de cada conexión, con bytes y hora, y exporta un `.pcap`. Secuencia: (a) copiar la cola y contar los eventos, como en la sección 9; (b) iniciar la captura con el Wi-Fi conectado; (c) leer una placa `ZZ…` impresa; (d) forzar la subida pendiente con `adb shell cmd jobscheduler run -f pe.prototipo.movilbuscador <id>` (el id sale de `adb shell dumpsys jobscheduler`); (e) esperar 5 minutos; (f) detener la captura y volver a copiar la cola. **Se espera:** una conexión de la app a `firebaselogging.googleapis.com` y que la cola se vacíe. Cualquier otro dominio de Google se anota | El S23 con Wi-Fi real: el túnel de `adb reverse` no sirve para esto. El humano instala PCAPdroid y acepta el diálogo de VPN de Android |
| **2. Qué envía** (recomendado, en la misma sesión) | El contenido de la subida de la cola: qué campos van y si va algo más que lo que se vio en la cola | **mitmproxy** (MIT) en la PC, con el **APK de depuración**. Su `network_security_config` confía en los certificados del usuario (`debug-overrides`, ADR-0017 regla 4), así que el tráfico del proceso de la app que use la pila de red de Android se puede leer si se instala la CA de mitmproxy como certificado del usuario. El cuerpo de la subida se decodifica con `protoc --decode_raw` (antes se descomprime, si viene en gzip) y se le pasa la misma búsqueda de imagen y de `ZZ…` del script del TESTER. El tráfico de Google Play services **no** se puede leer así, porque es otra app y no confía en los certificados del usuario: para ese queda solo el nivel 1 | El humano instala la CA de mitmproxy como certificado del usuario y la **quita** al terminar. El release no se puede inspeccionar, y eso es lo esperado: confirma que el release solo confía en las CA del sistema |
| **3. Control negativo** (opcional, para producción) | Si el OCR sigue funcionando con la red presente y los dominios de telemetría bloqueados (opción E) | Bloquear `firebaselogging.googleapis.com` (y lo que salga del nivel 1) en el DNS del punto de acceso que use el teléfono. Luego leer una placa y ver que OCR-02 aparece sin demora y que la cola crece sin vaciarse | Lo mismo que el nivel 1, más un punto de acceso con DNS controlable (por ejemplo, la PC del proyecto) |

**Quién lo corre:**
- **El DEV** prepara y corre los `adb` y la captura, como en la M-11 a la M-15.
- **El humano** hace en el teléfono lo que requiere su mano: instalar PCAPdroid, aceptar la VPN, instalar y quitar la CA de mitmproxy y leer la placa impresa.
- **El TESTER** escribe los pasos en su guion de dispositivo (`pruebas/datos/`) y, si hace falta, amplía `revisar_datatransport.py` para que descomprima y busque en el cuerpo capturado.
- **El ARCH** recibe el resultado y actualiza esta evaluación, el ADR-0017 y la brecha 10.
- **El LEAD** arma el encargo.

**Cuánto tarda (estimado, no medido):**
- Preparación del guion y de las herramientas: unas 2 horas entre el TESTER y el DEV.
- Sesión con el S23: unos 45 minutos el nivel 1 y otros 60 a 90 minutos el nivel 2. El nivel 3 suma unos 30 minutos.
- En total, **medio día** con el teléfono y el humano.

**Sí hace falta el S23 y el humano.** Sin root, solo el teléfono puede atribuir cada conexión a la app o a Google Play services. Además, instalar una app de captura y una CA de usuario obliga a aceptar diálogos del sistema a mano. Y lo que interesa es el comportamiento en un equipo con Google Play services real, como los de producción.

**Alternativa sin el S23 (no recomendada):** un emulador de Android con imagen de Google APIs y root, con `tcpdump` adentro y una imagen de placa sintética en la cámara virtual. No necesita al humano, pero tarda más (medio día solo en armarlo) y es menos representativo, porque usa el Google Play services del emulador y no el del Samsung. Además, el ARCH no comprobó que el OCR empaquetado funcione con la cámara virtual (**NO VERIFICADO**).

**Cuidados (regla 8 y ADR-0008):**
- La captura tiene el identificador de instalación y los datos del equipo. Se guarda **fuera del repositorio** (por ejemplo, en `C:\Willy\Trabajo\MININTER\flutter-capturas\red\`) y se borra al terminar, como la cola en el paso 9.6.
- En el repositorio solo quedan categorías, dominios y conteos, nunca valores identificadores.
- Solo se usan placas sintéticas `ZZ…` impresas.
- Al terminar se desinstala PCAPdroid y se quita la CA de mitmproxy, y se deja constancia en el registro.

**Qué cambia según el resultado:**
- **Solo `firebaselogging.googleapis.com`, sin imagen ni texto:** se cierra el NO VERIFICADO de la red del proceso de la app, se confirma la opción A y la brecha 10 queda con una lista concreta de dominios.
- **Otros dominios de Google** (por ejemplo, desde Google Play services al usar el OCR): se anotan en la brecha 10 y se le pregunta al humano si se excluye `play-services-mlkit-*`, con una prueba de que el OCR empaquetado sigue funcionando sin esa dependencia.
- **Una imagen o un texto `ZZ…` en lo que sale:** se reabre la decisión, igual que con la cola.

## Resultado 2026-11-25: verificación de red (niveles 1 y 2, sesión 1 de DESPLIEGUE-01)

**Fuente:** los resultados que el LEAD pasó al ARCH por herdr el 25-nov. La sesión la corrieron el DEV y el humano, con el S23 y el APK de depuración, siguiendo la M-6 del encargo de DESPLIEGUE-01 (`c5fff2a`, punto 5 con las condiciones del ARCH). Las capturas de PCAPdroid, los pcap y los cuerpos descifrados quedaron **fuera del repositorio**. Aquí van solo categorías, dominios, horas, bytes y conteos: ni el UUID de la instalación ni la huella del build. El nivel 3 (bloqueo por DNS) no se corrió, porque no estaba aprobado.

### Nivel 1: a quién se conecta

| Corrida | Qué se vio | Evidencia |
|---|---|---|
| **1. Filtro por la app** | **2 conexiones**, las dos cerradas: (a) DNS (UDP 53) de `firebaselogging.googleapis.com`, 76 B enviados y 204 B recibidos, a las 20:11:34.160; (b) TCP 443 con SNI `firebaselogging.googleapis.com` hacia una IP de Google, 2,7 KB enviados y 5,4 KB recibidos, de 20:11:34.199 a 20:12:36. **Ningún otro dominio.** Durante el OCR (20:09 a 20:10) **no hubo ninguna conexión**: la única salió con el job forzado (b.6, 20:11:34). Cola: 5 eventos antes y 0 después (20:22:14) | Lista y detalle de PCAPdroid, sin pcap porque el volcado estaba en "Ninguno"; 3 capturas de pantalla por `adb` fuera del repositorio. El ARCH dio por suficiente la lista con la cola antes y después |
| **2. Filtro por Google Play services** (`com.google.android.gms`) | Solo `mtalk.google.com` (FCM, TCP 5228), con su DNS y 5 conexiones. Una cae **dentro** de la ventana del OCR y del job (20:34:44 a 20:36:22, 2347 B enviados y 4688 B recibidos): ya estaba abierta antes y es la reconexión periódica de FCM, cada 1 a 1,5 minutos. Las otras 4 caen fuera. **Ningún `firebaselogging` ni ningún otro host desde gms.** En un pcap anterior (20:31:19), con el filtro sin confirmar y **fuera** de la ventana, aparecieron `spot-pa.googleapis.com` (QUIC 443, 6662/5691 B) y `mtalk`. Cola de la app: OCR poco antes de las 20:35:45, 5 eventos a las 20:35:56, job **forzado** a las 20:35:56-57 y 0 eventos a las 20:45:58 | Pcap leído solo por SNI y DNS, sin el contenido; capturas por `adb` |

**Lectura del ARCH:** la conexión de `mtalk` es el canal permanente de notificaciones de Google Play services y coincide con la ventana solo por tiempo. **No se atribuye a ML Kit.** `spot-pa.googleapis.com` queda como **no atribuible** (fuera de la ventana y con el filtro sin confirmar). En esta sesión, **no se observó tráfico de Google Play services ligado al OCR**.

### Nivel 2: qué envía

| Qué | Resultado |
|---|---|
| Disparo | OCR de `ZZB-201` a las 20:52. **Ningún POST antes del job forzado.** Cola con 5 eventos a las 20:53:37, `run -f` a las 20:53:37.966, **2 POST** `/v0cc/log/batch` a `firebaselogging.googleapis.com` a las 20:53:38, los dos con 200, y cola en 0 a las 20:54:46 |
| Formato | `Content-Type: application/json`, `Content-Encoding: gzip`; 819 B y 1827 B descomprimidos. El cuerpo **no** es protobuf: es JSON con `logRequest[]` |
| `clientInfo` (en cada pedido) | Versión del SDK, modelo, hardware, dispositivo, producto, build del sistema, fabricante, **huella del build**, idioma, país, **MCC/MNC** (código del país y del operador de la red móvil) y build de la app |
| Por evento (`logEvent[]`, con `logSourceName` y `qosTier`) | Hora, tiempo desde el arranque (*uptime*), zona horaria, tipo de red y un `sourceExtension`: un protobuf en base64, uno por evento (5 en total) |
| `sourceExtension` decodificado (`protoc --decode_raw`) | El paquete de la app, la versión del SDK de ML Kit, idioma y región, **un UUID** (el identificador de instalación) y el resto, **solo enteros**: códigos de evento y métricas |
| Búsqueda de placa e imagen | `ZZB-201`, `ZZB201`, `ZZA-101`, `ZZA101` y `ZZ`: **0** en el JSON y en el base64 decodificado. Firmas de imagen: **0**. `revisar_datatransport.py`: código 0 |
| Cuidados | No se guardó ningún cuerpo de otras apps. La CA de mitmproxy se usó solo con el APK de depuración |

### Qué cierra y qué no

**Se cierra (con evidencia en el S23, APK de depuración, una sesión):**

1. **La app se conecta a un solo destino de Google: `firebaselogging.googleapis.com`** (HTTPS, 443), y **solo** cuando se sube la cola. Durante el OCR no hay red. Es la lista de dominios de la brecha 10 para el proceso de la app.
2. **Lo que sale no tiene la imagen ni la placa leída.** Es lo que Google declara ("does not send that data and the resultant outputs"), ahora comprobado en lo que viaja por la red, no solo en la cola.
3. **Lo que sale coincide con las categorías de la divulgación de Google** (sección 1): dispositivo, app, versiones, un identificador por instalación, tipo de evento y métricas. No apareció un identificador del dispositivo como el que la divulgación atribuye a las funciones *thin*.
4. **La red de Google Play services no mostró tráfico ligado al OCR** en esta sesión.

**Va más allá de los ejemplos de Google, y hay que decirlo:** la divulgación lista "Device information (such as manufacturer, model, OS version and build)". El "such as" no cierra la lista, y lo que se vio la amplía con **país, idioma, zona horaria, tipo de red, MCC/MNC (operador móvil) y huella del build**. No son datos del usuario, pero sí del **teléfono y de la red**, y van junto al identificador de instalación. Para el aviso, entran en "datos técnicos del teléfono y de uso", el texto que el humano aprobó para HU-05 (evaluación de Face Detection, punto 4). El aviso de OCR-01 de HU-04 tendría que decir lo mismo, y eso lo decide el LEAD con el UX. Para Legal (brecha 10): con la hora, el identificador de instalación, el operador y el país, cada envío se puede vincular a un teléfono concreto, aunque no a una persona. Es un argumento más para la pregunta sobre el flujo transfronterizo (PA #31).

**Sigue NO VERIFICADO:**

- **La subida automática.** En las dos corridas con la app y en el nivel 2, los eventos salieron **solo** con el job forzado. No se vio cuándo sube el transporte por su cuenta.
- **El significado de los enteros** del `sourceExtension` (códigos de evento y métricas). Son enteros y no contienen texto, pero no se mapearon campo por campo.
- **El APK de release.** El nivel 2 solo se puede hacer con el de depuración. El SDK es el mismo, así que se espera el mismo contenido, pero no se comprobó.
- **El tráfico de Google Play services fuera de esta sesión**, y si `play-services-mlkit-*` descarga algo en otras condiciones (otro día, después de una actualización de gms o con otro teléfono).
- **Qué hace el SDK cuando el dominio está bloqueado** (nivel 3, no corrido). Sin ninguna red, el OCR funciona (sección 10 del S23), y como la subida va por un job aparte de la lectura, lo más probable es que el bloqueo no afecte al OCR. Qué pasa con la cola acumulada no se sabe.
- **Face Detection (HU-05).** Esta sesión cubre solo Text Recognition. Sigue la verificación reducida de la [evaluación de Face Detection](HU-05-telemetria-face-detection.md), que se puede comparar con este resultado: mismo destino, JSON con `clientInfo` y `sourceExtension` de tamaño parecido.

**Qué cambia:** **nada en la decisión.** Sigue la opción A, ahora respaldada por evidencia de red y no solo por la palabra de Google. Se actualizan el punto 3 del ADR-0017 y la brecha 10 de TECH-DESIGN.

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
