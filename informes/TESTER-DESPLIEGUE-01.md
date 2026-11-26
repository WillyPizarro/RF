# Informe TESTER — DESPLIEGUE-01

**Contrato:** `docs/contratos/CONTRATO-DESPLIEGUE-01.md` **v2.1** (aprobado el 25-nov), con la anotación `1cb361a` (`DESCARGA_APK_DIR`).
**Encargo:** `docs/contratos/ENCARGO-DESPLIEGUE-01.md`, **M-3** (fase B1, sin VPS), y la sesión 1 del teléfono por la **M-5** y la **M-6** puntos 1 a 7 (`c237fcf`). Contrato v2.2 (`c2ceb02`) para la sesión.
**Rama:** `despliegue-01`, worktree `C:\Willy\Trabajo\MININTER\Movil_Buscador-despliegue`, rebasada sobre `main` `889a91b`.
**Estado:** sobre la ENTREGA DEV B1 (`71b5ef0`): **regresión local con NGINX 78 de 78 en verde**, con la regla de la imagen ajustada por la M-4 (se apartó la prueba, vuelta 1). Guion de las dos sesiones completo. **Sesión 1 del teléfono (§5): (a), (b) y (c) VERDES; (e) en curso** (faltan la e.2 y la e.3, del humano); un incidente para el acta (el pcap por correo, M-6 p.7). No se miró el código del DEV (del `Dockerfile` solo se leen las líneas `FROM`, M-4).

La fase A (v1, `ef8917d`) dejó `test_despliegue_vps.py`, `test_compose_vps.py` y `pruebas/despliegue/COMANDOS-VPS.md` sin informe propio; quedan descritos aquí con sus cambios de la v2.1.

## 1. Qué hay (M-3, TESTER)

| Punto de la M-3 | Archivo | Qué cambió |
|---|---|---|
| 1. Pruebas de NGINX en local | `services/api/tests/test_proxy_nginx.py` (nuevo) | Ver la matriz §2 |
| 2. `test_despliegue_vps.py` | `services/api/tests/test_despliegue_vps.py` | De Caddy a NGINX; la ruta del APK (`401`, `200` con `APK_SHA256`, `404` en el resto de `/descargas/`); la redirección por HTTP también para la ruta del APK y sin pedir la credencial por HTTP; el APK descargado no es depurable (`aapt`). Se sigue omitiendo sin `URL_VPS` (comprobado: 21 omitidas) |
| 2 bis. Compose del VPS | `services/api/tests/test_compose_vps.py` | v2: `certbot` en el VPS y sin puertos; el `proxy` es `nginx` con versión fijada; el volumen de `DESCARGA_APK_DIR` de solo lectura; `certbot` no cuenta como herramienta con perfil |
| 2 ter. Comandos en el VPS | `pruebas/despliegue/COMANDOS-VPS.md` | v2.1: el APK de release descargado de la ruta (§8), `certbot renew --dry-run` (§9), la credencial de la descarga fuera de los logs (§10) y el `htpasswd` y el APK fuera del repositorio (§11) |
| 3. Guion del teléfono | `pruebas/datos/GUION-DESPLIEGUE-01-dispositivo.md` (nuevo) | **Sesión 1, local** (dato del LEAD): (a) de la CA de Caddy a la de NGINX con un login de `agente1`; (b) nivel 1 con PCAPdroid (la app y después `com.google.android.gms`, con la placa `ZZ` impresa y la subida forzada); (c) nivel 2 con mitmproxy y el APK de depuración; (e) limpieza. **Sesión 2, con el VPS:** (d) la descarga del release sin cable. Lo que depende de la entrega del DEV está marcado `[DEV B1]` |
| 3 bis. Herramientas del nivel 2 | `pruebas/datos/mitm_guardar_subidas.py` (nuevo) y `pruebas/datos/revisar_datatransport.py --cuerpos` | El complemento de mitmproxy guarda solo los cuerpos de las subidas a servidores que no son `localhost` (sin cabeceras, sin la consulta de la URL, sin respuestas). El modo `--cuerpos` los descomprime (gzip, zlib y gzip incrustado) y busca imágenes y texto `ZZ…`. Probado con cuerpos sintéticos: limpio → código 0; `zza-101` en gzip y un JPEG en un gzip incrustado → código 1 con los dos hallazgos |
| 3 ter. Guion de la migración | `pruebas/datos/GUION-MIGRACION-FLUTTER-dispositivo.md` | Nota al inicio: sus pasos de Caddy (0.6, 0.6b, 11.8b, 11.10, 11.10b y 12.3) se reemplazan por la parte (a) del guion nuevo y por el informe del DEV para NGINX |
| Comentarios | `conftest.py`, `test_hu04_sin_cache.py` | "CA local de Caddy" → "CA local del proxy (NGINX)". Sin cambios de lógica |

