# Informe DEV — MIGRACION-FLUTTER

**Contrato:** `docs/contratos/CONTRATO-MIGRACION-FLUTTER.md` v1.4 (M-1 a M-8 del encargo), con CONTRATO-HU-01 v6, HU-02 v4, HU-03 v5, HU-07 v5 y HU-04 v6
**Rama:** `migracion-flutter` (worktree `C:\Willy\Trabajo\MININTER\Movil_Buscador-flutter`)
**Fecha:** 2026-11-24
**Commits del DEV:**

| Commit | Qué |
|---|---|
| `dd08a54` | Interfaz §2 y toda la app en `lib/`; `pubspec.yaml` y `pubspec.lock` con versiones exactas |
| `cd9c3d2` | §5: borrado del código Expo de `apps/movil/` (sin tocar `__tests__/`) |
| `f315ff3` | §6: proyecto Android y `.gitignore` raíz (solo agregar) |
| `a70e627` | Comentarios de `android/` sin mencionar la app anterior por nombre |
| `0a1d93e` | Etiquetas de accesibilidad exactas en los campos con texto de ayuda |
| `0724e88` | M-7 (revisión del UX): obs. 1, círculo de carga de OCR-01 de 76 dp y centrado en el marco; obs. 2, opciones de filtro de BIT-01 a la medida de su texto, varias por fila y 48 dp de alto |
| `36d174a` | M-8 (contrato v1.4): `Cache-Control: no-store` en la API, portado tal cual de `0ccd8fb` (solo `services/api/app/traza.py`) |

Sin push ni merge. Ningún commit lleva `Co-Authored-By`.

---

## 1. SDK instalados (instalación autorizada por el humano, 2026-11-24)

| Qué | Versión | Ruta |
|---|---|---|
| Flutter SDK | **3.50.1**, canal stable, revisión `ae9b586f34`, engine `4d35714800` | `C:\Programas_Portables\flutter_3.50.1\flutter` (agregar `...\flutter\bin` al `PATH`) |
| Dart | **3.14.0** (incluido en Flutter) | ídem |
| Zip de Flutter | `flutter_windows_3.50.1-stable.zip`, sha256 `33c1e3d4dd08f1136ddb9c7976cfd2b0ab20296f1565b78ba176a4cbb4e140eb`, coincide con `releases_windows.json` | Bajado a `C:\Programas_Portables\descargas\` (se puede borrar) |
| Android SDK command-line tools | `commandlinetools-win-16111833` (cmdline-tools 23.0.0) | `C:\Android\cmdline-tools\latest` |
| Android SDK, raíz | — | `C:\Android` (`flutter config --android-sdk C:\Android`). `platform-tools` ya estaba |

**Paquetes del Android SDK instalados** (con `sdkmanager --sdk_root=C:\Android`):

| Paquete | Quién lo instaló | Por qué |
|---|---|---|
| `platforms/android-36` | DEV | compileSdk y targetSdk de Flutter 3.50.1 |
| `platforms/android-37.0` | DEV | `permission_handler_android` 14.1.1 compila contra la API 37 (ver §4) |
| `build-tools/36.0.0` | DEV | `aapt`, `apksigner` |
| `ndk/28.2.13676358` | DEV | `ndkVersion` de Flutter 3.50.1 |
| `cmake/3.22.1` | Gradle, solo, en el primer build | Lo pide el build de un plugin |
| `platforms/android-35` | Gradle, solo, en el primer build | Lo pide el build de un plugin |

**Licencias aceptadas:** `android-sdk-license` (queda en `C:\Android\licenses\`). `flutter doctor --android-licenses`: "All Android licenses accepted".

### `flutter doctor -v` (partes de Flutter y Android)

```
[√] Flutter (Channel stable, 3.50.1, on Microsoft Windows [Versión 10.0.26200.9974], locale es-PE)
    • Flutter version 3.50.1 on channel stable at C:\Programas_Portables\flutter_3.50.1\flutter
    • Upstream repository https://github.com/flutter/flutter.git
    • Framework revision ae9b586f34 (6 days ago), 2026-11-18 17:01:07 -0800
    • Engine revision 4d35714800
    • Dart version 3.14.0
    • DevTools version 2.61.0
[√] Windows Version (Windows 11 or higher, 25H2, 2009)
[√] Android toolchain - develop for Android devices (Android SDK version 36.0.0)
    • Android SDK at C:\Android
    • Emulator version unknown
    • Platform android-37.0, build-tools 36.0.0
    • Java binary at: C:\Program Files\Common Files\Oracle\Java\javapath\java.exe
    • Java version Java(TM) SE Runtime Environment (build 21.0.7+8-LTS-245)
    • All Android licenses accepted.
