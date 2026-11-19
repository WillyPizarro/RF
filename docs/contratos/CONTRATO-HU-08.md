# CONTRATO — HU-08 Simuladores de fuentes (base de placa y rostro)

**Tipo:** Feature
**Versión:** v1
**Estado:** Aprobado (2026-11-19, humano vía PM)
**Origen:** `docs/hus/HU-08-simuladores-fuentes.md` · encargo PM → LEAD (2026-11-19), Iteración 1, contrato 1 de 5
**Rama de trabajo:** `hu-08`, creada desde `main` (2ef0829)
**Pasa por UX:** No. Esta HU no cambia nada visible en la app (regla de coordinación 8 del LEAD).

---

## Paquete de contexto

| Fuente | Por qué entra |
|---|---|
| HU-08 | Historia y escenarios 1 a 3 |
| TECH-DESIGN.md › Modelo de datos (`sim_vehiculo`, `sim_persona`, `sim_galeria`) | Campos provisionales de cada fuente |
| TECH-DESIGN.md › Criterios › Servicios y simuladores (HU-08) | Criterios técnicos de esta HU |
| ADR-0006 | Contenedor `simuladores`, un contrato OpenAPI por fuente, adaptadores reemplazables, modos de falla, datos sintéticos, red interna |
| ADR-0014 | Timeout de 3 s por fuente y códigos de error estables (`FUENTE_NO_DISPONIBLE`, `FUENTE_RESPUESTA_INVALIDA`) |
| ADR-0011 | Formato de placa provisional (3 alfanuméricos, guion, 3 dígitos) para los datos sintéticos |
| ADR-0004 / ADR-0008 | La galería es una lista cerrada de ~20 personas; las fotos se guardan cifradas en el simulador y nunca en el repositorio |
| ADR-0009 | `simuladores` sin puerto publicado, en la red interna |
| SPRINT0.md › §5 y M-1 E | `GET /salud` del simulador y puerto interno 8001, ya construidos |
| `services/api/app/config.py:28` | La API ya usa `SIMULADORES_URL` (por defecto `http://simuladores:8001`) |
| PRD PA #6, PA #17 | Abiertos. Se trabaja con el supuesto vigente (PRD, 2026-11-19) y los campos provisionales del ADR-0006 |

No entran: ADR-0003, ADR-0005 (la bitácora se construye en HU-07) ni ADR-0007 más allá del formato de error.

## Interfaz observable

1. **El API HTTP del contenedor `simuladores`** (`http://simuladores:8001`), que solo es alcanzable desde la red interna de Docker.
2. **Los contratos OpenAPI 3.1** de `contratos/fuentes/`: `placas.yaml`, `requisitorias-personas.yaml` y `galeria.yaml`.
3. **La configuración del entorno** (`infra/.env.example` y `infra/docker-compose.yml`): las URL de las fuentes que usa la API y los modos de falla del simulador.

> **Alcance de los escenarios (DECISIÓN PROPUESTA 1).** El Escenario 1 ("la app hace una consulta de placa") y el Escenario 3 ("el servicio responde un error controlado y queda en la bitácora") necesitan `POST /v1/consultas/placa` (HU-03) y la bitácora (HU-07), que todavía no existen. Este contrato cubre la **mitad del simulador** de cada escenario. La mitad de la API se verifica en los contratos de HU-03 y HU-07, y queda anotada en `docs/contratos/PENDIENTES.md`. No se agrega ninguna ruta de la API solo para pruebas (SPRINT0 M-2).

## Comportamiento

Formato de error de los simuladores: `{"codigo": "<CODIGO>", "mensaje": "<texto>"}`. Es el mismo del ADR-0007, pero sin `id_traza`, porque la traza es de la API (DECISIÓN PROPUESTA 2).

Todas las respuestas `200` de datos llevan `"es_sintetico": true` en cada registro (ADR-0006 §5).

### 1. Fuente `placas`

**Entrada**

```text
GET /placas/{placa}
```

`{placa}` va en mayúsculas, con guion (`ZZA-101`). El simulador no valida el formato: eso lo hace la API (ADR-0007). Si la placa no está en la base, responde `404`.

**Casos**

