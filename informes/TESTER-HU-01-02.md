# Informe TESTER — HU-01 + HU-02 (iniciar sesión y acceso por rol)

**Contratos:** `docs/contratos/CONTRATO-HU-01.md` **v5** y `docs/contratos/CONTRATO-HU-02.md` **v3** · **Encargo:** `docs/contratos/ENCARGO-HU-01-02.md` (M-1 a M-7) · **Rama:** `hu-01`
**Suite completa (M-5), una sola vez:** 2026-11-19/20, sobre la punta de `hu-01` (`7053c9c`, que incluye el commit definitivo del DEV `c1b432f` y mis pruebas `af516e4`). Arranque con `up -d --build` y los dos archivos de compose; usuarios cargados con `python -m app.cargar_usuarios` (exit 0). El proxy no arrancó: el puerto 80 lo ocupa `http.sys` (encargo, regla 8).

## Vuelta 1 del veredicto (M-6)

- **A2 (se apartó la prueba):** `test_hu01_login.py::test_usuario_inactivo_identico` y `test_hu01_bitacora_config.py::test_carga_de_usuarios_idempotente` corren ahora con la configuración **intentos alto** (`BLOQUEO_INTENTOS=1000`, el resto por defecto; §6: cambiar parámetros sin tocar código). Así ningún fallo de `inactivo1` alcanza el umbral, sea cual sea su contador previo. No se apoyan en lo que pasa con el contador al terminar un bloqueo (está en pregunta al humano). Si hubiera un bloqueo **vigente** de antes de la prueba, fallan como `PRECONDICIÓN (no es un resultado del código)`, con su `bloqueado_hasta`.
- **A3 (prueba obsoleta):** `test_contrato_sin_rutas_de_negocio` se cambió por `test_contrato_openapi.py::test_contrato_rutas_vigentes`. El contrato publicado declara exactamente `/v1/salud` (GET), `/v1/auth/login`, `/v1/auth/refresh`, `/v1/auth/logout` (POST) y `/v1/me` (GET).
- **Corrida de lo tocado** (`test_contrato_openapi.py`, `test_hu01_login.py`, `test_hu01_bitacora_config.py`, `--integracion`): **29 en verde, 0 rojos, 2 omitidas** (NO VERIFICADO ya registrados) y **2 errores de entorno** (`test_contrato_publicado_identico_al_servido` y `test_proxy_no_expone_openapi` pasan por el proxy, igual que R4). En verde: `test_contrato_rutas_vigentes`, `test_usuario_inactivo_identico` y `test_carga_de_usuarios_idempotente`. Al terminar, `api` volvió a `infra/.env` (`BLOQUEO_INTENTOS=5`).
- **v5 (M-7), fallo después del bloqueo:** `test_hu01_bloqueo.py::test_fallo_despues_del_bloqueo_empieza_de_nuevo`, en tres variantes (clave incorrecta de `agente2`, usuario inexistente, `inactivo1`) y con la configuración corta. Primero lleva la cuenta a un bloqueo por el camino del §2 (fallos hasta el `423`) y espera `bloqueado_hasta`. Después comprueba que el fallo siguiente es `401 CREDENCIALES_INVALIDAS` con `LOGIN_FALLIDO` (no `423`), que los fallos 2 a 4 siguen en `401` y que el 5.º vuelve a bloquear. **3 en verde.** La API volvió a `infra/.env` (`BLOQUEO_DURACION_S=900`, `SESION_INACTIVIDAD_S=600`).
- **A1 (DEV, `1e6dd71`):** Jest completo de la app (`npx jest --ci`): **33 en verde, 0 rojos** (2 suites). `AUTH-03 › un 401 SESION_VENCIDA de la API también cierra la sesión con el aviso` pasó a **VERDE**.

## Resultado

