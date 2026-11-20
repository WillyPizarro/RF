# Informe DEV — HU-04 (capturar la placa con la cámara), etapa 1

**Documento de trabajo:** `docs/contratos/CONTRATO-HU-04.md` **v4** · **Encargo:** `docs/contratos/ENCARGO-HU-04.md` con M-1 a M-11 · **Rama:** `hu-04` · **Fecha:** 2026-11-19

No leí ni ejecuté las pruebas del TESTER. No instalé nada en la PC: ni `adb` ni drivers ni SDK de Android. Solo agregué dependencias npm al proyecto.

## M-9, M-10 y M-11 (después de la sesión física)

### M-9: safe area (observación 2 del UX, BLOQUEA)

- **`react-native-safe-area-context` ~5.11.1:** la versión de SDK 58, instalada con `expo install`.
- **`App.tsx`:**
  - Un solo `SafeAreaProvider` y un `ZonaSegura` que envuelve todas las pantallas.
  - La zona de la barra de estado (`insets.top`) lleva el fondo oscuro de la franja (`colores.franja`, `#1B1F24`), así que la franja "DATOS SINTÉTICOS · PROTOTIPO" queda **debajo** de la barra.
  - Abajo, `insets.bottom` en blanco.
  - `StatusBar style="light"`: íconos claros.
  - No cambió ningún texto.
- **Jest:** el proveedor recibe `initialMetrics` con márgenes 0 cuando no hay medidas nativas. Con eso, Jest dibuja las pantallas **sin simular** la librería: no hace falta un mock en `__tests__/`.
- **Dev build nuevo:** `react-native-safe-area-context` es un **módulo nativo**, así que el dev build anterior no lo trae. Para la mini sesión hace falta el nuevo, cuyo enlace va abajo.

### M-10: sin caché HTTP (CONTRATO-HU-04 v4)

- **API (`services/api/app/traza.py`):** el middleware que pone `X-Id-Traza` agrega `Cache-Control: no-store` a **toda** respuesta, incluidos los errores y las rutas que no existen.
  - Verificado con la API reconstruida, por la red interna y por el proxy (`https://localhost:8443`).
  - Respuestas probadas: `/v1/salud` 200, `/v1/me` sin token 401, `/v1/no-existe` 404, `PUT /v1/bitacora` 405, login vacío 422 y `/v1/motivos` sin token 401.
  - Todas llevan `Cache-Control: no-store`.
- **App:** `cache: 'no-store'` en el `fetch` de `src/api/cliente.ts` (todas las llamadas a la API) y en `src/api/salud.ts`.

**Verificación:** Jest temporal, ya borrado, con 18 casos en verde. Las llamadas del login, `/v1/me` y `/v1/motivos` llevan `cache: 'no-store'`, y la app monta con el safe area sin mock. `tsc` no da errores.

### M-11: de dónde viene `com.google.android.datatransport`

**Método:** no corrí `./gradlew :app:dependencies`. Esta PC no tiene JDK ni SDK de Android, y no los instalé. Además, el prebuild en una copia se cuelga (ver M-3). Usé la alternativa que permite M-11:

1. Las dependencias que declara cada módulo nativo en `node_modules/*/android/build.gradle`.
2. La cadena de los POM en Google Maven (`dl.google.com/dl/android/maven2`, lectura pública).

**Resultado:**

| Origen | Cadena hasta `datatransport` | En qué build |
|---|---|---|
| `@react-native-ml-kit/text-recognition` (OCR) | `com.google.mlkit:text-recognition:16.0.1` → `com.google.mlkit:common:18.11.0` → `transport-api` 2.2.1, `transport-backend-cct` 2.3.3, `transport-runtime` 2.2.6. También por `text-recognition-bundled-common:17.0.0` → `vision-common:17.3.0`, y por `play-services-mlkit-text-recognition:19.0.1` → `play-services-mlkit-text-recognition-common:19.1.0` | **Todos**: dev build y release |
| `expo-dev-launcher` | `debugOnly` `com.google.mlkit:barcode-scanning:17.3.0` → `common` y `vision-common` → `datatransport` | **Solo el dev build** |
| `expo-camera` | `barcode-scanning` y `play-services-code-scanner` en `compileOnly`, porque `barcodeScannerEnabled` es `false` en `app.json`: no entran al APK | Ninguno |

**Conclusión:**

