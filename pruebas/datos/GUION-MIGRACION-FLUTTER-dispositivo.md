# Guion de la mini sesión física — app Flutter en el Samsung Galaxy S23 Ultra (Android 16)

**Contratos:** `docs/contratos/CONTRATO-MIGRACION-FLUTTER.md` **v1.3** (§4 safe area, §6 build) y `docs/contratos/CONTRATO-HU-04.md` **v6** (§3 sin red, §6 dispositivo, §8 conexión). **Encargo:** `docs/contratos/ENCARGO-MIGRACION-FLUTTER.md`, punto 7 del TESTER.
**Cuándo:** el **miércoles 25-nov** (M-6 del encargo; antes era el jueves 4-dic), con el PM y el humano. **El TESTER no corre `adb` contra el teléfono**: el PM corre los comandos y el humano opera el teléfono. El TESTER escribe este guion y después pasa los resultados a `informes/TESTER-MIGRACION-FLUTTER.md`.
**Reemplaza** a `GUION-HU-04-dispositivo.md` de la referencia `hu-04-expo-referencia` (Expo, dev build con Metro). Los pasos son los mismos, adaptados al APK de Flutter: sin Metro, sin EAS y sin `http-cache` de OkHttp.

**Qué cubre:**

| Parte | Origen | Paso |
|---|---|---|
| Desinstalar la app de Expo e instalar el APK de depuración | CONTRATO-MIGRACION-FLUTTER, avisos de contexto | 0 |
| Conexión con la API local (CA de Caddy, `adb reverse`) | HU-04 v6 §8 | 1 |
| Recorrido de login, placa y bitácora, una vez | CONTRATO-MIGRACION-FLUTTER §8 | 2 |
| Capturas S1 a S15 del UX: S1 a S5 aprueban la safe area; S6 a S15 cierran la etapa 2 de HU-04 y los símbolos | CONTRATO-MIGRACION-FLUTTER §4, revisión del UX (M-7) | 3 |
| Permiso real del sistema | HU-04 v6 §6 | 4 |
| Sin lectura continua (30 s) | HU-04 v6 §6, regla 6 | 5 |
| La placa impresa se lee y el paso a paso del §5, una vez | HU-04 v6 §5 y §6 | 6 |
| Aviso de telemetría en OCR-01, una vez | HU-04 v6 §3 ("Qué se prueba dónde") | 6 |
| La foto se borra (10 capturas) | HU-04 v6 §6 | 7 |
| Sin caché HTTP en disco (`cache/` y `files/`) | HU-04 v6 §6 | 8 |
| Cola de telemetría de ML Kit | HU-04 v6 §6 | 9 |
| Sin red (modo avión) | HU-04 v6 §3 | 10 |
| APK de release no depurable | CONTRATO-MIGRACION-FLUTTER §6, HU-04 v6 §8 | 11 |

La **precisión del OCR (HU-04 §7) no entra**: va en la fase de pruebas del 16 al 26-dic, con `pruebas/datos/ocr-precision.csv`.

## Reglas durante la prueba

