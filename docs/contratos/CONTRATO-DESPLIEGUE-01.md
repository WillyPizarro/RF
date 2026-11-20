# CONTRATO — DESPLIEGUE-01 Despliegue temprano en el VPS y APK para probadores

**Tipo:** Feature (despliegue)
**Versión:** v1
**Estado:** Aprobado (2026-11-19, humano vía PM)
**Origen:** encargo PM → LEAD (2026-11-19, decisión del humano): el MININTER y el equipo prueban desde **sus** celulares en el demo del **jueves 10-dic**. Va en paralelo a HU-04 y no la frena.
**Alcance:** lo que hoy está en `main` (`fa75945`, Iteración 1: HU-08, HU-01, HU-02, HU-03 y HU-07). HU-04 y las siguientes se suben después con el mismo comando (§6).
**Rama de trabajo:** `despliegue-01`, desde `main` `fa75945`, en un worktree aparte (`C:\Willy\Trabajo\MININTER\Movil_Buscador-despliegue`) para no pisar `hu-04`
**Plazo:** el humano contrata el VPS, el dominio y Supabase a más tardar el **miércoles 2-dic**. La ventana de despliegue es del **3 al 7-dic**. Desplegado, y probado por el humano desde su S23 Ultra **por enlace (no por cable)**, antes del **8-dic**.

---

## Paquete de contexto

| Fuente | Por qué entra |
|---|---|
| ADR-0009 | VPS pequeño con docker compose (`api`, `simuladores`, `proxy` con HTTPS automático, que es el único con puertos: 80 y 443); Supabase en la nube (Auth y Postgres, referencia São Paulo); APK interno de EAS; secretos solo en variables del VPS |
| ADR-0005 y CONTRATO-HU-07 v4 | La API se conecta como `api_app` (solo `INSERT` y `SELECT` en `bitacora`, más el trigger), **nunca** con `service_role` |
| ADR-0012 y CONTRATO-HU-07 v2 | Alembic con SQL explícito, portable a cualquier Postgres; migración con `MIGRACION_DATABASE_URL` (rol dueño) |
| ADR-0003 y CONTRATO-HU-01 v5 | Supabase Auth; carga de los usuarios sintéticos fijos con `python -m app.cargar_usuarios`; la clave solo en `CLAVE_USUARIOS_PRUEBA` |
| ADR-0006 y CONTRATO-HU-08 v4 | `simuladores` solo en la red interna; datos sintéticos `ZZ` / `SIM-` |
| ADR-0008 | Al cierre se borra todo el ambiente y se firma un acta de eliminación; sin fotos de rostro hasta HU-05 |
| ADR-0010 | Solo en línea; Android primero; iOS no se distribuye |
| ADR-0002 | Expo con EAS; la app no se publica en las tiendas |
| `docs/contratos/PENDIENTES.md` › Despliegue | Dos tareas **obligatorias**: `api_app` en el Supabase de la nube, y que la clave no quede en los logs del proxy del VPS |
| CONTRATO-HU-01 §5, CONTRATO-HU-04 v3 §8 | La clave no aparece en logs; el build de release no confía en certificados del usuario |
| `infra/` (Caddyfile, compose, `.env.example`), `apps/movil/eas.json` | Lo que ya existe y se reutiliza |

## Interfaz observable

1. **URL pública** `https://<DOMINIO>` (pregunta 2), servida por Caddy con un certificado de Let's Encrypt. Expone solo `/v1/*`.
2. **El VPS:** puertos abiertos hacia internet y contenedores en marcha.
3. **El APK** del perfil EAS `preview`, distribuido por un enlace interno de EAS de la cuenta `willypizarros-team`.
4. **Documentos:** la guía para probadores y el manual de despliegue.
5. **Comandos de despliegue** (§6).

## Comportamiento

### 1. Servicios en el VPS

