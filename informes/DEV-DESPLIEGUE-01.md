# Informe DEV — DESPLIEGUE-01 (fase A sin VPS; v2.1: fase B1, NGINX y ML Kit)

**Documento de trabajo:** `docs/contratos/CONTRATO-DESPLIEGUE-01.md` **v1** · **Encargo:** `docs/contratos/ENCARGO-DESPLIEGUE-01.md` (fase A) · **Rama:** `despliegue-01`, en el worktree `C:\Willy\Trabajo\MININTER\Movil_Buscador-despliegue` · **Fecha:** 2026-11-19

- **Sin secretos:** no hay ninguno en el repositorio. Copié `infra/.env` de la carpeta principal al worktree solo para las verificaciones locales; está ignorado por git y no se commitea.
- **Sin contrataciones:** no compré ni creé nada, ni cuentas ni servicios.
- **Pruebas del TESTER:** no las leí.

## Qué construí

### `infra/docker-compose.vps.yml` (nuevo)

Se usa **siempre** junto con `infra/docker-compose.yml` y **nunca** con el compose de fotos.

- **`db`, `auth-preparar` y `auth`:** quedan en el perfil `solo-local`, así que ni `up` ni `config` los incluyen. Base y Auth los da Supabase.
- **`api`:**
  - Con `!reset`, deja de recibir `AUTH_JWT_SECRETO`, `MIGRACION_DATABASE_URL`, `API_APP_CLAVE` y `CLAVE_USUARIOS_PRUEBA`.
  - No depende de `db` ni de `auth`; sí de `simuladores` sano.
  - No monta los tests.
- **`simuladores`:** sin los tests montados y sin origen de fotos.
- **`proxy`:** sin cambios. Publica 80 y 443 si el `.env` del VPS no tiene `PROXY_PUERTO_*`. Caddy obtiene el certificado de Let's Encrypt con `DOMINIO`.
- **`herramientas` (nuevo, perfil `herramientas`):** la imagen de la API con las credenciales que la API en marcha no tiene. No arranca con `up`. Se corre a mano para dos cosas:
  - `python -m app.migrar`;
  - `python -m app.cargar_usuarios`.

### `infra/docker-compose.yml`

`POSTGRES_*`, `AUTH_DB_CLAVE` y `AUTH_JWT_SECRETO` pasan de `${VAR:?}` a `${VAR:-}`.

- **Por qué:** compose interpola todo el archivo, incluso los servicios que quedan fuera por perfil. Sin el cambio, el VPS tendría que llevar valores falsos de la base local.
- **Qué sigue igual:** `DATABASE_URL` y `JWT_SECRETO` siguen siendo obligatorias.
- **Qué se pierde en local:** el aviso temprano de compose si falta una de esas variables. Postgres y GoTrue igual fallan al arrancar sin ellas.

### Credencial de administración de Auth (decisión 1)

- **`services/api/app/supabase_auth.py`:** la carga de usuarios usa **`AUTH_ADMIN_CLAVE`**, leída del entorno **solo** al cargar usuarios.
  - Va en `apikey` y en `Authorization: Bearer`, que es como la aceptan tanto la "secret key" nueva de Supabase (`sb_secret_…`) como la clave heredada `service_role`.
  - Si falta, firma como antes un token `service_role` con `AUTH_JWT_SECRETO` (Auth local).
  - Si no hay ninguna de las dos, falla con un mensaje claro.
  - **El login no cambia.**
- **Cómo se pasa:** en el VPS se exporta solo en la sesión SSH del comando de carga, nunca en el contenedor `api`. `scripts/desplegar.ps1 -CargarUsuarios` la pide por teclado, sin mostrarla ni guardarla. También puede ir en el `.env` del VPS (permisos 600), como admite el §4.

### `scripts/desplegar.ps1 <rama o commit>` (nuevo)

Entra por SSH con la llave dedicada: `-Servidor` o `MOVIL_VPS`, y `-Llave` o `MOVIL_VPS_LLAVE`. En el VPS, dentro de `/opt/movil-buscador`:

