# Informe TESTER — DESPLIEGUE-01

**Contrato:** `docs/contratos/CONTRATO-DESPLIEGUE-01.md` **v2.1** (aprobado el 25-nov), con la anotación `1cb361a` (`DESCARGA_APK_DIR`).
**Encargo:** `docs/contratos/ENCARGO-DESPLIEGUE-01.md`, **M-3** (fase B1, sin VPS).
**Rama:** `despliegue-01`, worktree `C:\Willy\Trabajo\MININTER\Movil_Buscador-despliegue`, rebasada sobre `main` `889a91b`.
**Estado:** sobre la ENTREGA DEV B1 (`71b5ef0`): **regresión local con NGINX 78 de 78 en verde**, con la regla de la imagen ajustada por la M-4 (se apartó la prueba, vuelta 1). Guion de las dos sesiones completo. No se miró el código del DEV (del `Dockerfile` solo se leen las líneas `FROM`, M-4).

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

`movil-buscador-descargas` quedó vacía, como estaba. El guion quedó completo con el informe del DEV (sin marcas `[DEV B1]`): APK de depuración de `main` `5f62f6a4…`, PCAPdroid 2.0.5, mitmproxy 12.3.1, `protoc` 36.2, el proxy del teléfono en el **8090** y cómo se deshace, la CA de mitmproxy en `flutter-capturased\mitm-conf`, las huellas esperadas de las dos CA y, en (a), el borrado de `ca-local` y de los volúmenes `movil-buscador_caddy-datos` y `_caddy-config` (los borra el DEV; van al acta). **Diferencia con el informe del DEV:** el guion no guarda los flujos de mitmproxy con `-w` (llevarían el login con la clave); solo guarda los cuerpos de las subidas con `mitm_guardar_subidas.py`.

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

## 5. NO VERIFICADO

| Qué | Motivo |
|---|---|
| §2 `/.well-known/acme-challenge/` sin redirección | Solo existe en el VPS con `certbot` (fase B2) |
| §2 `X-Forwarded-For` y `X-Forwarded-Proto` | No es observable desde afuera; el contrato pide que la API siga respondiendo igual, y eso lo cubre la regresión |
| Lo del VPS (`test_despliegue_vps.py`, `COMANDOS-VPS.md`) | No hay VPS (fase B2) |
| Sesiones del teléfono | Las corre el DEV con el PM y el humano cuando lleguen las entregas de B1 (sesión 1) y con el VPS (sesión 2) |