```

`[!] Visual Studio` también aparece en el doctor: es para compilar apps de escritorio de Windows y no hace falta en este proyecto. No instalé nada para eso.

## 2. Paquetes y versiones (`apps/movil/pubspec.yaml`, todos exactos; `pubspec.lock` versionado)

`environment`: `sdk: 3.14.0`, `flutter: 3.50.1`.

| Paquete | Versión | Código nativo | Para qué |
|---|---|---|---|
| `camera` | 0.12.2 (en Android, `camera_android_camerax` 0.7.6+2) | Sí | Visor y `takePicture()`. **Nunca** `startImageStream` |
| `google_mlkit_text_recognition` | 1.0.3 (con `google_mlkit_commons` 1.0.3) | Sí | OCR en el dispositivo, modelo latino incluido |
| `flutter_secure_storage` | 11.2.0 | Sí | Tokens de la sesión (ADR-0013) |
| `http` | 1.6.0 | No | La interfaz `http.Client` de `clienteHttp` (§2) y el `MockClient` de las pruebas |
| `ok_http` (**v1.5, M-13**) | 0.1.0 (BSD-3-Clause, `dart-lang/http`; trae OkHttp 4.12.0 y Okio, Apache-2.0, y `jni` 0.10.1, BSD-3-Clause) | **Sí** | El `OkHttpClient` del arranque real (`lib/main.dart`). Ver la §12 |
| `clock` | 1.1.3 | No | `clock.now()` para la hora y la inactividad |
| `permission_handler` | 13.0.2 (en Android, `permission_handler_android` 14.1.1) | **Sí** | Ver la justificación abajo |
| `material_ui` | 1.11.1 | No (Dart puro) | Los widgets de Material. Flutter 3.50 marca `package:flutter/material.dart` como obsoleto y la plantilla oficial de `flutter create` usa `material_ui` |
| `flutter_lints` (dev) | 6.0.0 | No | `flutter analyze` |
| `flutter_test`, `integration_test` (dev) | del SDK | — | Para las pruebas del TESTER |

**Justificación de `permission_handler` (código nativo que no está en la lista de la §6):** la §2 pide que `asegurarPermisoCamara()` pida el permiso **sin abrir la cámara**, y que `abrirAjustes()` abra los ajustes de la app (OCR-04). `camera` solo pide el permiso al inicializar la cámara (es decir, abriéndola) y no tiene ninguna función para consultar el estado del permiso ni para abrir los ajustes. `permission_handler` hace las dos cosas (`Permission.camera.status` / `.request()` y `openAppSettings()`). Solo se importa en `lib/bordes/dispositivo.dart`.

**No agregados:** `google_mlkit_face_detection` y `geolocator` (HU-05 y HU-09). Ningún paquete de caché HTTP.

## 3. La app (lo que implementé)

Toda la estructura interna es libre (contrato, "Fuera del contrato"); lo observable sigue la §2 y los contratos de cada HU.

| Ruta | Qué |
|---|---|
| `lib/app.dart` | `MovilBuscadorApp({Key? key, required Dependencias dependencias})`. Una pantalla a la vez, sin pila de navegación. `Key('app-raiz')` en un `Listener` que envuelve todas las pantallas (cualquier toque cuenta como interacción). Safe area una sola vez (§4). "Atrás" del sistema por `didPopRoute` (lo que `handlePopRoute` invoca en `flutter_test`). Segundo plano con `didChangeAppLifecycleState` |
| `lib/main.dart` | Arma las `Dependencias` reales: `String.fromEnvironment('API_URL')`, `http.Client()`, `AlmacenSeguroDispositivo`, `LectorPlacaDispositivo` |
| `lib/bordes/bordes.dart` | Exporta `Dependencias`, `AlmacenSeguro`, `LectorPlaca`, `PermisoCamara`, `LecturaPlaca`, tal cual la §2 |
| `lib/bordes/dispositivo.dart` | Las implementaciones reales: el **único** archivo que importa `camera`, `google_mlkit_text_recognition`, `permission_handler` y `flutter_secure_storage`. La foto se borra en un `finally`; ninguna función devuelve una ruta ni una imagen |
| `lib/sesion/controlador_sesion.dart` | El ciclo de la sesión, portado de `controlador.ts`: login → `/v1/me`; retomar (**M-1**: `POST /v1/auth/refresh` y después `GET /v1/me`; sin token, AUTH-01 sin ninguna solicitud); inactividad con `Timer` y `clock.now()`; renovación; 401 → AUTH-03 o login; 403 `SIN_PERMISO` → ERR-01. Un controlador por montaje: desmontar no borra el almacenamiento; volver a montar con el mismo `AlmacenSeguro` retoma la sesión |
| `lib/api/` | `ClienteApi` (todo por `clienteHttp`) y los modelos escritos a mano desde `contratos/api/openapi.json` (solo los campos que la app usa). Un cuerpo con otra forma es error, nunca resultado (regla 7) |
| `lib/pantallas/` | AUTH-01 a AUTH-04, inicios de los tres roles, ERR-01, PLA-01 a PLA-08, OCR-01 a OCR-04 y BIT-01 y BIT-02, con los textos de la referencia letra por letra |
| `lib/placa/placa_leida.dart` | `proponerPlaca`, con el mismo algoritmo de `placaLeida.ts` (§9) |

**No portado (M-1):** `PantallaEstado` ni `api/salud.ts`.

**Claves internas del almacenamiento:** `sesion.token_acceso` y `sesion.token_renovacion` (las de la referencia). Son internas: nada fuera de `controlador_sesion.dart` depende de ellas (respuesta del LEAD).

**Etiquetas de accesibilidad:** cada campo lleva su etiqueta exacta (`Semantics(container: true, label: …)`) y la etiqueta visible queda fuera del árbol de accesibilidad, como `accessibilityLabelledBy` en Expo, para que `find.bySemanticsLabel` no encuentre dos nodos. Desde `0a1d93e`, el texto de ayuda de un campo ("ABC-123", "Mínimo 10 caracteres", "dd/mm/aaaa") tampoco se suma a la etiqueta. Los botones de un solo símbolo (←, ✕, 📷) llevan "Atrás", "Cerrar" y "Leer con cámara". Los indicadores de espera, "Ingresando" y "Cargando".

### Avisos para el UX

1. **Mayúsculas de los botones.** En Expo, el texto de los botones primarios se veía en MAYÚSCULAS por estilo (`textTransform: 'uppercase'`), pero el texto era "Ingresar", "Consultar", etc. Flutter no tiene esa transformación de estilo y convertir el texto rompería `find.text('Ingresar')` del contrato. Ahora se ven como están escritos ("Ingresar"). Si el UX quiere mayúsculas, hay que decidir cómo sin cambiar el texto del contrato.
2. **Símbolos en las capturas de `flutter_test`.** En `flutter_test` no hay fuentes de respaldo por carácter, así que ←, ✕, 📷, 🚗, ○/◉, ⚠, 🔒 y ⛔ salen como un cuadrado. En el teléfono se ven (Android usa sus fuentes de respaldo). Las capturas del teléfono lo van a mostrar bien.
3. **Margen seguro en las capturas de `flutter_test`.** Simulé una barra de estado de 40 dp y una de gestos de 24 dp para que se vea cómo queda la franja. No sirve como verificación de la §4: esa sale de las capturas del S23 Ultra.

## 4. Build y secretos (§6)

| Caso | Estado | Evidencia |
|---|---|---|
| Versión fijada | Hecho | `pubspec.yaml`: `sdk: 3.14.0`, `flutter: 3.50.1` |
| Dependencias exactas y `pubspec.lock` versionado | Hecho | `dd08a54` |
| `applicationId` y nombre | Hecho | `aapt dump badging`: `package: name='pe.prototipo.movilbuscador'`, `application-label:'Movil Buscador'` |
| `allowBackup="false"` | Hecho | `android/app/src/main/AndroidManifest.xml` (más `dataExtractionRules` que excluye todo, para Android 12+) |
| `network_security_config.xml` a mano | Hecho | `base-config`: solo `system`, `cleartextTrafficPermitted="false"`; `user` solo en `<debug-overrides>` |
| Release no depurable | Hecho | `aapt dump badging app-release.apk` no tiene `application-debuggable`; `app-debug.apk` sí |
| Llave fuera del repositorio | Hecho | Ver abajo. `git ls-files` no muestra ningún `.jks`, `.keystore`, `.pem`, `.crt`, `.key`, `.der`, `.p12`, `key.properties` ni `local.properties` |
| Permisos | Igual que la referencia | `INTERNET`, `CAMERA`. `RECORD_AUDIO`, `READ_EXTERNAL_STORAGE` y `WRITE_EXTERNAL_STORAGE` quitados con `tools:node="remove"` (como `blockedPermissions` de la referencia). `ACCESS_NETWORK_STATE` lo agrega ML Kit (cola de telemetría) |
| Sin "atrás predictivo" | Hecho | `android:enableOnBackInvokedCallback="false"`, como `predictiveBackGestureEnabled: false` de la referencia. Así el "atrás" del sistema siempre llega a la app (PLA y BIT lo manejan) |
| `compileSdk` | **37** (no el 36 de Flutter 3.50.1) | `permission_handler_android` 14.1.1 exige compilar contra la API 37. Solo cambia contra qué API se compila: `targetSdk` sigue en 36 y `minSdk` en 24 (los de Flutter 3.50.1), así que no cambia el comportamiento en el teléfono |
| R8 | `android/app/proguard-rules.pro` | El plugin de ML Kit declara como `compileOnly` los reconocedores de chino, devanagari, japonés y coreano. La app solo usa el latino; las reglas `-dontwarn` evitan que R8 los exija |
| Íconos | Los mismos PNG de la referencia | Movidos de `apps/movil/assets/` a `android/app/src/main/res/drawable-nodpi/` (ícono adaptable en API 26+, `ic_launcher_legacy.png` en API 24 y 25). Son las únicas imágenes de `apps/movil/` |

### Cómo se compila

Desde `apps/movil/`, con `C:\Programas_Portables\flutter_3.50.1\flutter\bin` en el `PATH`:

```
flutter pub get
flutter build apk --debug   --dart-define=API_URL=https://localhost:8443
flutter build apk --release --dart-define=API_URL=https://localhost:8443
```

Para un teléfono conectado: `flutter run --debug --dart-define=API_URL=https://localhost:8443`.

