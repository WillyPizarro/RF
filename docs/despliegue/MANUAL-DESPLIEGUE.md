# Manual de despliegue — Movil Buscador en un VPS (DESPLIEGUE-01)

Este manual explica cómo dejar la API de Movil Buscador corriendo en un VPS, con la base y Auth en
Supabase, y cómo generar el APK para los probadores.

- **Qué se despliega:** solo datos sintéticos, sin fotos. Ningún secreto va al repositorio: en este documento solo aparecen los **nombres** de las variables.
- **Arquitectura (ADR-0009):**
  - **VPS:** `api`, `simuladores`, `proxy` (**NGINX**) y `certbot`, con docker compose. Solo el `proxy` abre puertos, el 80 y el 443 (ADR-0018).
  - **Supabase en la nube:** Postgres y Auth.
  - **APK para los probadores:** el de release de Flutter, compilado y firmado en **esta PC** (la llave de firma no sale de aquí) y descargado desde `https://<DOMINIO>/descargas/movil-buscador.apk` con un usuario y una clave (§6.1).

Documentos relacionados:

- `DOMINIO.md`: comprar el dominio y crear el registro DNS.
- `LLAVE-SSH.md`: las llaves SSH.
- `GUIA-PROBADORES.md`: la guía que se reparte a los probadores.

---

## 1. Requisitos del VPS

- **Tamaño:** 2 vCPU, 4 GB de RAM y 40 GB de disco o más (US$ 6–12 al mes). La región más cercana a São Paulo o a Lima.
- **Sistema:** **Ubuntu 24.04 LTS**.
- **Acceso:** solo con la llave SSH dedicada (`LLAVE-SSH.md`), **sin clave**.

## 2. Preparar el VPS (una sola vez)

Entre con el usuario que dio el proveedor (normalmente `root`) y la llave de despliegue:

```
ssh -i $HOME\.ssh\movil_vps root@<IP-del-VPS>
```

En el VPS:

1. **Actualizar e instalar lo básico:**

   ```
   apt update && apt -y upgrade
   apt -y install git curl ufw
   ```

2. **Instalar Docker** (motor oficial, con el plugin de compose):

   ```
   curl -fsSL https://get.docker.com | sh
   docker compose version
   ```

3. **Crear el usuario de despliegue** y darle la misma llave:

   ```
   adduser --disabled-password --gecos "" deploy
   usermod -aG docker deploy
   mkdir -p /home/deploy/.ssh
   cp ~/.ssh/authorized_keys /home/deploy/.ssh/
   chown -R deploy:deploy /home/deploy/.ssh && chmod 700 /home/deploy/.ssh && chmod 600 /home/deploy/.ssh/authorized_keys
   ```

4. **SSH solo con llave y sin `root`.** En `/etc/ssh/sshd_config` deje estas líneas:

   ```
   PasswordAuthentication no
   PermitRootLogin no
   ```

   Aplíquelo con `systemctl restart ssh`. **Antes de cerrar la sesión**, abra otra terminal y compruebe que `ssh -i $HOME\.ssh\movil_vps deploy@<IP>` entra.

5. **Firewall: solo 22, 80 y 443.**

   ```
   ufw default deny incoming
   ufw default allow outgoing
   ufw allow 22/tcp
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw enable
   ```

   Docker publica solo los puertos del `proxy` (80 y 443): `api` (8000), `simuladores` (8001) y la base no se publican. Si el proveedor tiene firewall propio, configure las mismas tres reglas allí.

6. **Carpeta del proyecto y deploy key de GitHub** (como `deploy`; ver `LLAVE-SSH.md`, paso 3):

   ```
   sudo mkdir -p /opt/movil-buscador && sudo chown deploy:deploy /opt/movil-buscador
   su - deploy
   git clone git@github.com:<cuenta>/<repositorio>.git /opt/movil-buscador
   ```

7. **Carpeta de la descarga del APK**, fuera del repositorio (la monta el `proxy` de solo lectura; `DESCARGA_APK_DIR`):

   ```
   sudo mkdir -p /opt/movil-buscador-descargas && sudo chown deploy:deploy /opt/movil-buscador-descargas
   ```

## 3. Dominio (DNS)

Siga `DOMINIO.md`. Antes de levantar el `proxy`, el subdominio tiene que resolver a la IP del VPS:
`certbot` necesita eso para obtener el certificado de Let's Encrypt (lo valida por el puerto 80).

## 4. Supabase

1. **Crear el proyecto.** En `supabase.com`, cree un proyecto nuevo.
   - **Región:** South America (São Paulo).
   - **Clave de la base:** guárdela en su gestor de claves; es la del rol `postgres`.
   - **Plan:** el gratuito alcanza para preparar; antes del demo pase a **Pro**, porque el gratuito se pausa tras unos días sin uso y entonces la API responde `503`.
