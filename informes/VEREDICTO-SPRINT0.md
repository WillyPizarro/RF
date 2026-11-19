# Veredicto — Sprint 0 (vuelta 1)

**Fecha:** 2026-11-19 · **LEAD** · Skill `veredicto` v2
**Spec:** `SPRINT0.md` con M-1 y M-2 (último cambio de spec: commit `f929699`)
**Código verificado:** rama `sprint-0`, commit `119ec2a` (árbol limpio)
**Entregas:** TESTER `0ff3428` (`informes/TESTER-SPRINT0.md`) · DEV `2d9c0c7` + `119ec2a` (`informes/DEV-SPRINT0.md`)

**Resultado: 🔴 NO CUMPLE TODAVÍA.** 10 criterios en verde, 2 en rojo (los dos se devuelven al TESTER) y 2 `NO VERIFICADO` por entorno. Revisión humana pendiente en el criterio 14.

## 1. Propiedad de rutas

`git log main..sprint-0 --name-only`: todos los commits tienen prefijo y cada archivo está dentro de las rutas de su rol según `AGENTS.md`.
- `[DEV]`: `apps/movil/` (sin `__tests__/`), `services/*/` (sin `tests/`), `infra/`, `contratos/`, `README.md`, `.gitignore` (solo agregó `*.egg-info/`; no quitó nada) e `informes/DEV-SPRINT0.md`.
- `[TESTER]`: `services/api/tests/`, `services/simuladores/tests/`, `apps/movil/__tests__/` e `informes/TESTER-SPRINT0.md`.
- `[ARCH]`: solo `docs/arch/`. `[LEAD]`: `SPRINT0.md`, `AGENTS.md` y `docs/contratos/`.

**Sin hallazgos de rutas.**

## 2. Misma versión de la spec

Los dos informes citan M-1 y M-2, y ambos commits son posteriores a `f929699`. **Válido.**

## 3. Resultado por criterio de la DoD

| # | Criterio | Evidencia | Resultado |
|---|---|---|---|
| 1 | Arranca con un solo comando | Comando literal: `api`, `db` y `simuladores` sanos; `proxy` falla con `bind 0.0.0.0:80 … forbidden`. El puerto 80 está reservado por Windows en esta máquina (proceso System, PID 4) | `NO VERIFICADO` (entorno) |
| 2 | Salud por proxy con TLS | `test_salud.py` (4 pruebas) en verde vía `https://localhost:443`. Para levantar el proxy se usó un override fuera del repositorio (80→8080); el 443 no cambió | 🟢 |
| 3 | Conexión a Postgres | `test_dependencias.py[criterio3-bd]` (4 pruebas): 503 con la forma de M-1 A y vuelta a 200 | 🟢 |
| 4 | Alcanza a los simuladores | `test_dependencias.py[criterio4-simuladores]` (4) + `test_red.py::test_api_alcanza_simuladores_por_la_red_interna` | 🟢 |
| 5 | Simuladores no accesibles desde fuera | `test_red.py` (7 pruebas): solo el proxy publica 80 y 443; `api`, `simuladores` y `db` no publican puertos | 🟢 |
| 6 | Migraciones | `docker compose … run --rm api alembic upgrade head` → código 0; `0001_inicial` sin tablas | 🟢 |
| 7 | Formato de error e id de traza | `test_errores.py` (14 pruebas): 404 `NO_ENCONTRADO` (3 rutas), 405 `METODO_NO_PERMITIDO`, `id_traza` igual a la cabecera, sin la palabra prohibida | 🟢 |
| 8 | Logs JSON sin secretos | `test_logs.py` (5 pruebas), sobre `api` y `simuladores` | 🟢 |
| 9 | OpenAPI publicado y al día | `test_contrato_openapi.py` (4 pruebas), incluida "el proxy no expone /openapi.json"; `npm run generar:api` sin diferencias en el árbol | 🟢 |
| 10 | La app compila y usa la URL configurada | `npx tsc --noEmit` → exit 2 (TS2339 en `__tests__/PantallaEstado.test.tsx:139`); Jest 0/10 | 🔴 → TESTER |
| 11 | Los runners se ejecutan | `run --rm api pytest` y `run --rm simuladores pytest` → `IndexError` al cargar `conftest.py`; `npm test` 0/10 | 🔴 → TESTER |
| 12 | Sin secretos en el repositorio | gitleaks (imagen oficial): 10 commits, "no leaks found"; `infra/.env.example` sin valores reales; `infra/.env` ignorado | 🟢 |
| 13 | Respeta los ADRs transversales | Ver sección 6 | 🟢 |
| 14 | Cero lógica de negocio | Revisión LEAD: sin tablas, endpoints, pantallas ni simuladores de negocio (búsqueda de placa, rostro, requisitoria, bitácora, login y revisión en `services/*/app`, `apps/movil/src` y las migraciones: sin coincidencias) | 🟢 LEAD · confirmado por el humano (2026-11-19) |
| 15 | La app en el Android de referencia | Sin cuenta EAS ni APK todavía | `NO VERIFICADO` |