| Corrida | Comando | Resultado |
|---|---|---|
| API, bitácora y configuración | `pytest services/api/tests --integracion -rA` (52 min) | **HU-01/HU-02: 52 en verde, 2 rojos, 3 omitidas (NO VERIFICADO).** Sprint 0: 9 en verde, 2 rojos, 32 con error de entorno (proxy caído) |
| App | `npx jest --ci` en `apps/movil` | **32 en verde, 1 rojo** (33 en total; incluye las 10 de `PantallaEstado` del Sprint 0) |
| Simuladores, regresión de HU-08, en el contenedor | `docker compose … run --rm -T --no-deps simuladores pytest -rA` | 115 en verde, 0 rojos, 27 omitidas (las del anfitrión) |
| Simuladores, regresión de HU-08, desde el anfitrión | `pytest services/simuladores/tests --integracion -rA` | 136 en verde, 0 rojos, 6 omitidas. El origen de fotos quedó vacío |

Al terminar, `api` volvió a `infra/.env` (comprobado: `SESION_INACTIVIDAD_S=600`, `TOKEN_ACCESO_VIGENCIA_S=900`, `BLOQUEO_INTENTOS=5`, `BLOQUEO_DURACION_S=900`). La clave de los usuarios de prueba se leyó de `infra/.env` y no se escribió en ningún archivo ni en este informe.

## Rojos para que arbitre el LEAD

| # | Prueba | Qué pasó | Lectura del TESTER (decide el LEAD) |
|---|---|---|---|
| R1 | Jest `HU-01 AUTH-03 › un 401 SESION_VENCIDA de la API también cierra la sesión con el aviso` | Login `200`; después `GET /v1/me` (y `/v1/auth/refresh`) responden `401 SESION_VENCIDA`. La app vuelve al login, pero muestra "No se pudo completar la operación; intente nuevamente" en vez de "Su sesión se cerró por inactividad. Ingrese de nuevo." | HU-01 §4, AUTH-03: "… o un `401 SESION_VENCIDA`" → aviso de inactividad, sin otra condición. El estímulo es el primer `/v1/me` justo después del login. Si el contrato quiso limitar el caso a solicitudes posteriores a la carga del inicio, lo tiene que decir |
| R2 | `test_hu01_login.py::test_usuario_inactivo_identico` y el último paso de `test_hu01_bitacora_config.py::test_carga_de_usuarios_idempotente` (`inactivo1` → `401`) | Respondió `423 CUENTA_BLOQUEADA`. La bitácora muestra 4 `LOGIN_FALLIDO` de `inactivo1` **anteriores a la corrida** (22:58–22:59 UTC); mi primer intento (00:21:06) fue el 5.º seguido → `423` + `CUENTA_BLOQUEADA`, y el siguiente, `423` durante el bloqueo | **Se apartó la prueba:** la API hizo lo que dice el contrato (decisiones 3 y 5: el inactivo cuenta como fallo y bloquea al 5.º). La prueba no asegura que el contador de `inactivo1` esté en 0, y un usuario inactivo nunca acierta, así que el contador no vuelve a 0 solo. El resto de `test_carga_de_usuarios_idempotente` (dos corridas sin error, mismos `id`, roles y sin imprimir la clave) pasó. Corrección propuesta: esperar a que termine el bloqueo de `inactivo1` y comprobar su `401` en un intento, o correr esas pruebas con la configuración corta. Pero el contrato no dice si el fin del bloqueo pone el contador en 0 para un usuario que no acierta |
| R3 | `test_contrato_openapi.py::test_contrato_sin_rutas_de_negocio` (Sprint 0) | El OpenAPI publicado tiene `/v1/auth/login`, `/v1/auth/refresh` y `/v1/auth/logout` | **Prueba obsoleta:** verificaba el esqueleto del Sprint 0 ("sin rutas de negocio"); desde HU-01 esas rutas existen por contrato. Corrección propuesta: retirarla o cambiarla por la lista de rutas vigente |
| R4 | `test_red.py::test_simuladores_no_responde_desde_el_anfitrion` (Sprint 0) | `ConnectionRefusedError` al pedir `https://localhost/salud`: el proxy no corre | **Entorno:** con el proxy caído la prueba no se puede hacer (y su cliente no trata la conexión rechazada). NO VERIFICADO (entorno). El aislamiento de `simuladores` sí quedó verificado en la regresión de HU-08 (§8, sin puerto publicado) |

