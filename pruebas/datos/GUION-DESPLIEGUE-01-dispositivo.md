# Guion de la sesión del teléfono — DESPLIEGUE-01 (NGINX local, red de ML Kit y descarga)

**Contrato:** `docs/contratos/CONTRATO-DESPLIEGUE-01.md` **v2.1** (con la anotación `1cb361a`): §2 "Local", §5 "Funciona sin cable", "Qué prueba quién" (fila del teléfono de pruebas) y §8. **Encargo:** `docs/contratos/ENCARGO-DESPLIEGUE-01.md`, **M-3**, punto 3 del TESTER. **Verificación de red:** `docs/arch/evaluaciones/HU-04-telemetria-mlkit.md`, "Propuesta 2026-11-25", **niveles 1 y 2** (el 3 no entra). Contratos de la app: CONTRATO-MIGRACION-FLUTTER v1.5 y CONTRATO-HU-04 v7.
**Quién:** los `adb` y los programas de la PC los corre el **DEV** (como en la M-14 de la migración); el **PM** coordina; el **humano** opera el teléfono (instalar y quitar certificados y PCAPdroid, aceptar los diálogos, leer la placa). El **TESTER no usa `adb`**: escribe este guion y después pasa los resultados a `informes/TESTER-DESPLIEGUE-01.md`.
**Cuándo:** **dos sesiones** (dato del LEAD, M-3). **Sesión 1, local**, cuando lleguen las dos entregas de B1: (a) la CA de NGINX con el login de `agente1`, (b) el nivel 1, (c) el nivel 2 y, al final, la limpieza (e). **Sesión 2**, cuando exista el VPS (fase B2): la descarga del release (d).

## Reglas durante la sesión

- **Registro:** copia de este guion **fuera del repositorio**, en `C:\Willy\Trabajo\MININTER\Movil_Buscador_capturas\DESPLIEGUE-01\resultados-sesion.md`. En la columna "Resultado": `OK`, `ROJO: <qué se vio>` o `NO HECHO: <por qué>`. Un `ROJO` se avisa al LEAD en el momento y no se arregla en la sesión.
- **Capturas de red:** solo en `C:\Willy\Trabajo\MININTER\flutter-capturas\red\`, y se borran en (e). Tienen el identificador de instalación y datos del equipo: **al registro y al informe van solo dominios, categorías y conteos, nunca valores** (ni el identificador, ni la huella del build, ni tokens).
- **mitmproxy:** **no** se guardan los flujos completos (`-w`): pasan el login con la clave. Solo se guardan los cuerpos de las subidas a Google con `pruebas/datos/mitm_guardar_subidas.py`, que no toca `localhost`.
- **Placas:** solo las impresas de `pruebas/datos/hoja-placas-prueba.html` (`ZZ…`, "PRUEBA — NO VÁLIDA"). Nunca un vehículo real.
- **Claves:** la de los usuarios (`CLAVE_USUARIOS_PRUEBA`) y la de la descarga (`DESCARGA_APK_CLAVE`) las dicta el humano; no se escriben en ningún archivo.
- **Certificados:** la CA local de NGINX, la CA de mitmproxy y la llave de firma **nunca** entran al repositorio.
- **Comandos:** PowerShell 5.1 desde la raíz del worktree `C:\Willy\Trabajo\MININTER\Movil_Buscador-despliegue`; `adb` en `C:\Android\platform-tools`. Las copias binarias van con `cmd /c "… > archivo"`.
- **Compose:** uno solo arriba, desde `-despliegue` (con NGINX). Nunca dos carpetas a la vez.
- **APK:** el de **depuración de `main`** (`pe.prototipo.movilbuscador`, contrato de la migración v1.5) para (a) a (c), fuera del repositorio. Su SHA-256 lo anota el DEV en 0.2. El de **release** solo en (d).
- **Lo que depende de la ENTREGA DEV B1** (ruta de la CA local de NGINX, versiones de mitmproxy, `protoc` y PCAPdroid, cómo pasa el tráfico por mitmproxy y cómo se deshace) está marcado **`[DEV B1]`**: se completa con el informe `informes/DEV-DESPLIEGUE-01.md` (sección v2.1) antes de la sesión.

# Sesión 1 — local, con el cable (partes (a), (b), (c) y la limpieza (e))

## 0. Preparación (PC)

| Paso | Comando o acción | Esperado | Resultado |
|---|---|---|---|
| 0.1 | `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env ps` | `proxy` (NGINX), `api`, `auth`, `db` y `simuladores` arriba, **desde `-despliegue`** | |
| 0.2 | APK de depuración de `main`: `Get-FileHash -Algorithm SHA256 <ruta del APK de depuración de main>` `[DEV B1]` | Anotar el SHA-256 y el commit de `main` del que salió | |
| 0.3 | `curl.exe -k -s -o NUL -w "%{http_code}" https://localhost:8443/v1/salud` | `200` | |
| 0.4 | `adb devices` | El S23 Ultra (`R5CW21ERL2L`) como `device` | |
| 0.5 | `adb reverse tcp:8443 tcp:8443` y `adb reverse --list` | `tcp:8443 tcp:8443` | |
| 0.6 | Hoja de placas impresa (`ZZA-101` al menos) | A mano | |

