# Informe TESTER — HU-01 + HU-02 (iniciar sesión y acceso por rol)

**Contratos:** `docs/contratos/CONTRATO-HU-01.md` **v2** y `docs/contratos/CONTRATO-HU-02.md` **v3** · **Encargo:** `docs/contratos/ENCARGO-HU-01-02.md` (M-1, M-2) · **Rama:** `hu-01`
**Estado:** pruebas escritas; **suite completa pendiente** de la orden del LEAD (orden del cierre, punto 3: después de la entrega del DEV y la aprobación del UX). Las corridas hechas hasta ahora solo comprobaron el arnés contra lo que había; no son hallazgos.

## Cómo se corren

| Parte | Comando | Notas |
|---|---|---|
| API y bitácora | `pytest services/api/tests --integracion` (desde el anfitrión, con el sistema arrancado con `docker-compose.yml` + `docker-compose.fotos.yml`) | Las peticiones salen desde dentro del contenedor `api` a `http://api:8000` (encargo, regla 8). La bitácora se lee con `psql` dentro de `db` (HU-01, decisión 2). Las pruebas de tiempos recrean **solo** `api` (`--no-deps`) con un archivo de entorno temporal fuera del repositorio, y al final vuelven a `infra/.env` |
| App | `npx jest __tests__/HU01_HU02.test.tsx` en `apps/movil` | Monta el export por defecto de `App.tsx` (HU-01 §4 bis). Se simulan el `fetch` global, `expo-secure-store` (en memoria) y `BackHandler.addEventListener` |

**Requisito:** `CLAVE_USUARIOS_PRUEBA` en `infra/.env` (la misma que usa `python -m app.cargar_usuarios`) y los usuarios cargados.

Configuraciones de la API usadas por las pruebas (cambiarlas sin tocar código es parte de §6):

| Nombre | Valores | Para qué |
|---|---|---|
| por defecto | `infra/.env` sin cambios (600 / 900 / 5 / 900) | Login, perfil, 422, logout, bitácora, valores por defecto |
| corta | `SESION_INACTIVIDAD_S=12`, `TOKEN_ACCESO_VIGENCIA_S=120`, `BLOQUEO_DURACION_S=12` | Bloqueo con usuarios reales, inactividad, renovación |
| token corto | `TOKEN_ACCESO_VIGENCIA_S=6`, `SESION_INACTIVIDAD_S=600` | Token de acceso vencido |

## Caso del contrato → prueba

### HU-01 (v2) — API (`services/api/tests/`)

| § | Caso | Prueba | Estado |
|---|---|---|---|
| 1 | Camino feliz, los 4 usuarios activos con su rol | `test_hu01_login.py::test_camino_feliz` | Pendiente |
| 1 | `LOGIN_OK` con `usuario_id`, `rol`, `ocurrido_en` del servidor, `id_traza`, `es_sintetico` | `::test_camino_feliz_deja_login_ok` | Pendiente |
| 1 | Clave incorrecta → 401 `CREDENCIALES_INVALIDAS` + `LOGIN_FALLIDO` | `::test_clave_incorrecta` | Pendiente |
| 1 | Usuario inexistente idéntico; `usuario_id` nulo y el texto en `parametros` | `::test_usuario_inexistente_identico` | Pendiente |
| 1 | Usuario inactivo idéntico (decisión 3) | `::test_usuario_inactivo_identico` | Pendiente |
| 1 | Cuerpo inválido → 422 `SOLICITUD_INVALIDA`, formato estándar, sin evento (**pendiente del Sprint 0**) | `::test_cuerpo_invalido_422` (6 cuerpos) | Pendiente |
| 1 | Cuerpo inválido no cuenta como intento (decisión 4) | `test_hu01_bloqueo.py::test_cuerpo_invalido_no_cuenta_como_intento` | Pendiente |
| 1 | Éxito reinicia el contador | `test_hu01_bloqueo.py::test_exito_reinicia_el_contador` | Pendiente |
| 2 | 5.º fallo → 423 con `bloqueado_hasta` UTC; `LOGIN_FALLIDO` + `CUENTA_BLOQUEADA` | `::test_quinto_fallo_bloquea` | Pendiente |
| 2 | Clave correcta o incorrecta durante el bloqueo: mismo 423, mismo `bloqueado_hasta`, `LOGIN_FALLIDO` con `codigo_error` `CUENTA_BLOQUEADA` | `::test_durante_el_bloqueo_clave_correcta_o_incorrecta_identicas` | Pendiente |
| 2 | Fin del bloqueo → 200 y contador en 0 | `::test_fin_del_bloqueo` | Pendiente |
| 2 | Usuario inexistente también se bloquea (decisión 5) | `::test_usuario_inexistente_tambien_se_bloquea` | Pendiente |
| 2 | Valores por defecto: 5 intentos, 900 s | `::test_valores_por_defecto_5_intentos_15_min` | Pendiente |
| 3 | Renovar → 200 con la forma del login | `test_hu01_sesion.py::test_renovar` | Pendiente |
| 3 | Sin token / token basura / firma inválida → 401 `NO_AUTENTICADO` | `::test_sin_token`, `::test_token_basura`, `::test_firma_invalida`, `::test_logout_sin_token` | Pendiente |
| 3 | Token de acceso vencido → 401 `NO_AUTENTICADO` | `::test_token_vencido` | Pendiente |
| 3 | Inactividad en el servidor (solicitud y renovación) → 401 `SESION_VENCIDA`, evento, sesión invalidada | `::test_inactividad_en_una_solicitud`, `::test_inactividad_en_la_renovacion` | Pendiente |
| 3 | La actividad mantiene la sesión | `::test_la_actividad_mantiene_la_sesion` | Pendiente |
| 3 | Cerrar sesión → 204, `LOGOUT`, el `token_renovacion` deja de servir | `::test_cerrar_sesion` | Pendiente |
| 5 | Campos de cada evento; `id_traza` = `X-Id-Traza` | `test_hu01_bitacora_config.py::test_campos_de_cada_evento`, `::test_id_traza_del_evento_igual_a_la_cabecera` | Pendiente |
| 5 | Sin registro no hay sesión (503) | — | **NO VERIFICADO**: se prueba en HU-07 (decisión 2) |
| 5 | La clave no queda en la bitácora ni en los logs de la API | `::test_la_clave_no_queda_en_la_bitacora`, `::test_la_clave_no_queda_en_los_logs_de_la_api` | Pendiente |
| 5 | Ni en los logs del proxy | `::test_la_clave_no_queda_en_los_logs_del_proxy` | Probablemente **NO VERIFICADO (entorno)**: el proxy no arranca con el puerto 80 ocupado (regla 8) |
| 6 | Parámetros en `.env.example`, con sus valores y marcados como provisionales | `::test_parametros_en_env_example` | Pendiente |
| 6 | Cambiarlos no requiere tocar código | `::test_cambiar_parametros_no_toca_codigo` (y todas las pruebas con configuración corta) | Pendiente |
| 6 | Carga de usuarios idempotente; usuarios fijos; `inactivo1` inactivo | `::test_carga_de_usuarios_idempotente` | Pendiente |
| 6 | `CLAVE_USUARIOS_PRUEBA` en `infra/.env` y no versionada | `::test_clave_de_usuarios_desde_el_entorno` | Pendiente |