| Caso | Salida esperada | Origen |
|---|---|---|
| Servicios | En el VPS corren `api`, `simuladores` y `proxy` con el mismo `infra/docker-compose.yml`, más un archivo para el VPS (por ejemplo `infra/docker-compose.vps.yml`) que **quita** `db` y `auth`, porque esos los da Supabase en la nube. **No** se usa `docker-compose.fotos.yml` | ADR-0009 §1 y §2, ADR-0008 |
| Puertos | Desde internet solo responden **22** (SSH, solo con llave), **80** y **443**. `8000`, `8001` y `5432` no responden | ADR-0009 §1, ADR-0006 |
| Salud | `GET https://<DOMINIO>/v1/salud` → `200` con `"bd":"ok"` y `"simuladores":"ok"` | CONTRATO-HU-08 §8, Sprint 0 |
| Solo `/v1/*` | `GET https://<DOMINIO>/openapi.json` y `GET https://<DOMINIO>/` → `404` | Caddyfile (Sprint 0 M-1 G) |
| Mismo comportamiento | Los contratos vigentes en `main` se cumplen igual en el VPS: HU-08 v4, HU-01 v5, HU-02 v3, HU-03 v4 y HU-07 v4 | ADR-0009 ("lo que se entrega es lo que se probó") |

### 2. HTTPS con certificado público

| Caso | Salida esperada | Origen |
|---|---|---|
| Certificado | El certificado de `<DOMINIO>` lo emite **Let's Encrypt**, a través de Caddy, y se renueva solo. Con `DOMINIO=<dominio real>` en el VPS, Caddy lo obtiene sin pasos manuales | ADR-0009 §1, encargo |
| Android lo acepta | El APK de `preview` llega a la API **sin instalar ningún certificado** en el teléfono. No usa `debug-overrides` ni certificados del usuario | Encargo, CONTRATO-HU-04 v3 §8 |
| Verificación desde afuera | Un cliente con las CA del sistema (por ejemplo, `python` con `ssl.create_default_context()` desde esta PC) conecta a `https://<DOMINIO>/v1/salud` sin desactivar la verificación | Encargo |

### 3. Base de datos y Auth en Supabase (obligatorio, `PENDIENTES.md`)

| Caso | Salida esperada | Origen |
|---|---|---|
| Migraciones | Las migraciones de Alembic corren contra el Postgres de Supabase con `MIGRACION_DATABASE_URL` (rol dueño): dejan `bitacora`, `consulta` y los demás objetos, el rol `api_app` con solo `INSERT` y `SELECT` sobre `bitacora`, y el trigger de solo inserción. El esquema `auth` de Supabase no se toca | ADR-0012, CONTRATO-HU-07 v2 §1 |
| La API usa `api_app` | En `pg_stat_activity`, las conexiones de la API usan `usename = api_app`. **Nunca** `service_role` ni `postgres` | ADR-0005, `PENDIENTES.md` (obligatorio) |
| Solo inserción en la nube | Como `api_app` y como dueño, `UPDATE`, `DELETE` y `TRUNCATE` sobre `bitacora` fallan (mensaje del trigger: `bitacora es de solo insercion`) | CONTRATO-HU-07 §1 |
| Auth | La API usa Supabase Auth del proyecto (`AUTH_URL=https://<proyecto>.supabase.co/auth/v1`, `AUTH_APIKEY` con la clave pública) | ADR-0003, `.env.example` |
| Usuarios | `python -m app.cargar_usuarios` deja en Supabase Auth a `agente1`, `agente2`, `revisor1`, `supervisor1` e `inactivo1`, con la clave de `CLAVE_USUARIOS_PRUEBA` del VPS | CONTRATO-HU-01 §6 |
| Credencial de administración solo para la carga | La credencial de administración de Auth que necesita `cargar_usuarios` se pasa **solo a ese comando**, al correrlo. El contenedor `api` en marcha no la tiene: `docker compose exec api printenv` no muestra ningún secreto de administración ni de `service_role` | ADR-0005 (mínimo privilegio) · DECISIÓN PROPUESTA 1 |

### 4. Secretos y datos