## 2. Matriz: caso del contrato → prueba (NGINX en local)

| Caso (contrato v2.1) | Prueba en `test_proxy_nginx.py` |
|---|---|
| §1 "Solo `/v1/*` y el APK": `404` al resto | `test_rutas_fuera_de_v1_y_del_apk_dan_404` (11 rutas: `/`, `/openapi.json`, `/docs`, `/v2/salud`, `/salud`, `/descargas`, `/descargas/`, `/descargas/otro.apk`, `/descargas/movil-buscador.apk/`, mayúsculas, subcarpeta) |
| §1 `/v1/` llega a la API | `test_v1_sigue_llegando_a_la_api` (con la cabecera de traza) |
| §2 "HTTP → HTTPS" y §5 "Solo por HTTPS" | `test_http_redirige_a_https` (`/v1/salud` y la ruta del APK: `301` o `308` a `https://`, sin `WWW-Authenticate` por HTTP) |
| §2 "Solo TLS 1.2 y 1.3" | `test_tls_12_y_13_completan` y `test_tls_10_y_11_no_completan` (si el OpenSSL de la PC no puede ofrecer 1.0 o 1.1, se omite como NO VERIFICADO; no se da por verde) |
| §2 "Cabeceras de seguridad" en **toda** respuesta | `test_cabeceras_de_seguridad_en_toda_respuesta` (`200`, `404` del proxy, `401` de la descarga, error de la API y `413`) |
| §2 "Cuerpo máximo" | `test_cuerpo_de_mas_de_5_mb_recibe_413_del_proxy` (sin la traza de la API) y `test_cuerpo_de_menos_de_5_mb_llega_a_la_api` (con la traza) |
| §2 "Registro sin secretos" | La de siempre, `test_hu01_bitacora_config.py::test_la_clave_no_queda_en_los_logs_del_proxy`, ahora sobre NGINX |
| §2 "Caddy desaparece" y §1 imagen fijada | `test_proxy_es_nginx_con_version_fijada` y `test_no_queda_el_caddyfile` |
| §5 "Sin credencial" | `test_descarga_sin_credencial_401_con_basic` |
| §5 "Credencial incorrecta" | `test_descarga_con_credencial_incorrecta_401` (usuario, clave, las dos) |
| §5 "Con credencial" | `test_descarga_con_credencial_200_y_mismo_sha256` (archivo de prueba de bytes aleatorios, no un APK, en `DESCARGA_APK_DIR/movil-buscador.apk`; al terminar se deja lo que había) |
| §5 "Otras rutas" con credencial | `test_otras_rutas_de_descargas_dan_404_tambien_con_credencial` |
| §5 "Ruta exacta": volumen de solo lectura | `test_volumen_de_la_descarga_es_de_solo_lectura` |
| §5 "La clave no queda en los logs" | `test_la_credencial_de_la_descarga_no_queda_en_los_logs_del_proxy` (ni la clave, ni una clave incorrecta, ni el valor Basic, ni la cabecera `Authorization`) |
| Regresión: `no-store` por el proxy | `test_hu04_sin_cache.py` (por el proxy), sin cambios |

La credencial se lee de `DESCARGA_APK_USUARIO` y `DESCARGA_APK_CLAVE` de `infra/.env` y nunca se escribe; los mensajes de las pruebas no la incluyen.

## 3. Cómo se corren

Con el compose con NGINX arriba desde `-despliegue` y el venv de pruebas (`pytest==9.2.0`):

