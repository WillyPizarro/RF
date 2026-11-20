# VEREDICTO — HU-01 Iniciar sesión + HU-02 Acceso por rol

**Contratos:** `docs/contratos/CONTRATO-HU-01.md` **v5** (v4 en la vuelta 0) y `docs/contratos/CONTRATO-HU-02.md` **v3** (aprobados por el humano el 2026-11-19)
**Rama:** `hu-01` (base `main` `befd3d7`) · **Código del DEV:** `c1b432f` · **Pruebas del TESTER:** `af516e4`, informe `52649d7`
**Fecha:** 2026-11-19 · **LEAD**, skill `veredicto`
**Resultado:** **VERDE tras la vuelta 1** (A1, A2 y A3 cerrados; contrato HU-01 llevado a **v5**). Ningún rojo. Quedan `NO VERIFICADO` de entorno y casos diferidos por contrato (§7), para aceptación del humano.
*Vuelta 0:* **ROJO, vuelve en la vuelta 1.** Un rojo del código (R1, va al DEV) y dos de las pruebas (R2 y R3, van al TESTER). R4 y los 32 errores del Sprint 0 son de entorno.

---

## 1. Propiedad de rutas

`git log main..hu-01 --name-only`, agrupado por prefijo:

| Rol | Commits | Archivos | ¿Dentro de sus rutas? |
|---|---|---|---|
| `[DEV]` | `e6c6f22`, `c1b432f` | `apps/movil/` (sin `__tests__/`), `services/api/` (sin `tests/`), `contratos/api/openapi.json`, `infra/`, `informes/DEV-HU-01-02.md` | Sí |
| `[TESTER]` | `b32c4a3`, `2584e17`, `af516e4`, `52649d7` | `services/api/tests/`, `apps/movil/__tests__/`, `informes/TESTER-HU-01-02.md` | Sí |
| `[UX]` | `44712b9`, `12d9f78` | `docs/ux/revisiones/HU-01-02.md` | Sí |
| `[LEAD]` | 7 commits | `docs/contratos/` | Sí |

Ningún commit sin prefijo y ninguno con `Empezar.txt`. **Sin hallazgos.**

## 2. Versión del contrato

El DEV (`c1b432f`, M-4) y el TESTER (`af516e4` y la suite de M-5) trabajaron sobre HU-01 **v4** y HU-02 **v3**. El veredicto es válido.

## 3. Corrida del LEAD (no se confió en los informes)

| Corrida | Comando | Resultado |
|---|---|---|
| App | `npx jest --ci` en `apps/movil` | **32 en verde, 1 rojo** (`AUTH-03 › un 401 SESION_VENCIDA…`): coincide con el TESTER |
| Evidencia de R2 | `psql` en `db`: eventos de la bitácora de `inactivo1` | 4 `LOGIN_FALLIDO` del 19-nov entre las 22:58 y las 22:59 UTC, anteriores a la corrida. El 5.º, a las 00:21:06, va con `CUENTA_BLOQUEADA`, y el de las 00:21:13 con `codigo_error = CUENTA_BLOQUEADA`. Coincide con el TESTER |
| Revisión del código para R1 | `apps/movil/src/sesion/controlador.ts` | Ver A1 |

La corrida completa de la API (52 min) la hace el LEAD en la vuelta 1, sobre los commits que la cierren.

## 4. Arbitraje

