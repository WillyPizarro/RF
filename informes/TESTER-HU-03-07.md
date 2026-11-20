# Informe TESTER — HU-03 + HU-07 (consulta de placa y bitácora)

**Contratos:** `docs/contratos/CONTRATO-HU-03.md` **v4** y `docs/contratos/CONTRATO-HU-07.md` **v4** (más HU-08 v4, HU-01 v5 y HU-02 v3, vigentes) · **Encargo:** `docs/contratos/ENCARGO-HU-03-07.md` (M-1 a M-6) · **Rama:** `hu-03`
**Suite completa (M-4), una sola vez:** 2026-11-19/20, sobre la punta de `hu-03` (`c056068`, que incluye el commit definitivo del DEV `b82a63a` y mis pruebas de M-3). Arranque con `up -d --build`, los dos compose y el **proxy en el puerto alterno** (`PROXY_PUERTO_HTTP=8080`, `PROXY_PUERTO_HTTPS=8443`; `https://localhost:8443/v1/salud` → 200). Usuarios cargados con `python -m app.cargar_usuarios` (exit 0).

## Vuelta 1 del veredicto (M-5 y M-6)

Correcciones de las pruebas, según el arbitraje (`informes/VEREDICTO-HU-03-07.md` §4); ningún rojo apuntaba al código:

| # | Corrección | Prueba | Resultado |
|---|---|---|---|
| A1 | Rutas vigentes: se agregan `GET /v1/motivos`, `POST /v1/consultas/placa` y `GET /v1/bitacora` | `test_contrato_openapi.py::test_contrato_rutas_vigentes` | VERDE |
| A2 | En `latencia`, el reintento se verifica por tiempos (de 5 a 7 s dentro del contenedor `api`), y el conteo por log queda **NO VERIFICADO** con su motivo en el docstring | `test_hu03_placa.py::test_fuente_lenta` | VERDE |
| A3 | `{255,}` en la expresión de Postgres | `test_hu07_bitacora_db.py::test_sin_imagen_ni_clave` | VERDE |
| A4 | Prism con `--multiprocess=false` | `test_hu03_mock_y_roles.py::test_mock_del_contrato` | **VERDE: §4 verificado** (antes NO VERIFICADO); no quedó ningún contenedor de Prism |
| A5 | HOME-01: "Consultar placa" habilitada y "Verificar rostro" y "Mis verificaciones" deshabilitadas; "Bitácora" del supervisor habilitada | Jest `HU01_HU02.test.tsx` › `agente`, `supervisor` | VERDE |
| A6 | HU-07 v4: los filtros se despliegan tocando "Filtros" antes de buscar los campos (`desplegarFiltros`) | Jest `HU03_HU07.test.tsx` › BIT-01 (v3): filtros, fecha inválida (4) y "Aplicar filtros" | VERDE |
| A7 | "ID" sin coincidencia exacta (`/^ID(?! de captura)/`) | Jest `HU03_HU07.test.tsx` › BIT-02 (v3) | VERDE |

**Corridas de lo tocado:**
- **Jest** de `HU03_HU07.test.tsx` y `HU01_HU02.test.tsx`: **63 en verde, 0 rojos**.
- **pytest** (`--integracion`, `PROXY_DISPONIBLE=1`) de `test_contrato_openapi.py`, `test_hu03_placa.py`, `test_hu07_bitacora_db.py` y `test_hu03_mock_y_roles.py`: **64 en verde y 1 rojo esperado**. El rojo es `test_eventos_de_la_iteracion`, que exige que la **sesión** genere los 9 tipos de evento y que por eso solo vale en la suite completa (faltaron `CUENTA_BLOQUEADA`, `LOGIN_FALLIDO` y otros, que generan archivos que no corrí). En la suite completa de M-4 esa prueba pasó, y no la toqué.
- Al terminar, `api` volvió a `infra/.env` (`FUENTE_PLACAS_URL` vacía, `BLOQUEO_INTENTOS=5`, regex por defecto).

