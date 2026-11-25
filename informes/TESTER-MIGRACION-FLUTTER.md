# Informe TESTER — MIGRACION-FLUTTER

**Contrato:** `docs/contratos/CONTRATO-MIGRACION-FLUTTER.md` **v1.4** (con la M-1 a la M-9 del encargo), CONTRATO-HU-01 v6, HU-02 v4, HU-03 v5, HU-07 v5 y HU-04 v6.
**Encargo:** `docs/contratos/ENCARGO-MIGRACION-FLUTTER.md` (M-1 a M-9).
**Rama:** `migracion-flutter`, worktree `C:\Willy\Trabajo\MININTER\Movil_Buscador-flutter`.
**Estado:** **corrida M-9** sobre `6790594` (M-7 del DEV en `0724e88`, M-8 en `36d174a`), solo lo tocado: `flutter test` 137/137, `repositorio_test` 17/17, §1.3 v1.4 en verde y los dos APK nuevos en verde. **Pendiente:** `test_hu04_sin_cache.py` contra el compose, **bloqueado** porque pytest no está instalado en el anfitrión (escalado al humano por el LEAD; llega como M-n). Lo del teléfono queda `NO VERIFICADO` hasta la mini sesión del miércoles 25-nov. Antes: `ENTREGA TESTER` parcial M-5.

## 0. Corrida M-9 (2026-11-24, sobre `6790594`)