| # | Caso | Contrato | Prueba | Código | Desenlace | Destinatario | Vuelta |
|---|---|---|---|---|---|---|---|
| A1 (R1) | AUTH-03 por `401 SESION_VENCIDA` | HU-01 §4, AUTH-03: "`inactividad_s` sin que el usuario toque la pantalla, **o un `401 SESION_VENCIDA`**" → "Su sesión se cerró por inactividad. Ingrese de nuevo.". No pone condiciones sobre la solicitud que trae el 401 | Login `200` y luego `GET /v1/me` → `401 SESION_VENCIDA`; espera el aviso de inactividad | `cargarPerfil` (`controlador.ts:108-114`) convierte cualquier respuesta que no sea `200` en `null`, e `ingresar` (`:130-135`) cierra con `{ tipo: 'error' }` → mensaje genérico. `restaurar` (`:169-179`) tiene el mismo hueco: si la renovación da `200` y `/v1/me` da `401 SESION_VENCIDA`, mira el código de la renovación y cierra sin aviso | **Se apartó el código** | **DEV** | 1 |
| A2 (R2) | Usuario inactivo idéntico a la clave incorrecta; carga de usuarios idempotente (último paso) | HU-01 §1 (decisión 3) y §2 (decisión 5): el inactivo cuenta como fallo y el 5.º seguido bloquea | Supone que el contador de `inactivo1` está en 0, pero no lo asegura | Respondió `423`: era el 5.º fallo seguido (evidencia en §3) | **Se apartó la prueba**: el código cumplió | **TESTER** | 1 |
| A3 (R3) | `test_contrato_sin_rutas_de_negocio` (Sprint 0) | HU-01 §1 y §3 y HU-02 §1 crean `/v1/auth/*` y `/v1/me` | Exige un OpenAPI sin rutas de negocio (esqueleto del Sprint 0) | Publica las rutas que piden los contratos | **Se apartó la prueba** (quedó obsoleta) | **TESTER** | 1 |
| — (R4) | `test_simuladores_no_responde_desde_el_anfitrion` y los 32 errores de `sistema_sano` (Sprint 0) | — | Pasan por el proxy en `https://localhost` | — | **Entorno**: el puerto 80 lo ocupa `http.sys` (encargo, regla 8). `NO VERIFICADO`, igual que en el Sprint 0 y en HU-08 | — | — |

**Para A2, sin depender de un hueco del contrato:** el contrato no dice qué pasa con el contador cuando termina un bloqueo y el siguiente intento **falla** (§2 solo fija "clave correcta después de `bloqueado_hasta` → `200` y contador en 0"). Por eso la corrección no puede apoyarse en "esperar el fin del bloqueo y comprobar un `401`". Tiene que dejar a `inactivo1` en un estado conocido por un camino que el contrato sí fija. Por ejemplo, una configuración de la API con `BLOQUEO_INTENTOS` alto (§6: cambiar parámetros sin tocar código), o una carga de la base limpia. El hueco va como pregunta al humano (§7).

## 5. Matriz de trazabilidad (vuelta 0)