## (a) De la CA de Caddy a la CA local de NGINX (contrato §2 "Local", §8 v2.1)

| Paso | Comando o acción | Esperado | Resultado |
|---|---|---|---|
| a.1 | En el teléfono: Ajustes › Seguridad y privacidad › Más ajustes de seguridad › Ver certificados de seguridad › **Usuario** › la CA de Caddy (`Caddy Local Authority - 2026 ECC Root`) › **Quitar** | Ya no está en la lista de Usuario | |
| a.2 | En la PC: `Remove-Item -Recurse -Force C:\Willy\Trabajo\MININTER\ca-local` | `Test-Path C:\Willy\Trabajo\MININTER\ca-local` → `False`. Va al acta (§8 v2.1) | |
| a.3 | La CA local de NGINX que genera el script de `infra/` (fuera del repositorio) `[DEV B1: ruta del archivo]`. Anotar su **huella SHA-256** con `certutil -dump <archivo>` («Hash de cert(sha256)») | El archivo existe **fuera** del repositorio; huella anotada | |
| a.4 | `adb push <archivo de la CA de NGINX> /sdcard/Download/`; en el teléfono: Ajustes › Seguridad y privacidad › Más ajustes de seguridad › Instalar desde el almacenamiento › **Certificado de CA**; después `adb shell rm /sdcard/Download/<archivo>` | La CA aparece en Ver certificados de seguridad › Usuario, con la **misma huella** de a.3; `Download/` sin el archivo | |
| a.5 | Desinstalar lo que haya: `adb uninstall pe.prototipo.movilbuscador` | `Success` (o `Unknown package`) | |
| a.6 | `adb install <APK de depuración de main>` y `adb shell dumpsys package pe.prototipo.movilbuscador \| Select-String "flags="` | `Success`; `DEBUGGABLE`, sin `ALLOW_BACKUP` | |
| a.7 | Abrir "Movil Buscador" e iniciar sesión con `agente1` | **HOME-01** de agente1. En la API: `POST /v1/auth/login` 200 y `GET /v1/me` 200 (`docker compose … logs api --since 2m`) | |
| a.8 | "Consultar placa", `ZZA-101`, "Control vehicular", "Consultar" | PLA-05 "TIENE REQUISITORIA" | |
| a.9 | Control: la API **no** ve la clave. `docker compose … logs proxy --since 5m` y `logs api --since 5m`, buscando la clave que dicta el humano **sin escribirla en un archivo** (por ejemplo, `Select-String -SimpleMatch` con la clave tecleada en la consola) | Ninguna línea | |

> Si en a.7 la app muestra "No se pudo completar la operación; intente nuevamente", es TLS: se revisa que la huella de a.4 sea la de a.3 y que el `proxy` sirva un certificado firmado por esa CA (`[DEV B1]`: cómo ver el error de TLS en el log de NGINX). Es un `ROJO` y se avisa al LEAD.

## (b) Nivel 1: a quién se conecta (PCAPdroid)

Requiere **Wi-Fi real** en el teléfono: el túnel de `adb reverse` no sirve para esto. El `adb reverse` de 0.5 puede seguir (la app lo usa para la API), pero la captura mira todo lo que sale.