2. **Conexión a la base: Session pooler.** Entre a **Connect › Session pooler**.
   - **Por qué este:** es IPv4 y usa el puerto 5432, y la API (asyncpg) no funciona con el pooler en modo transacción. La conexión directa puede ser solo IPv6.
   - **Qué anotar:** el host (`aws-…pooler.supabase.com`) y la referencia del proyecto (`<ref>`).
3. **Auth.**
   - **Registro abierto:** en **Authentication › Sign In / Providers**, desactive **Allow new users to sign up**. Los usuarios los crea la carga.
   - **Confirmación de correo:** deje **Confirm email** como esté. La carga crea los usuarios ya confirmados.
4. **Claves (Project Settings › API Keys).**
   - **Publishable key** (o `anon`): va en `AUTH_APIKEY`. Es pública.
   - **Secret key** (`sb_secret_…`) o, en proyectos con claves heredadas, `service_role`: es la **credencial de administración**. Solo la usa la carga de usuarios (`AUTH_ADMIN_CLAVE`). **Nunca** va a la API en marcha ni a la app.

## 5. El `.env` del VPS

Créelo en `/opt/movil-buscador/infra/.env`, **fuera de git** (el `.gitignore` lo excluye), con
permisos `600`:

```
nano /opt/movil-buscador/infra/.env
chmod 600 /opt/movil-buscador/infra/.env
```

Variables (solo los **nombres**; los valores los pone el humano):

| Variable | Qué va |
|---|---|
| `DOMINIO` | el subdominio, por ejemplo `api.movil-prototipo.com` |
| `DATABASE_URL` | `postgresql+asyncpg://api_app.<ref>:<API_APP_CLAVE>@<host-pooler>:5432/postgres` |
| `API_APP_CLAVE` | una clave larga nueva para el rol `api_app` (la fija la migración) |
| `MIGRACION_DATABASE_URL` | `postgresql+asyncpg://postgres.<ref>:<clave-de-la-base>@<host-pooler>:5432/postgres` |
| `AUTH_URL` | `https://<ref>.supabase.co/auth/v1` |
| `AUTH_APIKEY` | la publishable key (o `anon`) |
| `JWT_SECRETO` | un secreto nuevo de 32 caracteres o más |
| `CLAVE_USUARIOS_PRUEBA` | la clave de los usuarios sintéticos (8 caracteres o más) |
| `SIM_FOTOS_LLAVE` | llave AES-GCM del simulador (ver `infra/.env.example`) |
| `SESION_INACTIVIDAD_S`, `TOKEN_ACCESO_VIGENCIA_S`, `BLOQUEO_INTENTOS`, `BLOQUEO_DURACION_S`, `FUENTE_TIMEOUT_S`, `PLACA_FORMATO_REGEX`, `PLACA_FORMATO_DESCRIPCION` | como en `infra/.env.example` |
| `AUTH_ADMIN_CLAVE` | **mejor no ponerla aquí**: el despliegue la pide al cargar usuarios y no la guarda |
| `CERTBOT_EMAIL` | (opcional) el correo para los avisos de Let's Encrypt; sin él, `certbot` se registra sin correo |
| `DESCARGA_APK_USUARIO` | el usuario de la descarga del APK, **uno solo para todos los probadores** |
| `DESCARGA_APK_CLAVE` | la clave de la descarga (larga, al azar). Se reparte por **otro canal**, nunca junto con el enlace |
| `DESCARGA_APK_DIR` | `/opt/movil-buscador-descargas` (la carpeta del paso 2.7) |

- **Puertos del proxy:** **no** ponga `PROXY_PUERTO_HTTP` ni `PROXY_PUERTO_HTTPS`. El proxy tiene que publicar 80 y 443.
- **Variables locales:** tampoco van `POSTGRES_*`, `AUTH_DB_CLAVE`, `AUTH_JWT_SECRETO` ni `SIM_FOTOS_ORIGEN`. Son solo para el ambiente local.
- **Generar valores aleatorios en el VPS:** `openssl rand -base64 36` sirve para `API_APP_CLAVE`, `JWT_SECRETO` y `CLAVE_USUARIOS_PRUEBA`.

## 6. Desplegar (y volver a desplegar)

Desde **esta PC**, en la carpeta del repositorio, con la llave cargada (`LLAVE-SSH.md`):

```
$env:MOVIL_VPS = "deploy@<IP-del-VPS>"
$env:MOVIL_VPS_LLAVE = "$HOME\.ssh\movil_vps"
.\scripts\desplegar.ps1 main -CargarUsuarios     # la primera vez
.\scripts\desplegar.ps1 main                     # las siguientes
```