| Paso de la M-9 | Comando | Resultado |
|---|---|---|
| 1 | `PROXY_DISPONIBLE=1 python -m pytest services/api/tests/test_hu04_sin_cache.py --integracion --url-base https://localhost:8443` (14 casos por la red interna y 14 por el proxy), con el compose arriba desde esta carpeta (`https://localhost:8443/v1/salud` → `200`) | **NO EJECUTADO, bloqueado:** `No module named pytest` en el Python del anfitrión (`Python313`); no hay venv en las carpetas del proyecto. Pregunté al LEAD; lo escaló al humano con la propuesta de un venv en `C:\Willy\Trabajo\MININTER\venv-pruebas` (fuera del repositorio) con solo `pytest==9.2.0`. No instalé nada |
| 2 | `flutter analyze` en `apps/movil` | **`No issues found!`** |
| 2 | `flutter test` en `apps/movil` | **`+137: All tests passed!`** (120 de la app y 17 de `repositorio_test`) |
| 2 | §1.3 v1.4: `git diff --stat main...HEAD -- services/ contratos/` | Solo `services/api/app/traza.py` (DEV, `36d174a`) y `services/api/tests/test_hu04_sin_cache.py` (TESTER, `3bcee92`). Las líneas cambiadas de `traza.py` son **las mismas** que en `0ccd8fb` (comparadas con `diff`) |
| 3 | `sha256sum -c SHA256SUMS.txt` en `C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\` | `movil-buscador-debug.apk: OK` (`987be377…40cc1`), `movil-buscador-release.apk: OK` (`3528cb54…50381`) |
| 3 | `aapt dump badging` (build-tools 36.0.0) | Los dos: `package: name='pe.prototipo.movilbuscador'`, `application-label:'Movil Buscador'`. Líneas `debuggable`: **release 0**, debug 1 (control) |
| 3 | `aapt dump xmltree <apk> AndroidManifest.xml` | Los dos: `allowBackup` 0x0, `usesCleartextTraffic` 0x0, `networkSecurityConfig` presente |
| 3 | `python -I pruebas/datos/revisar_modelo_apk.py <apk>` (§7 v1.2) | Los dos: **modelo dentro** (21 archivos en `assets/mlkit-google-ocr-models/` y `libmlkit_google_ocr_pipeline.so` en 3 ABI); `play-services-mlkit-*` sin rojo (v1.2), red `NO VERIFICADO` |
| 3 | `apksigner verify --print-certs` | Release: `CN=Movil Buscador (prototipo con datos sinteticos), O=Prototipo, C=PE`. Debug: `CN=Android Debug` |
| 4 | El compose | **Quedó arriba**, como pide la M-9. No lo toqué |

**Control propio sobre el APK de release.** Su tamaño (82 266 821 bytes) es igual al del release anterior a la M-7, aunque su SHA-256 cambió. Compilé un release sin firmar desde `6790594` en un worktree temporal, fuera del repositorio y ya borrado: pesa 82 254 533 bytes, **igual** que el que compilé desde `fb3869b` en la M-5. La M-7 no cambia el tamaño del APK, así que el tamaño igual no es una señal de problema. Comparar `libapp.so` byte a byte con el entregado no sirve: el binario guarda la ruta de compilación (`…\wt-m9\…` en el mío, `…\Movil_Buscador-flutter\…` en el del DEV). Que el entregado sale de `0724e88` queda respaldado por el informe del DEV (`20761dd`) y el `SHA256SUMS` que verificó el LEAD.

## 0 bis. Corrida M-5 (2026-11-24, sobre la ENTREGA DEV)

| Paso de la M-5 | Comando | Resultado |
|---|---|---|
| 1 | `flutter analyze` en `apps/movil` (todo el paquete: `lib/` y `test/`) | **`No issues found!`** |
| 1 | `flutter test` en `apps/movil` (las 7 suites) | **`+137: All tests passed!`**: 120 de la app y 17 de `repositorio_test` |
| 2 | `repositorio_test` completo, con `android/` en el repositorio | **17/17** (§2 imports y clientes HTTP, `clock.now()`; §5 sin Expo ni TypeScript y `grep -riw` de la v1.3; §6 Flutter 3.50.1, versiones exactas, `pubspec.lock`, paquetes, sin caché, sin `startImageStream`, `applicationId`, "Movil Buscador", `allowBackup`, `network_security_config.xml`, `.gitignore`; reglas 1 y 8) |
| 2 | `git ls-files` sin `.crt`, `.pem`, `.key`, `.der`, `.jks`, `.keystore`, `.p12`, `key.properties` ni `local.properties` | **Vacío** |
| 2 | `git ls-files apps/movil` con imágenes | Solo los 4 íconos de `android/app/src/main/res/drawable-nodpi/ic_launcher_*.png` (regla 8: permitidos) |
| 2 | `git ls-files apps/movil` con `.ts`, `.tsx`, `package.json` o `__tests__/` | **Vacío** |
| 2 | `grep -riw "expo\|react-native" apps/movil --include=*.yaml --include=*.gradle* --include=*.xml` (v1.3) | **Vacío** (código 1) |
| 2 | `grep -rw startImageStream apps/movil/lib` | **Vacío** (código 1) |
| 2 | `git diff --stat main...HEAD -- services/ contratos/` (§1.3) | **Vacío** |
| 3 | APK de release **compilado por el TESTER** desde `fb3869b` con el comando del informe del DEV (`flutter build apk --release --dart-define=API_URL=https://localhost:8443`), en un worktree temporal fuera del repositorio (ya borrado), **sin** la llave de firma (sale sin firmar; no cambia lo que se mide) | `√ Built … app-release.apk (78.4MB)` |
| 3 | `aapt dump badging` (build-tools 36.0.0) sobre ese APK | `package: name='pe.prototipo.movilbuscador'`, `application-label:'Movil Buscador'`, **0 líneas `debuggable`** |
| 3 | `aapt dump xmltree <apk> AndroidManifest.xml` | `allowBackup` 0x0, `usesCleartextTraffic` 0x0, `networkSecurityConfig` presente |
| 3 | `python -I pruebas/datos/revisar_modelo_apk.py <apk>` (§7 v1.2, M-3) | **Modelo dentro:** 21 archivos en `assets/mlkit-google-ocr-models/` y `libmlkit_google_ocr_pipeline.so` en `arm64-v8a`, `armeabi-v7a` y `x86_64`. `play-services-mlkit-text-recognition` y `-common` (`.properties`): **no es rojo** (v1.2); su comportamiento en la red queda `NO VERIFICADO` |
| 3 | Lo mismo sobre el `app-release.apk` firmado del DEV en `build/` (SHA-1 `6659053b52c3…`) | Igual (corrida preliminar de la M-3) |
| 4 | Lo del teléfono (safe area, HU-04 v6 §6 y §8, cola `datatransport`) | `NO VERIFICADO` hasta la mini sesión del 25-nov (guion `pruebas/datos/GUION-MIGRACION-FLUTTER-dispositivo.md`) |

**Arreglos de mis pruebas en esta corrida (`95741fa`):** `repositorio_test` recorría `build/` con `listSync(recursive: true)` y se rompía con una ruta de Gradle que Windows no puede listar (`PathNotFoundException`, 2 rojos que no eran de la app). Ahora no entra en `build/`, `.dart_tool/`, `.gradle/` ni `node_modules/`, que no son del repositorio. No cambia lo que se verifica.

## 0 ter. Corrida 1 (2026-11-24, contra `dd08a54`)

