# ENCARGO LEAD → TESTER y DEV — HU-01 + HU-02

**Documentos de trabajo:** `docs/contratos/CONTRATO-HU-01.md` **v1** y `docs/contratos/CONTRATO-HU-02.md` **v1**, aprobados por el humano el 2026-11-19. Son la única spec: lo que no dicen no se supone, se pregunta.
**Rama:** `hu-01`, creada desde `main` en `befd3d7`. El TESTER y el DEV trabajan en la misma rama, cada uno en sus rutas. Las dos HUs se construyen juntas y tienen un solo veredicto (CONTRATO-HU-02, decisión 1).
**Plazo:** construcción del 28-nov al 8-dic-2026, con veredicto antes del 10-dic. Si terminan antes, mejor.
**Pasa por UX:** sí. Pantallas AUTH-01 a AUTH-04, HOME-01, los inicios del revisor y del supervisor, y ERR-01. El UX revisa con capturas de Jest y del emulador, contra los wireframes.

## Reglas

1. Solo tocas las rutas que `AGENTS.md` asigna a tu rol (las repiten los contratos en "Rutas de cada rol").
2. Commits solo de tus rutas, con prefijo `[TESTER]` o `[DEV]` y **sin** la línea `Co-Authored-By`. Sin push y sin merge.
3. No mires ni preguntes por el trabajo del otro rol. Las dudas van al LEAD: `herdr agent prompt lead "PREGUNTA <ROL>: <pregunta>"`. La respuesta sale del contrato o se escala al humano; si cambia algo, llega como una versión nueva del contrato.
4. No toques `Empezar.txt` ni lo incluyas en commits.
5. Ninguna clave en el repositorio: las de los usuarios de prueba viven en `CLAVE_USUARIOS_PRUEBA`, en `infra/.env` (local, no versionado). Ninguna foto en el repositorio.
6. Reglas de negocio de `AGENTS.md`, en especial la 1 (la palabra prohibida) y la 7 (ningún error se convierte en un resultado negativo).
7. Arranque de referencia: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env up -d --build`. Usa siempre los dos archivos, para no recrear `simuladores` sin su montaje (lección del veredicto de HU-08).
8. El puerto 80 de esta máquina lo ocupa `http.sys` de Windows, así que lo que pase por el proxy puede quedar `NO VERIFICADO`. Lo que se pueda probar dentro de la red interna (`http://api:8000`) se prueba ahí.

## Qué entrega cada uno

- **TESTER:** pruebas automatizadas de cada caso de los dos contratos: pytest para la API y la tabla `bitacora`, y Jest con RNTL para las pantallas. Incluye la prueba del `422 SOLICITUD_INVALIDA` que quedó pendiente del Sprint 0 (`docs/contratos/PENDIENTES.md`). Informe en `informes/TESTER-HU-01-02.md`, con cada caso en verde, rojo o `NO VERIFICADO`, con evidencia.
- **DEV:** la implementación que cumple los dos contratos, con el OpenAPI y los tipos de la app regenerados e `infra/.env.example` al día. Informe en `informes/DEV-HU-01-02.md`: qué hizo, dónde, cómo se arranca y cómo se cargan los usuarios. Además, **capturas para el UX** de cada pantalla (de Jest o del emulador), guardadas fuera del repositorio. En el informe indica la ruta local donde quedaron.

## Orden del cierre

1. `ENTREGA DEV` con el informe y las capturas.
2. El LEAD le pasa las capturas al UX para su revisión. Si hay correcciones, vuelven al DEV como una M-n.
3. Con la aprobación del UX, el LEAD da la orden (en una M-n) de la **suite completa, una sola vez**, sobre el commit definitivo.
4. `ENTREGA TESTER` con el informe final.

Mientras tanto, el TESTER puede escribir y correr sus pruebas contra lo que haya; la corrida que cuenta es la del punto 3.

## Aviso de vuelta

Al terminar: `herdr agent prompt lead "ENTREGA <ROL>: <resumen corto> — informes/<ROL>-HU-01-02.md"`.

## Instrucciones del ciclo (M-n)