1. `git fetch --prune origin` y `checkout --detach` de `origin/<rama>` (o del commit).
2. `build` de `api`, `herramientas` y `simuladores`.
3. `run --rm herramientas python -m app.migrar`.
4. Opcional, con `-CargarUsuarios`: `app.cargar_usuarios`.
5. `up -d --build --remove-orphans`.
6. Espera a que `https://<DOMINIO>/v1/salud` responda `200`, con un máximo de 5 minutos. Si no, muestra `ps` y los logs, y falla.

No copia secretos (usa el `infra/.env` del VPS) y es idempotente.

### `apps/movil/eas.json`

- **Base:** el archivo no existe en `main`; nació en `hu-04`. Lo creé con el mismo perfil `development` de `hu-04`, para que el merge sea trivial.
- **Perfil `preview` nuevo:** `distribution: internal`, `developmentClient: false`, un APK de release (`assembleRelease`, con el JS embebido) y `EXPO_PUBLIC_API_URL=https://DOMINIO-PENDIENTE.invalid`.
- **El marcador:** el TLD `.invalid` está reservado y nunca resuelve, así que un APK generado por error no se conecta a ningún lado. Cuando haya dominio, se cambia por `https://<DOMINIO>` (manual, §6).

### `infra/.env.example`

- **`AUTH_ADMIN_CLAVE`:** queda documentada.
- **Sección del VPS:** lista solo los **nombres** de las variables que lleva el `.env` del VPS, y cuáles no van. Incluye la forma de las URL del *Session pooler* con `api_app.<ref>` y `postgres.<ref>`.

### `docs/despliegue/` (nuevo, en español simple)

- **`GUIA-PROBADORES.md`:** los 8 puntos del §7. La guía no tiene la clave: "se la da el responsable del demo".
  - Instalación en Samsung con Android 16 (incluido Auto Blocker) y una nota para otros Android.
  - Los usuarios.
  - Qué probar con las 3 placas y la bitácora.
  - Qué no funciona todavía.
  - Que todo es ficticio.
  - Cómo desinstalar.
- **`DOMINIO.md`:** comprar el dominio y crear el registro `A`, con el proxy de Cloudflare **apagado** para que Let's Encrypt llegue a Caddy. Cómo comprobarlo y cómo borrarlo.
- **`MANUAL-DESPLIEGUE.md`:**
  - el VPS (Ubuntu 24.04, Docker, usuario `deploy`, SSH sin clave y `ufw` con 22, 80 y 443);
  - Supabase (región São Paulo, Session pooler, registro abierto desactivado y claves);
  - el `.env` (solo nombres);
  - los comandos del §6, incluido el APK `preview` con `npx eas-cli@27.11.0`;
  - las comprobaciones, los logs y el borrado del §8.
- **`LLAVE-SSH.md`:**
  - la llave de despliegue en la PC;
  - la deploy key de GitHub en el VPS, de solo lectura;
  - cómo autorizarlas y cómo revocarlas al cierre.

## Lo que verifiqué en local

- **`docker compose -f infra/docker-compose.yml -f infra/docker-compose.vps.yml config`**, con un `.env` de ejemplo que tiene solo `DATABASE_URL`, `JWT_SECRETO` y `DOMINIO`:
  - Arma solo `api`, `proxy` y `simuladores`. Con `--profile herramientas`, suma `herramientas`.
  - Solo `proxy` tiene puertos: `80:80` y `443:443`.
  - El entorno de `api` tiene `AUTH_APIKEY`, `AUTH_URL`, `BLOQUEO_*`, `DATABASE_URL`, `FUENTE_*`, `JWT_SECRETO`, `PLACA_FORMATO_*`, `SESION_INACTIVIDAD_S`, `SIMULADORES_URL` y `TOKEN_ACCESO_VIGENCIA_S`. **Ninguna credencial de administración.**
