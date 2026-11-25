# Informe TESTER — MIGRACION-FLUTTER

**Contrato:** `docs/contratos/CONTRATO-MIGRACION-FLUTTER.md` **v1.1** (con la M-1 y la M-2 del encargo), CONTRATO-HU-01 v6, HU-02 v4, HU-03 v5, HU-07 v5 y HU-04 v6.
**Encargo:** `docs/contratos/ENCARGO-MIGRACION-FLUTTER.md` (M-1 y M-2).
**Rama:** `migracion-flutter`, worktree `C:\Willy\Trabajo\MININTER\Movil_Buscador-flutter`.
**Estado:** **ENTREGA PARCIAL 0 (sin ejecutar).** Las pruebas están escritas contra la interfaz de la §2 y **todavía no se compilaron ni corrieron**: falta la interfaz del DEV (`lib/app.dart`, `lib/bordes/bordes.dart`) y la instalación del SDK compartido (M-2). Todo queda `NO EJECUTADO` hasta la entrega del DEV.

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

Referencia: `apps/movil/__tests__/` en `hu-04-expo-referencia` (7 archivos, **121 casos** contando cada fila de `test.each`). Estado de todas las filas: **NO EJECUTADO** (falta la entrega del DEV).

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
| Imports de cámara, ML Kit, permisos y almacenamiento solo en `lib/bordes/` | `repositorio_test` | NO EJECUTADO |
| `HttpClient`, `dio` y otros clientes solo en `lib/main.dart` o `lib/bordes/` | `repositorio_test` | NO EJECUTADO |
| `DateTime.now()` no aparece en `lib/` (la hora sale de `clock.now()`) | `repositorio_test` | NO EJECUTADO |
| `startImageStream` no aparece en `lib/` | `repositorio_test` y `grep -r startImageStream apps/movil/lib` | NO EJECUTADO |
| Ningún paquete de caché | `repositorio_test` | NO EJECUTADO |
| Flutter 3.50.1 en `environment`, dependencias exactas, `pubspec.lock` | `repositorio_test` | NO EJECUTADO |
| Sin Expo: ni `.ts`/`.tsx`, ni `package.json`, ni menciones en `pubspec.yaml` y `android/` | `repositorio_test` y `git ls-files apps/movil` | NO EJECUTADO |
| `apps/movil/__tests__/` borrado | `git ls-files apps/movil/__tests__` vacío (commit del TESTER, cuando la matriz esté en verde) | PENDIENTE |
| `applicationId`, nombre visible, `allowBackup`, `network_security_config.xml` | `repositorio_test` | NO EJECUTADO |
| `.gitignore` con `key.properties`, `*.jks`, `*.keystore`; `git ls-files` sin `.crt`, `.pem`, `.key`, `.der`, `.jks`, `.keystore` | `repositorio_test` y `git ls-files \| grep -E '\.(crt\|pem\|key\|der\|jks\|keystore)$'` | NO EJECUTADO |
| `flutter analyze` sin errores ni avisos | Comando en `apps/movil` | NO EJECUTADO |
| APK de release no depurable | `aapt dump badging` (guion, paso 11) | NO EJECUTADO |
| `git diff main...migracion-flutter -- services/ contratos/` vacío | Comando | NO EJECUTADO |

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

- **Todo lo de este informe está `NO EJECUTADO`** hasta la interfaz del DEV y el SDK.
- **PLA-02 "con el foco ahí"** (HU-03 §6): no lo verificaba Jest; con un selector de motivo, el foco no es observable de forma estable en `flutter_test`. Queda para la revisión del UX.
- **PLA-07 "ícono y color distintos"** y **PLA-06 "gris, sin verde"**: se verifica la ausencia de ✓; el color queda para el UX.
- **Safe area (§4)** y **todo lo del teléfono** (HU-04 v6 §6 y §8): guion de la mini sesión del 4-dic.
