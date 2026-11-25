# ADR 0018: NGINX en lugar de Caddy como proxy TLS

## Estado

**Aceptado (2026-11-24).** Propuesto por el ARCH a pedido del PM (PRD PA #37: "NGINX reemplaza a Caddy") y aceptado por el humano el mismo día, con la descarga del APK desde una ruta protegida (punto 5). **Reemplaza** el servicio `proxy` del punto 1 del [ADR-0009](0009-despliegue.md). El resto del ADR-0009 (VPS, docker compose, Supabase en la nube, entrega con manual) no cambia.

## Contexto

- El `proxy` de hoy (`infra/Caddyfile`, `infra/docker-compose.yml`, imagen `caddy:2.10`) hace tres cosas: termina TLS con certificado automático (ACME en el VPS, CA interna con `DOMINIO=localhost`), enruta **solo** `/v1/*` hacia `api:8000` y responde 404 a todo lo demás (SPRINT0 M-1 G; `/openapi.json` no se expone).
- Es el único servicio que publica puertos (80 y 443, o `PROXY_PUERTO_HTTP` y `PROXY_PUERTO_HTTPS` en local).
- Dependen del proxy: la prueba `test_la_clave_no_queda_en_los_logs_del_proxy` (CONTRATO-HU-01 §5), su repetición obligatoria sobre el VPS (`docs/contratos/PENDIENTES.md`), y los pasos de HU-04 v3 para exportar la CA local del contenedor `proxy` e instalarla en el teléfono de pruebas.
- HU-05 enviará el recorte del rostro en el cuerpo de la solicitud. Caddy no limita el tamaño del cuerpo por defecto; **NGINX sí: 1 MB** (`client_max_body_size`).

## Decisión

1. El servicio `proxy` usa la imagen oficial `nginx` (versión estable fijada por el DEV), con la misma regla: `location /v1/ { proxy_pass http://api:8000; }` y `return 404` para todo lo demás.
2. **Certificados:**
   - **VPS:** Let's Encrypt con `certbot` en un contenedor aparte (modo *webroot* sobre el puerto 80 y renovación programada). El certificado vive en un volumen y nunca en el repositorio.
   - **Local:** una CA local generada por un script de `infra/` (por ejemplo, con `openssl`) la primera vez que se arranca, fuera del repositorio. Reemplaza a la CA interna de Caddy en los pasos de HU-04 v3.
3. **Configuración que Caddy daba por defecto y NGINX no:**
   - `client_max_body_size` explícito (provisional: 5 MB, que alcanza para un recorte JPEG; se fija en el ADR-0011).
   - Solo TLS 1.2 y 1.3, y redirección de HTTP a HTTPS.
   - Cabeceras `X-Forwarded-For` y `X-Forwarded-Proto` hacia la API, y la API confía en ellas solo si vienen del proxy.
   - Registro de acceso **sin cuerpo y sin cabecera `Authorization`**: el formato por defecto (`combined`) ya no los incluye, y la prueba de que la clave no queda en los logs se mantiene igual.
   - Cabeceras de seguridad básicas (`Strict-Transport-Security`, `X-Content-Type-Options`).
4. La prueba del proxy y la del VPS no cambian de intención. Solo cambia de dónde se leen los logs (`docker compose logs proxy`).
5. **Descarga del APK para los probadores (decisión del humano, 2026-11-24; reemplaza el enlace de EAS, ADR-0017):**
   - Es la **única excepción** a "solo `/v1/*`": una ruta `location = /descargas/movil-buscador.apk` (nombre exacto, sin listar el directorio: `autoindex off`) que sirve **un solo archivo** desde un volumen de solo lectura del contenedor `proxy`. Cualquier otra ruta bajo `/descargas/` responde 404.
   - **Protegida con usuario y clave** (autenticación básica de HTTP, solo sobre HTTPS). El archivo de claves (`htpasswd`) se genera en el VPS desde una variable de entorno y nunca va al repositorio (regla 8). La credencial se reparte a la lista de probadores por un canal aparte, nunca junto con el enlace.
   - El APK no se versiona en el repositorio: el DEV lo copia al volumen del VPS en cada build.
   - Al terminar la validación, o a más tardar en el acta de eliminación del cierre, se quitan la ruta, el archivo y la credencial.
   - El APK de la demo se compila sin las excepciones de depuración (`<debug-overrides>`, ADR-0017 punto 4) y apunta al dominio del VPS.

## Alternativas consideradas

- **Entregar el APK por un *release* privado de GitHub o por Firebase App Distribution.** El primero obliga a cada probador a tener una cuenta. El segundo suma un tercero (Google) que recibe datos de los probadores. Se descartan (decisión del humano, 2026-11-24).
- **Proteger la descarga con un token en la URL en vez de usuario y clave.** Es más cómodo, pero el token queda en el historial y en los logs de acceso. Se descarta.
- **Mantener Caddy.** Ya funciona, tiene HTTPS automático y no requiere `certbot`. Se descarta porque el humano decidió el 2026-11-24 usar NGINX, el estándar del MININTER para publicar.
- **NGINX sin TLS, detrás de un balanceador del MININTER que termine TLS.** Es como lo publicaría la entidad en producción. Se descarta para el MVP porque el demo vive en el VPS del proveedor. Queda en el manual como variante.
- **NGINX con el módulo ACME nativo (`ngx_http_acme_module`).** Evitaría `certbot`. Se descarta por ahora porque es reciente y no viene en todas las imágenes oficiales. **NO VERIFICADO:** disponibilidad en la imagen estable que fije el DEV.

## Consecuencias

- El proxy queda en el stack del MININTER, y su configuración se puede pasar a su NGINX casi sin cambios.
- **Costo:** un contenedor más (`certbot`), un script para la CA local y la ruta protegida del APK (unas horas más dentro de DESPLIEGUE-01). Estimado: 1 día de DEV, medio del TESTER y medio del LEAD (detalle en la [evaluación](../evaluaciones/PA-37-39-stack-mininter.md)).
- **Costo:** los pasos de HU-04 v3 para el teléfono de pruebas cambian de origen de la CA, y el acta de eliminación del cierre debe nombrar la CA nueva.
- **Costo:** el proxy deja de servir solo la API. El TESTER prueba que sin credencial la descarga responde 401, que con credencial descarga exactamente el APK, que cualquier otra ruta bajo `/descargas/` responde 404 y que la clave del probador no queda en los logs.
- **Riesgo:** quien tenga la credencial puede reenviarla. Es aceptable para un APK con datos sintéticos que, sin usuario de la app, no consulta nada. La credencial se cambia si se filtra.
- **Riesgo:** si se olvida el `client_max_body_size`, HU-05 recibe un 413 del proxy que la API no ve. La app debe mostrarlo como error controlado, nunca como "sin coincidencia" (regla 7). El TESTER lo incluye en el contrato de HU-05.

## Decisiones del humano (2026-11-24, vía PM)

1. NGINX reemplaza a Caddy.
2. El APK de la demo se descarga desde una ruta protegida del VPS, servida por NGINX (punto 5).