| Qué | Resultado |
|---|---|
| `flutter analyze test` | `No issues found!` |
| `flutter test test/hu01_hu02_test.dart test/hu01_retomar_test.dart test/hu03_hu07_test.dart test/hu04_ocr_test.dart test/red_sin_cache_test.dart` | **`+120: All tests passed!`** |
| `flutter test test/repositorio_test.dart` (árbol de trabajo) | 11 verdes, 5 rojos de trabajo en curso: quedan `.tsx` en `__tests__/` (los borra el TESTER), y en `android/` (plantilla de `flutter create` sin commit del DEV) falta `applicationId`, `allowBackup`, `network_security_config.xml`, y el manifiesto menciona `expo`. Se vuelve a correr con la `ENTREGA DEV`. Tras `cd9c3d2` y `7132e10`: las 120 de la app siguen en verde y "ningún archivo Expo ni TypeScript" pasa |
| Sanidad de las ayudas (prueba temporal, no versionada) | Verde: lo inverso falla (`habilitado("Verificar rostro")`, `deshabilitado("Consultar placa")`, un texto sin estado no cuenta como deshabilitado) |

**Ajustes de las pruebas al compilar (ninguno cambia lo que se verifica, y ninguno vino de leer `lib/`):**

1. `package:flutter/material.dart` está obsoleto en Flutter 3.50 (aviso de `flutter analyze`); las ayudas usan `package:material_ui/material_ui.dart` 1.11.1, la dependencia que declara `pubspec.yaml`, para `TextField` e `Icons`. El DEV lo avisó vía el LEAD.
2. `containsSemantics` está obsoleto desde 3.40; se usa `isSemantics`, que en el SDK es el mismo emparejamiento parcial.
3. Errores míos de compilación: una cascada del servidor falso y un import (`TextCapitalization`).
4. `tocar()` se desplaza hasta el botón si está en la pantalla pero fuera de la vista de 800 × 600 de `flutter_test` (con "Describa el motivo *" abierto, "Consultar" queda abajo). Es lo que hace el usuario; Jest no tenía diseño en pantalla.

**Corrida 2 (contra `0a1d93e`): etiquetas exactas.** El DEV avisó (vía el LEAD) que en `dd08a54` la etiqueta de accesibilidad de "Placa", "Describa el motivo *", "Desde", "Hasta" y "Placa leída" llevaba sumada la ayuda (por ejemplo "Placa" + "ABC-123"), y que mis 120 pasaban igual porque `campo()` aceptaba la etiqueta seguida de un salto de línea y además leía `labelText`/`hintText` del widget. **Era una prueba floja:** la §2 fija la etiqueta exacta. `campo()` ahora exige que la etiqueta del árbol de semántica sea **exactamente** el nombre de la §2, sin leer las propiedades del widget. Resultado:

| Contra | Resultado |
|---|---|
| `0a1d93e` (etiquetas exactas) | **`+120: All tests passed!`**; `flutter analyze test` sin avisos |
| `dd08a54` (etiqueta + ayuda), en un worktree temporal fuera del repositorio, ya borrado | **+86 −34**: todos los rojos son "campo con la etiqueta de accesibilidad exacta" no encontrado (27 de "Placa", 5 de "Desde", el resto de los otros campos con ayuda). La prueba estricta detecta lo que la anterior dejaba pasar |

Ningún nombre de la §2 difirió de lo que escribí: `MovilBuscadorApp(dependencias:)`, `Dependencias`, `AlmacenSeguro`, `LectorPlaca`, `PermisoCamara`, `LecturaPlaca`, `Key('app-raiz')` y las etiquetas de accesibilidad se usaron tal cual.

## 1. Qué hay