```
PROXY_DISPONIBLE=1 C:/Willy/Trabajo/MININTER/venv-pruebas/Scripts/python.exe -m pytest \
  services/api/tests/test_proxy_nginx.py services/api/tests/test_hu04_sin_cache.py \
  services/api/tests/test_hu01_bitacora_config.py::test_la_clave_no_queda_en_los_logs_del_proxy \
  services/api/tests/test_compose_vps.py --integracion --url-base https://localhost:8443
```

Contra el VPS (fase B2): `URL_VPS=https://<DOMINIO>`, `CLAVE_USUARIOS_PRUEBA`, `DESCARGA_APK_USUARIO`, `DESCARGA_APK_CLAVE` y `APK_SHA256` en el entorno, y `pytest services/api/tests/test_despliegue_vps.py`.

## 4. Resultados

**Corrida sobre la ENTREGA DEV B1 (`71b5ef0`, 25-nov), una vez, ~31 s**, con el compose arriba desde `-despliegue` (comando del §3, más `test_compose_vps.py`): **78 de 78 en verde**.

| Archivo | Resultado |
|---|---|
| `test_proxy_nginx.py` | 32 de 32, incluida `test_proxy_es_nginx_con_version_fijada` con la regla de la M-4 (`build:` con `FROM nginx:1.30.8-alpine`; `nginx -v` en marcha = 1.30.8) |
| `test_compose_vps.py` | Todo en verde, incluida `test_proxy_del_vps_es_nginx_fijado` (M-4) |
| `test_hu04_sin_cache.py` (red interna y proxy) | 28 de 28 |
| `test_hu01_bitacora_config.py::test_la_clave_no_queda_en_los_logs_del_proxy` | Verde, sobre NGINX |

`movil-buscador-descargas` quedó vacía, como estaba. El guion quedó completo con el informe del DEV (sin marcas `[DEV B1]`): APK de depuración de `main` `5f62f6a4…`, PCAPdroid 2.0.5, mitmproxy 12.3.1, `protoc` 36.2, el proxy del teléfono en el **8090** y cómo se deshace, la CA de mitmproxy en `C:/Willy/Trabajo/MININTER/flutter-capturas/red/mitm-conf`, las huellas esperadas de las dos CA y, en (a), el borrado de `ca-local` y de los volúmenes `movil-buscador_caddy-datos` y `_caddy-config` (los borra el DEV; van al acta). **Diferencia con el informe del DEV:** el guion no guarda los flujos de mitmproxy con `-w` (llevarían el login con la clave); solo guarda los cuerpos de las subidas con `mitm_guardar_subidas.py`.

### Corridas anteriores (M-3)

**Regresión local con NGINX** (25-nov, una vez, ~30 s; comando del §3), con el compose recreado por el DEV a las ~17:47 (`proxy` de `infra/nginx/`, `PROXY_PUERTO_HTTP=8080`, `PROXY_PUERTO_HTTPS=8443`, `DESCARGA_APK_DIR` = `C:\Willy\Trabajo\MININTER\movil-buscador-descargas`):

| Archivo | Resultado |
|---|---|
| `test_proxy_nginx.py` | **31 de 32** en verde: 404 (11 rutas y 6 con credencial), `/v1` llega a la API, HTTP → HTTPS (`/v1/salud` y la ruta del APK, sin `WWW-Authenticate`), TLS 1.2 y 1.3 sí y 1.0 y 1.1 no (el OpenSSL 3.0.16 de la PC sí los ofrece, así que no quedó omitida), HSTS y `nosniff` en las cinco respuestas, `413` sin traza y el cuerpo menor con traza, la descarga (`401` con Basic, `401` con usuario, clave o las dos incorrectas, `200` con el mismo SHA-256), volumen de solo lectura y la credencial fuera de los logs. **ROJO:** `test_proxy_es_nginx_con_version_fijada` |
| `test_hu04_sin_cache.py` (red interna y proxy) | **28 de 28** |
| `test_hu01_bitacora_config.py::test_la_clave_no_queda_en_los_logs_del_proxy` | Verde (sobre NGINX) |
| `test_compose_vps.py` | **ROJO:** `test_proxy_del_vps_es_nginx_fijado`; el resto en verde (`certbot` sin puertos, volumen de solo lectura, sin credenciales de administración en la API) |

Después de la corrida, `movil-buscador-descargas` quedó como estaba (vacía).