- **La API en marcha no tiene la credencial:** levanté el contenedor `api` real con el compose del VPS (proyecto aparte, `vpsprueba`, ya borrado) y corrí `printenv`. Los nombres coinciden con la lista de arriba, más los del sistema. No aparecen `AUTH_ADMIN_CLAVE`, `AUTH_JWT_SECRETO`, `MIGRACION_DATABASE_URL`, `API_APP_CLAVE` ni `CLAVE_USUARIOS_PRUEBA`.
- **La carga con la credencial nueva:** corrí `app.cargar_usuarios` desde la imagen del worktree contra el Auth local con **`AUTH_ADMIN_CLAVE` y sin `AUTH_JWT_SECRETO`**: cargó los 5 usuarios. Sin ninguna de las dos credenciales falla con el mensaje esperado. Fue en la red local; la clave de prueba vivió en un archivo temporal que se borró.
- **La API arranca solo con `api_app`:** `python -m app.migrar` con solo `DATABASE_URL` (`api_app`) termina bien cuando la base ya está al día. Así arranca la API en el VPS después de que `herramientas` migró.
- **Sintaxis:** `scripts/desplegar.ps1` pasa el parser de PowerShell, y el bash que envía al VPS pasa `bash -n`.
- **Compose local:** el compose local con los dos archivos de siempre sigue armando los 6 servicios.

**NO VERIFICADO (necesita el VPS, el dominio o Supabase; va en la fase B):**

- la ejecución real de `desplegar.ps1` por SSH;
- el certificado de Let's Encrypt;
- las migraciones contra Supabase por el Session pooler, incluido que `api_app.<ref>` entre por Supavisor;
- `AUTH_ADMIN_CLAVE` con una `sb_secret_…` real;
- que Supabase acepte los correos `@usuarios.movil-buscador.test`;
- el APK `preview`;
- los puertos desde internet.

## Avisos para el LEAD

1. **`PENDIENTES.md`:** es ruta del LEAD. Los pasos del §8 están en `MANUAL-DESPLIEGUE.md` §9, `LLAVE-SSH.md` §4 y `DOMINIO.md` §5, listos para el acta de eliminación.
2. **Merge de `eas.json`:** `despliegue-01` crea `apps/movil/eas.json` con el mismo `development` que `hu-04`. Si `hu-04` se mergea antes, el merge solo agrega `preview`.
3. **Primer build de `preview`:** tiene que ser interactivo, porque EAS pregunta si genera la llave de firma de Android. Desde el segundo se puede usar `--non-interactive`. Está en el manual.
4. **Riesgo para la fase B:**
   - Si el proyecto de Supabase rechaza el dominio `.test` en los correos de los usuarios, habría que cambiar `correo_de` en `supabase_auth.py`, por ejemplo a un dominio `example.com`.
   - Ese cambio afectaría también al login (que deriva el correo del usuario), así que iría con una M-n.


---

# Contrato v2.1 — Fase B1 (sin VPS) y preparación de la red de ML Kit (M-3, 2026-11-25)

Rama `despliegue-01` (worktree `Movil_Buscador-despliegue`), rebasada sobre `main` `889a91b`. Contrato **v2.1** con la anotación `1cb361a` (`DESCARGA_APK_DIR`). Todavía no hay VPS: lo del VPS está escrito y validado con `docker compose config`, pero **NO VERIFICADO** contra un servidor real (fase B2).

## 1. NGINX (§1 y §2)