La suite completa la repite el LEAD.

## Resultado

| Corrida | Comando | Resultado |
|---|---|---|
| API, fuente, bitácora, `api_app` y proxy | `PROXY_DISPONIBLE=1 pytest services/api/tests --integracion -rA` (11 min 40 s) | **177 en verde, 3 rojos, 1 error, 2 omitidas** (los 2 `NO VERIFICADO` de HU-01/02 que este ciclo cubre por otras pruebas). Los 4 son de la prueba o del arnés: R1 a R4 |
| **Pruebas del proxy (condición del veredicto)** | dentro de la corrida anterior | **Las 34 en verde, ninguna omitida** (`test_salud`, `test_errores`, `test_logs`, `test_dependencias`, 2 de `test_contrato_openapi`, `test_red::test_simuladores_no_responde_desde_el_anfitrion` y `test_la_clave_no_queda_en_los_logs_del_proxy`), más `test_proxy_publica_solo_sus_dos_puertos` y `test_proxy_sin_variables_publica_80_y_443` |
| App | `npx jest --ci` en `apps/movil` | **66 en verde, 9 rojos** (75, 5 archivos). Los 9 son de la prueba: R5 a R7 |
| Simuladores, regresión de HU-08, en el contenedor | `docker compose … run --rm -T --no-deps simuladores pytest -rA` | 115 en verde, 0 rojos, 27 omitidas (las del anfitrión) |
| Simuladores, regresión de HU-08, desde el anfitrión | `pytest services/simuladores/tests --integracion -rA` | 136 en verde, 0 rojos, 6 omitidas; el origen de fotos quedó vacío |

Al terminar, `api` volvió a `infra/.env` (comprobado: `BLOQUEO_INTENTOS=5`, `SESION_INACTIVIDAD_S=600`, `FUENTE_PLACAS_URL` vacía, `PLACA_FORMATO_REGEX` por defecto). La clave de los usuarios de prueba no aparece en este informe ni en ningún archivo versionado.

**Ningún rojo apunta al código.** Todos son desvíos de mis pruebas o de mi arnés. Los dejo para el arbitraje del LEAD, cada uno con la corrección que propongo; no toqué ninguna prueba después de la corrida.

## Rojos para que arbitre el LEAD