- `datatransport` llega por **ML Kit**: es su canal de telemetría (`transport-backend-cct`).
- En el APK de release viene solo del reconocimiento de texto. En el dev build hay una segunda vía, el escáner de códigos del menú de desarrollo de `expo-dev-launcher`.
- Quitar el escáner de `expo-camera` no cambia nada, porque ya está fuera. La única forma de quitar `datatransport` sería sacar ML Kit.
- El aviso de la opción A **no está implementado**: espera la v5.

**Observación para la etapa 2:** `com.google.mlkit:text-recognition:16.0.1` depende también de `play-services-mlkit-text-recognition`, el artefacto de Play Services. El modelo está incluido (`text-recognition-bundled-common`), pero la prueba en **modo avión** del §3 es la que confirma que la lectura funciona sin red. No la doy por verificada.

## M-7: proyecto EAS y dev build (etapa 2)

- **`apps/movil/app.json`:**
  - `"owner": "willypizarros-team"`.
  - `npx eas-cli@27.11.0 init` creó el proyecto `@willypizarros-team/movil-buscador` y escribió `extra.eas.projectId` (`bdd4c275-f367-433d-b472-2b127665a1a7`, público).
  - `init` agregó también `android.permissions: ["android.permission.CAMERA"]`, el mismo permiso que ya declara el plugin de `expo-camera`. Los permisos finales no cambian.
  - Commit `977fb18`.
- **Build:** `npx eas-cli@27.11.0 build --profile development --platform android --non-interactive`.
  - **Llave de firma:** EAS la generó **en su servidor**. No hay ningún keystore en la PC ni en el repositorio.
  - **Sesión:** la del humano, en su perfil de Windows (`eas whoami`: `willypizarro`, con acceso Owner a `willypizarros-team`). No se escribió ningún token.
  - **Resultado:** **FINISHED** en unos 7 minutos, sin errores de compilación.
    - Página del build: https://expo.dev/accounts/willypizarros-team/projects/movil-buscador/builds/1d3991b8-e5ed-446d-add7-0c6f30b66d75
    - APK: https://expo.dev/artifacts/eas/Odl1p_ULBybO8tgWRkuzfmxzQgCO5t2aUrLS5szu5Zo.apk
- **ML Kit:** el build pasó con `@react-native-ml-kit/text-recognition`, así que **no** hizo falta la alternativa `expo-text-extractor`. El aviso "not linked" solo aparecería al usar el módulo en el teléfono: queda por verificar en la etapa 2, al tocar "Capturar".
- **Para instalarlo:**
  - Abrir el enlace del APK (o el QR de la página del build) en el S23 Ultra, o
  - `adb install <archivo>.apk` desde la PC.

  Después siguen los pasos C del §7: `adb reverse` de 8443 y 8081, `apps/movil/.env` y `npx expo start --dev-client`.

## Cambios por M-3 y M-4 (HU-04 v3 §8 y revisión del UX)

### M-4: indicador de carga en OCR-01

Mientras `capturarYLeer` está en curso, aparece sobre el marco el `ActivityIndicator` de la app, blanco y con `accessibilityLabel="Cargando"`. No agrega ningún texto visible, y "Capturar" sigue desactivado. Antes de tocar no aparece.

Captura nueva: `OCR-01-leyendo`.

### M-3: conexión del dev build con la API local (§8)

- **Plugin `apps/movil/plugins/redDepuracion.js`**, registrado en `app.json`:
  - Agrega `android:networkSecurityConfig="@xml/network_security_config"` al `<application>` y quita `usesCleartextTraffic`, que con ese atributo no aplica.
  - **`src/main/res/xml/network_security_config.xml`** (lo usa el build de release):
    - el `base-config` lleva `cleartextTrafficPermitted="false"` y solo los certificados `system`;
    - los certificados `user` aparecen **solo** dentro de `<debug-overrides>`.
  - **`src/debug/res/xml/network_security_config.xml`** (solo en debug): lo mismo, más un `domain-config` que permite texto plano **solo hacia `localhost` y `127.0.0.1`**. El dev build carga el JS desde Metro por `http://localhost:8081` con `adb reverse`; sin esa excepción no podría.
  - **Release:** un build de release no incluye el source set `debug` y no es depurable, así que Android ignora `<debug-overrides>`.
