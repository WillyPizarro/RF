# VEREDICTO — HU-03 Consultar placa + HU-07 Bitácora

**Contratos:** `docs/contratos/CONTRATO-HU-03.md` **v4** y `docs/contratos/CONTRATO-HU-07.md` **v4** (v3 en la vuelta 0) (aprobados por el humano vía PM el 2026-11-19); siguen vigentes HU-08 v4, HU-01 v5 y HU-02 v3
**Rama:** `hu-03` (base `main` `b8e3210`) · **Código del DEV:** `27d0b30`, `95073db`, `b82a63a` · **Pruebas del TESTER:** `c056068`, informe `5a3a67a`
**Fecha:** 2026-11-19 · **LEAD**, skill `veredicto`
**Resultado:** **VERDE tras la vuelta 1** (A1 a A7 cerrados; HU-07 llevado a **v4**). Ningún rojo, y las 34 pruebas del proxy en verde con el puerto alterno. Quedan 3 `NO VERIFICADO` (§7 bis) para aceptación del humano.
*Vuelta 0:* **ROJO, vuelve en la vuelta 1.** Ningún rojo apunta al código. Hay 6 desvíos de las pruebas o del arnés (TESTER) y 1 hueco del contrato (R6), escalado al humano.

---

## 1. Propiedad de rutas

`git log main..hu-03 --name-only`, agrupado por prefijo:

| Rol | Commits | Archivos | ¿Dentro de sus rutas? |
|---|---|---|---|
| `[DEV]` | `27d0b30`, `95073db`, `71ac8f7`, `b82a63a` | `services/api/` (sin `tests/`), `apps/movil/` (sin `__tests__/`), `infra/`, `contratos/api/openapi.json`, `informes/DEV-HU-03-07.md` | Sí |
| `[TESTER]` | `3e4b0ba`, `970fac8`, `a1f71b7`, `c056068`, `5a3a67a` | `services/api/tests/`, `apps/movil/__tests__/`, `informes/TESTER-HU-03-07.md` | Sí |
| `[UX]` | `8aa120f`, `1e9facd`, `be5440c` | `docs/ux/` | Sí |
| `[LEAD]` | 7 commits | `docs/contratos/`, `informes/VEREDICTO-HU-01-02.md` | Sí |

Ningún commit sin prefijo y ninguno con `Empezar.txt`. **Sin hallazgos.**

## 2. Versión del contrato

El DEV (`b82a63a`, M-3) y el TESTER (`c056068`, M-3 y M-4) trabajaron sobre HU-03 **v4** y HU-07 **v3**. El veredicto es válido.

## 3. Corrida del TESTER (M-4) y del LEAD

**Corrida del TESTER (M-4):**
- **Condiciones:** proxy en 8080/8443 y `PROXY_DISPONIBLE=1`.
- **API:** 177 en verde, 3 rojos y 1 error.
- **Jest:** 66 en verde y 9 rojos.
- **Simuladores:** 115 en verde en el contenedor y 136 en el anfitrión.
- **Proxy:** las 34 pruebas que pasan por el proxy corrieron **en verde**, ninguna omitida, y se cumple la condición del humano.

La corrida completa del LEAD se hace en la vuelta 1, sobre los commits que la cierren.

## 4. Arbitraje

| # | Caso | Contrato | Prueba | Código | Desenlace | Destinatario | Vuelta |
|---|---|---|---|---|---|---|---|
| A1 (R1) | Rutas vigentes del OpenAPI | HU-03 §1 y §2 y HU-07 §4 agregan `GET /v1/motivos`, `POST /v1/consultas/placa` y `GET /v1/bitacora` | Tiene la lista de HU-01/02 | Publica las rutas de los contratos | **Se apartó la prueba** (obsoleta) | TESTER | 1 |
| A2 (R2) | Fuente lenta: un solo reintento | HU-03 §3: `503` tras un reintento, en ≤ 7 s | Cuenta las llamadas en el log del simulador, y una llamada cortada no deja línea | `503`, `ERROR_FUENTE` y 5 a 7 s (dos llamadas de unos 3 s) | **Se apartó la prueba**: el conteo por log en `latencia` no es posible. El reintento queda verificado **por tiempos** y el conteo por log en este modo queda `NO VERIFICADO`, como en la respuesta 3 del LEAD | TESTER | 1 |
| A3 (R3) | Sin imagen ni clave en la bitácora | HU-07 §2 | La expresión `{500,}` no es válida en Postgres (el máximo es 255) | — | **Se apartó la prueba** | TESTER | 1 |
| A4 (R4) | Reemplazo de la fuente por un mock del yaml | HU-03 §4 | Prism 5 no arranca en modo multiproceso | — | **Se apartó el arnés**: hay que agregar `--multiprocess=false`. Si después sigue sin poder correr, queda `NO VERIFICADO` con su motivo (§4 lo permite), pero se espera verde | TESTER | 1 |
| A5 (R5) | Inicio del agente y del supervisor | HU-02, decisión 4: deshabilitadas *hasta que su HU construya la pantalla*; HU-03 §6 y HU-07 §5 las habilitan | Exige "Consultar placa" y "Bitácora" deshabilitadas | Las habilita | **Se apartó la prueba** (obsoleta) | TESTER | 1 |
| A6 (R6) | Filtros de BIT-01 | HU-07 §5 v3 fija los textos de los filtros, pero **no dice si están a la vista o plegados**. El wireframe muestra desplegables a la vista | Supone los filtros a la vista | Los muestra plegados bajo "Filtros ▾" | **El contrato no lo decía** → pregunta al humano (§7) | — | 1 |
| A7 (R7) | BIT-02, campo "ID" | HU-07 §5 v3: "ID" con el id completo | Busca un texto exacto "ID" | Muestra "ID: <uuid>" | **Se apartó la prueba**: el campo y su valor cumplen | TESTER | 1 |