| Ruta | Qué es |
|---|---|
| `apps/movil/test/soporte/servidor_falso.dart` | Servidor falso de la API: un `MockClient` que registra cada solicitud (método, URL, cabeceras, cuerpo) y responde por ruta. Equivale al `fetch` simulado de Jest |
| `apps/movil/test/soporte/dobles.dart` | `AlmacenFalso` (`AlmacenSeguro` en memoria), `LectorFalso` (`LectorPlaca` sin cámara, cuenta las llamadas) y `Entorno` (las cuatro `Dependencias`) |
| `apps/movil/test/soporte/pantalla.dart` | Ayudas de caja negra: montar y desmontar `MovilBuscadorApp`, campos por etiqueta de accesibilidad, textos con `find.text`, habilitado por semántica, "atrás" con `handlePopRoute`, segundo plano con `handleAppLifecycleStateChanged` y `withClock`, textos que no se negocian |
| `apps/movil/test/hu01_hu02_test.dart` | HU-01 v6 §4 y HU-02 v4 §3, más §1.2 (segundo plano, segundo login, "Ingresando") |
| `apps/movil/test/hu01_retomar_test.dart` | §1.2 retomar la sesión (M-1: refresh y después `/v1/me`; sin token, AUTH-01) |
| `apps/movil/test/hu03_hu07_test.dart` | HU-03 v5 §6 y §7, HU-07 v5 §5, más "Cargando" (§1.2) |
| `apps/movil/test/hu04_ocr_test.dart` | HU-04 v6 §2 a §6 (parte de `flutter_test`), aviso de telemetría (§3, v5) |
| `apps/movil/test/red_sin_cache_test.dart` | §2 "toda la red pasa por `clienteHttp`" (reemplaza al `cache: 'no-store'` de Jest) |
| `apps/movil/test/repositorio_test.dart` | §2, §5 y §6 que se pueden leer en los archivos: imports fuera de `lib/bordes/`, `startImageStream`, paquetes de caché, versiones exactas, Flutter 3.50.1, `applicationId`, `allowBackup`, `network_security_config.xml`, `.gitignore`, regla 1 y regla 8 |
| `pruebas/datos/GUION-MIGRACION-FLUTTER-dispositivo.md` | Guion de la mini sesión del 4-dic, con los comandos `adb` exactos para el APK de Flutter (no lo ejecuta el TESTER) |
| `pruebas/datos/revisar_cache_app.py` | Revisa la copia de `cache/`, `files/` y `app_flutter/` (HU-04 v6 §6). Probado con dos `.tar` sintéticos: limpio → código 0; con `token_acceso` → código 1 |
| `pruebas/datos/revisar_datatransport.py`, `hoja-placas-prueba.html`, `generar_hoja_placas.py`, `ocr-precision.csv` | Traídos sin cambios de `hu-04-expo-referencia` (eran del TESTER), porque el guion los usa |

`integration_test` no se escribió (opcional, §8).

## 2. Decisiones de la §1.2 confirmadas contra la referencia

| Caso de la §1.2 | Qué hace la referencia (`hu-04-expo-referencia`) | Coincide | Prueba |
|---|---|---|---|
| Retomar la sesión | `restaurar()` (`src/sesion/controlador.ts`): con token de renovación guardado, `POST /v1/auth/refresh` y después `GET /v1/me` con el acceso nuevo; va al inicio sin AUTH-01. Sin token, AUTH-01 | Sí, desde la **v1.1** (M-1). En la v1 decía solo `GET /v1/me`: **hueco reportado y corregido** | `hu01_retomar_test`: sin token; con token (orden, cuerpo del refresh y token de `/v1/me`) |
| Retomar con la sesión vencida | Refresh 200 y `/v1/me` `401 SESION_VENCIDA` → AUTH-03 y `borrarTokens()` | Sí | `hu01_retomar_test` |
| **Retomar con todo vencido** | Refresh `401 SESION_VENCIDA` → `cerrarSesion({tipo:'inactividad'})`: **AUTH-03**, almacenamiento vacío (`HU01_retomar_todo_vencido.test.tsx` espera el texto de AUTH-03) | **Se fija AUTH-03** (confirmado por el LEAD) | `hu01_retomar_test` |
| Volver del segundo plano | `revisarAlVolver()` con `AppState` `active`: si pasó `inactividad_s` sin interacción, AUTH-03 | Sí | `hu01_hu02_test`, dos casos (601 s → AUTH-03; 30 s → sigue) |
| Segundo login | `cerrarSesion` sube la generación y reinicia el login; el rojo de `HU04_sin_cache` (`8110786`) era de la prueba (dos montajes) | Sí | `hu01_hu02_test` (tras "Salir", mismo usuario y otro); `hu01_retomar_test` (tras retomar vencida); AUTH-03 → revisor |
| Indicadores de espera | `ActivityIndicator` con `accessibilityLabel` "Ingresando" (login) y "Cargando" (App, Placa, Bitácora, OCR) | Sí | "Ingresando" en el login; "Cargando" en el catálogo de PLA-01 y en BIT-01 |

**Cómo se arma "con token guardado":** como en Jest, login, `desmontar` y volver a montar `MovilBuscadorApp` con el **mismo** `AlmacenFalso`. El nombre de la clave del token es libre (HU-01 v6 §4 bis); el LEAD lo confirmó.