| Caso | Salida esperada | Origen |
|---|---|---|
| Secretos fuera del repositorio | Los secretos viven solo en el `.env` del VPS (fuera del repositorio, con permisos `600`) y en las variables de entorno de EAS si hicieran falta. Son: `DATABASE_URL`, `API_APP_CLAVE`, `MIGRACION_DATABASE_URL`, `AUTH_APIKEY`, la credencial de administración de Auth, `JWT_SECRETO`, `CLAVE_USUARIOS_PRUEBA` y `SIM_FOTOS_LLAVE`. `git ls-files` y `git log -p` de la rama no muestran ninguno | ADR-0009 §5, regla 8 |
| La clave no queda en los logs del proxy del VPS | Después de un login desde el APK, `docker compose logs proxy` y los logs de `api` en el VPS no contienen la clave | `PENDIENTES.md` (obligatorio), CONTRATO-HU-01 §5 |
| Solo datos sintéticos | Simuladores con la semilla sintética (`ZZ`, `SIM-`), sin fotos de rostro (no se monta ningún origen de fotos) hasta HU-05. Ningún dato real de ciudadanos | ADR-0008, regla 8, encargo |
| Sin datos en el teléfono | El APK guarda solo el token en SecureStore, como en HU-01 | ADR-0013 |

### 5. APK para probadores (perfil `preview`)

| Caso | Salida esperada | Origen |
|---|---|---|
| Perfil | `apps/movil/eas.json` tiene un perfil `preview`: APK, `distribution: internal`, **sin** `developmentClient`, con el JS embebido y `EXPO_PUBLIC_API_URL=https://<DOMINIO>` (no es un secreto) | Encargo, ADR-0009 §4 |
| No es de depuración | El APK de `preview` no es depurable y no incluye `debug-overrides` en efecto ni confía en certificados del usuario. Se comprueba con `aapt dump badging` o `apkanalyzer` sobre el APK (no hay `application-debuggable`) | CONTRATO-HU-04 v3 §8, encargo |
| Distribución | Un **enlace interno de EAS** (cuenta `willypizarros-team`) que el humano reparte. No se publica en ninguna tienda | ADR-0009 §4 |
| Funciona sin cable | En el S23 Ultra, instalado desde el enlace y sin USB ni Metro: login con `agente1`, `ZZA-101` con motivo → "TIENE REQUISITORIA", `ZZB-201` → sin requisitoria, `ZZZ-999` → placa no registrada; `supervisor1` → BIT-01 con esas consultas | Encargo (prueba del humano) |

### 6. Volver a desplegar con un comando

| Caso | Salida esperada | Origen |
|---|---|---|
| Servidor | Un comando desde esta PC (por ejemplo `scripts/desplegar.ps1 <rama o commit>`) entra al VPS por SSH, trae el código, reconstruye y reinicia `api`, `simuladores` y `proxy`, y aplica las migraciones. Al terminar, `GET /v1/salud` responde `200`. **No copia ningún secreto**: usa el `.env` que ya está en el VPS | Encargo |
| App | Un comando, `npx eas-cli@27.11.0 build --profile preview --platform android --non-interactive`, genera un APK nuevo con el mismo enlace interno o uno nuevo. Queda documentado en el manual | Encargo |
| Idempotente | Correr el despliegue dos veces seguidas no rompe nada ni duplica usuarios | CONTRATO-HU-01 §6 (carga idempotente) |

### 7. Documentos

| Documento | Contenido | Origen |
|---|---|---|
| **Guía corta para probadores** (español simple, 1 o 2 páginas) | 1. Abrir el enlace en el celular Android. 2. Permitir la instalación desde esa fuente (Samsung con Android 16, y una nota genérica para otros Android). 3. Abrir "Movil Buscador". 4. Los usuarios de prueba (`agente1`, `revisor1`, `supervisor1`), **sin la clave**: "la clave se la da el responsable del demo". 5. Qué probar: las placas `ZZA-101`, `ZZB-201` y `ZZZ-999` con un motivo, y la bitácora con `supervisor1`. 6. Qué **no** esperar todavía: rostro (HU-05) y cámara (HU-04, hasta el siguiente despliegue). 7. Que todos los datos son ficticios. 8. Cómo desinstalar la app | Encargo |
| **Pasos para el dominio** (español simple) | Cómo comprar el dominio (junto con el VPS) y cómo crear el registro DNS `A` del subdominio hacia la IP del VPS. Lo hace el humano | Respuesta 2 del humano |
| **Manual de despliegue** | Requisitos del VPS, DNS, `.env` del VPS (solo los nombres de las variables), cómo crear el proyecto de Supabase, cómo migrar y cargar usuarios, los comandos del §6, cómo ver logs y cómo borrar todo (§8) | ADR-0009 §3 (base del manual de entrega) |