| Caso | Entrada | Salida esperada | Origen |
|---|---|---|---|
| Placa con requisitoria | `GET /placas/ZZA-101` | `200` `{"placa":"ZZA-101","marca":"…","modelo":"…","color":"…","tipo":"…","requisitoria_vigente":true,"requisitoria":{"codigo":"…","motivo":"…","autoridad":"…","fecha_emision":"AAAA-MM-DD"},"es_sintetico":true}` | Gherkin esc. 1, TDD `sim_vehiculo` |
| Placa sin requisitoria | `GET /placas/ZZB-201` | `200`, con la misma forma, `"requisitoria_vigente":false` y `"requisitoria":null` | TDD `sim_vehiculo` |
| Placa no registrada | `GET /placas/ZZZ-999` | `404` `{"codigo":"PLACA_NO_REGISTRADA","mensaje":"La placa no está registrada en la fuente"}` | DECISIÓN PROPUESTA 3 |
| Minúsculas | `GET /placas/zza-101` | `404` `PLACA_NO_REGISTRADA` (no normaliza; la API envía la placa normalizada) | DECISIÓN PROPUESTA 3 |

### 2. Fuente `requisitorias-personas`

**Entrada**

```text
GET /personas/{persona_id}
GET /personas/{persona_id}/fotos/{foto_id}
```

| Caso | Entrada | Salida esperada | Origen |
|---|---|---|---|
| Persona con requisitoria | `GET /personas/SIM-P-0001` | `200` `{"persona_id":"SIM-P-0001","nombres":"…","apellidos":"…","documento":"SIM-00000001","requisitoria":{"codigo":"…","motivo":"…","autoridad":"…","fecha_emision":"AAAA-MM-DD"},"foto_ids":["…"],"es_sintetico":true}` | ADR-0006, TDD `sim_persona` |
| Persona no registrada | `GET /personas/SIM-P-9999` | `404` `{"codigo":"PERSONA_NO_REGISTRADA","mensaje":"La persona no está registrada en la fuente"}` | DECISIÓN PROPUESTA 3 |
| Foto cargada | `GET /personas/{id}/fotos/{foto_id}` | `200`, `Content-Type: image/jpeg` o `image/png`, con los bytes descifrados | ADR-0006, ADR-0008 |
| Foto no cargada | `GET /personas/SIM-P-0001/fotos/inexistente` | `404` `{"codigo":"FOTO_NO_DISPONIBLE","mensaje":"La foto no está disponible"}` | DECISIÓN PROPUESTA 3 |

Toda persona de esta fuente tiene requisitoria (ADR-0004: la galería es de personas con requisitoria simulada). `foto_ids` puede estar vacío si sus fotos todavía no se cargaron.

### 3. Fuente `galeria`

**Entrada**

```text
GET /galeria
```

| Caso | Entrada | Salida esperada | Origen |
|---|---|---|---|
| Galería | `GET /galeria` | `200` `{"version":"<texto>","personas":[{"persona_id":"SIM-P-0001","foto_ids":["…"]}],"es_sintetico":true}` | ADR-0006, ADR-0004 |
| Solo personas con foto | — | `personas` solo incluye personas con al menos una foto cargada. Sin fotos cargadas, `personas` es `[]` | ADR-0008 §2 ("sin consentimiento no entra") |
| Versión estable | Dos `GET /galeria` sin cambiar las fotos | La misma `version`. Si cambia el conjunto de fotos, `version` cambia | ADR-0006 Consecuencias (caché de embeddings) |

### 4. Datos sintéticos

| Caso | Salida esperada | Origen |
|---|---|---|
| Volumen de placas | ≥ 200 vehículos, con ≥ 20 de ellos con requisitoria vigente | ADR-0006 Alternativas ("cientos de placas") · DECISIÓN PROPUESTA 4 |
| Placas reservadas | Todas las placas sintéticas empiezan con `ZZ` y cumplen `^[A-Z0-9]{3}-[0-9]{3}$` | ADR-0011 · DECISIÓN PROPUESTA 5 |
| Placas fijas para pruebas | `ZZA-101` siempre tiene requisitoria vigente; `ZZB-201` nunca la tiene; `ZZZ-999` nunca existe | DECISIÓN PROPUESTA 4 |
| Personas | Entre 20 y 30 personas `SIM-P-0001` en adelante, todas con requisitoria; `SIM-P-0001` siempre existe | ADR-0004 (~20) |
| Documento sintético | `SIM-` + 8 dígitos (no puede confundirse con un DNI real) | DECISIÓN PROPUESTA 5 |
| Datos versionados | La semilla vive en `services/simuladores/` como archivo versionado y es determinista (los mismos datos en cada arranque) | ADR-0006 §5 |
| Sin fotos en el repositorio | Ningún archivo de imagen en el repositorio. Las fotos se cargan desde un directorio externo (DECISIÓN PROPUESTA 6) | AGENTS.md regla 8, ADR-0008 |