**El rojo, para el arbitraje del LEAD:** el contrato §1 dice "`proxy` (**NGINX, imagen oficial `nginx` con versión estable fijada por el DEV**)". El compose del DEV no declara `image:` sino `build:` de `infra/nginx/` (aviso del DEV: `nginx:1.30.8-alpine` más `openssl`). La imagen construida, `movil-buscador-proxy`, trae `NGINX_VERSION=1.30.8` (`docker image inspect`). La prueba exige `image: nginx:<versión>` y no se aflojó. Puede ser que el código se apartó (el contrato pide la imagen oficial tal cual), que se apartó la prueba (si "imagen oficial" incluye una imagen propia `FROM nginx:<versión fijada>`) o que el contrato no lo dice. No se miró el `Dockerfile`.

Antes de esta corrida hubo una que **no cuenta**: coincidió con un reinicio del compose por el DEV (`service "api" is not running`) y con un error de alcance de fixture mío en `test_proxy_nginx.py` (`https` de módulo sobre `sistema_sano` de función), ya corregido.

Sin el sistema también se comprobó: los archivos compilan (`py_compile` con `-W error`), `test_despliegue_vps.py` se omite entero sin `URL_VPS` (21 omitidas) y el modo `--cuerpos` (§1).

## 5. Sesión 1 del teléfono (M-5 y M-6), 25-nov

**Fuente:** el registro del DEV, `C:\Willy\Trabajo\MININTER\Movil_Buscador_capturas\DESPLIEGUE-01\resultados-sesion1.md`, que está fuera del repositorio. Me lo pasó el LEAD.

- **Equipo:** el S23 Ultra, con el compose arriba solo desde `-despliegue`.
- **Quién hizo qué:** el DEV corrió los `adb`, PCAPdroid y mitmproxy. El humano operó el teléfono con los pasos que le llegaban por el LEAD (M-6 p.3). El TESTER no corrió `adb`.
- **Qué va aquí:** solo dominios, categorías, conteos y horas. Ningún identificador: ni de instalación, ni huella del build, ni UID, ni id de job.

**Resultado:** las partes (a), (b) y (c) están **VERDES**, según el LEAD. La (e) está **en curso**: faltan dos pasos del humano. Ningún paso salió `ROJO`.

### 5.1 Parte 0 y (a): de la CA de Caddy a la de NGINX

| Paso | Resultado |
|---|---|
| 0.1 a 0.6 | OK. El APK de depuración coincide con `5f62f6a4…`. El primer `adb devices` salió vacío porque el cable aún no estaba conectado; el segundo, OK |
| a.1 y a.2 | OK. El humano quitó la CA de Caddy del teléfono. El DEV borró `ca-local`, que solo tenía `caddy-root.crt`, y los volúmenes `movil-buscador_caddy-datos` y `movil-buscador_caddy-config`, que no usaba ningún contenedor. **Van al acta** |
| a.3 y a.4 | OK. La CA de NGINX exportada fuera del repositorio tiene la huella esperada, `14:74:99:F3…98:D2`, y no se regeneró. Quedó instalada en Usuario con esa huella; la de Caddy ya no está. El `.crt` no quedó en `Download/` |
| a.5 y a.6 | OK. El APK es depurable y no permite copias de seguridad (no tiene `ALLOW_BACKUP`) |
| a.7 y a.8 | OK. El login de `agente1` llega a HOME-01, con `POST /v1/auth/login` y `GET /v1/me` en 200 por HTTP/2. ZZA-101 da "TIENE REQUISITORIA", con `POST /v1/consultas/placa` en 200. El log del proxy no tiene ningún `handshake` |
| a.9 | OK. La clave no aparece en los logs: 0 de 4 líneas del proxy y 0 de 107 de la API. La clave estuvo solo en memoria, y el script se borró |

### 5.2 Parte (b), nivel 1 con PCAPdroid 2.0.5 (M-6 p.1 y p.5)

**Corrida 1, la app (filtro Movil Buscador).** Teléfono en Wi-Fi real, sin otra VPN y sin `http_proxy`.

