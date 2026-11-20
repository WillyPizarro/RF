# VEREDICTO — HU-03 Consultar placa + HU-07 Bitácora

**Contratos:** `docs/contratos/CONTRATO-HU-03.md` **v4** y `docs/contratos/CONTRATO-HU-07.md` **v3** (aprobados por el humano vía PM el 2026-11-19); siguen vigentes HU-08 v4, HU-01 v5 y HU-02 v3
**Rama:** `hu-03` (base `main` `b8e3210`) · **Código del DEV:** `27d0b30`, `95073db`, `b82a63a` · **Pruebas del TESTER:** `c056068`, informe `5a3a67a`
**Fecha:** 2026-11-19 · **LEAD**, skill `veredicto`
**Resultado (vuelta 0):** **ROJO, vuelve en la vuelta 1.** Ningún rojo apunta al código. Hay 6 desvíos de las pruebas o del arnés (TESTER) y 1 hueco del contrato (R6), escalado al humano.

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

## 6. Matriz de trazabilidad

Se completa al cerrar la vuelta 1, con la corrida del LEAD.

## 7. Pregunta para el humano

**R6:** ¿los filtros de BIT-01 pueden ir plegados en una sección "Filtros ▾" que se despliega con un toque, o tienen que estar siempre a la vista, como en el wireframe? **Respuesta del humano (vía PM, 2026-11-19): pueden ir plegados (opción A)** → CONTRATO-HU-07 **v4**. A6 pasa al TESTER: la prueba despliega los filtros antes de usarlos.

## 8. Siguiente paso

Vuelta 1: el TESTER corrige A1 a A5 y A7 (M-5 del encargo). A6 espera la respuesta del humano. Después, el LEAD corre la suite completa y cierra el veredicto.