### 8. Borrado al cierre (acta de eliminación)

Se agrega a `PENDIENTES.md` y al acta de eliminación (ADR-0008):
- borrar el VPS, con sus discos y snapshots;
- borrar el proyecto de Supabase, con sus respaldos;
- borrar los builds y el proyecto de EAS, o como mínimo los enlaces internos;
- borrar el registro DNS del subdominio;
- pedir a los probadores que desinstalen la app.

## Nombres que no se negocian

| Tipo | Valor exacto |
|---|---|
| URL | `https://<DOMINIO>/v1/*` (el dominio lo da el humano) |
| Perfil EAS | `preview` (cuenta `willypizarros-team`) |
| Servicios en el VPS | `api`, `simuladores`, `proxy` (sin `db` ni `auth`) |
| Rol de la API | `api_app` |
| Variables | Las de `infra/.env.example` (más la credencial de administración de Auth solo para la carga, nombre a elegir por el DEV y documentado) |
| Usuarios | `agente1` · `agente2` · `revisor1` · `supervisor1` · `inactivo1` |
| Placas del demo | `ZZA-101` · `ZZB-201` · `ZZZ-999` |

## Qué prueba quién y dónde

| Parte | Quién | Dónde |
|---|---|---|
| Puertos, certificado, `/v1/salud`, `404` fuera de `/v1/*` | TESTER | Desde esta PC contra `https://<DOMINIO>`. Prueba nueva en `services/api/tests/`, que se omite si no está `URL_VPS` |
| Flujo de API: login, consulta de las 3 placas, bitácora del supervisor, `403` por rol | TESTER | Desde esta PC contra el VPS, con `CLAVE_USUARIOS_PRUEBA` leída del entorno local y nunca escrita |
| `api_app` en `pg_stat_activity`, trigger, `printenv` sin secretos de administración, la clave fuera de los logs del proxy | TESTER, si tiene SSH (pregunta 5); si no, el DEV o el humano con los comandos que deja el TESTER | En el VPS |
| APK no depurable | TESTER | Sobre el APK descargado del enlace |
| Instalación por enlace y el paso a paso en el S23 Ultra, sin cable | **Humano** | Su teléfono |
| Regresión | TESTER | Las suites de siempre en local (`main` no cambia de comportamiento) |

## Rutas de cada rol

| Rol | Rutas | Origen |
|---|---|---|
| DEV | `infra/` (archivo de compose del VPS), `scripts/` (comando de despliegue), `apps/movil/eas.json` y `app.json`, `services/api/` (si `cargar_usuarios` necesita aceptar la credencial de administración de Supabase en la nube), `README.md` raíz, `informes/DEV-*.md` | AGENTS.md |
| DEV | `docs/despliegue/` (guía para probadores y manual de despliegue) | **DECISIÓN PROPUESTA 2**: `AGENTS.md` no le asigna dueño a esta carpeta. Si se aprueba, el LEAD la agrega a `AGENTS.md` |
| TESTER | `services/api/tests/` (pruebas contra el VPS), `pruebas/`, `informes/TESTER-*.md` | AGENTS.md |

## Avisos de contexto