| Paso | Comando o acción | Esperado | Resultado |
|---|---|---|---|
| b.1 | Instalar **PCAPdroid** (GPL-3.0) `[DEV B1: APK de F-Droid con su SHA-256, o el enlace de Google Play]`. Anotar la versión | Instalada; versión anotada | |
| b.2 | Cola antes: `adb shell run-as pe.prototipo.movilbuscador ls -la databases` y copia de `com.google.android.datatransport.events` a `C:\Willy\Trabajo\MININTER\flutter-capturas\red\cola-antes\` (como el paso 9.4 de la migración); `python -I pruebas\datos\revisar_datatransport.py C:\Willy\Trabajo\MININTER\flutter-capturas\red\cola-antes` | Anotar **la cantidad de eventos** de `events` (no su contenido); código 0 | |
| b.3 | Id de la tarea de subida: `adb shell dumpsys jobscheduler \| Select-String -Context 0,3 "pe.prototipo.movilbuscador"` | Anotar el id del job de `com.google.android.datatransport` (si no aparece, anotarlo: la cola puede no tener nada pendiente) | |
| b.4 | **Corrida 1, la app:** PCAPdroid › filtro de app = Movil Buscador (`pe.prototipo.movilbuscador`) › iniciar; aceptar el diálogo de VPN de Android | Captura en marcha | |
| b.5 | En la app: PLA-01 › 📷 › (el aviso, si sale, "Entendido"; HU-04 v7) › leer `ZZA-101` impresa › OCR-02 › "Usar esta placa" | OCR-02 con `ZZA-101` | |
| b.6 | Forzar la subida: `adb shell cmd jobscheduler run -f pe.prototipo.movilbuscador <id de b.3>` | Sin error | |
| b.7 | Esperar **5 minutos** (cronómetro) y detener la captura | — | |
| b.8 | Anotar de la lista de conexiones de PCAPdroid: por conexión, el **dominio** (DNS o SNI), el puerto, los **bytes** enviados y recibidos y la hora. Exportar el `.pcap` y copiarlo a `C:\Willy\Trabajo\MININTER\flutter-capturas\red\` (`adb pull`) | Se espera **una** conexión a `firebaselogging.googleapis.com` y las de la API local. **Cualquier otro dominio** se anota | |
| b.9 | Cola después: como b.2, en `…\red\cola-despues\` | Anotar la cantidad de eventos: se espera que **baje** (la cola se vació) | |
| b.10 | **Corrida 2, Google Play services:** PCAPdroid con el filtro de app = **Servicios de Google Play** (`com.google.android.gms`); repetir b.5 a b.8 (otra placa impresa) | Anotar **las conexiones nuevas** de `com.google.android.gms` en esa ventana: dominio, bytes y hora. Se comparan con el momento del OCR | |

## (c) Nivel 2: qué envía (mitmproxy, solo con el APK de depuración)

El APK de depuración confía en las CA de usuario (`<debug-overrides>`, MIGRACION v1.5 §6), así que la subida del proceso de la app se puede leer con la CA de mitmproxy. El tráfico de Google Play services **no** (no confía en las CA de usuario): para ese queda solo el nivel 1.

| Paso | Comando o acción | Esperado | Resultado |
|---|---|---|---|
| c.1 | Versiones: `mitmdump --version` y `protoc --version` `[DEV B1]` | Anotadas (mitmproxy es MIT; protoc, BSD-3) | |
| c.2 | En la PC: `mitmdump --listen-port 8080 --ssl-insecure -s pruebas\datos\mitm_guardar_subidas.py --set salida=C:\Willy\Trabajo\MININTER\flutter-capturas\red\cuerpos` (`--ssl-insecure` porque, hacia la API local, mitmproxy no conoce la CA de NGINX) | Escuchando en 8080 | |
| c.3 | El tráfico del teléfono por mitmproxy `[DEV B1: método probado y cómo se deshace]`. Por ejemplo: `adb reverse tcp:8080 tcp:8080` y `adb shell settings put global http_proxy 127.0.0.1:8080` | En el teléfono, el navegador a `http://mitm.it` muestra la página de mitmproxy | |
| c.4 | CA de mitmproxy como **CA de usuario**: desde `http://mitm.it` (Android) o con `adb push` de `%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.cer` a `/sdcard/Download/` e Instalar desde el almacenamiento › Certificado de CA; después borrar de `Download/` | Aparece en Usuario | |
| c.5 | En la app: iniciar sesión (si hace falta) y leer `ZZA-101` impresa con 📷 (como b.5) | OCR-02. En la consola de mitmdump se ven las solicitudes a la API local (no se guardan) | |
| c.6 | Forzar la subida como b.6 y esperar hasta 5 minutos | En `…\red\cuerpos\resumen.tsv`, al menos una línea a `firebaselogging.googleapis.com` | |
| c.7 | `python -I pruebas\datos\revisar_datatransport.py --cuerpos C:\Willy\Trabajo\MININTER\flutter-capturas\red\cuerpos` | Código 0: "Ninguna imagen … y ningún texto de placa ZZ en las subidas". **Si aparece una imagen o un texto `ZZ…`, es un `ROJO` y la decisión se reabre** | |
| c.8 | `cmd /c "protoc --decode_raw < C:\Willy\Trabajo\MININTER\flutter-capturas\red\cuerpos\<NNN>.bin > C:\Willy\Trabajo\MININTER\flutter-capturas\red\<NNN>.txt"` por cada cuerpo de c.6 (si `protoc` no lo decodifica, anotarlo: puede venir en otro formato) | Al registro: **qué categorías de campos** se ven (por ejemplo: paquete de la app, versión del SDK, modelo del equipo, un identificador, métricas, códigos de evento), **sin los valores** | |
| c.9 | Control del release (opcional, si sobra tiempo): con el APK de **release** instalado, la misma lectura | mitmproxy **no** puede leer su tráfico (el release no confía en CA de usuario): es lo esperado | |