Pruebas del TESTER ejecutadas: API 43/43 🟢 (51 s) · simuladores desde el anfitrión 3/3 🟢 · Jest 0/10 🔴 · runners en contenedor 🔴.

## 4. Arbitrajes

### 🔴 Criterio 11 (pytest en contenedor) — **se apartó la prueba** → TESTER, vuelta 1
- **Spec:** el criterio 11 exige que `docker compose -f infra/docker-compose.yml run --rm api pytest` y `… run --rm simuladores pytest` terminen con código 0.
- **Prueba:** `services/api/tests/conftest.py:32` y el de los simuladores calculan `Path(__file__).resolve().parents[3]` al importarse. Dentro del contenedor, el archivo está en `/app/tests/conftest.py`, así que esa ruta no existe y salta `IndexError: 3` antes de llegar a la omisión que el propio informe del TESTER anuncia ("sin `--integracion` quedan omitidas").
- **Código:** el Dockerfile copia el servicio a `/app`, como corresponde. No hay nada que corregir del lado del DEV.
- **Caso para el TESTER:** el arnés tiene que cargar en el contenedor sin la estructura del repositorio y terminar con código 0 (omitiendo con su motivo lo que necesita `--integracion`).

### 🔴 Criterio 10 (`tsc` y Jest) — **se apartó la prueba** → TESTER, vuelta 1
- **Spec:** el criterio 10 exige `npx tsc --noEmit` sin errores y la prueba Jest sobre `PantallaEstado` de M-1 D y M-1 F.
- **Prueba:**
  1. Carga el componente con `jest.isolateModules` + `require` (`PantallaEstado.test.tsx:56-58`). Eso crea un registro de módulos aparte, con **otra copia de React** distinta de la que usa `@testing-library/react-native`. Resultado: `Cannot read properties of null (reading 'useState')` en las 10 pruebas.
  2. Usa la API síncrona de `render` (`const { toJSON } = renderizar()`, línea 139). En `@testing-library/react-native` 14.1.0, la versión del manifiesto, `render` es asíncrono: de ahí TS2339 y `screen … notImplemented`.
- **Código:** `PantallaEstado.tsx` cumple M-1 D: export por defecto, `fetch` global con `EXPO_PUBLIC_API_URL + '/v1/salud'`, `App.tsx` solo la muestra y los textos de M-1 F. La única salida de `tsc` está en `__tests__/`.
- **Caso para el TESTER:** la prueba debe escribirse para las versiones del manifiesto (RNTL 14, `render` asíncrono) y renderizar el mismo React del proyecto. `EXPO_PUBLIC_API_URL` se fija antes de cargar la pantalla **sin** aislar el registro de módulos (por ejemplo, un módulo de entorno en `__tests__/` que se importe primero). **Si eso no es posible porque Expo incrusta las `EXPO_PUBLIC_*` al compilar, no se fuerza: se reporta y el LEAD lo escala como "la spec no lo decía".**

