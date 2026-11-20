# Informe TESTER — HU-04 Capturar la placa con la cámara (etapa 1)

**Contrato:** `docs/contratos/CONTRATO-HU-04.md` **v3** (siguen vigentes HU-03 v4, HU-07 v4, HU-01 v5, HU-02 v3 y HU-08 v4) · **Encargo:** `docs/contratos/ENCARGO-HU-04.md` (M-1 a M-5) · **Rama:** `hu-04`
**Suite completa de la etapa 1 (M-5), una sola vez:** 2026-11-19/20, sobre la punta de `hu-04` (`37c38b7`, que incluye el commit definitivo del DEV `3367787` y mis pruebas). Arranque con `up -d --build`, los dos compose, el proxy en el puerto alterno (8080/8443) y `PROXY_DISPONIBLE=1`; usuarios cargados con `python -m app.cargar_usuarios` (exit 0).

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
| 1 | Ninguna función del módulo devuelve una ruta de archivo ni una imagen | — | Pendiente de la etapa 2 (lo que se ve en el teléfono: §6 "La foto se borra") |
| 2 | Botón 📷 (`accessibilityLabel="Leer con cámara"`) habilitado | `§2 › el botón …` | VERDE |
| 2 | Permiso concedido → OCR-01; denegado → OCR-04, sin llamar a `capturarYLeer` | `§2 › permiso concedido …`, `› permiso denegado …` | VERDE |
| 3 | OCR-01: textos, `VisorCamara` con `activo: true`; **ninguna** lectura sin tocar "Capturar" (3 s de espera) | `§2 › permiso concedido …`, `§3 › sin tocar "Capturar" …` | VERDE |
| 3 | Una sola lectura por toque, "Capturar" desactivado mientras espera, un 2.º toque no lee; cada toque es una lectura (2 en total) | `§3 › una sola lectura …`, `› cada toque …` | VERDE |
| 3 | Falla de la cámara → OCR-03 (nunca un resultado) | `§3 › falla de la cámara …` | VERDE |
| 3 | "✕" → PLA-01 sin cambios (placa y motivo); "Ingresar manualmente" desde OCR-01, OCR-03 y OCR-04 → PLA-01 sin cambios | `§3 › "✕" …`, `› "Ingresar manualmente" …` (3) | VERDE. El foco en el campo "Placa" no se verifica en Jest |
| 3 | Sin red (modo avión) | — | Pendiente de la etapa 2 (guion, paso 6) |
| 4 | La tabla completa: `ZZA-101`, `zza-101`, `ZZA 101`, `ZZA.101`, `PERU\nZZB-201\nLIMA`, `ZZA-101 ZZB-201` → OCR-02 con su valor; `ZZA-1O1`, `PERU`, `""`, `null` → OCR-03 | `§4 › …` (10) | VERDE |
| 4 | Si cambia `formato_placa.regex`, cambia lo que se acepta | `§4 › si la API cambia …` | VERDE |
| 5 | OCR-02: textos y campo editable, **ninguna imagen** | `§5 › OCR-02 …` | VERDE |
| 5 | Corregir → PLA-01 con el texto corregido | `§5 › corregir …` | VERDE |
| 5 | Nunca consulta sola: **0 llamadas a `fetch`** entre 📷 y "Consultar"; el motivo vacío sigue vacío (PLA-02), y el elegido antes se conserva | `§5 › nunca consulta sola …`, `› el motivo elegido …` | VERDE |
| 5 | Sigue HU-03: una corrección inválida se rechaza en PLA-03 sin enviar | `§5 › sigue HU-03 …` | VERDE |
| 5 | "Volver a capturar" (descarta el valor), "Volver a intentar", "Abrir ajustes" (`abrirAjustes()` una vez), volver con permiso | `§5 › …` (4) | VERDE |
| 6 | Ninguna llamada a `fetch` en todo OCR-01 → OCR-03; el cuerpo de la consulta es el de HU-03 (solo `placa`, `motivo_codigo`, `motivo_texto`) | `§6 › en todo el flujo …`, `§5 › el motivo elegido …` | VERDE |
| 6 | SecureStore sin claves nuevas después de leer | `§6 › después de leer …` | VERDE |
| 6 | La foto se borra (`adb … find`), sin lectura continua (30 s), la placa impresa se lee, permiso real | — | **Pendientes de la etapa 2** (M-5: no son `NO VERIFICADO`). Guion: `pruebas/datos/GUION-HU-04-dispositivo.md` |
| 7 | Precisión del OCR | — | **Va aparte** (v2), en la fase de pruebas del 16 al 26-dic, con `pruebas/datos/ocr-precision.csv` |
| 8 | Confianza en certificados del usuario solo en depuración; `base-config` sin texto plano; `release` no depurable; sin certificados versionados | `pruebas/datos/verificar_prebuild_hu04.py` | **VERDE** (27 OK); ver la forma usada abajo |
| 8 | Conexión real del dev build con la CA de Caddy | — | Pendiente de la etapa 2 (guion, pasos 0 y 1) |

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
