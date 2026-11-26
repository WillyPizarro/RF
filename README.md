# Movil Buscador (MININTER) — prototipo

Prototipo móvil para que personal autorizado verifique si un vehículo (por placa) o una persona (por
rostro) tiene requisitoria. **Solo datos sintéticos y simuladores.** Reglas del proyecto en
`AGENTS.md`, producto en `PRD.md`, diseño técnico en `docs/arch/`.

## Estructura

| Ruta | Qué es |
|---|---|
| `apps/movil/` | App Flutter (Android primero): login, placas con lectura por cámara (ML Kit) y bitácora |
| `services/api/` | API FastAPI (único punto de entrada de la app), Alembic |
| `services/simuladores/` | Simuladores de fuentes (solo red interna) |
| `infra/` | `docker-compose.yml` (+ `.vps.yml` y `.fotos.yml`), `nginx/` (proxy), `.env.example` |
| `scripts/` | `desplegar.ps1` (VPS) y `publicar-apk.ps1` (APK para probadores) |
| `docs/despliegue/` | Manual de despliegue, guía para probadores, dominio y llaves SSH |
| `contratos/api/openapi.json` | Contrato app–API generado desde FastAPI |
| `contratos/fuentes/` | Contratos de las fuentes simuladas (llegan con las HU) |

## Arranque local

Requisitos: Docker con Compose v2, y Flutter 3.50.1 para la app.

```bash
cp infra/.env.example infra/.env      # y reemplazar las claves de ejemplo
docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --build
docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head
curl -k https://localhost:8443/v1/salud     # con PROXY_PUERTO_HTTPS=8443, como en .env.example
```

Solo el proxy (**NGINX**, `infra/nginx/`) publica puertos (80 y 443, o `PROXY_PUERTO_HTTP` y
`PROXY_PUERTO_HTTPS`); `api`, `simuladores` y `db` no se exponen. Con `DOMINIO=localhost`, el proxy
usa una **CA local** que genera al primer arranque, fuera del repositorio (de ahí el `-k`; para el
teléfono de pruebas se exporta con `infra/exportar-ca-local.ps1`). El proxy solo enruta `/v1/*` y
`/descargas/movil-buscador.apk` (con usuario y clave); el resto responde `404`. En el VPS usa
Let's Encrypt con `certbot` (`docs/despliegue/MANUAL-DESPLIEGUE.md`).

> En Windows, si el puerto 80 aparece como excluido (`netsh interface ipv4 show excludedportrange
> protocol=tcp`), el proxy no arranca hasta que se libere.

## Pruebas

```bash
docker compose -f infra/docker-compose.yml run --rm api pytest
docker compose -f infra/docker-compose.yml run --rm simuladores pytest
cd apps/movil && flutter test
```

## Contrato OpenAPI

Después de cambiar la API, se regenera el contrato (la app Flutter tiene sus modelos escritos a mano
en `apps/movil/lib/api/modelos.dart`, que siguen ese contrato):

```bash
docker compose -f infra/docker-compose.yml run --rm --no-deps -T api \
  python scripts/exportar_openapi.py > contratos/api/openapi.json
```

## App móvil

Flutter 3.50.1 / Dart 3.14.0 (CONTRATO-MIGRACION-FLUTTER). La URL de la API se pasa al compilar:

```bash
cd apps/movil
flutter pub get
flutter analyze
flutter build apk --debug --dart-define=API_URL=https://localhost:8443    # teléfono por adb reverse
```

- El APK de **depuración** confía además en la CA de usuario (la CA local del proxy, instalada en el teléfono de pruebas). El de **release** confía solo en las CA del sistema.
- El APK de release para probadores se firma con una llave que vive **fuera** del repositorio y se publica con `scripts/publicar-apk.ps1` (`docs/despliegue/MANUAL-DESPLIEGUE.md` §6.1). Los `.apk` y `.aab` no se versionan.
