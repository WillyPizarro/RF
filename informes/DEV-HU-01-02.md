# Informe DEV — HU-01 + HU-02 (sesión y acceso por rol)

**Documentos de trabajo:** `docs/contratos/CONTRATO-HU-01.md` **v4** y `docs/contratos/CONTRATO-HU-02.md` **v3** · **Encargo:** `docs/contratos/ENCARGO-HU-01-02.md` con M-1 a M-6 · **Rama:** `hu-01` · **Fecha:** 2026-11-19

No leí ni ejecuté las pruebas del TESTER.

## Corrección por M-6 (veredicto, vuelta 1: A1)

**Problema:** un `401 SESION_VENCIDA` en el `GET /v1/me` no mostraba AUTH-03.
- Después del login caía en el mensaje genérico.
- Al retomar la sesión al abrir la app, con la renovación en `200`, cerraba sin aviso.

**Corrección:** en `apps/movil/src/sesion/controlador.ts`, `cargarPerfil` ahora informa si el fallo fue un `401 SESION_VENCIDA`.
- `ingresar` y `restaurar` cierran la sesión con el aviso de inactividad en ese caso: "Su sesión se cerró por inactividad. Ingrese de nuevo." (CONTRATO-HU-01 §4, AUTH-03).
- Los demás fallos de `/v1/me` siguen igual: mensaje genérico tras el login y login sin mensaje al retomar.
- No cambió ningún texto.

**Verificación:** con una prueba Jest temporal, ya borrada, que monta `App.tsx` con `fetch` y `expo-secure-store` simulados.

| Caso | Sin el arreglo | Con el arreglo |
|---|---|---|
| Login `200` y luego `/v1/me` con `401 SESION_VENCIDA` | Falla | AUTH-03, y el almacenamiento queda vacío |
| Retomar: renovación `200` y luego `/v1/me` con `401 SESION_VENCIDA` | Falla | AUTH-03, y el almacenamiento queda vacío |
| Login `200` y luego `/v1/me` con `500` (control) | Pasa | Sigue el mensaje genérico |
| Retomar con `/v1/me` en `500` (control) | Pasa | Sigue el login sin mensaje |

`tsc` no da errores.

## Cambios por M-3 y M-4 (revisión del UX)