El script entra por SSH y, en el VPS, hace esto:

1. `git fetch` y deja la carpeta en esa rama o commit, desde `origin`.
2. Construye las imágenes.
3. Aplica las migraciones con el servicio `herramientas` (rol dueño). Crea las tablas, el rol `api_app` con su clave y el trigger de solo inserción. No toca el esquema `auth` de Supabase.
4. Con `-CargarUsuarios`: crea o actualiza `agente1`, `agente2`, `revisor1`, `supervisor1` e `inactivo1`, y **pide la credencial de administración** por teclado (no se muestra ni se guarda).
5. `up -d --build` de `api`, `simuladores`, `proxy` y `certbot`.
6. **La primera vez**, pide el certificado de Let's Encrypt con `certbot` (§6.2) y recarga NGINX.
7. Espera hasta que `https://<DOMINIO>/v1/salud` responda `200` (5 minutos como máximo).

No copia ningún secreto: usa el `.env` del VPS. Se puede correr dos veces seguidas, porque las
migraciones y la carga de usuarios son idempotentes.

**A mano en el VPS** (equivalente, como `deploy`, en `/opt/movil-buscador`):

```
C="docker compose -f infra/docker-compose.yml -f infra/docker-compose.vps.yml --env-file infra/.env"
$C --profile herramientas run --rm herramientas python -m app.migrar
read -r -s AUTH_ADMIN_CLAVE && export AUTH_ADMIN_CLAVE
$C --profile herramientas run --rm herramientas python -m app.cargar_usuarios
unset AUTH_ADMIN_CLAVE
$C up -d --build
```

**Nunca** use `infra/docker-compose.fotos.yml` en el VPS.

### 6.1 APK para los probadores (descarga protegida)

