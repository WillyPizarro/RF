# Informe DEV — HU-03 + HU-07 (consulta de placa y bitácora)

**Documentos de trabajo:** `docs/contratos/CONTRATO-HU-03.md` **v3** y `docs/contratos/CONTRATO-HU-07.md` **v2** · **Encargo:** `docs/contratos/ENCARGO-HU-03-07.md` con M-1 · **Rama:** `hu-03` · **Fecha:** 2026-11-19
**Commits:** `27d0b30` (API, infra, OpenAPI y tipos) y `95073db` (app).

No leí ni ejecuté las pruebas del TESTER.

## Cómo se arranca

```
docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env up -d --build
docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env exec api python -m app.cargar_usuarios
```

- **Migraciones automáticas:** al arrancar, el contenedor `api` corre `python -m app.migrar` antes de uvicorn.
  - Aplica `alembic upgrade head` como dueño de las tablas, con `MIGRACION_DATABASE_URL`.
  - Si `API_APP_CLAVE` tiene valor, le da login a `api_app` con esa clave.
- **URL local del proxy:** **`https://localhost:8443`**, con `PROXY_PUERTO_HTTP=8080` y `PROXY_PUERTO_HTTPS=8443` en `infra/.env`.
  - Comprobado: `GET https://localhost:8443/v1/salud` → `{"estado":"ok","bd":"ok","simuladores":"ok",…}`.
  - Sin esas variables se publican 80 y 443 (el VPS).
- **Redirección por HTTP:** `http://localhost:8080` redirige a `https://localhost/…`, sin el puerto. Caddy arma la redirección con el puerto interno 443. Por eso las pruebas tienen que usar la URL HTTPS directa.
- **Migración sobre una base vacía (CONTRATO-HU-07 v2):** `docker compose … run --rm api alembic upgrade head`, con `MIGRACION_DATABASE_URL` apuntando a esa base.

### Variables nuevas en `infra/.env`

Están en `infra/.env.example` sin claves. Mi `infra/.env` local ya las tiene; los valores no se imprimieron.

