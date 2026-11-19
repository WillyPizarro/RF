# Informe TESTER — Sprint 0 (esqueleto)

**Documento de trabajo:** `SPRINT0.md` aprobado (df0d7a3) + M-1 (b6238f9) + M-2 (f929699)
**Rama:** `sprint-0` · **Fecha:** 2026-11-18 · **Rol:** TESTER

Pruebas de **caja negra** contra la interfaz observable: HTTP por el proxy (`https://localhost`), HTTP dentro de la red de Docker (`http://api:8000`, `http://simuladores:8001`), la CLI de `docker compose` y el render de `PantallaEstado`. No se leyó ni se abrió ninguna ruta del DEV.

## Estado de ejecución

**Ninguna prueba se ejecutó contra el sistema todavía: todas están `NO EJECUTADA`.** Motivos:
- Por el playbook, la suite completa corre una sola vez, sobre el commit definitivo, con la orden expresa del LEAD.
- Las pruebas de los criterios 3 y 4 **detienen** `db` y `simuladores`. Corridas en paralelo con el trabajo del DEV, lo interrumpirían.

Lo único verificado: las 43 pruebas de la API y las 3 de los simuladores se recolectan sin errores con pytest 9 en el anfitrión. Sin `--integracion` quedan omitidas, como está previsto.

## Cómo se corren

| Suite | Dónde | Comando |
|---|---|---|
| API (criterios 2, 3, 4, 5, 7, 8, 9) | anfitrión, sistema arrancado, raíz del repo | `pytest services/api/tests --integracion` |
| Simuladores, desde el anfitrión | anfitrión, sistema arrancado | `pytest services/simuladores/tests --integracion` |
| Simuladores, dentro de la red (criterio 11) | contenedor | `docker compose -f infra/docker-compose.yml run --rm simuladores pytest` |
| API en contenedor (criterio 11) | contenedor | `docker compose -f infra/docker-compose.yml run --rm api pytest` → todas omitidas (necesitan la CLI de docker del anfitrión); termina con código 0 |
| App (criterio 10) | `apps/movil` | `npm test` |

Requisitos en el anfitrión: Python ≥ 3.10 con `pytest`, sin otras dependencias, y la CLI de Docker. Las dos suites de pytest se corren **por separado**, porque cada carpeta tiene su propio `conftest.py`. Opciones: `--url-base` (por defecto `https://localhost`) y `--espera-max` (por defecto 90 s). Los criterios 3 y 4 llevan el marcador `disruptiva`; para omitirlos, agregar `-m "not disruptiva"`.

## Trazabilidad: criterio de la DoD → prueba