**32 errores del Sprint 0 (entorno):** `test_salud.py`, `test_errores.py`, `test_logs.py` (2 de 3), `test_dependencias.py` y 2 de `test_contrato_openapi.py` usan la fixture `sistema_sano`, que espera `GET https://localhost/v1/salud` a través del proxy; el proxy no arrancó (puerto 80, regla 8) y cada una falló con `/v1/salud no volvió a 200 en 90s`. No es un resultado del código. Lo equivalente por la red interna sí se verificó en HU-01: formato de error estándar con `id_traza` = `X-Id-Traza` (422 y los 401/423), y la palabra prohibida.

## Caso del contrato → prueba → estado

### HU-01 (v5) — API (`services/api/tests/`)

| § | Caso | Prueba | Estado |
|---|---|---|---|
| 1 | Camino feliz, los 4 usuarios activos con su rol, `expira_en` 900, `inactividad_s` 600 | `test_hu01_login.py::test_camino_feliz` (4) | VERDE |
| 1 | `LOGIN_OK` con `usuario_id`, `rol`, `ocurrido_en` del servidor, `id_traza`, `es_sintetico` | `::test_camino_feliz_deja_login_ok` | VERDE |
| 1 | Clave incorrecta → 401 `CREDENCIALES_INVALIDAS` + `LOGIN_FALLIDO` | `::test_clave_incorrecta` | VERDE |
| 1 | Usuario inexistente idéntico; `usuario_id` nulo y el texto en `parametros` | `::test_usuario_inexistente_identico` | VERDE |
| 1 | Usuario inactivo idéntico (decisión 3) | `::test_usuario_inactivo_identico` | VERDE en la vuelta 1 (A2). En la vuelta 0: ROJO (R2, se apartó la prueba) |
| 1 | Cuerpo inválido → 422 `SOLICITUD_INVALIDA`, formato estándar, sin evento (**pendiente del Sprint 0**) | `::test_cuerpo_invalido_422` (6 cuerpos) | VERDE |
| 1 | Cuerpo inválido no cuenta como intento (decisión 4) | `test_hu01_bloqueo.py::test_cuerpo_invalido_no_cuenta_como_intento` | VERDE |
| 1 | Éxito reinicia el contador | `::test_exito_reinicia_el_contador` | VERDE |
| 2 | 5.º fallo → 423 con `bloqueado_hasta` UTC; `LOGIN_FALLIDO` + `CUENTA_BLOQUEADA` | `::test_quinto_fallo_bloquea` | VERDE |
| 2 | Clave correcta o incorrecta durante el bloqueo: mismo 423 y mismo `bloqueado_hasta`; `LOGIN_FALLIDO` con `codigo_error` `CUENTA_BLOQUEADA` | `::test_durante_el_bloqueo_clave_correcta_o_incorrecta_identicas` | VERDE |
| 2 | Fin del bloqueo → 200 y contador en 0 | `::test_fin_del_bloqueo` | VERDE |
| 2 | Usuario inexistente también se bloquea (decisión 5) | `::test_usuario_inexistente_tambien_se_bloquea` | VERDE |
| 2 | Fallo después del bloqueo → `401 CREDENCIALES_INVALIDAS` con `LOGIN_FALLIDO`; el contador empieza de nuevo (v5) | `::test_fallo_despues_del_bloqueo_empieza_de_nuevo` (3 variantes) | VERDE (vuelta 1) |
| 2 | Valores por defecto: 5 intentos, 900 s | `::test_valores_por_defecto_5_intentos_15_min` | VERDE |
| 3 | Renovar → 200 con la forma del login | `test_hu01_sesion.py::test_renovar` | VERDE |
| 3 | Sin token / token basura / firma inválida / logout sin token → 401 `NO_AUTENTICADO` | `::test_sin_token`, `::test_token_basura` (2), `::test_firma_invalida`, `::test_logout_sin_token` | VERDE |
| 3 | Token de acceso vencido → 401 `NO_AUTENTICADO` | `::test_token_vencido` | VERDE |
| 3 | Inactividad en el servidor (solicitud y renovación) → 401 `SESION_VENCIDA`, evento, sesión invalidada | `::test_inactividad_en_una_solicitud`, `::test_inactividad_en_la_renovacion` | VERDE |
| 3 | La actividad mantiene la sesión | `::test_la_actividad_mantiene_la_sesion` | VERDE |
| 3 | Una renovación exitosa cuenta como actividad (v3) | `::test_la_renovacion_cuenta_como_actividad` | VERDE |
| 3 | Cerrar sesión → 204, `LOGOUT`, el `token_renovacion` deja de servir | `::test_cerrar_sesion` | VERDE |
| 5 | Campos de cada evento; `id_traza` = `X-Id-Traza` | `test_hu01_bitacora_config.py::test_campos_de_cada_evento`, `::test_id_traza_del_evento_igual_a_la_cabecera` | VERDE |
| 5 | Sin registro no hay sesión (503) | — | **NO VERIFICADO**: se prueba en HU-07 (decisión 2) |
| 5 | La clave no queda en la bitácora ni en los logs de la API | `::test_la_clave_no_queda_en_la_bitacora`, `::test_la_clave_no_queda_en_los_logs_de_la_api` | VERDE |
| 5 | Ni en los logs del proxy | `::test_la_clave_no_queda_en_los_logs_del_proxy` | **NO VERIFICADO (entorno)**: el proxy no corre |
| 6 | Parámetros en `.env.example`, con sus valores y marcados como provisionales | `::test_parametros_en_env_example` (4) | VERDE |
| 6 | Cambiarlos no requiere tocar código | `::test_cambiar_parametros_no_toca_codigo` y todas las pruebas con configuración corta | VERDE |
| 6 | Carga de usuarios idempotente, usuarios fijos, sin imprimir la clave | `::test_carga_de_usuarios_idempotente` | VERDE en la vuelta 1 (A2) |
| 6 | `CLAVE_USUARIOS_PRUEBA` en `infra/.env` y no versionada | `::test_clave_de_usuarios_desde_el_entorno` | VERDE |