## 3. Matriz caso Jest → prueba Dart (§5)

Referencia: `apps/movil/__tests__/` en `hu-04-expo-referencia` (7 archivos, **121 casos** contando cada fila de `test.each`). Estado: los 111 casos que se portan y los nuevos están **en verde en la corrida 1** (contra `dd08a54`, antes de la `ENTREGA DEV`); se vuelven a correr con la entrega. Las filas 99 a 101 (borde) están en `repositorio_test`, también en verde.

### 3.1 `HU01_HU02.test.tsx` (23) → `hu01_hu02_test.dart`

| # | Caso Jest | Prueba Dart |
|---|---|---|
| 1 | AUTH-01: Usuario, Clave, Ingresar y la franja | `sin sesión muestra Usuario, Clave, Ingresar y la franja …` (+ regla 1 sobre el árbol) |
| 2 | envía usuario y clave a la API con el fetch global | `envía usuario y clave a urlApi + /v1/auth/login por clienteHttp` |
| 3 | login correcto → inicio y token guardado | `login correcto lleva al inicio de su rol y guarda el token …` |
| 4–9 | AUTH-01 vacío (6 variantes) | `… → "Ingrese su usuario y su clave" y no envía la solicitud` (6) |
| 10 | AUTH-02 | `mensaje único, el usuario queda escrito, la clave se vacía, sin intentos restantes` |
| 11 | AUTH-04 | `muestra la hora local (HH:MM) y los minutos …` (con el reloj de la prueba, `clock.now()`) |
| 12–14 | otro error (red, 500, 503) | `… en el login → mensaje genérico, nunca el de credenciales` (3) |
| 15 | AUTH-03 sin tocar durante `inactividad_s` | `sin tocar la pantalla durante inactividad_s …` (con `pump`, sin esperar en tiempo real) |
| 16 | tras el cierre: almacenamiento, atrás, otro usuario, token viejo | `tras el cierre: almacenamiento vacío, atrás no vuelve, …` (además revisa que el token viejo no vaya en ningún cuerpo) |
| 17 | 401 `SESION_VENCIDA` cierra con el aviso | `un 401 SESION_VENCIDA de la API también cierra la sesión con el aviso` |
| 18 | sesión activa con `touchStart` en `app-raiz` | `sesión activa: con toques dentro de app-raiz …` y `… un gesto que empieza en la vista raíz (startGesture) …` |
| 19 | HOME-01 del agente | `agente (HOME-01): …` |
| 20 | inicio del revisor | `revisor: …` |
| 21 | inicio del supervisor | `supervisor: …` |
| 22 | el menú sale de `GET /v1/me` | `el menú sale de GET /v1/me (con el token) …` |
| 23 | Salir | `Salir: POST /v1/auth/logout con el token, almacenamiento vacío y AUTH-01 sin mensaje` |

Nuevos (sin caso en Jest): la clave oculta; `inactividad_s` sale del login (600 s, sigue a los 30 s); "Ingresando" (§1.2); volver del segundo plano (§1.2, 2 casos); segundo login tras "Salir" (§1.2).

### 3.2 `HU01_retomar_me_vencida.test.tsx` y `HU01_retomar_todo_vencido.test.tsx` (2) → `hu01_retomar_test.dart`

| # | Caso Jest | Prueba Dart |
|---|---|---|
| 24 | refresh 200 y `/v1/me` 401 → AUTH-03 | `al volver a abrir: la renovación responde 200 y /v1/me 401 SESION_VENCIDA → AUTH-03, almacenamiento vacío` |
| 25 | refresh y `/v1/me` 401 → AUTH-03 | `retomar con todo vencido: … → AUTH-03 …` |

Nuevos: sin token → AUTH-01 sin solicitudes de sesión (M-1); retomar correcto con el orden refresh → `/v1/me` (M-1); login después de retomar vencida.

### 3.3 `HU03_HU07.test.tsx` (40) → `hu03_hu07_test.dart`