| Qué | Resultado |
|---|---|
| Cola antes del OCR (b.2) | **0 eventos**. La base de `datatransport` todavía no existía porque la app se acababa de instalar |
| OCR (b.5) | ZZA-101, de la hoja impresa, ~20:09–20:10 |
| Cola antes de forzar la subida (b.3, 2.ª vez) | **5 eventos `FIREBASE_ML_SDK`**, con destino `firebaselogging.googleapis.com`, sin intentos y sin cargas útiles. **2 jobs** de `JobInfoSchedulerService`. `revisar_datatransport.py` sale con código 0: ninguna imagen ni texto `ZZ` |
| Lo que la cola deja leer, por categoría | Paquete de la app, versión del SDK, idioma, **un identificador de instalación**. Del equipo: país, producto, modelo, fabricante, hardware, build y huella del SO, SDK de Android, tipo de red y zona horaria |
| Subida forzada (b.6) | 20:11:34, `run -f` de los 2 jobs, los dos `Running job [FORCED]` con código 0 |
| Conexiones de la app (b.8) | **2 conexiones, las dos cerradas, ningún otro dominio:** (1) DNS/UDP 53, consulta `firebaselogging.googleapis.com`, 76 B enviados y 204 B recibidos, 20:11:34; (2) HTTPS/TCP 443, SNI `firebaselogging.googleapis.com`, IP de Google, 2,7 KB enviados y 5,4 KB recibidos, 20:11:34–20:12:36. Fuente: la lista y el detalle de PCAPdroid, sin pcap (el volcado estaba en "Ninguno"). La API local no aparece porque va por `adb reverse` y no pasa por la VPN de PCAPdroid |
| En la ventana del OCR | **Ninguna conexión.** La conexión a Google sale solo con la subida forzada |
| Cola después (b.9) | **0 eventos**, sin jobs pendientes, código 0 |
| **Decisión de la M-6 p.1** | **Se corre la (c):** la app tiene tráfico a `firebaselogging.googleapis.com`. Según la M-6 p.5, la cola pasó de 5 a 0 **con un envío visible** (TCP 443 a las 20:11:34): **no es una anomalía** |

**Corrida 2, `com.google.android.gms` (filtro Servicios de Google Play).** Según la M-6 p.1, esta corrida no decide; se anota igual.

| Qué | Resultado |
|---|---|
| OCR | ZZB-201, hecho a las 20:35:45 |
| Cola de la app | **5 eventos** antes de forzar la subida (código 0, ningún `ZZ` ni imagen) y **0** después. Los 2 jobs se forzaron a las 20:35:56, con código 0. La subida sale por el UID de la app, así que no entra en el filtro de esta corrida |
| Conexiones de gms (pcap 20_34_36) | DNS: `mtalk.google.com` ×2. **5 conexiones TCP 5228 a `mtalk.google.com`** (FCM), de ~1,9 a 4,7 KB, que se reconectan cada ~1–1,5 min. Una estuvo abierta durante el OCR y la subida (**DENTRO** de la ventana, 2347/4688 B); las otras 4 fueron después (**FUERA**). **Ninguna a `firebaselogging` ni a otro host** en la ventana |
| pcap anterior (20_31_19) | Es de antes del OCR y no se confirmó su filtro. DNS de `spot-pa.googleapis.com` y `mtalk.google.com`, UDP/QUIC 443 a `spot-pa.googleapis.com` (6662/5691 B) y TCP 5228 a `mtalk` (2310/1950 B). Todo **FUERA** de la ventana |
| Pantallas de la corrida 2 | `NO HECHO`: el teléfono estaba bloqueado. La fuente de esta corrida es el pcap |
| Cierre | PCAPdroid detenido y **sin VPN activa** |

### 5.3 Parte (c), nivel 2 con mitmproxy 12.3.1 (M-6 p.6)