| Qué | Cómo |
|---|---|
| Imagen | `infra/nginx/Dockerfile`: `FROM nginx:1.30.8-alpine` (la estable de la rama 1.30, imagen oficial) **más `openssl`** (`apk add`), porque la alpine no lo trae y hace falta para la CA local, el certificado provisional del VPS y el `htpasswd`. El servicio se sigue llamando `proxy` |
| Configuración | `infra/nginx/templates/default.conf.template`, que el entrypoint oficial pasa por `envsubst` (solo `DOMINIO` y `MOVIL_PUERTO_HTTPS_SUFIJO`). `server_tokens off`. Puerto 80: `/.well-known/acme-challenge/` (webroot) y `301` a `https://$host<puerto>$request_uri` para todo lo demás. Puerto 443: `ssl_protocols TLSv1.2 TLSv1.3`, `http2`, `client_max_body_size 5m`, `Strict-Transport-Security: max-age=31536000` y `X-Content-Type-Options: nosniff` (`always`) |
| Ruteo | `location /v1/` → `api:8000` (resuelto por el DNS de Docker cada 10 s, para que un `api` recreado no deje a NGINX con la IP vieja), con `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Forwarded-Host` y `X-Real-IP`. `location = /v1` → `404` (sin esto NGINX redirige `/v1` a `/v1/`, y Caddy daba `404`). `location = /descargas/movil-buscador.apk` (§5). Todo lo demás → `404` |
| Registro | `log_format movil`: IP, fecha, **método y `$uri` sin la cadena de consulta**, estado, bytes, `User-Agent` y tiempo. **Sin** cuerpo, **sin** `Authorization` y **sin** el usuario de la autenticación básica (`$remote_user`). El log de errores queda en nivel `info`, así se ve el rechazo del certificado por parte del cliente (lo necesita el 11.10 del guion; con Caddy había que poner DEBUG en caliente) |
| Arranque | `infra/nginx/18-movil.envsh` (lo ejecuta el entrypoint oficial antes de `envsubst`): calcula el sufijo del puerto HTTPS, elige el certificado activo (`movil-certificado-activo.sh`), genera el `htpasswd` y quita `DESCARGA_APK_CLAVE` del entorno del proceso de NGINX. `infra/nginx/.gitattributes` fija LF para los scripts y el Dockerfile además normaliza CRLF (git en Windows) |
| CA local (`CERT_MODO=local`) | La genera `movil-certificado-activo.sh` al primer arranque en el volumen `proxy-certs` (**fuera del repositorio**): CA ECDSA P-256 de 10 años (`CN=Movil Buscador CA local de desarrollo`) y certificado de `localhost` (SAN `DNS:<DOMINIO>`, `DNS:localhost`, `IP:127.0.0.1`) de 397 días, que se rehace solo si le quedan menos de 30. La llave de la CA no sale del volumen (`0600`). `infra/exportar-ca-local.ps1` copia **solo el certificado** a `C:\Willy\Trabajo\MININTER\ca-local-nginx\` (se niega a escribir dentro del repositorio) y muestra su SHA-256: hoy `14:74:99:F3:D3:97:14:8E:04:E6:7D:9E:7F:0F:58:DD:DB:70:7A:96:AD:25:76:77:FB:23:C4:17:58:88:98:D2` (igual a `openssl x509 -fingerprint -sha256` dentro del contenedor) |
| VPS (`CERT_MODO=letsencrypt`) | `docker-compose.vps.yml`: el `proxy` monta `letsencrypt` y `certbot-webroot` (solo lectura) y suma el servicio **`certbot`** (`certbot/certbot:v5.10.0`, sin puertos, en una red `salida` propia) que corre `certbot renew --webroot` cada 12 h. Mientras no hay certificado de Let's Encrypt, el proxy arranca con uno **provisional autofirmado de 30 días**, para poder responder el desafío por el 80. Cada 6 h el proxy vuelve a elegir el certificado y se recarga (toma el renovado). La primera emisión la hace `desplegar.ps1` |
| Caddy | `infra/Caddyfile` borrado; ningún compose usa `caddy`. Los volúmenes viejos `movil-buscador_caddy-datos` y `_caddy-config` quedan en el Docker de esta PC (sin usar; se pueden borrar con `docker volume rm`) |

## 2. La ruta del APK (§5, v2.1 anotación)

- `location = /descargas/movil-buscador.apk`: `auth_basic` con `/etc/nginx/htpasswd-descarga`, `alias /srv/descargas/movil-buscador.apk`, `autoindex off`, `Content-Type: application/vnd.android.package-archive`, `Content-Disposition: attachment`, `Cache-Control: no-store`, y las dos cabeceras de seguridad repetidas (en NGINX, un `add_header` dentro de un `location` anula los del `server`).
- La carpeta es **`DESCARGA_APK_DIR`** de `infra/.env` (relativa a `infra/` o absoluta), montada de **solo lectura** en `/srv/descargas`. Por defecto `../../movil-buscador-descargas`: en esta PC, `C:\Willy\Trabajo\MININTER\movil-buscador-descargas` (fuera del repositorio; además `.gitignore` agrega `movil-buscador-descargas/`). Se monta la **carpeta**, no el archivo, así un reemplazo atómico del APK se ve sin reiniciar.
- El `htpasswd` lo genera el proxy al arrancar desde `DESCARGA_APK_USUARIO` y `DESCARGA_APK_CLAVE` (`openssl passwd -apr1`, un solo usuario, `root:nginx 0640`, dentro del contenedor y no en un volumen). **Si falta alguna de las dos**, genera uno con una clave al azar que nadie conoce: la ruta responde siempre `401` (cerrada por defecto).
- `infra/.env` local: agregué `DESCARGA_APK_USUARIO=probador`, `DESCARGA_APK_CLAVE` (al azar, 32 caracteres) y `DESCARGA_APK_DIR`. Ese archivo no se versiona.

## 3. Scripts (§6)

- **`scripts/desplegar.ps1`:** construye también la imagen `proxy`; levanta `api`, `simuladores`, `proxy` y `certbot`; **nuevo paso 5**: si no existe `/etc/letsencrypt/live/<DOMINIO>/fullchain.pem`, corre `certbot certonly --webroot -w /var/www/certbot -d <DOMINIO> --agree-tos --non-interactive` (con `CERTBOT_EMAIL` si está en el `.env`, si no `--register-unsafely-without-email`) y recarga NGINX. Después, la salud como antes. Sigue sin copiar secretos y es idempotente.
- **`scripts/publicar-apk.ps1` (nuevo):** `flutter build apk --release --dart-define=API_URL=https://<DOMINIO>` (exige `key.properties`, la llave fuera del repositorio), comprueba con `aapt dump badging` que **no** sea depurable y que sea `pe.prototipo.movilbuscador`, calcula el SHA-256, lo copia por `scp` a un temporal del VPS, comprueba allá el SHA-256, lo instala como `.movil-buscador.apk.nuevo` y lo renombra a `DESCARGA_APK_DIR/movil-buscador.apk` (no corta una descarga en curso) y muestra el SHA-256. No copia la llave ni la credencial. `-SinCompilar` publica el último compilado. Rechaza `localhost` como dominio.
- Los tres `.ps1` (`desplegar`, `publicar-apk`, `exportar-ca-local`) parsean sin errores (`Parser.ParseFile`). `publicar-apk.ps1` y el paso de `certbot` quedan **NO VERIFICADOS** hasta que haya VPS.