- **`.gitignore`** (raíz, solo agregando): `*.crt`, `*.pem`, `*.key` y `*.der`. `git ls-files` no muestra ningún archivo con esas extensiones.
- **`apps/movil/.env.example`:** `EXPO_PUBLIC_API_URL=https://localhost:8443`.

**Verificación:**

- **Mods del plugin:** los corrí con `evalModsAsync` de `expo/config-plugins` sobre una carpeta temporal fuera del repositorio. El manifiesto queda con `networkSecurityConfig`, sin `usesCleartextTraffic`, y los dos XML salen como se describe arriba.
- **Prebuild completo:** `npx expo prebuild --platform android` en una copia de `apps/movil` fuera del repositorio **se colgó en este equipo**, en un paso propio de Expo (`withPackageRefactor`), antes de llegar a los plugins de la app. Lo dejo anotado para la verificación del TESTER.
- **Indicador:** Jest temporal, ya borrado, con 17 casos en verde. El indicador aparece al tocar "Capturar" y no antes.
- `tsc` no da errores.

## Librerías elegidas

| Para qué | Librería | Por qué |
|---|---|---|
| Cámara | `expo-camera` ~58.0.14 | Viene con Expo SDK 58: su versión sigue a la del SDK y trae un config plugin para el permiso. Toma **una foto por llamada** (`takePictureAsync`) y el visor no lee nada por su cuenta. La referencia del ADR-0002 es `react-native-vision-camera`, pero la v5 exige `react-native-nitro-modules` y `react-native-nitro-image`, un riesgo nativo mayor sobre RN 0.88 que esta HU no necesita (no hay procesamiento de cuadros). El contrato deja la elección al DEV dentro del ADR-0002 |
| OCR | `@react-native-ml-kit/text-recognition` 2.0.0 | ML Kit Text Recognition **en el dispositivo**, con el modelo incluido en el APK (`com.google.mlkit:text-recognition:16.0.1`, no la variante de Play Services): funciona **sin red** (ADR-0010). Lee una imagen por URI |
| Borrar la foto | `expo-file-system` ~58.0.14 | `new File(uri).delete()` |
| Abrir los ajustes | `Linking.openSettings()` de React Native | Sin dependencias nuevas |

**Riesgos a verificar en la etapa 2** (con dev build, no se ven en Jest):

- **Interoperabilidad de ML Kit:** el wrapper es un módulo nativo "clásico" (`NativeModules`). Funciona en la nueva arquitectura a través de la capa de interoperabilidad de React Native.
  - Si en el dev build aparece el error de "not linked", la alternativa es `expo-text-extractor` 2.0.0, un módulo Expo que también usa ML Kit en Android.
  - El cambio quedaría dentro de `src/camara/lectorPlaca.ts`, sin tocar nada más.
- **Tamaño del APK:** el wrapper incluye también los modelos chino, devanagari, japonés y coreano, lo que agrega varios MB al APK. Es aceptable en el prototipo.

## Qué construí (`apps/movil/`)

- **`src/camara/lectorPlaca.ts`:** el módulo de borde, con la forma exacta del §1. Es el **único** archivo que importa `expo-camera`, `@react-native-ml-kit/text-recognition` y `expo-file-system`; lo comprobé con `grep` en `src` y `App.tsx`.
  - **`asegurarPermisoCamara()`:** si el permiso ya está dado, `'concedido'`. Si se puede pedir, lo pide. Si el usuario lo negó para siempre, `'denegado'`.
  - **`VisorCamara({activo})`:** un `CameraView` trasero a pantalla completa, sin animación del disparador. No lee nada.
  - **`capturarYLeer()`:** toma una foto con `takePictureAsync`, sin base64 ni EXIF, y la lee con ML Kit.
    - La foto queda en el **cache privado de la app** y se borra en un `finally`, salga bien o mal.
    - Devuelve solo `{texto}`, o `null` si no se reconoció ningún texto.
    - Si la cámara no está lista o falla, rechaza.
    - No devuelve ninguna ruta ni imagen.
  - **`abrirAjustes()`:** llama a `Linking.openSettings()`.
- **`src/camara/placaLeida.ts`:** `proponerPlaca(texto, regex)`, la regla del §4, en un módulo puro sin dependencias nativas.
  - Pasa el texto a mayúsculas y lo separa en líneas.
  - En cada línea prueba primero tal cual (la línea entera y cada palabra) y después con el espacio o el punto entre dos grupos cambiado por un guion.
  - Devuelve el primer candidato que cumpla la regex de `GET /v1/motivos`, o `null`. No adivina caracteres.