## 5. Trampas

- **Código:** no tiene casos especiales para las placas sintéticas. `ZZA-101`, `ZZB-201` y `ZZZ-999` solo aparecen en la semilla del simulador y en las pruebas.
- **Cambios de las pruebas entre vueltas:** responden a la v3 y la v4 (M-1 y M-3) y al aislamiento de P1 (retirado).
- **Sin trampas detectadas.**

## 6. Matriz de trazabilidad (cierre de la vuelta 1)

| Criterio de aceptación (HU) | Caso del contrato | Prueba | Resultado |
|---|---|---|---|
| HU-03 esc. 1: placa con requisitoria | §2 `con_requisitoria`, `CONSULTA_PLACA`; §6 PLA-05 | `test_hu03_placa.py`; Jest PLA-05 | 🟢 |
| HU-03 esc. 5: sin requisitoria | §2 `sin_requisitoria`; §6 PLA-06 (sin verde ni ✓) | `test_hu03_placa.py`; Jest PLA-06 | 🟢 |
| HU-03 (HU-08 dec. 3) | §2 `placa_no_registrada`; PLA-08 | `test_hu03_placa.py`; Jest PLA-08 | 🟢 |
| HU-03 esc. 2: motivo obligatorio | §1 catálogo y configurable; §2 `MOTIVO_REQUERIDO`; PLA-02 | `test_hu03_placa.py`; Jest PLA-02 | 🟢 |
| HU-03 esc. 4: formato inválido | §2 `PLACA_FORMATO_INVALIDO`, normalización; §1 y §6 `formato_placa` (v3); PLA-03 | `test_hu03_placa.py`; Jest PLA-03 | 🟢 |
| HU-03 esc. 3: fuente caída | §3 `error_500` → `503`, 2 llamadas (conteo por log), `ERROR_FUENTE` | `::test_fuente_caida` | 🟢 |
| HU-03 esc. 3 | §3 `latencia` → `503` en 5 a 7 s | `::test_fuente_lenta` | 🟢 por tiempos; conteo por log `NO VERIFICADO` (A2) |
| HU-08 esc. 3 (API) | §3 `malformada` → `502`, 1 llamada, `ERROR_FUENTE` | `::test_respuesta_fuera_de_contrato` | 🟢 |
| HU-08 esc. 2 (API) | §4 mock de Prism solo desde el yaml | `test_hu03_mock_y_roles.py::test_mock_del_contrato` | 🟢 |
| HU-03 esc. 3 (app) | PLA-07 (nunca "sin requisitoria"), PLA-04, PLA-01 sin catálogo (v4) | Jest | 🟢 |
| HU-02 esc. 2: acceso denegado | Matriz `403 SIN_PERMISO` + `ACCESO_DENEGADO`, `401` antes que `403`; ERR-01 | `test_matriz_de_roles` (9), `test_sin_token_401_antes_que_403` (3), `test_403_identico_entre_rutas`; Jest ERR-01 | 🟢 (cierra el `NO VERIFICADO` 4 de HU-01/02) |
| HU-07 esc. 1: contenido | §2 campos de `CONSULTA_PLACA`, `ERROR_FUENTE` y los 9 tipos de la iteración; sin imagen ni clave | `test_hu07_bitacora_db.py` | 🟢 |
| HU-07 esc. 2: solo inserción | §1 `api_app` (INSERT y SELECT), UPDATE, DELETE y TRUNCATE rechazados, trigger también para el dueño, migración con `MIGRACION_DATABASE_URL` (v2), `405` | `test_hu07_bitacora_db.py` | 🟢 |
| HU-07 esc. 3 / HU-01 §5: fail-closed | §3: sin registro no hay resultado ni sesión (`503`) | `::test_fail_closed_consulta`, `::test_fail_closed_login` | 🟢 (cierra el `NO VERIFICADO` 3 de HU-01/02) |
| HU-07: consulta del supervisor | §4 filtros, cursor y `CONSULTA_BITACORA`; otros roles `403` | `test_hu07_consulta_bitacora.py` | 🟢 |
| HU-07 (app) | §5 BIT-01 (etiquetas, filtros plegados v4, error ≠ vacío), BIT-02 (título corto e "ID" v3) | Jest BIT-01 y BIT-02 | 🟢 |
| HU-01 (pendiente) | AUTH-03 al retomar la sesión (dos variantes) | `HU01_retomar_*.test.tsx` | 🟢 |
| Puerto 80 (condición del humano) | Las 34 pruebas del proxy (Sprint 0 y la clave en los logs del proxy); el proxy publica sus dos puertos, y 80/443 sin variables | `PROXY_DISPONIBLE=1`, `test_red.py` | 🟢 (cierra el `NO VERIFICADO` 2 de HU-01/02) |
| Regresión | HU-08 v4, HU-01 v5, HU-02 v3 | Simuladores 115 + 136; API y Jest completas | 🟢 |
| HU-03: desempeño | p95 ≤ 2 s | — | Fuera de este veredicto (decisión 10, prueba de carga) |