## 4. `eas.json`, documentos y `.gitignore`

- **`apps/movil/eas.json` borrado** (lo único que toqué en `apps/movil/`).
- **`docs/despliegue/`:** sin EAS ni Caddy (`git grep -niw eas -- docs/despliegue` vacío).
  - `MANUAL-DESPLIEGUE.md`: arquitectura con NGINX, `certbot` y el APK por descarga; carpeta `/opt/movil-buscador-descargas` en el VPS; las variables nuevas (`CERTBOT_EMAIL`, `DESCARGA_APK_*`); §6.1 (llave de firma, `publicar-apk.ps1`, cómo repartir, **cómo cambiar la credencial si se filtra** y **cómo quitar la ruta**), §6.2 (emisión, renovación, `--dry-run`, qué hacer si falla) y §6.3 (proxy y CA local); logs de NGINX y `certbot`; borrado al cierre con la descarga, la llave de firma, la CA local y los builds de EAS de la etapa Expo.
  - `GUIA-PROBADORES.md`: reescrita con los 10 puntos del §7 (desinstalar la versión anterior, la descarga con su usuario y clave, permitir la instalación en Samsung con Android 16 y en otros Android, abrir, usuarios sin clave, qué probar con la cámara incluida, qué no esperar, el aviso de telemetría, datos ficticios y desinstalar). La sección 8 es el §2 del anexo `docs/hus/anexos/HU-04-aviso-telemetria-mlkit.md` **tal cual** (comprobado por comparación de texto), como pedía la M-2. Queda más larga que 2 páginas por el anexo.
  - `DOMINIO.md`: `certbot` en lugar de Caddy.
- **`README.md`:** proxy NGINX con la CA local, la ruta de descarga y los scripts; app Flutter en lugar de Expo.
- **`.gitignore`** (solo agregar): `*.crt`, `*.cer`, `*.pem`, `*.key`, `*.der`, `*.p12`, `*.pfx`, `*.csr`, `*.srl`, `htpasswd*` y `movil-buscador-descargas/` (`*.apk` y `*.aab` ya estaban). `git ls-files` no muestra ningún archivo con esas extensiones.
- `infra/.env.example`: `DESCARGA_APK_USUARIO`, `DESCARGA_APK_CLAVE`, `DESCARGA_APK_DIR` y, para el VPS, `CERTBOT_EMAIL`.

## 5. Verificación local (M-3 punto 6)

