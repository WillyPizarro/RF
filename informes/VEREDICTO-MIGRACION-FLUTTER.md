# Veredicto — MIGRACION-FLUTTER (app móvil en Flutter: HU-01, 02, 03 y 07, más HU-04)

**Fecha:** 2026-11-25 · **LEAD** · Rama `migracion-flutter` (sin push), base `main` `1204a77`.
**Contratos:** `docs/contratos/CONTRATO-MIGRACION-FLUTTER.md` **v1.5** (aprobado por el humano vía PM el 2026-11-25) y `docs/contratos/CONTRATO-HU-04.md` **v7** (aprobado por el humano vía PM el 2026-11-25; precisión solo de texto). Encargo: `docs/contratos/ENCARGO-MIGRACION-FLUTTER.md`, de la M-1 a la M-17.
**Entregas:**
- DEV: código definitivo de la app `d81c6f9` (M-15) e informe `bb36969`.
- TESTER: suite completa `ebe8e5d` (M-16, informe `d16e831`) y corrección de dos pruebas `2bb50b3` (M-17).
- UX: aprobación final `54906c3`.
- ARCH: nota en ADR-0017 regla 4 (`ad57ee3`).

## Resultado

**VERDE.** Los `NO VERIFICADO` están aceptados por el humano (vía PM, 2026-11-25). Todos los casos del contrato tienen evidencia en verde o un `NO VERIFICADO` con su motivo. Los dos rojos de la suite completa se arbitraron como **"se apartó la prueba"** (vuelta 1). Los corrigió el TESTER y el LEAD verificó la corrección sobre `2bb50b3`.

## Corridas

| Suite | Commit | Resultado | Quién |
|---|---|---|---|
| API (`pytest services/api/tests --integracion`, `PROXY_DISPONIBLE=1`, por el proxy de `https://localhost:8443`) | `ebe8e5d` | 207 pasan, 2 rojos (arbitrados), 2 omitidas por contrato | TESTER (M-16) |
| `test_hu04_sin_cache.py` (28, red interna y proxy) | `2bb50b3` | **28/28** | LEAD |
| Simuladores (dentro de la red, opción B, sin `--reinicio`) | `ebe8e5d` | 115 pasan, 0 rojos, 27 `NO VERIFICADO` | TESTER (M-16) |
| `flutter analyze` | `2bb50b3` | Sin avisos | LEAD |
| `flutter test` | `2bb50b3` | **138/138** | LEAD |
| `integration_test` | — | No aplica: `apps/movil/integration_test/` no existe | — |
| Mini sesión física en el S23 Ultra (Android 16) | APK debug `6d6b0405`, después `5f62f6a4`; release `48f8117a`, después `65799fb6` | Tres vueltas (M-11 a M-15). Única falla funcional: S14, corregida en la M-15 y verde en la tercera vuelta | DEV con `adb` y el humano en el teléfono, vía PM |

Entre `ebe8e5d` y `2bb50b3` solo cambian `apps/movil/test/hu01_hu02_test.dart`, `services/api/tests/test_hu04_sin_cache.py` y documentos del LEAD. Por eso los resultados de la M-16 para el resto de la API y de los simuladores siguen valiendo.