| Criterio de aceptación (HU) | Caso del contrato | Prueba | Resultado |
|---|---|---|---|
| HU-01 esc. 1: login correcto | §1 camino feliz, `LOGIN_OK` | `test_hu01_login.py::test_camino_feliz*`; Jest `AUTH-01 › login correcto` | 🟢 |
| HU-01 esc. 2: credenciales inválidas | §1 clave incorrecta, usuario inexistente | `::test_clave_incorrecta`, `::test_usuario_inexistente_identico`; Jest `AUTH-02` | 🟢 |
| HU-01 esc. 2 | §1 usuario inactivo idéntico | `::test_usuario_inactivo_identico` | 🔴 A2 (prueba) |
| HU-01 esc. 2 | §1 cuerpo inválido `422` (pendiente del Sprint 0), no cuenta como intento | `::test_cuerpo_invalido_422`, `test_hu01_bloqueo.py::test_cuerpo_invalido_no_cuenta_como_intento` | 🟢 |
| HU-01 esc. 2 | v4: AUTH-01 vacío no envía | Jest `AUTH-01 vacío (v4)` (6) | 🟢 |
| HU-01 esc. 4: bloqueo | §2 completo y AUTH-04 | `test_hu01_bloqueo.py` (6); Jest `AUTH-04` | 🟢 |
| HU-01 esc. 3: inactividad | §3 renovar, `NO_AUTENTICADO`, `SESION_VENCIDA` en el servidor, actividad, renovación como actividad (v3), logout | `test_hu01_sesion.py` (11) | 🟢 |
| HU-01 esc. 3 | §4 AUTH-03 por tiempo, borrado y "atrás" (v2), `touchStart` | Jest `AUTH-03` (3) | 🟢 |
| HU-01 esc. 3 | §4 AUTH-03 por `401 SESION_VENCIDA` | Jest `AUTH-03 › un 401 SESION_VENCIDA…` | 🔴 A1 (código) |
| HU-01 (otro error) | §4 red, 500, 503 → mensaje genérico | Jest `otro error` (3) | 🟢 |
| HU-01 bitácora | §5 campos, `id_traza`, la clave no queda en la bitácora ni en los logs de la API | `test_hu01_bitacora_config.py` | 🟢 |
| HU-01 bitácora | §5 sin registro no hay sesión (`503`) | — | `NO VERIFICADO`: pasa a HU-07 (decisión 2) |
| HU-01 bitácora | §5 la clave no queda en los logs del proxy | `::test_la_clave_no_queda_en_los_logs_del_proxy` | `NO VERIFICADO` (entorno, puerto 80) |
| HU-01 configuración | §6 parámetros, cambio sin tocar código, `CLAVE_USUARIOS_PRUEBA` | `test_hu01_bitacora_config.py` | 🟢 |
| HU-01 configuración | §6 carga de usuarios idempotente | `::test_carga_de_usuarios_idempotente` | 🟢 salvo el último paso (A2) |
| HU-02 esc. 1: inicio según el rol | §1 `GET /v1/me`; §3 inicio de agente, revisor y supervisor; menú desde `/v1/me` | `test_hu02_perfil_roles.py::test_perfil`; Jest `HU-02 — inicio por rol` | 🟢 |
| HU-02 esc. 2: rol no se falsifica | §1 token manipulado, rol del cliente ignorado, sin token → `401` sin `ACCESO_DENEGADO` | `test_hu02_perfil_roles.py` | 🟢 |
| HU-02 esc. 2: acceso denegado | §2 matriz de `403 SIN_PERMISO` + `ACCESO_DENEGADO` | `::test_matriz_403_sin_permiso` (skip) | `NO VERIFICADO`: no hay rutas de rol, pasa a HU-03 y HU-07 (decisión 3) |
| HU-02 esc. 2 | §3 ERR-01 | — | Diferido a HU-03 (v3, aprobado) |
| HU-02 "Salir" | §3 logout, SecureStore vacío, "atrás" | Jest `› Salir…` | 🟢 |
| Regresión HU-08 | CONTRATO-HU-08 v4 | simuladores: 115 (contenedor) + 136 (anfitrión) | 🟢 (TESTER; el LEAD la repite en la vuelta 1) |
| Regresión Sprint 0 | `SPRINT0.md` | `test_contrato_openapi.py::test_contrato_sin_rutas_de_negocio` | 🔴 A3 (prueba obsoleta) |
| Regresión Sprint 0 | `SPRINT0.md` (todo lo que pasa por el proxy) | `sistema_sano` (32), `test_red.py` | `NO VERIFICADO` (entorno, puerto 80) |

**Casos sin criterio de la HU** (el negocio ya los aprobó como decisiones del contrato): el usuario inexistente que también se bloquea (decisión 5), la idempotencia de la carga de usuarios (decisión 8) y AUTH-01 vacío (v4).

## 6. Trampas

- **El código no tiene casos especiales** para los usuarios de prueba. `inactivo1` y los demás solo aparecen en la carga de usuarios.
- **Las pruebas sí verifican:** tienen aserciones sobre los textos, los códigos y los eventos que fija el contrato.
- **Los cambios de las pruebas entre vueltas** (`b32c4a3` → `2584e17` → `af516e4`) siguen la v3 y la v4 de HU-01, aprobadas por el humano.
- **AUTH-04, redondeo de los minutos:** el contrato no lo fija y la prueba acepta el entero por abajo o por arriba. Es una tolerancia razonable, no una trampa, porque el texto lo muestra igual.
- **Sin trampas detectadas.**

## 7. Preguntas para el humano y `NO VERIFICADO`

**Pregunta (hueco de HU-01 §2):** cuando termina un bloqueo y el siguiente intento falla, ¿el contador empieza de nuevo (es el fallo 1 de 5) o la cuenta se vuelve a bloquear con ese fallo? El código hace lo primero (`services/api/app/auth.py:110`). **Respuesta del humano (2026-11-19): empieza de nuevo** → CONTRATO-HU-01 **v5** y M-7 del encargo.

**`NO VERIFICADO` para aceptación del humano:**

1. Capturas del emulador (el humano ya aceptó la revisión del UX solo con Jest, M-3).
2. La clave en los logs del proxy y todas las pruebas del Sprint 0 que pasan por el proxy (puerto 80 ocupado por `http.sys`).
3. Sin registro en la bitácora no hay sesión (`503`): pasa a HU-07 (decisión 2).
4. Matriz de `403 SIN_PERMISO` y ERR-01: pasan a HU-03 y HU-07 (HU-02, decisión 3 y v3).