Compose bajado desde `-flutter` (`down`, **sin `-v`**: `datos-bd` y `fotos-galeria` intactos) y levantado desde `-despliegue` con `docker-compose.fotos.yml`, como antes. Los dos `infra/.env` (`-flutter` y `-despliegue`) eran idénticos, así que no copié nada; solo agregué las tres variables de la descarga. `docker compose config` valida el local y el del VPS (servicios del VPS: `api`, `simuladores`, `proxy`, `certbot`).

| Prueba (a mano, con `curl`) | Resultado |
|---|---|
| `https://localhost:8443/v1/salud` | `200` con `"bd":"ok"`, `"simuladores":"ok"`; `Strict-Transport-Security`, `X-Content-Type-Options: nosniff` y el `Cache-Control: no-store` de la API |
| `http://localhost:8080/v1/salud` y `http://…/descargas/movil-buscador.apk` (con credencial) | `301` a `https://localhost:8443/…`, **antes** de pedir la credencial |
| `/`, `/openapi.json`, `/v1` | `404` |
| APK sin credencial / usuario o clave incorrectos | `401`, con `WWW-Authenticate: Basic realm="Movil Buscador"` |
| APK con la credencial (archivo de prueba mío, 300 000 bytes al azar) | `200`, `application/vnd.android.package-archive`, **el mismo SHA-256**. El archivo lo borré después (la carpeta quedó vacía, para el TESTER) |
| `/descargas/`, `/descargas/otro.apk`, `/descargas/movil-buscador.apk/`, `/descargas` (con credencial) | `404` |
| `POST /v1/auth/login` con 5,3 MB / con 4 MB | `413` del proxy / `422` de la API (llegó) |
| TLS 1.0 y 1.1 (`openssl s_client` con `SECLEVEL=0` dentro del contenedor) | el servidor responde `alert protocol version` (70) |
| TLS 1.2 y 1.3 | conectan (`ECDHE-ECDSA-AES256-GCM-SHA384` y `TLS_AES_256_GCM_SHA384`) |
| Logs del proxy después de las descargas | **0** apariciones de la clave, de `Authorization`/`Basic` y del usuario de la descarga |
| Entorno del proceso de NGINX (`/proc/1/environ`) | sin `DESCARGA_APK_CLAVE` (sí sigue en la configuración del contenedor, como toda variable del `.env`) |
| `curl` sin confiar en la CA local | el log de errores registra `[info] … peer closed connection in SSL handshake` |

El APK de depuración de `main` en el teléfono no hacía falta todavía (M-3 punto 6). Avisé al TESTER cuando el compose quedó arriba, y otra vez cuando quedó quieto: mi `up --build proxy` también recreó `api` y `simuladores` y le cortó una corrida (lección: `--no-deps`).

## 6. Preparación de la red de ML Kit (M-3 punto 7), fuera del repositorio

| Herramienta | Versión | Dónde | Licencia | Verificación |
|---|---|---|---|---|
| mitmproxy (binarios para Windows) | **12.3.1** (Python 3.15.1, OpenSSL 4.0.3) | `C:\Programas_Portables\mitmproxy-12.3.1\` (`mitmdump.exe`, `mitmproxy.exe`, `mitmweb.exe`) | MIT | `downloads.mitmproxy.org/12.3.1/mitmproxy-12.3.1-windows-x86_64.zip`, sha256 del zip `336c03e7…48af829` |
| `protoc` | **36.2** (`libprotoc 36.2`) | `C:\Programas_Portables\protoc-36.2\bin\protoc.exe` | BSD-3-Clause | release de GitHub `protoc-36.2-win64.zip`, sha256 `f0c128dc…4edd3` |
| PCAPdroid | **2.0.5** (23-nov-2026) | para el humano: F-Droid <https://f-droid.org/packages/com.emanuelef.remote_capture/> o Google Play <https://play.google.com/store/apps/details?id=com.emanuelef.remote_capture> (no lo descargué ni lo instalé) | GPL-3.0 | — |

**Captura:** `C:\Willy\Trabajo\MININTER\flutter-capturas\red\`. Ahí quedó solo `mitm-conf\` (la configuración de mitmproxy con **su CA**: `CN=mitmproxy`, SHA-256 `95:E3:03:AC:97:9F:FA:7C:A0:CD:D1:FE:91:BF:CD:F6:14:AC:E5:73:AD:05:14:D2:7E:64:C3:61:CA:E7:BD:AC`; `mitmproxy-ca-cert.cer` es la que se instala como CA de usuario en el teléfono). Se borra entera en la limpieza (e).

**Cómo pasa el tráfico del S23 por mitmproxy (para el guion del TESTER):**

```
# PC
C:\Programas_Portables\mitmproxy-12.3.1\mitmdump.exe --listen-port 8090 `
  --set confdir=C:\Willy\Trabajo\MININTER\flutter-capturas\red\mitm-conf --ssl-insecure `
  -w C:\Willy\Trabajo\MININTER\flutter-capturas\red\nivel2.mitm
