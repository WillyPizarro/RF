# ADR 0007: Contrato entre la app y la API, REST versionado con OpenAPI generado

## Estado

Aceptado (2026-11-18)

## Contexto

- ADR-0001: la app solo habla con la API. ADR-0002: la app es TypeScript (Expo). La API es Python (FastAPI).
- El TESTER y el DEV trabajan sin verse, contra un contrato observable (skill `escribir-contrato` del equipo). Necesitan un contrato que se pueda leer y validar con herramientas.
- Son unas 10 operaciones fijas (login, placa, rostro, revisión, bitácora). Cada una se controla por rol y queda en la bitácora.

## Decisión

**REST/JSON sobre HTTPS, versionado en la ruta (`/v1`).** La API es la dueña del contrato. FastAPI genera el **OpenAPI** desde los modelos Pydantic, y ese archivo se publica en el repositorio (`contratos/api/openapi.json`) en cada cambio. La app genera sus tipos TypeScript desde ese archivo (`openapi-typescript` o equivalente) y no se escriben tipos a mano.

Catálogo inicial (el detalle lo fija el OpenAPI):

| Método y ruta | Rol | HU |
|---|---|---|
| `POST /v1/auth/login`, `/v1/auth/refresh`, `/v1/auth/logout` | público / autenticado | HU-01 |
| `GET /v1/me` (perfil y rol, para armar el menú) | todos | HU-02 |
| `POST /v1/consultas/placa` (placa, motivo) | agente | HU-03, HU-04 |
| `POST /v1/consultas/rostro` (imagen multipart, motivo) | agente | HU-05 |
| `GET /v1/consultas/{id}` (estado, incluido el resultado de la revisión) | agente (solo las propias) | HU-05, HU-06 |
| `GET /v1/revisiones?estado=pendiente`, `GET /v1/revisiones/{id}` | revisor | HU-06 |
| `POST /v1/revisiones/{id}/decision` (decisión, motivo) | revisor | HU-06 |
| `GET /v1/bitacora?usuario&desde&hasta&tipo&resultado&cursor` | supervisor | HU-07 |

Convenciones:
- Los errores siguen un formato único `{codigo, mensaje, id_traza}`, con códigos estables (`MOTIVO_REQUERIDO`, `PLACA_FORMATO_INVALIDO`, `FUENTE_NO_DISPONIBLE`, `CAPTURA_RECHAZADA`, `SIN_PERMISO`, ...).
- Las bandas biométricas son valores de enumeración (`candidato`, `no_concluyente`, `sin_coincidencia`, `captura_rechazada`). Ningún campo ni valor del contrato contiene "identificado".
- La validación del motivo y del formato de placa vive en la API. La app también valida, pero solo para dar una mejor experiencia.

## Alternativas consideradas

- **REST con tipos escritos a mano en la app.** No requería herramientas extra. Se descartó porque el contrato y la app se desincronizan sin que nadie lo detecte hasta que algo falla en ejecución.
- **GraphQL.** Ofrecía un esquema único y consultas flexibles. Se descartó porque sobra para unas 10 operaciones fijas y complica el control por rol y la bitácora por operación.

## Consecuencias

- El TESTER puede escribir pruebas de contrato contra el OpenAPI antes de que exista la app.
- Un cambio que rompe el contrato se detecta en tiempo de compilación en la app, porque los tipos se regeneran.
- **Costo:** hay que regenerar los tipos y versionar el OpenAPI en cada cambio. Si alguien lo olvida, la verificación de CI debe fallar (el LEAD lo define en el Sprint 0).
- **Costo:** subir la imagen del rostro con multipart añade latencia frente a procesarla en el dispositivo. Es inevitable porque la comparación ocurre en el backend (ADR-0004).
