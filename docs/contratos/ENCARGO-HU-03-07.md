# ENCARGO LEAD → TESTER y DEV — HU-03 + HU-07

**Documentos de trabajo:** `docs/contratos/CONTRATO-HU-03.md` **v2** y `docs/contratos/CONTRATO-HU-07.md` **v1**, aprobados por el humano el 2026-11-19. Son la única spec: lo que no dicen no se supone, se pregunta. Los contratos anteriores (HU-08 v4, HU-01 v5, HU-02 v3) siguen vigentes y no se pueden romper.
**Rama:** `hu-03`, creada desde `main` en `b8e3210` (ya incluye HU-08, HU-01 y HU-02). El TESTER y el DEV trabajan en la misma rama, cada uno en sus rutas. Las dos HUs se construyen juntas y tienen un solo veredicto (CONTRATO-HU-03, decisión 1).
**Plazo:** construcción del 28-nov al 8-dic-2026, con veredicto antes del demo del 10-dic. Si terminan antes, mejor.
**Pasa por UX:** sí. Las pantallas son:
- PLA-01 a PLA-07 y PLA-08 (placa no registrada, wireframe del UX en `befd3d7`);
- ERR-01, que se construyó en HU-02 y se verifica aquí;
- BIT-01 y BIT-02;
- HOME-01 con la opción "Consultar placa" ya habilitada.

El UX revisa las capturas de Jest contra los wireframes. Las del emulador quedan `NO VERIFICADO`, como en HU-01.

## Reglas

1. Solo tocas las rutas que `AGENTS.md` asigna a tu rol (las repiten los contratos en "Rutas de cada rol"; las migraciones de `services/api/alembic/` son del DEV).
2. Commits solo de tus rutas, con prefijo `[TESTER]` o `[DEV]` y **sin** la línea `Co-Authored-By`. Sin push y sin merge.
3. No mires ni preguntes por el trabajo del otro rol. Las dudas van al LEAD: `herdr agent prompt lead "PREGUNTA <ROL>: <pregunta>"`. La respuesta sale del contrato o se escala al humano; si cambia algo, llega como una versión nueva del contrato.
4. No toques `Empezar.txt` ni lo incluyas en commits.
5. Ninguna clave en el repositorio (`CLAVE_USUARIOS_PRUEBA` vive solo en `infra/.env`). Ninguna foto en el repositorio. Solo las placas sintéticas de HU-08 (`ZZA-101`, `ZZB-201`, `ZZZ-999`…).
6. Reglas de negocio de `AGENTS.md`, en especial:
   - la 1: la palabra prohibida;
   - la 2: el motivo es obligatorio;
   - la 7: **ningún error se convierte en "sin requisitoria"**.
7. Arranque de referencia: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env up -d --build`. Usa siempre los dos archivos.
8. **Proxy:** el puerto 80 de esta máquina lo ocupa `http.sys` de Windows. En esta rama se arregla (ver "Puerto alterno del proxy"). Hasta que esté hecho, lo que se pueda probar dentro de la red interna (`http://api:8000`) se prueba ahí.

## Puerto alterno del proxy (decisión del humano, 2026-11-19)

No cambia ningún contrato: es configuración del entorno local. Viene de la aceptación del veredicto de HU-01/02.

- **DEV**, en `infra/`:
  - **Configuración:** los puertos que publica el proxy se configuran con variables, `PROXY_PUERTO_HTTP` y, si hace falta, `PROXY_PUERTO_HTTPS`. Quedan documentadas en `infra/.env.example` con un valor local alterno (por ejemplo `8080` y `8443`).
  - **Valores por defecto:** sin las variables, se publican 80 y 443, que es lo que se usa en el VPS.
  - **En esta máquina:** el proxy tiene que arrancar sano y servir `/v1/salud`.
  - **Informe:** en tu informe va la URL local que queda (por ejemplo `https://localhost:8443`).
- **TESTER**, en `services/api/tests/`:
  - **Qué pruebas:** las 33 pruebas que pasan por el proxy (`sistema_sano`, `test_red.py`, `test_contrato_openapi.py`…) y `test_la_clave_no_queda_en_los_logs_del_proxy`.
  - **Cómo:** usan esa URL a través de las variables (`--url-base` o `URL_BASE_PRUEBAS` ya existen), sin escribir el puerto en el código.
  - **La M-8 de HU-01/02:** queda solo como respaldo.