### 5. Modos de falla

Se configuran **por fuente, en tiempo de ejecución y sin reiniciar ni tocar código**, mediante una ruta de control del simulador, que solo es alcanzable desde la red interna (DECISIÓN PROPUESTA 7):

```text
PUT /control/modos/{fuente}      body: {"modo": "<modo>", "latencia_ms": <int, opcional>}
GET /control/modos               → {"placas": {...}, "requisitorias-personas": {...}, "galeria": {...}}
```

`{fuente}` ∈ `placas` · `requisitorias-personas` · `galeria`. Al arrancar, todas las fuentes están en `normal`.

| Modo | Efecto en cada ruta de esa fuente | Origen |
|---|---|---|
| `normal` | Responde según las secciones 1 a 3, sin latencia artificial | ADR-0006 §4, ADR-0011 (p95 con simulador sin latencia) |
| `latencia` | Responde lo normal tras `latencia_ms` (por defecto 5000, por encima del timeout de 3 s del ADR-0014) | ADR-0006 §4 |
| `error_500` | `500` `{"codigo":"ERROR_SIMULADO","mensaje":"Falla simulada de la fuente"}` | ADR-0006 §4 |
| `malformada` | `200` con un cuerpo que **no** valida contra el contrato de su fuente: falta un campo obligatorio, o `requisitoria_vigente` no es booleano | ADR-0006 §4, Gherkin esc. 3 |
| Fuente inválida | `PUT /control/modos/otra` → `404` `{"codigo":"FUENTE_DESCONOCIDA",…}` | DECISIÓN PROPUESTA 7 |
| Modo inválido | `{"modo":"x"}` → `422` `{"codigo":"SOLICITUD_INVALIDA",…}` | SPRINT0 M-1 B |
| Aislamiento | El modo de una fuente no altera las otras; `GET /salud` responde `200` en cualquier modo | DECISIÓN PROPUESTA 7 |

### 6. Contratos documentados

| Caso | Salida esperada | Origen |
|---|---|---|
| Existen | `contratos/fuentes/placas.yaml`, `requisitorias-personas.yaml` y `galeria.yaml`, OpenAPI 3.1 válidos | ADR-0006 §1 |
| Contenido | Cada uno documenta campos, códigos de error, un ejemplo por respuesta y el tiempo de respuesta simulado (`x-tiempo-respuesta-ms` o una descripción equivalente) | ADR-0006 §1, HU-08 Supuestos |
| Coinciden con lo desplegado | Toda respuesta del simulador en modo `normal` (200 y 404) valida contra el yaml de su fuente | TDD › HU-08 criterio 4 |
| Sin palabra prohibida | Ninguno contiene "identificado" | AGENTS.md regla 1 |
| Ruta de control | `/control/*` **no** figura en los yaml de las fuentes (no es parte de lo que una fuente real debe cumplir) | DECISIÓN PROPUESTA 7 |

### 7. Reemplazo del simulador (Gherkin esc. 2, mitad del simulador)

| Caso | Salida esperada | Origen |
|---|---|---|
| Segunda implementación | Un mock generado **solo** desde el yaml (por ejemplo, `prism mock contratos/fuentes/placas.yaml`) responde a `GET /placas/{placa}` con un cuerpo que valida contra el mismo contrato que el simulador | Gherkin esc. 2, TDD › HU-08 criterio 2 |
| URL por fuente | La API lee `FUENTE_PLACAS_URL`, `FUENTE_REQUISITORIAS_URL` y `FUENTE_GALERIA_URL`. Si una no está definida, usa `SIMULADORES_URL`. Las tres figuran en `infra/.env.example` con un comentario | ADR-0006 §2 · DECISIÓN PROPUESTA 8 |
| Timeout configurable | `FUENTE_TIMEOUT_S` (valor por defecto 3) en `infra/.env.example` | ADR-0014 |

