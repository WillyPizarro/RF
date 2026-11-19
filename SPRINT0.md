# SPRINT 0 — Movil Buscador (MININTER)

**Estado:** Pendiente de aprobación
**Fuentes:** `docs/arch/TECH-DESIGN.md`, `docs/arch/adrs/` (ADR-0001 a ADR-0014, aprobados el 2026-11-18)
**Preparado por:** LEAD, 2026-11-18 (skill `preparar-sprint0`)

Objetivo: un **esqueleto que funciona de punta a punta** (app → proxy → API → base de datos, y API → simuladores), con el runner de pruebas andando en cada pieza y **cero lógica de negocio**. Ninguna HU se construye en este sprint.

---

## 1. ADRs que aplican (transversales)

| ADR | Decisión | Por qué aplica ahora |
|---|---|---|
| ADR-0001 | La app solo habla con la API FastAPI; Supabase solo para Auth y Postgres | Define los componentes y quién habla con quién: sin esto no existe el esqueleto |
| ADR-0007 | REST/JSON versionado en `/v1`; OpenAPI generado por FastAPI y publicado en `contratos/api/openapi.json`; tipos TS generados; formato de error `{codigo, mensaje, id_traza}` | Es el contrato app–API desde el primer endpoint (`/v1/salud`) |
| ADR-0009 | docker compose con `api`, `simuladores` y `proxy` (Caddy); solo el proxy expone 80/443; secretos en variables de entorno | Es la forma en que el sistema arranca y se entrega |
| ADR-0010 | Android como plataforma de referencia; código Expo multiplataforma | Fija el objetivo de build de la app |
| ADR-0012 | SQLAlchemy 2 async (`asyncpg`) y Alembic con SQL explícito; modelos BD y Pydantic separados | Es la capa de datos y migraciones de todo el proyecto |
| ADR-0013 | TanStack Query (caché solo en memoria) y Zustand; token en `expo-secure-store` | Es el manejo de estado general de la app |

## 2. ADRs que NO aplican todavía (de historia)

| ADR | Decisión | Aplica cuando llegue |
|---|---|---|
| ADR-0003 | Login vía API, tres roles, bloqueo por intentos, usuarios por script de carga | HU-01, HU-02 |
| ADR-0004 | Lista acotada, motor YuNet + SFace dentro de la API, bandas y umbrales | HU-05 |
| ADR-0005 | Bitácora de solo inserción (permisos + trigger), fail-closed, consulta por supervisor | HU-07 (y cada HU que registra eventos) |
| ADR-0008 | Retención de la captura (24 h), galería con consentimiento, acta de eliminación | HU-05, HU-06 |
| ADR-0011 | Valores provisionales (sesión, bloqueo, desempeño, OCR, formato de placa, motivo) | HU-01, HU-03, HU-04, HU-05 y pruebas de desempeño |

## 3. A discutir (mixtos)

| ADR | Qué parte aplica ahora | Qué parte espera a su HU | Pregunta |
|---|---|---|---|
| ADR-0002 | Proyecto Expo con TypeScript, configurado para **dev build** (no Expo Go) | Cámara (`react-native-vision-camera`), ML Kit OCR y Face Detection → HU-04, HU-05 | ¿Confirmas que el dev build se genera con una cuenta EAS del proveedor (cuota gratuita)? |
| ADR-0006 | Contenedor `simuladores` (FastAPI) con `GET /salud`, en la red interna y sin puerto publicado | Endpoints y contratos de `placas`, `requisitorias-personas` y `galeria`; modos de falla → HU-03, HU-05, HU-08 | — (se propone así) |
| ADR-0014 | Logs JSON con `id_traza` por solicitud y sin secretos; formato de error único | Timeout de 3 s y reintento hacia fuentes → HU-03, HU-08 | — (se propone así) |

## 4. Propiedad de rutas

Monorepo propuesto (el stack lo fijan los ADRs; la estructura de carpetas es propuesta del LEAD):

| Rol | Rutas |
|---|---|
| TESTER | `services/api/tests/`, `services/simuladores/tests/`, `apps/movil/__tests__/`, `apps/movil/.maestro/` (flujos E2E, desde HU-01), `pruebas/carga/` (k6, desde las pruebas de desempeño), `pruebas/datos/` (fixtures sintéticos de prueba) |
| DEV | `apps/movil/` (salvo `__tests__/` y `.maestro/`), `services/api/` (salvo `tests/`; incluye `alembic/` y `pyproject.toml`), `services/simuladores/` (salvo `tests/`), `infra/` (`docker-compose.yml`, `Caddyfile`, `.env.example`), `contratos/api/`, `contratos/fuentes/`, `scripts/` |
| ARCH | `docs/arch/` |
| UX | `docs/ux/` |
| BA / PM | `docs/hus/`, `PRD.md` |
| Solo LEAD / humano | `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.agents/`, `skills-lock.json`, `settings.json`, `SPRINT0.md`, `docs/contratos/` (contratos de HU de la skill `escribir-contrato`) |