| Variable | Para qué |
|---|---|
| `DATABASE_URL` | **Ahora usa el rol `api_app`.** Es la conexión de la API en marcha (ADR-0005 §1) |
| `API_APP_CLAVE` | Clave de `api_app`. La fija `app.migrar` |
| `MIGRACION_DATABASE_URL` | Rol dueño (`POSTGRES_USER`). Solo para migraciones y la carga de usuarios (HU-07 v2) |
| `PROXY_PUERTO_HTTP`, `PROXY_PUERTO_HTTPS` | Puertos que publica el proxy. Por defecto 80 y 443 |
| `PLACA_FORMATO_REGEX`, `PLACA_FORMATO_DESCRIPCION` | Formato de placa. Provisional (PA #20). Van entre comillas simples para que compose no interprete el `$` |

## Qué construí

### Base de datos: migración `0003_placa_bitacora_blindada`

- **`motivo_catalogo`:** columnas `codigo`, `descripcion`, `activo` y `orden`, con los 5 motivos iniciales. "otro" va siempre al final.
- **`consulta`:** las columnas del modelo de datos del TDD más `es_sintetico`.
- **`bitacora`:**
  - **Trigger:** `bitacora_solo_insercion()` lanza `bitacora es de solo insercion (<op> rechazado)` y se dispara en `BEFORE UPDATE OR DELETE` (por fila) y en `BEFORE TRUNCATE` (por sentencia). Aplica a cualquier rol, incluido el dueño.
  - **Índices** para el orden y para el filtro por tipo.
- **Rol `api_app`:** la migración lo crea sin login si no existe, así sirve también para el Supabase del VPS.
  - Sobre `bitacora` solo tiene `INSERT` y `SELECT`.
  - Sobre `control_acceso`, `sesion` y `consulta` tiene `SELECT`, `INSERT` y `UPDATE`.
  - Sobre `usuario_perfil`, `motivo_catalogo` y `alembic_version` solo tiene `SELECT`.
  - La clave viaja como parámetro: nunca aparece en el texto de una sentencia ni en los logs.

### API (`services/api/`)

- **`app/fuente_placas.py` (`FuentePlacas`):** el adaptador de la fuente de placas.
  - **Configuración:** URL y timeout salen de `FUENTE_PLACAS_URL` y `FUENTE_TIMEOUT_S`.
  - **Validación:** cada respuesta se valida con modelos Pydantic estrictos alineados con `placas.yaml` (`Vehiculo`, `Requisitoria` y `Error`).
  - **Caída, 5xx o timeout:** un solo reintento tras unos 200 ms; si vuelve a fallar, `FuenteNoDisponible`.
  - **Respuesta fuera de contrato:** `FuenteRespuestaInvalida`, sin reintento.
  - **404 `PLACA_NO_REGISTRADA`** → `placa_no_registrada`.
- **`app/placas.py`:**
  - **`GET /v1/motivos`** (solo agente): `{motivos, formato_placa: {regex, descripcion}}` (v3).
  - **`POST /v1/consultas/placa`** (solo agente):
    - Normaliza la placa: recorta los espacios y la pasa a mayúsculas.
    - Valida en este orden: motivo, formato y fuente. Los `422` no consultan la fuente ni dejan evento.
    - La fila de `consulta` y su evento (`CONSULTA_PLACA` o `ERROR_FUENTE`) se escriben en una sola transacción. Si la escritura falla: `503 SERVICIO_NO_DISPONIBLE`, sin resultado.
    - El campo `motivo` de la bitácora lleva el código, o `otro: <texto>` si el motivo es "Otro".
- **`app/consulta_bitacora.py`:**
  - **`GET /v1/bitacora`** (solo supervisor):
    - Filtros, `limite` de 1 a 100 (50 por defecto) y orden `ocurrido_en DESC, id DESC`.
    - **Cursor:** opaco, en base64url con el último `(ocurrido_en, id)`. Al ser keyset, los registros nuevos no corren las páginas.
    - **Fechas sin zona horaria:** se toman como UTC.
    - **Evento `CONSULTA_BITACORA`:** se escribe en la misma transacción, después de leer, así que no aparece en su propia respuesta. Lleva en `parametros` los filtros usados, el `limite` y `pagina_siguiente` cuando hubo cursor.
  - **405 en las rutas de modificación:** existe una ruta `GET /v1/bitacora/{registro}` oculta del OpenAPI, que responde `404`. Sirve para que `PUT`, `PATCH`, `DELETE` y `POST` sobre `/v1/bitacora/<id>` den `405 METODO_NO_PERMITIDO` en vez de `404`.
- **`app/bitacora.py`:** `registrar` acepta además `motivo`, `resultado` y `consulta_id`.
- **`app/migrar.py`:** nuevo (descrito arriba). `app/cargar_usuarios.py` lo reutiliza y escribe los perfiles como dueño, porque `api_app` solo los lee. `alembic/env.py` usa `MIGRACION_DATABASE_URL`, o `DATABASE_URL` si falta.
- **Regenerados:** `contratos/api/openapi.json` y `apps/movil/src/api/esquema.ts`. Las rutas son `/v1/salud`, `/v1/auth/login`, `/v1/auth/refresh`, `/v1/auth/logout`, `/v1/me`, `/v1/motivos`, `/v1/consultas/placa` y `/v1/bitacora`.

### App (`apps/movil/`)

- **HOME-01:**
  - **"Consultar placa"** queda habilitada, con el ícono 🚗 oculto para el lector de pantalla (`Boton` acepta `icono`). El texto no cambió.
  - **"Bitácora"** del supervisor queda habilitada.
  - **Siguen deshabilitadas:** "Verificar rostro", "Mis verificaciones" y "Pendientes de revisión".
- **`PantallaPlaca.tsx` (PLA-01 a PLA-08):**
  - **Datos de partida:** el catálogo y el formato salen de `GET /v1/motivos`.
  - **Motivo:** se elige en una lista de opciones visibles (rol `radio`). "Describa el motivo *" aparece solo con "Otro".
  - **PLA-02 y PLA-03:** se validan en la app con la regex y la descripción de la API, y no envían nada. Si faltan las dos cosas, se muestran los dos mensajes. El foco va al motivo.
  - **PLA-04:** "Consultando…" con "Placa ZZA-101", y el botón desactivado.
  - **Resultados:** PLA-05 (rojo), PLA-06 (gris neutro) y PLA-08 (gris azulado). PLA-08 lleva "Volver", que regresa al formulario con la placa y el motivo cargados. Los otros dos llevan "Nueva consulta".
  - **PLA-07:** cubre `503`, `502`, la falla de red y cualquier respuesta inesperada. Tiene ícono ⚠ en ámbar. "Reintentar" reenvía con la misma placa y el mismo motivo, y "Volver" lleva al formulario con lo escrito.
  - **422 de la API:** se muestra el `mensaje` de la API en el campo correspondiente.
  - **`403`:** pasa a ERR-01 por `llamarAutenticado`.
  - **Sin persistencia:** el resultado vive solo en el estado de la pantalla.
- **`PantallaBitacora.tsx` (BIT-01 y BIT-02):**
  - **Tarjetas:** `dd/mm hh:mm · usuario`, o "sistema" si no hay usuario; la etiqueta del tipo; la placa si existe; el resultado; y "SINTÉTICO".
  - **Filtros** con la marca "PA 24", plegados por defecto. Ver la nota para el UX.
  - **Paginación:** "Cargar más".
  - **Error:** "No se pudo cargar la bitácora; intente nuevamente" con "Reintentar", nunca una lista vacía. La lista vacía real muestra su propio texto.
  - **BIT-02:** "Registro #<id>", con el 🔒 oculto para el lector y "Registro de solo lectura". Muestra los campos; "ID de captura" y "Score" solo si existen. Termina con "Origen: datos sintéticos".
- **"Atrás":** cada pantalla maneja el suyo.
  - Del formulario de placa vuelve al inicio.
  - De un resultado o de PLA-07 vuelve al formulario.
  - Del detalle de la bitácora vuelve a la lista, y de la lista al inicio.

## Lo que verifiqué

**API:** en el contenedor, con `scratchpad/verificar_placa.py`, un script mío que no es prueba del TESTER. Todo pasó.

- **`api_app`:**
  - La API se conecta como `api_app` (`current_user` de `DATABASE_URL`).
  - En `information_schema`, sobre `bitacora` tiene solo `INSERT` y `SELECT`.
- **Motivos:**
  - La respuesta es exacta, con `formato_placa`.
  - Agregar o desactivar un motivo cambia la lista, y "otro" sigue al final.
  - Revisor y supervisor reciben `403` + `ACCESO_DENEGADO`. Sin token, `401`.
- **Resultados:**
  - `ZZA-101`, `ZZB-201`, `ZZZ-999` y `" zza-101 "` dan los resultados esperados, cada uno con un solo evento `CONSULTA_PLACA` completo y su fila en `consulta`.
  - "Otro" guarda su texto recortado.
- **Rechazos:**
  - `422 MOTIVO_REQUERIDO` en todas sus variantes, con los mensajes exactos.
  - `422 PLACA_FORMATO_INVALIDO` con `HOLA MUNDO`, `ABC123` y `AB-1234`.
  - Si faltan el motivo y el formato, responde primero `MOTIVO_REQUERIDO`.
  - `422 SOLICITUD_INVALIDA` sin `placa` o con un JSON roto.
  - Ningún rechazo deja evento.
  - Revisor y supervisor reciben `403`.
- **Fuente:**
  - `error_500`: `503 FUENTE_NO_DISPONIBLE` en 0,22 s; la espera del reintento muestra que hubo 2 llamadas.
  - `latencia` de 5000 ms: `503` en 6,23 s, dentro del límite de 7 s.
  - `malformada`: `502 FUENTE_RESPUESTA_INVALIDA` en 0,02 s, sin reintento.
  - Cada error deja `ERROR_FUENTE` con todos sus campos y `consulta` en `error`.
  - Al volver al modo `normal`, la consulta funciona.
- **Solo inserción:**
  - `UPDATE`, `DELETE` y `TRUNCATE` fallan como `api_app` y como dueño.
  - Como dueño, el mensaje contiene `bitacora es de solo insercion`.
  - El registro queda igual.
- **Fail-closed:** con `REVOKE INSERT ON bitacora FROM api_app`:
  - La consulta responde `503 SERVICIO_NO_DISPONIBLE`, sin resultado y sin fila en `consulta`.
  - El login responde `503`, sin tokens.
  - Al restaurar el permiso, todo vuelve a funcionar.
- **`GET /v1/bitacora`:**
  - La forma de la respuesta es la del contrato, en orden descendente, y deja `CONSULTA_BITACORA` con sus filtros.
  - Los filtros por usuario, tipo, resultado y rango de fechas funcionan.
  - Paginación con `limite=3`: recorrió todos los registros sin repetir ninguno, aunque entró uno nuevo a mitad del recorrido.
  - Responde `422` ante una fecha mal formada, un tipo desconocido, `limite` 0 o 101, y un cursor inválido.
  - Agente y revisor reciben `403`.
  - `PUT`, `PATCH`, `DELETE` y `POST` sobre `/v1/bitacora` y `/v1/bitacora/<id>` dan `405`.
  - Una lista vacía da `{"registros":[],"siguiente_cursor":null}`.
- **Contenido de la bitácora:**
  - Ningún registro contiene la clave ni cadenas largas tipo base64.
  - Están presentes los 9 tipos de evento de la iteración.
- **Base vacía:** `run --rm api alembic upgrade head`, con `MIGRACION_DATABASE_URL` hacia una base nueva, aplicó `0001` a `0003`. Dejó los 2 triggers, `INSERT,SELECT` para `api_app` y los 5 motivos.
- **`app.cargar_usuarios`:** sigue funcionando.

**App:** con un Jest temporal mío, ya borrado. Pasaron 18 casos:

- HOME-01 con 🚗 oculto para el lector.
- PLA-02 y PLA-03, incluido "Otro" corto, con 0 envíos.
- PLA-04: solo 1 envío aunque se toque "Consultar" dos veces.
- PLA-05, PLA-06 y PLA-08: texto, "Motivo:", "Consultado:" y ningún ✓.
- PLA-08 → "Volver" conserva la placa y el motivo.
- PLA-07 con `503`, `502`, falla de red y una respuesta `200` rara. "Reintentar" reenvía lo mismo y "Volver" lo conserva.
- Un `422` de la API muestra su mensaje.
- Una regex y una descripción distintas en `/v1/motivos` cambian la validación.
- `403` → ERR-01 → "Volver al inicio".
- "Atrás" desde el formulario lleva al inicio.
- BIT-01: lista, "Cargar más", BIT-02 sin "ID de captura" ni "Score", error y "Reintentar", lista vacía, y filtros en la URL.
- El revisor sigue sin opciones nuevas.

`tsc` no da errores. La palabra prohibida tiene 0 apariciones en `services/api/app`, `contratos/api`, `apps/movil/src` e `infra`.

**NO VERIFICADO:**

- **§4 de HU-03 (mock de Prism desde `placas.yaml`):** levantar `stoplight/prism` (por `docker run`) no fue autorizado en este equipo, igual que `npx` en HU-08.
  - El adaptador acepta los ejemplos del yaml: el `200` de `con_requisitoria` cumple `Vehiculo`.
  - Cambiar `FUENTE_PLACAS_URL` no requiere tocar código.
- **Emulador:** no hay SDK de Android. Las capturas son de Jest, como en HU-01/02.

## Capturas para el UX

Están en `C:\Willy\Trabajo\MININTER\Movil_Buscador_capturas\HU-03-07\`, fuera del repositorio, en PNG y HTML a 390 px. Salen del árbol de Jest con el mismo método que en HU-01/02.

| Archivo | Pantalla |
|---|---|
| `HOME-01` | Inicio del agente: "Consultar placa" habilitada con 🚗 |
| `PLA-01` | Formulario |
| `PLA-02-03` | Sin motivo y con formato inválido a la vez |
| `PLA-02-otro` | "Otro" con menos de 10 caracteres |
| `PLA-04` | Consultando |
| `PLA-05` | Tiene requisitoria |
| `PLA-06` | Sin requisitoria registrada |
| `PLA-08` | Placa no registrada |
| `PLA-07` | No se pudo completar la consulta |
| `ERR-01` | `403` desde la consulta |
| `BIT-01` | Lista, con los filtros plegados |
| `BIT-01-filtros` | Lista con los filtros desplegados |
| `BIT-01-vacio` | Lista vacía |
| `BIT-01-error` | Error al cargar |
| `BIT-02` | Detalle de un `ERROR_FUENTE` |

## Avisos para el LEAD

1. **Arnés del TESTER:** `DATABASE_URL` ahora usa `api_app`, como pide CONTRATO-HU-07 §1.
   - Lo que requiera escribir como dueño (por ejemplo `REVOKE` o `GRANT`, o cambiar `motivo_catalogo` o `control_acceso`) usa `MIGRACION_DATABASE_URL`, que también está en el entorno del contenedor `api`.
   - `api_app` no tiene `DELETE` en ninguna tabla.
2. **Decisiones de interfaz para el UX** (no cambian ningún texto del contrato):
   - **Selector de motivo:** el motivo se elige en una lista de opciones siempre visible, no en un desplegable "Seleccione ▾". Así se elige con un toque, con guantes.
   - **Filtros de BIT-01:** van plegados ("Filtros ▾" con "PA 24"), como en el wireframe. Si no, sus etiquetas repetirían las de las tarjetas ("Consulta de placa", "Tiene requisitoria"…).
   - **Fechas de los filtros:** se escriben como `dd/mm/aaaa`. "Hasta" incluye el día indicado.
   - **Catálogo que no carga:** si `GET /v1/motivos` falla, PLA-01 muestra el mensaje de PLA-07 con "Reintentar" y "Volver". El contrato no define este caso.
   - **Motivo en BIT-02:** se muestra legible: `control_vehicular` → "Control vehicular" y `otro: …` → "Otro: …".
3. **Despliegue** (ya anotado en `PENDIENTES.md`): en el Supabase del VPS, la misma migración crea `api_app`. Allí hay que definir `API_APP_CLAVE` y `MIGRACION_DATABASE_URL` (rol `postgres`), y apuntar `DATABASE_URL` a `api_app`.
