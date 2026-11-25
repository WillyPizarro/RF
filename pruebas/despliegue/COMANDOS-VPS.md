# Comandos para correr DENTRO del VPS — DESPLIEGUE-01 (fase B)

**Contrato:** `docs/contratos/CONTRATO-DESPLIEGUE-01.md` **v2.1** (§2, §3, §4 y §5; proxy NGINX y `certbot`). **Quién:** quien tenga el SSH con la llave dedicada (el humano, o el TESTER o el DEV si el humano los autoriza).
**Estos comandos no se corrieron todavía:** no hay VPS hasta la fase B2.

Lo que se ve desde afuera (puertos, certificado, `/v1/salud`, el flujo del demo y el 403) lo cubre `services/api/tests/test_despliegue_vps.py`, que se corre desde la PC con `URL_VPS`.

## Reglas al correrlos

- **Ningún comando imprime un secreto.** Las URL de la base y la clave se leen del `.env` dentro de una variable de la sesión y nunca se muestran. No pegar la salida de `cat infra/.env` en ningún lado.
- **Operaciones destructivas:** van siempre dentro de una transacción con `ROLLBACK`. Aunque el trigger faltara, no se borra nada.
- **Resultados:** se anotan en `informes/TESTER-DESPLIEGUE-01.md`, sin valores secretos.

## 0. Entrar y preparar

```bash
ssh -i ~/.ssh/movil_vps deploy@<IP o DOMINIO>
cd /opt/movil-buscador
C="docker compose -f infra/docker-compose.yml -f infra/docker-compose.vps.yml --env-file infra/.env"

# psql contra Supabase sin mostrar la URL: la lee del .env y se la pasa a un contenedor efímero.
psql_con() {   # $1 = nombre de la variable del .env (MIGRACION_DATABASE_URL o DATABASE_URL)
  local url; url=$(grep -E "^$1=" infra/.env | cut -d= -f2- | sed 's/+asyncpg//')
  docker run --rm -i -e PGURL="$url" postgres:17 sh -c 'psql "$PGURL" -v ON_ERROR_STOP=1 -At'
}
```

## 1. El `.env` del VPS (§4 "Secretos fuera del repositorio")

| Comando | Esperado |
|---|---|
| `stat -c '%a %U' infra/.env` | `600 deploy` |
| `git status --porcelain --ignored infra/.env` | `!! infra/.env` (ignorado por git) |
| `git ls-files \| grep -E '\.env$\|\.(crt\|pem\|key\|der)$'` | Ninguna salida |

## 2. La API en marcha no tiene credenciales de administración (§3, decisión 1)

| Comando | Esperado |
|---|---|
| `$C ps --services --status running` | `api`, `proxy`, `simuladores` (sin `db`, `auth` ni `herramientas`) |
| `$C exec -T api printenv \| cut -d= -f1 \| grep -E '^(AUTH_ADMIN_CLAVE\|AUTH_JWT_SECRETO\|MIGRACION_DATABASE_URL\|API_APP_CLAVE\|CLAVE_USUARIOS_PRUEBA)$'` | Ninguna salida |
| `$C exec -T api printenv \| grep -ciE 'service_role\|sb_secret_'` | `0` |
| `grep -E '^DATABASE_URL=' infra/.env \| sed -E 's#^[^:]+://([^:@]+).*#\1#'` | El usuario de la API: `api_app` (en el *Session pooler* de Supabase, `api_app.<ref del proyecto>`). **Nunca** `postgres` ni `service_role` |

## 3. La API se conecta como `api_app` (§3, obligatorio)

Primero, generar tráfico: un login y una consulta desde el APK, o correr `test_despliegue_vps.py`.

```bash
echo "select usename, count(*) from pg_stat_activity where datname = current_database() group by usename order by 1;" | psql_con MIGRACION_DATABASE_URL
```

**Esperado:** aparece `api_app` con al menos una conexión. Las conexiones de la API **no** aparecen como `postgres` ni como `service_role`. Supabase tiene sus propias conexiones internas (`supabase_admin`, `authenticator` y otras): se anotan, pero no son de la API.

## 4. Solo inserción en la nube (§3, CONTRATO-HU-07 §1)

```bash
# Como dueño (rol de las migraciones): el trigger rechaza las tres operaciones.
for op in "update bitacora set motivo = 'x' where id = (select id from bitacora limit 1)" \
          "delete from bitacora where id = (select id from bitacora limit 1)" \
          "truncate bitacora"; do
  printf 'begin;\n%s;\nrollback;\n' "$op" | psql_con MIGRACION_DATABASE_URL 2>&1 | tail -1
done

# Como api_app (la URL de la API): sin permiso para las tres.
for op in "update bitacora set motivo = 'x' where id = (select id from bitacora limit 1)" \
          "delete from bitacora where id = (select id from bitacora limit 1)" \
          "truncate bitacora"; do
  printf 'begin;\n%s;\nrollback;\n' "$op" | psql_con DATABASE_URL 2>&1 | tail -1
done

# Permisos de api_app y cantidad de registros (no debe bajar).
echo "select has_table_privilege('api_app','bitacora','INSERT'), has_table_privilege('api_app','bitacora','SELECT'), has_table_privilege('api_app','bitacora','UPDATE'), has_table_privilege('api_app','bitacora','DELETE'), has_table_privilege('api_app','bitacora','TRUNCATE'), (select count(*) from bitacora);" | psql_con MIGRACION_DATABASE_URL
```