## (e) Limpieza (siempre, aunque algo haya salido `ROJO`)

| Paso | Comando o acción | Esperado | Resultado |
|---|---|---|---|
| e.1 | Quitar el proxy del teléfono `[DEV B1]`, por ejemplo `adb shell settings put global http_proxy :0` y `adb reverse --remove tcp:8080` | `adb shell settings get global http_proxy` → `:0` o `null`; el navegador ya no va a `mitm.it` | |
| e.2 | En el teléfono: Ver certificados de seguridad › Usuario › **quitar la CA de mitmproxy** | Ya no está; la de NGINX **sigue** (se quita al cierre, §8) | |
| e.3 | Desinstalar **PCAPdroid** | No está en Ajustes › Aplicaciones | |
| e.4 | Cerrar `mitmdump` (Ctrl+C) | — | |
| e.5 | `Remove-Item -Recurse -Force C:\Willy\Trabajo\MININTER\flutter-capturas\red` | `Test-Path` → `False` | |
| e.6 | `adb reverse --remove-all` | `--list` vacío | |
| e.7 | Al terminar la sesión 1: pasar el registro (sin capturas ni valores identificadores) al TESTER y los resultados de los niveles 1 y 2 al LEAD para el ARCH | — | |


---

# Sesión 2 — cuando exista el VPS (fase B2)

Va aparte, con el **APK de release** publicado en el VPS (`scripts/publicar-apk.ps1`). La CA de NGINX local sigue en el teléfono (no molesta: el release no confía en CA de usuario).

## (d) Descarga por el enlace, sin cable (contrato §5 "Funciona sin cable") — **cuando exista el VPS (B2)**

| Paso | Acción | Esperado | Resultado |
|---|---|---|---|
| d.1 | Desconectar el cable; comprobar que el teléfono **no** tiene proxy (`adb shell settings get global http_proxy` → `:0` o `null`, antes de desconectar; la sesión 1 lo quitó en e.1); Wi-Fi o datos móviles | Sin proxy | |
| d.2 | Desinstalar "Movil Buscador" (Ajustes › Aplicaciones) | Desinstalada | |
| d.3 | En el navegador del teléfono: `https://<DOMINIO>/descargas/movil-buscador.apk`, con el usuario y la clave **de la descarga** que dicta el humano | Descarga el APK (sin aviso de certificado) | |
| d.4 | Permitir instalar desde esa fuente (Samsung, Android 16) e instalar | Instalada "Movil Buscador" | |
| d.5 | Login `agente1`; `ZZA-101` con motivo → "TIENE REQUISITORIA"; `ZZB-201` → sin requisitoria; `ZZZ-999` → placa no registrada | Los tres resultados | |
| d.6 | 📷 lee una placa impresa | OCR-02 con la placa | |
| d.7 | `supervisor1` → BIT-01 | Las consultas de d.5 | |
| d.8 | En la PC, el SHA-256 del APK descargado por la prueba `test_despliegue_vps.py` (`APK_SHA256`) es el que mostró `scripts/publicar-apk.ps1` | Iguales | |


**No** se baja el compose al terminar, salvo que el LEAD lo pida.