| # | Prueba | Qué pasó | Lectura del TESTER |
|---|---|---|---|
| R1 | `test_contrato_openapi.py::test_contrato_rutas_vigentes` | El OpenAPI publicado tiene además `/v1/motivos`, `/v1/consultas/placa` y `/v1/bitacora` | **Se apartó la prueba (obsoleta):** la lista era la de HU-01/02 y no le sumé las rutas de HU-03 y HU-07 (§1 y §2 de HU-03, §4 de HU-07). Corrección: agregar `GET /v1/motivos`, `POST /v1/consultas/placa` y `GET /v1/bitacora` |
| R2 | `test_hu03_placa.py::test_fuente_lenta` | Pasó todo lo del contrato: `503 FUENTE_NO_DISPONIBLE`, nunca `sin_requisitoria`, `ERROR_FUENTE` completo con la fila en `consulta`, y una duración de entre 5 y 7 s medida dentro del contenedor (eso son dos llamadas: una sola tarda unos 3 s). Falló solo el conteo por log: **0** líneas `GET /placas/ZZA-101` | **Arnés:** en modo `latencia` la API corta las llamadas a los 3 s, y el simulador no deja línea de acceso de una petición que el cliente abandonó. Con el log no se pueden contar, pero mi ayudante solo devolvía "no verificable" cuando no había ninguna línea de acceso. Según la respuesta 3 del LEAD, ese conteo queda **NO VERIFICADO**, y el reintento queda verificado por tiempos. En `error_500` (2 llamadas) y en `malformada` (1) el conteo por log sí funcionó: `test_fuente_caida` y `test_respuesta_fuera_de_contrato` en verde. Corrección: en `latencia`, conteo `NO VERIFICADO` con su motivo |
| R3 | `test_hu07_bitacora_db.py::test_sin_imagen_ni_clave` | `psql`: `invalid regular expression: invalid repetition count(s)` | **Defecto de la prueba:** la expresión `{500,}` supera el máximo de repeticiones de las expresiones de Postgres (255). La prueba no llegó a mirar los datos. Corrección: `{255,}`. En la misma corrida, el `REVOKE` del fail-closed se restauró, y la prueba de la clave en la bitácora de HU-01 pasó |
| R4 | `test_hu03_mock_y_roles.py::test_mock_del_contrato` (error en la fixture) | "Prism no arrancó" | **Arnés:** la imagen se descargó, pero `stoplight/prism:5` falla al arrancar en modo multiproceso (`TypeError: Cannot read properties of undefined (reading 'isPrimary')` en `createMultiProcessPrism`) y termina con código 1. Comprobado aparte, sin repetir la suite: con `--multiprocess=false` arranca y queda corriendo. El caso §4 queda **NO VERIFICADO** por el arnés. Corrección: agregar `--multiprocess=false` |
| R5 | Jest `HU01_HU02.test.tsx` › `HU-02 — inicio por rol › agente` y `› supervisor` | "Consultar placa" y "Bitácora" ya no están deshabilitadas | **Se apartó la prueba (obsoleta):** CONTRATO-HU-02, decisión 4: deshabilitadas *hasta que su HU construya la pantalla*. HU-03 §6 y HU-07 §5 las habilitan, y `HU03_HU07.test.tsx` lo verifica en verde. Corrección: esas dos opciones, habilitadas; las demás siguen deshabilitadas |
| R6 | Jest `HU03_HU07.test.tsx` › BIT-01 (v3): filtros (1), fecha inválida (4) y "Aplicar filtros" (1) | No encuentra "Aplicar filtros" | **Se apartó la prueba:** la app muestra los filtros dentro de una sección plegable "Filtros ▾" (`accessibilityState.expanded: false`), con "PA 24". La prueba suponía que estaban siempre a la vista, y el contrato (§5 v3) no dice si van abiertos o plegados. Corrección: tocar "Filtros" para desplegarlos antes de buscar los campos |
| R7 | Jest `HU03_HU07.test.tsx` › BIT-02 (v3) | No encuentra un texto "ID" exacto | **Se apartó la prueba:** la app muestra "ID: 77abcdef-0000-4000-8000-000077abcdef" (con "ID" y ": " anidados en el mismo texto), y el título "Registro #77abcdef" cumple la v3. La búsqueda exacta de "ID" no encuentra el texto anidado. Corrección: buscar "ID" sin coincidencia exacta (por ejemplo, `/^ID/`), sin confundirlo con "ID de captura" |

## Cómo se corren

| Parte | Comando | Notas |
|---|---|---|
| API, fuente, bitácora y `api_app` | `pytest services/api/tests --integracion` (anfitrión, sistema arrancado con los dos compose) | Las peticiones salen desde dentro del contenedor `api` a `http://api:8000`. Los modos de la fuente se fuerzan con `PUT http://simuladores:8001/control/modos/placas`. La base se toca con `psql` dentro de `db`, con `SET ROLE api_app` o `SET ROLE <dueño>`; las operaciones destructivas van siempre dentro de una transacción con `ROLLBACK`, y el `REVOKE` del fail-closed se restaura en `finally`. Para los tiempos y el formato de placa, se recrea solo `api` con un archivo de entorno temporal y al final se vuelve a `infra/.env` |
| Proxy (34 pruebas) | igual, con el proxy arriba en el puerto alterno | La URL sale de `URL_BASE_PRUEBAS` o `--url-base`; si no están, de `https://localhost:<PROXY_PUERTO_HTTPS de infra/.env>` (sin el puerto escrito en el código). `PROXY_DISPONIBLE=1` obliga a correrlas (la M-8 de HU-01/02 queda como respaldo) |
| App | `npx jest` en `apps/movil` | Monta `App.tsx` (HU-01 §4 bis). Se simulan el `fetch` global, `expo-secure-store` y `BackHandler` |
| Mock de §4 | incluido en `--integracion` | Prism (`stoplight/prism:5`) como contenedor en la red interna, solo con `contratos/fuentes/placas.yaml`; la API se recrea con `FUENTE_PLACAS_URL` apuntando a él |

