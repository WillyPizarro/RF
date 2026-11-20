# Informe TESTER — HU-03 + HU-07 (consulta de placa y bitácora)

**Contratos:** `docs/contratos/CONTRATO-HU-03.md` **v3** y `docs/contratos/CONTRATO-HU-07.md` **v2** (más HU-08 v4, HU-01 v5 y HU-02 v3, vigentes) · **Encargo:** `docs/contratos/ENCARGO-HU-03-07.md` (M-1) · **Rama:** `hu-03`
**Estado:** pruebas escritas; **suite completa pendiente** de la orden del LEAD (orden del cierre, punto 3). Lo corrido hasta ahora solo comprobó el arnés; no son hallazgos, salvo el aviso preliminar P1.

## Cómo se corren

| Parte | Comando | Notas |
|---|---|---|
| API, fuente, bitácora y `api_app` | `pytest services/api/tests --integracion` (anfitrión, sistema arrancado con los dos compose) | Las peticiones salen desde dentro del contenedor `api` a `http://api:8000`. Los modos de la fuente se fuerzan con `PUT http://simuladores:8001/control/modos/placas`. La base se toca con `psql` dentro de `db`, con `SET ROLE api_app` o `SET ROLE <dueño>`; las operaciones destructivas van siempre dentro de una transacción con `ROLLBACK`, y el `REVOKE` del fail-closed se restaura en `finally`. Para los tiempos y el formato de placa, se recrea solo `api` con un archivo de entorno temporal y al final se vuelve a `infra/.env` |
| Proxy (34 pruebas) | igual, con el proxy arriba en el puerto alterno | La URL sale de `URL_BASE_PRUEBAS` o `--url-base`; si no están, de `https://localhost:<PROXY_PUERTO_HTTPS de infra/.env>` (sin el puerto escrito en el código). `PROXY_DISPONIBLE=1` obliga a correrlas (la M-8 de HU-01/02 queda como respaldo) |
| App | `npx jest` en `apps/movil` | Monta `App.tsx` (HU-01 §4 bis). Se simulan el `fetch` global, `expo-secure-store` y `BackHandler` |
| Mock de §4 | incluido en `--integracion` | Prism (`stoplight/prism:5`) como contenedor en la red interna, solo con `contratos/fuentes/placas.yaml`; la API se recrea con `FUENTE_PLACAS_URL` apuntando a él |

**Conteo de llamadas a la fuente** (respuesta del LEAD a la pregunta 3): por tiempos en `latencia` (≤ 7 s y ~6 s = dos llamadas) y por el log de acceso del simulador (`docker compose logs --since <t> simuladores`, líneas `GET /placas/<placa>`): 2 en `503` y 1 en `502`. Si el log no trae líneas de acceso, solo el conteo queda `NO VERIFICADO`. Comprobado: el log cuenta bien (2 pedidos → 2 líneas).

## Caso del contrato → prueba

### HU-03 v3 — API (`services/api/tests/`)

