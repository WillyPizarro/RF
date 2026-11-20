# CONTRATO — HU-07 Registrar cada consulta en una bitácora

**Tipo:** Feature
**Versión:** v4
**Estado:** Aprobado (v1 a v4: 2026-11-19, humano vía PM)
**Origen:** `docs/hus/HU-07-bitacora-consultas.md` · encargo PM → LEAD (2026-11-19), Iteración 1, contrato 5 de 5
**Rama de trabajo:** `hu-03`, la misma de HU-03 (CONTRATO-HU-03, decisión 1)
**Pasa por UX:** Sí. Pantallas BIT-01 y BIT-02 (`docs/ux/wireframes/HU-07-bitacora-consultas.md`), revisadas con capturas de Jest y del emulador.

---

## Paquete de contexto

| Fuente | Por qué entra |
|---|---|
| HU-07 | Historia y escenarios 1 a 3 |
| ADR-0005 | Solo inserción por permisos más trigger, rol `api_app`, fail-closed, consulta por el supervisor con filtros y cursor, contenido mínimo |
| ADR-0003 | El rol `supervisor` consulta; `agente` y `revisor`, no |
| ADR-0007 | `GET /v1/bitacora?usuario&desde&hasta&tipo&resultado&cursor` |
| ADR-0008 | La bitácora se conserva todo el proyecto, sin purga |
| TECH-DESIGN.md › Modelo de datos y Criterios › Bitácora | Columnas, tipos de evento y criterios (`UPDATE`/`DELETE`/`TRUNCATE`, fail-closed, filtros, sin imagen ni clave) |
| CONTRATO-HU-01 decisión 2 | La tabla `bitacora` nace en HU-01; HU-07 la blinda |
| CONTRATO-HU-03 | Eventos `CONSULTA_PLACA` y `ERROR_FUENTE`; resultados de placa |
| `docs/contratos/PENDIENTES.md` | `ERROR_FUENTE` con `codigo_error` (desde HU-08) |
| Wireframes BIT-01, BIT-02 | Textos y comportamiento de la pantalla |