| # | Caso Jest | Prueba Dart |
|---|---|---|
| 26 | HOME-01: "Consultar placa" habilitada, "Verificar rostro" no | igual |
| 27 | PLA-01: campo, catálogo, Consultar; "Describa el motivo *" solo con Otro | igual |
| 28 | PLA-01: mayúsculas y monoespaciada | igual (`textCapitalization` o valor en mayúsculas; `fontFamily`/`fontFamilyFallback` con "mono" o "courier") |
| 29–31 | PLA-01 sin catálogo (503, red, inesperada) | igual (3) |
| 32 | PLA-02 sin motivo | igual |
| 33 | PLA-02 "Otro" corto | igual |
| 34 | PLA-03 formato inválido con la descripción de la API | igual |
| 35 | PLA-03 valida con la regex de la API | igual |
| 36 | PLA-03 los dos mensajes | igual |
| 37 | PLA-03 422 de la API | igual |
| 38 | cuerpo de `POST /v1/consultas/placa` con el token | igual |
| 39 | PLA-04 "Consultando…", sin doble envío | igual (con `Completer`) |
| 40 | PLA-05 | igual (+ regla 1) |
| 41 | PLA-06 sin ✓ | igual (caracteres ✓✔☑✅ y los `Icons.check*`, `done*`, `task_alt`, `verified`) |
| 42 | PLA-08 sin ✓ | igual |
| 43–48 | PLA-07 (6 variantes) | igual (6) |
| 49 | PLA-07 "Reintentar" con la misma placa y motivo | igual |
| 50 | 403 → ERR-01 → "Volver al inicio" | igual |
| 51 | nada en el dispositivo | igual (`leerTodo()` sin claves nuevas ni el resultado) |
| 52 | BIT-01 tarjetas | igual (pantalla alta para ver las 9 tarjetas a la vez) |
| 53 | BIT-01 etiquetas de resultado | igual |
| 54 | BIT-01 "Cargar más" | igual (+ el cursor en la consulta) |
| 55 | BIT-02 | igual |
| 56 | BIT-01 filtros y ayuda | igual (campos por etiqueta: "Usuario", "Desde", "Hasta") |
| 57–60 | BIT-01 fecha inválida (4) | igual (4) |
| 61 | BIT-01 "Aplicar filtros" con usuario y desde | igual |
| 62–64 | error al cargar la bitácora (3) | igual (3) |
| 65 | lista vacía real | igual |

Nuevos: "Cargando" mientras llegan el catálogo y la bitácora (§1.2).

### 3.4 `HU04_ocr.test.tsx` (45) → `hu04_ocr_test.dart` y `repositorio_test.dart`

| # | Caso Jest | Prueba Dart |
|---|---|---|
| 66 | 📷 habilitado | `el botón 📷 "Leer con cámara" está habilitado` (por semántica) |
| 67 | permiso concedido → OCR-01, visor activo | igual (✕ por la etiqueta "Cerrar"; `visorCamara(activo: true)`) |
| 68 | permiso denegado → OCR-04 | igual |
| 69 | sin tocar "Capturar" no se lee nada | igual (30 s de reloj de prueba) |
| 70 | una lectura por toque | igual |
| 71 | cada toque una lectura (2 en total) | igual |
| 72 | falla de la cámara → OCR-03 | igual (`capturarYLeer` lanza) |
| 73 | ✕ vuelve sin cambios | igual |
| 74–76 | "Ingresar manualmente" desde OCR-01, 03 y 04 | igual (3), **más el foco en "Placa"** (HU-04 §3, no estaba en Jest) |
| 77–82 | §4 aceptados (6) | igual (6) |
| 83–86 | §4 → OCR-03 (4) | igual (4) |
| 87 | la regex de la API cambia lo que se acepta | igual |
| 88 | OCR-02 textos, editable, sin imagen | igual (`readOnly` falso; ningún `Image` ni `RawImage`) |
| 89 | corregir | igual |
| 90 | nunca consulta sola | igual (cuenta las solicitudes del `MockClient`) |
| 91 | el motivo se conserva; cuerpo de HU-03 | igual |
| 92 | corrección inválida → PLA-03 | igual |
| 93 | "Volver a capturar" descarta | igual |
| 94 | "Volver a intentar" | igual |
| 95 | "Abrir ajustes" | igual |
| 96 | volver con permiso | igual |
| 97 | OCR-01 → OCR-03 sin solicitudes | igual |
| 98 | almacenamiento sin claves nuevas | igual |
| 99 | existe `src/camara/lectorPlaca.ts` | `repositorio_test`: existe `lib/bordes/bordes.dart` |
| 100 | nada fuera del borde importa cámara/ML Kit | `repositorio_test`: `camera`, `google_mlkit_*`, `permission_handler` y `flutter_secure_storage` solo en `lib/bordes/` |
| 101 | `App.tsx` tampoco | cubierto por el anterior (`lib/app.dart` y `lib/main.dart` están fuera de `lib/bordes/`) |
| 102 | aviso: primera vez, "Capturar" desactivado | igual |
| 103 | aviso: tocar fuera no hace nada | igual |
| 104 | "Entendido" y no vuelve en la sesión | igual |
| 105–107 | salir con ✕, atrás o "Ingresar manualmente" no lo da por visto | igual (3; atrás con `handlePopRoute`) |
| 108 | aviso tras "Salir" | igual |
| 109 | aviso tras el cierre por inactividad | igual (+ almacenamiento vacío) |
| 110 | OCR-04 sin aviso | igual |