- **`src/pantallas/PantallaOcr.tsx`:** OCR-01 a OCR-04, con los textos exactos del contrato.
  - **OCR-01:** "✕" (`accessibilityLabel="Cerrar"`), "Leer placa", el visor con el marco de la placa como guía (no recorta) y "Encuadre la placa y toque Capturar". Abajo, "Capturar", que se desactiva mientras lee, e "Ingresar manualmente".
  - **OCR-02:** "Placa leída" con un campo editable, "Confirme o corrija la placa antes de consultar.", "Usar esta placa" y "Volver a capturar". **No muestra ninguna imagen.**
  - **OCR-03:** ⚠ (oculto para el lector), el mensaje, "Volver a intentar" e "Ingresar manualmente".
  - **OCR-04:** 📷✕ (oculto para el lector), los dos textos, "Abrir ajustes" e "Ingresar manualmente".
- **`src/pantallas/PantallaPlaca.tsx`:**
  - El botón 📷 (`accessibilityLabel="Leer con cámara"`) queda habilitado. Pide el permiso y abre OCR-01 o OCR-04.
  - "Usar esta placa" solo cambia la placa. **El motivo queda como estaba** y **no se envía nada**; la consulta sigue igual que en HU-03 v4.
  - "Ingresar manualmente" vuelve con el foco en "Placa". "✕" y el "atrás" del sistema vuelven sin cambios.
  - Si falla la consulta del permiso, se muestra OCR-03 (nunca una pantalla en blanco). El contrato no define ese caso.
- **`app.json`:**
  - Plugin `expo-camera` con el texto del permiso: "Movil Buscador usa la cámara solo para leer una placa cuando usted toca Capturar. La foto no se guarda.".
  - Sin micrófono ni escáner de códigos.
  - `android.blockedPermissions` bloquea `RECORD_AUDIO`, `READ_EXTERNAL_STORAGE` y `WRITE_EXTERNAL_STORAGE`, que agregaba el prebuild. La app no necesita escribir fuera de su cache privado.
  - Comprobado con `expo config --type prebuild`: los permisos finales son solo `CAMERA` e `INTERNET`.
- **`eas.json`:** el perfil `development`, con `developmentClient`, distribución `internal` y un APK (`assembleDebug`). No tiene secretos ni URL.
- **`package.json` y `package-lock.json`:** las tres dependencias nuevas, instaladas con `expo install`.

## Lo que verifiqué (etapa 1)

Con un Jest temporal mío, ya borrado, que monta `App.tsx` con el módulo de borde simulado (`jest.mock`). Pasaron **18 casos**:

- **§4:** la tabla completa de `proponerPlaca`, con sus 10 filas.
- **§2:**
  - 📷 queda habilitado.
  - `concedido` abre OCR-01; `denegado` abre OCR-04, y `capturarYLeer` nunca se llama.
  - "Abrir ajustes" llama a `abrirAjustes` una vez.
  - Si después se da el permiso, 📷 lleva a OCR-01.
- **§3:**
  - OCR-01 muestra todos sus textos y el visor con `activo=true`, sin ninguna llamada a `capturarYLeer` hasta tocar.
  - **Dos toques seguidos en "Capturar" hacen una sola llamada.**
  - `"PERU\nzzb 201"` lleva a OCR-02 con `ZZB-201`.
  - `"ZZA-1O1"`, `null` y una falla de la cámara llevan a OCR-03. Desde ahí, "Volver a intentar" lleva a OCR-01 e "Ingresar manualmente" vuelve con la placa anterior intacta.
- **§5:**
  - Si se corrige a `zza-101` y se toca "Usar esta placa", PLA-01 queda con `ZZA-101` y el motivo elegido antes.
  - **Ninguna llamada a `fetch` entre 📷 y "Consultar".**
  - La consulta posterior lleva exactamente `{placa, motivo_codigo, motivo_texto}`.
  - Sin motivo, "Usar esta placa" deja el motivo vacío y "Consultar" muestra PLA-02 sin enviar nada.
  - "Volver a capturar" descarta lo leído, y "✕" vuelve sin cambios.
- **§6:** después de leer, SecureStore solo tiene los dos tokens de la sesión.
- **Sin simular `lectorPlaca`:** la app monta y llega a PLA-01. Las pruebas que no usan la cámara no necesitan el mock.