Salida: `apps/movil/build/app/outputs/flutter-apk/app-debug.apk` y `app-release.apk` (78,5 MB; lleva las tres ABI). `build/` no se versiona.

**APK de la M-13 (contrato v1.5; reemplazados por los de la M-15, §13)**, compilados con el árbol de `29617a7` y copiados a `C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\`, con `SHA256SUMS.txt` nuevo (verificado con `sha256sum -c`). Reemplazan a los de abajo:

| APK | sha256 | Tamaño (antes → después) |
|---|---|---|
| `movil-buscador-debug.apk` | `6d6b040554204fc603665dad8246c605df327a3855d0f748785a42b995bef3c8` | 236 872 366 → 236 277 571 bytes |
| `movil-buscador-release.apk` | `48f8117a841e4dbbbd735c95062c9ce5f2ff5b1f4f5ce779d6852e991d2ed008` | 82 266 821 → 82 177 616 bytes |

**APK anteriores (M-6, M-7 y M-8, reemplazados por la M-13)**, compilados con el árbol de `3bcee92` (el commit del TESTER con la prueba del no-store, encima de mi `36d174a`; el código de la app es el de `0724e88`) y copiados fuera del repositorio a `C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\`, con `SHA256SUMS.txt` (verificado con `sha256sum -c`):

| APK | sha256 |
|---|---|
| `movil-buscador-debug.apk` | `987be377aad06c985a25f19ef2571656037c367b08290eccaafe204074d40cc1` |
| `movil-buscador-release.apk` | `3528cb541c73c4fce4b1e70f62bdb0a012c492ec70f8227925e20e1512950381` |

Reemplazan a los de `0a1d93e` (`4e92ae28…` y `9d753eb9…`).

El primer build tardó unos 25 min (Gradle 9.5.0 y las dependencias se bajan una vez); los siguientes, menos de 2 min.

### La llave de firma

- **Dónde vive:** `C:\Users\Willy\.movil-buscador-firma\movil-buscador-release.jks` (PKCS12, RSA 4096, alias `movilbuscador`, válida 10 años, `CN=Movil Buscador (prototipo con datos sinteticos), O=Prototipo, C=PE`). La clave está en `C:\Users\Willy\.movil-buscador-firma\key.properties`. Las dos fuera del repositorio.
- **Huella del certificado (SHA-256):** `12:8B:C0:1A:D2:4A:BB:69:75:53:08:18:FE:FC:89:11:93:5A:BA:76:47:99:9A:C9:A3:CA:12:4D:1F:1D:EF:60`. `apksigner verify --print-certs app-release.apk` da la misma.
- **Cómo la usa el build:** `android/app/build.gradle.kts` lee `apps/movil/android/key.properties` (una copia del archivo de arriba, ignorada por git: `git check-ignore` → `apps/movil/android/.gitignore:12:key.properties`). Si ese archivo no existe, el APK de release sale **sin firmar**. Nunca se firma con la llave de depuración.
- **Cómo se borra al cierre (para el acta):** borrar la carpeta `C:\Users\Willy\.movil-buscador-firma\` y el archivo `apps/movil/android/key.properties` de cada copia de trabajo donde exista (hoy solo en `Movil_Buscador-flutter`). En PowerShell: `Remove-Item -Recurse -Force "$env:USERPROFILE\.movil-buscador-firma"` y `Remove-Item C:\Willy\Trabajo\MININTER\Movil_Buscador-flutter\apps\movil\android\key.properties`. Con eso, ningún APK nuevo puede firmarse con esa identidad.

## 5. ML Kit: el modelo dentro del APK (§7, contrato v1.2, M-3)

Lo reporté como hueco; el humano (vía PM) decidió la **opción A** (contrato v1.2, M-3 del encargo): la §7 pide el modelo de ML Kit dentro del APK, no que falte `play-services-mlkit-*`. **No excluí nada.** Lo que esa dependencia transitiva haga en la red queda **NO VERIFICADO**; la cola `datatransport` se revisa en la mini sesión del 4-dic.

**1. El `build.gradle` del plugin, en la versión fijada** (`google_mlkit_text_recognition-1.0.3/android/build.gradle`, en la caché de pub):

```
    dependencies {
        implementation("com.google.mlkit:text-recognition:16.0.1")
        compileOnly("com.google.mlkit:text-recognition-chinese:16.0.1")
        compileOnly("com.google.mlkit:text-recognition-devanagari:16.0.1")
        compileOnly("com.google.mlkit:text-recognition-japanese:16.0.1")
        compileOnly("com.google.mlkit:text-recognition-korean:16.0.1")
    }