### HU-01 (v5) — App (`apps/movil/__tests__/HU01_HU02.test.tsx`)

| Caso | Prueba | Estado |
|---|---|---|
| AUTH-01: textos, franja y `testID="app-raiz"` | `AUTH-01 › sin sesión muestra…` | VERDE |
| La app usa `EXPO_PUBLIC_API_URL` + `/v1/auth/login` con el `fetch` global (§4 bis) | `AUTH-01 › envía usuario y clave…` | VERDE |
| Login correcto → inicio de su rol; el token va a SecureStore | `AUTH-01 › login correcto…` | VERDE |
| AUTH-01 vacío (v4): "Ingrese su usuario y su clave" y ninguna solicitud de login | `AUTH-01 vacío (v4) › …` (6 combinaciones) | VERDE |
| AUTH-02: mensaje, el usuario queda escrito, la clave se vacía, sin intentos restantes | `AUTH-02 › …` | VERDE |
| AUTH-04: hora local HH:MM y minutos desde `bloqueado_hasta`, clave vacía, "Ingresar" activo | `AUTH-04 › …` | VERDE (el contrato no fija el redondeo de los minutos: se acepta el entero por abajo o por arriba) |
| Otro error (red, 500, 503) → mensaje genérico, nunca el de credenciales | `otro error › …` (3) | VERDE |
| AUTH-03 por inactividad, con el tiempo de `inactividad_s` del login | `AUTH-03 › sin tocar la pantalla…` | VERDE |
| AUTH-03: SecureStore sin claves, "atrás" no vuelve, otro usuario no ve datos del anterior, no se reenvía el token viejo (v2) | `AUTH-03 › tras el cierre…` | VERDE |
| AUTH-03 por `401 SESION_VENCIDA` | `AUTH-03 › un 401 SESION_VENCIDA…` | VERDE en la vuelta 1 (A1, `1e6dd71`). En la vuelta 0: ROJO (R1) |
| Sesión activa con `touchStart` sobre `app-raiz` (v2) | `AUTH-03 › sesión activa…` | VERDE |
| Capturas del emulador | — | **NO VERIFICADO** (M-3: el UX revisó solo las de Jest) |