- **Placas:** solo las de `pruebas/datos/hoja-placas-prueba.html`, impresas, con prefijo `ZZ` y la leyenda "PRUEBA — NO VÁLIDA". **Nunca** se apunta la cámara a un vehículo real.
- **Capturas de pantalla para el UX:** pantalla completa del teléfono (con la barra de estado y la de navegación), **fuera del repositorio**, en `C:\Willy\Trabajo\MININTER\Movil_Buscador_capturas\MIGRACION-FLUTTER\s23\` (revisión del UX, `docs/ux/revisiones/MIGRACION-FLUTTER.md`). **Copias del teléfono** (caché, cola de telemetría): en `C:\Willy\Trabajo\MININTER\flutter-capturas\`, y se borran al terminar. Nunca se hace commit de imágenes, fotos, bases ni copias.
- **Cómo se saca una captura:** `cmd /c "adb exec-out screencap -p > C:\Willy\Trabajo\MININTER\Movil_Buscador_capturas\MIGRACION-FLUTTER\s23\<archivo>.png"` (en PowerShell 5.1 el `>` directo corrompe el PNG).
- **Certificados y llaves:** la CA de Caddy y la llave de firma del APK no se copian nunca dentro del repositorio.
- **Clave de los usuarios de prueba:** la dicta el humano (`CLAVE_USUARIOS_PRUEBA` de `infra/.env`); no se escribe en ningún archivo.
- **Comandos:** PowerShell 5.1, desde la raíz del worktree `C:\Willy\Trabajo\MININTER\Movil_Buscador-flutter`, con `adb` en `C:\Android\platform-tools` (en el `PATH`). En PowerShell 5.1 el `>` corrompe la salida binaria: las copias binarias van con `cmd /c "… > archivo"`.
- **Paquete de la app:** `pe.prototipo.movilbuscador` (CONTRATO-MIGRACION-FLUTTER §6).
- **APK de la sesión:** los de la `ENTREGA DEV` (`1382d13`, código `0a1d93e`), **fuera del repositorio**, en `C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\`: `movil-buscador-debug.apk`, `movil-buscador-release.apk` y `SHA256SUMS.txt` (M-6). En la sesión **no se compila nada**.
- **CA de Caddy:** los pasos son los de la §9 del informe del DEV (`informes/DEV-MIGRACION-FLUTTER.md`). La copia de la CA va en `C:\Willy\Trabajo\MININTER\ca-local\`, fuera del repositorio.
- **Flutter:** `C:\Programas_Portables\flutter_3.50.1\flutter\bin\flutter.bat` (M-2). Si `flutter` no está en el `PATH`, usar esa ruta completa.

## 0. Preparación (una vez)

| Paso | Comando o acción | Esperado | Resultado |
|---|---|---|---|
| 0.1 | Imprimir `pruebas/datos/hoja-placas-prueba.html` en A4 horizontal al 100 % | 8 hojas, una placa por hoja | |
| 0.2 | `New-Item -ItemType Directory -Force C:\Willy\Trabajo\MININTER\flutter-capturas, C:\Willy\Trabajo\MININTER\Movil_Buscador_capturas\MIGRACION-FLUTTER\s23 \| Out-Null` | Carpetas fuera del repositorio | |
| 0.2b | **Anotar el modo de navegación del teléfono** (Ajustes › Pantalla › Barra de navegación): "Gestos de deslizar" o "Botones" (lo pide el UX antes de empezar; S5 se hace en el otro) | Modo anotado: ________ | |
| 0.3 | `adb devices` | El S23 Ultra aparece como `device` (no `unauthorized`) | |
| 0.4 | `adb shell getprop ro.build.version.release` | `16` | |
| 0.5 | Sistema arrancado **solo desde esta carpeta** (`Movil_Buscador-flutter`; nunca dos carpetas a la vez), con `infra/.env` copiado de la carpeta principal (nunca versionado) y `PROXY_PUERTO_HTTPS=8443`: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env up -d --build` | Contenedores arriba | |
| 0.5b | `curl.exe -k -s -o NUL -w "%{http_code}" https://localhost:8443/v1/salud` | `200` | |
| 0.6 | Sacar la CA de Caddy (§9 paso 2 del DEV): `New-Item -ItemType Directory -Force C:\Willy\Trabajo\MININTER\ca-local \| Out-Null` y `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env cp proxy:/data/caddy/pki/authorities/local/root.crt C:\Willy\Trabajo\MININTER\ca-local\caddy-root.crt` | El archivo existe, fuera del repositorio | |
| 0.6b | Instalarla como certificado del usuario (§9 paso 3): `adb push C:\Willy\Trabajo\MININTER\ca-local\caddy-root.crt /sdcard/Download/`; en el teléfono: Ajustes › Seguridad y privacidad › Más ajustes de seguridad › Instalar desde el almacenamiento › Certificado de CA; después `adb shell rm /sdcard/Download/caddy-root.crt` | La CA aparece en Ver certificados de seguridad › Usuario; `Download/` sin el archivo | |
| 0.7 | `adb reverse tcp:8443 tcp:8443` y `adb reverse --list` | `tcp:8443 tcp:8443` | |
| 0.8 | **Desinstalar la app de Expo** (otra firma; §9 paso 1): `adb uninstall pe.prototipo.movilbuscador` | `Success` (o `Unknown package` si ya no estaba) | |
| 0.9 | Comprobar los APK contra `SHA256SUMS.txt` (M-6): `Get-FileHash -Algorithm SHA256 C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\movil-buscador-*.apk \| ForEach-Object { $h = $_.Hash.ToLower(); Select-String -Path C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\SHA256SUMS.txt -SimpleMatch $h }` | Dos líneas, una por APK (`… movil-buscador-debug.apk` y `… movil-buscador-release.apk`). Si falta alguna, **no se instala** y se avisa al LEAD. Los valores salen del `SHA256SUMS.txt` de la entrega de la M-7 (los APK se recompilan después de las observaciones del UX) | |
| 0.10 | Instalar el APK de depuración (§9 paso 5): `adb install C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\movil-buscador-debug.apk` | `Success` | |
| 0.11 | `adb shell pm list packages pe.prototipo.movilbuscador` | `package:pe.prototipo.movilbuscador` | |
| 0.12 | `adb shell dumpsys package pe.prototipo.movilbuscador \| Select-String "versionName\|flags="` | Anotar la versión. En `flags=` aparece `DEBUGGABLE` (es el de depuración) y **no** `ALLOW_BACKUP` | |
| 0.13 | Contar las fotos de la galería: `adb shell "ls /sdcard/DCIM/Camera 2>/dev/null \| wc -l"` y `adb shell "ls /sdcard/Pictures 2>/dev/null \| wc -l"` | Anotar G0 y P0 | |