> Esta tabla también se copia en `AGENTS.md` → `## Propiedad de rutas`.
> Nota: `contratos/` (raíz) son los **contratos técnicos OpenAPI** del ADR-0006/0007 y pertenecen al DEV. Los **contratos de HU** del LEAD van en `docs/contratos/` para no mezclarlos (ver pregunta 3).

## 5. Definition of Done — esqueleto

Nombres exactos que TESTER y DEV deben respetar:

- Endpoint de salud de la API: **`GET /v1/salud`** → `200` con JSON `{"estado": "ok", "bd": "ok", "simuladores": "ok", "version": "<semver>"}`. Si la base o los simuladores no responden, `503` con el campo correspondiente en `"error"`.
- Endpoint de salud de los simuladores: **`GET /salud`** (solo en la red interna) → `200` con `{"estado": "ok"}`.
- Cabecera de traza: toda respuesta de la API lleva **`X-Id-Traza`**.
- Error estándar (ADR-0007): cualquier ruta inexistente bajo `/v1` → `404` con `{"codigo": "NO_ENCONTRADO", "mensaje": "...", "id_traza": "<igual a X-Id-Traza>"}`.
- Comando de arranque: **`docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --build`**.

| # | Criterio | Cómo se verifica |
|---|---|---|
| 1 | El sistema arranca en local con un solo comando y los tres servicios quedan sanos | comando: el de arranque; luego `docker compose -f infra/docker-compose.yml ps` muestra `api`, `simuladores` y `proxy` en estado `running`/`healthy` |
| 2 | La API responde salud a través del proxy, con TLS | prueba: `GET https://localhost/v1/salud` → 200 y cuerpo exacto de arriba (TLS local de Caddy) |
| 3 | La API se conecta a Postgres | prueba: con la base detenida, `/v1/salud` → 503 con `bd`; con la base arriba → 200 |
| 4 | La API alcanza a los simuladores por la red interna | prueba: con `simuladores` detenido, `/v1/salud` → 503 con `simuladores`; arriba → 200 |
| 5 | Los simuladores no son accesibles desde fuera | prueba: `docker compose -f infra/docker-compose.yml config` no publica puertos para `simuladores` ni `api`; solo `proxy` publica 80 y 443 |
| 6 | Las migraciones corren | comando: `docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head` termina con código 0 sobre una base vacía (migración inicial sin tablas de negocio) |
| 7 | Formato de error e id de traza (ADR-0007, ADR-0014) | prueba: `GET /v1/no-existe` → 404 con el JSON de error; `id_traza` igual a la cabecera `X-Id-Traza` |
| 8 | Logs estructurados sin secretos | prueba: una solicitud genera una línea de log JSON con `id_traza`; ninguna línea contiene el valor de `DATABASE_URL` ni de otras variables secretas |
| 9 | El contrato OpenAPI está publicado y al día | prueba: `contratos/api/openapi.json` es idéntico al `/openapi.json` que sirve la API; comando `npm run generar:api` en `apps/movil` genera los tipos sin errores |
| 10 | La app compila y llama a la API solo a través de la URL configurada | comando: `npx tsc --noEmit` en `apps/movil` sin errores; prueba Jest: la pantalla de estado muestra "Conectado" cuando `/v1/salud` responde 200 y "Sin conexión con el servidor" ante error (fetch simulado) |
| 11 | Los runners de pruebas se ejecutan | comandos: `docker compose -f infra/docker-compose.yml run --rm api pytest`, `docker compose -f infra/docker-compose.yml run --rm simuladores pytest` y `npm test` en `apps/movil` terminan con código 0 |
| 12 | No hay secretos en el repositorio | comando: escaneo de secretos (`gitleaks detect` o equivalente) sin hallazgos; existe `infra/.env.example` sin valores reales y `infra/.env` está en `.gitignore` |
| 13 | Respeta los ADRs transversales | revisión LEAD: archivo:línea para ADR-0001, 0007, 0009, 0010, 0012 y 0013 |
| 14 | Cero lógica de negocio | revisión humana: no existen tablas, endpoints, pantallas ni simuladores de placas, rostros, revisión, bitácora o login |
| 15 | La app corre en el Android de referencia | revisión humana: APK de dev build instalado muestra la pantalla de estado en "Conectado" contra el ambiente local o el VPS. Si no hay cuenta EAS a tiempo, se reporta `NO VERIFICADO` |

