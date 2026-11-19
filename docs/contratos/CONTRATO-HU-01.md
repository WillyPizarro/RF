# CONTRATO — HU-01 Iniciar sesión y mantener una sesión segura

**Tipo:** Feature
**Versión:** v2
**Estado:** Aprobado (v1 y v2: 2026-11-19, humano)
**Origen:** `docs/hus/HU-01-iniciar-sesion.md` · encargo PM → LEAD (2026-11-19), Iteración 1, contrato 2 de 5
**Rama de trabajo:** `hu-01`, desde `main` después de que el humano mergee `hu-08`
**Pasa por UX:** Sí. Pantallas AUTH-01 a AUTH-04 (`docs/ux/wireframes/HU-01-iniciar-sesion.md`).

---

## Paquete de contexto

| Fuente | Por qué entra |
|---|---|
| HU-01 | Historia y escenarios 1 a 4 |
| TECH-DESIGN.md › Criterios › Sesión y acceso | Criterios técnicos (login, mensaje único, bloqueo, inactividad, 401, clave fuera de logs) |
| TECH-DESIGN.md › Modelo de datos | `usuario_perfil`, `control_acceso`, `bitacora` y los tipos de evento |
| ADR-0003 | El login pasa por la API, valida contra Supabase Auth, tres roles y usuarios cargados por script |
| ADR-0011 | Valores provisionales: 10 min de inactividad, token de 15 min, 5 intentos y bloqueo de 15 min (PA #18, #19). Todos configurables |
| ADR-0005 | Bitácora: contenido mínimo y fail-closed |
| ADR-0007 | Rutas `/v1/auth/*`, formato de error `{codigo, mensaje, id_traza}` |
| ADR-0013 | Token en `expo-secure-store`; caché solo en memoria |
| Wireframes AUTH-01 a AUTH-04 | Textos visibles y comportamiento de la pantalla |
| `docs/contratos/PENDIENTES.md` | La prueba del 422 `SOLICITUD_INVALIDA` (SPRINT0 M-2) |

**Puntos abiertos de la HU:** PA #18 y PA #19 se cubren con los valores provisionales del ADR-0011, como ordena el encargo; quedan marcados como provisionales y configurables. PA #3 (identidades institucionales) no cambia el login del MVP.

## Interfaz observable

1. **API:** `POST /v1/auth/login`, `POST /v1/auth/refresh`, `POST /v1/auth/logout`, y cualquier ruta autenticada (para el 401).
2. **App:** pantallas AUTH-01 a AUTH-04 y el almacenamiento del dispositivo (SecureStore, caché y store).
3. **Base de datos:** filas de la tabla `bitacora`, leídas directamente por las pruebas (DECISIÓN PROPUESTA 2).
4. **Configuración:** variables de entorno de la API y el comando de carga de usuarios.

## Comportamiento

### 1. Iniciar sesión

```text
POST /v1/auth/login
{"usuario": "<texto>", "clave": "<texto>"}
```

| Caso | Entrada | Salida esperada | Origen |
|---|---|---|---|
| Camino feliz | Usuario activo, clave correcta | `200` `{"token_acceso":"…","token_renovacion":"…","expira_en":900,"inactividad_s":600,"usuario":{"id":"…","usuario":"agente1","nombre":"…","rol":"agente"}}` · bitácora `LOGIN_OK` con `usuario_id`, `rol` y `ocurrido_en` | Gherkin esc. 1, ADR-0003, TDD |
| Clave incorrecta | Usuario existente, clave mala | `401` `{"codigo":"CREDENCIALES_INVALIDAS","mensaje":"Usuario o clave incorrectos","id_traza":"…"}` · bitácora `LOGIN_FALLIDO` | Gherkin esc. 2, TDD |
| Usuario inexistente | `usuario` que no existe | **Idéntico** al caso anterior (mismo status, código y mensaje) · bitácora `LOGIN_FALLIDO` con `usuario_id` nulo y el texto de `usuario` en `parametros` | Gherkin esc. 2 ("sin indicar cuál falló") |
| Usuario inactivo | `usuario_perfil.activo = false`, clave correcta | Idéntico a "clave incorrecta" · bitácora `LOGIN_FALLIDO` | DECISIÓN PROPUESTA 3 |
| Éxito reinicia el contador | 4 fallos y luego un acierto | El acierto da `200` y el contador vuelve a 0 (hacen falta otros 5 fallos seguidos para bloquear) | ADR-0011 ("consecutivos") |
| Cuerpo inválido | Falta `usuario` o `clave`, alguno vacío, o el JSON está mal formado | `422` `{"codigo":"SOLICITUD_INVALIDA",…}` · no cuenta como intento y no deja evento | SPRINT0 M-2, PENDIENTES · DECISIÓN PROPUESTA 4 |

### 2. Bloqueo por intentos (provisional, PA #19)

| Caso | Entrada | Salida esperada | Origen |
|---|---|---|---|
| 5.º fallo seguido | Quinto fallo consecutivo del mismo `usuario` | `423` `{"codigo":"CUENTA_BLOQUEADA","mensaje":"Cuenta bloqueada temporalmente","id_traza":"…","bloqueado_hasta":"<ISO 8601 UTC>"}` · bitácora `LOGIN_FALLIDO` y `CUENTA_BLOQUEADA` | Gherkin esc. 4, TDD, AUTH-02 ("al quinto fallo se pasa a AUTH-04") · DECISIÓN PROPUESTA 5 |
| Clave correcta durante el bloqueo | Clave correcta antes de `bloqueado_hasta` | La misma respuesta `423`, con el mismo `bloqueado_hasta` (el bloqueo no se alarga) · bitácora `LOGIN_FALLIDO` con `codigo_error = CUENTA_BLOQUEADA` | Gherkin esc. 4 ("no indica si la clave era correcta") |
| Clave incorrecta durante el bloqueo | — | Idéntico al caso anterior | Gherkin esc. 4 |
| Fin del bloqueo | Clave correcta después de `bloqueado_hasta` | `200` y el contador en 0 | ADR-0011 |
| Usuario inexistente | 5 fallos seguidos con un `usuario` que no existe | Se comporta igual (`423` con `bloqueado_hasta`), para no revelar qué usuarios existen | Observación de UX en AUTH-04 · DECISIÓN PROPUESTA 5 |

### 3. Renovación, cierre e inactividad (provisional, PA #18)

```text
POST /v1/auth/refresh   {"token_renovacion": "<texto>"}
POST /v1/auth/logout    (con Authorization: Bearer <token_acceso>)
```

| Caso | Entrada | Salida esperada | Origen |
|---|---|---|---|
| Renovar | `token_renovacion` válido dentro del tiempo de inactividad | `200` con la misma forma que el login | ADR-0011 ("renovable mientras haya actividad") |
| Token de acceso vencido o firma inválida | Cualquier ruta autenticada | `401` `{"codigo":"NO_AUTENTICADO","mensaje":"Inicie sesión nuevamente",…}` | TDD |
| Sin token | Cualquier ruta autenticada | `401` `NO_AUTENTICADO` | ADR-0003 §4 |
| Inactividad en el servidor | Una solicitud autenticada o una renovación más de `SESION_INACTIVIDAD_S` después de la última solicitud autenticada de esa sesión | `401` `{"codigo":"SESION_VENCIDA","mensaje":"Su sesión se cerró por inactividad",…}` · bitácora `SESION_VENCIDA` · la sesión queda invalidada (renovar después también da `401`) | Gherkin esc. 3, TDD (evento `SESION_VENCIDA`) · DECISIÓN PROPUESTA 6 |
| Cerrar sesión | `POST /v1/auth/logout` con un token válido | `204` · bitácora `LOGOUT` · el `token_renovacion` de esa sesión deja de servir (`401`) | ADR-0003 §3, "Salir" aprobado en UX |

### 4. App

| Caso | Acción | Resultado visible | Origen |
|---|---|---|---|
| AUTH-01 | Abrir la app sin sesión | Pantalla de login con "Usuario", "Clave" y "Ingresar", más la franja "DATOS SINTÉTICOS · PROTOTIPO" | Wireframe AUTH-01 |
| Login correcto | Credenciales válidas | Va al inicio de su rol (el contenido de cada inicio lo fija HU-02) | Gherkin esc. 1 |
| AUTH-02 | `401 CREDENCIALES_INVALIDAS` | Muestra "Usuario o clave incorrectos". El usuario queda escrito y la clave se vacía. No muestra los intentos restantes | Gherkin esc. 2, AUTH-02 |
| AUTH-04 | `423 CUENTA_BLOQUEADA` | Muestra "Cuenta bloqueada temporalmente. Podrá volver a intentar a las HH:MM (en N min).", con la hora local calculada desde `bloqueado_hasta`. Vacía la clave y "Ingresar" sigue activo | Gherkin esc. 4, AUTH-04 |
| AUTH-03 | `inactividad_s` sin que el usuario toque la pantalla, o un `401 SESION_VENCIDA` | Vuelve al login con "Su sesión se cerró por inactividad. Ingrese de nuevo.". El almacenamiento simulado de `expo-secure-store` queda sin ninguna clave; si después inicia sesión otro usuario, no aparece ningún dato del anterior (nombre, rol, pantallas); la app no vuelve a enviar el token anterior en ninguna solicitud; y "atrás" (`hardwareBackPress` de `BackHandler`) no vuelve a la pantalla anterior | Gherkin esc. 3, AUTH-03, TDD · **v2** |
| Sesión activa | El usuario interactúa con la app | La sesión no vence mientras haya interacción (la app renueva a tiempo; cómo lo hace es libre). **Cuenta como interacción** un `touchStart` sobre la vista raíz de la app, que lleva `testID="app-raiz"` | ADR-0011 · **v2** |
| Otro error | Error de red o `5xx` en el login | Muestra "No se pudo completar la operación; intente nuevamente". Nunca muestra un mensaje de credenciales | AGENTS.md regla 7 · DECISIÓN PROPUESTA 7 |
| Valor de inactividad | — | La app toma el tiempo de `inactividad_s` del login; no lo tiene fijo en el código | ADR-0011 ("sin cambiar código") |

### 4 bis. Interfaz de la app para las pruebas (v2)

| Caso | Valor exacto | Origen |
|---|---|---|
| Montaje | La app completa es el export por defecto de `apps/movil/App.tsx`. **Sin expo-router.** Renderizarlo muestra AUTH-01 si no hay sesión | SPRINT0 M-1 D · v2 |
| API | La app llama a `EXPO_PUBLIC_API_URL` + `/v1/...` con el `fetch` global, como en el Sprint 0 | SPRINT0 M-1 D · v2 |
| Vista raíz | Elemento con `testID="app-raiz"` que envuelve todas las pantallas | v2 |
| Atrás | El botón atrás de Android es `BackHandler` (`hardwareBackPress`) | v2 |
| Token | Se guarda en `expo-secure-store` (ADR-0013); el nombre de la clave es libre | ADR-0013 |

### 5. Bitácora y seguridad

| Caso | Salida esperada | Origen |
|---|---|---|
| Campos de cada evento | `id`, `ocurrido_en` (UTC, del servidor), `usuario_id` (nulo si el usuario no existe), `rol`, `tipo_evento`, `parametros`, `codigo_error`, `id_traza` (igual a `X-Id-Traza`), `es_sintetico = true` | ADR-0005 §4, TDD |
| Sin registro no hay sesión | Si la escritura del `LOGIN_OK` falla, el login responde `503` `{"codigo":"SERVICIO_NO_DISPONIBLE","mensaje":"No se pudo completar la operación; intente nuevamente",…}` y no entrega tokens | ADR-0005 §2 · DECISIÓN PROPUESTA 2 |
| La clave no queda en ningún lado | El valor de `clave` no aparece en la bitácora (`parametros` incluido), en los logs de la API ni en los del proxy | TDD, ADR-0003 Consecuencias |

### 6. Configuración y usuarios de prueba

| Caso | Salida esperada | Origen |
|---|---|---|
| Parámetros | `SESION_INACTIVIDAD_S` (600), `TOKEN_ACCESO_VIGENCIA_S` (900), `BLOQUEO_INTENTOS` (5) y `BLOQUEO_DURACION_S` (900) en `infra/.env.example`, marcados como provisionales (PA #18, #19). Cambiarlos no requiere tocar código | ADR-0011 |
| Carga de usuarios | `docker compose -f infra/docker-compose.yml run --rm api python -m app.cargar_usuarios` crea o actualiza los usuarios sintéticos de forma idempotente | ADR-0003 §2 · DECISIÓN PROPUESTA 8 |
| Usuarios fijos | `agente1`, `agente2`, `revisor1`, `supervisor1` (activos, con ese rol) e `inactivo1` (rol `agente`, `activo = false`) | ADR-0003 · DECISIÓN PROPUESTA 8 |
| Claves | Las toma de `CLAVE_USUARIOS_PRUEBA` en `infra/.env` (nunca versionada). La prueba la lee de la misma variable | AGENTS.md regla 8 · DECISIÓN PROPUESTA 8 |

## Nombres que no se negocian

| Tipo | Valor exacto |
|---|---|
| Rutas | `POST /v1/auth/login` · `POST /v1/auth/refresh` · `POST /v1/auth/logout` |
| Campos | `usuario`, `clave`, `token_acceso`, `token_renovacion`, `expira_en`, `inactividad_s`, `usuario.id`, `usuario.usuario`, `usuario.nombre`, `usuario.rol`, `bloqueado_hasta` |
| Roles | `agente` · `revisor` · `supervisor` |
| Códigos | `401 CREDENCIALES_INVALIDAS` · `423 CUENTA_BLOQUEADA` · `401 NO_AUTENTICADO` · `401 SESION_VENCIDA` · `422 SOLICITUD_INVALIDA` · `503 SERVICIO_NO_DISPONIBLE` |
| Mensajes de la API | "Usuario o clave incorrectos" · "Cuenta bloqueada temporalmente" · "Inicie sesión nuevamente" · "Su sesión se cerró por inactividad" · "No se pudo completar la operación; intente nuevamente" |
| Textos de la app | "Usuario" · "Clave" · "Ingresar" · "DATOS SINTÉTICOS · PROTOTIPO" · "Usuario o clave incorrectos" · "Cuenta bloqueada temporalmente. Podrá volver a intentar a las HH:MM (en N min)." · "Su sesión se cerró por inactividad. Ingrese de nuevo." · "No se pudo completar la operación; intente nuevamente" |
| Eventos de bitácora | `LOGIN_OK` · `LOGIN_FALLIDO` · `CUENTA_BLOQUEADA` · `SESION_VENCIDA` · `LOGOUT` |
| Variables | `SESION_INACTIVIDAD_S` · `TOKEN_ACCESO_VIGENCIA_S` · `BLOQUEO_INTENTOS` · `BLOQUEO_DURACION_S` · `CLAVE_USUARIOS_PRUEBA` |
| Comando | `python -m app.cargar_usuarios` (en el contenedor `api`) |
| Usuarios | `agente1` · `agente2` · `revisor1` · `supervisor1` · `inactivo1` |

## Rutas de cada rol

| Rol | Rutas | Origen |
|---|---|---|
| TESTER | `services/api/tests/`, `apps/movil/__tests__/`, `apps/movil/.maestro/` (si hay dev build), `pruebas/datos/` | AGENTS.md |
| DEV | `services/api/` (salvo `tests/`, incluida la migración), `apps/movil/` (salvo `__tests__/` y `.maestro/`), `infra/`, `contratos/api/openapi.json` (regenerado) | AGENTS.md |

## Avisos de contexto

- Patrones: formato de error, `X-Id-Traza` y logs JSON del Sprint 0; `PantallaEstado` como referencia de pantalla y de prueba Jest.
- El OpenAPI de `contratos/api/openapi.json` y los tipos de la app se regeneran (SPRINT0 criterio 9).
- La palabra prohibida (AGENTS.md regla 1) no puede aparecer en ningún texto nuevo.

## Decisiones propuestas (no venían en la tarea)

| # | Decisión | Por qué hace falta | Estado |
|---|---|---|---|
| 1 | **Supabase Auth en local:** se agrega al compose un servicio `auth` (la imagen oficial de Supabase Auth, GoTrue, con la versión fijada) sobre el `db` local, sin puerto publicado, solo para desarrollo y pruebas. En el VPS se usa el proyecto Supabase | Las pruebas necesitan un Supabase Auth. Sin él, solo quedarían el proyecto en la nube (que no existe todavía, y las pruebas dependerían de internet) o reemplazar Supabase (cambia el ADR-0001) | Aprobada por el humano (2026-11-19) |
| 2 | **La tabla `bitacora` nace en HU-01** (columnas del TDD, `INSERT` desde la API, fail-closed). El trigger, los permisos de solo inserción y `GET /v1/bitacora` llegan en HU-07. Las pruebas de HU-01 leen la tabla directamente. La prueba del fail-closed (simular un fallo de escritura) se hace en HU-07 | HU-01 es la primera HU que escribe en la bitácora, y su escenario 1 lo exige | Aprobada por el humano (2026-11-19) |
| 3 | Un usuario inactivo recibe la misma respuesta que una clave incorrecta | La HU no lo dice; si se distinguiera, se revelaría qué usuarios existen | Aprobada por el humano (2026-11-19) |
| 4 | Un cuerpo inválido (`422`) no cuenta como intento fallido ni deja evento | Sin esto, un error de la app podría bloquear cuentas | Aprobada por el humano (2026-11-19) |
| 5 | El bloqueo usa `423`, la respuesta trae `bloqueado_hasta` (la app calcula la hora local) y el conteo es por el texto de `usuario`, exista o no | AUTH-04 muestra la hora exacta. UX pide no revelar qué usuarios existen | Aprobada por el humano (2026-11-19) |
| 6 | La inactividad también se controla en el servidor (desde la última solicitud autenticada) y queda en la bitácora como `SESION_VENCIDA` | El TDD lista el evento `SESION_VENCIDA`. Si solo la controlara la app, una app cerrada dejaría la sesión viva y sin registro | Aprobada por el humano (2026-11-19) |
| 7 | Un error de red o `5xx` en el login muestra "No se pudo completar la operación; intente nuevamente" | La HU no cubre ese caso; la regla 7 prohíbe disfrazarlo de credenciales malas | Aprobada por el humano (2026-11-19) |
| 8 | Comando, usuarios fijos y `CLAVE_USUARIOS_PRUEBA` | El TESTER y el DEV no se ven y necesitan los mismos usuarios. La clave no puede versionarse | Aprobada por el humano (2026-11-19) |

## Fuera del contrato (decide el DEV)

- Cómo se valida la clave contra Supabase Auth, cómo se firman y verifican los JWT, y dónde se guarda la última actividad de la sesión.
- El esquema exacto de `control_acceso` y la estrategia de renovación en la app (siempre que la sesión no venza con el usuario interactuando).
- La navegación interna de la app, siempre sin expo-router (v2) y montada desde `App.tsx`.

## Preguntas abiertas para el humano

Respondidas por el humano el 2026-11-19:

1. **Decisiones 1 a 8:** aprobadas.
2. **Rama:** `hu-01` sale de `main` después del merge de `hu-08`.
3. **UX:** confirmada por el humano (vía PM, 2026-11-19). El UX revisa con capturas de Jest y del emulador, contra los wireframes, antes del veredicto.

## Changelog

| Versión | Fecha | Cambio | Motivo | Aprobado por |
|---|---|---|---|---|
| v1 | 2026-11-19 | Versión inicial | Encargo PM → LEAD, Iteración 1 | Humano, 2026-11-19 |
| v2 | 2026-11-19 | §4 bis (montaje en `App.tsx` sin expo-router, `fetch` global, `testID="app-raiz"`, `BackHandler`); AUTH-03 observable desde afuera (SecureStore simulado sin claves, sin datos del usuario anterior, sin el token viejo) en lugar de "caché y store vacíos"; qué cuenta como interacción | Hueco que reportó el TESTER: el contrato no fijaba la interfaz de la app para Jest | Humano, 2026-11-19 |