## 1. Conexión con la API local (HU-04 v6 §8)

| Paso | Acción | Esperado | Resultado |
|---|---|---|---|
| 1.1 | Abrir "Movil Buscador" (el nombre visible) | AUTH-01 con "Usuario", "Clave", "Ingresar" y la franja "DATOS SINTÉTICOS · PROTOTIPO" | |
| 1.2 | Iniciar sesión con `agente1` | HOME-01: "Hola, …", "Rol: Agente", "Salir"; "Consultar placa" habilitada, "Verificar rostro" y "Mis verificaciones" deshabilitadas | |
| 1.3 | Tocar "Consultar placa" | PLA-01 con el catálogo de motivos (llegó `GET /v1/motivos`) y el botón 📷 habilitado | |

## 2. Recorrido de login, placa y bitácora (CONTRATO-MIGRACION-FLUTTER §8), una vez

| Paso | Acción | Esperado | Resultado |
|---|---|---|---|
| 2.1 | En PLA-01 escribir `zza-101` | El campo muestra `ZZA-101`, en letra monoespaciada | |
| 2.2 | Elegir "Control vehicular" y tocar "Consultar" | "Consultando…" y después PLA-05 "TIENE REQUISITORIA", con "Motivo:", "Consultado: dd/mm/aaaa hh:mm" (hora local) y "Nueva consulta" | |
| 2.3 | "Nueva consulta", `ZZB-201`, un motivo, "Consultar" | PLA-06 "Sin requisitoria registrada en la fuente consultada", gris y sin ✓ | |
| 2.4 | "Atrás" del sistema hasta HOME-01 y "Salir" | AUTH-01 sin mensaje | |
| 2.5 | Iniciar sesión con `supervisor1` y tocar "Bitácora" | BIT-01 con las consultas recién hechas (fecha `dd/mm hh:mm`, usuario, etiqueta, resultado, "SINTÉTICO") y los filtros con "PA 24" | |
| 2.6 | Tocar un registro | BIT-02 "Registro #…" y "Registro de solo lectura" | |
| 2.7 | "Salir". Cerrar la app desde recientes y volver a abrirla | AUTH-01 (sin sesión guardada, no retoma nada) | |
| 2.8 | Iniciar sesión con `agente1`, cerrar la app desde recientes **sin** "Salir" y volver a abrirla | Va directo a HOME-01 del agente, sin pasar por AUTH-01 (retomar, §1.2) | |

## 3. Capturas del S23 Ultra para el UX (S1 a S15; M-7)

