# ENCARGO LEAD → DEV y TESTER — DESPLIEGUE-01

**Documento de trabajo:** `docs/contratos/CONTRATO-DESPLIEGUE-01.md` **v2.1** (aprobado por el humano vía PM el 2026-11-25; la fase B va en la M-3). La v1 (2026-11-19) rigió la fase A. Es la única spec.
**Rama:** `despliegue-01`, desde `main` `fa75945`. **Se trabaja en un worktree aparte**, `C:\Willy\Trabajo\MININTER\Movil_Buscador-despliegue`, para no pisar `hu-04` en la carpeta principal. Ahí no está `infra/.env` (no se versiona): si lo necesitas, cópialo desde la carpeta principal y **no lo agregues a git**. Tampoco están las dependencias: corre `npm ci` en `apps/movil` si te hacen falta.
**Bloqueo:** el humano contrata el VPS, el dominio y Supabase **a más tardar el 2-dic**. La ventana de despliegue es del 3 al 7-dic. **Fase A (ahora):** todo lo que no necesita el VPS. **Fase B (3 al 7-dic):** el despliegue real, con una M-n.
**Prioridad:** HU-04 va primero. Esto avanza en los huecos y **no la frena**.

## Reglas

1. Solo tus rutas (`AGENTS.md`; el DEV ahora también es dueño de `docs/despliegue/`). Commits con `[DEV]` o `[TESTER]`, **sin** `Co-Authored-By`, sin push y sin merge.
2. **Ningún secreto en el repositorio:**
   - nada de claves de Supabase, `CLAVE_USUARIOS_PRUEBA`, llaves SSH, *deploy keys*, tokens de EAS ni el `.env` del VPS;
   - en los documentos van solo los **nombres** de las variables;
   - la clave de los usuarios nunca va en la guía.
3. Solo datos sintéticos. Sin fotos.
4. No toques `Empezar.txt`. Las dudas van al LEAD con `PREGUNTA <ROL>`.
5. No compres ni contrates nada, y no crees cuentas: eso lo hace el humano.

## Fase A — qué entrega cada uno

- **DEV:**
  - **Compose del VPS:** `infra/docker-compose.vps.yml`, que quita `db` y `auth` y deja `api`, `simuladores` y `proxy` con los puertos 80 y 443. **Sin** el compose de fotos.
  - **Variables:** `infra/.env.example` documenta las del VPS. La credencial de administración de Auth va **solo** para `cargar_usuarios` (decisión 1), con el nombre que elijas.
  - **La credencial fuera de la API en marcha:** que el contenedor `api` no la reciba, y que `cargar_usuarios` la acepte al correrlo, también con las "secret keys" nuevas de Supabase si el proyecto no tiene el JWT secret heredado. **El login no cambia.**
  - **Script de despliegue:** `scripts/desplegar.ps1 <rama o commit>`, que entra por SSH (decisión 4), hace `git fetch` y `checkout` desde `origin`, levanta los servicios con `up -d --build`, migra y espera a que `/v1/salud` responda `200`. No copia secretos y se puede correr dos veces seguidas.
  - **Perfil de EAS:** `preview` en `apps/movil/eas.json`. APK interno, sin `developmentClient` y con `EXPO_PUBLIC_API_URL` del dominio. Mientras no haya dominio, usa un marcador documentado.
  - **En `docs/despliegue/`, en español simple:**
    - `GUIA-PROBADORES.md` (§7 del contrato);
    - `DOMINIO.md`: comprar el dominio y crear el registro DNS `A`;
    - `MANUAL-DESPLIEGUE.md`: el VPS, el `.env` (solo nombres), Supabase (*Session pooler*), migrar, cargar usuarios, los comandos del §6, los logs y el borrado (§8);
    - cómo generar la llave SSH dedicada, autorizarla y revocarla al cierre.
  - **Verificaciones en local:**
    - `docker compose -f infra/docker-compose.yml -f infra/docker-compose.vps.yml config` arma solo `api`, `simuladores` y `proxy`;
    - la API en marcha no tiene la credencial de administración.
  - **Al terminar:** `ENTREGA DEV` con el informe en `informes/DEV-DESPLIEGUE-01.md`.