La prueba de punta a punta del escenario 2 (la API apuntando al mock, con las pruebas funcionales en verde) se hace en HU-03.

### 8. Aislamiento (Gherkin esc. 1, "la app no se conecta directo al simulador")

| Caso | Salida esperada | Origen |
|---|---|---|
| Sin puerto publicado | `docker compose -f infra/docker-compose.yml config` no publica ningún puerto de `simuladores` | ADR-0006 §6, ADR-0009, SPRINT0 criterio 5 |
| Ni el proxy ni la app | El `Caddyfile` no enruta nada hacia `simuladores`, y `apps/movil/src/` no contiene `simuladores`, `8001` ni `/placas/` | TDD › HU-08 criterio 1 |
| Desde la API sí | Desde el contenedor `api`, `GET http://simuladores:8001/placas/ZZA-101` → `200` | ADR-0006 §6 |
| Salud intacta | `GET /v1/salud` sigue cumpliendo SPRINT0 §5 sin cambios | SPRINT0 |

## Nombres que no se negocian

| Tipo | Valor exacto |
|---|---|
| Rutas | `GET /placas/{placa}` · `GET /personas/{persona_id}` · `GET /personas/{persona_id}/fotos/{foto_id}` · `GET /galeria` · `PUT /control/modos/{fuente}` · `GET /control/modos` · `GET /salud` (ya existe) |
| Fuentes | `placas` · `requisitorias-personas` · `galeria` |
| Archivos | `contratos/fuentes/placas.yaml` · `contratos/fuentes/requisitorias-personas.yaml` · `contratos/fuentes/galeria.yaml` |
| Campos de placa | `placa`, `marca`, `modelo`, `color`, `tipo`, `requisitoria_vigente`, `requisitoria`, `es_sintetico` |
| Campos de requisitoria | `codigo`, `motivo`, `autoridad`, `fecha_emision` |
| Campos de persona | `persona_id`, `nombres`, `apellidos`, `documento`, `requisitoria`, `foto_ids`, `es_sintetico` |
| Campos de galería | `version`, `personas[].persona_id`, `personas[].foto_ids`, `es_sintetico` |
| Modos | `normal` · `latencia` · `error_500` · `malformada` · campo `latencia_ms` |
| Códigos de error del simulador | `PLACA_NO_REGISTRADA` · `PERSONA_NO_REGISTRADA` · `FOTO_NO_DISPONIBLE` · `ERROR_SIMULADO` · `FUENTE_DESCONOCIDA` · `SOLICITUD_INVALIDA` |
| Códigos de error de la API (los usan HU-03 y HU-05) | `FUENTE_NO_DISPONIBLE` · `FUENTE_RESPUESTA_INVALIDA` (ADR-0006, ADR-0014) |
| Variables de entorno | `FUENTE_PLACAS_URL` · `FUENTE_REQUISITORIAS_URL` · `FUENTE_GALERIA_URL` · `FUENTE_TIMEOUT_S` · `SIM_FOTOS_DIR` · `SIMULADORES_URL` (ya existe) |
| Datos fijos | `ZZA-101` (con requisitoria) · `ZZB-201` (sin) · `ZZZ-999` (no existe) · `SIM-P-0001` (existe) |

## Rutas de cada rol

| Rol | Rutas | Origen |
|---|---|---|
| TESTER | `services/simuladores/tests/`, `pruebas/datos/` (solo fixtures sintéticos; ninguna imagen versionada) | AGENTS.md |
| DEV | `services/simuladores/` (salvo `tests/`), `contratos/fuentes/`, `infra/` (compose, `.env.example`), `services/api/` (salvo `tests/`) para la configuración de las URL por fuente, `scripts/` si hace falta un cargador de fotos | AGENTS.md |

## Avisos de contexto

- Deuda (`DEUDA.md`): no existe (proyecto nuevo).
- Patrones: imitar `services/simuladores/app/main.py` y el formato de error del Sprint 0.
- El simulador hoy tiene `openapi_url=None`. Puede seguir así: la coincidencia con el contrato se prueba validando respuestas contra los yaml, no exponiendo el OpenAPI.

## Decisiones propuestas (no venían en la tarea)