| Qué | Resultado |
|---|---|
| Lo que pide la M-6 p.6 | OK en todo. El APK es el de depuración (a.6). Antes de la c.5 se leyó una placa `ZZ` nueva (ZZB-201), así que la cola volvió a tener **5 eventos** antes de forzar la subida. Los ids de los jobs se sacaron de nuevo y no habían cambiado. El `run -f` se repitió |
| c.1 a c.4 | OK. mitmdump escucha en el **8090**, **sin `-w`**, con `mitm_guardar_subidas.py`. El proxy del teléfono quedó en `127.0.0.1:8090` y `mitm.it` responde a través de él. La CA de mitmproxy tiene la huella esperada, `95:E3:03:AC…BD:AC`, y está instalada en Usuario junto a la de NGINX. El `.cer` se borró de `Download/` |
| c.5, el OCR por el proxy | ZZB-201 a las 20:52, sin error. Por el proxy pasaron solo las llamadas a la API local (no se guardan). **Antes del `run -f` no hubo ningún POST a `firebaselogging`, así que no hubo subida automática** |
| c.6, la subida forzada | `run -f` a las 20:53:37. La conexión a `firebaselogging.googleapis.com:443` sale a las 20:53:38, con **2 POST a `/v0cc/log/batch`**, los dos `200 OK`. La cola pasó de **5 a 0** |
| c.7, los cuerpos | **2 cuerpos**, `Content-Type: application/json`, `Content-Encoding: gzip`, de **819 B y 1827 B** ya descomprimidos (mitmproxy los guarda decodificados; empiezan con `{`). `revisar_datatransport.py --cuerpos` sale con código 0. El DEV buscó además en el JSON y en los base64 decodificados: 0 `ZZB-201`, 0 `ZZB201`, 0 `ZZA-101`, 0 `ZZA101`, 0 `ZZ` y 0 firmas JPEG o PNG, ni crudas ni en base64 |
| c.8, categorías | **El cuerpo entero es JSON, no protobuf.** Contiene `logRequest[]` con la hora y el uptime; `clientInfo` (tipo de cliente; Android: SDK, modelo, hardware, dispositivo, producto, build del SO, fabricante, **huella del build**, idioma, país, mcc/mnc y build de la app); `logSourceName`; `logEvent[]` (hora, uptime, zona horaria, tipo de red y `sourceExtension`); y `qosTier`. Los **5 `sourceExtension`**, uno por evento, son protobuf en base64. Con `protoc --decode_raw` (código 0) dan: paquete de la app, versión del SDK de ML Kit, idioma y región, **un UUID de instalación**, y el resto son **solo enteros** (códigos de evento, tiempos y métricas). **Ningún texto libre ni bytes de imagen.** No se anotaron valores |
| c.9 | `NO HECHO`: es opcional, y el LEAD ordenó no correrla |

**Lo que muestran los niveles 1 y 2 juntos**, para la evaluación del ARCH:
- **Qué sale y cuándo:** la app solo habla con `firebaselogging.googleapis.com`, y solo cuando corre el job de `datatransport`. No sale nada en el momento del OCR.
- **Qué lleva:** telemetría de uso de ML Kit con datos del equipo y un identificador de instalación.
- **Qué no lleva:** ni la imagen ni el texto de la placa (ninguna placa `ZZ` en dos lecturas, ZZA-101 y ZZB-201).

### 5.4 Parte (e), limpieza, en curso