Lista y condiciones de `docs/ux/revisiones/MIGRACION-FLUTTER.md`. Todas con el APK de depuración contra la API local, datos sintéticos y placas `ZZ…`, **pantalla completa** (barra de estado y barra de navegación incluidas), en `C:\Willy\Trabajo\MININTER\Movil_Buscador_capturas\MIGRACION-FLUTTER\s23\`. Una captura de `flutter_test` no sirve para la §4 (no hay barra de estado).

### 3.A Para aprobar la §4 (safe area) — obligatorias

Si alguna falla, la §4 queda **BLOQUEA** (misma observación 2 de `docs/ux/revisiones/HU-04.md`). Se hacen en el modo de navegación anotado en 0.2b, salvo S5.

| # | Cómo llegar | Archivo | Qué tiene que verse | Resultado |
|---|---|---|---|---|
| S1 | Sesión de `agente1`, HOME-01 | `S01-home-01.png` | La hora, la señal y la batería completas y legibles en claro sobre el fondo oscuro; la franja "DATOS SINTÉTICOS · PROTOTIPO" entera, justo debajo, sin superponerse | |
| S2 | "Consultar placa" → PLA-01, **sin** teclado | `S02-pla-01.png` | Lo mismo arriba; "Consultar" lejos de la barra de abajo | |
| S3 | 📷 → aviso → "Entendido" → OCR-01 con el visor de la cámara | `S03-ocr-01.png` | Lo mismo arriba; "Capturar" e "Ingresar manualmente" enteros y por encima de la línea de gestos o de los botones de navegación | |
| S4 | "Capturar" sobre una placa impresa → OCR-02 | `S04-ocr-02.png` | Lo mismo arriba; "Usar esta placa" y "Volver a capturar" visibles | |
| S5 | Cambiar al **otro** modo de navegación (Ajustes › Pantalla › Barra de navegación), volver a la app y abrir OCR-01 | `S05-ocr-01-otro-modo.png` | Los botones de abajo no quedan bajo la barra de navegación (en modo botones es más alta). **Después, volver al modo anotado en 0.2b** | |

### 3.B Otras pantallas — no bloquean la §4; cierran la etapa 2 de HU-04 y los símbolos

| # | Cómo llegar | Archivo | Qué se mira | Resultado |
|---|---|---|---|---|
| S6 | "Salir", volver a entrar con `agente1` (sesión nueva) → PLA-01 → 📷 | `S06-ocr-01-aviso.png` | La tarjeta del aviso de ML Kit sobre el visor atenuado; el cuerpo completo. **No tocar "Entendido" todavía** | |
| S7 | Con el aviso a la vista: Ajustes › Pantalla › Tamaño y estilo de fuente › **letra al máximo**; volver a la app | `S07-ocr-01-aviso-letra-maxima.png` | El cuerpo del aviso se lee completo, sin cortes; "Entendido" a la vista o alcanzable desplazando. **Después, volver la letra a su tamaño anterior** | |
| S8 | "Entendido"; apuntar a una placa impresa, de día, y tocar "Capturar"; sacar la captura **mientras lee** (si no se llega a tiempo, repetir) | `S08-ocr-01-leyendo.png` | El indicador de carga sobre la imagen real; con la obs. 1 del UX resuelta, **chico y centrado en el marco** | |
| S9 | OCR-01 con el visor sobre una placa impresa a 1 o 2 m | `S09-ocr-01-placa-1-2m.png` | El contraste del marco blanco sobre la imagen real y que la placa entre en el marco | |
| S10 | Pasos 4.1 a 4.3 (permiso denegado) → OCR-04; después "Abrir ajustes" | `S10a-ocr-04.png` y `S10b-ajustes.png` | El 📷✕ se dibuja; "Abrir ajustes" abre la información de la app, con "Permisos" a mano | |
| S11 | Con el permiso concedido otra vez (paso 4.5): PLA-01, elegir un motivo y tocar "Placa" (teclado abierto) | `S11-pla-01-teclado.png` | Se dibujan ←, 📷 y ○/◉; el teclado sale en mayúsculas; "Consultar" se alcanza desplazando | |
| S12 | PLA-01: escribir `HOLA`, **sin** motivo, "Consultar" | `S12-pla-02-pla-03.png` | Se dibuja el ⚠ en los dos mensajes | |
| S13 | "Salir"; en AUTH-01, `agente1` con una clave errada | `S13-auth-02.png` | Se dibuja el ⚠ | |
| S14 | Sesión de `supervisor1` → "Bitácora" → abrir "Filtros" → tocar "Desde" | `S14-bit-01-filtros-teclado.png` | El teclado es numérico con "/" (obs. 4 de `HU-03-07.md`); con la obs. 2 resuelta, las opciones de "Tipo" **agrupadas** varias por fila | |
| S15 | Tocar un registro → BIT-02 | `S15-bit-02.png` | Se dibuja el 🔒 | |

Si en S10 a S15 algún símbolo sale como un cuadrado, se avisa al LEAD: entonces el UX revisa también AUTH-03, AUTH-04, ERR-01 y PLA-05 a PLA-08 en el teléfono.

**No hace falta en el teléfono:** AUTH-03, AUTH-04, ERR-01 ni PLA-05 a PLA-08 (aprobadas con `flutter_test`).

## 4. Permiso real del sistema (HU-04 v6 §6)

| Paso | Acción o comando | Esperado | Resultado |
|---|---|---|---|
| 4.1 | Dejar el permiso sin decidir: `adb shell pm revoke pe.prototipo.movilbuscador android.permission.CAMERA` y `adb shell pm clear-permission-flags pe.prototipo.movilbuscador android.permission.CAMERA user-set user-fixed` | Sin error | |
| 4.2 | En PLA-01, tocar 📷 | El diálogo del sistema pide el permiso de cámara | |
| 4.3 | Elegir "No permitir" | OCR-04: "La app no tiene permiso para usar la cámara.", "Para darlo: Ajustes › Aplicaciones › Movil Buscador › Permisos › Cámara.", "Abrir ajustes" e "Ingresar manualmente". Sin el aviso de telemetría | |
| 4.4 | "Abrir ajustes" y `adb shell "dumpsys activity activities \| grep -E 'topResumedActivity\|mResumedActivity'"` | La ficha de la app en Ajustes (`com.android.settings`) **o** su pantalla de permisos (`com.google.android.permissioncontroller`) | |
| 4.5 | Dar "Permitir solo mientras se usa la app", volver y tocar 📷 | OCR-01 con el visor en vivo | |

## 5. Sin lectura continua (HU-04 v6 §6, regla 6)

| Paso | Acción | Esperado | Resultado |
|---|---|---|---|
| 5.1 | En OCR-01 (con el aviso ya cerrado), apuntar a `ZZA-101` durante **30 s** (cronómetro) **sin tocar "Capturar"** | No aparece OCR-02; el visor sigue en vivo | |

## 6. La placa se lee, el paso a paso y el aviso de telemetría (HU-04 v6 §3, §5 y §6)

Empezar con una sesión nueva (después de "Salir" y volver a entrar), para ver el aviso.

| Paso | Acción | Esperado | Resultado |
|---|---|---|---|
| 6.1 | En PLA-01, **sin** elegir motivo, tocar 📷 | OCR-01 con la tarjeta "Antes de leer la placa", su texto y "Entendido"; "Capturar" desactivado; "Ingresar manualmente" activo. La captura del aviso ya es S6 (paso 3.B); aquí no se repite | |
| 6.2 | Tocar el visor fuera de la tarjeta | No pasa nada | |
| 6.3 | "Entendido" | La tarjeta desaparece y "Capturar" se activa | |
| 6.4 | Apuntar a `ZZA-101` de frente, con buena luz, y "Capturar" | Mientras lee, "Capturar" desactivado; después OCR-02 "Placa leída" con `ZZA-101`. **Ninguna imagen** | |
| 6.5 | Corregir a `ZZB-201` y "Usar esta placa" | PLA-01 con `ZZB-201`; el motivo sigue vacío; **no se consultó nada** | |
| 6.6 | "Consultar" | "Indique el motivo de la consulta." (no se envía) | |
| 6.7 | Elegir "Control vehicular" y "Consultar" | PLA-06 (`ZZB-201`) | |
| 6.8 | Volver a PLA-01 y tocar 📷 | OCR-01 **sin** la tarjeta (en esta sesión ya se vio) | |
| 6.9 | Leer `ZZZ-999` y consultar con un motivo | OCR-02 con `ZZZ-999`; después PLA-08 "Placa no registrada en la fuente consultada. Verifique la placa." | |
| 6.10 | En OCR-01, tapar la cámara con la mano y "Capturar" | OCR-03: "No se pudo leer la placa. Pruebe de frente y con más luz." | |

## 7. La foto se borra (HU-04 v6 §6)

| Paso | Acción o comando | Esperado | Resultado |
|---|---|---|---|
| 7.1 | **10 capturas seguidas** (OCR-01 → "Capturar" → "Volver a capturar"), alternando las placas impresas | Cada una termina en OCR-02 u OCR-03 | |
| 7.2 | `adb shell run-as pe.prototipo.movilbuscador find . -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png"` | **Ningún archivo de captura** (ni en `files/`, ni en `cache/`, ni en `app_flutter/`). Si aparece algo, anotar la ruta | |
| 7.3 | `adb shell "ls /sdcard/DCIM/Camera 2>/dev/null \| wc -l"` y `adb shell "ls /sdcard/Pictures 2>/dev/null \| wc -l"` | Los mismos G0 y P0 del paso 0.13 | |