```

Y en `google_mlkit_commons-1.0.3`: `implementation("com.google.mlkit:vision-common:17.3.0")`. Es la variante empaquetada (`com.google.mlkit:text-recognition`), **no** `com.google.android.gms:play-services-mlkit-text-recognition`.

**2. Pero el árbol del APK** (`./gradlew :app:dependencies --configuration releaseRuntimeClasspath`, desde `apps/movil/android/`) muestra que el propio artefacto empaquetado, por su POM oficial de Google, depende de dos artefactos de Play services:

```
+--- project :google_mlkit_text_recognition
|    +--- com.google.mlkit:text-recognition:16.0.1
|    |    +--- com.google.android.gms:play-services-base:18.5.0 (*)
|    |    +--- com.google.android.gms:play-services-basement:18.4.0 (*)
|    |    +--- com.google.android.gms:play-services-mlkit-text-recognition:19.0.1
|    |    |    +--- ...
|    |    |    +--- com.google.android.gms:play-services-mlkit-text-recognition-common:19.1.0
|    |    |    |    +--- com.google.android.datatransport:transport-api:2.2.1 (*)
|    |    |    |    +--- com.google.android.datatransport:transport-backend-cct:2.3.3 (*)
|    |    |    |    +--- com.google.android.datatransport:transport-runtime:2.2.6 (*)
|    |    |    |    +--- ...
|    |    |    \--- com.google.mlkit:common:18.11.0 (*)
|    |    +--- com.google.mlkit:common:18.11.0 (*)
|    |    \--- com.google.mlkit:text-recognition-bundled-common:17.0.0
```

El POM publicado en `https://dl.google.com/android/maven2/com/google/mlkit/text-recognition/16.0.1/text-recognition-16.0.1.pom` lo confirma: sus dependencias son `play-services-base`, `play-services-basement`, `play-services-mlkit-text-recognition`, `common` y `text-recognition-bundled-common`.

**3. El modelo va dentro del APK** (`unzip -l app-release.apk`), así que la lectura no depende de que Play services baje un modelo:

