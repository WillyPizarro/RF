# Informe TESTER — HU-04 Capturar la placa con la cámara (etapa 1)

**Contrato:** `docs/contratos/CONTRATO-HU-04.md` **v4** (siguen vigentes HU-03 v4, HU-07 v4, HU-01 v5, HU-02 v3 y HU-08 v4) · **Encargo:** `docs/contratos/ENCARGO-HU-04.md` (M-1 a M-10) · **Rama:** `hu-04`
**Suite completa de la etapa 1 (M-5), una sola vez:** 2026-11-19/20, sobre la punta de `hu-04` (`37c38b7`, que incluye el commit definitivo del DEV `3367787` y mis pruebas). Arranque con `up -d --build`, los dos compose, el proxy en el puerto alterno (8080/8443) y `PROXY_DISPONIBLE=1`; usuarios cargados con `python -m app.cargar_usuarios` (exit 0).

## Etapa 2 — paso a paso en el S23 Ultra (M-8), 2026-11-20

**Quién:** el humano operó el teléfono; el **PM corrió los comandos `adb`** (cambio de reparto del LEAD) y pasó la tabla. Antes del cambio, el TESTER había corrido solo 0.2, 0.3 y 0.8 (de solo lectura), y los resultados coinciden. Los pasos son los de `pruebas/datos/GUION-HU-04-dispositivo.md`. Dispositivo: SM-S918B (`R5CW21ERL2L`), Android 16.

| Paso | Qué | Resultado | Estado |
|---|---|---|---|
| 0.2 | `adb devices` | `device` | VERDE |
| 0.3 | Versión de Android | 16 | VERDE |
| 0.5 | CA de Caddy como certificado del usuario | La instaló el humano; borró la copia de Descargas | VERDE |
| 0.6 | `adb reverse` 8443 y 8081 | OK | VERDE |
| 0.8 | Galería antes | G0 = 1065 (`DCIM/Camera`), P0 = 5 (`Pictures`) | — (referencia) |
| 1.1 | Login de `agente1` | HOME-01 | VERDE (§8 "Conexión") |
| 1.2 | PLA-01 con motivos | Cargó por HTTPS con la CA | VERDE (§8 "Conexión") |
| 2.1–2.2 | Permiso sin decidir → diálogo del sistema | OK. En el primer intento el humano tocó "Permitir" por error; se reseteó el permiso y se repitió | VERDE |
| 2.3 | "No permitir" → OCR-04 | OK | VERDE (§6 "Permiso real") |
| 2.4 | "Abrir ajustes" | Abre la pantalla de permisos de la app (`com.google.android.permissioncontroller`, `ManagePermissionsActivity`) | VERDE: cumple la **v4** (hallazgo D; con la v3 era una observación) |
| 2.5 | "Permitir solo mientras se usa" → 📷 → OCR-01 en vivo | OK | VERDE |
| 3.1 | 30 s apuntando a `ZZA-101` sin tocar "Capturar" | No aparece OCR-02 | VERDE (§6 "Sin lectura continua", regla 6) |
| 4.1 | Capturar `ZZA-101` | OCR-02 con `ZZA-101`, sin imagen. Captura de pantalla en `C:\Willy\Trabajo\MININTER\hu04-capturas\ocr-02.png`, fuera del repositorio | VERDE (§6 "La placa se lee") |
| 4.2–4.6 | Corregir a `ZZB-201` con el motivo vacío y sin consulta; "Indique el motivo de la consulta."; PLA-06; `ZZZ-999` → PLA-08; cámara tapada → OCR-03 | Conformes, según el humano | VERDE (§5 paso a paso, una vez) |
| 5.1 | 10 capturas seguidas | Hechas | — |
| 5.2 | `run-as … find` de `*.jpg`, `*.jpeg` y `*.png` | Ninguna imagen (21 archivos privados, ninguno de imagen), ni en `files/` ni en `cache/` | VERDE (§6 "La foto se borra", hallazgo A) |
| 5.3 | Galería después | 1065 / 5, sin cambios | VERDE |
| 6.1–6.3 | Modo avión: leer y consultar | Lectura local OK; consulta → "No se pudo completar la consulta; intente nuevamente" (nunca "sin requisitoria") | VERDE (§3 "Sin red") |
| 6.4 | Quitar el modo avión | Lo hizo el humano | — |
| 7.1 | `adb reverse` quitado | OK | — |
| Cierre | Galería e imágenes privadas | 1065 / 5; 0 imágenes | VERDE |