| § | Caso | Prueba | Estado |
|---|---|---|---|
| 1 | Catálogo exacto con `formato_placa` (v3) | `test_hu03_placa.py::test_catalogo` | Pendiente |
| 1 | Configurable (agregar y desactivar en `motivo_catalogo`; `otro` al final) | `::test_catalogo_configurable` | Pendiente |
| 1/2 | Otro rol → 403 + `ACCESO_DENEGADO`, sin efecto | `test_hu03_mock_y_roles.py::test_matriz_de_roles` | Pendiente |
| 2 | Con, sin requisitoria y no registrada (nunca `sin_requisitoria`): forma, `CONSULTA_PLACA`, fila en `consulta` `completada`; variante "Solo estado" | `::test_resultados_y_registro` (3) | Pendiente |
| 2 | Minúsculas y espacios | `::test_minusculas_y_espacios` | Pendiente |
| 2 | "Otro" con texto válido | `::test_motivo_otro_con_texto` | Pendiente |
| 2 | Sin motivo (4 variantes), "Otro" corto (4), formato inválido (3): `422` con su mensaje exacto, **sin consultar la fuente** (con la fuente en `error_500`, consultarla daría `503`) y sin evento | `::test_sin_motivo`, `::test_otro_corto`, `::test_formato_invalido` | Pendiente |
| 2 | Faltan los dos → primero el motivo | `::test_faltan_los_dos` | Pendiente |
| 2 | Cuerpo mal formado → `422 SOLICITUD_INVALIDA` | `::test_cuerpo_mal_formado` (2) | Pendiente |
| 3 | Fuente caída: `503`, `ERROR_FUENTE`, 2 llamadas | `::test_fuente_caida` | Pendiente |
| 3 | Fuente lenta: `503` en ≤ 7 s, ~6 s (reintento), 2 llamadas | `::test_fuente_lenta` | Pendiente |
| 3 | Fuera de contrato: `502` sin reintento (1 llamada) | `::test_respuesta_fuera_de_contrato` | Pendiente |
| 3 | Evento de error completo y fila en `consulta` `error`/`error` | dentro de los tres anteriores | Pendiente |
| 3 | Vuelve la fuente | `::test_vuelve_la_fuente` | Pendiente |
| 4 | Mock del contrato (Prism) | `test_hu03_mock_y_roles.py::test_mock_del_contrato` | Pendiente (`NO VERIFICADO` si la imagen no se descarga) |
| 5 | Fail-closed de la consulta | `test_hu07_bitacora_db.py::test_fail_closed_consulta` | Pendiente |
| 7 | Formato configurable sin tocar código (regex y descripción nuevas en `/v1/motivos`, en el `422` y en la validación) | `test_hu03_placa.py::test_formato_configurable_sin_tocar_codigo` | Pendiente |

### HU-03 v3 — App (`apps/movil/__tests__/HU03_HU07.test.tsx`)

| Caso | Estado |
|---|---|
| HOME-01: "Consultar placa" habilitada, "Verificar rostro" deshabilitada | Pendiente |
| PLA-01: campo, catálogo de `/v1/motivos`, "Describa el motivo *" solo con "Otro"; placa en mayúsculas y monoespaciada | Pendiente |
| PLA-01: botón de cámara deshabilitado | **NO VERIFICADO**: el contrato no le da un texto ni un nombre, así que no se puede encontrar desde afuera |
| PLA-02 (sin motivo; "Otro" corto) sin enviar | Pendiente. El foco en el campo de motivo no se verifica (no es observable en Jest de forma fiable) |
| PLA-03: descripción y regex de `/v1/motivos` (v3), los dos mensajes juntos, y el `mensaje` del `422` de la API | Pendiente |
| Envía `placa`, `motivo_codigo`, `motivo_texto` con el token | Pendiente |
| PLA-04: "Consultando…", botón desactivado, un solo envío | Pendiente |
| PLA-05, PLA-06, PLA-08 (textos, fecha local, sin ✓, textos distintos) | Pendiente. El color (rojo, gris, "sin verde") no se verifica: el contrato no fija valores |
| PLA-07 con `503`, `502`, `503 SERVICIO_NO_DISPONIBLE`, red, `500` y un resultado desconocido; "Reintentar" con la misma placa y motivo | Pendiente |
| `403` → ERR-01 y "Volver al inicio" (desde HU-02 v3) | Pendiente |
| Nada en el dispositivo | Pendiente |

### HU-07 v2