### HU-01 (v2) — App (`apps/movil/__tests__/HU01_HU02.test.tsx`)

| Caso | Prueba | Estado |
|---|---|---|
| AUTH-01: textos, franja y `testID="app-raiz"` | `AUTH-01 › sin sesión muestra…` | Pendiente |
| La app usa `EXPO_PUBLIC_API_URL` + `/v1/auth/login` con el `fetch` global (§4 bis) | `AUTH-01 › envía usuario y clave…` | Pendiente |
| Login correcto → inicio de su rol; el token va a SecureStore | `AUTH-01 › login correcto…` | Pendiente |
| AUTH-02: mensaje, el usuario queda escrito, la clave se vacía, sin intentos restantes | `AUTH-02 › …` | Pendiente |
| AUTH-04: hora local HH:MM y minutos desde `bloqueado_hasta`, clave vacía, "Ingresar" activo | `AUTH-04 › …` | Pendiente. El contrato no fija el redondeo de los minutos: se acepta el entero por abajo o por arriba |
| Otro error (red, 500, 503) → mensaje genérico, nunca el de credenciales | `otro error › …` (3 casos) | Pendiente |
| AUTH-03 por inactividad, con el tiempo de `inactividad_s` del login (2 s) | `AUTH-03 › sin tocar la pantalla…` | Pendiente |
| AUTH-03: SecureStore sin claves, "atrás" no vuelve, otro usuario no ve datos del anterior, no se reenvía el token viejo (v2) | `AUTH-03 › tras el cierre…` | Pendiente |
| AUTH-03 por `401 SESION_VENCIDA` | `AUTH-03 › un 401 SESION_VENCIDA…` | Pendiente |
| Sesión activa con `touchStart` sobre `app-raiz` (v2) | `AUTH-03 › sesión activa…` | Pendiente |

### HU-02 (v3)

| § | Caso | Prueba | Estado |
|---|---|---|---|
| 1 | Perfil `GET /v1/me` de los 4 usuarios | `test_hu02_perfil_roles.py::test_perfil` | Pendiente |
| 1/2 | Sin token → 401 y sin `ACCESO_DENEGADO` (decisión 2) | `::test_sin_token_401_sin_acceso_denegado` | Pendiente |
| 1 | Token manipulado para declarar otro rol → 401; el rol enviado por el cliente se ignora | `::test_rol_manipulado_no_valida`, `::test_rol_enviado_por_el_cliente_se_ignora` | Pendiente |
| 2 | Matriz de 403 `SIN_PERMISO` + `ACCESO_DENEGADO`; "Sin efecto" | `::test_matriz_403_sin_permiso` (skip) | **NO VERIFICADO**: no hay rutas de rol; pasa a HU-03 y HU-07 (decisión 3) |
| 3 | Inicio del agente, del revisor y del supervisor (textos, opciones, deshabilitadas, nada de otros roles) | Jest `HU-02 — inicio por rol › agente/revisor/supervisor` | Pendiente |
| 3 | El menú sale de `GET /v1/me` | Jest `› el menú sale de GET /v1/me…` | Pendiente |
| 3 | "Salir": logout con el token, SecureStore vacío, AUTH-01 sin mensaje | Jest `› Salir…` | Pendiente |
| 3 | ERR-01 | — | **Diferido a HU-03 (v3)** |

## Cambios al arnés del Sprint 0

- `services/api/tests/conftest.py`: `Compose` usa siempre `docker-compose.fotos.yml` (regla 7 del encargo). Las pruebas se ordenan por configuración de la API para recrearla las menos veces posible. Hay fixtures nuevas (`sistema`, `config_defecto`, `config_corta`, `config_token_corto`, `clave`).
- Nuevos `red_interna.py` (API por la red interna, bitácora y configuración) y `ayudas_hu01.py` (formas del contrato).