## 6. Plan

### DEV crea
- Monorepo con la estructura de la sección 4, `.gitignore` y un `README.md` con el comando de arranque.
- `services/api/`: FastAPI con Python 3.12, `pyproject.toml` con versiones exactas fijadas (referencia de estables a la fecha: FastAPI 0.165, SQLAlchemy 2.1, Alembic 1.20, asyncpg 0.32), configuración por variables de entorno, middleware de `id_traza`, manejador de errores con el formato estándar, logs JSON, `GET /v1/salud`, Alembic configurado con una migración inicial vacía, script `scripts/exportar_openapi.py` y Dockerfile.
- `services/simuladores/`: FastAPI con `GET /salud` y Dockerfile. Sin datos ni endpoints de fuentes.
- `infra/`: `docker-compose.yml` (`api`, `simuladores`, `proxy` y, si se aprueba la pregunta 2, `db`), `Caddyfile` (TLS local y proxy a `api`), `.env.example`.
- `contratos/api/openapi.json` generado; `contratos/fuentes/` vacío con un `README.md` que explique su propósito.
- `apps/movil/`: proyecto Expo (SDK estable vigente, referencia 58) con TypeScript, configurado para dev build, TanStack Query, Zustand y `expo-secure-store` instalados, generación de tipos desde el OpenAPI (`npm run generar:api`) y **una sola pantalla técnica de estado** que consulta `/v1/salud`. URL de la API por configuración.

### TESTER crea
- Pruebas automatizadas para los criterios 2, 3, 4, 5, 7, 8, 9 y 10 de la sección 5, con pytest (API y simuladores) y Jest (app).
- Fixtures mínimos en `pruebas/datos/` si los necesita, siempre sintéticos.
- Un informe con el resultado de cada criterio de la DoD (verde, rojo o `NO VERIFICADO`, con evidencia).

### Tareas fuera de TESTER/DEV (no bloquean el veredicto del esqueleto)
- **ARCH:** verificar el LICENSE vigente de YuNet y SFace en opencv_zoo y anotar los hashes SHA-256 de los `.onnx` en el TDD (riesgo abierto del TDD). Confirmar que la versión de OpenCV elegida para HU-05 trae `FaceDetectorYN` y `FaceRecognizerSF` (la estable a la fecha es la 5.x; el TDD se escribió pensando en la API de la 4.x).
- **PM / humano:** consentimientos ampliados firmados antes del día 6; cuenta EAS; proyecto Supabase (si se aprueba la pregunta 2, solo para el VPS).

### NO se crea
- Nada de los ADRs de la sección 2: login, roles, bloqueo, bitácora y su trigger, motor biométrico, modelos ONNX, captura, retención, umbrales, catálogo de motivos.
- Ningún endpoint de `/v1/auth`, `/v1/consultas`, `/v1/revisiones` ni `/v1/bitacora`.
- Ningún simulador de fuentes, contrato de fuente ni dato sintético de negocio.
- Ninguna pantalla de las HUs ni de los wireframes de UX.
- Despliegue en el VPS (llega con la primera HU que se demuestre).

## 7. Preguntas abiertas para el humano

1. **Repositorio git y remoto.** El proyecto no es un repositorio git todavía, y el proceso del LEAD trabaja con ramas y PR (`gh pr create`). ¿Inicializo git aquí y creas un repositorio privado en GitHub? (Nota: la conexión MCP de GitHub falló por token vencido; `gh` en la terminal debe estar autenticado.)
2. **Base de datos para desarrollo y pruebas.** Los ADRs fijan Supabase en la nube para el demo, pero las pruebas de migraciones y del trigger de la bitácora piden "una base recién migrada". Propongo un servicio `db` (Postgres oficial, misma versión mayor que el proyecto Supabase) en el compose, solo para desarrollo y pruebas; Supabase se usa en el VPS. ¿Lo apruebas?
3. **Carpeta de contratos.** ARCH usa `contratos/` para los OpenAPI (DEV) y el playbook del LEAD usa `contratos/` para los contratos de HU. Propongo dejar `contratos/` a ARCH/DEV y mover los contratos de HU a `docs/contratos/`. ¿De acuerdo?
4. **Cuenta EAS** para el dev build de Android (criterio 15): ¿la crea el proveedor ahora? Sin ella, el criterio 15 queda `NO VERIFICADO` y el resto del esqueleto avanza igual.
5. **Estructura de monorepo** (`apps/movil`, `services/api`, `services/simuladores`, `infra`, `contratos`, `pruebas`): es propuesta del LEAD, no de un ADR. ¿La apruebas?

## 8. Cambios durante el ciclo

| Fecha | Cambio | Aprobado por |
|---|---|---|