### `NO VERIFICADO` — Criterio 1 (puerto 80)
No se apartó el código ni la prueba: Windows reserva el puerto 80 en esta máquina. **Decisión del humano:** liberar el puerto 80 (rango excluido o servicio de http.sys) y repetir el comando literal, o aceptar el criterio como `NO VERIFICADO` en esta máquina y verificarlo en el VPS.

### `NO VERIFICADO` — Criterio 15 (APK)
Pendiente de la cuenta EAS (pregunta 4 del Sprint 0). El humano puede aceptarlo como `NO VERIFICADO`.

## 5. Trampas y hallazgos

- **Independencia rota una vez (DEV), sin efecto en el resultado.** El DEV informa que corrió `npm test` y vio el resumen de las pruebas del TESTER (10/10 en rojo). Después cambió dos cosas: los tipos de Jest en `tsconfig` y un `QueryClient` sin reintentos que se vacía al desmontar. Revisé las dos: son configuración razonable (evitan que Jest se cuelgue 5 minutos y cumplen ADR-0013), no casos especiales para pasar una prueba. **No es trampa.** Se registra para el proceso: el DEV no debe ejecutar `npm test` mientras existan pruebas del TESTER que no ha visto.
- **Pruebas sin aserciones:** no se encontraron. Las 43 pruebas de la API afirman sobre los nombres exactos de la sección 5 y de M-1.
- **El 500 está cubierto en el código aunque no esté en la DoD:** `services/api/app/traza.py:26-29` convierte cualquier excepción no controlada en `ERROR_INTERNO` con el formato estándar (M-1 B).
- **Contenedor ajeno en el anfitrión:** `postgres-dev` publica 5432. No es de este proyecto; no interfiere (el `db` del proyecto no publica puertos).

## 6. ADRs transversales (criterio 13)

| ADR | Evidencia |
|---|---|
| 0001 | `infra/docker-compose.yml`: redes `interna` (api, simuladores, db) y `borde` (proxy, api); `apps/movil/src` no menciona Supabase ni los simuladores |
| 0007 | `services/api/app/errores.py:16-21` (códigos estables), `:25-30` (`{codigo, mensaje, id_traza}`); rutas bajo `/v1`; `contratos/api/openapi.json` publicado |
| 0009 | `infra/docker-compose.yml:47-52` (`caddy:2.10`, solo 80 y 443); `infra/Caddyfile` (solo `/v1/*`) |
| 0010 | `apps/movil/app.json:12` (configuración Android); `expo-dev-client` en `package.json:8` y `app.json:26` (dev build, parte de ADR-0002) |
| 0012 | `services/api/app/bd.py:6-14` (`create_async_engine`, asyncpg); `services/api/alembic/env.py:37`; migración `0001_inicial` |
| 0013 | `apps/movil/package.json:6,9,13` (TanStack Query, `expo-secure-store`, Zustand) |

## 7. Vueltas

| Desacuerdo | Rol | Vuelta |
|---|---|---|
| Criterio 11 — `conftest.py` no carga en el contenedor | TESTER | 1 |
| Criterio 10 — Jest con React duplicado y `render` síncrono | TESTER | 1 |

## 8. Próximos pasos

1. TESTER corrige los criterios 10 y 11 (vuelta 1), sin tocar el código del DEV.
2. Humano: decide el criterio 1 (liberar el puerto 80 o aceptar `NO VERIFICADO` aquí), acepta o no el 15 como `NO VERIFICADO`, y hace la revisión humana del 14.
3. LEAD: con la corrección del TESTER, una sola suite completa sobre el commit definitivo y, si todo está en verde, el PR (sin push a `main` ni merge).

## 9. Decisiones del humano (2026-11-19)

- Criterio 1: aceptado como `NO VERIFICADO` en esta máquina; se verifica con el comando literal en el VPS.
- Criterio 15: aceptado como `NO VERIFICADO` hasta tener la cuenta EAS.
- Criterio 14: confirmado (cero lógica de negocio).