**Conteo de llamadas a la fuente** (respuesta del LEAD a la pregunta 3): por tiempos en `latencia` (≤ 7 s y ~6 s = dos llamadas) y por el log de acceso del simulador (`docker compose logs --since <t> simuladores`, líneas `GET /placas/<placa>`): 2 en `503` y 1 en `502`. Si el log no trae líneas de acceso, solo el conteo queda `NO VERIFICADO`. Comprobado: el log cuenta bien (2 pedidos → 2 líneas).

## Caso del contrato → prueba → estado

Estado de la suite completa (M-4). Además del contrato, las pruebas de HU-01/02 de `HU01_HU02.test.tsx` siguen en verde, salvo R5.

### HU-03 v3 — API (`services/api/tests/`)

| § | Caso | Prueba | Estado |
|---|---|---|---|
| 1 | Catálogo exacto con `formato_placa` (v3) | `test_hu03_placa.py::test_catalogo` | VERDE |
| 1 | Configurable (agregar y desactivar en `motivo_catalogo`; `otro` al final) | `::test_catalogo_configurable` | VERDE |
| 1/2 | Otro rol → 403 + `ACCESO_DENEGADO`, sin efecto | `test_hu03_mock_y_roles.py::test_matriz_de_roles` | VERDE |
| 2 | Con, sin requisitoria y no registrada (nunca `sin_requisitoria`): forma, `CONSULTA_PLACA`, fila en `consulta` `completada`; variante "Solo estado" | `::test_resultados_y_registro` (3) | VERDE |
| 2 | Minúsculas y espacios | `::test_minusculas_y_espacios` | VERDE |
| 2 | "Otro" con texto válido | `::test_motivo_otro_con_texto` | VERDE |
| 2 | Sin motivo (4 variantes), "Otro" corto (4), formato inválido (3): `422` con su mensaje exacto, **sin consultar la fuente** (con la fuente en `error_500`, consultarla daría `503`) y sin evento | `::test_sin_motivo`, `::test_otro_corto`, `::test_formato_invalido` | VERDE |
| 2 | Faltan los dos → primero el motivo | `::test_faltan_los_dos` | VERDE |
| 2 | Cuerpo mal formado → `422 SOLICITUD_INVALIDA` | `::test_cuerpo_mal_formado` (2) | VERDE |
| 3 | Fuente caída: `503`, `ERROR_FUENTE`, 2 llamadas | `::test_fuente_caida` | VERDE |
| 3 | Fuente lenta: `503` en ≤ 7 s, ~6 s (reintento), 2 llamadas | `::test_fuente_lenta` | VERDE en código, evento y tiempos; conteo por log **NO VERIFICADO** (A2) |
| 3 | Fuera de contrato: `502` sin reintento (1 llamada) | `::test_respuesta_fuera_de_contrato` | VERDE |
| 3 | Evento de error completo y fila en `consulta` `error`/`error` | dentro de los tres anteriores | VERDE |
| 3 | Vuelve la fuente | `::test_vuelve_la_fuente` | VERDE |
| 4 | Mock del contrato (Prism) | `test_hu03_mock_y_roles.py::test_mock_del_contrato` | VERDE en la vuelta 1 (A4). En la vuelta 0: NO VERIFICADO (arnés, R4) |
| 5 | Fail-closed de la consulta | `test_hu07_bitacora_db.py::test_fail_closed_consulta` | VERDE |
| 7 | Formato configurable sin tocar código (regex y descripción nuevas en `/v1/motivos`, en el `422` y en la validación) | `test_hu03_placa.py::test_formato_configurable_sin_tocar_codigo` | VERDE |