**Pendientes que NO se cierran todavía:**
- **Hallazgo B, caché HTTP en disco** (`/v1/me` y `/v1/motivos` en `cache/http-cache`): da origen a la **v4** (M-10). Pruebas nuevas:
  - `services/api/tests/test_hu04_sin_cache.py` (cabecera `no-store`, por la red interna y por el proxy, en éxito y en error);
  - `apps/movil/__tests__/HU04_sin_cache.test.tsx` (`cache: 'no-store'` en cada `fetch`);
  - el paso 8 del guion para la **mini sesión**.

  Esperan la entrega del DEV de la M-10.
- **Hallazgo C, telemetría de ML Kit:** lo evalúa el ARCH.
- **Safe area** (UX, BLOQUEA, M-9): espera la entrega del DEV. Después corro el Jest completo y agrego la simulación de `react-native-safe-area-context` si hace falta.

## Resultado

| Corrida | Comando | Resultado |
|---|---|---|
| App (Jest completo) | `npx jest --ci` en `apps/movil` | **111 en verde, 0 rojos** (6 archivos). HU-04: **36 en verde** (`HU04_ocr.test.tsx`) |
| §8 sin teléfono | `python pruebas/datos/verificar_prebuild_hu04.py` | **27 OK, 0 FALLA** (ver "Verificación del §8") |
| API, regresión | `PROXY_DISPONIBLE=1 pytest services/api/tests --integracion -rA` (9 min 29 s) | **181 en verde, 0 rojos, 2 omitidas.** Las 2 omitidas son esqueletos `NO VERIFICADO` de HU-01/02 que cubren otras pruebas desde HU-03/07. Las 34 del proxy, en verde |
| Simuladores, regresión de HU-08, en el contenedor | `docker compose … run --rm -T --no-deps simuladores pytest -rA` | 115 en verde, 0 rojos, 27 omitidas (las del anfitrión) |
| Simuladores, regresión de HU-08, desde el anfitrión | `pytest services/simuladores/tests --integracion -rA` | 136 en verde, 0 rojos, 6 omitidas; el origen de fotos quedó vacío |

**Ningún rojo.** Al terminar, `api` quedó con `infra/.env` (`BLOQUEO_INTENTOS=5`, `SESION_INACTIVIDAD_S=600`, `FUENTE_PLACAS_URL` vacía, regex por defecto) y no quedó ningún contenedor de Prism. Ninguna foto ni imagen en el repositorio; las placas son solo sintéticas `ZZ`.

## Caso del contrato → prueba → estado

Todas las pruebas de Jest están en `apps/movil/__tests__/HU04_ocr.test.tsx`. Montan `App.tsx` y simulan el **módulo de borde** `src/camara/lectorPlaca.ts` con `jest.mock` (`asegurarPermisoCamara`, `VisorCamara`, `capturarYLeer`, `abrirAjustes`), además del `fetch` global y `expo-secure-store`.