### 3.5 `HU04_sin_cache.test.tsx` (1) → `red_sin_cache_test.dart` y `repositorio_test.dart`

| # | Caso Jest | Prueba Dart |
|---|---|---|
| 111 | cada llamada lleva `cache: 'no-store'` | `toda la red de la app pasa por clienteHttp (…)`: el mismo recorrido (login, me, motivos, consulta, retomar con refresh, logout, bitácora); cada solicitud con `urlApi + /v1/` y **ningún `HttpClient` de `dart:io` creado** durante el recorrido. Más `repositorio_test`: ningún paquete de caché en `pubspec.yaml` (§3 y HU-04 v6 §6) |

### 3.6 `PantallaEstado.test.tsx` (10) → no se porta

| # | Caso Jest | Prueba Dart |
|---|---|---|
| 112–121 | `/v1/salud` → "Conectado" / "Sin conexión con el servidor" (2 + 4 + 4) | **No se porta: pantalla del Sprint 0 que la app no monta** (M-1, contrato v1.1) |

### 3.7 M-9 a M-12 de HU-04 que faltaban

| Tarea | Dónde |
|---|---|
| M-9 safe area | Solo en el teléfono (§4): guion, paso 3 |
| M-10 sin caché | App: `repositorio_test` (paquetes) y `red_sin_cache_test`; teléfono: guion, paso 8 (`cache/`, `files/`, `app_flutter/` con `revisar_cache_app.py`); la cabecera `no-store` sigue en pytest de la API (§1.3) |
| M-11 origen de la telemetría | Lo confirma el DEV en su informe (§7); la cola en el teléfono: guion, paso 9 |
| M-12 aviso de OCR-01 | `hu04_ocr_test`, casos 102 a 110; una vez en el teléfono: guion, paso 6 |

## 4. Comprobaciones del repositorio (§2, §5, §6; HU-04 v6 §1 y §6)

Automatizadas en `repositorio_test.dart` (corren con `flutter test`) y, por comando, después de la entrega del DEV:

| Comprobación | Cómo | Estado |
|---|---|---|
| Imports de cámara, ML Kit, permisos y almacenamiento solo en `lib/bordes/` | `repositorio_test` | **VERDE** (M-5) |
| `HttpClient`, `dio` y otros clientes solo en `lib/main.dart` o `lib/bordes/` | `repositorio_test` | **VERDE** (M-5) |
| `DateTime.now()` no aparece en `lib/` (la hora sale de `clock.now()`) | `repositorio_test` | **VERDE** (M-5) |
| `startImageStream` no aparece en `lib/` | `repositorio_test` y `grep -r startImageStream apps/movil/lib` | **VERDE** (M-5) |
| Ningún paquete de caché | `repositorio_test` | **VERDE** (M-5) |
| Flutter 3.50.1 en `environment`, dependencias exactas, `pubspec.lock` | `repositorio_test` | **VERDE** (M-5) |
| Sin Expo: ni `.ts`/`.tsx`, ni `package.json`, ni menciones en `pubspec.yaml` y `android/` | `repositorio_test` y `git ls-files apps/movil` | Archivos: **VERDE** tras `cd9c3d2` (DEV) y `7132e10` (TESTER). Menciones: **VERDE con el criterio de la v1.3** (palabra completa, `grep -riw`; definitivo por la M-4). Con la v1.1 (`grep -ri`, subcadena) sale un falso positivo: `apps/movil/android/app/src/main/AndroidManifest.xml: android:exported="true"` ("exported" contiene "expo"). Con `grep -riw "expo\|react-native" apps/movil --include=*.yaml --include=*.gradle* --include=*.xml` no sale nada (código 1), sobre el árbol de trabajo con el `android/` del DEV todavía sin commit. `repositorio_test` usa el mismo criterio (palabra completa: `android:exported` no cuenta; `expo`, `expo-camera` o `react-native` sí). Se repite con la `ENTREGA DEV` |
| `apps/movil/__tests__/` borrado | `git ls-files apps/movil/__tests__` vacío | **HECHO** (`7132e10`, TESTER; los 5 archivos que había en la rama) |
| `applicationId`, nombre visible, `allowBackup`, `network_security_config.xml` | `repositorio_test` | **VERDE** (M-5) |
| `.gitignore` con `key.properties`, `*.jks`, `*.keystore`; `git ls-files` sin `.crt`, `.pem`, `.key`, `.der`, `.jks`, `.keystore` | `repositorio_test` y `git ls-files \| grep -E '\.(crt\|pem\|key\|der\|jks\|keystore)$'` | **VERDE** (M-5) |
| `flutter analyze` sin errores ni avisos | Comando en `apps/movil` | **VERDE** (M-5) |
| APK de release no depurable | `aapt dump badging` (build-tools 36.0.0; guion, paso 11) | **VERDE** (M-5): sobre el APK compilado por el TESTER desde `fb3869b` y sobre el firmado del DEV; ver §0 |
| Modelo de ML Kit dentro del APK (§7, v1.2, M-3) | `python -I pruebas/datos/revisar_modelo_apk.py <app-release.apk>` (equivale a `unzip -l`; guion, paso 11.5) | **VERDE** (M-5): modelo dentro en los dos APK; `play-services-mlkit-*` sin rojo (v1.2); la red queda **NO VERIFICADO** y la cola `datatransport` va en el paso 9 del guion |
| `git diff main...migracion-flutter -- services/ contratos/` vacío | Comando | **VERDE** (M-5) |

