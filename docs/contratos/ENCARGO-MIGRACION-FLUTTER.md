# ENCARGO LEAD → TESTER y DEV — MIGRACION-FLUTTER

**Documento de trabajo:** `docs/contratos/CONTRATO-MIGRACION-FLUTTER.md` **v1.3** (M-1, M-3 y M-4), aprobado por el humano (vía PM) el 2026-11-24, junto con CONTRATO-HU-01 **v6**, HU-02 **v4**, HU-03 **v5**, HU-07 **v5** y HU-04 **v6**. Es la única spec: lo que no dice no se supone, se pregunta. CONTRATO-HU-08 v4 y todo lo de la API siguen vigentes y no se pueden romper.
**Rama:** `migracion-flutter` (rebasada sobre `main` `1204a77`, que ya tiene los ADR-0017 a 0020), en la carpeta **`C:\Willy\Trabajo\MININTER\Movil_Buscador-flutter`** (worktree). TESTER y DEV trabajan en la misma rama, cada uno en sus rutas. No trabajes en la carpeta principal (`Movil_Buscador`, rama `hu-04`).
**Plazo:** del 26-nov al 5-dic. Mini sesión física el **jueves 4-dic** o antes. Veredicto el 5 y 6-dic.
**Pasa por UX:** sí, todas las pantallas (contrato §10).

## Reglas

