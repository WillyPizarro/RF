# Manual de despliegue — Movil Buscador en un VPS (DESPLIEGUE-01)

Este manual explica cómo dejar la API de Movil Buscador corriendo en un VPS, con la base y Auth en
Supabase, y cómo generar el APK para los probadores.

- **Qué se despliega:** solo datos sintéticos, sin fotos. Ningún secreto va al repositorio: en este documento solo aparecen los **nombres** de las variables.
- **Arquitectura (ADR-0009):**
  - **VPS:** `api`, `simuladores` y `proxy` (Caddy), con docker compose. Solo el `proxy` abre puertos, el 80 y el 443.
  - **Supabase en la nube:** Postgres y Auth.
  - **EAS:** el APK interno para los probadores.

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

## 3. Dominio (DNS)

Siga `DOMINIO.md`. Antes de levantar el `proxy`, el subdominio tiene que resolver a la IP del VPS:
Caddy necesita eso para obtener el certificado de Let's Encrypt.

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
5. `up -d --build` de `api`, `simuladores` y `proxy`.
6. Espera hasta que `https://<DOMINIO>/v1/salud` responda `200` (5 minutos como máximo).

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

### APK para los probadores (perfil `preview`)

1. **Dominio en el perfil.** En `apps/movil/eas.json`, perfil `preview`, cambie el marcador `https://DOMINIO-PENDIENTE.invalid` por `https://<DOMINIO>` y haga commit. Es una URL pública, no un secreto.
2. **Generar el APK.** En `apps/movil/`, con la cuenta `willypizarros-team`:

   ```
   ! npx eas-cli@27.11.0 login
   npx eas-cli@27.11.0 init                     # solo si app.json no tiene extra.eas.projectId
   npx eas-cli@27.11.0 build --profile preview --platform android
   ```

   - **La primera vez, sin `--non-interactive`:** EAS pregunta si genera la llave de firma de Android; responda que sí. EAS la guarda en su servidor, y el repositorio no la tiene.
   - **Las siguientes:** `npx eas-cli@27.11.0 build --profile preview --platform android --non-interactive`.
3. **Repartir.** EAS da un **enlace interno**, que se reparte a los probadores junto con `GUIA-PROBADORES.md`. La clave de los usuarios va por un canal privado aparte.
4. **Qué contiene el APK:** es de release, así que **no es depurable** y no confía en certificados del usuario. Llega a la API con el certificado de Let's Encrypt, sin instalar nada en el teléfono.

## 7. Comprobar

Desde la PC:

```
curl.exe https://<DOMINIO>/v1/salud              # 200, con "bd":"ok" y "simuladores":"ok"
curl.exe -o NUL -w "%{http_code}" https://<DOMINIO>/openapi.json   # 404
```

En el VPS (como `deploy`):

```
$C ps                                             # api, simuladores y proxy "healthy"/"running"
$C exec api printenv | cut -d= -f1                # sin AUTH_ADMIN_CLAVE, AUTH_JWT_SECRETO, MIGRACION_DATABASE_URL ni CLAVE_USUARIOS_PRUEBA
```

La comprobación completa (`api_app` en `pg_stat_activity`, trigger, logs sin la clave) es del
TESTER (`informes/TESTER-DESPLIEGUE-01.md`).

## 8. Logs

En el VPS:

```
$C logs --tail 100 api          # API (JSON, con id_traza; nunca claves ni tokens)
$C logs --tail 100 proxy        # Caddy
$C logs -f api                  # en vivo (Ctrl+C para salir)
```

Si `/v1/salud` responde `503`:

- con `"bd":"error"`: revise `DATABASE_URL` y que el proyecto de Supabase no esté **pausado** (plan gratuito);
- con `"simuladores":"error"`: revise `$C logs simuladores`.

## 9. Borrado al cierre del proyecto (acta de eliminación, ADR-0008)

1. **VPS:** elimínelo desde el panel del proveedor, **con sus discos, volúmenes y snapshots o respaldos**.
2. **Supabase:** en **Project Settings › General › Delete project**. Se borran la base, Auth y sus respaldos.
3. **EAS:** en `expo.dev`, en el proyecto, borre los builds (o como mínimo desactive los enlaces internos). Si ya no se usa, borre el proyecto.
4. **DNS:** borre el registro `A` del subdominio (`DOMINIO.md`, paso 5).
5. **Llaves:** revoque la deploy key de GitHub y borre la llave de despliegue de la PC (`LLAVE-SSH.md`, paso 4).
6. **Probadores:** pídales que desinstalen la app (`GUIA-PROBADORES.md`, paso 5).
7. **Registro:** anote la fecha de cada paso en el acta de eliminación.
