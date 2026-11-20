# CONTRATO — HU-03 Consultar si una placa tiene requisitoria (ingreso manual)

**Tipo:** Feature
**Versión:** v3
**Estado:** Aprobado (v1: 2026-11-19, humano vía PM · v2: 2026-11-19, humano · v3: 2026-11-19, humano vía PM)
**Origen:** `docs/hus/HU-03-consultar-placa.md` · encargo PM → LEAD (2026-11-19), Iteración 1, contrato 4 de 5
**Rama de trabajo:** `hu-03` (HU-03 + HU-07), desde `main` después del merge de `hu-01` (o desde `hu-01`, rebasada después)
**Pasa por UX:** Sí. Pantallas PLA-01 a PLA-07 (`docs/ux/wireframes/HU-03-consultar-placa.md`) y una pantalla nueva para la placa no registrada (DECISIÓN PROPUESTA 3). Se revisa con capturas de Jest y del emulador contra los wireframes, como en HU-01.

---

## Paquete de contexto

| Fuente | Por qué entra |
|---|---|
| HU-03 | Historia y escenarios 1 a 5 |
| TECH-DESIGN.md › Criterios › Consulta de placa | Resultados, `MOTIVO_REQUERIDO`, `PLACA_FORMATO_INVALIDO`, `FUENTE_NO_DISPONIBLE`, máximo 1 reintento |
| TECH-DESIGN.md › Modelo de datos | `consulta`, `motivo_catalogo`, eventos `CONSULTA_PLACA` y `ERROR_FUENTE` |
| ADR-0006, ADR-0014 | Adaptador de placas, validación contra el contrato de la fuente, timeout de 3 s, 1 reintento, errores estables, nunca un negativo por error |
| ADR-0011 | Formato de placa (regex configurable, PA #20) y motivo (catálogo configurable + "Otro" de ≥ 10 caracteres, PA #21); p95 ≤ 2 s (PA #4) |
| ADR-0005 | Registro antes de responder (fail-closed) |
| ADR-0003, CONTRATO-HU-02 | Solo `agente`; `403 SIN_PERMISO` con `ACCESO_DENEGADO` para los demás roles |
| ADR-0007 | `POST /v1/consultas/placa`; la validación vive en la API |
| CONTRATO-HU-08 v4 | Fuente `placas` (`ZZA-101`, `ZZB-201`, `ZZZ-999`), modos de falla y `FUENTE_PLACAS_URL` |
| CONTRATO-HU-01 | Tabla `bitacora`, `503 SERVICIO_NO_DISPONIBLE` y usuarios fijos |
| `docs/contratos/PENDIENTES.md` | Mitad de la API de HU-08 (errores, mock) y la placa no registrada |
| Wireframes PLA-01 a PLA-07 | Textos y comportamiento de la pantalla |

**Puntos abiertos de la HU:** PA #20, PA #21 y PA #4 se cubren con los valores provisionales del ADR-0011, como ordena el encargo. **PA #15** (qué se muestra en el resultado) sigue abierto: el contrato usa la variante "Solo estado" (DECISIÓN PROPUESTA 4). La sesión del 25-nov puede cambiar el motivo y los datos visibles; si cambian, se versiona el contrato.

## Interfaz observable

1. **API:** `GET /v1/motivos` y `POST /v1/consultas/placa`.
2. **App:** pantallas PLA-01 a PLA-07, y PLA-08 (nueva).
3. **Base de datos:** filas de `bitacora` y `consulta`.
4. **Configuración:** `PLACA_FORMATO_REGEX`, `PLACA_FORMATO_DESCRIPCION` y el catálogo de motivos.

## Comportamiento

### 1. Catálogo de motivos

```text
GET /v1/motivos   (rol agente)
```

| Caso | Salida esperada | Origen |
|---|---|---|
| Catálogo | `200` `{"motivos":[{"codigo":"control_vehicular","descripcion":"Control vehicular"},{"codigo":"intervencion_policial","descripcion":"Intervención policial"},{"codigo":"denuncia","descripcion":"Denuncia"},{"codigo":"operativo","descripcion":"Operativo"},{"codigo":"otro","descripcion":"Otro"}],"formato_placa":{"regex":"^[A-Z0-9]{3}-[0-9]{3}$","descripcion":"ABC-123 (3 letras o números, guion, 3 números)"}}`. Solo los activos; `otro` siempre va al final | ADR-0011 (catálogo inicial, provisional PA #21) · DECISIÓN PROPUESTA 5 |
| Formato de placa (**v3**) | `formato_placa.regex` y `formato_placa.descripcion` son los valores vigentes de `PLACA_FORMATO_REGEX` y `PLACA_FORMATO_DESCRIPCION` (§7). Si cambian, la respuesta cambia sin tocar código | DECISIÓN 9 · **v3** |
| Configurable | Agregar o desactivar un motivo en `motivo_catalogo` cambia la respuesta sin tocar código | ADR-0011 |
| Otro rol | `revisor` o `supervisor` → `403 SIN_PERMISO` + `ACCESO_DENEGADO` | CONTRATO-HU-02 |

### 2. Consultar placa

```text
POST /v1/consultas/placa   (rol agente)
{"placa": "<texto>", "motivo_codigo": "<codigo>", "motivo_texto": "<texto o null>"}
```

La API recorta los espacios y pasa la placa a mayúsculas antes de validar. El orden de validación es: motivo, formato, fuente.

| Caso | Entrada | Salida esperada | Origen |
|---|---|---|---|
| Con requisitoria | `ZZA-101`, motivo válido | `200` `{"consulta_id":"…","placa":"ZZA-101","resultado":"con_requisitoria","motivo":{"codigo":"…","texto":…},"consultado_en":"<ISO 8601 UTC>"}` · bitácora `CONSULTA_PLACA` con usuario, rol, motivo, `parametros.placa` y `resultado` · fila en `consulta` con `estado = completada` | Gherkin esc. 1, TDD |
| Sin requisitoria | `ZZB-201`, motivo válido | `200` con `"resultado":"sin_requisitoria"` · bitácora `CONSULTA_PLACA` | Gherkin esc. 5, TDD |
| Placa no registrada | `ZZZ-999` (la fuente responde `404 PLACA_NO_REGISTRADA`) | `200` con `"resultado":"placa_no_registrada"`. **Nunca** `sin_requisitoria` · bitácora `CONSULTA_PLACA` con ese resultado | CONTRATO-HU-08 decisión 3, regla 7 · DECISIÓN PROPUESTA 3 |
| Minúsculas y espacios | `" zza-101 "` | Igual que `ZZA-101` | DECISIÓN PROPUESTA 6 |
| Sin motivo | Falta `motivo_codigo`, viene vacío o no está en el catálogo activo | `422` `{"codigo":"MOTIVO_REQUERIDO","mensaje":"Indique el motivo de la consulta",…}` · **no consulta la fuente** · sin evento | Gherkin esc. 2, TDD |
| "Otro" corto | `motivo_codigo = otro` y `motivo_texto` recortado < 10 caracteres | `422` `{"codigo":"MOTIVO_REQUERIDO","mensaje":"Describa el motivo (mínimo 10 caracteres)",…}` · no consulta la fuente | ADR-0011, PLA-02 |
| Formato inválido | `HOLA MUNDO`, `ABC123`, `AB-1234` | `422` `{"codigo":"PLACA_FORMATO_INVALIDO","mensaje":"El formato de placa no es válido. Formato esperado: <PLACA_FORMATO_DESCRIPCION>",…}` · no consulta la fuente | Gherkin esc. 4, TDD, ADR-0011 |
| Faltan los dos | Sin motivo y formato inválido | `422 MOTIVO_REQUERIDO` (primero el motivo) | DECISIÓN PROPUESTA 7 |
| Cuerpo mal formado | JSON inválido o `placa` ausente | `422 SOLICITUD_INVALIDA` | SPRINT0 M-1 B |
| Otro rol | `revisor` o `supervisor` | `403 SIN_PERMISO` + `ACCESO_DENEGADO` · no consulta la fuente | CONTRATO-HU-02 (matriz) |

### 3. Errores de la fuente (mitad de la API de HU-08)

Se fuerzan con `PUT http://simuladores:8001/control/modos/placas` (CONTRATO-HU-08 §5).

| Caso | Modo de la fuente | Salida esperada | Origen |
|---|---|---|---|
| Fuente caída | `error_500` | `503` `{"codigo":"FUENTE_NO_DISPONIBLE","mensaje":"No se pudo completar la consulta; intente nuevamente",…}` tras **un solo reintento** (2 llamadas a la fuente en total) · bitácora `ERROR_FUENTE` · nunca `sin_requisitoria` | Gherkin esc. 3, ADR-0014, PENDIENTES |
| Fuente lenta | `latencia` (5000 ms, mayor que `FUENTE_TIMEOUT_S` = 3) | `503 FUENTE_NO_DISPONIBLE` tras un reintento · bitácora `ERROR_FUENTE` · responde en ≤ 7 s | ADR-0014 (peor caso ~6,2 s) |
| Respuesta fuera de contrato | `malformada` | `502` `{"codigo":"FUENTE_RESPUESTA_INVALIDA","mensaje":"No se pudo completar la consulta; intente nuevamente",…}` **sin reintento** · bitácora `ERROR_FUENTE` | Gherkin HU-08 esc. 3, ADR-0006 §3 · DECISIÓN PROPUESTA 8 |
| Evento de error | Cualquiera de los tres | `ERROR_FUENTE` con usuario, rol, motivo, `parametros.placa`, `parametros.fuente = "placas"`, `resultado = "error"`, `codigo_error`, `id_traza` y `consulta_id` · fila en `consulta` con `resultado = error` y `estado = error` | ADR-0005, PENDIENTES (HU-07) |
| Vuelve la fuente | Modo `normal` después de un error | La siguiente consulta funciona normal | ADR-0014 (sin circuit breaker) |

### 4. Reemplazo de la fuente (HU-08 esc. 2, mitad de la API)

| Caso | Salida esperada | Origen |
|---|---|---|
| Mock del contrato | Con `FUENTE_PLACAS_URL` apuntando a un mock generado **solo** desde `contratos/fuentes/placas.yaml` (por ejemplo Prism) y la API reiniciada, `POST /v1/consultas/placa` con una placa válida responde `200` con un `resultado` válido, sin cambios en la app ni en el código | HU-08 esc. 2, TDD › HU-08 criterio 2 |

Si el mock no se puede descargar en el equipo, el caso se reporta `NO VERIFICADO` con el motivo.

### 5. Registro obligatorio (fail-closed)

| Caso | Salida esperada | Origen |
|---|---|---|
| Falla la escritura de la bitácora | La consulta responde `503 SERVICIO_NO_DISPONIBLE` y **no** devuelve el resultado. La forma de provocar la falla la fija CONTRATO-HU-07 §3 | ADR-0005 §2, CONTRATO-HU-01 |

### 6. App

| Pantalla | Acción o respuesta | Resultado visible | Origen |
|---|---|---|---|
| Acceso | "Consultar placa" en HOME-01 | Se habilita y abre PLA-01 | CONTRATO-HU-02 decisión 4 |
| PLA-01 | — | Campo "Placa" (en mayúsculas, con fuente monoespaciada), selector "Motivo de consulta *" con el catálogo de `GET /v1/motivos`, y "Describa el motivo *" solo si se elige "Otro". Botón "Consultar". El botón de cámara (HU-04) aparece deshabilitado | PLA-01, CONTRATO-HU-02 decisión 4 |
| PLA-02 | Consultar sin motivo | "Indique el motivo de la consulta." en el campo de motivo, con el foco ahí. **No se envía nada** | Gherkin esc. 2, PLA-02 |
| PLA-02 | "Otro" con < 10 caracteres | "Describa el motivo (mínimo 10 caracteres)." No se envía nada | PLA-02 |
| PLA-03 | Formato inválido | "El formato de placa no es válido. Formato esperado: <formato_placa.descripcion>" (con los valores por defecto: "… Formato esperado: ABC-123 (3 letras o números, guion, 3 números)"). La app valida con `formato_placa.regex` de `GET /v1/motivos` y no envía nada (**v3**). Si faltan el motivo y el formato, se muestran los dos mensajes | Gherkin esc. 4, PLA-03 |
| PLA-04 | Mientras espera | "Consultando…" con la placa; el botón queda desactivado (no se envía dos veces) | PLA-04 |
| PLA-05 | `con_requisitoria` | Bloque rojo con la placa y "TIENE REQUISITORIA". "Motivo: …", "Consultado: dd/mm/aaaa hh:mm" (hora local) y "Nueva consulta". Sin bloque de datos adicionales (variante "Solo estado"). Sin botones de acción operativa | Gherkin esc. 1, PLA-05 · DECISIÓN PROPUESTA 4 |
| PLA-06 | `sin_requisitoria` | Bloque gris neutro con la placa y "Sin requisitoria registrada en la fuente consultada". **Sin verde ni ✓** | Gherkin esc. 5, PLA-06 |
| PLA-08 | `placa_no_registrada` | Bloque gris neutro con la placa y "Placa no registrada en la fuente consultada. Verifique la placa." Sin verde ni ✓, con un texto distinto de PLA-06 | DECISIÓN PROPUESTA 3 |
| PLA-07 | `503`, `502`, error de red o cualquier respuesta inesperada | "No se pudo completar la consulta; intente nuevamente", con un ícono y un color distintos de los resultados. "Reintentar" conserva la placa y el motivo; "Volver". **Nunca** muestra "sin requisitoria" | Gherkin esc. 3, PLA-07, regla 7 |
| `403` | `POST /v1/consultas/placa` responde `403 SIN_PERMISO` (en Jest, con la respuesta simulada) | ERR-01 de CONTRATO-HU-02: "No tiene permiso para usar esta función.", "El intento quedó registrado." y "Volver al inicio", que vuelve al inicio del rol | CONTRATO-HU-02 v3 · **v2** |
| Nada en el dispositivo | — | El resultado vive solo en memoria; no queda en SecureStore ni en disco | ADR-0013 |

### 7. Configuración

| Caso | Salida esperada | Origen |
|---|---|---|
| Formato de placa | `PLACA_FORMATO_REGEX` (por defecto `^[A-Z0-9]{3}-[0-9]{3}$`) y `PLACA_FORMATO_DESCRIPCION` (por defecto `ABC-123 (3 letras o números, guion, 3 números)`) en `infra/.env.example`, marcados como provisionales (PA #20, NO VERIFICADO contra la normativa). Cambiarlos no requiere tocar código | ADR-0011 |
| La app no fija el formato | El mensaje de PLA-03 usa la descripción que envía la API (`formato_placa.descripcion` de `GET /v1/motivos` en la validación local; `mensaje` del `422` si la API lo rechaza), y la validación local usa `formato_placa.regex` (**v3**) | ADR-0011, ADR-0007 · DECISIÓN PROPUESTA 9 |

## Nombres que no se negocian

| Tipo | Valor exacto |
|---|---|
| Rutas | `GET /v1/motivos` · `POST /v1/consultas/placa` |
| Campos de entrada | `placa`, `motivo_codigo`, `motivo_texto` |
| Campos de respuesta | `consulta_id`, `placa`, `resultado`, `motivo.codigo`, `motivo.texto`, `consultado_en`, `motivos[].codigo`, `motivos[].descripcion`, `formato_placa.regex`, `formato_placa.descripcion` (v3) |
| Resultados | `con_requisitoria` · `sin_requisitoria` · `placa_no_registrada` |
| Motivos iniciales | `control_vehicular` · `intervencion_policial` · `denuncia` · `operativo` · `otro` |
| Códigos | `422 MOTIVO_REQUERIDO` · `422 PLACA_FORMATO_INVALIDO` · `422 SOLICITUD_INVALIDA` · `503 FUENTE_NO_DISPONIBLE` · `502 FUENTE_RESPUESTA_INVALIDA` · `503 SERVICIO_NO_DISPONIBLE` · `403 SIN_PERMISO` |
| Eventos | `CONSULTA_PLACA` · `ERROR_FUENTE` · `ACCESO_DENEGADO` |
| Textos de la app | "Consultar placa" · "Placa" · "Motivo de consulta *" · "Describa el motivo *" · "Consultar" · "Indique el motivo de la consulta." · "Describa el motivo (mínimo 10 caracteres)." · "El formato de placa no es válido. Formato esperado: …" · "Consultando…" · "TIENE REQUISITORIA" · "Sin requisitoria registrada en la fuente consultada" · "Placa no registrada en la fuente consultada. Verifique la placa." · "No se pudo completar la consulta; intente nuevamente" · "Reintentar" · "Volver" · "Nueva consulta" · "Motivo:" · "Consultado:" |
| Variables | `PLACA_FORMATO_REGEX` · `PLACA_FORMATO_DESCRIPCION` · `FUENTE_PLACAS_URL` · `FUENTE_TIMEOUT_S` |
| Placas de prueba | `ZZA-101` (con) · `ZZB-201` (sin) · `ZZZ-999` (no registrada), de CONTRATO-HU-08 |

## Rutas de cada rol

| Rol | Rutas | Origen |
|---|---|---|
| TESTER | `services/api/tests/`, `apps/movil/__tests__/`, `apps/movil/.maestro/` (si hay dev build), `pruebas/datos/` | AGENTS.md |
| DEV | `services/api/` (salvo `tests/`), `apps/movil/` (salvo `__tests__/` y `.maestro/`), `infra/`, `contratos/api/openapi.json` | AGENTS.md |

## Avisos de contexto

- **Placas de ejemplo:** la HU y los wireframes usan `ABC-123`, `DEF-456` y `GHI-789`. La HU dice que son solo ejemplos ("Supuestos"), y CONTRATO-HU-08 fijó las placas sintéticas con prefijo `ZZ`. Las pruebas y el demo usan `ZZA-101`, `ZZB-201` y `ZZZ-999`. `ABC-123` solo aparece como ejemplo de formato en PLA-03. El guion de validación del UX (`docs/ux/prototipo/GUION-VALIDACION.md`) y la app real deben coincidir; se avisa al UX.
- **Desempeño:** el p95 ≤ 2 s con 20 usuarios (ADR-0011) no entra en este veredicto (DECISIÓN PROPUESTA 10).

## Decisiones propuestas (no venían en la tarea)

| # | Decisión | Por qué hace falta | Estado |
|---|---|---|---|
| 1 | HU-03 y HU-07 se construyen juntas, en una rama y un ciclo, con un solo veredicto | HU-07 necesita eventos reales de consulta y la consulta de placa necesita la bitácora blindada (fail-closed) | Aprobada por el humano (2026-11-19) |
| 2 | Catálogo de motivos expuesto en `GET /v1/motivos` | El catálogo es configurable (ADR-0011), así que la app no puede tenerlo fijo | Aprobada por el humano (2026-11-19) |
| 3 | Placa no registrada: `resultado = placa_no_registrada` (un `200`, no un error) y pantalla nueva PLA-08 con "Placa no registrada en la fuente consultada. Verifique la placa." **El UX tiene que dibujar PLA-08** | Pendiente de HU-08 decisión 3. Un `404` de la fuente no puede leerse como "sin requisitoria" (regla 7), y tampoco es una falla de la fuente | Aprobada por el humano (2026-11-19) |
| 4 | PA #15: variante "Solo estado". La API no devuelve datos del vehículo ni de la requisitoria al agente | Es la menor exposición de datos hasta que el MININTER decida. Agregar campos después es una v2 | Aprobada por el humano (2026-11-19) |
| 5 | Códigos y descripciones del catálogo inicial | ADR-0011 da los nombres; los códigos los fija este contrato | Aprobada por el humano (2026-11-19) |
| 6 | La API normaliza la placa (recorta los espacios y la pasa a mayúsculas) | Si no, `zza-101` sería formato inválido o placa no registrada, y en campo se escribe en minúsculas | Aprobada por el humano (2026-11-19) |
| 7 | Si faltan el motivo y el formato, la API responde primero `MOTIVO_REQUERIDO`. Los rechazos `422` no dejan evento en la bitácora | La API devuelve un solo código. El motivo es la regla 2 | Aprobada por el humano (2026-11-19) |
| 8 | Una respuesta fuera de contrato se responde con `502` y sin reintento; una caída o un timeout, con `503` y un reintento | ADR-0014 limita el reintento a fallas momentáneas; una respuesta mal formada se repetiría igual | Aprobada por el humano (2026-11-19) |
| 9 | La regex vigente llega a la app por la API en `GET /v1/motivos`, campo `formato_placa` `{regex, descripcion}` (**v3**; antes la forma la decidía el DEV) | ADR-0011 pide cambiar el formato sin tocar código, y la app también valida | Aprobada por el humano (2026-11-19) |
| 10 | El p95 ≤ 2 s se mide en la prueba de desempeño de la iteración (k6, `pruebas/carga/`), aparte, no en este veredicto | La carga necesita el VPS de referencia (ADR-0011) y no bloquea la funcionalidad | Aprobada por el humano (2026-11-19) |

## Fuera del contrato (decide el DEV)

- La estructura del adaptador `FuentePlacas`, cómo valida contra el yaml y cómo hace el reintento.
- Cómo se guardan la consulta y el evento en una misma transacción.

## Preguntas abiertas para el humano

Respondidas por el humano (vía PM) el 2026-11-19:

1. **Decisiones 1 a 10:** aprobadas tal cual.
2. **PLA-08:** el PM se la encarga al UX antes del 28-nov, y entra en el prototipo y en el guion del 1-dic. Si la validación cambia el texto, se versiona este contrato.
3. **Rama:** `hu-03` (HU-03 + HU-07) sale de `main` después del merge de `hu-01`. Si `hu-01` no está mergeada el 28-nov, parte de `hu-01` y se rebasa sobre `main` tras el merge.

## Changelog

| Versión | Fecha | Cambio | Motivo | Aprobado por |
|---|---|---|---|---|
| v1 | 2026-11-19 | Versión inicial | Encargo PM → LEAD, Iteración 1 | Humano (vía PM), 2026-11-19 |
| v2 | 2026-11-19 | La prueba de la pantalla ERR-01 llega desde HU-02 (§6, fila `403`) | En HU-01/02 ninguna solicitud de la app podía recibir un `403` | Humano, 2026-11-19 |
| v3 | 2026-11-19 | §1, §6 PLA-03, §7 y decisión 9: `GET /v1/motivos` agrega `formato_placa` `{regex, descripcion}` desde `PLACA_FORMATO_REGEX` y `PLACA_FORMATO_DESCRIPCION`; PLA-03 valida en la app con esa descripción sin enviar nada | Pregunta del TESTER: sin la forma fijada, la prueba de la app tendría que leer el código del DEV | Humano (vía PM), 2026-11-19 |