**La llave de firma** vive solo en esta PC, fuera del repositorio
(`C:\Users\<usuario>\.movil-buscador-firma\`, con una copia ignorada por git en
`apps/movil/android/key.properties`; informe del DEV de la migración, §4). Sin ella, el APK de
release sale sin firmar y `publicar-apk.ps1` se detiene.

**Publicar** (compila, comprueba y copia al VPS):

```
$env:MOVIL_VPS = "deploy@<IP-del-VPS>"
$env:MOVIL_DOMINIO = "<DOMINIO>"
.\scripts\publicar-apk.ps1
```

El script:

1. corre `flutter build apk --release --dart-define=API_URL=https://<DOMINIO>`;
2. comprueba con `aapt dump badging` que el APK **no** sea depurable y que sea `pe.prototipo.movilbuscador`;
3. lo copia por SSH a `DESCARGA_APK_DIR/movil-buscador.apk` en el VPS (primero a un temporal y después lo renombra, así no corta una descarga en curso) y comprueba allá el mismo SHA-256;
4. muestra el **SHA-256**, para compararlo con el archivo que descargan los probadores.

No copia la llave de firma ni la credencial. Con `-SinCompilar` publica el último APK compilado.

**Repartir:** el enlace `https://<DOMINIO>/descargas/movil-buscador.apk` y `GUIA-PROBADORES.md` por un
canal; el **usuario y la clave de la descarga** por otro; la clave de los usuarios de la app, por un
canal privado aparte.

**Qué contiene el APK:** es de release, así que **no es depurable** y no confía en certificados del
usuario. Llega a la API con el certificado de Let's Encrypt, sin instalar nada en el teléfono.

**Si la credencial de la descarga se filtra:** cambie `DESCARGA_APK_CLAVE` en el `.env` del VPS,
vuelva a desplegar (`.\scripts\desplegar.ps1 main`: el `proxy` se recrea y regenera el `htpasswd`) y
reparta la clave nueva a todos los probadores. La anterior deja de servir en ese momento.

**Quitar la ruta** (al terminar la validación y, a más tardar, en el acta de eliminación): en el VPS,
`rm -f /opt/movil-buscador-descargas/movil-buscador.apk` (la ruta pasa a responder `404`); después
borre `DESCARGA_APK_USUARIO` y `DESCARGA_APK_CLAVE` del `.env` del VPS y vuelva a desplegar (sin
ellas, la ruta responde siempre `401`).

### 6.2 Certificado: NGINX y certbot

- **Emisión:** la primera vez, `desplegar.ps1` corre `certbot certonly --webroot` (modo *webroot*
  por el puerto 80; `certbot` no publica puertos). Mientras no hay certificado, NGINX arranca con
  uno provisional autofirmado de 30 días para poder responder el desafío.
- **Renovación:** el servicio `certbot` corre `certbot renew` cada 12 horas (no hace nada si faltan
  más de 30 días para el vencimiento), y el `proxy` vuelve a cargar el certificado cada 6 horas.
  Prueba en seco: `$C run --rm --entrypoint certbot certbot renew --dry-run`.
- **Si falla:** revise que el registro `A` apunte al VPS (`DOMINIO.md`), que el puerto 80 esté
  abierto (`ufw status`) y que el proxy de Cloudflare esté apagado; mire `$C logs certbot` y
  `$C logs proxy`. Para volver a intentarlo, corra otra vez `.\scripts\desplegar.ps1 main`. Let's
  Encrypt limita los intentos fallidos (5 por hora por dominio): si hay que probar varias veces,
  use primero `--dry-run`.
- **Dónde vive:** en el volumen `letsencrypt` del VPS, **nunca** en el repositorio.

### 6.3 Proxy local y CA local (desarrollo)

En la PC, el mismo `proxy` NGINX genera al primer arranque una **CA local** propia (volumen
`proxy-certs`, fuera del repositorio) y el certificado de `localhost` firmado por ella. Para el
teléfono de pruebas, `.\infra\exportar-ca-local.ps1` copia la CA a
`C:\Willy\Trabajo\MININTER\ca-local-nginx\` y muestra su SHA-256.

Esa CA se instala como **CA de usuario** en el teléfono; solo la confía el APK de **depuración**
(`<debug-overrides>`), nunca el de release. La ruta de descarga en local sirve
`DESCARGA_APK_DIR/movil-buscador.apk` (por defecto `..\..\movil-buscador-descargas`, fuera del
repositorio), con la credencial del `infra/.env` local.

## 7. Comprobar

Desde la PC:

```
curl.exe https://<DOMINIO>/v1/salud              # 200, con "bd":"ok" y "simuladores":"ok"
curl.exe -o NUL -w "%{http_code}" https://<DOMINIO>/openapi.json   # 404
```

En el VPS (como `deploy`):

```
$C ps                                             # api, simuladores, proxy y certbot "healthy"/"running"
$C exec api printenv | cut -d= -f1                # sin AUTH_ADMIN_CLAVE, AUTH_JWT_SECRETO, MIGRACION_DATABASE_URL ni CLAVE_USUARIOS_PRUEBA
```

La comprobación completa (`api_app` en `pg_stat_activity`, trigger, logs sin la clave) es del
TESTER (`informes/TESTER-DESPLIEGUE-01.md`).

## 8. Logs

En el VPS:

```
$C logs --tail 100 api          # API (JSON, con id_traza; nunca claves ni tokens)
$C logs --tail 100 proxy        # NGINX (acceso sin Authorization ni cuerpos; errores en nivel info)
$C logs --tail 100 certbot      # renovaciones del certificado
$C logs -f api                  # en vivo (Ctrl+C para salir)
```

Si `/v1/salud` responde `503`:

- con `"bd":"error"`: revise `DATABASE_URL` y que el proyecto de Supabase no esté **pausado** (plan gratuito);
- con `"simuladores":"error"`: revise `$C logs simuladores`.

## 9. Borrado al cierre del proyecto (acta de eliminación, ADR-0008)

1. **VPS:** elimínelo desde el panel del proveedor, **con sus discos, volúmenes y snapshots o respaldos**.
2. **Supabase:** en **Project Settings › General › Delete project**. Se borran la base, Auth y sus respaldos.
3. **Builds de la etapa Expo:** en `expo.dev`, borre los builds de la etapa anterior (por ejemplo `a3380e39`) o, como mínimo, desactive sus enlaces internos. Si ya no se usa, borre el proyecto.
4. **Descarga del APK:** borre `movil-buscador.apk` y la credencial `DESCARGA_APK_*`, si no se borraron antes (§6.1).
5. **Llave de firma y CA local:** borre la llave de firma del APK de esta PC (`.movil-buscador-firma` y `apps/movil/android/key.properties`) y la CA local del proxy (`docker volume rm movil-buscador_proxy-certs` y `C:\Willy\Trabajo\MININTER\ca-local-nginx\`), y pida que se quite la CA de usuario del teléfono de pruebas.
6. **DNS:** borre el registro `A` del subdominio (`DOMINIO.md`, paso 5).
7. **Llaves SSH:** revoque la deploy key de GitHub y borre la llave de despliegue de la PC (`LLAVE-SSH.md`, paso 4).
8. **Probadores:** pídales que desinstalen la app (`GUIA-PROBADORES.md`, sección 10).
9. **Registro:** anote la fecha de cada paso en el acta de eliminación.