### HU-02 (v3)

| § | Caso | Prueba | Estado |
|---|---|---|---|
| 1 | Perfil `GET /v1/me` de los 4 usuarios | `test_hu02_perfil_roles.py::test_perfil` (4) | VERDE |
| 1/2 | Sin token → 401 y sin `ACCESO_DENEGADO` (decisión 2) | `::test_sin_token_401_sin_acceso_denegado` | VERDE |
| 1 | Token manipulado para declarar otro rol → 401; el rol enviado por el cliente se ignora | `::test_rol_manipulado_no_valida` (2), `::test_rol_enviado_por_el_cliente_se_ignora` | VERDE |
| 2 | Matriz de 403 `SIN_PERMISO` + `ACCESO_DENEGADO`; "Sin efecto" | `::test_matriz_403_sin_permiso` (skip) | **NO VERIFICADO**: no hay rutas de rol; pasa a HU-03 y HU-07 (decisión 3) |
| 3 | Inicio del agente, del revisor y del supervisor (textos, opciones deshabilitadas, nada de otros roles) | Jest `HU-02 — inicio por rol › agente/revisor/supervisor` | VERDE |
| 3 | El menú sale de `GET /v1/me` | Jest `› el menú sale de GET /v1/me…` | VERDE |
| 3 | "Salir": logout con el token, SecureStore vacío, AUTH-01 sin mensaje, "atrás" no vuelve | Jest `› Salir…` | VERDE |
| 3 | ERR-01 | — | **Diferido a HU-03 (v3)** |

## Cómo se corren

| Parte | Comando | Notas |
|---|---|---|
| API y bitácora | `pytest services/api/tests --integracion` desde el anfitrión, con el sistema arrancado con `docker-compose.yml` + `docker-compose.fotos.yml` | Las peticiones salen desde dentro del contenedor `api` a `http://api:8000` (regla 8). La bitácora se lee con `psql` dentro de `db` (decisión 2). Las pruebas de tiempos recrean **solo** `api` (`--no-deps`) con un archivo de entorno temporal fuera del repositorio, y al final vuelven a `infra/.env` |
| App | `npx jest` en `apps/movil` | Monta el export por defecto de `App.tsx` (§4 bis). Se simulan el `fetch` global, `expo-secure-store` (en memoria) y `BackHandler.addEventListener` |

Configuraciones de la API usadas por las pruebas (cambiarlas sin tocar código es parte de §6): **por defecto** (`infra/.env`: 600 / 900 / 5 / 900); **corta** (`SESION_INACTIVIDAD_S=12`, `TOKEN_ACCESO_VIGENCIA_S=120`, `BLOQUEO_DURACION_S=12`); **token corto** (`TOKEN_ACCESO_VIGENCIA_S=6`, `SESION_INACTIVIDAD_S=600`).

## Revisión del UX

Las mejoras 1, 3 y 4 (íconos, alto de "Salir", tono del error) no cambian el contrato y no tienen prueba; la 5 es la v4 y sí la tiene. El humano aceptó que el UX revisara solo las capturas de Jest (M-3).

## Cambios al arnés del Sprint 0

- `services/api/tests/conftest.py`: `Compose` usa siempre `docker-compose.fotos.yml` (regla 7). Las pruebas se ordenan por configuración de la API, para recrearla las menos veces posible. Hay fixtures nuevas (`sistema`, `config_defecto`, `config_corta`, `config_token_corto`, `clave`).
- Nuevos `red_interna.py` (API por la red interna, bitácora y configuración) y `ayudas_hu01.py` (formas del contrato).