### HU-03 v3 — App (`apps/movil/__tests__/HU03_HU07.test.tsx`)

| Caso | Estado |
|---|---|
| HOME-01: "Consultar placa" habilitada, "Verificar rostro" deshabilitada | VERDE |
| PLA-01 sin catálogo (v4): `/v1/motivos` con `503`, red o respuesta inesperada → error de PLA-07, no se puede consultar, "Reintentar" vuelve a pedir el catálogo | VERDE (3) |
| PLA-01: campo, catálogo de `/v1/motivos`, "Describa el motivo *" solo con "Otro"; placa en mayúsculas y monoespaciada | VERDE |
| PLA-01: botón de cámara deshabilitado | **NO VERIFICADO**: el contrato no le da un texto ni un nombre, así que no se puede encontrar desde afuera |
| PLA-02 (sin motivo; "Otro" corto) sin enviar | VERDE. El foco en el campo de motivo no se verifica (no es observable en Jest de forma fiable) |
| PLA-03: descripción y regex de `/v1/motivos` (v3), los dos mensajes juntos, y el `mensaje` del `422` de la API | VERDE |
| Envía `placa`, `motivo_codigo`, `motivo_texto` con el token | VERDE |
| PLA-04: "Consultando…", botón desactivado, un solo envío | VERDE |
| PLA-05, PLA-06, PLA-08 (textos, fecha local, sin ✓, textos distintos) | VERDE. El color (rojo, gris, "sin verde") no se verifica: el contrato no fija valores |
| PLA-07 con `503`, `502`, `503 SERVICIO_NO_DISPONIBLE`, red, `500` y un resultado desconocido; "Reintentar" con la misma placa y motivo | VERDE |
| `403` → ERR-01 y "Volver al inicio" (desde HU-02 v3) | VERDE |
| Nada en el dispositivo | VERDE |

### HU-07 v2

| § | Caso | Prueba | Estado |
|---|---|---|---|
| 1 | La API usa `api_app` (`pg_stat_activity` de las conexiones del contenedor `api`) | `test_hu07_bitacora_db.py::test_la_api_usa_api_app` | VERDE |
| 1 | Permisos de `api_app` | `::test_permisos_de_api_app` | VERDE |
| 1 | `UPDATE`, `DELETE`, `TRUNCATE` como `api_app` → error, sin cambios | `::test_api_app_no_puede_modificar` (3) | VERDE |
| 1 | Las tres como dueño → error del trigger con `bitacora es de solo insercion` | `::test_el_dueno_tampoco_por_el_trigger` (3) | VERDE |
| 1 | Base recién migrada con `MIGRACION_DATABASE_URL` (v2): tabla, columnas, permisos y trigger; la clave no se imprime | `::test_base_recien_migrada` | VERDE |
| 1 | Sin ruta de edición → `405` | `::test_sin_ruta_de_edicion` (6) | VERDE |
| 2 | Columnas; `es_sintetico` siempre `true` | `::test_columnas` | VERDE |
| 2 | `CONSULTA_PLACA` y `ERROR_FUENTE` con su contenido | en `test_hu03_placa.py` | VERDE |
| 2 | Los 9 tipos de la iteración se generan en la sesión (corre al final) | `::test_eventos_de_la_iteracion` | VERDE |
| 2 | Sin imagen ni clave | `::test_sin_imagen_ni_clave` | VERDE en la vuelta 1 (A3). En la vuelta 0: ROJO (R3) |
| 3 | Fail-closed en la consulta y en el login (y CONTRATO-HU-01 §5); al restaurar, normal | `::test_fail_closed_consulta`, `::test_fail_closed_login`, `::test_al_restaurar_vuelve_a_la_normalidad` | VERDE |
| 4 | Lista, forma, orden y límite por defecto; `usuario` como nombre | `test_hu07_consulta_bitacora.py::test_lista_forma_orden_y_limite_por_defecto`, `::test_usuario_es_el_nombre_de_usuario` | VERDE |
| 4 | Límite 1 y 100; 0, 101 y texto → `422` | `::test_limite`, `::test_parametro_invalido` | VERDE |
| 4 | Filtros por usuario, fechas (`desde` incluido, `hasta` excluido), tipo, resultado y combinados | `::test_filtro_*`, `::test_filtros_combinados` | VERDE |
| 4 | Paginación sin repetir ni saltar, con registros nuevos entrando | `::test_paginacion_sin_repetir_ni_saltar` | VERDE |
| 4 | `CONSULTA_BITACORA` con los filtros | `::test_la_consulta_se_registra` | VERDE |
| 4 | Agente y revisor → 403 | `test_hu03_mock_y_roles.py::test_matriz_de_roles` | VERDE |
| 5 | BIT-01 (etiquetas de tipo y de resultado, fecha `dd/mm hh:mm`, "sistema", SINTÉTICO, PA 24, "Cargar más", sin editar ni borrar), errores ≠ lista vacía, lista vacía real | Jest `HU-07 — BIT-01 y BIT-02` | VERDE |
| 5 | BIT-01 (v3): textos de los filtros, fecha inválida sin enviar, "Aplicar filtros" | Jest `BIT-01 (v3) › …` (6) | VERDE en la vuelta 1 (A6, v4). En la vuelta 0: ROJO (R6) |
| 5 | BIT-02 (v3): "Registro #<8>", "ID" con el id completo, solo lectura, sin "ID de captura" ni "Score" | Jest `BIT-02 (v3)` | VERDE en la vuelta 1 (A7). En la vuelta 0: ROJO (R7) |