| § | Caso | Prueba | Estado |
|---|---|---|---|
| 1 | La API usa `api_app` (`pg_stat_activity` de las conexiones del contenedor `api`) | `test_hu07_bitacora_db.py::test_la_api_usa_api_app` | Pendiente |
| 1 | Permisos de `api_app` | `::test_permisos_de_api_app` | Pendiente |
| 1 | `UPDATE`, `DELETE`, `TRUNCATE` como `api_app` → error, sin cambios | `::test_api_app_no_puede_modificar` (3) | Pendiente |
| 1 | Las tres como dueño → error del trigger con `bitacora es de solo insercion` | `::test_el_dueno_tampoco_por_el_trigger` (3) | Pendiente |
| 1 | Base recién migrada con `MIGRACION_DATABASE_URL` (v2): tabla, columnas, permisos y trigger; la clave no se imprime | `::test_base_recien_migrada` | Pendiente |
| 1 | Sin ruta de edición → `405` | `::test_sin_ruta_de_edicion` (6) | Pendiente |
| 2 | Columnas; `es_sintetico` siempre `true` | `::test_columnas` | Pendiente |
| 2 | `CONSULTA_PLACA` y `ERROR_FUENTE` con su contenido | en `test_hu03_placa.py` | Pendiente |
| 2 | Los 9 tipos de la iteración se generan en la sesión (corre al final) | `::test_eventos_de_la_iteracion` | Pendiente |
| 2 | Sin imagen ni clave | `::test_sin_imagen_ni_clave` | Pendiente |
| 3 | Fail-closed en la consulta y en el login (y CONTRATO-HU-01 §5); al restaurar, normal | `::test_fail_closed_consulta`, `::test_fail_closed_login`, `::test_al_restaurar_vuelve_a_la_normalidad` | Pendiente |
| 4 | Lista, forma, orden y límite por defecto; `usuario` como nombre | `test_hu07_consulta_bitacora.py::test_lista_forma_orden_y_limite_por_defecto`, `::test_usuario_es_el_nombre_de_usuario` | Pendiente |
| 4 | Límite 1 y 100; 0, 101 y texto → `422` | `::test_limite`, `::test_parametro_invalido` | Pendiente |
| 4 | Filtros por usuario, fechas (`desde` incluido, `hasta` excluido), tipo, resultado y combinados | `::test_filtro_*`, `::test_filtros_combinados` | Pendiente |
| 4 | Paginación sin repetir ni saltar, con registros nuevos entrando | `::test_paginacion_sin_repetir_ni_saltar` | Pendiente |
| 4 | `CONSULTA_BITACORA` con los filtros | `::test_la_consulta_se_registra` | Pendiente |
| 4 | Agente y revisor → 403 | `test_hu03_mock_y_roles.py::test_matriz_de_roles` | Pendiente |
| 5 | BIT-01 (etiquetas de tipo y de resultado, fecha `dd/mm hh:mm`, "sistema", SINTÉTICO, PA 24, "Cargar más", sin editar ni borrar), BIT-02, errores ≠ lista vacía, lista vacía real | Jest `HU-07 — BIT-01 y BIT-02` | Pendiente |

### Arrastrado de otras HU

| Caso | Prueba | Estado |
|---|---|---|
| HU-02 §2: matriz de `403` + `ACCESO_DENEGADO` con usuario, rol, ruta y método; sin efecto; `401` antes que `403` | `test_hu03_mock_y_roles.py::test_matriz_de_roles` (9), `::test_sin_token_401_antes_que_403` (3), `::test_403_identico_entre_rutas` | Pendiente |
| HU-01 §5: fail-closed del login | `test_hu07_bitacora_db.py::test_fail_closed_login` | Pendiente |
| HU-01: retomar la sesión → AUTH-03 (renovación `200` y `/v1/me` `401`; o las dos `401 SESION_VENCIDA`) | Jest `HU-01 AUTH-03 al retomar la sesión` (2) | Pendiente; ver P1 |
| Proxy: 34 pruebas en verde con el puerto alterno; el proxy publica solo sus dos puertos, y sin variables 80 y 443 | `test_red.py::test_proxy_publica_solo_sus_dos_puertos`, `::test_proxy_sin_variables_publica_80_y_443` y las del Sprint 0 | Pendiente |

## Aviso preliminar (no es la corrida que cuenta)

**P1.** Contra la app que hay hoy en la rama (código de HU-01 ya en `main`), retomar la sesión cuando la renovación **y** `/v1/me` responden `401 SESION_VENCIDA` no muestra el aviso de AUTH-03. La variante "renovación `200` y `/v1/me` `401`" sí lo muestra. El arbitraje A1 de HU-01/02 dice "venga de la solicitud que venga". Se repite en la corrida final.