```
11064544 lib/arm64-v8a/libmlkit_google_ocr_pipeline.so
 6781940 lib/armeabi-v7a/libmlkit_google_ocr_pipeline.so
11626128 lib/x86_64/libmlkit_google_ocr_pipeline.so
assets/mlkit-google-ocr-models/aksara/… (2 archivos)
assets/mlkit-google-ocr-models/gocr/gocr_models/line_recognition_legacy_mobile/Latn_ctc/… (LabelMap.pb, conv_model.fb, lstm_model.fb)
assets/mlkit-google-ocr-models/gocr/gocr_models/line_recognition_legacy_mobile/Latn_ctc_cpu.binarypb
assets/mlkit-google-ocr-models/gocr/gocr_models/line_recognition_legacy_mobile/tflite_langid.tflite
assets/mlkit-google-ocr-models/gocr/layout/line_clustering_custom_ops/model.tflite
assets/mlkit-google-ocr-models/gocr/layout/line_splitting_custom_ops/model.tflite
assets/mlkit-google-ocr-models/taser/… (detector, segmenter y script identification)
assets/mlkit-google-ocr-models/taser_tflite_gocrlatin_mbv2_scriptid_aksara_layout_gcn_mobile_*.binarypb (5 archivos)
```

**4. Calidad facial (HU-05, no agregado):** `google_mlkit_face_detection` 1.0.3 (`android/build.gradle`) declara `implementation("com.google.mlkit:face-detection:16.1.7")`, la variante empaquetada. Su POM oficial tiene el mismo patrón: depende de `play-services-mlkit-face-detection` (además de `transport-api`, `transport-backend-cct`, `transport-runtime`, `play-services-base`, `play-services-basement`, `play-services-tasks`, `firebase-components`, `firebase-encoders`, `firebase-encoders-json` y `common`). El paquete solo se bajó a la caché de pub (`dart pub cache add`) para leer su `build.gradle`; no está en `pubspec.yaml`.

**Telemetría:** sigue la decisión A. El aviso de OCR-01 está implementado con el texto de HU-04 v5. La cola `datatransport` se revisa en el teléfono (mini sesión).

## 6. Comprobaciones del repositorio que corrí (las oficiales son del TESTER)

| Comprobación | Resultado |
|---|---|
| `flutter analyze lib` (desde `apps/movil/`) | `No issues found!` |
| `git ls-files apps/movil` sin `.ts` ni `.tsx` fuera de `__tests__/` | 0 archivos. `__tests__/` sigue: lo borra el TESTER |
| `grep -riw "expo\|react-native" apps/movil --include=*.yaml --include=*.gradle* --include=*.xml` (contrato v1.3, M-4) | Vacío. (Con `grep -ri`, sin `-w`, salía `android:exported="true"`, un falso positivo que reporté) |
| `grep -r startImageStream apps/movil/lib` | Vacío |
| Imports de `camera`, `google_mlkit_*`, `permission_handler`, `flutter_secure_storage`, `dart:io` `HttpClient` o `dio` fuera de `lib/bordes/` | Ninguno |
| Paquetes de caché en `pubspec.yaml` y `pubspec.lock` | Ninguno |
| Secretos en `git ls-files` | Ninguno |

`flutter analyze` sobre todo `apps/movil/` también analiza `test/`, que es del TESTER. En mi primera corrida (antes de saber que ya había pruebas) vi en la salida errores de sus archivos; no los abrí ni los corrí. Desde entonces analizo solo `lib/`.

**`flutter create`** generó `test/widget_test.dart` (ruta del TESTER). Lo borré antes de cualquier commit; nunca se versionó.

## 7. Cómo lo comprobé a mano

Sin leer ni correr las pruebas del TESTER: un paquete aparte, fuera del repositorio (`C:\Users\Willy\AppData\Local\Temp\claude\c39409f218ea2544\c970638d-ae90-4530-b94a-5de7abc13d98\scratchpad\verif_dev`), que depende de `movil_buscador` por ruta y monta `MovilBuscadorApp` con un `MockClient` y dobles propios. Comprobé:

- Sin token: AUTH-01 y ninguna solicitud. Login → `/v1/me` → HOME-01.
- Desmontar y volver a montar con el mismo `AlmacenSeguro`: exactamente `POST /v1/auth/refresh` y después `GET /v1/me`, y HOME-01 (M-1).
- PLA-01 → 📷 → aviso de ML Kit → "Entendido" → "Capturar" (una llamada a `capturarYLeer`) → OCR-02 → "Usar esta placa": ninguna solicitud entre 📷 y "Consultar".
- "Consultar" → PLA-06; "atrás" (`handlePopRoute`) → PLA-01; "atrás" → HOME-01.
- "Salir" → AUTH-01 y `leerTodo()` vacío.
- 403 `SIN_PERMISO` → ERR-01; "atrás" → inicio.
- Inactividad con `pump`: un toque en `Key('app-raiz')` a los 599 s reinicia el plazo; 600 s sin tocar → AUTH-03 y `leerTodo()` vacío.
- Todas las etiquetas de la §2 se encuentran con `find.bySemanticsLabel` (de ahí salió `0a1d93e`).

Ese mismo paquete genera las capturas para el UX.

## 8. Capturas para el UX (fuera del repositorio)