## 8. Sin caché HTTP en disco (HU-04 v6 §6)

| Paso | Acción o comando | Esperado | Resultado |
|---|---|---|---|
| 8.1 | `adb shell pm clear pe.prototipo.movilbuscador` (borra también la sesión y el permiso) | `Success` | |
| 8.2 | Abrir la app, iniciar sesión con `agente1`, "Consultar placa" (carga los motivos) y consultar `ZZA-101` con un motivo | PLA-05 "TIENE REQUISITORIA" | |
| 8.3 | `adb shell run-as pe.prototipo.movilbuscador ls -laR cache files app_flutter` | Anotar qué hay (sin abrir el contenido) | |
| 8.4 | Copia fuera del repositorio: `cmd /c "adb exec-out run-as pe.prototipo.movilbuscador tar -cf - cache files app_flutter > C:\Willy\Trabajo\MININTER\flutter-capturas\cache-app.tar"` (si una carpeta no existe, `tar` lo avisa y sigue) | Archivo `.tar` con tamaño mayor que 0 | |
| 8.5 | `python -I pruebas\datos\revisar_cache_app.py C:\Willy\Trabajo\MININTER\flutter-capturas\cache-app.tar` | Termina con "Ningún archivo con /v1/, respuestas de la API ni imágenes …" (código 0). Si encuentra algo, imprime solo la ruta y la marca | |
| 8.6 | `Remove-Item -Force C:\Willy\Trabajo\MININTER\flutter-capturas\cache-app.tar` | La copia borrada | |