**Casos sin criterio de la HU** (ya aprobados como decisiones del contrato): `placa_no_registrada` y PLA-08 (decisión 3), la normalización de la placa (decisión 6), el `502` sin reintento (decisión 8), PLA-01 sin catálogo (v4) y los filtros plegados (v4).

## 7 bis. Vuelta 1 (2026-11-19)

**Commits:**
- `6b20867 [TESTER]`, que corrige A1 a A7 y solo toca sus rutas;
- `befa2fb [UX]`, el wireframe de BIT-01 con los filtros plegados.

Contratos: HU-03 **v4** y HU-07 **v4**.

**Corrida del LEAD sobre la punta `6b20867`**, con `up -d --build`, los dos archivos de compose y el proxy arriba en `8080`/`8443` (`docker compose ps`):

| Corrida | Comando | Resultado |
|---|---|---|
| API | `PROXY_DISPONIBLE=1 pytest services/api/tests --integracion -rA` (9 min 35 s) | **181 en verde, 0 rojos, 2 omitidas**. Las 2 son marcadores de HU-01/02 (`test_hu01_bitacora_config.py:88` y `test_hu02_perfil_roles.py:55`) cuyos casos ahora cubren `test_fail_closed_login` y `test_matriz_de_roles`, en verde |
| App | `npx jest --ci` | **75 de 75 en verde** (5 archivos) |
| Simuladores, contenedor | `run --rm -T --no-deps simuladores pytest` | **115 en verde, 27 omitidas** (las del anfitrión) |
| Simuladores, anfitrión | `pytest services/simuladores/tests --integracion` | **136 en verde, 6 omitidas** |
| Estado final | `printenv` en `api`, `docker ps -a` | `infra/.env` (600 / 5), sin `FUENTE_PLACAS_URL` (usa el simulador), sin contenedores de Prism |

**Trampas:**
- **A7:** la prueba sigue exigiendo el id completo (`getByText(id)`) y que el título no lo muestre entero.
- **A5:** sigue exigiendo que "Verificar rostro", "Mis verificaciones" y las demás opciones estén deshabilitadas.
- **A2:** sigue exigiendo una duración de 5 s o más (el reintento).
- **Sin trampas detectadas.**

**`NO VERIFICADO` para aceptación del humano:**

1. **Conteo de llamadas en `latencia`:** se hizo por log, y el simulador no registra una llamada cortada. El reintento sí quedó verificado por tiempos.
2. **Capturas del emulador:** el UX revisó las de Jest, igual que en HU-01.
3. **El rol `api_app` en el Supabase del VPS:** queda fuera de este veredicto, como tarea obligatoria del despliegue (`PENDIENTES.md`).

## 7. Pregunta para el humano

**R6:** ¿los filtros de BIT-01 pueden ir plegados en una sección "Filtros ▾" que se despliega con un toque, o tienen que estar siempre a la vista, como en el wireframe? **Respuesta del humano (vía PM, 2026-11-19): pueden ir plegados (opción A)** → CONTRATO-HU-07 **v4**. A6 pasa al TESTER: la prueba despliega los filtros antes de usarlos.

## 8. Siguiente paso

Escalar los `NO VERIFICADO` del §7 bis al humano, vía el PM. Con su aceptación, el merge `hu-03 → main` lo decide el humano.