Aquí se agregan las aclaraciones durante el ciclo (M-1, M-2, …). Cada una dice qué reemplaza. Si recibes "lee M-n del encargo", es esta sección.

### M-1 (2026-11-19) — Contratos v2

**Reemplaza** la versión del encabezado: los documentos de trabajo ahora son CONTRATO-HU-01 **v2** y CONTRATO-HU-02 **v2**, aprobados por el humano. Los cambios están en sus changelogs: la nueva §4 bis de HU-01 (montaje en `apps/movil/App.tsx` sin expo-router, `fetch` global con `EXPO_PUBLIC_API_URL`, `testID="app-raiz"`, `BackHandler`), AUTH-03 observable desde afuera y qué cuenta como interacción.

- **DEV:** cumple la §4 bis.
- **TESTER:** monta `App.tsx` y verifica AUTH-03 como dice la v2.

### M-2 (2026-11-19) — CONTRATO-HU-02 v3

**Reemplaza** a M-1 en la versión de HU-02: el documento de trabajo ahora es CONTRATO-HU-02 **v3**. HU-01 sigue en v2. La pantalla ERR-01 **se construye**, pero **no se verifica** en este ciclo: su prueba pasa a HU-03.

- **DEV:** construye ERR-01 igual.
- **TESTER:** ERR-01 no entra en tu informe como caso de este ciclo; anótalo como "diferido a HU-03 (v3)".

### M-3 (2026-11-19) — CONTRATO-HU-01 v3 y revisión del UX

**Reemplaza** a M-1 en la versión de HU-01: el documento de trabajo ahora es CONTRATO-HU-01 **v3**. HU-02 sigue en v3. El cambio, en el §3: una renovación exitosa cuenta como actividad en el servidor. Es lo que ya hizo el DEV en `e6c6f22`.

- **DEV:** sin cambios. Tu entrega `e6c6f22` está en revisión del UX; no hagas commits hasta que el LEAD te pase sus observaciones.
- **TESTER:** ajusta tus pruebas de inactividad a la v3. La suite completa espera la próxima M-n.
- **Capturas:** el humano aceptó que el UX revise solo las de Jest. Las del emulador quedan `NO VERIFICADO`.

### M-4 (2026-11-19) — Revisión del UX: CONTRATO-HU-01 v4 y mejoras

**Reemplaza** a M-3 en la versión de HU-01: el documento de trabajo ahora es CONTRATO-HU-01 **v4**. HU-02 sigue en v3. El UX aprobó (`docs/ux/revisiones/HU-01-02.md`, commit `44712b9`) con 5 observaciones de tipo MEJORA. El humano decidió:

- **v4 (observación 5):** en AUTH-01, "Ingresar" con el usuario o la clave vacíos (o solo con espacios) muestra "Ingrese su usuario y su clave" y no envía la solicitud.
- **DEV — hacer ahora** (sin tocar ningún texto): la v4, más las observaciones **1** (íconos ⚠ en AUTH-02, ⓘ en AUTH-03 y 🔒 en AUTH-04, ocultos al lector de pantalla), **3** ("Salir" de al menos 48 dp de alto) y **4** (tono neutro o ámbar, no rojo, para el error de red o del servidor). La observación **2** (íconos de HOME-01) queda para HU-03 y HU-05. Al terminar: `ENTREGA DEV` con el commit, el informe actualizado y capturas nuevas de AUTH-01 (vacío), AUTH-02 a AUTH-04, AUTH-xx y un inicio.
- **TESTER:** agrega la prueba de la v4. Sigue sin correr la suite completa; espera la M-n.

### M-5 (2026-11-19) — Suite completa

**No reemplaza nada.** El UX dio su aprobación final (`docs/ux/revisiones/HU-01-02.md`, commit `12d9f78`). El commit definitivo del DEV es `c1b432f`, sobre CONTRATO-HU-01 v4 y CONTRATO-HU-02 v3.

- **TESTER:** corre la suite completa **una sola vez** sobre la punta de `hu-01`: pytest de la API (en la red interna, con tus recreaciones de `api` para los tiempos cortos y luego de vuelta a `infra/.env`), pytest de los simuladores (para comprobar que HU-08 no se rompió) y Jest de la app. Arranca con `--build` y con los dos archivos de compose. Al terminar: `ENTREGA TESTER` con el informe final.
- **DEV:** no hagas más commits en `hu-01` salvo que el LEAD te los pida.