## 9. Cola de telemetría de ML Kit (HU-04 v6 §6)

Después de leer al menos una placa (pasos 6 o 7). La copia va fuera del repositorio y se borra al terminar.

| Paso | Comando | Esperado | Resultado |
|---|---|---|---|
| 9.1 | Leer una placa impresa con 📷 → "Capturar" → OCR-02 | OCR-02 con la placa | |
| 9.2 | `adb shell run-as pe.prototipo.movilbuscador ls -la databases` | Se ve `com.google.android.datatransport.events` (y quizá `-wal` y `-shm`). Anotar los nombres. Si no existe, anotarlo: la cola puede no haberse creado todavía | |
| 9.3 | `$d = "C:\Willy\Trabajo\MININTER\flutter-capturas\datatransport"; New-Item -ItemType Directory -Force $d \| Out-Null` | Carpeta fuera del repositorio | |
| 9.4 | `cmd /c "adb exec-out run-as pe.prototipo.movilbuscador cat databases/com.google.android.datatransport.events > C:\Willy\Trabajo\MININTER\flutter-capturas\datatransport\com.google.android.datatransport.events"`. Repetir con `-wal` y `-shm` si aparecieron en 9.2 | Archivos con tamaño mayor que 0 | |
| 9.5 | `python -I pruebas\datos\revisar_datatransport.py C:\Willy\Trabajo\MININTER\flutter-capturas\datatransport` | Termina con "Ninguna imagen … y ningún texto de placa ZZ en la cola" (código 0). Lista tablas, eventos y datos legibles para compararlos con la divulgación de Google. **Si aparece una imagen o un texto `ZZ…`, la decisión se reabre** | |
| 9.6 | `Remove-Item -Recurse -Force C:\Willy\Trabajo\MININTER\flutter-capturas\datatransport` | La copia borrada | |

## 10. Sin red (HU-04 v6 §3)

| Paso | Acción o comando | Esperado | Resultado |
|---|---|---|---|
| 10.1 | `adb reverse --remove tcp:8443` y modo avión: `adb shell cmd connectivity airplane-mode enable` (el Wi-Fi también apagado) | Ícono de avión | |
| 10.2 | En PLA-01, 📷 y capturar `ZZA-101` | OCR-01, OCR-02 y OCR-03 funcionan igual: la lectura es local | |
| 10.3 | "Usar esta placa", elegir motivo y "Consultar" | PLA-07 "No se pudo completar la consulta; intente nuevamente", con "Reintentar" y "Volver". **Nunca** "sin requisitoria" | |
| 10.4 | `adb shell cmd connectivity airplane-mode disable` y `adb reverse tcp:8443 tcp:8443` | Vuelve la red | |

