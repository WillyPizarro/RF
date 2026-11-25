# CONTRATO — DESPLIEGUE-01 Despliegue temprano en el VPS y APK para probadores

**Tipo:** Feature (despliegue)
**Versión:** v2.1
**Estado:** v1 aprobada (2026-11-19, humano vía PM) · v2 aprobada (humano vía PM, 2026-11-24) · **v2.1 PROPUESTA, espera la aprobación del humano (vía PM)**
**Origen:** encargo PM → LEAD (2026-11-19, decisión del humano): el MININTER y el equipo prueban desde **sus** celulares en el demo del **jueves 10-dic**. **v2:** encargo PM → LEAD (2026-11-24, tarea 2): NGINX en lugar de Caddy (ADR-0018) y el APK de Flutter descargable desde una ruta protegida del VPS (ADR-0018 punto 5, decisión 4 del humano), en lugar del enlace de EAS
**Alcance:** lo que esté en `main` después del merge de la migración a Flutter (CONTRATO-MIGRACION-FLUTTER: HU-08, HU-01, HU-02, HU-03, HU-07 y HU-04 en la app Flutter). Las HU siguientes se suben después con los mismos comandos (§6)
**Rama de trabajo:** `despliegue-01` (worktree `C:\Willy\Trabajo\MININTER\Movil_Buscador-despliegue`), con la fase A de la v1 ya hecha. **v2.1:** rebasada el 2026-11-25 sobre `main` `7c81105` (merge de MIGRACION-FLUTTER, PR #1). La fase A quedó en `fb2eef2` (DEV), `5b2d45e` (TESTER), `3186a95` y `c98d3ec` (LEAD). La rama anterior se conserva en `backup/despliegue-01-pre-rebase-4fb531c`. `origin/despliegue-01` tiene la historia previa al rebase, así que subirla exige un push forzado de **esta** rama, con autorización del humano
**Plazo (plan decidido, evaluación del stack §5):** del 6 al 8-dic, después del veredicto de la migración. **v2.1:** la migración se mergeó el 25-nov, así que la fase B puede empezar en cuanto se apruebe esta versión. El humano contrata el VPS, el dominio y Supabase a más tardar el **miércoles 2-dic**. Desplegado, y probado por el humano desde su S23 Ultra **por descarga (no por cable)**, antes del **10-dic**

> **Qué cambia de la v1 a la v2:** el proxy (§1 y §2), el APK y su entrega (§5), los comandos de la app (§6), la guía (§7), el borrado al cierre (§8) y las pruebas del proxy. Lo de Supabase, los secretos y `api_app` (§3 y §4) no cambia, salvo los secretos nuevos. Cada cambio lleva la marca **v2**.

---

## Paquete de contexto

| Fuente | Por qué entra |
|---|---|
| ADR-0009 | VPS pequeño con docker compose, Supabase en la nube (Auth y Postgres, referencia São Paulo), secretos solo en variables del VPS. **v2:** su punto 1 (proxy) lo reemplaza el ADR-0018 y su punto 4 (EAS) el ADR-0017 |
| **ADR-0018 (v2)** (`docs/arch/adrs/0018-proxy-nginx.md`) | NGINX con la misma regla (`/v1/` → `api:8000`, 404 al resto), `certbot` en un contenedor aparte en el VPS, CA local generada por un script de `infra/`, la configuración que Caddy daba por defecto (cuerpo máximo, TLS, cabeceras, registro sin `Authorization`) y la ruta protegida del APK (punto 5) |
| **ADR-0017 (v2)** | APK firmado en la máquina del proyecto, sin EAS; la llave de firma es un secreto fuera del repositorio; el APK de la demo sin `debug-overrides` |
| **CONTRATO-MIGRACION-FLUTTER v1.5 (v2.1)** | `--dart-define=API_URL`, `applicationId` `pe.prototipo.movilbuscador`, release no depurable y llave de firma fuera del repositorio (§6). **v1.5:** la app usa `ok_http`, así que rige el `network_security_config`: el release confía **solo** en las CA del sistema (Let's Encrypt sirve) y el de depuración, además, en la CA de usuario (la CA local de NGINX) |
| ADR-0005 y CONTRATO-HU-07 v5 | La API se conecta como `api_app` (solo `INSERT` y `SELECT` en `bitacora`, más el trigger), **nunca** con `service_role` |
| ADR-0012 y CONTRATO-HU-07 v2 | Alembic con SQL explícito; migración con `MIGRACION_DATABASE_URL` (rol dueño) |
| ADR-0003 y CONTRATO-HU-01 v6 | Supabase Auth; carga de los usuarios sintéticos con `python -m app.cargar_usuarios`; la clave solo en `CLAVE_USUARIOS_PRUEBA` |
| ADR-0006 y CONTRATO-HU-08 v4 | `simuladores` solo en la red interna; datos sintéticos `ZZ` / `SIM-` |
| ADR-0008 | Al cierre se borra todo el ambiente y se firma un acta de eliminación |
| ADR-0010 | Solo en línea; Android primero; iOS no se distribuye |
| `docs/contratos/PENDIENTES.md` › Despliegue | Dos tareas **obligatorias**: `api_app` en el Supabase de la nube, y que la clave no quede en los logs del proxy del VPS |
| CONTRATO-HU-01 §5, CONTRATO-HU-04 v6 §8 | La clave no aparece en logs; el build de release no confía en certificados del usuario; la CA local del proxy para el teléfono de pruebas |
| Fase A de la v1 en `despliegue-01` | `infra/docker-compose.vps.yml`, `scripts/desplegar.ps1`, `docs/despliegue/` y las pruebas del TESTER contra el VPS, que se reutilizan |

## Interfaz observable

1. **URL pública** `https://<DOMINIO>`, servida por **NGINX** (**v2**) con un certificado de Let's Encrypt. Expone solo `/v1/*` y `/descargas/movil-buscador.apk` (**v2**).
2. **El VPS:** puertos abiertos hacia internet y contenedores en marcha.
3. **El APK de release de Flutter** (**v2**), descargable con usuario y clave desde `https://<DOMINIO>/descargas/movil-buscador.apk`.
4. **El proxy local** del compose de desarrollo (**v2**): el mismo NGINX, con la CA local.
5. **Documentos:** la guía para probadores y el manual de despliegue.
6. **Comandos de despliegue** (§6).

## Comportamiento

### 1. Servicios en el VPS

| Caso | Salida esperada | Origen |
|---|---|---|
| Servicios | En el VPS corren `api`, `simuladores`, `proxy` (**NGINX**, imagen oficial `nginx` con versión estable fijada por el DEV) y `certbot` (**v2**), con `infra/docker-compose.yml` más `infra/docker-compose.vps.yml`, que **quita** `db` y `auth`. **No** se usa `docker-compose.fotos.yml` | ADR-0009 §1 y §2, ADR-0018 §1 y §2, ADR-0008 |
| El servicio se sigue llamando `proxy` | Para que `docker compose logs proxy` y las pruebas existentes sigan valiendo | ADR-0018 §4 · **v2** |
| Puertos | Desde internet solo responden **22** (SSH, solo con llave), **80** y **443**. `8000`, `8001` y `5432` no responden. `certbot` no publica puertos | ADR-0009 §1, ADR-0006 |
| Salud | `GET https://<DOMINIO>/v1/salud` → `200` con `"bd":"ok"` y `"simuladores":"ok"` | CONTRATO-HU-08 §8, Sprint 0 |
| Solo `/v1/*` y el APK | `GET https://<DOMINIO>/openapi.json`, `GET https://<DOMINIO>/` y cualquier otra ruta fuera de `/v1/` y de `/descargas/movil-buscador.apk` → `404` | ADR-0018 §1 y §5 · **v2** |
| Mismo comportamiento | Los contratos vigentes en `main` se cumplen igual en el VPS: HU-08 v4, HU-01 v6, HU-02 v4, HU-03 v5, HU-07 v5 y HU-04 **v7** (**v2.1**) | ADR-0009 ("lo que se entrega es lo que se probó") |

### 2. NGINX: TLS, certificados y configuración (v2)

| Caso | Salida esperada | Origen |
|---|---|---|
| Certificado del VPS | Lo emite **Let's Encrypt** con `certbot` en modo *webroot* sobre el puerto 80, y se renueva solo (renovación programada y recarga de NGINX). El certificado vive en un volumen, **nunca** en el repositorio | ADR-0018 §2 |
| Android lo acepta | El APK de release llega a la API **sin instalar ningún certificado** en el teléfono | Encargo v1, CONTRATO-HU-04 v6 §8 |
| Verificación desde afuera | Un cliente con las CA del sistema (por ejemplo, `python` con `ssl.create_default_context()`) conecta a `https://<DOMINIO>/v1/salud` sin desactivar la verificación | Encargo v1 |
| HTTP → HTTPS | `http://<DOMINIO>/v1/salud` responde con una redirección (`301` o `308`) a `https://`. La única excepción es `/.well-known/acme-challenge/` (para `certbot`) | ADR-0018 §3 |
| Solo TLS 1.2 y 1.3 | Un cliente que fuerza TLS 1.0 o 1.1 no completa el saludo | ADR-0018 §3 |
| Cabeceras de seguridad | Toda respuesta por HTTPS lleva `Strict-Transport-Security` y `X-Content-Type-Options: nosniff` | ADR-0018 §3 |
| Cabeceras hacia la API | NGINX pasa `X-Forwarded-For` y `X-Forwarded-Proto`. La API sigue respondiendo igual (las pruebas de la API no cambian) | ADR-0018 §3 |
| Cuerpo máximo | `client_max_body_size 5m` (provisional, ADR-0011): un `POST` a `/v1/…` con un cuerpo de más de 5 MB recibe `413` del proxy; uno de menos llega a la API | ADR-0018 §3 |
| Registro sin secretos | El registro de acceso usa un formato sin cuerpo y sin la cabecera `Authorization`. La prueba `test_la_clave_no_queda_en_los_logs_del_proxy` sigue igual, ahora sobre NGINX | ADR-0018 §3 y §4, CONTRATO-HU-01 §5 |
| Local | En el compose de desarrollo, el mismo `proxy` NGINX con una **CA local** generada por un script de `infra/` la primera vez que se arranca, fuera del repositorio. Reemplaza a la CA interna de Caddy en los pasos del teléfono (CONTRATO-HU-04 v6 §8). Los puertos siguen en `PROXY_PUERTO_HTTP` y `PROXY_PUERTO_HTTPS` | ADR-0018 §2 |
| Caddy desaparece | `infra/Caddyfile` ya no existe y ningún compose usa la imagen `caddy` | ADR-0018 (reemplaza) |

### 3. Base de datos y Auth en Supabase (obligatorio, `PENDIENTES.md`; sin cambios)

| Caso | Salida esperada | Origen |
|---|---|---|
| Migraciones | Las migraciones de Alembic corren contra el Postgres de Supabase con `MIGRACION_DATABASE_URL` (rol dueño): dejan `bitacora`, `consulta` y los demás objetos, el rol `api_app` con solo `INSERT` y `SELECT` sobre `bitacora`, y el trigger de solo inserción. El esquema `auth` de Supabase no se toca | ADR-0012, CONTRATO-HU-07 v2 §1 |
| La API usa `api_app` | En `pg_stat_activity`, las conexiones de la API usan `usename = api_app`. **Nunca** `service_role` ni `postgres` | ADR-0005, `PENDIENTES.md` (obligatorio) |
| Solo inserción en la nube | Como `api_app` y como dueño, `UPDATE`, `DELETE` y `TRUNCATE` sobre `bitacora` fallan (mensaje del trigger: `bitacora es de solo insercion`) | CONTRATO-HU-07 §1 |
| Auth | La API usa Supabase Auth del proyecto (`AUTH_URL=https://<proyecto>.supabase.co/auth/v1`, `AUTH_APIKEY` con la clave pública) | ADR-0003, `.env.example` |
| Usuarios | `python -m app.cargar_usuarios` deja en Supabase Auth a `agente1`, `agente2`, `revisor1`, `supervisor1` e `inactivo1`, con la clave de `CLAVE_USUARIOS_PRUEBA` del VPS | CONTRATO-HU-01 §6 |
| Credencial de administración solo para la carga | La credencial de administración de Auth se pasa **solo** a `cargar_usuarios`, al correrlo. `docker compose exec api printenv` no muestra ningún secreto de administración ni de `service_role` | ADR-0005 · decisión 1 (v1) |

### 4. Secretos y datos

| Caso | Salida esperada | Origen |
|---|---|---|
| Secretos fuera del repositorio | Los secretos viven solo en el `.env` del VPS (fuera del repositorio, con permisos `600`). Son: `DATABASE_URL`, `API_APP_CLAVE`, `MIGRACION_DATABASE_URL`, `AUTH_APIKEY`, la credencial de administración de Auth, `JWT_SECRETO`, `CLAVE_USUARIOS_PRUEBA`, `SIM_FOTOS_LLAVE` y, **v2**, `DESCARGA_APK_CLAVE`. La **llave de firma del APK** vive solo en la máquina del proyecto (**v2**). `git ls-files` y `git log -p` de la rama no muestran ninguno | ADR-0009 §5, ADR-0017, ADR-0018 §5, regla 8 |
| La clave no queda en los logs del proxy del VPS | Después de un login desde el APK, `docker compose logs proxy` y los logs de `api` en el VPS no contienen la clave | `PENDIENTES.md` (obligatorio), CONTRATO-HU-01 §5 |
| Solo datos sintéticos | Simuladores con la semilla sintética (`ZZ`, `SIM-`), sin fotos de rostro hasta HU-05. Ningún dato real de ciudadanos | ADR-0008, regla 8 |
| Sin datos en el teléfono | El APK guarda solo el token en el almacenamiento seguro, como en HU-01 v6 | ADR-0013 |

### 5. APK para probadores: descarga protegida (v2; reemplaza el perfil `preview` de EAS)

| Caso | Salida esperada | Origen |
|---|---|---|
| Build | `flutter build apk --release --dart-define=API_URL=https://<DOMINIO>` en la máquina del proyecto, firmado con la llave de firma fuera del repositorio (CONTRATO-MIGRACION-FLUTTER §6) | ADR-0017, ADR-0018 §5 |
| No es de depuración | El APK no es depurable y no confía en certificados del usuario: `aapt dump badging` (o `apkanalyzer`) no muestra `application-debuggable` | ADR-0018 §5, CONTRATO-HU-04 v6 §8 |
| Ruta exacta | `location = /descargas/movil-buscador.apk` sirve **un solo archivo** desde un volumen de **solo lectura** del contenedor `proxy`, sin listar el directorio (`autoindex off`) | ADR-0018 §5 |
| Sin credencial | `GET https://<DOMINIO>/descargas/movil-buscador.apk` sin usuario y clave → `401` con `WWW-Authenticate: Basic` | ADR-0018 §5 y consecuencias |
| Credencial incorrecta | Usuario o clave equivocados → `401` | ADR-0018 §5 |
| Con credencial | Con `DESCARGA_APK_USUARIO` y `DESCARGA_APK_CLAVE` → `200` y el cuerpo es **exactamente** el APK publicado (el mismo SHA-256 que el archivo copiado al volumen) | ADR-0018 consecuencias |
| Otras rutas | `/descargas/`, `/descargas/otro.apk`, `/descargas/movil-buscador.apk/` y cualquier otra bajo `/descargas/` → `404` (también con credencial) | ADR-0018 §5 |
| Solo por HTTPS | `http://<DOMINIO>/descargas/movil-buscador.apk` redirige a `https://` antes de pedir la credencial; la clave nunca viaja por HTTP | ADR-0018 §5 |
| La clave no queda en los logs | Después de una descarga con credencial, `docker compose logs proxy` no contiene la clave ni la cabecera `Authorization` | ADR-0018 consecuencias |
| `htpasswd` | El archivo de claves se genera **en el VPS** desde `DESCARGA_APK_USUARIO` y `DESCARGA_APK_CLAVE` al arrancar o al desplegar, con **un solo usuario y una sola clave para todos los probadores** (respuesta 4 de la v2); nunca va al repositorio. La clave se reparte por un canal aparte, nunca junto con el enlace | ADR-0018 §5 · DECISIÓN PROPUESTA 5 |
| El APK no se versiona | `git ls-files` no muestra ningún `.apk` ni `.aab`, y `.gitignore` los excluye | ADR-0018 §5, regla 8 |
| Funciona sin cable | En el S23 Ultra, **después de desinstalar** la app de Expo, descargado desde la ruta con la credencial e instalado, sin USB: login con `agente1`, `ZZA-101` con motivo → "TIENE REQUISITORIA", `ZZB-201` → sin requisitoria, `ZZZ-999` → placa no registrada; 📷 lee una placa impresa; `supervisor1` → BIT-01 con esas consultas | Encargo v1 (prueba del humano), HU-04 |

### 6. Volver a desplegar con un comando

| Caso | Salida esperada | Origen |
|---|---|---|
| Servidor | `scripts/desplegar.ps1 <rama o commit>` entra al VPS por SSH, trae el código desde `origin`, reconstruye y reinicia `api`, `simuladores`, `proxy` y `certbot`, y aplica las migraciones. Al terminar, `GET /v1/salud` responde `200`. **No copia ningún secreto** | Encargo v1, decisión 4 (v1) |
| App (**v2**) | `scripts/publicar-apk.ps1` compila el APK de release (§5), lo copia al volumen del `proxy` en el VPS por SSH y muestra su SHA-256. No copia la llave de firma ni la credencial | ADR-0018 §5 ("el DEV lo copia al volumen del VPS en cada build") · DECISIÓN PROPUESTA 6 |
| Idempotente | Correr los dos comandos dos veces seguidas no rompe nada ni duplica usuarios | CONTRATO-HU-01 §6 |
| Sin EAS (**v2**, **v2.1**) | `apps/movil/eas.json` y el perfil `preview` de la fase A **no existen** en la rama. **v2.1:** la migración no lo quitó, porque el archivo solo estaba en `despliegue-01` (`fb2eef2`) y sobrevivió al rebase. Lo **borra el DEV** en este ciclo (única excepción en `apps/movil/`, ver Rutas). Tampoco queda ninguna mención de EAS en `docs/despliegue/`: `grep -rniw "eas" apps/movil docs/despliegue` vacío | ADR-0017 · hallazgo del rebase (2026-11-25) |

### 7. Documentos

| Documento | Contenido | Origen |
|---|---|---|
| **Guía corta para probadores** (español simple, 1 o 2 páginas; **v2**) | 1. Si tiene instalada una versión anterior de "Movil Buscador", **desinstalarla** primero. 2. Abrir `https://<DOMINIO>/descargas/movil-buscador.apk` en el celular Android y escribir el usuario y la clave **de la descarga**, que le da el responsable del demo por otro canal. 3. Permitir la instalación desde esa fuente (Samsung con Android 16, y una nota genérica para otros Android). 4. Abrir "Movil Buscador". 5. Los usuarios de prueba de la app (`agente1`, `revisor1`, `supervisor1`), **sin la clave**. 6. Qué probar: las placas `ZZA-101`, `ZZB-201` y `ZZZ-999` con un motivo, la lectura con la cámara de una placa impresa de prueba y la bitácora con `supervisor1`. 7. Qué **no** esperar todavía: rostro (HU-05). 8. El aviso de telemetría de ML Kit (anexo del BA, M-2 de la v1). 9. Que todos los datos son ficticios. 10. Cómo desinstalar la app | Encargo v1, ADR-0018 §5 |
| **Pasos para el dominio** | Sin cambios (v1) | Respuesta 2 del humano (v1) |
| **Manual de despliegue** (**v2**) | Lo de la v1 más: NGINX y `certbot` (emisión, renovación, qué hacer si falla), la CA local, cómo compilar y firmar el APK, `scripts/publicar-apk.ps1`, cómo cambiar la credencial de la descarga si se filtra, y cómo quitar la ruta | ADR-0009 §3, ADR-0018 |

### 8. Borrado al cierre (acta de eliminación)

Se agrega a `PENDIENTES.md` y al acta de eliminación (ADR-0008):
- borrar el VPS, con sus discos y snapshots (incluidos los certificados de Let's Encrypt y el APK del volumen);
- borrar el proyecto de Supabase, con sus respaldos;
- **v2:** quitar la ruta `/descargas/movil-buscador.apk`, el archivo y la credencial `DESCARGA_APK_*`, al terminar la validación y a más tardar en el acta (ADR-0018 §5);
- **v2:** borrar la llave de firma del APK y la CA local del proxy (y pedir que se quite del teléfono de pruebas);
- **v2.1:** la CA de Caddy de la migración (`C:\Willy\Trabajo\MININTER\ca-local\` y la CA de usuario del S23) se quita **en este ciclo**, cuando el S23 pase a la CA de NGINX, y queda anotado en el acta;
- borrar los builds y el proyecto de EAS de la etapa Expo (por ejemplo `a3380e39`), o como mínimo sus enlaces internos;
- borrar el registro DNS del subdominio;
- pedir a los probadores que desinstalen la app.

## Nombres que no se negocian

| Tipo | Valor exacto |
|---|---|
| URL | `https://<DOMINIO>/v1/*` · `https://<DOMINIO>/descargas/movil-buscador.apk` (**v2**) |
| Servicios en el VPS | `api`, `simuladores`, `proxy` (NGINX), `certbot` (**v2**; sin `db` ni `auth`) |
| Rol de la API | `api_app` |
| Variables | Las de `infra/.env.example`, más `DESCARGA_APK_USUARIO` y `DESCARGA_APK_CLAVE` (**v2**) y la credencial de administración de Auth solo para la carga |
| Comandos | `scripts/desplegar.ps1` · `scripts/publicar-apk.ps1` (**v2**) |
| ID de la aplicación (`applicationId`) | `pe.prototipo.movilbuscador` · "Movil Buscador" |
| Usuarios | `agente1` · `agente2` · `revisor1` · `supervisor1` · `inactivo1` |
| Placas del demo | `ZZA-101` · `ZZB-201` · `ZZZ-999` |

## Qué prueba quién y dónde

| Parte | Quién | Dónde |
|---|---|---|
| NGINX en local (**v2**): `404` fuera de `/v1/` y del APK, redirección a HTTPS, TLS 1.2 y 1.3, cabeceras, `413` sobre 5 MB, la clave fuera de los logs, la ruta del APK (`401`, `200` con el SHA-256, `404` en el resto de `/descargas/`) con un **archivo de prueba** (no un APK real) en el volumen | TESTER | Compose local, en `services/api/tests/` |
| Puertos, certificado, `/v1/salud`, `404` fuera de `/v1/*` y la ruta del APK | TESTER | Desde esta PC contra `https://<DOMINIO>`. Pruebas que se omiten si no está `URL_VPS` (la fase A ya las tiene para `/v1`) |
| Flujo de API: login, consulta de las 3 placas, bitácora del supervisor, `403` por rol | TESTER | Desde esta PC contra el VPS, con `CLAVE_USUARIOS_PRUEBA` y `DESCARGA_APK_CLAVE` leídas del entorno local y nunca escritas |
| `api_app` en `pg_stat_activity`, trigger, `printenv` sin secretos de administración, la clave fuera de los logs del proxy, renovación de `certbot` en seco (`certbot renew --dry-run`) | TESTER con SSH (respuesta 5 de la v1) | En el VPS |
| APK no depurable | TESTER | Sobre el APK descargado de la ruta |
| Instalación por descarga y el paso a paso en el S23 Ultra, sin cable | **Humano** | Su teléfono |
| Regresión | TESTER | Las suites de siempre en local, ahora con NGINX en el compose, incluidas `test_hu04_sin_cache.py` por el proxy y `test_la_clave_no_queda_en_los_logs_del_proxy` |
| Teléfono de pruebas con el NGINX local (**v2.1**) | TESTER (guion) y **humano** | El TESTER pasa a la CA local de NGINX los pasos de Caddy del guion `pruebas/datos/GUION-MIGRACION-FLUTTER-dispositivo.md`: exportar la CA, la CA de usuario y ver el error de TLS en el log del proxy. En el S23, con el APK de depuración de `main`, el humano quita la CA de Caddy, instala la de NGINX y hace un login con `agente1` contra el compose local. Va en la misma sesión que la prueba por descarga |

## Rutas de cada rol

| Rol | Rutas | Origen |
|---|---|---|
| DEV | `infra/` (NGINX, `certbot`, CA local, composes), `scripts/` (`desplegar.ps1`, `publicar-apk.ps1`), `docs/despliegue/`, **v2.1:** borrar `apps/movil/eas.json` (lo único que toca en `apps/movil/`), `services/api/` (solo si la API necesitara confiar en `X-Forwarded-*`; no se espera), `.gitignore` (solo agregar: `*.apk`, `*.aab`, certificados), `README.md` raíz, `informes/DEV-*.md` | AGENTS.md (`docs/despliegue/` en la fila del DEV desde la rama `migracion-flutter`: decisión 2 de la v1 y respuesta 3 de la v2) |
| TESTER | `services/api/tests/` (pruebas del proxy y contra el VPS; **v2.1:** también las referencias a Caddy de `test_despliegue_vps.py`), `pruebas/` (**v2.1:** el guion del teléfono con NGINX), `informes/TESTER-*.md` | AGENTS.md |

La app (`apps/movil/`) no se toca en este ciclo, **salvo el borrado de `apps/movil/eas.json` (v2.1)**: el APK sale del `main` con la migración (CONTRATO-MIGRACION-FLUTTER v1.5).

## Avisos de contexto

- **Supabase y `asyncpg`, llaves de Supabase, plan gratuito, usuarios compartidos:** siguen los avisos de la v1 (Session pooler en IPv4; adaptar solo la carga si el proyecto no tiene el secreto heredado; el plan gratuito se pausa; el bloqueo y la bitácora se comparten si varios usan `agente1`).
- **La credencial de la descarga se puede reenviar** (ADR-0018, riesgo aceptado): el APK tiene datos sintéticos y sin usuario de la app no consulta nada. Como es una sola para todos (respuesta 4), si se filtra se cambia `DESCARGA_APK_CLAVE`, se vuelve a desplegar y se reparte la nueva a todos los probadores.
- **`client_max_body_size` es provisional (5 MB)** y lo fija el ADR-0011 cuando llegue HU-05. Si se olvida, HU-05 recibe un `413` que la API no ve, y la app lo tiene que mostrar como error (regla 7).
- **Módulo ACME nativo de NGINX:** descartado por el ADR-0018 (se usa `certbot`), así que su NO VERIFICADO no aplica a este contrato.
- **Desinstalar la app de Expo:** el APK de Flutter tiene otra firma y no se instala encima.
- **Riesgo del cronograma:** si la migración se atrasa más de 2 días, la demo se hace con el último APK de Expo (DESPLIEGUE-01 v1, por EAS). Lo decide el humano.

## Decisiones propuestas (no venían en la tarea)

| # | Decisión | Por qué hace falta | Estado |
|---|---|---|---|
| 1 a 4 | Las de la v1 (credencial de administración solo para la carga, `docs/despliegue/` del DEV, VPS con `DOMINIO` real y SSH con llave, despliegue por SSH desde `origin`) | — | Aprobadas por el humano (vía PM, 2026-11-19) |
| 5 | La credencial de la descarga es **una sola** (un usuario y una clave para todos los probadores), entra por `DESCARGA_APK_USUARIO` y `DESCARGA_APK_CLAVE` en el `.env` del VPS, y el `htpasswd` se genera desde ahí. La clave se reparte por otro canal y nunca se versiona | El ADR-0018 dice "desde una variable de entorno" sin nombrarla. El TESTER y el DEV necesitan el mismo nombre | Aprobada por el humano (vía PM, 2026-11-24), con un solo usuario (respuesta 4) |
| 6 | El APK se compila y se sube con `scripts/publicar-apk.ps1` | El ADR-0018 dice que el DEV lo copia en cada build; un comando fijo lo hace repetible y comprobable | Aprobada por el humano (vía PM, 2026-11-24) |
| 7 | En local, la ruta del APK sirve un archivo de prueba que pone el TESTER en el volumen; el APK real solo existe en el VPS | Las pruebas de `401`, `200` y `404` no necesitan un APK real, y así no se compila uno en cada prueba | Aprobada por el humano (vía PM, 2026-11-24) |
| 8 | El compose local también pasa a NGINX (no solo el VPS) | Lo que se prueba en local tiene que ser lo que se despliega (ADR-0009). El ADR-0018 ya prevé la CA local | Aprobada por el humano (vía PM, 2026-11-24) |

## Fuera del contrato (decide el DEV)

- La versión estable de `nginx` y de `certbot`, la configuración exacta (archivos, `include`) y cómo se programa la renovación.
- El sistema operativo del VPS, el firewall y cómo se instala Docker; cómo entra el VPS al repositorio privado (por ejemplo, una *deploy key* de solo lectura, que nunca se versiona).
- Si el script de la CA local es PowerShell o bash, y dónde deja la CA (fuera del repositorio).

## Preguntas abiertas para el humano

Respuestas de la v1 (humano vía PM, 2026-11-19): VPS y Supabase los contrata el humano a más tardar el 2-dic; dominio comprado junto con el VPS; usuarios actuales para el 10-dic y la lista de probadores antes del 8-dic (**pendiente**); SSH con una llave dedicada; decisiones 1 a 4 aprobadas.

Nuevas en la v2:

Respuestas del humano a la v2 (vía PM, 2026-11-24):

1. **Rama:** `despliegue-01` se rebasa sobre `main` **después** del merge de la migración.
2. **Decisiones 5 a 8:** aprobadas (la 5, ajustada por la respuesta 4).
3. **`docs/despliegue/` en `AGENTS.md`:** el LEAD la agrega a la fila del DEV en la rama `migracion-flutter`, junto con el cambio de rutas.
4. **Credencial de la descarga:** **un solo usuario y una sola clave** para todos los probadores. La clave se reparte por otro canal y nunca se versiona. Si se filtra, se cambia para todos.

## Changelog

| Versión | Fecha | Cambio | Motivo | Aprobado por |
|---|---|---|---|---|
| v1 | 2026-11-19 | Versión inicial | Encargo PM → LEAD (despliegue temprano para el demo del 10-dic) | Humano (vía PM), 2026-11-19 |
| v2 | 2026-11-24 | NGINX en lugar de Caddy, con `certbot`, CA local, TLS, cabeceras, cuerpo máximo y registro sin `Authorization` (§1, §2); APK de Flutter descargable desde `/descargas/movil-buscador.apk` con usuario y clave, en lugar de EAS (§5); `scripts/publicar-apk.ps1` (§6); guía con la desinstalación de la app de Expo y la credencial de la descarga (§7); borrado de la ruta, la credencial, la llave de firma y la CA (§8); pruebas del proxy | ADR-0017 y ADR-0018 aceptados (decisiones del humano del 2026-11-24, 1 y 4) | Humano (vía PM), 2026-11-24, con las respuestas 1 a 4 (una sola credencial de descarga) |
| v2.1 | 2026-11-25 | Rama rebasada sobre `main` `7c81105`, con los commits nuevos de la fase A y el aviso de que subirla exige un push forzado autorizado. Paquete: MIGRACION-FLUTTER **v1.5** (`ok_http`: el release confía solo en las CA del sistema y el de depuración, además, en la CA de usuario). §1: HU-04 **v7**. §6: `apps/movil/eas.json` sobrevivió al rebase y lo borra el DEV; sin menciones de EAS en `docs/despliegue/`. Qué prueba quién: regresión con `test_hu04_sin_cache.py` por NGINX, y el teléfono de pruebas pasa de la CA de Caddy a la de NGINX (guion del TESTER y un login del humano). Rutas: el borrado de `eas.json` para el DEV, y las referencias a Caddy de `test_despliegue_vps.py` y el guion para el TESTER. §8: la CA de Caddy se quita en este ciclo | Rebase del 2026-11-25 sobre el merge de la migración (encargo PM → LEAD, aprobado por el humano): la v2 suponía que la migración borraba `eas.json` y citaba MIGRACION v1 y HU-04 v6 | **Pendiente:** humano (vía PM) |