**`flutter_test`** (390 × 844 dp, ×3): `C:\Willy\Trabajo\MININTER\Movil_Buscador_capturas\MIGRACION-FLUTTER\flutter_test\` — 32 PNG (M-7: se agregaron PLA-01-sin-catalogo y BIT-01-fecha-invalida, y se regeneraron OCR-01-leyendo y BIT-01-filtros con las correcciones; el resto se regeneró igual). Las 30 originales:

AUTH-01, AUTH-01-vacios, AUTH-02, AUTH-03, AUTH-04, AUTH-otro-error · HOME-01-agente, HOME-revisor, HOME-supervisor · ERR-01 · PLA-01, PLA-02-sin-motivo, PLA-02-otro-corto-y-PLA-03-formato, PLA-04-consultando, PLA-05-con-requisitoria, PLA-06-sin-requisitoria, PLA-07-error, PLA-08-no-registrada, PLA-01-con-placa-leida · OCR-01-aviso-mlkit, OCR-01, OCR-01-leyendo, OCR-02, OCR-03, OCR-04 · BIT-01, BIT-01-filtros, BIT-01-vacia, BIT-01-error, BIT-02.

Todos los datos de las capturas son sintéticos (placas `ZZ…`, nombres inventados). Ver los avisos para el UX del §3 (mayúsculas, símbolos, margen simulado).

**Del S23 Ultra (§4: OCR-01 con el visor, OCR-02, PLA-01 y HOME-01): NO VERIFICADO.** No había ningún teléfono conectado (`adb devices` vacío). Se sacan cuando esté el teléfono; van a `C:\Willy\Trabajo\MININTER\Movil_Buscador_capturas\MIGRACION-FLUTTER\s23\`.

## 9. Pasos para el humano (HU-04 v6 §8), en el S23 Ultra

Con el compose local levantado desde `Movil_Buscador-flutter` (encargo, regla 8) y el proxy publicado en el 8443 (`PROXY_PUERTO_HTTPS=8443` en `infra/.env`):

1. **Desinstalar la app de Expo** (tiene otra firma y el APK nuevo no se instala encima):
   `C:\Android\platform-tools\adb.exe uninstall pe.prototipo.movilbuscador`
2. **Sacar la CA local de Caddy** a una carpeta fuera del repositorio:
   `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env cp proxy:/data/caddy/pki/authorities/local/root.crt C:\Willy\Trabajo\MININTER\ca-local\caddy-root.crt`
3. **Instalarla en el teléfono como certificado del usuario:** `adb push C:\Willy\Trabajo\MININTER\ca-local\caddy-root.crt /sdcard/Download/` y en el teléfono: Ajustes › Seguridad y privacidad › Más ajustes de seguridad › Instalar desde el almacenamiento › Certificado de CA. Después borrar el archivo de `Download/`.
4. **Conectar el puerto:** `adb reverse tcp:8443 tcp:8443`.
5. **Instalar y abrir el APK de depuración:** `adb install apps\movil\build\app\outputs\flutter-apk\app-debug.apk` (o `flutter run --debug --dart-define=API_URL=https://localhost:8443` desde `apps/movil/`). La app confía en la CA del usuario solo en este APK (`<debug-overrides>`).
6. **Al cierre:** en el teléfono, Ajustes › Seguridad y privacidad › Más ajustes de seguridad › Ver certificados de seguridad › Usuario › quitar la CA de Caddy; `adb reverse --remove-all`; borrar `C:\Willy\Trabajo\MININTER\ca-local\`.

El APK de release no confía en la CA del usuario: contra la API local con Caddy no va a conectar, y es lo esperado (sirve para la demo con DESPLIEGUE-01 v2).

## 9 bis. Compose para la mini sesión (M-8)

Con la autorización del humano, bajé el compose de la carpeta principal con el comando exacto de la M-8 (`down`, sin `-v`) y lo levanté desde `Movil_Buscador-flutter` con `up -d --build`. Queda **levantado** para la mini sesión. Comprobado: `https://localhost:8443/v1/salud` → `200` con `Cache-Control: no-store`; `GET /v1/me` sin token → `401`, también con `no-store`; la CA de Caddy se copia con el comando del paso 2 (lo probé y borré la copia). `infra/.env` está copiado de la carpeta principal (con `PROXY_PUERTO_HTTPS=8443`) y lo ignora git.

## 10. Lo que queda NO VERIFICADO o pendiente

| Qué | Por qué | Cuándo |
|---|---|---|
| Todo lo del S23 Ultra: safe area (§4), la foto se borra, sin caché en disco, cola de telemetría, la placa impresa se lee, permiso real, 30 s sin lectura, conexión con la CA de Caddy | No había teléfono conectado | Mini sesión (4-dic) o antes, en cuanto esté el teléfono |
| La app contra la API real (sin `MockClient`) | Sin teléfono ni emulador (no instalé imágenes de emulador: no estaban en la autorización) | Con el teléfono |
| §7: lo que hace en la red la dependencia transitiva `play-services-mlkit-*` (opción A, M-3) | Decisión del humano: no se excluye y queda NO VERIFICADO | Cola `datatransport` en la mini sesión del 4-dic |
| §1.3 (pytest de la API y de los simuladores) | Es del TESTER; no toqué `services/` ni `contratos/` | Suite completa con orden del LEAD |

## 11. Para el arnés de pruebas

- Desde `0a1d93e`, las etiquetas de los campos con ayuda son exactas: "Placa", "Describa el motivo *", "Desde" y "Hasta" (antes llevaban la ayuda sumada).
- La app importa `package:material_ui/material_ui.dart`; los widgets de `package:flutter/widgets.dart` son los mismos.
- No hay variables de entorno nuevas aparte de `--dart-define=API_URL`. No hay migraciones.