**Esperado:**
- **Como dueño:** las tres terminan en un `ERROR` que contiene `bitacora es de solo insercion`.
- **Como `api_app`:** las tres terminan en `ERROR: permission denied` (`permiso denegado`).
- **Permisos y registros:** `t|t|f|f|f|<n>`, y `<n>` no baja entre una corrida y la siguiente.

## 5. La clave no queda en los logs (§4, obligatorio)

Hacer antes un login desde el APK. La clave se toma del `.env` del VPS y no se muestra.

```bash
CL=$(grep -E '^CLAVE_USUARIOS_PRUEBA=' infra/.env | cut -d= -f2-)
$C logs --no-color proxy 2>&1 | grep -cF -- "$CL"   # → 0
$C logs --no-color api   2>&1 | grep -cF -- "$CL"   # → 0
unset CL
```

**Esperado:** `0` y `0`.

## 6. Usuarios cargados e idempotencia (§3 "Usuarios", §6 "Idempotente")

```bash
$C --profile herramientas run --rm herramientas python -m app.cargar_usuarios   # dos veces seguidas
```

**Esperado:**
- **Las dos corridas** terminan sin error y la salida **no** muestra la clave.
- **En la base:** `echo "select count(*) from auth.users where email like '%agente1%';" | psql_con MIGRACION_DATABASE_URL` → `1` (sin duplicados).
- **En el login:** el flujo de `test_despliegue_vps.py` sigue en verde.

## 7. Puertos escuchando en el VPS (§1, complemento de la prueba desde afuera)

| Comando | Esperado |
|---|---|
| `sudo ss -tlnp \| awk 'NR>1 {print $4}' \| sort -u` | Hacia afuera, solo `:22`, `:80` y `:443` (más lo que escuche solo en `127.0.0.1`) |
| `$C ps --format '{{.Service}} {{.Ports}}'` | Solo `proxy` con `0.0.0.0:80` y `0.0.0.0:443`; `certbot` sin puertos |
| `$C exec proxy nginx -v` | `nginx version: nginx/<x.y.z>`, la **misma** versión fijada en el compose del VPS (`image: nginx:<x.y.z>` o el `FROM nginx:<x.y.z>` del `Dockerfile`; M-4) |

## 8. El APK de release no es depurable (§5, v2) — en la PC, sobre el APK descargado de la ruta

Lo hace también `test_despliegue_vps.py::test_apk_descargado_no_es_depurable` (con `DESCARGA_APK_USUARIO`, `DESCARGA_APK_CLAVE` y el `aapt` de `C:\Android\build-tools`). A mano, con el APK descargado de `https://<DOMINIO>/descargas/movil-buscador.apk` en una carpeta **fuera del repositorio**:

```powershell
$aapt = (Get-ChildItem C:\Android\build-tools\*\aapt.exe | Sort-Object FullName | Select-Object -Last 1).FullName
& $aapt dump badging <APK descargado> | Select-String "package:|application-label:|debuggable"
& $aapt dump xmltree <APK descargado> AndroidManifest.xml | Select-String "allowBackup|usesCleartextTraffic|networkSecurityConfig"
(Get-FileHash -Algorithm SHA256 <APK descargado>).Hash.ToLower()
```

**Esperado:**
- **`dump badging`:** `package: name='pe.prototipo.movilbuscador'`, `application-label:'Movil Buscador'` y **ninguna** línea `application-debuggable`.
- **El manifiesto:** `allowBackup` y `usesCleartextTraffic` en `0x0`; `networkSecurityConfig` presente (sus `debug-overrides` no se aplican en un APK no depurable).
- **El SHA-256:** el mismo que mostró `scripts/publicar-apk.ps1`.
- **El archivo:** queda **fuera del repositorio** y se borra al terminar.

## 9. Renovación del certificado en seco (§2, v2; "Qué prueba quién")

```bash
$C run --rm certbot renew --dry-run    # o el comando que indique el manual del DEV para el servicio certbot
```

**Esperado:** termina con "Congratulations, all simulated renewals succeeded" (o equivalente, sin errores), y no cambia el certificado en uso.

## 10. La credencial de la descarga no queda en los logs (§5, v2)

Hacer antes una descarga con la credencial desde la PC o el teléfono. La clave se toma del `.env` del VPS y no se muestra.

```bash
DU=$(grep -E '^DESCARGA_APK_USUARIO=' infra/.env | cut -d= -f2-)
DC=$(grep -E '^DESCARGA_APK_CLAVE=' infra/.env | cut -d= -f2-)
B64=$(printf '%s:%s' "$DU" "$DC" | base64 -w0)
$C logs --no-color proxy 2>&1 | grep -cF -- "$DC"              # → 0
$C logs --no-color proxy 2>&1 | grep -cF -- "$B64"             # → 0
$C logs --no-color proxy 2>&1 | grep -ciE 'authorization[:=]'  # → 0
unset DU DC B64
```

**Esperado:** `0`, `0` y `0`.

## 11. El `htpasswd` y el APK no están en el repositorio (§5, v2)

| Comando | Esperado |
|---|---|
| `git ls-files \| grep -iE '\.(apk\|aab)$\|htpasswd'` | Sin salida |
| `git check-ignore -v <ruta del APK en el volumen>` (si el volumen está dentro de la carpeta del repositorio) | La regla de `.gitignore` que lo excluye |