- **Supabase y `asyncpg`:** la conexión directa de Supabase puede ser solo IPv6, y el pooler en modo transacción no admite sentencias preparadas. Conviene usar el *Session pooler* (IPv4, puerto 5432) para `DATABASE_URL` y `MIGRACION_DATABASE_URL`. Es un detalle de configuración del DEV, documentado en el manual.
- **Llaves de Supabase:** los proyectos nuevos de Supabase pueden firmar con llaves asimétricas y usar "secret keys" en lugar del JWT secret heredado. `cargar_usuarios` hoy arma un token de `service_role` con `AUTH_JWT_SECRETO`. Si el proyecto no tiene el secreto heredado, el DEV adapta solo la carga, sin tocar el login (decisión 1).
- **Plan gratuito de Supabase:** se pausa tras unos días sin uso (ADR-0009). Si el demo cae después de una pausa, la API falla con `503`. Va a la pregunta 3.
- **Enlace de EAS:** quien tenga el enlace puede descargar el APK. El APK no tiene secretos: sin usuario y clave no se entra.
- **Usuarios compartidos:** si varios probadores usan `agente1`, el bloqueo (5 fallos) y la bitácora se comparten. Va a la pregunta 4.
- **Contradicción con algún ADR:** con las respuestas de abajo no se ve ninguna. Si el humano elige otro proveedor de base de datos o de Auth, o distribuir fuera de EAS, eso reabre el ADR-0009 y **pasa por el ARCH**.

## Decisiones propuestas (no venían en la tarea)

| # | Decisión | Por qué hace falta | Estado |
|---|---|---|---|
| 1 | La credencial de administración de Auth se pasa solo a `cargar_usuarios` al correrlo; la API en marcha no la tiene | Hoy `AUTH_JWT_SECRETO` vive en el entorno de `api` y permite firmar un token `service_role`. En la nube eso daría a la API en marcha más privilegio que el necesario | Aprobada por el humano (vía PM, 2026-11-19) |
| 2 | La guía y el manual van en `docs/despliegue/`, a cargo del DEV | Nadie es dueño de esa carpeta en `AGENTS.md` | Aprobada por el humano (vía PM, 2026-11-19) |
| 3 | El VPS se configura con `DOMINIO` real y los puertos por defecto (80 y 443); solo SSH con llave, sin clave | ADR-0009 y lo mínimo de seguridad para un servidor en internet | Aprobada por el humano (vía PM, 2026-11-19) |
| 4 | El despliegue del servidor se hace desde esta PC por SSH con `scripts/desplegar.ps1`, y el código llega al VPS desde `origin` (GitHub), no copiando archivos sueltos | Repetible y sin secretos en tránsito | Aprobada por el humano (vía PM, 2026-11-19) |

## Fuera del contrato (decide el DEV)

- El sistema operativo del VPS, el firewall concreto (ufw o el del proveedor) y cómo se instala Docker.
- Si el script es PowerShell o bash, y cómo entra el VPS al repositorio privado (por ejemplo, una *deploy key* de solo lectura, que nunca se versiona).
- El nombre de la variable de la credencial de administración.

## Preguntas abiertas para el humano

Respuestas del humano (vía PM, 2026-11-19):

1. **VPS (y 3, Supabase):** los contrata el humano a más tardar el **miércoles 2-dic**. Él elige el proveedor del VPS (2 vCPU y 4 GB, US$ 6–12 al mes). Supabase arranca en el plan **gratuito** y pasa a **Pro** la semana del demo. La ventana de despliegue es del **3 al 7-dic**.
2. **Dominio:** no tiene. Lo compra junto con el VPS. El DEV deja en `docs/despliegue/` los pasos en español simple para comprarlo y crear el registro DNS `A` del subdominio; los hace el humano.
4. **Probadores:** los **usuarios actuales** para el 10-dic. El humano reparte la clave por un canal privado. La lista de probadores la define antes del 8-dic (**pendiente**).
5. **Acceso al VPS:** por **SSH con una llave dedicada** que autoriza el humano. Nunca se versiona y se revoca al cierre.
6. **Decisiones 1 a 4:** aprobadas tal cual. `docs/despliegue/` pasa a `AGENTS.md` como ruta del DEV.

**Lo que no necesita el VPS avanza ya**, sin bloquear HU-04: el perfil `preview`, `scripts/desplegar.ps1`, el compose del VPS, la guía y los documentos, y las verificaciones en local.

## Changelog

| Versión | Fecha | Cambio | Motivo | Aprobado por |
|---|---|---|---|---|
| v1 | 2026-11-19 | Versión inicial | Encargo PM → LEAD (despliegue temprano para el demo del 10-dic) | Humano (vía PM), 2026-11-19 |