| § | Caso | Prueba | Estado |
|---|---|---|---|
| 1 | Existe `src/camara/lectorPlaca.ts` | `§1 › existe …` | VERDE |
| 1 | Ningún archivo de `src` fuera del módulo de borde, ni `App.tsx`, importa la librería de cámara ni la de ML Kit (búsqueda de importaciones de paquetes `camera`, `ml-kit`, `text-recognition`, `vision` y `ocr`) | `§1 › ningún archivo …`, `› App.tsx tampoco …` | VERDE |
| 1 | Ninguna función del módulo devuelve una ruta de archivo ni una imagen | Guion, pasos 4.1 y 5.2 (OCR-02 sin imagen; ninguna imagen en disco) | VERDE (etapa 2) |
| 2 | Botón 📷 (`accessibilityLabel="Leer con cámara"`) habilitado | `§2 › el botón …` | VERDE |
| 2 | Permiso concedido → OCR-01; denegado → OCR-04, sin llamar a `capturarYLeer` | `§2 › permiso concedido …`, `› permiso denegado …` | VERDE |
| 3 | OCR-01: textos, `VisorCamara` con `activo: true`; **ninguna** lectura sin tocar "Capturar" (3 s de espera) | `§2 › permiso concedido …`, `§3 › sin tocar "Capturar" …` | VERDE |
| 3 | Una sola lectura por toque, "Capturar" desactivado mientras espera, un 2.º toque no lee; cada toque es una lectura (2 en total) | `§3 › una sola lectura …`, `› cada toque …` | VERDE |
| 3 | Falla de la cámara → OCR-03 (nunca un resultado) | `§3 › falla de la cámara …` | VERDE |
| 3 | "✕" → PLA-01 sin cambios (placa y motivo); "Ingresar manualmente" desde OCR-01, OCR-03 y OCR-04 → PLA-01 sin cambios | `§3 › "✕" …`, `› "Ingresar manualmente" …` (3) | VERDE. El foco en el campo "Placa" no se verifica en Jest |
| 3 | Sin red (modo avión) | Guion, pasos 6.1 a 6.3 | VERDE (etapa 2) |
| 4 | La tabla completa: `ZZA-101`, `zza-101`, `ZZA 101`, `ZZA.101`, `PERU\nZZB-201\nLIMA`, `ZZA-101 ZZB-201` → OCR-02 con su valor; `ZZA-1O1`, `PERU`, `""`, `null` → OCR-03 | `§4 › …` (10) | VERDE |
| 4 | Si cambia `formato_placa.regex`, cambia lo que se acepta | `§4 › si la API cambia …` | VERDE |
| 5 | OCR-02: textos y campo editable, **ninguna imagen** | `§5 › OCR-02 …` | VERDE |
| 5 | Corregir → PLA-01 con el texto corregido | `§5 › corregir …` | VERDE |
| 5 | Nunca consulta sola: **0 llamadas a `fetch`** entre 📷 y "Consultar"; el motivo vacío sigue vacío (PLA-02), y el elegido antes se conserva | `§5 › nunca consulta sola …`, `› el motivo elegido …` | VERDE |
| 5 | Sigue HU-03: una corrección inválida se rechaza en PLA-03 sin enviar | `§5 › sigue HU-03 …` | VERDE |
| 5 | "Volver a capturar" (descarta el valor), "Volver a intentar", "Abrir ajustes" (`abrirAjustes()` una vez), volver con permiso | `§5 › …` (4) | VERDE |
| 6 | Ninguna llamada a `fetch` en todo OCR-01 → OCR-03; el cuerpo de la consulta es el de HU-03 (solo `placa`, `motivo_codigo`, `motivo_texto`) | `§6 › en todo el flujo …`, `§5 › el motivo elegido …` | VERDE |
| 6 | SecureStore sin claves nuevas después de leer | `§6 › después de leer …` | VERDE |
| 6 | La foto se borra (`adb … find`), sin lectura continua (30 s), la placa impresa se lee, permiso real (v4: pantalla de Ajustes o de permisos) | Guion, pasos 2, 3, 4 y 5 | VERDE (etapa 2) |
| 6 | Sin caché HTTP (v4): cabecera `no-store` en la API; `cache: 'no-store'` en la app; `cache/http-cache` sin `/v1/` | `test_hu04_sin_cache.py`, `HU04_sin_cache.test.tsx`, guion paso 8 | Pendiente: entrega del DEV de la M-10 y mini sesión |
| 7 | Precisión del OCR | — | **Va aparte** (v2), en la fase de pruebas del 16 al 26-dic, con `pruebas/datos/ocr-precision.csv` |
| 8 | Confianza en certificados del usuario solo en depuración; `base-config` sin texto plano; `release` no depurable; sin certificados versionados | `pruebas/datos/verificar_prebuild_hu04.py` | **VERDE** (27 OK); ver la forma usada abajo |
| 8 | Conexión real del dev build con la CA de Caddy | Guion, pasos 0.5, 0.6, 1.1 y 1.2 | VERDE (etapa 2) |