- **TESTER** (cuando termine la suite de la etapa 1 de HU-04):
  - **Prueba contra el VPS:** `services/api/tests/test_despliegue_vps.py`, que se omite si no está `URL_VPS`. Cubre los casos del contrato que se ven desde afuera:
    - los puertos 22, 80 y 443, y que 8000, 8001 y 5432 están cerrados;
    - el certificado validado con las CA del sistema;
    - `/v1/salud` responde `200`, y `/openapi.json` y `/` responden `404`;
    - login, las 3 placas, la bitácora del supervisor y el `403` por rol.

    La clave se lee del entorno y nunca se escribe.
  - **Comandos para dentro del VPS**, que corre quien tenga SSH: `pg_stat_activity` con `api_app`, el trigger, `printenv` sin la credencial de administración, la clave fuera de los logs del proxy y de `api`, y que el APK no es depurable (`aapt` o `apkanalyzer`).
  - **En local:** comprueba que la prueba nueva se omite sin `URL_VPS` y que la configuración del compose del VPS es la correcta.
  - **Informe:** `informes/TESTER-DESPLIEGUE-01.md`.

## Fase B (3 al 7-dic)

Se abre con una M-n cuando el humano tenga el VPS, el dominio y Supabase. La verificación del humano en su S23 Ultra, por el enlace y sin cable, cierra el veredicto antes del 8-dic.

## Aviso de vuelta

`herdr agent prompt lead "ENTREGA <ROL>: <resumen corto> — informes/<ROL>-DESPLIEGUE-01.md"`.

## Instrucciones del ciclo (M-n)

### M-1 (2026-11-19) — Entrega del DEV de la fase A; regresión local

**No reemplaza nada.** El DEV entregó la fase A (`8402ef2`). Cambió también el compose base (`infra/docker-compose.yml`): las variables de `db` y `auth` ahora tienen valores por defecto vacíos (`:-`), para que el VPS no necesite valores falsos.

- **TESTER**, en la fase A y **después** de terminar la suite de HU-04, en el worktree de `despliegue-01`:
  1. Lo que ya pedía el encargo.
  2. Una **regresión local completa**: pytest de la API con el proxy en el puerto alterno y `PROXY_DISPONIBLE=1`, los simuladores y Jest. Así se comprueba que el cambio del compose base no rompió el entorno local.
  3. Que `infra/docker-compose.vps.yml` no le pasa a `api` ni `AUTH_ADMIN_CLAVE` ni `AUTH_JWT_SECRETO`, revisando `docker compose … config`.

  Al terminar: `ENTREGA TESTER`, con el informe en `informes/TESTER-DESPLIEGUE-01.md`.
- **DEV:** sin cambios. Los pasos del §8 para el acta ya están en `PENDIENTES.md` (los agregó el LEAD).

### M-2 (2026-11-20) — Aviso de telemetría en la guía para probadores

**No reemplaza nada.** El humano aprobó el anexo del BA, `docs/hus/anexos/HU-04-aviso-telemetria-mlkit.md` (commit `6eafcd1`, rama `hu-04`). Ese anexo no está en esta rama: léelo con `git show 6eafcd1:docs/hus/anexos/HU-04-aviso-telemetria-mlkit.md`.

- **DEV:** **después** de entregar la M-9 a la M-12 de HU-04, que tienen prioridad, copia **tal cual** el §2 del anexo en `docs/despliegue/GUIA-PROBADORES.md`. Ponlo como una sección sobre la lectura de la placa con la cámara y aclara que **se aplica desde el despliegue que incluya HU-04**: el APK de la Iteración 1 no tiene cámara. No cambies el texto. Commit `[DEV]` en `despliegue-01` y avisa con `ENTREGA DEV`.

### M-3 (2026-11-25) — Contrato v2.1: fase B (NGINX, APK de Flutter por descarga) y verificación de red de ML Kit (DEV y TESTER)