## 7 bis. Vuelta 1 (2026-11-19)

**Commits:** `1e6dd71 [DEV]` (A1: `apps/movil/src/sesion/controlador.ts`, `informes/DEV-HU-01-02.md`); `00f273a [TESTER]` (A2 y A3), `f750578 [TESTER]` (prueba de la v5), `354edfc [TESTER]` (M-8: las pruebas del proxy se omiten en 2 s como `NO VERIFICADO`). Todos dentro de sus rutas. Contratos: HU-01 **v5**, HU-02 **v3**.

**Corrida del LEAD sobre la punta `354edfc`**, con `up -d --build` y los dos archivos de compose, y los usuarios cargados (exit 0):

| Corrida | Comando | Resultado |
|---|---|---|
| API | `pytest services/api/tests --integracion -rA` (5 min 20 s) | **67 en verde, 0 rojos, 36 omitidas**: 33 del proxy ("NO VERIFICADO: puerto 80 ocupado por http.sys") y 3 de HU-01/02 (la clave en los logs del proxy, el `503` que pasa a HU-07 y la matriz de `403` que pasa a HU-03 y HU-07) |
| App | `npx jest --ci` | **33 de 33 en verde** |
| Simuladores, contenedor | `run --rm -T --no-deps simuladores pytest` | **115 en verde, 27 omitidas** (las del anfitrión) |
| Simuladores, anfitrión | `pytest services/simuladores/tests --integracion` | **136 en verde, 6 omitidas** |
| Configuración final de `api` | `printenv` | 600 / 900 / 5 / 900 (`infra/.env`) |

**Cierres:**

- **A1 🟢:** `cargarPerfil` informa si el `401` fue `SESION_VENCIDA`, e `ingresar` y `restaurar` cierran con el aviso de inactividad. El arreglo es general, sin casos especiales. **Observación (no es rojo):** la suite del TESTER no prueba el camino de retomar la sesión (`restaurar`); el DEV lo comprobó con un Jest temporal. Queda anotado para HU-03, que vuelve a tocar la app.
- **A2 🟢:** `test_usuario_inactivo_identico` y `test_carga_de_usuarios_idempotente` corren con `BLOQUEO_INTENTOS=1000` (§6).
- **A3 🟢:** `test_contrato_rutas_vigentes` exige exactamente `/v1/salud`, `/v1/auth/{login,refresh,logout}` y `/v1/me`.
- **v5 🟢:** `test_fallo_despues_del_bloqueo_empieza_de_nuevo` pasa en sus 3 variantes (clave incorrecta, usuario inexistente, usuario inactivo).
- **Trampas:** ninguna. Los cambios de las pruebas responden a M-6, M-7 y M-8, y la M-8 omite sin dar verde (`PROXY_DISPONIBLE=1` las fuerza a correr).

**La matriz del §5 queda toda en 🟢**, salvo los `NO VERIFICADO` y los casos diferidos del §7.

## 7 ter. Aceptación del humano (vía PM, 2026-11-19)

- Los 4 `NO VERIFICADO` del §7 quedan **aceptados**. El PM hizo el merge: `main` = `b8e3210` (fast-forward) y quedó subida a origin. No hizo falta descripción de PR.
- **Condición nueva: se arregla el puerto 80.** El proxy tendrá un puerto local alterno configurable (por ejemplo `PROXY_PUERTO_HTTP=8080`; en el VPS sigue el 80/443). Las 33 pruebas de `sistema_sano` y la de la clave en los logs del proxy lo usarán. Entra en la rama `hu-03` (`docs/contratos/ENCARGO-HU-03-07.md`). **Desde el veredicto de HU-03/07 esas pruebas tienen que correr en verde**, no como `NO VERIFICADO`. La M-8 (omitirlas si el proxy no responde) queda solo como respaldo.
- **Despliegue:** se agrega como chequeo **obligatorio** que la clave no quede en los logs del proxy en el VPS (`docs/contratos/PENDIENTES.md`).

## 8. Siguiente paso

Cerrado. Lo que sigue va en `hu-03` (HU-03 + HU-07).
