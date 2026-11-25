# ADR 0009: Despliegue en un VPS con docker compose y Supabase en la nube

## Estado

Aceptado (2026-11-18). **Precisado el 2026-11-24 (PA #37 y #38, decisiones del humano):** el [ADR-0018](0018-proxy-nginx.md) reemplaza Caddy por NGINX en el punto 1 y agrega la descarga protegida del APK; el [ADR-0019](0019-servicios-python-motor-aislado.md) agrega el servicio interno `motor`; el [ADR-0017](0017-app-movil-flutter-mlkit.md) reemplaza el build de EAS del punto 4. El punto 2 (Supabase en la nube) no cambia en el MVP: Keycloak se entrega solo documentado ([ADR-0020](0020-keycloak-al-final.md)).

## Contexto

- PRD › Plazo y entrega: el proveedor define el stack y aloja el desarrollo y el demo; el MININTER recibe el código fuente y el manual de instalación al cierre (PA #8 y #17, **pendientes de aceptación escrita**).
- El encargo incluye "despliegue en ambiente autorizado" y pruebas de desempeño.
- El análisis de factibilidad advierte que un proyecto gratuito de Supabase se pausa tras días sin uso y que un servicio gratuito de Render se duerme.
- ADR-0004: el motor biométrico corre dentro de la API, que al arrancar carga OpenCV, los modelos ONNX y los embeddings de la galería. Un servicio que se duerme hace muy lento el primer request.
- ADR-0006: los simuladores son un contenedor aparte, alcanzable solo por la red interna. ADR-0008: las fotos de la galería se guardan cifradas en el almacenamiento del simulador, y todo el ambiente se borra al cierre.

## Decisión

1. **Ambiente del demo y de pruebas:** un **VPS pequeño pagado** (2 vCPU y 4 GB de RAM como referencia, alrededor de US$ 6–12 al mes) con **docker compose**:
   - `api` (FastAPI con el motor biométrico);
   - `simuladores` (FastAPI con los datos sintéticos y la galería cifrada en un volumen);
   - `proxy` (Caddy, con HTTPS automático; es lo único que expone puertos: 80 y 443).

   `api` y `simuladores` comparten una red interna, y `simuladores` no publica ningún puerto.

2. **Supabase en la nube** (Auth y Postgres), en la región más cercana disponible (referencia: São Paulo). Sus credenciales solo las tiene `api`.

3. **Lo que se entrega al MININTER:** el mismo `docker-compose.yml`, los Dockerfiles, las migraciones SQL (esquema, roles, trigger de la bitácora), los scripts de carga de datos sintéticos y usuarios, los contratos OpenAPI y un manual de instalación. El manual describe dos variantes: con Supabase en la nube o con Supabase autoalojado (su docker compose oficial) o cualquier otro Postgres más un proveedor OIDC (ADR-0001).

4. La app móvil se distribuye como **build interno** (APK de EAS para Android; TestFlight solo si PA #12 confirma iOS). No se publica en las tiendas.

5. Los secretos (llaves de Supabase, la llave de cifrado de la captura, el JWT secret o el JWKS) viven en variables de entorno del VPS y nunca en el repositorio.

## Alternativas consideradas

- **Planes gratuitos (Render o Hugging Face Spaces) más Supabase gratis.** Costaban cero. Se descartaron porque el servicio se duerme y el primer request, al cargar OpenCV y los modelos, tarda decenas de segundos. Eso pone en riesgo el demo y deja sin sentido las pruebas de desempeño.
- **Todo autoalojado en el VPS, incluido Supabase.** Probaba exactamente lo que se entrega. Se descartó porque el stack de Supabase son unos 10 contenedores, necesita un VPS más grande y cuesta 1 o 2 días de operación. Queda como variante documentada en el manual.

## Consecuencias

- El demo es estable (no se duerme) y las pruebas de desempeño miden un ambiente real, con números que se pueden reproducir.
- Lo que se entrega es el mismo compose que se probó.
- **Costo:** hay un gasto mensual (VPS, y quizá Supabase Pro si el plan gratuito se pausa en la semana de validación) que no estaba en "herramientas gratuitas".
- **Costo:** el proveedor administra el servidor (parches, firewall, respaldos) durante el proyecto.
- **Costo / riesgo:** Postgres con la bitácora y las capturas pendientes cifradas vive en la nube de Supabase, fuera del Perú. Con datos sintéticos y del equipo con consentimiento (ADR-0008) es defendible, pero queda en la evaluación de impacto.
- **Abierto:** si el MININTER no acepta la propuesta (PA #17) y exige su propio ambiente desde el inicio, este ADR se vuelve a abrir.