| # | Criterio | Prueba / verificación | Estado |
|---|---|---|---|
| 1 | Arranca con un comando, 3 servicios sanos | Por comando: `docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --build` y luego `docker compose -f infra/docker-compose.yml ps` (`api`, `simuladores` y `proxy` en `running`/`healthy`) | NO VERIFICADO (por comando) |
| 2 | Salud por proxy con TLS | `services/api/tests/test_salud.py`: 200, cuerpo exacto (4 claves, `ok`, `version` semver), JSON, `X-Id-Traza` | NO EJECUTADA |
| 3 | API ↔ Postgres | `test_dependencias.py` `[criterio3-bd]`: `db` detenido → 503 con la misma forma, `estado`/`bd` = `"error"`, `simuladores` = `"ok"`, sin formato de error estándar, con `X-Id-Traza` (M-1 A); `db` arriba → 200 | NO EJECUTADA |
| 4 | API ↔ simuladores por red interna | `test_dependencias.py` `[criterio4-simuladores]` (igual que el 3); `test_red.py::test_api_alcanza_simuladores_por_la_red_interna` | NO EJECUTADA |
| 5 | Simuladores no accesibles desde fuera | `test_red.py`: `config` sin puertos para `simuladores`, `api` y `db`; `proxy` publica solo `{80, 443}`; ningún otro servicio publica; `/salud` no alcanzable por el proxy | NO EJECUTADA |
| 6 | Migraciones corren | Por comando: `docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head`, código 0 sobre una base vacía | NO VERIFICADO (por comando) |
| 7 | Formato de error e id de traza | `test_errores.py`: 3 rutas inexistentes bajo `/v1` → 404 `NO_ENCONTRADO`; claves exactas `{codigo, mensaje, id_traza}`; `id_traza` == `X-Id-Traza`; un `id_traza` distinto por solicitud (ADR-0014); sin la palabra prohibida | NO EJECUTADA |
| 7 (fuera del criterio) | 405 de M-1 B | `test_errores.py` `[405-post-salud]`: `POST /v1/salud` → 405 `METODO_NO_PERMITIDO` con formato estándar. Se prueba porque M-1 B sigue vigente y el caso es observable sin agregar rutas | NO EJECUTADA |
| 7 (422) | 422 `SOLICITUD_INVALIDA` | Sin prueba: por M-2 se escribe con HU-01 | Fuera de alcance (M-2) |
| 8 | Logs JSON sin secretos | `test_logs.py`: la solicitud (200 y 404) deja una línea JSON del log de `api` con su `id_traza`; los logs de `api` y `simuladores` no contienen los valores secretos de `infra/.env` (variables con PASSWORD, SECRET, KEY, TOKEN, PASS o JWT en el nombre, `DATABASE_URL` y su contraseña; se ignoran los valores de menos de 6 caracteres) | NO EJECUTADA |
| 9 | OpenAPI publicado y al día | `test_contrato_openapi.py`: `contratos/api/openapi.json` == `http://api:8000/openapi.json`, pedido con `docker compose exec api` (M-1 G); el proxy no expone `/openapi.json`; el contrato declara `GET /v1/salud` y no tiene rutas de negocio. Además, por comando: `npm run generar:api` en `apps/movil` | NO EJECUTADA |
| 10 | App compila y usa la URL configurada | `apps/movil/__tests__/PantallaEstado.test.tsx`: 200 → "Conectado"; 503, 500, 404 y error de red → "Sin conexión con el servidor" (M-1 F); la única URL llamada es `EXPO_PUBLIC_API_URL + '/v1/salud'` (M-1 D); un error no muestra "sin requisitoria", "sin coincidencia" ni la palabra prohibida. Además, por comando: `npx tsc --noEmit` | NO EJECUTADA |
| 11 | Runners se ejecutan | Por comando (ver "Cómo se corren") | NO VERIFICADO (por comando) |
| 12 | Sin secretos en el repo | Por comando: `gitleaks detect` sin hallazgos; existe `infra/.env.example`; `infra/.env` está en `.gitignore` | NO VERIFICADO (por comando) |
| 13 | ADRs transversales | Revisión del LEAD | Fuera del TESTER |
| 14 | Cero lógica de negocio | Revisión humana. Apoyo automático: `test_contrato_sin_rutas_de_negocio` y `test_sin_endpoints_de_fuentes` (simuladores) | Revisión humana |
| 15 | Android de referencia | Revisión humana (cuenta EAS) | NO VERIFICADO |

## Simuladores

`services/simuladores/tests/test_salud_simuladores.py`: `GET /salud` → 200, JSON y cuerpo exacto `{"estado": "ok"}`. Además, `/placas`, `/requisitorias-personas` y `/galeria` → 404 (SPRINT0.md §6, "NO se crea").

## Decisiones de arnés (no de comportamiento) que el LEAD debe conocer

1. **TLS sin verificar.** El cliente de pruebas no verifica el certificado, porque Caddy usa una CA local. Se verifica que el esquema sea `https`.
2. **QueryClientProvider en la prueba Jest.** `PantallaEstado` se envuelve en un `QueryClientProvider` sin opciones, por si usa TanStack Query (ADR-0013). Si la pantalla no lo usa, no tiene efecto. Cuando ve un error, la prueba espera hasta 20 s, por los reintentos por defecto de TanStack Query.
3. **`EXPO_PUBLIC_API_URL`.** La prueba la fija en `process.env` antes de cargar la pantalla. Si la configuración de Jest del DEV inyecta las `EXPO_PUBLIC_*` en tiempo de compilación, la prueba de la URL fallará. En ese caso, el veredicto debe aclarar si se apartó el código o la prueba.
4. **`run --rm simuladores pytest`.** El GET va directo a `http://simuladores:8001`. Si el nombre `simuladores` no resuelve, la prueba se omite con su motivo. La versión que corre desde el anfitrión (`--integracion`) no depende de cómo resuelva el contenedor de `run`.

## Riesgos y notas

- Los criterios 3 y 4 detienen servicios. El fixture los vuelve a levantar aunque la prueba falle; si el proceso se corta a la mitad, hay que correr `docker compose -f infra/docker-compose.yml start db simuladores`.
- El criterio 8 necesita `infra/.env` con `DATABASE_URL`. Si no existe, la prueba falla con su motivo y no se omite.

## Archivos entregados

- `services/api/tests/`: `conftest.py`, `test_salud.py`, `test_errores.py`, `test_dependencias.py`, `test_red.py`, `test_logs.py`, `test_contrato_openapi.py`
- `services/simuladores/tests/`: `conftest.py`, `test_salud_simuladores.py`
- `apps/movil/__tests__/PantallaEstado.test.tsx`
- `informes/TESTER-SPRINT0.md`
