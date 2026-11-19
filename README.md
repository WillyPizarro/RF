# Movil Buscador (MININTER) — prototipo

Prototipo móvil para que personal autorizado verifique si un vehículo (por placa) o una persona (por
rostro) tiene requisitoria. **Solo datos sintéticos y simuladores.** Reglas del proyecto en
`AGENTS.md`, producto en `PRD.md`, diseño técnico en `docs/arch/`.

## Estructura

| Ruta | Qué es |
|---|---|
| `apps/movil/` | App Expo (TypeScript, dev build). Hoy: una pantalla técnica de estado |
| `services/api/` | API FastAPI (único punto de entrada de la app), Alembic |
| `services/simuladores/` | Simuladores de fuentes (solo red interna) |
| `infra/` | `docker-compose.yml`, `Caddyfile`, `.env.example` |
| `contratos/api/openapi.json` | Contrato app–API generado desde FastAPI |
| `contratos/fuentes/` | Contratos de las fuentes simuladas (llegan con las HU) |

## Arranque local

Requisitos: Docker con Compose v2, y Node 20 o superior para la app.

```bash
cp infra/.env.example infra/.env      # y reemplazar las claves de ejemplo
docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --build
docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head
curl -k https://localhost/v1/salud
```

Solo el proxy (Caddy) publica los puertos 80 y 443; `api`, `simuladores` y `db` no se exponen. Con
`DOMINIO=localhost`, Caddy usa su CA interna (de ahí el `-k`). El proxy solo enruta `/v1/*`.

> En Windows, si el puerto 80 aparece como excluido (`netsh interface ipv4 show excludedportrange
> protocol=tcp`), el proxy no arranca hasta que se libere.

## Pruebas

```bash
docker compose -f infra/docker-compose.yml run --rm api pytest
docker compose -f infra/docker-compose.yml run --rm simuladores pytest
cd apps/movil && npm test
```

## Contrato OpenAPI

Después de cambiar la API, se regeneran el contrato y los tipos de la app:

```bash
docker compose -f infra/docker-compose.yml run --rm --no-deps -T api \
  python scripts/exportar_openapi.py > contratos/api/openapi.json
cd apps/movil && npm run generar:api
```

## App móvil

```bash
cd apps/movil
cp .env.example .env                  # EXPO_PUBLIC_API_URL
npm install
npx tsc --noEmit
```

La app usa un **dev build** (no Expo Go) generado con EAS; Android es la plataforma de referencia.