- **Condición del veredicto:** desde el veredicto de HU-03/07, esas 34 pruebas tienen que correr **en verde**, no como `NO VERIFICADO`. El LEAD corre la suite final con `PROXY_DISPONIBLE=1`.

## Qué entrega cada uno

- **TESTER:** pruebas automatizadas de cada caso de los dos contratos:
  - **pytest** para la API, la fuente de placas y sus modos de falla, la tabla `bitacora` y el rol `api_app`;
  - **Jest con RNTL** para las pantallas.

  Incluye también:
  - lo de HU-08 que pasó a esta HU: CONTRATO-HU-03 §3 y §4, con el mock de Prism generado desde `contratos/fuentes/placas.yaml`;
  - ERR-01 (CONTRATO-HU-03 §6, fila `403`);
  - la matriz de `403 SIN_PERMISO` + `ACCESO_DENEGADO` de CONTRATO-HU-02 §2, ahora que hay rutas por rol;
  - el fail-closed de CONTRATO-HU-01 §5 (`503` sin registro), que pasó a HU-07;
  - el Jest que faltó en HU-01/02: retomar la sesión al abrir la app con `/v1/me` → `401 SESION_VENCIDA` muestra AUTH-03.

  Informe en `informes/TESTER-HU-03-07.md`, con cada caso en verde, rojo o `NO VERIFICADO`, con evidencia.
- **DEV:** la implementación que cumple los dos contratos, con:
  - el OpenAPI y los tipos de la app regenerados;
  - `infra/.env.example` al día;
  - la migración de `bitacora` con el rol `api_app` y el trigger;
  - el puerto alterno del proxy;
  - en HOME-01, el ícono 🚗 de "Consultar placa" (revisión UX de HU-01/02, observación 2; el 👤 de "Verificar rostro" queda para HU-05). No toques ningún texto.

  Informe en `informes/DEV-HU-03-07.md`: qué hizo, dónde y cómo se arranca. Además, **capturas de Jest para el UX** de cada pantalla, guardadas fuera del repositorio; en el informe indica la ruta local donde quedaron.

## Orden del cierre

1. `ENTREGA DEV` con el informe y las capturas.
2. El LEAD le pasa las capturas al UX. Si hay correcciones, vuelven al DEV como una M-n.
3. Con la aprobación del UX, el LEAD da la orden (en una M-n) de la **suite completa, una sola vez**, sobre el commit definitivo.
4. `ENTREGA TESTER` con el informe final.

Mientras tanto, el TESTER puede escribir y correr sus pruebas contra lo que haya; la corrida que cuenta es la del punto 3.

## Aviso de vuelta

Al terminar: `herdr agent prompt lead "ENTREGA <ROL>: <resumen corto> — informes/<ROL>-HU-03-07.md"`.

## Instrucciones del ciclo (M-n)

Aquí se agregan las aclaraciones durante el ciclo (M-1, M-2, …). Cada una dice qué reemplaza. Si recibes "lee M-n del encargo", es esta sección.

### M-1 (2026-11-19) — CONTRATO-HU-03 v3 y CONTRATO-HU-07 v2

**Reemplaza** la versión del encabezado: los documentos de trabajo ahora son CONTRATO-HU-03 **v3** y CONTRATO-HU-07 **v2**, aprobados por el humano (vía PM). Responden a las preguntas (1) y (2) del TESTER:

- **HU-03 v3:** `GET /v1/motivos` agrega `"formato_placa": {"regex": …, "descripcion": …}` con los valores de `PLACA_FORMATO_REGEX` y `PLACA_FORMATO_DESCRIPCION`. PLA-03 valida en la app con esa regex y muestra esa descripción sin enviar nada.
- **HU-07 v2:** la migración se corre con `docker compose … run --rm api alembic upgrade head`, y la base destino va en `MIGRACION_DATABASE_URL` (rol dueño, en `infra/.env`, nunca versionada; en `.env.example` sin clave). Si falta, usa la base del proyecto.
- **DEV:** cumple las dos.
- **TESTER:** ya puedes escribir las pruebas que dependen de esto. Para el conteo de reintentos sigue valiendo mi respuesta a tu pregunta (3).