| Paso | Resultado |
|---|---|
| e.1 | OK. Se quitó el proxy en el orden del guion y `http_proxy` volvió a `null`. Sin el proxy, `mitm.it` responde con el sitio real ("traffic is not going through mitmproxy") |
| e.2 | **Pendiente del humano:** quitar la CA de mitmproxy. La de NGINX se queda |
| e.3 | **Pendiente del humano:** desinstalar PCAPdroid |
| e.4 | OK. mitmdump cerrado y el 8090 sin escucha. Se borró el log de consola, que estaba en el scratchpad |
| e.5 y los pcap | OK. Se borraron: los 2 pcap del teléfono y la carpeta `Download/PCAPdroid` (`find *pcap*` da 0); el pcap de `Movil_Buscador_capturas\DESPLIEGUE-01\`; y `flutter-capturas\red\`, con 30 archivos (colas, pantallas, pcap, cuerpos, salidas de `protoc` y `mitm-conf` con la CA y su llave). No quedaron capturas de pantalla en el teléfono: se tomaron por `adb exec-out`, directo a la PC |
| e.6 | OK. Se corrió `adb reverse --remove-all` y la lista quedó vacía |

**Comprobado por el TESTER en la PC, sin `adb`:**
- `flutter-capturas\red` no existe.
- No queda ningún `*pcap*` en `Movil_Buscador_capturas` ni en `Downloads`.
- En `Movil_Buscador_capturas\DESPLIEGUE-01\` queda solo el registro.
- El repositorio (`git ls-files` de `-despliegue`) no tiene ningún pcap, captura, cuerpo, `.cer`, `.crt` ni `.pem`. Los únicos `.png` son los íconos de la app.
- `git status` está limpio.

### 5.5 Para el acta de eliminación

- **Lo borrado de la CA de Caddy:** `C:\Willy\Trabajo\MININTER\ca-local\` y los volúmenes `movil-buscador_caddy-datos` y `movil-buscador_caddy-config`, con la llave de la CA.
- **Dónde estaban las capturas borradas:**
  - teléfono: `Download/PCAPdroid/` (2 pcap);
  - PC: `Movil_Buscador_capturas\DESPLIEGUE-01\` (1 pcap), `Downloads\` y `flutter-capturas\red\`, que incluía la CA de mitmproxy y su llave.
- **Incidente del pcap por correo (M-6 p.7):**
  - **Qué pasó:** el pcap de la corrida 2 salió del teléfono **por correo**, al correo propio del humano, para pasarlo a la PC. Es una **salida a un servicio externo**.
  - **Qué contenía:** ningún dato real. Solo telemetría de red de un teléfono de prueba: conexiones de Servicios de Google Play a `mtalk.google.com`, con el identificador de instalación y datos del equipo.
  - **Pendiente del humano:** borrarlo de Enviados, de la Bandeja de entrada y de la papelera, en el teléfono y en la PC. Lo confirma por el PM.
  - **Regla desde ahora**, también para el bloque HU-05 + HU-06: el pcap sale del teléfono **solo por `adb pull`**, nunca con "compartir" ni por correo.
- **Falta averiguar quién borró la copia de `Downloads\`:** cuando el DEV fue a borrarla en la (e), ya no estaba. El registro dice que cómo llegó el pcap a la PC lo confirma el PM.

### 5.6 Observaciones, sin rojo

1. **Pantallas de la corrida 2:** quedaron sin recorrer porque el teléfono estaba bloqueado. La corrida 2 se respalda solo con el pcap. No decide nada (M-6 p.1).
2. **pcap anterior (20_31_19):** no se confirmó con qué filtro se tomó. Como está fuera de la ventana, no cambia el resultado.
3. **USB en la b.9:** el enlace falló una vez. Windows mostró "Error de solicitud de descriptor de dispositivo". Las dos copias de la cola salieron de 0 bytes, se descartaron y **no se contaron como cola vacía**. Con otro puerto y otro cable salió bien.
4. **Login en la c.5:** dio un `401` antes del `200`. Es coherente con un error al teclear la clave. Ya se sabía que el login de la app funciona (a.7).
5. **Forma del cuerpo en el guion:** la c.8 esperaba aplicar `protoc` al cuerpo entero. El cuerpo es JSON con `sourceExtension` en base64 y protobuf, y el DEV decodificó cada `sourceExtension` aparte. La búsqueda de `revisar_datatransport.py --cuerpos` cubre el cuerpo tal cual. La búsqueda del DEV sobre los base64 decodificados cubre lo de adentro.

## 6. NO VERIFICADO

| Qué | Motivo |
|---|---|
| §2 `/.well-known/acme-challenge/` sin redirección | Solo existe en el VPS con `certbot` (fase B2) |
| §2 `X-Forwarded-For` y `X-Forwarded-Proto` | No es observable desde afuera; el contrato pide que la API siga respondiendo igual, y eso lo cubre la regresión |
| Lo del VPS (`test_despliegue_vps.py`, `COMANDOS-VPS.md`) | No hay VPS (fase B2) |
| Sesión 2 del teléfono, la (d): la descarga del release sin cable | Necesita el VPS (fase B2) |
| e.2 y e.3 de la sesión 1 (la CA de mitmproxy fuera; PCAPdroid desinstalado) | Pendientes del humano cuando se escribió esto. El almacén de usuario no se lee por `adb` sin root, así que lo confirma el humano por el LEAD |
| Que el pcap se borró del correo (M-6 p.7) | Lo confirma el humano por el PM |