Reemplaza: el documento de trabajo pasa a ser `docs/contratos/CONTRATO-DESPLIEGUE-01.md` **v2.1**, aprobado tal cual por el humano vía PM el 2026-11-25. Del encabezado quedan reemplazados la v1 y `main` `fa75945`, y de la fase A, el perfil de EAS. La rama `despliegue-01` está rebasada sobre `main` `889a91b`, que ya trae la app Flutter (PR #1). Las reglas 1 a 5 siguen; en la 2, los "tokens de EAS" pasan a ser la llave de firma del APK, `DESCARGA_APK_CLAVE` y las CA. Sin push ni merge.

**Además (decisión del humano, 2026-11-25):** la verificación de red de ML Kit, **niveles 1 y 2** de la "Propuesta 2026-11-25" de `docs/arch/evaluaciones/HU-04-telemetria-mlkit.md` (`889a91b`), se hace **en la misma sesión del teléfono** que el login contra NGINX y la prueba por descarga. El nivel 3 no entra.

**Antes de la sesión, B1 (sin VPS):**

**DEV:**
1. **NGINX en el compose local y en el del VPS**, según §1 y §2 del contrato:
   - el servicio `proxy` con la imagen `nginx` fijada;
   - `certbot` solo en el VPS;
   - TLS 1.2 y 1.3, la redirección a HTTPS, las cabeceras, `client_max_body_size 5m` y el registro sin `Authorization`;
   - la CA local generada por un script de `infra/`, fuera del repositorio;
   - fuera `infra/Caddyfile` y la imagen `caddy`.
2. **La ruta `/descargas/movil-buscador.apk`** (§5), con un volumen de solo lectura, autenticación básica y el `htpasswd` generado desde `DESCARGA_APK_USUARIO` y `DESCARGA_APK_CLAVE`. En local sirve el archivo de prueba del TESTER (decisión 7).
3. **`scripts/publicar-apk.ps1`** (§6) y `desplegar.ps1` con `certbot`.
4. **Borrar `apps/movil/eas.json`**, lo único que tocas en `apps/movil/`. Saca EAS y Caddy de `docs/despliegue/`: el manual y la guía van con NGINX, la descarga y la desinstalación de la app anterior (§7).
5. `.gitignore`: agrega `*.apk`, `*.aab` y los certificados.
6. **Verificación local:**
   - el compose arriba con NGINX;
   - `/v1/salud` responde `200` por `https://localhost:8443`;
   - `curl` contra la ruta del APK da `401`, `200` y `404`;
   - un APK de depuración de `main` instalado no hace falta todavía.
7. **Preparación de la red de ML Kit**, fuera del repositorio. Usa los programas que hagan falta sin dejarlos en el repositorio; las versiones van en el informe.
   - **mitmproxy** (MIT) y **`protoc`** en la PC.
   - **PCAPdroid** (GPL-3.0): el APK de F-Droid o el enlace de Google Play para el humano.
   - **La captura**, en `C:\Willy\Trabajo\MININTER\flutter-capturas\red\`.
   - **Cómo pasa el tráfico del S23 por mitmproxy:** por ejemplo, el proxy global con `adb` y `adb reverse`. Pruébalo **sin el teléfono** en lo que se pueda, y deja escrito cómo se deshace.
8. Informe `informes/DEV-DESPLIEGUE-01.md` con una sección v2.1 y `ENTREGA DEV: B1 <commit>`.

**TESTER:**
1. **Pruebas de NGINX en local** (Qué prueba quién, primera fila) en `services/api/tests/`, con un **archivo de prueba** (no un APK) en el volumen.
2. **`test_despliegue_vps.py`:** las referencias a Caddy pasan a NGINX y se suman la ruta del APK (`401`, `200` con el SHA-256 y `404`) y la redirección a HTTPS. Se siguen omitiendo sin `URL_VPS`.
3. **Guion de la sesión del teléfono**, en `pruebas/datos/`: uno nuevo o una sección del de la migración. En orden:
   - **(a)** Quitar la CA de Caddy del S23 y de `ca-local`. Instalar la CA local de NGINX y hacer un login de `agente1` con el APK de depuración contra el compose local.
   - **(b)** Nivel 1 con PCAPdroid: la app, después `com.google.android.gms`, y el OCR de una placa `ZZ` impresa.
   - **(c)** Nivel 2 con mitmproxy y el APK de depuración, con la CA de mitmproxy como CA de usuario, y `protoc --decode_raw` sobre la subida.
   - **(d)** Cuando exista el VPS: la prueba por descarga (§5, "Funciona sin cable") con el APK de release.
   - **(e)** Limpieza: desinstalar PCAPdroid, quitar la CA de mitmproxy, quitar el proxy del teléfono y borrar `flutter-capturas\red\`.

   Si hace falta, amplía `revisar_datatransport.py` para que descomprima el cuerpo y busque `ZZ` o imágenes en lo capturado. Solo categorías, dominios y conteos van al informe, **nunca** identificadores.
4. **Regresión local con NGINX**, solo de lo que toca el proxy: `test_hu04_sin_cache.py` por el proxy, la clave fuera de los logs y las pruebas nuevas. La suite completa va después, con una M-n.
5. `ESTADO TESTER` con el commit del guion y los resultados.

**La sesión** (DEV con los `adb` y el humano en el teléfono, coordinados por el PM, como en la M-14 de la migración) se arma cuando lleguen las dos entregas de B1. **Fase B2 (VPS):** cuando el humano dé el VPS, el dominio y Supabase, con otra M-n. **Al final**, el ARCH actualiza la evaluación con el resultado de los niveles 1 y 2.

Al terminar: DEV con `herdr agent prompt lead "ENTREGA DEV: ..."`, TESTER con `"ESTADO TESTER: ..."`.

### M-4 (2026-11-25) — Arbitraje: "imagen oficial `nginx` con versión fijada" (TESTER, vuelta 1)

Reemplaza: nada. El rojo es de `test_proxy_es_nginx_con_version_fijada` y `test_proxy_del_vps_es_nginx_fijado` (`f098f9a`): esperan `image: nginx:<versión>` en el compose, y el DEV construye `proxy` con `build: infra/nginx/` (`FROM nginx:1.30.8-alpine`, más `openssl` y su configuración).

**Desenlace: se apartó la prueba.**
- **Qué pide el contrato (§1 y ADR-0018 §1):** que el proxy sea **NGINX oficial con una versión estable fijada**.
- **Lo que deja al DEV** ("Fuera del contrato"): la configuración exacta (archivos, `include`) y cómo se arma.
- **Por qué cumple la imagen del DEV:** se construye sobre la imagen oficial fijada y le copia la configuración, así que cumple la intención.
- **Por qué se apartó la prueba:** verifica un mecanismo (`image:`) que el contrato no exige.

**TESTER:** la prueba acepta las dos formas, y en las dos verifica lo que pide el contrato:
- `image: nginx:<x.y.z[-variante]>`;
- `build:` con un `Dockerfile` cuyo `FROM` sea `nginx:<x.y.z[-variante]>`, de la librería oficial de Docker Hub (sin otro registro). Ni `latest`, ni `stable`, ni `mainline`, ni una etiqueta sin versión completa.

Además, si el contenedor está arriba, la versión de NGINX en marcha (`nginx -v` o `NGINX_VERSION`) coincide con la fijada. Vale para el compose local y para el del VPS. Corre las dos pruebas **cuando yo avise de la `ENTREGA DEV` de B1**, no antes.

### M-5 (2026-11-25) — Sesión 1 en el S23: el DEV corre los `adb` y la captura (DEV; TESTER, el registro)

Reemplaza: nada. Es la sesión 1 de la M-3. Contrato **v2.2**. Guion: `pruebas/datos/GUION-DESPLIEGUE-01-dispositivo.md` (`67a39e2`), secciones 0, (a), (b), (c) y (e). La (d) queda para la sesión 2, con el VPS. Se hace igual que en la M-14 de la migración: el DEV corre los `adb`, PCAPdroid y mitmproxy, el humano opera el teléfono con las instrucciones del PM, y el DEV coordina el momento de cada paso **directo con el PM**. El TESTER sigue sin correr `adb` contra el teléfono.

**DEV:**
1. **Antes de empezar:** borra `apps/movil/node_modules` (v2.2) y confirma que el compose está arriba solo desde `-despliegue`.
2. **Registro:** anota cada paso en `C:\Willy\Trabajo\MININTER\Movil_Buscador_capturas\DESPLIEGUE-01\resultados-sesion1.md`, fuera del repositorio, como `OK`, `ROJO: …` o `NO HECHO: …`.
   - **Nunca** escribas la clave, el identificador de instalación ni otros valores que identifiquen. Solo dominios, categorías y conteos.
   - Las capturas de red van en `flutter-capturas\red\` y se borran en (e).
3. **Un `ROJO`:** se para el paso y me avisas en el momento. Nada se arregla en la sesión.
4. **(a):** al terminar, `docker volume rm movil-buscador_caddy-datos movil-buscador_caddy-config` y borras `C:\Willy\Trabajo\MININTER\ca-local\`. Queda anotado para el acta.
5. **(e) siempre**, aunque algo salga `ROJO`:
   - desinstalar PCAPdroid;
   - quitar la CA de mitmproxy del teléfono;
   - quitar el proxy del teléfono y comprobar que `settings get global http_proxy` da `:0` o vacío;
   - `adb reverse --remove-all`;
   - borrar `flutter-capturas\red\`.

   La CA de NGINX **se queda** en el teléfono para el desarrollo.
6. **Al terminar:** `ESTADO DEV` con el resumen y el registro. Después se lo paso al TESTER para su informe, y el resultado de (b) y (c) al ARCH.

### M-6 (2026-11-25) — Sesión 1: el nivel 2 pasa a ser condicional y los pasos del humano van por el LEAD (DEV; TESTER y ARCH, aviso)

Reemplaza en la M-5: la coordinación "directo con el PM" y la (c) obligatoria. Lo decidió el humano (vía PM, 25-nov). El guion `67a39e2` no se cambia: esta M-6 se aplica encima.

1. **Nivel 2 condicional.** Al terminar la (b), y antes de la c.1, el DEV mira las conexiones de la **corrida 1**, la de la app (b.4 a b.8, filtro `pe.prototipo.movilbuscador`):
   - **Se corre la (c)** si la app tiene al menos una conexión a `firebaselogging.googleapis.com` u **otro host de Google**. Cuentan `*.googleapis.com`, `*.google.com`, `*.gstatic.com`, `*.googleusercontent.com`, `*.firebaseio.com`, `*.app-measurement.com` y `*.doubleclick.net`. Ante la duda, cuenta como de Google.
   - **No se corre la (c)** si la corrida 1 solo muestra la API local. Va al registro: `NO HECHO: nivel 2 no corrido; nivel 1 sin tráfico de la app a Google (M-6)`. Se pasa a la (e).
   - Las conexiones de `com.google.android.gms` (corrida 2, b.10) **no** deciden: mitmproxy no puede leerlas. Se anotan igual.
2. **La (e) sin la (c).** Se corre igual, entera. e.1 y e.6 confirman que no quedó proxy ni `reverse`. e.2 confirma que en Usuario está **solo** la CA de NGINX. e.4 no aplica.
3. **Coordinación.** El DEV corre los `adb`, PCAPdroid y mitmproxy y **me avisa a mí** antes de cada paso del humano. Yo se los mando al PM como `ESTADO LEAD`. El DEV espera mi "hecho" para seguir.
4. **Registro y salida.** Iguales a la M-5. El resultado de la (b), con la (c) o con su `NO HECHO`, va al ARCH. Si no se corrió el nivel 2, el ARCH lo deja escrito en la evaluación como "nivel 2 no necesario".
5. **Condiciones del ARCH (25-nov)** para que valga "nivel 2 no necesario":
   - Se corren la b.2 y la b.9 (la cola antes y después) y la b.6 (`jobscheduler run -f`). Al registro van el id del job y su resultado.
   - Si no hay tráfico y la cola **sigue con eventos**, se anota "no se observó envío en la ventana; N eventos siguen pendientes", no "no envía".
   - Si la cola **se vació sin tráfico visible**, es una **anomalía**. El DEV me avisa **antes de la (e)** y yo se lo paso al ARCH.
   - Por cada UID (app y `com.google.android.gms`) van: host o SNI, bytes y hora. También va la confirmación de que las capturas quedaron fuera del repositorio y se borraron en la e.5.
6. **Nivel 2: lo que pide el ARCH (25-nov)**:
   - La cola queda vacía después de la corrida 1. Antes de la c.5 se leen placas ZZ nuevas para generar eventos. La cola se cuenta antes de forzar la subida, y el id del job se saca otra vez con `dumpsys jobscheduler`, porque puede cambiar.
   - El APK tiene que ser el de depuración. La CA de mitmproxy se quita en la e.2.
   - Si el POST viene en gzip, se descomprime antes de `protoc --decode_raw` y de `revisar_datatransport.py --cuerpos`.
   - Al registro van: `Content-Type`, `Content-Encoding`, el tamaño, los campos del `decode_raw` solo por categoría (sin el identificador de instalación ni la huella del build) y el resultado de la búsqueda de imágenes y de `ZZ` sobre el cuerpo descomprimido.
7. **Incidente de la corrida 2 (25-nov, ~20:41), va al acta de eliminación.** El humano mandó el pcap de la corrida 2 a su propio correo para pasarlo a la PC. Es una salida a un servicio externo **sin datos reales**: solo la telemetría de un teléfono de prueba, con el identificador de instalación y datos del equipo. El humano lo borra de Enviados, de la Bandeja de entrada y de la papelera, en el teléfono y en la PC (lo confirma por el PM). En la (e), el DEV borra los dos pcap del teléfono (`Download/PCAPdroid/`), las dos copias de la PC (`Movil_Buscador_capturas\DESPLIEGUE-01\` y `Downloads\`) y `flutter-capturas\red\`.
   **Regla desde ahora, también para el bloque HU-05 + HU-06:** el pcap se saca **solo por `adb pull`**. Nunca con "compartir" ni por correo.