## 12. M-13 (contrato v1.5): cliente `ok_http`

**Por qué:** ROJO del paso 1.2 en la S23 (M-12). `http.Client()` es `dart:io` y su TLS (BoringSSL) no lee el `network_security_config` ni las CA de usuario. Caddy registró `http: TLS handshake error from 172.20.0.1:48884: EOF` y no llegó ningún acceso a `/v1/auth/login`.

**Commits:** `a15535f` (pubspec, lock, `main.dart`, `android/build.gradle.kts`) y `29617a7` (`android/app/proguard-rules.pro`). Opción A. No hizo falta el plan B.

| Qué | Cómo |
|---|---|
| Versión | `ok_http: 0.1.0` exacta. Es la **única** publicada en pub.dev (agosto de 2024) y pide `jni ^0.10.1`. Licencia BSD-3-Clause (`LICENSE` del paquete: "Copyright 2014, the Dart project authors") |
| Cambios transitivos en `pubspec.lock` | Entran `ok_http` 0.1.0, `http_profile` 0.1.0 y `web_socket` 0.1.6. Bajan `jni` (1.2.1 → 0.10.1), `path_provider_android` (2.3.1 → 2.2.23) y `package_config` (3.0.0 → 2.2.0) para cumplir `jni ^0.10.1`. Salen `jni_flutter` 1.1.0 y `jni_util` 1.0.0. Ninguna dependencia directa cambia de versión |
| El cliente sin caché | `lib/main.dart`: `clienteHttp: OkHttpClient()`. El constructor de `ok_http` 0.1.0 hace `bindings.OkHttpClient.new1()`, es decir, `new OkHttpClient()` de OkHttp con su configuración por defecto, que **no tiene `Cache`** (en el paquete, `cache` solo aparece en `close()`, para cerrarla si existiera). No se llama a `newBuilder().cache(...)` en ningún lado. La interfaz `clienteHttp` (§2) y el `network_security_config` no cambian |
| `compileSdk` de los módulos `jni` y `ok_http` | `android/build.gradle.kts`: solo para esos dos módulos, `compileSdkVersion(37)` en `afterEvaluate`. Sin eso falla `checkDebugAarMetadata`: "`androidx.window.extensions.core:core:1.0.0` requires … compile against version 33 or later … `:jni` is currently compiled against android-31". No cambia `minSdk` ni `targetSdk` |
| R8 (release) | `proguard-rules.pro`: `-keep class okhttp3.** { *; }`, `-keep class okio.** { *; }` y `-keep class com.example.ok_http.** { *; }`. `ok_http` busca esas clases **por nombre** desde Dart por JNI (`okhttp3/OkHttpClient`, …). En el primer release, sin las reglas, el `classes.dex` no tenía `Lokhttp3/OkHttpClient;` (solo la nombraba `libapp.so`): el release habría fallado al arrancar. Con las reglas, las tres familias están en el dex de los dos APK |
| Aviso de Flutter | `WARNING: Your app uses the following plugins that apply Kotlin Gradle Plugin (KGP): ok_http … Future versions of Flutter will fail to build`. Con 3.50.1 compila. Queda como riesgo si se cambia de Flutter (la versión está fijada hasta el cierre del MVP, ADR-0017 regla 5) |
| Comprobaciones | `flutter analyze`: sin avisos. `flutter test`: 137/137 (lo pide la M-13). `aapt dump badging` del release: sin `application-debuggable`, `package: name='pe.prototipo.movilbuscador'`, `application-label:'Movil Buscador'`. `apksigner`: `CN=Movil Buscador (prototipo con datos sinteticos), O=Prototipo, C=PE`. `unzip -l` del release: 21 entradas en `assets/mlkit-google-ocr-models/` y `libmlkit_google_ocr_pipeline.so` en las tres ABI |
| **Ninguna CA en un APK** | `unzip -l` de los dos APK: ningún `.crt`, `.pem`, `.der`, `.cer`, `.p12` ni `.bks`. Además, dentro de **cada** entrada descomprimida de los dos APK (574 del de depuración y 339 del de release), busqué el DER de `C:\Willy\Trabajo\MININTER\ca-local\caddy-root.crt`, los primeros 64 caracteres de su base64 y el texto "Caddy Local Authority": **ninguna coincidencia** |

**Cómo se prueba a mano (en el S23, cuando el PM lo pida):** desde el paso 0.8 del guion. Con el de depuración (`6d6b0405…`), iniciar sesión con `agente1` entra (la CA de usuario ya está instalada) y Caddy registra un acceso a `/v1/auth/login`. Con el de release (`48f8117a…`), el inicio de sesión muestra "No se pudo completar la operación; intente nuevamente" (falla el TLS). **NO VERIFICADO todavía en el teléfono**, porque la M-13 no pide instalarlo.

**Para el arnés:** no cambia ninguna prueba (siguen inyectando `MockClient`). El paso 8 del guion (caché de OkHttp en `cache/` y `files/`) y el paso 11 (login con el release) los pone el TESTER. No hay variables de entorno nuevas ni migraciones.

## 13. M-15: lo que dejó la S23 (obs. 7, 5 y 6 del UX)

**Commit:** `d81c6f9` (`lib/pantallas/pantalla_bitacora.dart`, `lib/pantallas/pantalla_ocr.dart` y `lib/pantallas/comunes.dart`). HU-04 v7 no cambia el código.

### Obs. 7 (BLOQUEA): "Desde" y "Hasta" con "/" en el S23