### M-6 (2026-11-19) — Veredicto, vuelta 1

**No reemplaza nada.** Los contratos siguen en HU-01 **v4** y HU-02 **v3**. El arbitraje está en `informes/VEREDICTO-HU-01-02.md` §4.

- **DEV — A1 (se apartó el código):** HU-01 §4, AUTH-03: un `401 SESION_VENCIDA` muestra "Su sesión se cerró por inactividad. Ingrese de nuevo.", **venga de la solicitud que venga**. Eso incluye el primer `GET /v1/me` después del login y el que sigue a retomar la sesión al abrir la app. Hoy los dos caminos muestran el mensaje genérico o ningún mensaje. No toques ningún texto. Al terminar: `ENTREGA DEV` con el commit y el informe actualizado.
- **TESTER — A2 (se apartó la prueba):** `test_usuario_inactivo_identico` y el último paso de `test_carga_de_usuarios_idempotente` suponen que el contador de `inactivo1` está en 0 y no lo aseguran. Haz que lo aseguren **por un camino que el contrato fija**, por ejemplo con una configuración de la API con `BLOQUEO_INTENTOS` alto (§6). No te apoyes en lo que pasa con el contador después de que termina un bloqueo: el contrato no lo dice y está en pregunta al humano.
- **TESTER — A3 (se apartó la prueba):** `test_contrato_sin_rutas_de_negocio` quedó obsoleta desde HU-01. Cámbiala por la lista de rutas vigente (`/v1/salud`, `/v1/auth/login`, `/v1/auth/refresh`, `/v1/auth/logout` y `/v1/me`), o retírala si eso ya lo cubre otra prueba.
- **TESTER, después de A2 y A3:** corre los archivos que tocaste, y el Jest de AUTH-03 cuando llegue la entrega del DEV (el LEAD te avisa). Al terminar: `ENTREGA TESTER` con el informe actualizado. La suite completa la repite el LEAD.

### M-7 (2026-11-19) — CONTRATO-HU-01 v5

**Reemplaza** a M-4 en la versión de HU-01: el documento de trabajo ahora es CONTRATO-HU-01 **v5**. HU-02 sigue en v3. El humano respondió la pregunta de M-6: **al terminar un bloqueo, el contador empieza de nuevo**, así que el siguiente fallo es el 1 de `BLOQUEO_INTENTOS` (nueva fila en §2, "Fallo después del bloqueo").

- **DEV:** sin cambios por la v5: es lo que ya hace `services/api/app/auth.py`. Sigue con A1 de M-6.
- **TESTER:** agrega la prueba de la v5 (fallo después de `bloqueado_hasta` → `401 CREDENCIALES_INVALIDAS`, no `423`). Para A2 ya puedes apoyarte en esa regla si te sirve.

### M-8 (2026-11-19) — Pruebas que pasan por el proxy

**No reemplaza nada.** No cambia ningún contrato. Pedido del PM: las pruebas que pasan por el proxy (`https://localhost`, fixture `sistema_sano`, `test_red.py`) ya están aceptadas como `NO VERIFICADO` en esta máquina (Sprint 0 y HU-08). Esperar 90 s por cada una cuesta unos 48 min por corrida.

- **TESTER**, en tus rutas (`services/api/tests/`): antes de usar el proxy, haz un chequeo de unos 2 s (o lee una variable, por ejemplo `PROXY_DISPONIBLE=0`). Si el proxy no responde, esas pruebas se marcan `skip` con el motivo **"NO VERIFICADO: puerto 80 ocupado por http.sys"**. Nunca pueden quedar en verde sin haber corrido. Con el proxy arriba, se comportan como hoy. Documenta en tu informe cómo se activa. Si no se puede hacer sin tocar un contrato, avísame con `PREGUNTA TESTER`.
- **No corras la suite completa:** solo comprueba que esas pruebas se omiten rápido y con ese motivo. Mi corrida de la vuelta 1 sigue con el arnés anterior. Al terminar: `ENTREGA TESTER` con el commit.