**APK finales**, fuera del repositorio, en `C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\`:
- depuración `5f62f6a4c8eb192e38bddd3895409a84325f12e914c69b1fc1801ad08b997085`;
- release `65799fb64635fc424efab1c255f5202a729a6da68a8d28aa0c16d67184c6bdc6`.

## Propiedad de rutas

`git log main..HEAD --name-only`, agrupado por prefijo y comparado contra `AGENTS.md` y las "Rutas de cada rol" del contrato:
- **Todos los commits llevan su prefijo de rol.**
- `[TESTER]` borra `apps/movil/__tests__/` (5 archivos): fuera de sus rutas de `AGENTS.md`, pero **lo encarga el contrato** (§5, rutas del TESTER: "Borra `apps/movil/__tests__/`"). No es un hallazgo.
- En `services/` cambian solo `services/api/app/traza.py` (DEV) y `services/api/tests/test_hu04_sin_cache.py` (TESTER), como permite la §1.3 v1.4. `contratos/`, `infra/` y `services/simuladores/` no cambian: el diff contra `main` sale vacío.
- `[ARCH]` toca solo `docs/arch/`; `[UX]` solo `docs/ux/`; `[LEAD]` solo `docs/contratos/` y este informe.

**Sin hallazgos de rutas.**

## Arbitrajes

| # | Rojo | Qué dice el contrato | Desenlace | Destinatario | Vuelta | Cierre |
|---|---|---|---|---|---|---|
| 1 | Login en la S23 (paso 1.2): `TLS handshake error … EOF` y ningún acceso a `/v1/auth/login` (M-12) | La v1.4 §6 pedía la CA de usuario solo en `<debug-overrides>`, pero no decía qué cliente HTTP. El de `dart:io` no lee el `network_security_config` | **El contrato no lo decía** | Humano: opción A (`ok_http`) con plan B → contrato **v1.5** | — | M-13; login OK en la segunda vuelta |
| 2 | El aviso de ML Kit vuelve a salir tras recrear la actividad (antes de S5) | HU-04 v6 §3 dice "en cada sesión", pero no aclaraba qué pasa con una sesión retomada | **El contrato no lo decía** | Humano: opción A → **HU-04 v7**, solo texto | — | Sin código |
| 3 | S14: "Desde" y "Hasta" sin "/" en Samsung Keyboard; `25112026` no se puede filtrar | §1.1: el refactor no cambia el comportamiento. En Expo, `numbers-and-punctuation` (obs. 4 de HU-03-07) | **Se apartó el código** | DEV (M-15) | 1 | `d81c6f9` con la "/" automática; prueba nueva del TESTER (falla en `875cb26` y pasa en `d81c6f9`); S14-v3 en verde |
| 4 | Paso 8.5: marcas `/v1/` y `token_*` en `app_flutter/flutter_assets/kernel_blob.bin` | HU-04 v6 §6 mira `cache/` y `files/`, y las dos están limpias. El archivo marcado es el código del APK (mismo SHA-256) | **Se apartó la prueba** | TESTER (M-15) | 1 | `revisar_cache_app.py --apk` |
| 5 | Paso 10.3 de la primera vuelta: la consulta llegó a la API "sin red" | HU-04 v6 §3 pide un teléfono sin red. El keep-alive de OkHttp sobrevivió a `adb reverse --remove`, así que la red no estaba cortada | **Se apartó la prueba** | TESTER (M-15) | 1 | Repetido con el cable USB fuera: PLA-07, 0 solicitudes; guion corregido |
| 6 | Suite: `test_hu04_sin_cache.py [login-401]` dio `423` | HU-01: un usuario, aunque no exista, se bloquea al 5.º fallo. La prueba usaba un usuario fijo que acumulaba fallos entre corridas | **Se apartó la prueba** | TESTER (M-17) | 1 | `2bb50b3`, 28/28 (LEAD) |
| 7 | Suite: `hu01_hu02_test.dart` AUTH-04 | El código muestra HH:MM y los minutos restantes (`pantalla_login.dart:18`). La prueba dependía del reloj real en el borde de 900 s | **Se apartó la prueba** | TESTER (M-17) | 1 | `2bb50b3`, con `withClock`; 138/138 (LEAD) |

**Ningún desacuerdo pasó de la vuelta 1.**

## Trampas

- **Pruebas modificadas entre vueltas:** `hu01_hu02_test.dart` AUTH-04 y `test_hu04_sin_cache.py [login-401]` cambiaron después de la suite completa. Las dos están justificadas por el arbitraje de la M-17 (se apartó la prueba) y **siguen verificando lo mismo**:
  - AUTH-04: el texto exacto "… a las 17:24 (en 15 min).", la clave vacía, "Ingresar" activo y sin AUTH-02;
  - `login-401`: el `Cache-Control: no-store` del `401`.
  
  Lo comprobé en el diff.
- **Casos especiales para pasar pruebas:** no hay. El formateador de fechas (`pantalla_bitacora.dart`) actúa solo al agregar un dígito al final y no trata ninguna fecha concreta.
- **Pruebas sin aserciones sobre el contrato:** no encontré ninguna en lo que cambió en las M-13 a M-17.

## Matriz de trazabilidad

| Criterio (HU) | Caso del contrato | Prueba / evidencia | Resultado |
|---|---|---|---|
| HU-01 login, AUTH-02 a AUTH-04, retomar, inactividad | MIGRACION §1.1 y §1.2 (CONTRATO-HU-01 v6) | `hu01_hu02_test.dart`, `hu01_retomar_test.dart`; S23 1.1 a 1.3 y 2.4 a 2.8 | 🟢 |
| HU-02 rol en el inicio | §1.1 (HU-02 v4) | `hu01_hu02_test.dart`; S23 1.2 y 2.5 | 🟢 |
| HU-03 consulta de placa con motivo; un error nunca es negativo | §1.1 (HU-03 v5) | `hu03_hu07_test.dart`; S23 2.1 a 2.3 y 10.3 (PLA-07) | 🟢 |
| HU-07 bitácora de solo lectura con filtros | §1.1 (HU-07 v5), obs. 7 (M-15) | `hu03_hu07_test.dart`, incluida "BIT-01 (M-15, obs. 7)"; S23 2.5, 2.6 y S14-v3 | 🟢 |
| HU-04 captura de la placa (OCR-01 a OCR-04), una foto por toque, sin lectura continua | HU-04 v7 §2 a §5; MIGRACION §6 (`startImageStream` prohibido) | `hu04_ocr_test.dart`; `repositorio_test.dart`; S23 4 a 6 y S6 a S13 | 🟢 |
| HU-04 aviso de telemetría | HU-04 v7 §3, sesión retomada incluida | `hu04_ocr_test.dart`; S23 S6 y la observación antes de S5 | 🟢 |
| HU-04 la foto se borra; nada en disco | HU-04 v6 §6 | S23 7.1 a 7.3 (galería sin cambios, ninguna imagen) | 🟢 |
| HU-04 sin caché HTTP | HU-04 v6 §6; MIGRACION §1.3 v1.4 y §6 v1.5 (sin `Cache` de OkHttp) | `test_hu04_sin_cache.py` 28/28; `red_sin_cache_test.dart`; S23 8.3, 8.3b y 8.5 | 🟢 |
| HU-04 sin red | HU-04 v6 §3 | S23 10.2 y 10.3 con el cable fuera | 🟢 |
| HU-04 cola de telemetría | HU-04 v6 §6 | S23 9 y `revisar_datatransport.py`: 5 eventos sin imagen ni placa | 🟢 |
| — (refactor) | Margen seguro (§4) | Capturas S1 a S5; UX `7a16428` | 🟢 |
| — (refactor) | Repositorio sin Expo, Jest ni `.ts` (§5) | `repositorio_test.dart`; `flutter analyze`; `grep -riw` | 🟢 |
| — (refactor) | Versiones exactas, `applicationId`, `allowBackup=false`, llave fuera del repositorio, sin secretos (§6) | `repositorio_test.dart`; S23 0.12 y 11.2 a 11.6 | 🟢 |
| — (refactor) | Cliente `ok_http`: debug entra y release no; ninguna CA en un APK (§6 y §8 v1.5) | S23 1.2, T.2 y T.5 a T.8 (`tls: unknown certificate`); `revisar_ca_apk.py` | 🟢 |
| — (refactor) | Modelo de ML Kit dentro del APK (§7) | Informe del DEV y paso 11 | 🟢 |
| — (refactor) | API sin cambios salvo el `no-store` (§1.3) | `services/api/tests` (207 + 28) | 🟢 |
| — (refactor) | Simuladores sin cambios | 115 dentro de la red | 🟢 (27 `NO VERIFICADO`) |

Los casos "— (refactor)" vienen del contrato de migración, no de una HU. El negocio los aceptó con ADR-0017 y las decisiones del 24-nov.

## NO VERIFICADO

| Qué | Motivo | Aceptado por |
|---|---|---|
| Qué hace en la red `play-services-mlkit-*` | Contrato v1.2 §7, opción A | Humano (2026-11-24) |
| 27 pruebas de los simuladores que corren desde el anfitrión, y `--reinicio` | Sin cambios en `services/simuladores/`, `contratos/` ni `infra/` desde `main` (diff vacío); cubiertas en veredictos anteriores | LEAD (decisión M-16) y **humano (vía PM), 2026-11-25** |
| API: `test_hu01_bitacora_config.py:88` y `test_hu02_perfil_roles.py:55` | Omitidas por contrato (HU-01 decisión 2, HU-02 decisión 3) | Contratos aprobados |
| `integration_test` | No existe en el proyecto | — |
| PLA-02 "con el foco ahí"; colores de PLA-06 y PLA-07 | No es observable de forma estable en `flutter_test`; revisión visual del UX | UX |
| Precisión del OCR (HU-04 §7) | Fuera de este ciclo: fase de pruebas del 16 al 26-dic | Contrato |

## Riesgos para el PR

- `ok_http` 0.1.0 es la única versión publicada. Flutter avisa que aplica KGP y que versiones futuras de Flutter no lo compilarán; con la 3.50.1 fijada compila. Hay que revisarlo cuando se suba Flutter.
- Los ajustes de build en las rutas del DEV (`compileSdk` 37 para `jni` y `ok_http`, reglas `-keep` de R8) y las transitivas que bajan de versión (`jni` 0.10.1, `path_provider_android` 2.2.23, `package_config` 2.2.0) están en el informe del DEV §12.
- La barra de desplazamiento del aviso tiene poco contraste con la letra al máximo: es una nota del UX para la fase de pruebas, no una observación.

## Al cierre (acta de eliminación)

Borrar:
- `C:\Willy\Trabajo\MININTER\venv-pruebas`;
- la CA de Caddy, tanto `C:\Willy\Trabajo\MININTER\ca-local\` como la CA de usuario del S23;
- `C:\Willy\Trabajo\MININTER\flutter-capturas\`, si quedó algo.

Decidir el destino de los APK y las capturas de `Movil_Buscador_capturas\MIGRACION-FLUTTER\`. La llave de firma `C:\Users\Willy\.movil-buscador-firma` se conserva para la demo.