1. Solo tocas las rutas que `AGENTS.md` asigna a tu rol (las repite el contrato en "Rutas de cada rol"). El TESTER ahora es dueño de `apps/movil/test/` y `apps/movil/integration_test/`.
2. Commits solo de tus rutas, con prefijo `[TESTER]` o `[DEV]` y **sin** la línea `Co-Authored-By`. Sin push y sin merge.
3. Las dudas van al LEAD: `herdr agent prompt lead "PREGUNTA <ROL>: <pregunta>"`. Si el contrato no dice algo, es un hueco: no lo completes, avísalo.
4. No toques `Empezar.txt` ni lo incluyas en commits.
5. **Ninguna foto de placa ni de rostro en el repositorio ni guardada en el dispositivo.** Solo placas sintéticas con el prefijo `ZZ`. Ningún secreto en el repositorio: ni la llave de firma del APK, ni la CA del proxy, ni claves.
6. Reglas de negocio de `AGENTS.md`: la 1 (la palabra prohibida no aparece en ningún texto, nombre ni comentario), la 2 (motivo obligatorio), la 6 (sin lectura continua: nunca `startImageStream`), la 7 (ningún error se convierte en un negativo) y la 8.
7. **Instalación autorizada por el humano (2026-11-24):** puedes instalar el **Flutter SDK** (la versión que fija el DEV, contrato §6) y el **Android SDK (command-line tools)** en esta PC. Anota versiones y rutas en tu informe. `adb` ya está en `C:\Android\platform-tools`. No instales nada más sin preguntar.
8. Arranque de la API, si lo necesitas: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env up -d --build`, desde esta carpeta. **Las carpetas `Movil_Buscador`, `Movil_Buscador-despliegue` y `Movil_Buscador-flutter` comparten el proyecto de compose: nunca levantes Docker en dos a la vez.** `infra/.env` no se versiona; si falta en esta carpeta, cópialo de `C:\Willy\Trabajo\MININTER\Movil_Buscador\infra\.env` (nunca lo agregues a un commit).
9. **Referencia de Expo:** el código y las pruebas Jest aceptadas están en la etiqueta `hu-04-expo-referencia` (por ejemplo, `git show hu-04-expo-referencia:apps/movil/src/camara/placaLeida.ts`). Se leen, no se mergean.

## Qué entrega cada uno

- **DEV:**
  1. **Primero, y avisando al LEAD antes de seguir:** la versión estable de Flutter (y de Dart) que fijas, escrita en `apps/movil/pubspec.yaml` (contrato §6, decisión 5). Mándala con `herdr agent prompt lead "PREGUNTA DEV: versión de Flutter <x.y.z>"`. El LEAD la anota en el changelog y te confirma. Así el TESTER instala la misma.
  2. **La app Flutter en `apps/movil/`**, con la interfaz exacta del contrato §2 (paquete `movil_buscador`, `MovilBuscadorApp`, `Dependencias`, `AlmacenSeguro`, `LectorPlaca`, `Key('app-raiz')`, etiquetas de accesibilidad, `clock`, `--dart-define=API_URL`). **Publica la interfaz (§2) en un commit temprano**, aunque las pantallas no estén, para que el TESTER pueda compilar sus pruebas contra ella.
  3. Todas las pantallas y flujos de HU-01 v6, HU-02 v4, HU-03 v5, HU-07 v5 y HU-04 v6, más lo que se conserva de Expo (§1.2) y la safe area (§4).
  4. Borrar el código Expo de `apps/movil/` (§5), sin tocar `apps/movil/__tests__/` (lo borra el TESTER).
  5. Build y secretos (§6): versiones exactas y `pubspec.lock`, `applicationId`, `allowBackup`, `network_security_config.xml`, APK de release firmado con la llave **fuera del repositorio**, `.gitignore` (solo agregar).
  6. Variante empaquetada de ML Kit (§7): las líneas del `build.gradle` de los dos plugins y el árbol de dependencias del APK.
  7. **Informe** en `informes/DEV-MIGRACION-FLUTTER.md`, con: las versiones y rutas de los SDK instalados; los paquetes y sus versiones; la §7; cómo se compilan el APK de depuración y el de release (comandos exactos); dónde vive la llave de firma (sin la clave) y cómo se borra al cierre; los **pasos para el humano** de HU-04 v6 §8 (desinstalar la app de Expo, CA de Caddy, `adb reverse tcp:8443 tcp:8443`, borrar la CA al cierre); y la ruta de las capturas para el UX.
  8. **Capturas para el UX**, fuera del repositorio: de `flutter_test` (o del emulador) de todas las pantallas del contrato, y del S23 Ultra las de la §4 cuando haya teléfono.
- **TESTER:**
  1. Instalar la versión de Flutter que fije el DEV (el LEAD te avisa). Mientras tanto, prepara la matriz.
  2. **Matriz** caso Jest → prueba Dart (contrato §5): cada caso de `apps/movil/__tests__/` de la referencia `hu-04-expo-referencia`, más los de M-9 a M-12 de HU-04 que faltaban (safe area queda para el teléfono; sin caché, origen de la telemetría y el aviso de OCR-01).
  3. **Pruebas en `apps/movil/test/`** (`flutter_test`) contra la interfaz §2: todo lo que el contrato §8 marca en la primera columna, con `MockClient`, dobles de `AlmacenSeguro` y `LectorPlaca`, `handlePopRoute`, `withClock` / `pump`.
  4. **Confirmar la §1.2 contra la referencia** y fijar en tu informe qué muestra hoy "retomar con todo vencido" (AUTH-01 o AUTH-03). Si algo de la §1.2 no coincide con Expo, avísalo al LEAD: se corrige el contrato.
  5. **Comprobaciones del repositorio** (§2, §5, §6 y HU-04 v6 §1 y §6): las búsquedas con `grep` de los imports fuera de `lib/bordes/`, de `startImageStream` y de los paquetes de caché, `git ls-files` sin Expo ni secretos, `flutter analyze` y `aapt dump badging` sobre el APK de release.
  6. **Borrar `apps/movil/__tests__/`** en un commit tuyo, cuando tus pruebas Dart cubran la matriz.
  7. **Para la mini sesión del 4-dic, sin ejecutarla:** el guion actualizado en `pruebas/datos/` (HU-04 v6 §6 y §8, la §4 del contrato y un recorrido de login, placa y bitácora), con los comandos `adb` exactos para el APK de Flutter. `integration_test` es opcional (§8).
  8. **Informe** en `informes/TESTER-MIGRACION-FLUTTER.md`, con la matriz, cada caso en verde, rojo o `NO VERIFICADO`, y la evidencia.

## Orden del cierre (contrato §10)

1. `ENTREGA DEV` con el informe y las capturas.
2. El TESTER corre las pruebas de lo tocado contra la entrega y manda su `ENTREGA TESTER` parcial.
3. El LEAD pasa las capturas al UX. Las correcciones vuelven al DEV como una M-n.
4. Mini sesión física con el PM y el humano (4-dic o antes).
5. Con la aprobación del UX, el LEAD da la orden (en una M-n) de **la suite completa, una sola vez**, sobre el commit definitivo: pytest de la API y de los simuladores, `flutter test` e `integration_test` si existe.
6. `ENTREGA TESTER` final y veredicto.

## Aviso de vuelta

`herdr agent prompt lead "ENTREGA <ROL>: <resumen corto> — informes/<ROL>-MIGRACION-FLUTTER.md"`.

## Secciones M-n

Las aclaraciones de este ciclo se agregan abajo como `M-1`, `M-2`, … Cada una dice qué reemplaza. Los mensajes de herdr solo dicen "lee M-n del encargo".

### M-1 (2026-11-24) — Contrato v1.1 (TESTER y DEV)

Reemplaza: la §1.2 ("Retomar la sesión") y la §5 (fila "Pruebas de la app") de la v1. El humano (vía PM) aprobó la v1.1 por los dos huecos que reportó el TESTER:

1. **`PantallaEstado` no se porta.** Ni el DEV la construye ni el TESTER porta `PantallaEstado.test.tsx`. En la matriz queda como "no se porta: pantalla del Sprint 0 que la app no monta".
2. **"Retomar la sesión" (§1.2) con la secuencia exacta de la referencia:** al abrir la app con un token de renovación guardado, **primero** `POST /v1/auth/refresh` con ese token y **después** `GET /v1/me` con el token de acceso nuevo, y se va al inicio del rol. **Sin token guardado: AUTH-01**, sin enviar ninguna solicitud de sesión. El TESTER lo prueba con el orden de las solicitudes del `MockClient`; el DEV lo implementa así.

### M-2 (2026-11-24) — Versión de Flutter fijada (TESTER y DEV)

Reemplaza: el punto 1 de "Qué entrega cada uno" de los dos roles, en lo que respecta a la versión.

- **Versión:** **Flutter 3.50.1** (stable) con **Dart 3.14.0**, anotada en el changelog del contrato (§6). No se cambia hasta el cierre.
- **SDK compartido:** el DEV lo instala en `C:\Programas_Portables\flutter_3.50.1\flutter` y el Android SDK en `C:\Android`. **El TESTER usa esa misma instalación** y no descarga otra copia. Espera a que el DEV confirme que terminó la instalación (`flutter --version` muestra 3.50.1) antes de correr `flutter test`.
- Los dos anotan en su informe la salida de `flutter --version` y de `flutter doctor -v`.

### M-3 (2026-11-24) — Contrato v1.2: §7, el modelo dentro del APK (DEV y TESTER)

Reemplaza: la §7 de la v1.1 y el punto 6 del DEV en "Qué entrega cada uno". Decisión del humano (vía PM): **opción A**.

- **DEV:** no excluyes nada. En tu informe van: la línea del `build.gradle` del plugin (variante empaquetada `com.google.mlkit:text-recognition`), el fragmento de `releaseRuntimeClasspath` con `play-services-mlkit-text-recognition` y `-common` (dependencia transitiva del POM de Google), y la lista de archivos del modelo **dentro del APK** (`assets/mlkit-google-ocr-models/` y `lib/*/libmlkit_google_ocr_pipeline.so`). Lo que esa dependencia haga en la red queda `NO VERIFICADO`. Para Face Detection (HU-05) solo reportas lo que ves, sin agregarlo.
- **TESTER:** sobre el APK de release, comprueba con `unzip -l` (o `apkanalyzer`) que esos archivos del modelo están. **No** marques en rojo la presencia de `play-services-mlkit-*`. La revisión de la cola `datatransport` sigue en el guion de la mini sesión del 4-dic.
- **La §5 (`grep -riw`) sigue pendiente de aprobación** en una v1.3. Mientras tanto vale lo que ya les dije: se evalúa con palabra completa.

### M-4 (2026-11-24) — Contrato v1.3: §5 con palabra completa (TESTER)

Reemplaza: el último punto de la M-3 (la §5 pendiente). El humano (vía PM) aprobó la v1.3: la comprobación de la §5 es `grep -riw "expo\|react-native" apps/movil --include=*.yaml --include=*.gradle* --include=*.xml`, que tiene que salir vacío. **TESTER:** el criterio que dejaste como pendiente en `4201fee` pasa a definitivo; quita la marca "pendiente de aprobación" en tu informe y en `repositorio_test`.


### M-5 (2026-11-24) — ENTREGA DEV recibida: corrida del TESTER (TESTER)

Reemplaza: el paso 2 de "Orden del cierre" (concreta qué corres). La `ENTREGA DEV` llegó con el informe en `1382d13` (commits `dd08a54`, `cd9c3d2`, `f315ff3`, `a70e627` y `0a1d93e`).

**TESTER**, sobre `1382d13` o sobre el último commit del DEV, **solo lo tocado**, sin la suite completa:
1. `flutter analyze` de todo `apps/movil/` y `flutter test` de la app.
2. `repositorio_test` completo (§2, §5 con `grep -riw`, §6 y HU-04 v6 §1 y §6), ahora con `android/` en el repositorio.
3. Sobre el APK de release que compila el DEV (o uno que compiles tú con sus comandos del informe, fuera del repositorio): `aapt dump badging` sin `application-debuggable` y el modelo de la §7 dentro del APK (M-3).
4. Lo del teléfono queda `NO VERIFICADO` hasta la mini sesión.

Al terminar: `ENTREGA TESTER` parcial con el informe actualizado. La suite completa es una M-n aparte, después de la aprobación del UX.

**Nota del DEV para todos:** `compileSdk` 37 (por `permission_handler_android`), con `targetSdk` 36 y `minSdk` 24. No cambia nada observable.

### M-6 (2026-11-24) — Mini sesión física adelantada al miércoles 25-nov (DEV y TESTER)

Reemplaza: la fecha de la mini sesión (jueves 4-dic) del encabezado y del paso 4 de "Orden del cierre". El humano (vía PM) la hace el **miércoles 25-nov**.

**DEV**, hoy:
1. Compila desde el último commit de código (`0a1d93e`; el informe `1382d13` no cambia el código) el **APK de depuración** con `--dart-define=API_URL=https://localhost:8443` y el **APK de release** firmado, con los comandos de tu informe.
2. Los copia, **fuera del repositorio**, a `C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\` como `movil-buscador-debug.apk` y `movil-buscador-release.apk`, con un `SHA256SUMS.txt` al lado.
3. Comprueba que el compose local arranca desde esta carpeta con `infra/.env` (copiado de la carpeta principal, nunca versionado) y `PROXY_PUERTO_HTTPS=8443`, que `https://localhost:8443/v1/salud` responde `200` y que la CA de Caddy se puede copiar (paso 2 de tu §9). Después baja el compose (`down`) y deja Docker libre.
4. Avisa con `herdr agent prompt lead "PREGUNTA DEV: APK listos <sha256 de los dos>"`. No necesitas un commit si no cambias nada del repositorio.

**TESTER**, hoy, después de la M-5:
1. Pone el guion `pruebas/datos/GUION-MIGRACION-FLUTTER-dispositivo.md` al día con la entrega del DEV: el paso 0.9 ya no compila, sino que instala `C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\movil-buscador-debug.apk` y comprueba su SHA-256 contra `SHA256SUMS.txt`; los pasos de la CA y de la desinstalación coinciden con la §9 del informe del DEV; y el paso 11 usa `movil-buscador-release.apk`.
2. Cuando llegue la revisión del UX (`docs/ux/revisiones/MIGRACION-FLUTTER.md`), suma al paso 3 (safe area) las capturas que pida el UX. El LEAD te avisa.
3. Avisa con `herdr agent prompt lead "ESTADO TESTER: guion al día <commit>"`.

### M-7 (2026-11-24) — Revisión del UX (DEV y TESTER)

Reemplaza: el paso 1 de la M-6 del DEV, en cuanto a **desde qué commit** se compilan los APK. La revisión del UX está en `docs/ux/revisiones/MIGRACION-FLUTTER.md` (`6e5111a`): aprueba las 30 capturas con 3 observaciones, ninguna BLOQUEA, sin cambios de contrato. Los botones se quedan como están escritos (sin mayúsculas).

**DEV**, **antes** de compilar los APK de la M-6, para que el teléfono pruebe la versión definitiva:
1. **Obs. 1 (OCR-01 leyendo):** el círculo del indicador de carga vuelve a ser chico y centrado en el marco, sin tapar el visor. Sin texto nuevo.
2. **Obs. 2 (BIT-01 filtros):** las opciones de "Tipo" y "Resultado" miden lo que su texto y se agrupan varias por fila, para que "Aplicar filtros" quede a la vista. Mantén el alto mínimo (36 dp, o 48 dp si se puede). Sin texto nuevo.
3. **Obs. 3:** agrega a tu paquete de capturas PLA-01 sin catálogo (falla `GET /v1/motivos`) y BIT-01 con una fecha inválida, y regenera las capturas de OCR-01 leyendo y de BIT-01 con los filtros abiertos. Todas fuera del repositorio, en la misma carpeta.
4. Compila los APK de la M-6 **desde ese commit**, y avisa con `PREGUNTA DEV: M-7 en <commit>; APK listos <sha256>`.

**TESTER:**
1. Suma al guion (M-6, punto 2) las capturas del S23 Ultra que pide el UX: **S1 a S5 son obligatorias para la §4** y S6 a S15 cierran la etapa 2 de HU-04 y los símbolos. Todas van a la carpeta de capturas fuera del repositorio. Respeta el orden y las condiciones que pide el UX (S5 en el otro modo de navegación; S7 con la letra del sistema al máximo).
2. Cuando el DEV entregue la M-7, corre `flutter test` sobre ese commit (solo lo tocado).

### M-8 (2026-11-24) — Contrato v1.4: el no-store de la API, y Docker (DEV y TESTER)

Reemplaza: la §1.3 y la fila "Nadie" de las rutas de la v1.3, y el punto 3 de la M-6 del DEV. El humano (vía PM) aprobó la v1.4 y autorizó el comando de Docker.

**DEV:**
1. **Docker (autorización del humano):** en `C:\Willy\Trabajo\MININTER\Movil_Buscador` corre **exactamente** `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env down`, **sin `-v`** y sin tocar volúmenes ni contenedores de otros proyectos. Después levanta el compose desde `Movil_Buscador-flutter` (regla 8) y comprueba `https://localhost:8443/v1/salud` = `200` y que la CA de Caddy se puede copiar.
2. **No-store:** porta **solo** el cambio de `services/api/app/traza.py` de `0ccd8fb` (rama `hu-04`; `git show 0ccd8fb -- services/api/app/traza.py`). Nada más en `services/`. Commit `[DEV]` aparte.
3. Sigue con la M-7 (observaciones del UX) y compila los APK de la M-6 desde el commit que tenga la M-7 y el no-store. Avisa con `PREGUNTA DEV: M-7 y M-8 en <commit>; APK listos <sha256>`. Deja el compose levantado desde `Movil_Buscador-flutter` para la mini sesión.

**TESTER:**
1. Porta `services/api/tests/test_hu04_sin_cache.py` de `773d1be` (`git show 773d1be:services/api/tests/test_hu04_sin_cache.py`). Commit `[TESTER]` aparte.
2. Cuando el DEV avise que el compose está arriba desde esta carpeta, córrela con el no-store del DEV (solo esa prueba; la suite completa va en otra M-n). Antes de eso, no levantes Docker.

### M-9 (2026-11-24) — M-7 y M-8 entregadas: corrida del TESTER antes de la mini sesión (TESTER)

Reemplaza: el punto 2 de la M-7 y el punto 2 de la M-8 del TESTER. El DEV entregó la M-7 (`0724e88`) y la M-8 (`36d174a`). Su informe está en `20761dd` y `6790594`. Los APK, recompilados con la M-7 y la M-8, están en `C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\`, con `SHA256SUMS.txt` (el LEAD lo verificó): debug `987be377…40cc1`, release `3528cb54…50381`. El compose está levantado desde esta carpeta.

**TESTER**, sobre `6790594`, solo lo tocado:
1. `services/api/tests/test_hu04_sin_cache.py` contra el compose (los 14 casos por la red interna y los 14 por el proxy).
2. `flutter test` de la app y `repositorio_test` (§1.3 v1.4: `git diff` de `services/` con solo `traza.py` y tu prueba).
3. Sobre los dos APK nuevos: `SHA256SUMS`, `aapt`, el modelo y la firma, como en el paso 11 del guion.
4. **No bajes el compose:** queda arriba para la mini sesión del 25-nov.

Al terminar: `ESTADO TESTER` con el resultado.
