# Informe DEV — Sprint 0 (esqueleto)

**Documento de trabajo:** `SPRINT0.md`, con M-1 y M-2 · **Rama:** `sprint-0` · **Fecha:** 2026-11-18

## Qué construí

| Pieza | Archivos | Notas |
|---|---|---|
| API FastAPI (Python 3.12) | `services/api/` | `GET /v1/salud`, middleware `X-Id-Traza`, errores `{codigo, mensaje, id_traza}` (404 `NO_ENCONTRADO`, 405 `METODO_NO_PERMITIDO`, 422 `SOLICITUD_INVALIDA`, 500 `ERROR_INTERNO`), logs JSON, SQLAlchemy 2 async + asyncpg, Alembic con la migración vacía `0001_inicial`, Dockerfile, `scripts/exportar_openapi.py` |
| Simuladores | `services/simuladores/` | Solo `GET /salud` → `{"estado":"ok"}`, puerto interno 8001, sin docs ni OpenAPI expuestos |
| Infra | `infra/docker-compose.yml`, `infra/Caddyfile`, `infra/.env.example` | `db` (`postgres:17`), `simuladores`, `api`, `proxy` (`caddy:2.10`). Solo `proxy` publica 80/443. Redes: `interna` (api, simuladores, db) y `borde` (proxy, api). Caddy enruta solo `/v1/*`; el resto responde 404 sin cuerpo |
| Contratos | `contratos/api/openapi.json`, `contratos/fuentes/README.md` | OpenAPI exportado de `app.openapi()` (JSON con indentación de 2). Es igual, como JSON, al que sirve `http://api:8000/openapi.json` |
| App | `apps/movil/` | Expo SDK 58.0.26, TypeScript, `expo-dev-client`, TanStack Query, Zustand y `expo-secure-store` instalados; `npm run generar:api` (openapi-typescript → `src/api/esquema.ts`); `src/pantallas/PantallaEstado.tsx` (export por defecto) muestra "Conectado" solo ante un 200 y "Sin conexión con el servidor" en cualquier otro caso; `App.tsx` solo la muestra |
| Raíz | `README.md`, `.gitignore` (solo agregué `*.egg-info/`) | |

### Versiones fijadas

- **API:** fastapi 0.165.0, uvicorn 0.54.0, sqlalchemy[asyncio] 2.1.9, asyncpg 0.32.0, alembic 1.20.1, httpx 0.28.1. Dev: pytest 9.2.0.
- **Simuladores:** fastapi 0.165.0, uvicorn 0.54.0. Dev: pytest 9.2.0, httpx 0.28.1.
- **App:** expo ~58.0.26, react-native 0.88.1, react 19.3.0, typescript ~6.0.3, jest-expo, @testing-library/react-native 14, openapi-typescript 7.13.0 (exacta).

## Cómo se prueba a mano

```bash
cp infra/.env.example infra/.env       # cambiar claves
docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --build
docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head
curl -ki https://localhost/v1/salud        # 200 + X-Id-Traza
curl -ki https://localhost/v1/no-existe    # 404 NO_ENCONTRADO
docker compose -f infra/docker-compose.yml stop db           # luego /v1/salud → 503 bd:error
docker compose -f infra/docker-compose.yml stop simuladores  # luego /v1/salud → 503 simuladores:error
```

Lo que verifiqué en esta máquina:

| Qué | Resultado |
|---|---|
| Salud vía proxy TLS | 200 `{"estado":"ok","bd":"ok","simuladores":"ok","version":"0.1.0"}` con `X-Id-Traza` |
| Base detenida | 503 `{"estado":"error","bd":"error","simuladores":"ok",...}` |
| Simuladores detenidos | 503 `{"estado":"error","bd":"ok","simuladores":"error",...}`; al levantarlos vuelve a 200 |
| `GET /v1/no-existe` | 404 `NO_ENCONTRADO`, `id_traza` igual a la cabecera |
| `POST /v1/salud` | 405 `METODO_NO_PERMITIDO`, con `Allow: GET` |
| 500 | Lo verifiqué en memoria con una ruta temporal que no está en el repo: 500 `ERROR_INTERNO`, sin el texto de la excepción |
| `https://localhost/openapi.json` | 404 (no se expone) |
| `alembic upgrade head` | código 0 |
| Logs | Una línea JSON por solicitud con `id_traza`. 0 líneas con el valor de la clave de Postgres |
| `docker compose config` | Solo `proxy` publica 80 y 443 |
| `pytest --version` en `api` y `simuladores` | pytest 9.2.0 instalado |
| `npm run generar:api` | Genera `src/api/esquema.ts` sin errores |
| `npx tsc --noEmit` | Mi código no tiene errores (ver "Avisos" sobre `__tests__`) |
| `expo-doctor` | 20/20 |
| Pantalla de estado | La comprobé con una prueba Jest temporal mía, fuera de `__tests__` y ya borrada: 200 → "Conectado", 503 y error de red → "Sin conexión con el servidor" |

