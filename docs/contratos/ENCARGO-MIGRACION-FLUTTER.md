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

