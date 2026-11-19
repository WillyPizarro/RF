# CONTRATO — HU-02 Acceder solo a las funciones de mi rol

**Tipo:** Feature
**Versión:** v3
**Estado:** Aprobado (v1 a v3: 2026-11-19, humano)
**Origen:** `docs/hus/HU-02-acceso-por-rol.md` · encargo PM → LEAD (2026-11-19), Iteración 1, contrato 3 de 5
**Rama de trabajo:** la misma de HU-01 (`hu-01`), porque HU-02 depende del login (DECISIÓN PROPUESTA 1)
**Pasa por UX:** Sí. Pantallas HOME-01 y ERR-01 (`docs/ux/wireframes/HU-02-acceso-por-rol.md`).

---

## Paquete de contexto

| Fuente | Por qué entra |
|---|---|
| HU-02 | Historia y escenarios 1 y 2 |
| ADR-0003 | Tres roles (`agente`, `revisor`, `supervisor`), un rol por usuario, control en el backend, `403` más bitácora |
| ADR-0007 | `GET /v1/me` y el catálogo de rutas por rol; código `SIN_PERMISO` |
| TECH-DESIGN.md › Criterios › Sesión y acceso | Matriz completa de `403` con los tres roles · `ACCESO_DENEGADO` · menú según `GET /v1/me` |
| Wireframes HOME-01, ERR-01 | Textos y opciones visibles |
| CONTRATO-HU-01 | Login, tokens, usuarios fijos y tabla `bitacora` |

**Puntos abiertos de la HU:** PA #9 está resuelto por el ADR-0003 (tres roles). PA #2 (el revisor como rol distinto) se trabaja con el supuesto del ADR-0003, variante A. PA #3 (administración de usuarios) sigue sin pantalla, por el conflicto C1. Ninguno impide construir. Si la sesión del 25-nov cambia los roles o las opciones, se versiona el contrato (lo dice el encargo).

## Interfaz observable

1. **API:** `GET /v1/me` y la respuesta `403` de cualquier ruta reservada a otro rol.
2. **App:** el inicio de cada rol (opciones visibles) y la pantalla ERR-01.
3. **Base de datos:** filas `ACCESO_DENEGADO` en `bitacora`.

## Comportamiento

### 1. Perfil

```text
GET /v1/me   (Authorization: Bearer <token_acceso>)
```

| Caso | Entrada | Salida esperada | Origen |
|---|---|---|---|
| Perfil | Token válido de cualquier rol | `200` `{"id":"…","usuario":"agente1","nombre":"…","rol":"agente"}` | ADR-0007 |
| Sin token o token inválido | — | `401` `NO_AUTENTICADO` (CONTRATO-HU-01) | ADR-0003 §4 |
| El rol sale del servidor | Un token manipulado para declarar otro rol | `401` (la firma no valida). El rol nunca se toma de lo que envía el cliente | ADR-0003 §4 |

### 2. Rechazo por rol

| Caso | Entrada | Salida esperada | Origen |
|---|---|---|---|
| Ruta de otro rol | Usuario autenticado llama a una ruta que su rol no tiene | `403` `{"codigo":"SIN_PERMISO","mensaje":"No tiene permiso para usar esta función","id_traza":"…"}` · bitácora `ACCESO_DENEGADO` con `usuario_id`, `rol`, la ruta y el método en `parametros` | Gherkin esc. 2, ADR-0003 §4, ADR-0007 |
| Primero autenticación | Sin token en una ruta de rol | `401 NO_AUTENTICADO`, no `403`, y sin evento `ACCESO_DENEGADO` | DECISIÓN PROPUESTA 2 |
| Sin efecto | Una ruta rechazada con `403` | No ejecuta nada: no consulta fuentes ni escribe otros eventos | HU-02 Supuestos ("control en el backend") |

**Matriz de roles** (fuente: ADR-0003 y ADR-0007). Cada HU que construye una ruta prueba su fila con los tres roles:

| Ruta | `agente` | `revisor` | `supervisor` | Se prueba en |
|---|---|---|---|---|
| `GET /v1/me`, `/v1/auth/*` | sí | sí | sí | HU-01, HU-02 |
| `POST /v1/consultas/placa` | sí | 403 | 403 | HU-03 |
| `POST /v1/consultas/rostro`, `GET /v1/consultas/{id}` | sí | 403 | 403 | HU-05 |
| `GET /v1/revisiones`, `GET /v1/revisiones/{id}`, `POST /v1/revisiones/{id}/decision` | 403 | sí | 403 | HU-06 |
| `GET /v1/bitacora` | 403 | 403 | sí | HU-07 |

En esta HU todavía no existe ninguna ruta reservada a un rol. El mecanismo de `403` (código, mensaje y evento) queda construido, y su prueba con rutas reales viaja a los contratos de HU-03 y HU-07 en esta iteración (DECISIÓN PROPUESTA 3).

### 3. App