**Puntos abiertos de la HU:** "quién consulta y con qué filtros" (PA #24) y PA #9 los resuelve el ADR-0003/0005 (supervisor, desde la app, cuatro filtros); en pantalla se mantienen con la marca PA 24. PA #16 (retención) lo cubre el ADR-0008 para el MVP. **El escenario 3 (registro de verificación facial) se prueba en HU-05**, que es la HU que genera ese evento (DECISIÓN PROPUESTA 1).

## Interfaz observable

1. **Base de datos:** la tabla `bitacora`, el rol `api_app` y las operaciones `UPDATE`, `DELETE` y `TRUNCATE`.
2. **API:** `GET /v1/bitacora` y el comportamiento fail-closed de cualquier operación que registra.
3. **App:** pantallas BIT-01 y BIT-02.

## Comportamiento

### 1. Solo inserción (Gherkin esc. 2)

| Caso | Entrada | Salida esperada | Origen |
|---|---|---|---|
| La API usa `api_app` | Una solicitud que escribe en la bitácora | La conexión de la API a Postgres usa el rol `api_app` (visible en `pg_stat_activity.usename`), no el dueño de la tabla | ADR-0005 §1 |
| Permisos | — | `api_app` tiene `INSERT` y `SELECT` sobre `bitacora`, y no tiene `UPDATE`, `DELETE` ni `TRUNCATE` | ADR-0005 §1 |
| `UPDATE` como `api_app` | `UPDATE bitacora SET motivo='x' WHERE id=…` | Error; el registro queda igual | Gherkin esc. 2, TDD |
| `DELETE` como `api_app` | `DELETE FROM bitacora WHERE id=…` | Error; el registro sigue | Gherkin esc. 2, TDD |
| `TRUNCATE` como `api_app` | `TRUNCATE bitacora` | Error; los registros siguen | TDD |
| Mismo intento como dueño | Las tres operaciones con el rol dueño de la tabla (el que corre las migraciones) | Error por el trigger, con un mensaje que contiene `bitacora es de solo insercion`; los registros quedan iguales | ADR-0005 §1, TDD · DECISIÓN PROPUESTA 2 |
| Base recién migrada | `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env run --rm api alembic upgrade head`, con `MIGRACION_DATABASE_URL` apuntando a una base vacía | Deja la tabla, los permisos y los triggers listos | TDD · **v2** |
| Base destino de la migración (**v2**) | `MIGRACION_DATABASE_URL`: URL de la base con el rol dueño, en `infra/.env`, nunca versionada (en `infra/.env.example` sin clave). Si falta, la migración usa la base del proyecto | Pregunta del TESTER · **v2** |
| Sin ruta de edición | — | La API no tiene ninguna ruta para modificar o borrar registros (`PUT`, `PATCH` o `DELETE` sobre `/v1/bitacora*` → `405 METODO_NO_PERMITIDO`) | Gherkin esc. 2 |

### 2. Contenido de cada registro (Gherkin esc. 1)

| Caso | Salida esperada | Origen |
|---|---|---|
| Columnas | `id`, `ocurrido_en` (UTC, del servidor), `usuario_id`, `rol`, `tipo_evento`, `motivo`, `parametros` (JSON), `resultado`, `score`, `version_modelo`, `version_umbral`, `captura_id`, `consulta_id`, `codigo_error`, `id_traza`, `es_sintetico` (siempre `true`) | ADR-0005 §4, TDD |
| Consulta de placa | `CONSULTA_PLACA`: usuario, rol, `motivo` (código y, si es "Otro", su texto), `parametros.placa`, `resultado` y `consulta_id` | Gherkin esc. 1, CONTRATO-HU-03 |
| Consulta con error | `ERROR_FUENTE`: los mismos campos, más `resultado = "error"`, `codigo_error` y `parametros.fuente` | Gherkin esc. 1 ("con éxito o con error"), CONTRATO-HU-03 |
| Eventos de esta iteración | Cada uno de `LOGIN_OK`, `LOGIN_FALLIDO`, `CUENTA_BLOQUEADA`, `LOGOUT`, `SESION_VENCIDA`, `ACCESO_DENEGADO`, `CONSULTA_PLACA`, `ERROR_FUENTE` y `CONSULTA_BITACORA` se genera en al menos una prueba. Los eventos biométricos y de revisión llegan con HU-05 y HU-06 | TDD · DECISIÓN PROPUESTA 1 |
| Sin imagen ni clave | Ningún registro contiene la clave de un login ni datos de imagen (ninguna cadena base64 de imagen ni bytes de imagen en `parametros`) | TDD, Gherkin esc. 3 |

### 3. Sin registro no hay resultado (fail-closed)

| Caso | Entrada | Salida esperada | Origen |
|---|---|---|---|
| Falla la escritura | Con el `INSERT` sobre `bitacora` revocado a `api_app` en la base de pruebas (`REVOKE INSERT ON bitacora FROM api_app`), una consulta de placa válida | `503 SERVICIO_NO_DISPONIBLE` ("No se pudo completar la operación; intente nuevamente"), **sin** el resultado. Al restaurar el permiso, todo vuelve a la normalidad | ADR-0005 §2, TDD · DECISIÓN PROPUESTA 3 |
| Lo mismo en el login | Igual, con un login válido | `503 SERVICIO_NO_DISPONIBLE`, sin tokens | CONTRATO-HU-01 decisión 2 |

### 4. Consultar la bitácora

```text
GET /v1/bitacora?usuario=<usuario>&desde=<ISO 8601>&hasta=<ISO 8601>&tipo=<TIPO_EVENTO>&resultado=<resultado>&limite=<n>&cursor=<texto>   (rol supervisor)
```

| Caso | Entrada | Salida esperada | Origen |
|---|---|---|---|
| Lista | Sin filtros | `200` `{"registros":[…],"siguiente_cursor":"<texto o null>"}`, del más reciente al más antiguo (`ocurrido_en` y luego `id`, descendentes). `limite` por defecto 50, máximo 100 | ADR-0005 §3, ADR-0007 · DECISIÓN PROPUESTA 4 |
| Forma de un registro | — | `{"id","ocurrido_en","usuario" (nombre de usuario o null),"rol","tipo_evento","motivo","parametros","resultado","score","captura_id","consulta_id","codigo_error","es_sintetico"}` | ADR-0005 §4 · DECISIÓN PROPUESTA 4 |
| Filtro por usuario | `usuario=agente1` | Solo los registros de ese usuario | ADR-0005 §3 |
| Filtro por fechas | `desde` y `hasta` | Registros con `desde ≤ ocurrido_en < hasta` | ADR-0005 §3 |
| Filtro por tipo | `tipo=CONSULTA_PLACA` | Solo ese tipo | ADR-0005 §3 |
| Filtro por resultado | `resultado=con_requisitoria` | Solo ese resultado | ADR-0005 §3 |
| Filtros combinados | Varios filtros | Se combinan con Y | ADR-0005 §3 |
| Paginación | Seguir `siguiente_cursor` hasta `null` | Recorre todos los registros del filtro sin repetir ni saltar ninguno, aunque entren registros nuevos mientras se pagina | ADR-0005 §3 |
| Parámetro inválido | Fecha mal formada, `tipo` desconocido, `limite` fuera de 1 a 100 o cursor inválido | `422 SOLICITUD_INVALIDA` | SPRINT0 M-1 B |
| La consulta se registra | Cada `GET /v1/bitacora` exitoso | Evento `CONSULTA_BITACORA` con los filtros usados en `parametros` | TDD (tipo de evento) |
| Otros roles | `agente` o `revisor` | `403 SIN_PERMISO` + `ACCESO_DENEGADO` | Gherkin, ADR-0003, CONTRATO-HU-02 |

### 5. App (rol supervisor)

| Pantalla | Resultado visible | Origen |
|---|---|---|
| Acceso | "Bitácora" en el inicio del supervisor se habilita y abre BIT-01 | CONTRATO-HU-02 decisión 4 |
| BIT-01 | Lista del más reciente al más antiguo. Cada tarjeta muestra fecha y hora local (`dd/mm hh:mm`), el usuario (o "sistema" si es nulo), la etiqueta del tipo de evento, el resultado si existe y la marca "SINTÉTICO". Filtros de fecha, usuario, tipo y resultado con la marca "PA 24": título "Filtros", etiquetas "Usuario", "Desde", "Hasta", "Tipo" y "Resultado", ayuda "dd/mm/aaaa" en "Desde" y "Hasta", y botón "Aplicar filtros". Los filtros pueden ir plegados bajo "Filtros ▾" y se despliegan con un toque (**v4**). Una fecha que no cumple `dd/mm/aaaa` muestra "Use fechas con el formato dd/mm/aaaa." y no envía la solicitud (**v3**). "Cargar más" al final mientras haya `siguiente_cursor`. **Sin** botones de editar, borrar ni exportar | BIT-01 · DECISIÓN PROPUESTA 5 |
| BIT-02 | Al tocar un registro: "Registro #<primeros 8 caracteres del id>" (**v3**), "Registro de solo lectura", "ID" con el id completo (**v3**), usuario, fecha y hora completas, tipo, motivo, resultado, código de error si existe, y "Origen: datos sintéticos". En un registro de placa no hay "ID de captura" ni "Score" | BIT-02 |
| Etiquetas de tipo | `LOGIN_OK` "Inicio de sesión" · `LOGIN_FALLIDO` "Intento fallido" · `CUENTA_BLOQUEADA` "Cuenta bloqueada" · `LOGOUT` "Cierre de sesión" · `SESION_VENCIDA` "Sesión vencida" · `ACCESO_DENEGADO` "Acceso denegado" · `CONSULTA_PLACA` "Consulta de placa" · `ERROR_FUENTE` "Error de fuente" · `CONSULTA_BITACORA` "Consulta de bitácora" | BIT-01 · DECISIÓN PROPUESTA 5 |
| Etiquetas de resultado | `con_requisitoria` "Tiene requisitoria" · `sin_requisitoria` "Sin requisitoria registrada" · `placa_no_registrada` "Placa no registrada" · `error` "Error" | CONTRATO-HU-03 · DECISIÓN PROPUESTA 5 |
| Errores | `503`, error de red o respuesta inesperada → "No se pudo cargar la bitácora; intente nuevamente" con "Reintentar". Nunca una lista vacía en su lugar | Regla 7 · DECISIÓN PROPUESTA 6 |
| Lista vacía real | `200` sin registros → "No hay registros para estos filtros." | DECISIÓN PROPUESTA 6 |

## Nombres que no se negocian

| Tipo | Valor exacto |
|---|---|
| Tabla y rol | `bitacora` · `api_app` |
| Ruta | `GET /v1/bitacora` |
| Parámetros | `usuario`, `desde`, `hasta`, `tipo`, `resultado`, `limite`, `cursor` |
| Campos de respuesta | `registros`, `siguiente_cursor` y los campos de cada registro del §4 |
| Eventos | `LOGIN_OK`, `LOGIN_FALLIDO`, `CUENTA_BLOQUEADA`, `LOGOUT`, `SESION_VENCIDA`, `ACCESO_DENEGADO`, `CONSULTA_PLACA`, `ERROR_FUENTE`, `CONSULTA_BITACORA` (más los de HU-05 y HU-06 del TDD, cuando lleguen) |
| Códigos | `503 SERVICIO_NO_DISPONIBLE` · `422 SOLICITUD_INVALIDA` · `403 SIN_PERMISO` · `405 METODO_NO_PERMITIDO` |
| Mensaje del trigger | contiene `bitacora es de solo insercion` |
| Textos de la app | "Bitácora" · "SINTÉTICO" · "PA 24" · "sistema" · "Cargar más" · "Registro #" · "Registro de solo lectura" · "ID" · "Filtros" · "Usuario" · "Desde" · "Hasta" · "Tipo" · "Resultado" · "dd/mm/aaaa" · "Aplicar filtros" · "Use fechas con el formato dd/mm/aaaa." (v3) · "Origen: datos sintéticos" · las etiquetas del §5 · "No se pudo cargar la bitácora; intente nuevamente" · "Reintentar" · "No hay registros para estos filtros." |

## Rutas de cada rol

Las mismas que CONTRATO-HU-03 (AGENTS.md). Las migraciones (`services/api/alembic/`) son del DEV.

## Decisiones propuestas (no venían en la tarea)

| # | Decisión | Por qué hace falta | Estado |
|---|---|---|---|
| 1 | El escenario 3 (registro facial con id de captura y score, sin imagen) y los eventos biométricos y de revisión se prueban en HU-05 y HU-06. Aquí solo se verifica que ningún registro tenga una imagen | Hoy no existe ninguna verificación facial que genere esos eventos | Aprobada por el humano (2026-11-19) |
| 2 | El mensaje del trigger contiene `bitacora es de solo insercion` | Así la prueba distingue el rechazo del trigger de otro error | Aprobada por el humano (2026-11-19) |
| 3 | El fail-closed se provoca revocando el `INSERT` a `api_app` en la base de pruebas, sin agregar código ni rutas solo para pruebas | Es una falla real de escritura, reproducible y reversible (SPRINT0 M-2) | Aprobada por el humano (2026-11-19) |
| 4 | Forma de la respuesta: `registros` y `siguiente_cursor`, `limite` 50/100, orden descendente, `usuario` como nombre de usuario | ADR-0007 da los parámetros, no la forma de la respuesta | Aprobada por el humano (2026-11-19) |
| 5 | Etiquetas de los tipos de evento y de los resultados, y "Cargar más" para paginar | El wireframe muestra ejemplos, no la lista completa | Aprobada por el humano (2026-11-19) |
| 6 | Un error al cargar se muestra como error, nunca como lista vacía, y la lista vacía real tiene su propio texto | Regla 7 aplicada a la bitácora | Aprobada por el humano (2026-11-19) |

## Fuera del contrato (decide el DEV)

- El índice, el formato del cursor, cómo se crea `api_app` y las credenciales del rol dueño (en `infra/.env`, nunca versionadas). El comando y la variable de la migración los fija §1 (v2).
- Cómo agrupa la app los filtros en pantalla.

## Preguntas abiertas para el humano

Respondidas por el humano (vía PM) el 2026-11-19:

1. **Decisiones 1 a 6:** aprobadas tal cual.
2. **`api_app` en el Supabase del VPS:** queda fuera de este veredicto, como tarea **obligatoria** del despliegue (anotada en `docs/contratos/PENDIENTES.md`).

## Changelog

| Versión | Fecha | Cambio | Motivo | Aprobado por |
|---|---|---|---|---|
| v1 | 2026-11-19 | Versión inicial | Encargo PM → LEAD, Iteración 1 | Humano (vía PM), 2026-11-19 |
| v2 | 2026-11-19 | §1: la migración se corre con `docker compose … run --rm api alembic upgrade head` y la base destino va en `MIGRACION_DATABASE_URL` (rol dueño, en `infra/.env`, nunca versionada; si falta, la base del proyecto) | Pregunta del TESTER: el contrato no decía cómo correr la migración sobre una base vacía | Humano (vía PM), 2026-11-19 |
| v3 | 2026-11-19 | §5: BIT-02 con título "Registro #<primeros 8 caracteres del id>" y el id completo en el campo "ID"; BIT-01 con los textos de los filtros ("Filtros", "Usuario", "Desde", "Hasta", "Tipo", "Resultado", "dd/mm/aaaa", "Aplicar filtros") y el error "Use fechas con el formato dd/mm/aaaa." | Revisión UX de HU-03/07, observaciones 1 y 3 (`docs/ux/revisiones/HU-03-07.md`) | Humano (vía PM), 2026-11-19 |
| v4 | 2026-11-19 | §5: los filtros de BIT-01 pueden ir plegados bajo "Filtros ▾" y se despliegan con un toque | Veredicto de la vuelta 0, A6 (R6): el contrato no decía si iban a la vista o plegados | Humano (vía PM), 2026-11-19 |