`tsc` no da errores.

**NO VERIFICADO (etapa 2, espera dispositivo y dev build):** todo lo que el contrato marca como "Dispositivo":

- que la foto se borre, comprobado con `adb`;
- 30 s sin tocar "Capturar";
- que la placa impresa se lea de verdad;
- el permiso real del sistema;
- el modo avión.

La precisión va aparte (v2).

## Capturas para el UX

Están en `C:\Willy\Trabajo\MININTER\Movil_Buscador_capturas\HU-04\`, en PNG y HTML a 390 px, con el método de Jest de siempre. En OCR-01 el visor aparece en gris oscuro porque en Jest la cámara está simulada.

| Archivo | Pantalla |
|---|---|
| `PLA-01-camara` | PLA-01 con 📷 habilitado |
| `OCR-01` | Visor con el marco, "Capturar" e "Ingresar manualmente" |
| `OCR-01-leyendo` | Leyendo la foto: indicador sobre el marco y "Capturar" desactivado (M-4) |
| `OCR-02` | Placa leída, editable |
| `OCR-03` | No se pudo leer |
| `OCR-04` | Sin permiso de cámara |

## Instrucciones para esta PC y el S23 Ultra (las ejecuta el humano)

### 1. Android platform-tools (`adb`)

1. Descargar el ZIP de **SDK Platform-Tools for Windows** desde la página oficial de Android Developers (`developer.android.com/tools/releases/platform-tools`).
2. Descomprimirlo en `C:\Android\platform-tools`.
3. Agregar `C:\Android\platform-tools` al `PATH` del usuario: Configuración › Sistema › Información › Configuración avanzada del sistema › Variables de entorno › `Path` (usuario) › Nuevo.
4. Abrir una terminal nueva y comprobar: `adb version`.

### 2. Driver USB de Samsung (solo si Windows no reconoce el teléfono)

1. Conectar el S23 Ultra por USB. Si en el Administrador de dispositivos aparece con un signo de advertencia, o si `adb devices` no lo lista (con la depuración USB ya activada), instalar el **Samsung Android USB Driver for Windows** desde la página oficial de desarrolladores de Samsung (`developer.samsung.com/android-usb-driver`).
2. Desconectar y volver a conectar el teléfono.

### 3. Depuración USB en el S23 Ultra (Android 16, One UI)

1. Ajustes › Acerca del teléfono › Información de software › tocar **Número de compilación** 7 veces y poner el PIN. Se activan las Opciones de desarrollador.
2. Ajustes › **Opciones de desarrollador** › activar **Depuración USB**.
3. Conectar el cable USB. En el teléfono aparece "¿Permitir depuración USB?": marcar "Permitir siempre desde este equipo" y aceptar.
4. Si el modo USB está en "Solo carga", no hace falta cambiarlo para `adb`.

### 4. Comprobación

```
adb devices
```

Tiene que listar el teléfono con el estado `device`. Si dice `unauthorized`, falta aceptar el diálogo del paso 3.3.

### 5. Dev build con EAS (A, aprobado)

Desde `apps/movil/`:

```
! npx eas-cli@27.11.0 login
npx eas-cli@27.11.0 init          # una vez: vincula el proyecto y agrega extra.eas.projectId a app.json
npx eas-cli@27.11.0 build --profile development --platform android
```

- **Login:** `! npx eas-cli@27.11.0 login` lo hace el humano en la terminal. El token queda en su perfil de usuario, **nunca en el repositorio**.
- **`eas init`:** escribe `extra.eas.projectId` en `app.json`. Es un identificador público, no un secreto. Ese cambio lo commitea el DEV cuando el LEAD lo pida.
- **Resultado:** EAS compila en la nube y da un enlace o QR al **APK**. Para instalarlo:
  - abrir el enlace en el teléfono, o
  - descargarlo y correr `adb install <archivo>.apk`.
- **Arranque:** en la PC, `npx expo start --dev-client` (o `npm start`). La app instalada se conecta a Metro por Wi-Fi o por USB con `adb reverse tcp:8081 tcp:8081`.

### 6. Respaldo: build local (B)

Requiere **Android Studio** (SDK y JDK 17) en la PC, que hoy no está instalado. Con eso:

```
npx expo prebuild --platform android
npx expo run:android --device
```

`prebuild` genera `android/`, que no se versiona. Usa la misma configuración de `app.json`.

### 7. Conexión del teléfono a la API local (opción B, §8)

**Qué se logra:**

- **Certificado:** el teléfono confía en el certificado de la PC (la CA local de Caddy), solo en el dev build.
- **Puerto:** el `localhost:8443` del teléfono llega a la PC por el cable USB.

Antes de empezar, la PC tiene la API arrancada con el proxy en el puerto 8443 (`infra/.env`).

**A. Exportar el certificado de la PC (una vez)**

1. Crear una carpeta **fuera del repositorio**, por ejemplo `C:\Willy\Trabajo\MININTER\Movil_Buscador_certificados`.
2. Desde la carpeta del repositorio, en PowerShell, copiar **solo el certificado raíz público**, nunca un archivo `.key`:

   ```
   docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env cp proxy:/data/caddy/pki/authorities/local/root.crt C:\Willy\Trabajo\MININTER\Movil_Buscador_certificados\caddy-local.crt
   ```

3. Este certificado sirve mientras exista el volumen `caddy-datos`. Si alguien borra ese volumen (por ejemplo con `docker compose down -v`), Caddy genera uno nuevo y hay que repetir A y B.

**B. Instalarlo en el S23 Ultra (Android 16)**

1. Con el teléfono conectado y `adb devices` en `device`, pasar el archivo a Descargas:

   ```
   adb push C:\Willy\Trabajo\MININTER\Movil_Buscador_certificados\caddy-local.crt /sdcard/Download/caddy-local.crt
   ```

2. En el teléfono: **Ajustes › Seguridad y privacidad › Más ajustes de seguridad › Instalar desde el almacenamiento del dispositivo › Certificado de CA**.
3. Android avisa que una CA puede ver el tráfico cifrado: tocar **Instalar de todas formas**, desbloquear con el PIN y elegir `caddy-local.crt` en Descargas.
4. Comprobarlo: **Ajustes › Seguridad y privacidad › Más ajustes de seguridad › Ver certificados de seguridad › pestaña Usuario**. Tiene que aparecer "Caddy Local Authority".
5. Borrar la copia de Descargas, que ya no hace falta:

   ```
   adb shell rm /sdcard/Download/caddy-local.crt
   ```

**C. Cada vez que se conecta el teléfono**

1. Conectar el cable y comprobar con `adb devices`.
2. Redirigir los puertos:

   ```
   adb reverse tcp:8443 tcp:8443
   adb reverse tcp:8081 tcp:8081
   ```

   El 8443 es la API y el 8081 es Metro, de donde el dev build carga el JS. `adb reverse --list` muestra los dos.
3. En `apps/movil/`, copiar `.env.example` a `.env`, que no se versiona. Debe quedar `EXPO_PUBLIC_API_URL=https://localhost:8443`.
4. Arrancar Metro: `npx expo start --dev-client`. En el teléfono, abrir la app y elegir el servidor `http://localhost:8081`.
5. Iniciar sesión con un usuario de prueba. Si aparece la lista de motivos al tocar "Consultar placa", la conexión funciona.

**D. Generar el dev build con la configuración del §8**

- Se genera con el paso 5 (EAS) o el 6 (local), **después de este cambio**. El plugin solo entra al compilar, así que un dev build anterior no tiene la configuración de red.
- La URL de la API **no** va en el build: la pone Metro desde `apps/movil/.env` (paso C.3). Por eso no hay que regenerar el build para cambiarla.

**E. Borrar el certificado al cierre del proyecto** (va al acta de eliminación de `PENDIENTES.md`)

1. En el teléfono: **Ajustes › Seguridad y privacidad › Más ajustes de seguridad › Ver certificados de seguridad › Usuario › Caddy Local Authority › Quitar**.
2. Si hubiera otros certificados de usuario que tampoco sirven, **Borrar credenciales**, en la misma pantalla, los elimina todos.
3. Quitar las redirecciones: `adb reverse --remove-all`.
4. Desinstalar el dev build: `adb uninstall pe.prototipo.movilbuscador`.
5. En la PC, borrar la carpeta `C:\Willy\Trabajo\MININTER\Movil_Buscador_certificados`.
6. Para invalidar la CA en la PC, borrar el volumen de Caddy: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env down` y después `docker volume rm movil-buscador_caddy-datos`.