| Caso | Rol | Resultado visible | Origen |
|---|---|---|---|
| Inicio del agente (HOME-01) | `agente` | Encabezado "Hola, <nombre>" con "Rol: Agente" y "Salir". Opciones "Consultar placa" y "Verificar rostro", más el enlace "Mis verificaciones". No hay opciones de revisión ni de bitácora | Gherkin esc. 1, HOME-01 |
| Inicio del revisor | `revisor` | Encabezado con "Rol: Revisor" y "Salir". Opción "Pendientes de revisión". Nada de consulta ni de bitácora | ADR-0003, flujo UX (REV-01) |
| Inicio del supervisor | `supervisor` | Encabezado con "Rol: Supervisor" y "Salir". Opción "Bitácora". Nada de consulta ni de revisión | ADR-0003, flujo UX (BIT-01) |
| El menú sale de `/v1/me` | Cualquiera | Las opciones dependen del `rol` que devuelve la API, no de un valor guardado en la app | TDD |
| Opción cuya pantalla aún no existe | Cualquiera | La opción aparece **deshabilitada** hasta que su HU construya la pantalla (HU-03, HU-05, HU-06, HU-07) | DECISIÓN PROPUESTA 4 |
| ERR-01 | Cualquiera, ante un `403 SIN_PERMISO` | "No tiene permiso para usar esta función." · "El intento quedó registrado." · botón "Volver al inicio" (vuelve al inicio de su rol). **Se prueba en HU-03** (CONTRATO-HU-03 v2): en este ciclo ninguna solicitud de la app puede recibir un `403`. Aquí se construye y no se verifica | Gherkin esc. 2, ERR-01 · **v3** |
| "Salir" | Cualquiera | Llama a `POST /v1/auth/logout`, vacía el almacenamiento (como en AUTH-03) y vuelve a AUTH-01 sin mensaje | UX (elemento aprobado), CONTRATO-HU-01 |

## Nombres que no se negocian

| Tipo | Valor exacto |
|---|---|
| Ruta | `GET /v1/me` |
| Campos | `id`, `usuario`, `nombre`, `rol` |
| Roles | `agente` · `revisor` · `supervisor` |
| Código | `403 SIN_PERMISO` |
| Mensaje de la API | "No tiene permiso para usar esta función" |
| Evento | `ACCESO_DENEGADO` |
| Textos de la app | "Hola, <nombre>" · "Rol: Agente" · "Rol: Revisor" · "Rol: Supervisor" · "Salir" · "Consultar placa" · "Verificar rostro" · "Mis verificaciones" · "Pendientes de revisión" · "Bitácora" · "No tiene permiso para usar esta función." · "El intento quedó registrado." · "Volver al inicio" |

## Rutas de cada rol

Las mismas que CONTRATO-HU-01 (AGENTS.md).

## Decisiones propuestas (no venían en la tarea)

| # | Decisión | Por qué hace falta | Estado |
|---|---|---|---|
| 1 | HU-01 y HU-02 se construyen juntas, en la misma rama y en el mismo ciclo de TESTER y DEV, con un solo veredicto | HU-02 no se puede probar sin login, y las pantallas de inicio son el destino del login | Aprobada por el humano (2026-11-19) |
| 2 | Sin token se responde `401` antes que `403` | Orden estándar. Evita llenar la bitácora con `ACCESO_DENEGADO` anónimos | Aprobada por el humano (2026-11-19) |
| 3 | La matriz de `403` se prueba en cada HU que crea una ruta (HU-03 y HU-07 en esta iteración), sin agregar rutas solo para pruebas | Hoy no existe ninguna ruta de rol. SPRINT0 M-2 prohíbe las rutas solo para pruebas | Aprobada por el humano (2026-11-19) |
| 4 | Las opciones sin pantalla aparecen deshabilitadas | Mostrar el menú completo sirve para la demo, y una opción que no lleva a ningún lado confunde | Aprobada por el humano (2026-11-19) |
| 5 | Textos de los inicios del revisor y del supervisor ("Pendientes de revisión", "Bitácora", "Rol: …") | UX solo dibujó el inicio del agente; los otros dos son pantallas de otras HUs | Aprobada por el humano (2026-11-19) |

## Fuera del contrato (decide el DEV)

- Cómo se declara qué rol tiene cada ruta (decorador, dependencia o tabla) y cómo navega la app, dentro de la interfaz que fija CONTRATO-HU-01 §4 bis (v2): montaje en `App.tsx` sin expo-router, `fetch` global y `testID="app-raiz"`.

## Preguntas abiertas para el humano

Respondidas por el humano el 2026-11-19:

1. **Decisiones 1 a 5:** aprobadas. HU-01 y HU-02 tienen un solo encargo y un solo veredicto, en `hu-01`.
2. **Decisión 4:** se aprueba como estaba propuesta: las opciones sin pantalla aparecen deshabilitadas.

## Changelog

| Versión | Fecha | Cambio | Motivo | Aprobado por |
|---|---|---|---|---|
| v1 | 2026-11-19 | Versión inicial | Encargo PM → LEAD, Iteración 1 | Humano, 2026-11-19 |
| v2 | 2026-11-19 | La app se prueba con la interfaz de CONTRATO-HU-01 §4 bis (v2) | Hueco que reportó el TESTER | Humano, 2026-11-19 |
| v3 | 2026-11-19 | La prueba de ERR-01 pasa a HU-03 | Hueco que reportó el TESTER: en este ciclo no hay ninguna solicitud de la app que pueda recibir un `403` | Humano, 2026-11-19 |