## 5. Cómo se corren

Desde `apps/movil`, con el SDK compartido de la M-2:

```powershell
cd C:\Willy\Trabajo\MININTER\Movil_Buscador-flutter\apps\movil
C:\Programas_Portables\flutter_3.50.1\flutter\bin\flutter.bat test
```

## 6. SDK

| Qué | Valor |
|---|---|
| Flutter | 3.50.1 (stable), Dart 3.14.0, instalación compartida del DEV en `C:\Programas_Portables\flutter_3.50.1\flutter` (M-2). El TESTER no instaló nada propio |
| Android SDK | `C:\Android` (del DEV) |

`flutter --version` (2026-11-24):

```
Flutter 3.50.1 • channel stable • https://github.com/flutter/flutter.git
Framework • revision ae9b586f34 (6 days ago) • 2026-11-18 17:01:07 -0800
Engine • hash 51379e6df48ea8ee7205623b90fe66491cad8df3 (revision 4d35714800) (6 days ago) • 2026-11-18 01:50:07.000Z
Tools • Dart 3.14.0 • DevTools 2.61.0
```

`flutter doctor -v` (2026-11-24), resumen:

| Categoría | Resultado |
|---|---|
| Flutter | `[!]` 3.50.1 stable en `C:\Programas_Portables\flutter_3.50.1\flutter`, Dart 3.14.0. Avisa solo que `flutter` y `dart` no están en el `PATH` (se usa la ruta completa) |
| Windows | `[√]` Windows 11 25H2 |
| **Android toolchain** | **`[!]` "Android SDK at C:\Android" pero "Unable to locate Android SDK" y "No valid Android SDK platforms found in C:\Android\platforms. Directory was empty."** No afecta a `flutter test`; **sí bloquea** el APK (`flutter build apk`), `aapt` (build-tools) y la mini sesión. Avisado al LEAD |
| Chrome | `[√]` (no se usa) |
| Visual Studio | `[!]` faltan los componentes de C++ (solo para apps de Windows; no se usa) |
| Dispositivos | `[√]` Windows, Chrome y Edge (sin teléfono conectado; normal) |
| Red | `[√]` |

## 7. NO VERIFICADO (por diseño o por ahora)

- **Qué hace en la red `play-services-mlkit-*`** (§7 v1.2): NO VERIFICADO por decisión del humano (opción A).
- **PLA-02 "con el foco ahí"** (HU-03 §6): no lo verificaba Jest; con un selector de motivo, el foco no es observable de forma estable en `flutter_test`. Queda para la revisión del UX.
- **PLA-07 "ícono y color distintos"** y **PLA-06 "gris, sin verde"**: se verifica la ausencia de ✓; el color queda para el UX.
- **Safe area (§4)** y **todo lo del teléfono** (HU-04 v6 §6 y §8): guion de la mini sesión del 4-dic.