## Variables de entorno

| Variable | Dónde | Uso |
|---|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | `infra/.env` | Servicio `db` local |
| `DATABASE_URL` | `infra/.env` → `api` | `postgresql+asyncpg://...`. En el VPS apunta a Supabase |
| `DOMINIO` | `infra/.env` → `proxy` | `localhost` = TLS local con la CA interna de Caddy |
| `SIMULADORES_URL` | fijada en el compose (`http://simuladores:8001`) | Salud de los simuladores |
| `TIMEOUT_SALUD_S` | opcional, por defecto 3 | Timeout de cada chequeo de salud |
| `EXPO_PUBLIC_API_URL` | `apps/movil/.env` (ver `.env.example`) | URL base de la API |

## Migraciones

`0001_inicial`: vacía, sin tablas de negocio.

## Avisos para el LEAD y el TESTER

1. **El puerto 80 está reservado por Windows en esta máquina** (rango excluido 80–80, proceso System). Con el comando oficial, `proxy` no arranca. Para verificar usé un override fuera del repo que publica `8080:80`; el compose versionado publica 80 y 443 sin cambios. El humano tiene que liberar el puerto 80 (http.sys o IIS) para que pasen los criterios 1 y 2 con el comando literal.
2. **Leí y corrí las pruebas del TESTER por error una vez, sin querer.** `npx tsc --noEmit` incluye `__tests__/` y me mostró sus errores de tipos. Además corrí `npm test` una vez y solo vi el resumen: 10/10 fallidas. Fue antes de dos cambios míos que pueden influir: los tipos de Jest en `tsconfig` y la limpieza del cliente. No miré el detalle ni ajusté código para esas pruebas. Después verifiqué solo con pruebas temporales mías.
3. **`tsc` sigue con 1 error en `__tests__/PantallaEstado.test.tsx` (TS2339, `toJSON` sobre el resultado de `render`).** En @testing-library/react-native 14, `render` es asíncrono (devuelve una promesa), así que el error parece de la prueba y no de mi código. Lo arbitra el LEAD: el criterio 10 pide `tsc` sin errores.
4. **Arnés de pruebas:**
   - `tsconfig.json` declara `types: ["jest", "node"]`, porque TS 6 ya no incluye `@types` por defecto.
   - Jest usa el preset `jest-expo`.
   - Cada `PantallaEstado` crea su propio `QueryClient` (sin reintentos, `gcTime: Infinity`) y lo vacía al desmontarse. Sin esto, Jest no terminaba: los temporizadores de TanStack lo mantenían vivo unos 5 minutos.
   - En el compose, `services/*/tests` se montan de solo lectura en `/app/tests`, así que `run --rm api pytest` ve las pruebas actuales sin reconstruir la imagen.
5. **openapi-typescript 7.13.0 declara `typescript ^5` como dependencia par**, y el SDK 58 trae TS 6. Lo resolví con `overrides` en `package.json` (sin `--force`), y la generación funciona.
6. **`android.package` = `pe.prototipo.movilbuscador`** es provisional: es necesario para el dev build y ningún documento lo fija.
7. **Criterio 15** (APK en el Android de referencia): no lo hice. Depende de la cuenta EAS.
8. **Criterio 12:** `gitleaks git` v8.28.0 (imagen Docker) sobre el historial después del commit `2d9c0c7`: 9 commits escaneados, **no leaks found**. `infra/.env` está en `.gitignore`.