# Telefono (por USB)
adb reverse tcp:8090 tcp:8090              # el 8090 del telefono llega al mitmproxy de la PC
adb reverse tcp:8443 tcp:8443              # la API local, como siempre
adb shell settings put global http_proxy 127.0.0.1:8090
```

- `--ssl-insecure` hace falta porque, del lado de la PC, mitmproxy habla con `https://localhost:8443` (la CA local de NGINX no está en su almacén). No afecta lo que se le presenta al teléfono.
- **Solo el APK de depuración** confía en la CA de usuario de mitmproxy (`<debug-overrides>`), así que el nivel 2 ve en claro el tráfico **de la app** (incluida la cola de `datatransport` de ML Kit, que corre en el proceso de la app). El tráfico de `com.google.android.gms` (otro proceso, que no confía en CA de usuario) va a fallar el TLS contra mitmproxy: para ese, el nivel 1 con PCAPdroid (dominios y conteos, sin descifrar).
- **Para deshacerlo** (orden): `adb shell settings put global http_proxy :0`, `adb shell settings delete global http_proxy`, `adb reverse --remove tcp:8090`; detener `mitmdump`; quitar la CA de mitmproxy de la CA de usuario del teléfono; borrar `C:\Willy\Trabajo\MININTER\flutter-capturas\red\`. Si el teléfono se queda sin internet, casi siempre es el `http_proxy` que quedó puesto: el primer comando lo arregla.

**Probado sin el teléfono:** `mitmdump` en el 8090 con esa `confdir`; un cliente que confía en la CA de mitmproxy llegó por el proxy a `https://localhost:8443/v1/salud` (`200`) y a `https://firebaselogging.googleapis.com/` (`404` del servidor de Google), y los dos flujos quedaron en la captura y se leyeron con `mitmdump -r`. Un cliente que **no** confía en esa CA no pasa (`curl` rc 60). `protoc --decode_raw` decodifica un mensaje de ejemplo (`1: 150`, `2: "ZZA-101"`). En Windows, `curl` necesita `--ssl-no-revoke` con la CA de mitmproxy (schannel no puede comprobar su revocación); no aplica al teléfono. Borré la captura y los archivos de la prueba. **NO VERIFICADO** con el S23: el `http_proxy` global, que OkHttp y ML Kit lo respeten, y la CA de mitmproxy instalada.

## 7. Avisos para el LEAD

- **`grep -rniw "eas" apps/movil docs/despliegue` (contrato §6) no sale vacío**, por dos cosas que no son mías ni de este ciclo: `apps/movil/node_modules/` (restos de Expo en este worktree, sin versionar e ignorados por git) y `apps/movil/test/repositorio_test.dart:124`, que es una prueba del TESTER que nombra `eas.json` en la lista de archivos de Expo que no deben existir. Con `git grep` (solo lo versionado) sale solo esa línea de la prueba. No toqué ninguna de las dos.
- La imagen del `proxy` es `nginx:1.30.8-alpine` **más `openssl`** (una línea de `apk add`). Si se quiere la imagen oficial sin capas propias, la alternativa es un servicio aparte que prepare certificados y `htpasswd`; no lo creo necesario.
- Volúmenes viejos de Caddy en esta PC (`movil-buscador_caddy-datos`, `_caddy-config`): no los borré (el `down` fue sin `-v`). La CA de Caddy de la migración (`C:\Willy\Trabajo\MININTER\ca-local\` y la CA de usuario del S23) se quita en la sesión 1 (a), según el guion del TESTER.