| Origen | Qué cambió | Archivos |
|---|---|---|
| HU-01 v3 (M-3) | Nada: la renovación exitosa ya contaba como actividad en `e6c6f22` | — |
| HU-01 v4 (UX #5) | "Ingresar" con el usuario o la clave vacíos, o solo con espacios, muestra "Ingrese su usuario y su clave" (tono ámbar, sin ícono) y **no envía** la solicitud | `src/pantallas/PantallaLogin.tsx`, `src/estado/sesion.ts` |
| UX #1 | Íconos ⚠ (AUTH-02), ⓘ (AUTH-03) y 🔒 (AUTH-04) delante del mensaje, ocultos al lector de pantalla (`accessibilityElementsHidden` e `importantForAccessibility="no-hide-descendants"`). El texto del mensaje sigue en su propio `Text`, sin cambios | `src/pantallas/PantallaLogin.tsx` |
| UX #3 | "Salir" (y "Mis verificaciones", que usa el mismo estilo secundario) con 48 de alto mínimo | `src/pantallas/comunes.tsx` |
| UX #4 | El error de red o del servidor pasa a un tono neutro gris, sin ícono. "Usuario o clave incorrectos" sigue en rojo | `src/pantallas/PantallaLogin.tsx`, `src/pantallas/comunes.tsx` |
| UX #2 | Sin cambios: queda para HU-03 y HU-05 (M-4) | — |

Lo verifiqué con otra prueba Jest temporal, ya borrada:

- Las cuatro combinaciones de campos vacíos o con espacios muestran el mensaje y hacen **0** llamadas a `fetch`.
- `getByText` sigue encontrando cada mensaje con su texto exacto.
- El ícono ⚠ tiene las dos propiedades que lo ocultan al lector de pantalla.
- AUTH-03 sigue funcionando.
- `npx tsc --noEmit` no da errores.

**Capturas nuevas (M-4):** `C:\Willy\Trabajo\MININTER\Movil_Buscador_capturas\HU-01-02-v4\`. Hay un PNG y un HTML de cada una de estas pantallas: `AUTH-01_vacio`, `AUTH-02_credenciales`, `AUTH-03_inactividad`, `AUTH-04_bloqueada`, `AUTH-xx_otro_error` y `HOME-01_inicio_agente`. Se hicieron con el mismo método que las anteriores: el árbol de Jest pasado a HTML y fotografiado con Chrome headless.

## Qué construí

### API (`services/api/`)

| Pieza | Archivos | Notas |
|---|---|---|
| Rutas de sesión | `app/auth.py` | `POST /v1/auth/login`, `/refresh` y `/logout`, con los códigos y mensajes exactos del contrato. `bloqueado_hasta` en ISO 8601 UTC, al segundo (`2026-11-19T23:00:21Z`) |
| Perfil | `app/perfil.py` | `GET /v1/me` → `{id, usuario, nombre, rol}`, resuelto en el servidor |
| Sesión y rol | `app/sesion.py` | Dependencia `usuario_actual` (401 `NO_AUTENTICADO` o `SESION_VENCIDA`) y `requiere_rol(...)` (403 `SIN_PERMISO` + `ACCESO_DENEGADO`, siempre después de autenticar). Hoy ninguna ruta la usa (CONTRATO-HU-02, decisión 3); HU-03 y HU-07 la aplican |
| Supabase Auth | `app/supabase_auth.py` | Valida la clave con el grant `password` de GoTrue y cierra de inmediato esa sesión de Supabase. Un error de Supabase da 503 `SERVICIO_NO_DISPONIBLE`, nunca "clave incorrecta" (regla 7) |
| Bitácora | `app/bitacora.py`, migración `0002_sesion_bitacora` | Tabla con las columnas del TDD, `es_sintetico = true`, `ocurrido_en` del servidor (UTC) e `id_traza` igual a `X-Id-Traza`. Escritura dentro de la misma transacción: si falla, no hay tokens (503). Trigger y permisos: HU-07 |
| Tablas | migración `0002_sesion_bitacora` | `usuario_perfil` (con la columna `usuario`), `control_acceso` (por el texto del usuario normalizado, exista o no), `sesion` (hash del token de renovación, `ultima_actividad`, `estado`) y `bitacora` |
| Carga de usuarios | `app/cargar_usuarios.py` | `python -m app.cargar_usuarios`: aplica las migraciones pendientes, crea o actualiza en Supabase Auth y en `usuario_perfil` a `agente1`, `agente2`, `revisor1`, `supervisor1` e `inactivo1` (`activo = false`). Idempotente (lo corrí dos veces). No imprime la clave |
| Errores | `app/errores.py` | `ErrorApi` para los códigos propios. Formato `{codigo, mensaje, id_traza}` (+ `bloqueado_hasta` en el 423). El 422 `SOLICITUD_INVALIDA` ya existía y ahora también cubre el login |
| Motor de base | `app/bd.py` | Un motor por bucle de eventos: un cliente de pruebas en proceso (`TestClient`) usa varios bucles, y asyncpg no comparte conexiones entre bucles. Con uvicorn no cambia nada |
| Dependencia | `pyproject.toml` | `pyjwt==2.15.1`, para firmar y verificar los JWT (ADR-0003 §4) |

**Cómo funciona la sesión (lo que el contrato deja al DEV):**

- **Token de acceso:** JWT HS256 que firma la API con `JWT_SECRETO` (`iss`, `sub`, `sid`, `iat`, `exp`). **No lleva el rol**: el rol sale de `usuario_perfil` en cada solicitud. Un token con otra firma da `401`.
- **Token de renovación:** valor aleatorio. En la base solo queda su sha256. La renovación devuelve el **mismo** token de renovación y un token de acceso nuevo (sin rotación).
- **Inactividad en el servidor:** cada solicitud autenticada **y cada renovación** actualizan `ultima_actividad`. Las renovaciones cuentan porque en el inicio no hay ninguna otra llamada autenticada: si solo contaran las solicitudes autenticadas, la sesión vencería aunque el usuario estuviera tocando la pantalla. Pasado `SESION_INACTIVIDAD_S`, la sesión queda `vencida` y se registra **un** `SESION_VENCIDA`. Después responde `401 SESION_VENCIDA` sin repetir el evento.
- **Bloqueo:** se cuenta por el texto del usuario en minúsculas y sin espacios en los extremos, exista o no el usuario. Al 5.º fallo seguido se guarda `bloqueado_hasta` y se registran `LOGIN_FALLIDO` y `CUENTA_BLOQUEADA`. Mientras dure el bloqueo no se valida la clave y se registra `LOGIN_FALLIDO` con `codigo_error = CUENTA_BLOQUEADA`. Cuando el bloqueo vence, el contador vuelve a 0.
- **Usuario inexistente o inactivo:** también se llama a Supabase Auth, para que el tiempo de respuesta no delate qué usuarios existen.

### Infra (`infra/`)

- **`auth`:** Supabase Auth oficial, `supabase/gotrue:v2.198.0`, sin puerto publicado, sobre el `db` local (decisión 1).
- **`auth-preparar`:** `postgres:17` corre `infra/auth/preparar.sql`, que crea de forma idempotente el usuario `supabase_auth_admin`, el esquema `auth` y el rol `postgres` que piden las migraciones de GoTrue. Termina y sale; no deja la clave en su log.
- `api` depende de `auth` (healthy).
- Variables nuevas en `infra/.env.example`: `AUTH_URL`, `AUTH_APIKEY`, `AUTH_JWT_SECRETO`, `AUTH_DB_CLAVE`, `JWT_SECRETO`, `SESION_INACTIVIDAD_S` (600), `TOKEN_ACCESO_VIGENCIA_S` (900), `BLOQUEO_INTENTOS` (5), `BLOQUEO_DURACION_S` (900) y `CLAVE_USUARIOS_PRUEBA`. Las cuatro de tiempos e intentos van marcadas como provisionales (PA #18, #19).
- **Mi `infra/.env` local (no versionado):** le agregué estas variables con secretos y una `CLAVE_USUARIOS_PRUEBA` aleatorios. No los mostré en ningún lado.

### App (`apps/movil/`)

| Pieza | Archivos | Notas |
|---|---|---|
| Montaje | `App.tsx` | App completa sin expo-router (§4 bis): una pantalla a la vez según el store. Vista raíz con `testID="app-raiz"`, cuyo `onTouchStart` es la interacción. Cada montaje empieza limpio y el desmontaje cancela los temporizadores |
| Pantallas | `src/pantallas/PantallaLogin.tsx`, `PantallaInicio.tsx`, `PantallaSinPermiso.tsx`, `comunes.tsx` | AUTH-01 a AUTH-04, el error genérico, HOME-01, los inicios del revisor y del supervisor (opciones **deshabilitadas**, decisión 4) y ERR-01 (construida; su prueba es de HU-03) |
| Sesión | `src/sesion/controlador.ts`, `src/sesion/almacen.ts`, `src/estado/sesion.ts` | Tokens en `expo-secure-store` (`sesion.token_acceso`, `sesion.token_renovacion`), perfil en Zustand en memoria. Temporizador de `inactividad_s`, que viene del login y no está fijo en el código. Renovación en segundo plano con la interacción (como mucho cada `min(60 s, inactividad/3)`, y antes de que venza el token). El cierre borra SecureStore, la caché de TanStack Query y el store, sube una "generación" para descartar respuestas pendientes y no vuelve a enviar el token viejo. Al abrir la app, si quedó un token de renovación, intenta retomar la sesión |
| API | `src/api/cliente.ts`, `src/api/sesion.ts` | `fetch` global con `EXPO_PUBLIC_API_URL`. Un error de red nunca se muestra como credenciales |
| Tipos | `src/api/esquema.ts`, `contratos/api/openapi.json` | Regenerados (`exportar_openapi.py` y `npm run generar:api`) |

**Comportamiento de la app que el contrato no fija:**

- **Campos vacíos:** desde la v4 los fija el contrato (ver arriba).
- **Clave:** se vacía apenas se envía, sea cual sea el resultado.
- **Usuario tras un cierre:** al cerrar la sesión, el login se vuelve a montar con el campo de usuario vacío, así no queda ningún dato del usuario anterior.
- **Atrás:** en ERR-01 vuelve al inicio del rol. En las demás pantallas lo maneja el sistema: no hay pila de pantallas a la que volver.
- **Si `GET /v1/me` falla después de un login correcto:** se cierra todo y el login muestra "No se pudo completar la operación; intente nuevamente".

## Cómo se arranca y se cargan los usuarios

```bash
cp infra/.env.example infra/.env     # completar secretos y CLAVE_USUARIOS_PRUEBA
docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env up -d --build
docker compose -f infra/docker-compose.yml --env-file infra/.env run --rm api python -m app.cargar_usuarios
```

Para probar la inactividad y el bloqueo sin esperar 10 o 15 minutos, se arranca la API con valores cortos, por ejemplo `SESION_INACTIVIDAD_S=4 BLOQUEO_DURACION_S=4 docker compose … up -d api`.

## Lo que verifiqué

| Qué | Cómo | Resultado |
|---|---|---|
| Casos de API de HU-01 §1 a §3 y §5 | Script mío fuera del repo, corrido dentro del contenedor `api` contra `http://127.0.0.1:8000`, leyendo `bitacora` directamente, con `SESION_INACTIVIDAD_S=4` y `BLOQUEO_DURACION_S=4` | Todos OK: login 200 con la forma exacta y `LOGIN_OK`; clave mala, usuario inexistente e inactivo dan el mismo 401 y `LOGIN_FALLIDO` (el inexistente con `usuario_id` nulo y el texto en `parametros`); los cinco 422 sin evento; `/v1/me`; 401 sin token, con firma ajena y vencido; renovación; inactividad (`SESION_VENCIDA` una vez, y renovar después da 401); la actividad mantiene la sesión; logout 204 con `LOGOUT`, y después el token de renovación da 401; un acierto pone el contador en 0; el 5.º fallo da 423 con `LOGIN_FALLIDO` y `CUENTA_BLOQUEADA`; durante el bloqueo, clave buena o mala dan el mismo `bloqueado_hasta`; un usuario inexistente también se bloquea; al terminar el bloqueo, 200 |
| La clave en ningún lado | `grep -F` del valor de `CLAVE_USUARIOS_PRUEBA` en `docker compose logs api auth proxy` y en `json_agg(bitacora)` | 0 coincidencias |
| Mecanismo de 403 (HU-02 §2) | `TestClient` con una ruta temporal en memoria (no está en el repo) protegida con `requiere_rol('supervisor')` | Sin token → 401 `NO_AUTENTICADO`; agente → 403 `SIN_PERMISO` con el mensaje exacto y `ACCESO_DENEGADO` con `{"ruta","metodo"}`; supervisor → 200 |
| `GET /v1/salud` | Desde `api` | Sin cambios: 200 `{"estado":"ok","bd":"ok","simuladores":"ok",…}` |
| Carga de usuarios | Dos corridas seguidas | Idempotente |
| App | Prueba Jest temporal mía (fuera de `__tests__`, ya borrada) que monta `App.tsx` con `fetch` y `expo-secure-store` simulados | 9/9: AUTH-01; AUTH-02 (el usuario queda y la clave se vacía); AUTH-04 con la hora local y "(en 15 min)"; error de red y 503 → mensaje genérico; inicio de los tres roles con sus opciones exactas; el menú sale de `/v1/me` aunque el login diga otro rol; AUTH-03 con temporizadores simulados (SecureStore vacío, usuario vacío, "atrás" mediante el manejador real de `hardwareBackPress` no vuelve, el siguiente usuario no ve nada del anterior y nunca se reenvía `Bearer VIEJO`); 30 min de toques cada 60 s no cierran la sesión y renuevan; 401 `SESION_VENCIDA` al renovar → AUTH-03; "Salir" llama a `logout` y vuelve sin mensaje |
| Tipos | `npx tsc --noEmit` | Sin errores |
| Palabra prohibida | `grep -ri identificad` en lo nuevo | Sin coincidencias |

**No verificado:**

- Nada por el proxy (`https://localhost`): el puerto 80 está ocupado por `http.sys` (encargo, regla 8).
- El fail-closed con una falla real de escritura en la bitácora: va en HU-07 (decisión 2).
- En el emulador: no hay Android SDK en esta máquina.

## Capturas para el UX

Están en **`C:\Willy\Trabajo\MININTER\Movil_Buscador_capturas\HU-01-02\`**, fuera del repositorio. Hay un `.png` (390 px de ancho) y un `.html` por pantalla: `AUTH-01_login`, `AUTH-02_credenciales`, `AUTH-03_inactividad`, `AUTH-04_bloqueada`, `AUTH-xx_otro_error`, `HOME-01_inicio_agente`, `HOME_inicio_revisor`, `HOME_inicio_supervisor` y `ERR-01_sin_permiso`.

**Cómo se hicieron:** son el árbol que renderiza Jest al montar `App.tsx` (los componentes y estilos reales), convertido a HTML y fotografiado con Chrome headless. **No son del emulador**: la tipografía y los detalles nativos (teclado, sombras, barra de estado) pueden variar.

**Diferencias que conviene que el UX mire:**

- Los botones no llevan los íconos 🚗 y 👤 del wireframe.
- "Mis verificaciones" se ve como un botón secundario deshabilitado, no como un enlace.

## Avisos para el LEAD

1. **Renovación = actividad:** en el servidor, la renovación cuenta como actividad (ver "Cómo funciona la sesión"). El §3 dice "desde la última solicitud autenticada". Sin esto, la regla "no vence mientras haya interacción" no se puede cumplir en las pantallas que no llaman a la API. Si el LEAD lo lee distinto, que llegue como versión nueva del contrato.
2. **Arnés del TESTER:**
   - La API ahora necesita `auth` sano y la migración `0002`. `python -m app.cargar_usuarios` la aplica.
   - `App.tsx` ya no muestra `PantallaEstado`. El archivo sigue existiendo, igual que antes.
   - Las pruebas de Jest que monten `App.tsx` necesitan un `expo-secure-store` simulado.
3. **Despliegue (pendiente, fuera de este ciclo):** en Supabase en la nube, `AUTH_URL` es `https://<proyecto>.supabase.co/auth/v1` y `AUTH_APIKEY` es la clave pública. El alta de usuarios con `AUTH_JWT_SECRETO` supone el secreto JWT del proyecto.
