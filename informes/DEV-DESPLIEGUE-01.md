# Informe DEV — DESPLIEGUE-01, fase A (sin VPS)

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
