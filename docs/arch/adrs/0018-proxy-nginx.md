# ADR 0018: NGINX en lugar de Caddy como proxy TLS

## Estado

**Propuesto (2026-11-24).** Lo pidió el PM (PRD PA #37: "NGINX reemplaza a Caddy", decisión del humano). Si se acepta, **reemplaza** el servicio `proxy` del punto 1 del [ADR-0009](0009-despliegue.md). El resto del ADR-0009 (VPS, docker compose, Supabase en la nube, entrega con manual) no cambia.

## Contexto

- El `proxy` de hoy (`infra/Caddyfile`, `infra/docker-compose.yml`, imagen `caddy:2.10`) hace tres cosas: termina TLS con certificado automático (ACME en el VPS, CA interna con `DOMINIO=localhost`), enruta **solo** `/v1/*` hacia `api:8000` y responde 404 a todo lo demás (SPRINT0 M-1 G; `/openapi.json` no se expone).
- Es el único servicio que publica puertos (80 y 443, o `PROXY_PUERTO_HTTP` y `PROXY_PUERTO_HTTPS` en local).
- Dependen del proxy: la prueba `test_la_clave_no_queda_en_los_logs_del_proxy` (CONTRATO-HU-01 §5), su repetición obligatoria sobre el VPS (`docs/contratos/PENDIENTES.md`), y los pasos de HU-04 v3 para exportar la CA local del contenedor `proxy` e instalarla en el teléfono de pruebas.
- HU-05 enviará el recorte del rostro en el cuerpo de la solicitud. Caddy no limita el tamaño del cuerpo por defecto; **NGINX sí: 1 MB** (`client_max_body_size`).

## Decisión (propuesta)

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

## Alternativas consideradas

- **Mantener Caddy.** Ya funciona, tiene HTTPS automático y no requiere `certbot`. Se descarta porque el humano decidió el 2026-11-24 usar NGINX, el estándar del MININTER para publicar.
- **NGINX sin TLS, detrás de un balanceador del MININTER que termine TLS.** Es como lo publicaría la entidad en producción. Se descarta para el MVP porque el demo vive en el VPS del proveedor. Queda en el manual como variante.
- **NGINX con el módulo ACME nativo (`ngx_http_acme_module`).** Evitaría `certbot`. Se descarta por ahora porque es reciente y no viene en todas las imágenes oficiales. **NO VERIFICADO:** disponibilidad en la imagen estable que fije el DEV.

## Consecuencias

- El proxy queda en el stack del MININTER, y su configuración se puede pasar a su NGINX casi sin cambios.
- **Costo:** un contenedor más (`certbot`) y un script para la CA local. Estimado: 1 día de DEV, medio del TESTER y medio del LEAD (detalle en la [evaluación](../evaluaciones/PA-37-39-stack-mininter.md)).
- **Costo:** los pasos de HU-04 v3 para el teléfono de pruebas cambian de origen de la CA, y el acta de eliminación del cierre debe nombrar la CA nueva.
- **Riesgo:** si se olvida el `client_max_body_size`, HU-05 recibe un 413 del proxy que la API no ve. La app debe mostrarlo como error controlado, nunca como "sin coincidencia" (regla 7). El TESTER lo incluye en el contrato de HU-05.