- **Qué pasaba:** los dos campos pedían `TextInputType.datetime`. En el S23, Samsung Keyboard da para ese tipo un teclado de solo dígitos, sin "/", y `25/11/2026` quedaba `25112026` (M-14, S14).
- **Qué hice:** el teclado queda igual (los dígitos grandes son lo cómodo, y en Gboard ese teclado sí trae "/"). A los dos campos les agregué un formateador, `_BarraDeFecha`, que pone la "/" solo mientras se escribe la fecha: cuando se agrega **un dígito al final** y con eso quedan `ddd` o `dd/mmm`, inserta la barra antes de ese dígito (`251` → `25/1`, `25/112` → `25/11/2`). Así, tocando 2-5-1-1-2-0-2-6 queda `25/11/2026`, sin cambiar de teclado.
- **Por qué así y no otro teclado:** no hay un `TextInputType` que garantice "/" en todos los teclados de Android (`numbers-and-punctuation` de Expo no existe en Android: allí cae al teclado de texto, donde la "/" está en la página de símbolos). Lo único que no depende del teclado es poner la barra desde la app. Además, `CampoTexto` acepta ahora una lista opcional `formateadores` (`inputFormatters` del `TextField`); los demás campos no la usan.
- **Lo que no cambia (CONTRATO-HU-07 v3):** el formateador **no toca** nada más. Borrar, escribir uno mismo la "/" (en los teclados que la tienen), letras, otros formatos o pegar el texto entero pasan tal cual, así que una fecha que no cumple `dd/mm/aaaa` sigue mostrando "Use fechas con el formato dd/mm/aaaa." y no envía la solicitud. La ayuda "dd/mm/aaaa" y los textos tampoco cambian.
- **Cómo lo comprobé, sin teléfono** (la M-15 dice que no se instala): con una copia de la lógica en un script de Dart fuera del repositorio, tecla por tecla: `25112026` → `25/11/2026`; `25/11/2026` escrito con "/" → igual; borrar hasta `25/1` y seguir funciona, sin trabarse en la barra; `ayer` → `ayer`; pegar `2026-11-25`, `25/11/2026` o `25112026` → sin cambios; un noveno dígito → `25/11/20261` (inválido, muestra el error). **NO VERIFICADO en el S23:** queda para la tercera vuelta (S14).

### Obs. 5 (MEJORA): barra de desplazamiento en la tarjeta del aviso

En OCR-01, el `SingleChildScrollView` de la tarjeta "Antes de leer la placa" va dentro de un `Scrollbar` con `thumbVisibility: true` y su propio `ScrollController` (se libera en `dispose`). Sin texto nuevo. Con la letra normal la tarjeta entra entera y la barra no se nota; con la letra al máximo (S7) se ve que hay más abajo.

### Obs. 6 (MEJORA): la franja con la letra al máximo

`FranjaPrototipo`: `textAlign: TextAlign.center` y relleno lateral de 16 dp (`EdgeInsets.symmetric(vertical: 6, horizontal: 16)`). No se limita el tamaño de la letra.

### Comprobaciones

- `flutter analyze`: sin avisos. `flutter test`: **137/137** (ninguna prueba se puso roja).
- **APK nuevos** (árbol de `d81c6f9`), en `C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\`, con `SHA256SUMS.txt` nuevo (`sha256sum -c`: OK). Reemplazan a `6d6b0405` y `48f8117a`. **No se instalaron.**

| APK | sha256 | Tamaño (M-13 → M-15) |
|---|---|---|
| `movil-buscador-debug.apk` | `5f62f6a4c8eb192e38bddd3895409a84325f12e914c69b1fc1801ad08b997085` | 236 277 571 → 236 279 013 bytes |
| `movil-buscador-release.apk` | `65799fb64635fc424efab1c255f5202a729a6da68a8d28aa0c16d67184c6bdc6` | 82 177 616 → 82 325 072 bytes |

- **Ninguna CA en un APK:** ningún `.crt`, `.pem`, `.der`, `.cer`, `.p12` ni `.bks`; ni el DER, ni el base64 ni "Caddy Local Authority" en ninguna entrada descomprimida (574 y 339) ni en el archivo crudo.
- **Release:** sin `application-debuggable`; `package: name='pe.prototipo.movilbuscador'`, `application-label:'Movil Buscador'`; firma `CN=Movil Buscador (prototipo con datos sinteticos), O=Prototipo, C=PE`; 21 entradas en `assets/mlkit-google-ocr-models/` y `libmlkit_google_ocr_pipeline.so` en las tres ABI; `Lokhttp3/OkHttpClient;`, `Lokio/Buffer;` y `Lcom/example/ok_http/` en el dex (las reglas `-keep` de la M-13 siguen sirviendo). El de depuración sí es depurable.

### Entorno (M-15 punto 7)

El log del proxy volvió a lo normal: dentro del contenedor, `caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile` recargó la configuración versionada, que no tiene `logging` ni log de acceso (la API de administración devuelve `null` en los dos). No se tocó el Caddyfile. Después de la recarga, `/v1/salud` da 200 y no aparecen líneas `debug` ni de acceso. **El compose sigue arriba** (no se corrió el 12.4).

**Para el arnés:** ninguna prueba cambia. El S14 de la tercera vuelta tiene que dejar `25/11/2026` tocando solo dígitos. En el teléfono quedó el release `48f8117a` de la M-14: para la tercera vuelta hay que desinstalarlo e instalar el de depuración `5f62f6a4` (desde el 0.8).

