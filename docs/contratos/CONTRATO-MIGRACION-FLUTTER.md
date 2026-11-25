# CONTRATO — MIGRACION-FLUTTER La app móvil en Flutter (HU-01, 02, 03 y 07, más HU-04)

**Tipo:** Refactor (HU-01, HU-02, HU-03 y HU-07 en la app: el comportamiento no cambia) + Feature (HU-04, construida directo en Flutter)
**Versión:** v1
**Estado:** Pendiente de aprobación
**Origen:** encargo PM → LEAD (2026-11-24, tarea 2). Decisiones del humano del 2026-11-24: escenario 1, migrar ya (PRD PA #37 y #38, `7cec298`); ADR-0017 aceptado; decisiones 1 a 6 de la evaluación del stack (`docs/arch/evaluaciones/PA-37-39-stack-mininter.md` §6)
**Rama de trabajo:** `migracion-flutter`, desde `main` `47ace7b`. TESTER y DEV trabajan en la misma rama, cada uno en sus rutas
**Plazo (plan decidido, evaluación §5):** contrato el 25 y 26-nov · DEV y TESTER del 26-nov al 5-dic · veredicto el 5 y 6-dic · después, DESPLIEGUE-01 v2 (6 al 8-dic) y la demo con APK del 10-dic
**Pasa por UX:** sí. Se rehacen todas las pantallas: AUTH-01 a AUTH-04, HOME-01 (y los inicios del revisor y del supervisor), ERR-01, PLA-01 a PLA-08, BIT-01 y BIT-02, y OCR-01 a OCR-04 (§10)

**Contratos que esta migración versiona** (cada uno cambia solo sus secciones de la app y apunta a este documento):

| Contrato | Versión anterior | Versión nueva | Qué cambia |
|---|---|---|---|
| `CONTRATO-HU-01.md` | v5 | **v6** | §4 y §4 bis: la interfaz de la app para las pruebas pasa a la §2 de este contrato |
| `CONTRATO-HU-02.md` | v3 | **v4** | "Fuera del contrato": la interfaz de la app es la §2 de este contrato |
| `CONTRATO-HU-03.md` | v4 | **v5** | §6: el `403` se simula con el cliente HTTP de prueba; la revisión del UX usa capturas de `flutter_test` y del teléfono |
| `CONTRATO-HU-07.md` | v4 | **v5** | Revisión del UX con capturas de `flutter_test` y del teléfono |
| `CONTRATO-HU-04.md` | v5 | **v6** | §1 (módulo de borde en Dart), §6 y §8 (sin Expo ni EAS), "Qué se prueba dónde", rutas y avisos |
| `CONTRATO-HU-08.md` | v4 | sin cambios | No tiene app |

**La API, los contratos de la API (`contratos/api/openapi.json`, `contratos/fuentes/`), la base y la bitácora no cambian.** Nada de lo que se ve desde la API puede cambiar en esta rama.

---

## Paquete de contexto

| Fuente | Por qué entra |
|---|---|
| ADR-0017 (rama `entregables-osigp`, `docs/arch/adrs/0017-app-movil-flutter-mlkit.md`) | Flutter para Android en `apps/movil/`, los paquetes de referencia, los módulos de borde detrás de interfaces Dart, nada de imágenes en disco, telemetría sin cambios, `debug-overrides`, versión fijada, build sin EAS |
| Evaluación del stack, §2, §3, §5, §6 y §7 | Qué cambia por pieza, qué se reutiliza de Expo, el plan con días, las decisiones del humano y lo que queda NO VERIFICADO |
| ADR-0013 | Estado solo en memoria, el token en almacenamiento seguro, limpieza al cerrar sesión (lo precisa el ADR-0017) |
| ADR-0007 | El contrato de la API no cambia; los modelos de la app se generan desde `contratos/api/openapi.json` |
| ADR-0010 | Android primero, el S23 Ultra con Android 16 como teléfono de referencia; iOS fuera hasta el PA #12 |
| ADR-0011 | Valores provisionales que la app toma de la API (`inactividad_s`, `formato_placa`), sin fijarlos en el código |
| CONTRATO-HU-01 v5, HU-02 v3, HU-03 v4, HU-07 v4 | El comportamiento de la app que **no cambia** (§1) |
| CONTRATO-HU-04 v5 y `ENCARGO-HU-04.md` M-9 a M-12 | HU-04 completa, incluidas las tareas que quedaron sin cerrar en Expo (safe area, sin caché HTTP, origen de la telemetría y el aviso de OCR-01) |
| `docs/ux/revisiones/HU-04.md`, observación 2 | El margen seguro superior e inferior en todas las pantallas (BLOQUEA) |
| `ENCARGO-HU-01-02.md` A1 y `PENDIENTES.md` (HU-03) | Retomar la sesión al abrir la app y el `401 SESION_VENCIDA` del primer `GET /v1/me` |
| Código Expo en la etiqueta `hu-04-expo-referencia` (`125cabe`) | Comportamiento actual que se conserva (§1.2) y lo que se reutiliza (§9). **No se mergea** |
| AGENTS.md (`d6d97dd` en esta rama) | Rutas de cada rol, con `apps/movil/test/` e `apps/movil/integration_test/` para el TESTER (decisión 6 del humano) |

**Aviso:** el ADR-0017 al ADR-0020, la evaluación del stack y el TECH-DESIGN actualizado están en la rama `entregables-osigp` (en origin hasta `5d3879a`), todavía no en `main`. Ver la pregunta 1.

## Alcance

| Entra | No entra |
|---|---|
| La app completa en Flutter (Dart), solo Android, en `apps/movil/`, con HU-01, HU-02, HU-03, HU-07 y HU-04 | Cualquier cambio en la API, los simuladores, la base o la bitácora |
| Borrar el código Expo de `apps/movil/` (el DEV) y las pruebas Jest de `apps/movil/__tests__/` (el TESTER) | HU-05, HU-06 y HU-09 (van después, con su propio contrato). HU-05 E8 a E10 y HU-10 no se construyen |
| Las pruebas de la app en `flutter_test` y `integration_test` | NGINX, la descarga protegida del APK y el VPS: son `CONTRATO-DESPLIEGUE-01.md` v2 |
| Build de depuración y de release firmado en la máquina del proyecto | iOS (PA #12), Keycloak (ADR-0020) y cualquier pantalla web (PA #39) |
| Las verificaciones en el S23 Ultra de HU-04 (contrato v6, §6 y §8) y la safe area | La precisión del OCR (≥ 100 capturas): sigue aparte, del 16 al 26-dic |

## Interfaz observable

1. **App en `flutter_test`:** se monta el widget raíz de la §2 con los dobles de los bordes. Es lo que ve el TESTER.
2. **App en el teléfono:** el APK de depuración (`flutter run` o `flutter build apk --debug`) y el de release (§6), en el S23 Ultra con Android 16.
3. **El repositorio:** qué archivos existen en `apps/movil/`, qué dependencias declara `pubspec.yaml`, qué no se versiona (§5 y §6).
4. **La API**, solo para comprobar que no cambió (§1.3).

## Comportamiento

### 1. Lo que no cambia (refactor)

#### 1.1 Los contratos de la app se cumplen igual

Cada caso de la app de estos contratos se cumple en Flutter **con los mismos textos, el mismo orden de pantallas y las mismas solicitudes a la API**:

| Contrato | Secciones de la app |
|---|---|
| CONTRATO-HU-01 v6 | §4 (AUTH-01 a AUTH-04, sesión activa, otros errores, `inactividad_s` desde la API) |
| CONTRATO-HU-02 v4 | §3 (inicios de los tres roles, menú desde `GET /v1/me`, opciones deshabilitadas, ERR-01, "Salir") |
| CONTRATO-HU-03 v5 | §6 y §7 (PLA-01 a PLA-08, validación local con `formato_placa`, `403` → ERR-01, nada en el dispositivo) |
| CONTRATO-HU-07 v5 | §5 (BIT-01 y BIT-02, filtros, etiquetas, "Cargar más", error y lista vacía) |
| CONTRATO-HU-04 v6 | Todo el contrato (feature) |

Los textos son los de la tabla "Nombres que no se negocian" de cada contrato, letra por letra.

#### 1.2 Comportamiento de la app Expo que se conserva (no estaba en las tablas de los contratos)

El TESTER lo confirma contra la referencia `hu-04-expo-referencia` (las pruebas Jest y el código) al escribir sus casos. Si algo no coincide, se corrige **este** contrato, no la app.

| Caso | Comportamiento | Origen |
|---|---|---|
| Retomar la sesión | Al abrir la app con un token guardado, la app pide `GET /v1/me` y va al inicio de su rol, sin pasar por AUTH-01 | `App.tsx` (`restaurar`), pruebas `HU01_retomar_*` |
| Retomar con la sesión vencida | Si ese `GET /v1/me` (o la renovación) responde `401 SESION_VENCIDA`, la app muestra AUTH-03 ("Su sesión se cerró por inactividad. Ingrese de nuevo.") y el almacenamiento queda vacío | `ENCARGO-HU-01-02.md` A1, `PENDIENTES.md` (HU-03) |
| Retomar con todo vencido | Si el token de acceso y el de renovación ya no sirven (`401` en los dos), la app muestra AUTH-01 o AUTH-03 tal como lo hace hoy la referencia (el TESTER fija cuál en su informe) y el almacenamiento queda vacío | `HU01_retomar_todo_vencido.test.tsx` |
| Volver del segundo plano | Si la app vuelve del segundo plano después de más de `inactividad_s` sin interacción, muestra AUTH-03 | `App.tsx` (`revisarAlVolver`, `AppState`) |
| Segundo login | Después de "Salir" o de AUTH-03, un segundo login (del mismo usuario o de otro) funciona igual que el primero y no muestra nada del anterior | CONTRATO-HU-01 §4 (AUTH-03); el rojo de `HU04_sin_cache` en Expo (`8110786`) no se arrastra, pero el caso se prueba |
| Indicadores de espera | Mientras espera, el login y las listas muestran un indicador con la etiqueta de accesibilidad "Ingresando" (login) o "Cargando" (el resto) | Referencia Expo |

#### 1.3 La API sigue igual (pruebas que ya existen)

Estas suites tienen que seguir en verde **sin cambiar una línea** de `services/`:

- `services/api/tests/` (pytest, con el compose local), con el mismo número de casos que en el cierre de la Iteración 1 más los de HU-04 v4 (`Cache-Control: no-store`);
- `services/simuladores/tests/`.

`git diff main...migracion-flutter -- services/ contratos/` tiene que salir vacío, salvo las pruebas nuevas del TESTER en `services/api/tests/` si hicieran falta (no se espera ninguna).

### 2. Interfaz de la app para las pruebas (reemplaza CONTRATO-HU-01 §4 bis v2) — DECISIÓN PROPUESTA 1

El TESTER escribe sus pruebas **solo** contra esta interfaz. El DEV no puede cambiar ningún nombre sin un contrato nuevo.

**Paquete y montaje**

| Qué | Valor exacto |
|---|---|
| Nombre del paquete (`pubspec.yaml`) | `movil_buscador` |
| Widget raíz | `MovilBuscadorApp`, en `apps/movil/lib/app.dart` (`import 'package:movil_buscador/app.dart';`) |
| Constructor | `MovilBuscadorApp({Key? key, required Dependencias dependencias})` |
| Arranque real | `apps/movil/lib/main.dart` arma las `Dependencias` reales y llama a `runApp(MovilBuscadorApp(dependencias: …))`. Las pruebas no lo usan |
| Sin sesión | Montar `MovilBuscadorApp` con un `AlmacenSeguro` vacío muestra AUTH-01 |
| Con token guardado | Montarla con un `AlmacenSeguro` que ya tiene el token retoma la sesión (§1.2) |

**Dependencias y bordes** (en `apps/movil/lib/bordes/`, exportados por `package:movil_buscador/bordes/bordes.dart`):

```dart
/// Todo lo que la app recibe de afuera. Las pruebas pasan dobles.
class Dependencias {
  const Dependencias({
    required this.urlApi,        // p. ej. 'https://localhost:8443'; la app llama a urlApi + '/v1/...'
    required this.clienteHttp,   // package:http; en las pruebas, MockClient de package:http/testing.dart
    required this.almacen,       // token de sesión
    required this.lectorPlaca,   // cámara + OCR (HU-04)
  });
  final String urlApi;
  final http.Client clienteHttp;
  final AlmacenSeguro almacen;
  final LectorPlaca lectorPlaca;
}

/// Almacenamiento seguro del dispositivo (ADR-0013). Real: flutter_secure_storage.
abstract class AlmacenSeguro {
  Future<String?> leer(String clave);
  Future<void> escribir(String clave, String valor);
  Future<void> borrar(String clave);
  /// Todo lo guardado. Las pruebas lo usan para comprobar que queda vacío.
  Future<Map<String, String>> leerTodo();
}

/// Cámara y OCR de la placa (HU-04; reemplaza a lectorPlaca.ts). Real: camera + google_mlkit_text_recognition.
enum PermisoCamara { concedido, denegado }

class LecturaPlaca {
  const LecturaPlaca(this.texto);
  /// null si no se reconoció ningún texto.
  final String? texto;
}

abstract class LectorPlaca {
  /// Si nunca se pidió, lo pide al sistema. No abre la cámara.
  Future<PermisoCamara> asegurarPermisoCamara();
  /// El visor en vivo de OCR-01. No lee nada por su cuenta.
  Widget visorCamara({required bool activo});
  /// Toma UNA foto, la lee con OCR en el dispositivo, borra la foto y devuelve solo el texto.
  /// Lanza una excepción si la cámara falla.
  Future<LecturaPlaca> capturarYLeer();
  /// Abre los ajustes de la app en el sistema (OCR-04).
  Future<void> abrirAjustes();
}
```

**Reglas de la interfaz**

| Caso | Valor exacto | Origen |
|---|---|---|
| Toda la red pasa por `clienteHttp` | Ninguna solicitud de la app sale por otro camino (ni `HttpClient` de `dart:io` directo ni otro cliente). Se comprueba con `grep` en `apps/movil/lib/`: `dart:io` `HttpClient`, `dio` y otros clientes solo pueden aparecer dentro de `lib/main.dart` o `lib/bordes/` si el DEV los usa para crear el cliente real | ADR-0017 regla 1 · DECISIÓN PROPUESTA 2 |
| La cámara y ML Kit solo en el borde | Fuera de `lib/bordes/`, ningún archivo importa `package:camera`, `package:google_mlkit_*`, `package:permission_handler` ni `package:flutter_secure_storage` (`grep` en `apps/movil/lib/`). Ninguna función del borde devuelve una ruta de archivo ni una imagen | CONTRATO-HU-04 v5 §1, ADR-0017 regla 1 |
| Vista raíz | Un widget con `key: const Key('app-raiz')` envuelve todas las pantallas. **Cuenta como interacción** (CONTRATO-HU-01 §4, sesión activa) cualquier toque que empiece dentro de él (`tester.tap` o `tester.startGesture` sobre `find.byKey(const Key('app-raiz'))` o sobre cualquier widget de la pantalla) | CONTRATO-HU-01 v2 (`testID="app-raiz"`) |
| Atrás de Android | Lo que antes era `hardwareBackPress` es el "atrás" del sistema: en `flutter_test`, `await tester.binding.handlePopRoute()` | CONTRATO-HU-01 v2 (`BackHandler`) |
| Segundo plano | En `flutter_test`, `tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused)` y después `.resumed` | §1.2 |
| Hora y temporizadores | La app toma la hora actual con `clock.now()` del paquete `clock` (nunca `DateTime.now()` directo) y mide la inactividad con `Timer` de `dart:async`. Así el TESTER controla el tiempo con `withClock` y `tester.pump(Duration)` (o `fakeAsync`) | CONTRATO-HU-01 §4 (AUTH-03, AUTH-04 con la hora local) · DECISIÓN PROPUESTA 3 |
| Campos y botones sin texto | Se encuentran por su etiqueta de accesibilidad (`find.bySemanticsLabel`), con los mismos nombres que en Expo: "Usuario", "Clave", "Placa", "Describa el motivo *", "Desde", "Hasta", "Placa leída" (campo de OCR-02), "Leer con cámara" (📷 de PLA-01), "Cerrar" (✕ de OCR-01), "Atrás", "Ingresando" y "Cargando" | Referencia Expo (`accessibilityLabel`), CONTRATO-HU-04 v5 |
| Textos visibles | Se encuentran con `find.text` y el texto exacto de cada contrato | Contratos de cada HU |
| Selector de motivo | Al tocar "Motivo de consulta *" aparecen las descripciones del catálogo como opciones tocables por su texto (por ejemplo "Control vehicular") | CONTRATO-HU-03 §6, referencia Expo |
| URL de la API en el teléfono | `lib/main.dart` toma `urlApi` de `--dart-define=API_URL=…` (reemplaza a `EXPO_PUBLIC_API_URL`). No es un secreto | ADR-0017 · DECISIÓN PROPUESTA 4 |

### 3. Equivalencias de lo que se observaba en Jest

| En Expo / Jest (contratos hasta hoy) | En Flutter / `flutter_test` (desde esta versión) |
|---|---|
| El `fetch` global simulado (contar llamadas, leer el cuerpo y las opciones) | El `MockClient` que se pasa en `clienteHttp`: cuenta las solicitudes, su método, URL, cabeceras y cuerpo |
| El `expo-secure-store` simulado "sin ninguna clave" | `almacen.leerTodo()` devuelve un mapa vacío |
| `jest.mock` de `src/camara/lectorPlaca.ts` | Un doble de `LectorPlaca` en `dependencias.lectorPlaca` |
| `testID="app-raiz"` y `touchStart` | `Key('app-raiz')` y un toque dentro de ella |
| `BackHandler` / `hardwareBackPress` | `tester.binding.handlePopRoute()` |
| `accessibilityLabel` | Etiqueta de accesibilidad (`Semantics`) |
| `fetch` con `cache: 'no-store'` (HU-04 v4) | La app no usa ninguna caché HTTP: ningún paquete de caché en `pubspec.yaml` (`dio_cache_interceptor`, `flutter_cache_manager`, `http_cache*`, `cached_network_image`) y, en el teléfono, ninguna respuesta de `/v1/` en el directorio de caché de la app (CONTRATO-HU-04 v6 §6) |
| Capturas de Jest para el UX | Capturas de `flutter_test` (fuera del repositorio) y del teléfono (§10) |

### 4. Pantalla: margen seguro (safe area) en todas las pantallas

| Caso | Salida esperada | Origen |
|---|---|---|
| Arriba | La franja "DATOS SINTÉTICOS · PROTOTIPO" empieza debajo de la barra de estado de Android. La zona de la barra se pinta del mismo fondo oscuro de la franja con íconos claros (o fondo blanco con íconos oscuros), sin superponerse | `docs/ux/revisiones/HU-04.md` obs. 2 (BLOQUEA), ENCARGO-HU-04 M-9 |
| Abajo | Ningún botón queda bajo la barra de navegación ni la línea de gestos; sobre todo "Capturar" e "Ingresar manualmente" en OCR-01 | Ídem |
| Una sola vez | Se resuelve una vez para todas las pantallas (por ejemplo, `SafeArea` en la raíz) | ENCARGO-HU-04 M-9 |
| Cómo se verifica | Capturas del S23 Ultra de OCR-01 (con el visor), OCR-02, PLA-01 y HOME-01: la barra de estado y la franja se leen enteras. Una captura de `flutter_test` no sirve (no hay barra de estado) | `docs/ux/revisiones/HU-04.md` obs. 2, punto 5 |

### 5. El repositorio después de la migración (mejora medible)

| Qué se mide | Hoy (`main` `47ace7b`) | Después | Cómo se comprueba |
|---|---|---|---|
| Código Expo en `apps/movil/` | `App.tsx`, `index.ts`, `package.json`, `package-lock.json`, `tsconfig.json`, `app.json`, `src/` (unas 2.400 líneas de TypeScript) | Ninguno de esos archivos. Ningún `.ts` ni `.tsx` en `apps/movil/` | `git ls-files apps/movil` |
| Pruebas Jest | `apps/movil/__tests__/` (7 archivos en la referencia) | No existe | `git ls-files apps/movil/__tests__` vacío |
| Dependencias de Expo | `expo`, `react-native` y los paquetes `@react-native-*` / `expo-*` | Ninguna mención en `apps/movil/pubspec.yaml` ni en `apps/movil/android/` | `grep -ri "expo\|react-native" apps/movil --include=*.yaml --include=*.gradle* --include=*.xml` vacío |
| Análisis estático | — | `flutter analyze` sin errores ni avisos en `apps/movil/` | Comando |
| Pruebas de la app | Jest: 111/111 en el veredicto parcial de HU-04 | Cada caso de las pruebas Jest de la referencia tiene su equivalente en `flutter_test` (los casos se mantienen; el código no), más los de M-9 a M-12 que faltaban | Matriz del TESTER en `informes/TESTER-MIGRACION-FLUTTER.md`: caso Jest → prueba Dart |

El historial no se reescribe: el código Expo queda en `main` hasta el merge y en la etiqueta `hu-04-expo-referencia`.

### 6. Build, versiones y secretos

| Caso | Salida esperada | Origen |
|---|---|---|
| Versión de Flutter | El DEV fija **una versión estable de Flutter** (y su Dart) al empezar, la escribe en `apps/movil/pubspec.yaml` (`environment`, con `flutter:` exacto) y en su informe, y no se cambia hasta el cierre del MVP. El LEAD la anota en el changelog de este contrato | ADR-0017 regla 5 · DECISIÓN PROPUESTA 5 |
| Dependencias exactas | Cada dependencia de `pubspec.yaml` lleva versión exacta (sin `^`), y `pubspec.lock` se versiona | ADR-0017 ("el LEAD fija las versiones") · DECISIÓN PROPUESTA 5 |
| Paquetes | `camera` (solo `takePicture()`, **nunca** `startImageStream`), `google_mlkit_text_recognition`, `flutter_secure_storage`, `http`, `clock`. Cualquier otro paquete con código nativo lo justifica el DEV en su informe. `google_mlkit_face_detection` y `geolocator` **no se agregan** en este ciclo (son de HU-05 y HU-09) | ADR-0017, regla 6 |
| Sin flujo continuo | `grep -r startImageStream apps/movil/lib` vacío | ADR-0017 alternativa D, regla 6 |
| Identificador de la app | `applicationId` `pe.prototipo.movilbuscador` y nombre visible "Movil Buscador", los mismos de Expo, para que los comandos `adb … run-as pe.prototipo.movilbuscador` de HU-04 sigan valiendo | CONTRATO-HU-04 v5 §6 · DECISIÓN PROPUESTA 6 |
| Respaldo | `android:allowBackup="false"` en el manifiesto | ADR-0017 (fila del token) |
| Conexión de depuración | `apps/movil/android/app/src/main/res/xml/network_security_config.xml` escrito a mano: el `base-config` confía solo en los certificados del sistema y no permite texto plano; los certificados del usuario solo dentro de `<debug-overrides>` | ADR-0017 regla 4, CONTRATO-HU-04 v3 §8 |
| Release no depurable | `flutter build apk --release` da un APK sin `application-debuggable` (`aapt dump badging` o `apkanalyzer`) | CONTRATO-HU-04 v3 §8 |
| Llave de firma fuera del repositorio | El APK de release se firma con una llave que vive fuera del repositorio. `.gitignore` agrega `apps/movil/android/key.properties`, `*.jks` y `*.keystore`, y `git ls-files` no muestra ninguno. El informe del DEV dice dónde vive (sin la clave) y cómo se borra en el acta de cierre | ADR-0017 (consecuencias), regla 8 |
| Sin secretos ni fotos | `git ls-files` no muestra `.crt`, `.pem`, `.key`, `.der`, `.jks`, `.keystore` ni imágenes de captura. Las únicas imágenes permitidas en `apps/movil/` son los íconos de la app | Regla 8 |

### 7. ML Kit: variante empaquetada (NO VERIFICADO del ARCH)

| Caso | Salida esperada | Origen |
|---|---|---|
| OCR de la placa | El DEV confirma, en el `android/build.gradle` del plugin `google_mlkit_text_recognition` **de la versión fijada**, que depende de `com.google.mlkit:text-recognition` (variante empaquetada) y **no** de `com.google.android.gms:play-services-mlkit-text-recognition`. Lo confirma también en el APK (`./gradlew :app:dependencies` o el árbol de dependencias). Pega las líneas en su informe | Evaluación §7, ADR-0017 regla 3 |
| Calidad facial (para HU-05) | El DEV revisa el `android/build.gradle` del plugin `google_mlkit_face_detection` en la misma línea de versiones y dice si usa `com.google.mlkit:face-detection` (empaquetada). **No lo agrega** a la app | Evaluación §7, ESTADO-2026-11-20 (pendiente del contrato de HU-05) |
| Si alguno usa Google Play services | El DEV lo reporta como hueco del contrato y no lo resuelve solo (forzar la dependencia es una decisión) | Regla del LEAD |
| Telemetría | Sigue la decisión A (2026-11-20): el aviso de OCR-01 y la revisión de la cola `datatransport` en el teléfono (CONTRATO-HU-04 v6 §3 y §6) | ADR-0017 regla 3 |

### 8. Qué se prueba dónde

| Parte | `flutter_test` (`apps/movil/test/`) | `integration_test` (`apps/movil/integration_test/`) en el S23 Ultra | A mano en el S23 Ultra (mini sesión) |
|---|---|---|---|
| HU-01, 02, 03 y 07 en la app (§1.1 y §1.2) | **Sí, todo**, con `MockClient` y los dobles | Opcional: un recorrido de humo contra la API local | Login, placa y bitácora una vez |
| HU-04 en la app (contrato v6 §2 a §5) | **Sí, todo**, con el doble de `LectorPlaca` | Opcional | Paso a paso (contrato v6 §6) |
| Interfaz y repositorio (§2, §5 y §6) | — | — | `grep`, `git ls-files`, `flutter analyze`, `aapt` |
| Safe area (§4) | No | No | Capturas |
| Variante empaquetada (§7) | — | — | Informe del DEV; el LEAD lo revisa en el veredicto |
| La foto se borra, sin caché en disco, cola de telemetría, la placa impresa se lee, permiso real, sin red, 30 s sin lectura (HU-04 v6 §6) | No | Puede automatizar lo que no necesite `adb` | **Sí**, con `adb` |

Lo que necesite el teléfono y no se pueda hacer a tiempo queda `NO VERIFICADO` y se escala.

### 9. Lo que se reutiliza de Expo (evaluación §3)

| Qué | Cómo se reutiliza |
|---|---|
| Normalización y validación de la placa (`src/camara/placaLeida.ts`, `proponerPlaca`) | El DEV la porta a Dart con el mismo algoritmo. La tabla de ejemplos de CONTRATO-HU-04 §4 no cambia |
| Textos y estados de OCR-01 a OCR-04 y el aviso de telemetría | Los mismos, letra por letra (CONTRATO-HU-04 v6) |
| Lista de casos del TESTER (Jest) | El TESTER porta cada caso a `flutter_test` (§5, matriz) |
| Pantallas y textos de HU-01, 02, 03 y 07 | Los mismos (§1.1); el prototipo de UX (`docs/ux/prototipo/`) no cambia |
| `contratos/api/openapi.json` | Fuente de los modelos de la app. Cómo se generan (`openapi-generator` u otro) lo decide el DEV, siempre que la red pase por `clienteHttp` (§2) |
| `eas.json`, `app.json`, `plugins/`, `package.json` | **No se reutilizan**: desaparecen |

### 10. Revisión del UX y orden del cierre

1. **DEV** entrega con `ENTREGA DEV` (informe `informes/DEV-MIGRACION-FLUTTER.md`): la app, la versión de Flutter fijada, la §7 y las capturas para el UX (de `flutter_test` y del teléfono, **fuera del repositorio**).
2. **TESTER** corre las pruebas de lo tocado y entrega con `ENTREGA TESTER` (informe `informes/TESTER-MIGRACION-FLUTTER.md`, con la matriz de la §5).
3. **UX** revisa todas las pantallas del encabezado contra los wireframes, incluida la safe area (§4) con capturas del S23 Ultra. Las vueltas que hagan falta.
4. **Mini sesión física** con el PM y el humano en el S23 Ultra: HU-04 v6 §6 y §8, y la §4.
5. **Una sola suite completa** (pytest de la API y de los simuladores, `flutter test`, y `integration_test` si existe) sobre el commit definitivo, con orden expresa del LEAD.
6. **Veredicto** (skill `veredicto`) con la matriz de trazabilidad.

## Nombres que no se negocian

| Tipo | Valor exacto |
|---|---|
| Paquete | `movil_buscador` |
| Widget raíz | `MovilBuscadorApp` en `lib/app.dart`, con `dependencias:` |
| Dependencias | `Dependencias` (`urlApi`, `clienteHttp`, `almacen`, `lectorPlaca`) |
| Bordes | `lib/bordes/bordes.dart` · `AlmacenSeguro` (`leer`, `escribir`, `borrar`, `leerTodo`) · `LectorPlaca` (`asegurarPermisoCamara`, `visorCamara`, `capturarYLeer`, `abrirAjustes`) · `PermisoCamara.concedido` · `PermisoCamara.denegado` · `LecturaPlaca` (`texto`) |
| Vista raíz | `Key('app-raiz')` |
| Etiquetas de accesibilidad | "Usuario" · "Clave" · "Placa" · "Describa el motivo *" · "Desde" · "Hasta" · "Placa leída" · "Leer con cámara" · "Cerrar" · "Atrás" · "Ingresando" · "Cargando" |
| URL de la API | `--dart-define=API_URL=…` |
| Identificador de la app | `pe.prototipo.movilbuscador` · "Movil Buscador" |
| Informes | `informes/DEV-MIGRACION-FLUTTER.md` · `informes/TESTER-MIGRACION-FLUTTER.md` |
| Textos de pantalla | Los de cada contrato (HU-01 v6, HU-02 v4, HU-03 v5, HU-07 v5, HU-04 v6) |

## Rutas de cada rol

| Rol | Rutas | Origen |
|---|---|---|
| TESTER | `apps/movil/test/`, `apps/movil/integration_test/`, `apps/movil/.maestro/` (si lo usa), `pruebas/datos/` (guion de la mini sesión y `revisar_datatransport.py`, sin imágenes), `services/api/tests/` (solo si hiciera falta), `informes/TESTER-*.md`. **Borra** `apps/movil/__tests__/` en un commit suyo | AGENTS.md (`d6d97dd`) |
| DEV | `apps/movil/` (salvo `test/`, `integration_test/` y `.maestro/`), incluidos `pubspec.yaml`, `pubspec.lock`, `android/`, `lib/` y la configuración del análisis; `.gitignore` (solo agregar); `informes/DEV-*.md`. **Borra** el código Expo de `apps/movil/` (§5) | AGENTS.md |
| Nadie | `services/`, `contratos/`, `infra/` (no hace falta tocarlos en este ciclo; si alguien cree que sí, es un hueco del contrato) | §1.3 |

Las capturas, las placas impresas y la llave de firma quedan **fuera del repositorio**.

## Avisos de contexto

- **Herramientas en esta PC (2026-11-24):** no hay Flutter SDK en el `PATH` ni Android SDK en la ruta por defecto; sí hay `adb` (`C:\Android\platform-tools`) y Java 21. El DEV y el TESTER instalan el SDK de la versión fijada (§6) y lo dicen en su informe. El humano puede tener que aprobar la instalación.
- **El APK nuevo no se instala encima del de Expo:** tiene otra firma. En el S23 Ultra hay que desinstalar antes "Movil Buscador" de Expo (lo dice el DEV en su informe y la guía de DESPLIEGUE-01 v2).
- **Riesgo del cronograma (evaluación §5):** si la migración se atrasa más de 2 días, la demo del 10-dic se hace con el último APK de Expo. El LEAD avisa al PM en cuanto lo vea.
- **Proxy durante este ciclo:** el compose local sigue con Caddy hasta DESPLIEGUE-01 v2. La conexión del teléfono (HU-04 v6 §8) usa la CA local de Caddy en este ciclo.
- **iOS** queda fuera (ADR-0010, PA #12).
- La palabra prohibida (regla 1) no puede aparecer en ningún texto, nombre ni comentario nuevo.

## Decisiones propuestas (no venían en la tarea)

| # | Decisión | Por qué hace falta | Estado |
|---|---|---|---|
| 1 | La interfaz de la §2: paquete `movil_buscador`, `MovilBuscadorApp(dependencias:)`, `Dependencias` con cuatro campos, interfaces `AlmacenSeguro` y `LectorPlaca`, `Key('app-raiz')`, las etiquetas de accesibilidad de Expo y el "atrás" con `handlePopRoute` | El ADR-0017 pide que el LEAD fije los nombres de las interfaces. Sin una interfaz fija, el TESTER tendría que adivinar cómo monta el DEV la app (como pasó en HU-01 v2) | Pendiente |
| 2 | La red pasa por un `http.Client` de `package:http` inyectado, y el TESTER usa `MockClient`. El ADR-0017 nombra `dart-dio` como referencia del cliente generado: si el DEV usa `dio` por dentro, igual tiene que pasar todas las solicitudes por `clienteHttp` | `MockClient` es la forma estándar de simular la red en `flutter_test` y equivale al `fetch` simulado de Jest. Un adaptador de `dio` sería un segundo mecanismo | Pendiente |
| 3 | La hora sale de `clock.now()` (paquete `clock`) y la inactividad se mide con `Timer` | Sin esto, el TESTER no puede probar AUTH-03 (10 min) ni la hora de AUTH-04 sin esperar en tiempo real | Pendiente |
| 4 | La URL de la API entra por `--dart-define=API_URL` | Reemplaza a `EXPO_PUBLIC_API_URL`; DESPLIEGUE-01 v2 la usa para el APK de la demo | Pendiente |
| 5 | El DEV fija la versión estable de Flutter al empezar y las dependencias exactas, y el LEAD la anota en el changelog sin una vuelta de aprobación (no cambia nada observable) | El ADR-0017 pide fijar la versión. El LEAD no puede comprobar hoy cuál es la estable vigente, porque Flutter no está instalado | Pendiente |
| 6 | Se mantienen el `applicationId` `pe.prototipo.movilbuscador` y el nombre "Movil Buscador" | Los pasos con `adb run-as` de HU-04 y la guía de los probadores ya los usan | Pendiente |
| 7 | Los casos de la §1.2 (retomar la sesión, volver del segundo plano, segundo login e indicadores de espera) se conservan aunque no estaban en las tablas de los contratos | Es el comportamiento aceptado en Expo. En un refactor no se cambia lo observable | Pendiente |
| 8 | Un solo encargo, un solo ciclo y un solo veredicto para las cinco HU de la app | Comparten la interfaz, el build y la revisión del UX. Separarlas duplicaría el montaje y la mini sesión | Pendiente |

## Fuera del contrato (decide el DEV)

- La arquitectura interna de la app (Riverpod o `ChangeNotifier`, cómo navega, cómo organiza `lib/`), siempre que el estado viva en memoria salvo el token (ADR-0013) y que "atrás" no vuelva a una pantalla de la sesión anterior.
- Cómo se generan los modelos desde `contratos/api/openapi.json`, y si usa `dio` por dentro del cliente real (con la red pasando por `clienteHttp`).
- La resolución de la cámara, cómo borra el JPEG temporal (siempre en un `finally`) y cómo pide el permiso.
- Cómo instala el SDK y dónde guarda la llave de firma, dentro de la §6.

## Preguntas abiertas para el humano

1. **ADR-0017 a 0020 en `main`.** Están solo en `entregables-osigp`. ¿Se mergea `entregables-osigp` a `main` antes de levantar al DEV y al TESTER (y el LEAD rebasa `migracion-flutter` sobre ese `main`), o los agentes leen los ADR desde `origin/entregables-osigp`? **Recomendación del LEAD:** mergearla antes, para que la rama de trabajo tenga los ADR que el contrato cita.
2. **Decisiones 1 a 8:** ¿se aprueban tal cual?
3. **Mini sesión física:** ¿la hacen el PM y el humano entre el 4 y el 5-dic, antes del veredicto? El plan deja un día para el veredicto (5 y 6-dic).
4. **Instalación del SDK:** ¿el humano autoriza que el DEV y el TESTER instalen el Flutter SDK y el Android SDK (command-line tools) en esta PC?

## Changelog

| Versión | Fecha | Cambio | Motivo | Aprobado por |
|---|---|---|---|---|
| v1 | 2026-11-24 | Versión inicial | Encargo PM → LEAD (2026-11-24), tarea 2: migración de la app a Flutter (ADR-0017, escenario 1) | Pendiente |