> `adb reverse` va por USB y sigue funcionando en modo avión; por eso se quita en 10.1.

## 11. APK de release no depurable (CONTRATO-MIGRACION-FLUTTER §6, HU-04 v6 §8)

No necesita el teléfono. El TESTER ya lo corrió sobre la entrega (informe, corrida M-5): en la sesión se repite solo si el PM quiere confirmarlo.

| Paso | Comando | Esperado | Resultado |
|---|---|---|---|
| 11.1 | El APK de release de la entrega: `C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\movil-buscador-release.apk`, ya comprobado en 0.9 | El archivo existe y su SHA-256 coincide | |
| 11.2 | `& (Get-ChildItem C:\Android\build-tools\*\aapt.exe \| Sort-Object FullName \| Select-Object -Last 1).FullName dump badging C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\movil-buscador-release.apk \| Select-String "package:\|application-label:\|debuggable"` | `package: name='pe.prototipo.movilbuscador'`, `application-label:'Movil Buscador'` y **ninguna** línea `application-debuggable` | |
| 11.3 | `& (Get-ChildItem C:\Android\build-tools\*\aapt.exe \| Sort-Object FullName \| Select-Object -Last 1).FullName dump xmltree C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\movil-buscador-release.apk AndroidManifest.xml \| Select-String "allowBackup\|usesCleartextTraffic\|networkSecurityConfig"` | `android:allowBackup` y `android:usesCleartextTraffic` en `0x0` (false) y `android:networkSecurityConfig` presente | |
| 11.4 | El mismo `dump badging` sobre `C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\movil-buscador-debug.apk` | Aparece `application-debuggable` (control: el de depuración sí lo es) | |
| 11.5 | Modelo de ML Kit dentro del APK (contrato v1.2 §7, M-3): `python -I pruebas\datos\revisar_modelo_apk.py C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\movil-buscador-release.apk` (equivale a `unzip -l`) | Archivos en `assets/mlkit-google-ocr-models/` y `lib/*/libmlkit_google_ocr_pipeline.so`; termina con "El modelo de ML Kit está dentro del APK." (código 0). Si aparecen `play-services-mlkit-*.properties`, **no** es un rojo (v1.2: dependencia transitiva; lo que hace en la red queda NO VERIFICADO) | |
| 11.6 | Firma: `C:\Android\build-tools\36.0.0\apksigner.bat verify --print-certs C:\Willy\Trabajo\MININTER\Movil_Buscador_apk\MIGRACION-FLUTTER\movil-buscador-release.apk \| Select-String "certificate DN"` | `CN=Movil Buscador (prototipo con datos sinteticos), O=Prototipo, C=PE` (la llave del proyecto, fuera del repositorio; **no** `CN=Android Debug`, que es la del APK de depuración) | |

> El APK de release **no** confía en la CA del usuario: contra la API local con Caddy no conecta, y es lo esperado (informe del DEV, §9). No se instala en esta sesión.

## 12. Al terminar

| Paso | Comando | Esperado |
|---|---|---|
| 12.1 | `adb reverse --remove-all` | Sin error |
| 12.2 | Pasar los resultados (sin imágenes) al TESTER para `informes/TESTER-MIGRACION-FLUTTER.md` y las capturas al LEAD para el UX | — |
| 12.3 | La CA de Caddy queda instalada hasta el cierre del proyecto. **Al cierre** (§9 paso 6 del DEV): en el teléfono, Ajustes › Seguridad y privacidad › Más ajustes de seguridad › Ver certificados de seguridad › Usuario › quitar la CA de Caddy; y en la PC `Remove-Item -Recurse -Force C:\Willy\Trabajo\MININTER\ca-local`. La llave de firma se borra según el informe del DEV (§4, "La llave de firma"). Las dos van en el acta de eliminación (`docs/contratos/PENDIENTES.md`) | — |
| 12.4 | Bajar el compose: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env down` | Docker libre para las otras carpetas |
