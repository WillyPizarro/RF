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

### M-2 (2026-11-19) — Revisión del UX: mejoras sin cambio de contrato

**No reemplaza nada.** El UX aprobó con 4 observaciones MEJORA (`docs/ux/revisiones/HU-03-07.md`, commit `8aa120f`). La 1 y la 3 cambian textos visibles y esperan la decisión del humano: si se aprueban, llegan como una versión del contrato en una M-n siguiente.

- **DEV — hacer ahora, sin tocar ningún texto:**
  - **Observación 2:** el ⚠ en el aviso de error de BIT-01, oculto para el lector de pantalla, como en PLA-07.
  - **Observación 4:** `keyboardType="numbers-and-punctuation"` en "Desde" y "Hasta" de BIT-01.
  - **Capturas:** el registro `ERROR_FUENTE` de las capturas de BIT-01 y BIT-02 tiene que llevar un usuario real (CONTRATO-HU-07 §2), no "sistema".
  - **Entrega:** espera la M-n de la versión del contrato antes de entregar, para entregar todo junto.
- **TESTER:** si tus datos de Jest tienen un `ERROR_FUENTE` sin usuario, corrígelos (§2: lleva los mismos campos que la consulta). La suite completa espera su M-n.

### M-3 (2026-11-19) — CONTRATO-HU-03 v4 y CONTRATO-HU-07 v3

**Reemplaza** a M-1 en las versiones: los documentos de trabajo ahora son CONTRATO-HU-03 **v4** y CONTRATO-HU-07 **v3**, aprobados por el humano (vía PM), a partir de la revisión del UX.

- **HU-07 v3 (§5):**
  - **BIT-02:** el título es "Registro #<primeros 8 caracteres del id>", y el id completo va en el campo "ID" del detalle.
  - **Filtros de BIT-01:** se fijan sus textos: "Filtros", "Usuario", "Desde", "Hasta", "Tipo", "Resultado", la ayuda "dd/mm/aaaa" y "Aplicar filtros".
  - **Fecha inválida:** muestra "Use fechas con el formato dd/mm/aaaa." y no envía la solicitud.
- **HU-03 v4 (§6, PLA-01 sin catálogo):** si falla `GET /v1/motivos`, se muestra el error de PLA-07 ("No se pudo completar la consulta; intente nuevamente", con "Reintentar" y "Volver") y no se puede consultar.
- **DEV:** cumple las dos versiones, junto con la M-2. Al terminar: `ENTREGA DEV` con el commit, el informe actualizado y capturas nuevas de BIT-01 (filtros, error de fecha y error de carga), BIT-02 y PLA-01 sin catálogo.
- **TESTER:** agrega las pruebas de las dos versiones. La suite completa espera su M-n.

### M-4 (2026-11-19) — Suite completa

**No reemplaza nada.** El UX dio su aprobación final (`docs/ux/revisiones/HU-03-07.md`, commit `1e9facd`). El commit definitivo del DEV es `b82a63a`, sobre CONTRATO-HU-03 v4 y CONTRATO-HU-07 v3 (siguen vigentes HU-08 v4, HU-01 v5 y HU-02 v3).

- **TESTER:** antes de correr, agrega las pruebas de HU-03 v4 y HU-07 v3 si todavía no están (M-3). Después corre la suite completa **una sola vez** sobre la punta de `hu-03`:
  - **Arranque:** con `--build` y los dos archivos de compose, **con el proxy en el puerto alterno** (`PROXY_PUERTO_HTTP` y `PROXY_PUERTO_HTTPS` en `infra/.env`).
  - **pytest de la API** con `PROXY_DISPONIBLE=1`. Las 34 pruebas del proxy tienen que correr, no omitirse.
  - **pytest de los simuladores**, en el contenedor y en el anfitrión, para la regresión de HU-08.
  - **Jest de la app.**
  - **Al terminar:** `api` vuelve a `infra/.env`, y mandas `ENTREGA TESTER` con el informe final.
- **DEV:** no hagas más commits en `hu-03` salvo que el LEAD te los pida.