### Arrastrado de otras HU

| Caso | Prueba | Estado |
|---|---|---|
| HU-02 §2: matriz de `403` + `ACCESO_DENEGADO` con usuario, rol, ruta y método; sin efecto; `401` antes que `403` | `test_hu03_mock_y_roles.py::test_matriz_de_roles` (9), `::test_sin_token_401_antes_que_403` (3), `::test_403_identico_entre_rutas` | VERDE |
| HU-01 §5: fail-closed del login | `test_hu07_bitacora_db.py::test_fail_closed_login` | VERDE |
| HU-01: retomar la sesión → AUTH-03 (renovación `200` y `/v1/me` `401`; o las dos `401 SESION_VENCIDA`) | Jest `HU01_retomar_me_vencida.test.tsx` y `HU01_retomar_todo_vencido.test.tsx` (un archivo por variante) | VERDE |
| Proxy: 34 pruebas en verde con el puerto alterno; el proxy publica solo sus dos puertos, y sin variables 80 y 443 | `test_red.py::test_proxy_publica_solo_sus_dos_puertos`, `::test_proxy_sin_variables_publica_80_y_443` y las del Sprint 0 | VERDE |

## P1 retirado (falso positivo de la prueba)

El aviso preliminar P1 ("retomar con renovación y `/v1/me` en `401 SESION_VENCIDA` no muestra AUTH-03") venía de **la prueba, no de la app**. Las dos variantes estaban en un mismo `test.each`, y la segunda heredaba el estado en memoria de módulo que dejaba la primera: la app no mostraba el login al montar, y la prueba fallaba antes del escenario (lo señaló el LEAD). Evidencia: la segunda variante, corrida sola, pasa. Corrección: cada variante va en su propio archivo (`HU01_retomar_me_vencida.test.tsx`, `HU01_retomar_todo_vencido.test.tsx`), porque Jest da un registro de módulos limpio por archivo. Probé antes `jest.isolateModules`, pero carga otra copia de React (`useRef` de `null`), lo mismo que en el Sprint 0. Resultado: las dos en verde contra la app actual.