## Verificación del §8 (M-3), sin teléfono

`pruebas/datos/verificar_prebuild_hu04.py` copia `apps/movil` a una carpeta temporal **fuera del repositorio** (con `node_modules` enlazado por un junction, que se quita sin tocar el original) y genera `android/` allí.

**Cómo se genera (documentado en el script, como pidió el LEAD):** en este equipo, `npx expo prebuild --platform android` **no termina**. Lo comprobé: más de 10 min sin avanzar después de "Running prebuild", en `withPackageRefactor` (aviso del DEV). Tampoco termina la plantilla de Expo con **todos** los plugins (`compileModsAsync`): 10 min. Por eso, la forma por defecto es la **c**:
1. la plantilla del propio Expo (`node_modules/expo/template.tgz`);
2. los mods base de Expo;
3. **solo los plugins locales de la app** (los de `app.json` que empiezan con `./`; aquí `./plugins/redDepuracion`), con `withPlugins` + `compileModsAsync`.

Es lo que haría el prebuild después de copiar la plantilla, y genera el mismo `network_security_config.xml` y el mismo manifiesto. No evalúa los plugins de terceros (`expo-dev-client`, `expo-secure-store`, `expo-camera`), que no declaran un `network_security_config`. Con `--intentar-completo`, el script prueba antes las formas a y b, con 4 min cada una.

**Lo generado** (`res/xml/network_security_config.xml`):

```xml
<network-security-config>
  <base-config cleartextTrafficPermitted="false">
    <trust-anchors><certificates src="system" /></trust-anchors>
  </base-config>
  <debug-overrides>
    <trust-anchors><certificates src="user" /></trust-anchors>
  </debug-overrides>
</network-security-config>
```

**Comprobaciones:**
- El manifiesto lleva `android:networkSecurityConfig="@xml/network_security_config"` y no lleva `android:debuggable`. `expo config --type introspect` da lo mismo.
- El bloque `release` del `build.gradle` no pone `debuggable` en `true`.
- `git ls-files` no tiene ningún `.crt`, `.pem`, `.key` ni `.der`.
- `.gitignore` excluye las cuatro extensiones (`git check-ignore`, en tres rutas cada una).

## Material de la etapa 2 (sin ejecutar)

| Qué | Dónde |
|---|---|
| Hoja A4 de placas (M-1): 8 placas `ZZ` (`ZZA-101`, `ZZB-201`, `ZZZ-999` y 5 de la semilla), una por hoja, A4 horizontal al 90 % (27 × 13,5 cm), fondo blanco, texto negro grueso y "PRUEBA — NO VÁLIDA" fuera del recuadro. Se genera leyendo `semilla.json`. Comprobada con Edge sin ventana: el PDF sale de 8 páginas y cada placa en una línea; sin imágenes | `pruebas/datos/hoja-placas-prueba.html` (generador: `pruebas/datos/generar_hoja_placas.py`) |
| Guion de las pruebas físicas (M-2): casos "Dispositivo" del §6, sin red (§3), conexión (§8) y el paso a paso del §5, con los comandos `adb` exactos | `pruebas/datos/GUION-HU-04-dispositivo.md` |
| Plantilla del CSV de precisión (columnas `placa_impresa,leida,condicion,coincide`), para la fase de pruebas | `pruebas/datos/ocr-precision.csv` |