| # | Decisión | Por qué hace falta | Estado |
|---|---|---|---|
| 1 | HU-08 cubre la mitad del simulador de los escenarios 1 a 3. La mitad de la API (error controlado, bitácora `ERROR_FUENTE`, app sin cambios con el mock) se verifica en HU-03 y HU-07 | Sin `/v1/consultas/placa` ni bitácora, esos pasos no son observables; no se agregan rutas solo para pruebas | Aprobada por el humano (2026-11-19) |
| 2 | Formato de error del simulador `{codigo, mensaje}`, sin `id_traza` | El ADR-0007 fija el formato de la API, no el de las fuentes | Aprobada por el humano (2026-11-19) |
| 3 | "No registrado" es un `404` con su código, **distinto** de "registrado sin requisitoria" (`200` con `requisitoria_vigente:false`). Cómo lo presenta la API al agente se decide en HU-03 | Regla 7: una placa que la fuente no conoce no puede leerse como "sin requisitoria" sin decidirlo | Aprobada por el humano (2026-11-19) |
| 4 | Volumen mínimo de datos (≥ 200 placas, ≥ 20 con requisitoria, 20 a 30 personas) y datos fijos para pruebas | TESTER y DEV no se ven: necesitan valores conocidos | Aprobada por el humano (2026-11-19) |
| 5 | Placas sintéticas con prefijo reservado `ZZ` y documentos `SIM-########` | Una placa o DNI sintético que coincida con uno real mostraría "con requisitoria" sobre un vehículo o una persona real en un demo (regla 8) | Aprobada por el humano (2026-11-19) |
| 6 | Las fotos se cargan desde el directorio `SIM_FOTOS_DIR`, fuera del repositorio, con el nombre `<persona_id>__<n>.<jpg|png>`, y el simulador las guarda cifradas en su volumen. **En HU-08 se construyen la carga y el cifrado; las fotos reales con consentimiento se cargan en HU-05.** El TESTER prueba con una imagen generada en tiempo de ejecución (no es un rostro), que nunca se versiona | ADR-0008 exige fotos cifradas y fuera del repositorio, pero no dice cómo entran | Aprobada por el humano (2026-11-19) |
| 7 | Modos de falla por una ruta `/control/modos/*` del simulador, en tiempo de ejecución, fuera de los yaml de las fuentes. Alternativa: variables de entorno y reiniciar el contenedor | ADR-0006 §4 pide modos configurables "sin tocar código". Con variables, cada prueba de falla de HU-03 obligaría a reiniciar el contenedor | Aprobada por el humano (2026-11-19) |
| 8 | Una variable de URL por fuente, con `SIMULADORES_URL` como respaldo | El escenario 2 pide reemplazar una fuente sin tocar las demás | Aprobada por el humano (2026-11-19) |

## Fuera del contrato (decide el DEV)

- La estructura interna del simulador, el formato de la semilla (JSON, CSV o SQL), si usa base de datos o archivos, y cómo genera la `version` de la galería.
- El algoritmo y la llave del cifrado de las fotos, siempre que la llave venga del entorno y no se versione (ADR-0008, ADR-0009).
- Los adaptadores `FuentePlacas`, `FuenteRequisitorias` y `FuenteGaleria` de la API, y cómo validan contra el contrato (ADR-0006 §2-3). Su comportamiento observable se prueba en HU-03 y HU-05.
- Cómo genera el cuerpo `malformado`, siempre que no valide contra el yaml.

## Preguntas abiertas para el humano

Todas respondidas por el humano (vía PM) el 2026-11-19:

1. **Decisiones 1 a 8:** aprobadas tal cual.
2. **PA #6 y campos de las fuentes reales:** se construye con los campos provisionales del ADR-0006 y del TDD. Si el MININTER entrega los campos reales, se saca una v2 sin reabrir el alcance.
3. **Fotos (decisión 6):** la carga cifrada de fotos de la galería entra en HU-08.
4. **Rama:** `sprint-0` se mergeó a `main` (fast-forward, 2ef0829). La Iteración 1 parte de `main`; esta HU va en `hu-08`.

## Changelog

| Versión | Fecha | Cambio | Motivo | Aprobado por |
|---|---|---|---|---|
| v1 | 2026-11-19 | Versión inicial; decisiones 1 a 8 aprobadas, preguntas respondidas | Encargo PM → LEAD, Iteración 1 | Humano (vía PM), 2026-11-19 |
