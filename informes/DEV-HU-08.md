# Informe DEV — HU-08 Simuladores de fuentes

**Documento de trabajo:** `docs/contratos/CONTRATO-HU-08.md` **v4** (v1 a v4 aprobados 2026-11-19) · **Encargo:** `docs/contratos/ENCARGO-HU-08.md` con M-1, M-2 y M-3 · **Rama:** `hu-08` · **Fecha:** 2026-11-19

No leí ni ejecuté las pruebas del TESTER. `services/simuladores/tests/` tiene cambios en el árbol de trabajo que no son míos: no los miré ni los incluí en mis commits.

## Revisión contra v2, v3 y v4

| Cambio | Qué hice | Verificación |
|---|---|---|
| C1 carga de fotos (§4 bis) | Nada: ya lo cumplía lo construido en v1 (origen `/fotos-origen`, nombres `<persona_id>__<n>.<jpg|png>`, `foto_id` `<persona_id>__<n>`, carga en cada solicitud, `version` estable entre reinicios con la misma llave, cifrado con `SIM_FOTOS_LLAVE`) | Script propio y Docker (ver "Lo que verifiqué") |
| C2 y C7 textos prohibidos en `apps/movil/src/` | Nada que cambiar | `grep -F` de `//simuladores`, `simuladores:8001`, `:8001` y `/placas/` → sin coincidencias |
| C3 imágenes versionadas fuera de `apps/movil/assets/` | Nada que cambiar | `git ls-files` → ninguna |
| C4 respuestas de `/control/modos` | Nada: ya devolvía `{"modo", "latencia_ms"}`, con `latencia_ms` en `null` salvo en `latencia` (5000 por defecto) | Script propio |
| C5 dependencias de prueba | `pyyaml==6.0.3` y `jsonschema==4.26.0` en el grupo `dev` de `services/simuladores/pyproject.toml` | `run --rm simuladores python -c "import yaml, jsonschema"` → OK; `pytest --version` → 9.2.0 |
| C6 montaje de los yaml | `infra/docker-compose.yml`: `../contratos/fuentes` → `/app/contratos/fuentes:ro` y `CONTRATOS_FUENTES_DIR=/app/contratos/fuentes` en `simuladores` | `run --rm simuladores sh -c 'ls $CONTRATOS_FUENTES_DIR'` → los tres yaml y el README; `docker compose config` muestra el bind en solo lectura |

## Qué construí

| Pieza | Archivos | Notas |
|---|---|---|
| Fuente `placas` | `services/simuladores/app/main.py` | `GET /placas/{placa}`: 200 con `requisitoria` o `null`; 404 `PLACA_NO_REGISTRADA`. No normaliza (`zza-101` → 404) |
| Fuente `requisitorias-personas` | `app/main.py`, `app/fotos.py` | `GET /personas/{persona_id}` (404 `PERSONA_NO_REGISTRADA`), `GET /personas/{persona_id}/fotos/{foto_id}` (200 `image/jpeg` o `image/png` descifrada, `Cache-Control: no-store`; 404 `FOTO_NO_DISPONIBLE`) |
| Fuente `galeria` | `app/main.py`, `app/fotos.py` | `GET /galeria`: solo personas con ≥ 1 foto; `version` = `g-` + 16 hex del sha256 del conjunto de fotos cifradas. Sin fotos: `personas: []` |
| Modos de falla | `app/modos.py`, `app/main.py` | `PUT /control/modos/{fuente}` y `GET /control/modos`. `normal`, `latencia` (por defecto 5000 ms), `error_500` (`ERROR_SIMULADO`), `malformada`. Fuente inválida → 404 `FUENTE_DESCONOCIDA`; cuerpo inválido → 422 `SOLICITUD_INVALIDA`. En memoria: al arrancar todo está en `normal` |
| Datos sintéticos | `app/datos/semilla.json`, `app/datos.py`, `scripts/generar_semilla.py` | 220 vehículos (32 con requisitoria), todas `ZZ?-###`; `ZZA-101` con, `ZZB-201` sin, `ZZZ-999` no existe. 24 personas `SIM-P-0001`…`SIM-P-0024`, documentos `SIM-########`, apellidos claramente ficticios. El script es determinista (mismo md5 en dos corridas) |
| Fotos cifradas | `app/fotos.py`, `Dockerfile`, `infra/docker-compose.yml`, `infra/docker-compose.fotos.yml` | AES-GCM (256 bits, nonce de 12 bytes) con la llave `SIM_FOTOS_LLAVE`, en el volumen `fotos-galeria` (`/datos/fotos`) |
| Contratos | `contratos/fuentes/placas.yaml`, `requisitorias-personas.yaml`, `galeria.yaml`, `README.md` | OpenAPI 3.1 con campos, códigos de error, ejemplos (alineados con la semilla) y `x-tiempo-respuesta-ms`. `/control/*` no figura |
| URL por fuente en la API | `services/api/app/config.py`, `infra/docker-compose.yml`, `infra/.env.example` | `FUENTE_PLACAS_URL`, `FUENTE_REQUISITORIAS_URL`, `FUENTE_GALERIA_URL` (vacías → `SIMULADORES_URL`), `FUENTE_TIMEOUT_S` (por defecto 3). Solo configuración: los adaptadores llegan con HU-03 y HU-05 |

Formato de error del simulador: `{codigo, mensaje}`. Las rutas inexistentes responden 404 `NO_ENCONTRADO`, los métodos no permitidos 405 `METODO_NO_PERMITIDO` y una excepción 500 `ERROR_INTERNO`, igual que la API (patrón del Sprint 0).

### Cuerpos `malformada`

| Fuente | Cuerpo 200 |
|---|---|
| `placas` | `{"placa": <la pedida>, "requisitoria_vigente": "desconocido", "es_sintetico": true}` (faltan campos y no es booleano), exista o no la placa |
| `requisitorias-personas` | `/personas/{id}` → `{"persona_id": <id>, "es_sintetico": true}`; `/fotos/{foto_id}` → JSON en lugar de imagen |
| `galeria` | `{"version": …, "personas": "no_es_lista", "es_sintetico": true}` |

### Decisiones internas (el contrato las deja al DEV)

- **Semilla:** JSON versionado, generado por `scripts/generar_semilla.py`. No hay base de datos en el simulador.
- **Fotos:** el almacenamiento cifrado es un **espejo** de `SIM_FOTOS_DIR`, que se revisa en cada solicitud (sin reiniciar): un archivo `<persona_id>__<n>.<jpg|png>` nuevo o cambiado se cifra, uno que se quita se borra del almacenamiento. Se ignoran los nombres que no cumplen el patrón y las personas que no están en la semilla. `foto_id` = `<persona_id>__<n>` (por ejemplo `SIM-P-0001__1`). Si `SIM_FOTOS_DIR` no está definida, se usa lo que ya está cifrado. Consecuencia: en compose la carpeta de origen tiene que estar montada para que la galería tenga fotos. Si en HU-05 se prefiere que el origen se pueda desmontar tras cargar, es un cambio interno chico.
- **Llave:** `SIM_FOTOS_LLAVE` (32 bytes en base64). Vacía → llave aleatoria en memoria (las fotos se vuelven a cifrar en cada arranque y `version` cambia). Mal formada → 500 `ERROR_INTERNO` al tocar fotos.
- **Dependencia nueva:** `cryptography==50.0.2` en el simulador, para el AES-GCM que fijan el ADR-0008 y el TDD (no hay AES-GCM en la biblioteca estándar).

## Cómo se arranca y se prueba a mano

```bash
cp infra/.env.example infra/.env     # completar claves; SIM_FOTOS_LLAVE recomendado
docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --build
# Con fotos (carpeta del host FUERA del repositorio en SIM_FOTOS_ORIGEN):
docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env up -d --build

# Desde la red interna (el simulador no publica puertos):
docker compose -f infra/docker-compose.yml exec api python -c "import httpx;print(httpx.get('http://simuladores:8001/placas/ZZA-101').text)"
docker compose -f infra/docker-compose.yml exec api python -c "import httpx;print(httpx.put('http://simuladores:8001/control/modos/placas', json={'modo':'error_500'}).text)"
```

Regenerar la semilla (solo si cambian las reglas de datos): `cd services/simuladores && python scripts/generar_semilla.py`.

### Lo que verifiqué

| Qué | Cómo | Resultado |
|---|---|---|
| Los tres yaml son OpenAPI 3.1 válidos | `openapi-spec-validator` 0.9.0 en un venv fuera del repo | OK |
| Los ejemplos de cada yaml validan contra su esquema | `jsonschema` (Draft 2020-12) | 13/13 OK |
| Secciones 1 a 3 y 5 del contrato | Script mío fuera del repo con `TestClient` y una PNG de 1×1 generada en tiempo de ejecución (no es un rostro, no se versiona) | Todos los casos OK, incluidas las 220 placas y 24 personas validando contra su yaml en `normal`, y los cuerpos `malformada` NO validando |
| Aislamiento de modos | idem | `error_500` en `placas` no afecta personas, galería ni `/salud` |
| Latencia | `latencia_ms: 300` | la respuesta tarda ≥ 0,3 s; sin `latencia_ms` → 5000 |
| Stack en Docker | `up -d --build` | `db`, `simuladores` y `api` healthy. `GET /v1/salud` desde `api` → `{"estado":"ok","bd":"ok","simuladores":"ok",…}` |
| Desde `api` | `GET http://simuladores:8001/placas/ZZA-101` | 200 |
| Puertos | `docker compose … config` | solo `proxy` publica |
| Fotos en Docker | Override con una PNG generada y llave aleatoria | aparece en `/galeria`, la foto vuelve con `image/png` y los mismos bytes; en el volumen el archivo `.enc` no tiene la cabecera PNG; tras `restart` la `version` es la misma |
| URL por fuente | `FUENTE_PLACAS_URL=http://mock-placas:4010/` | la API la toma (sin `/` final) y las otras dos caen en `SIMULADORES_URL`; timeout 3.0 |
| Palabra prohibida | `grep -ri identific` en contratos, simulador, infra y config | sin coincidencias |

**No verificado por mí:** el mock de Prism del §7 (no tuve permiso para descargar `@stoplight/prism-cli` en esta máquina). Además, el `proxy` no levantó en esta máquina porque el puerto 80 del host está ocupado por otro proceso; es del entorno, no de este cambio (no toqué el `Caddyfile`).

## Variables de entorno nuevas

| Variable | Servicio | Uso |
|---|---|---|
| `FUENTE_PLACAS_URL`, `FUENTE_REQUISITORIAS_URL`, `FUENTE_GALERIA_URL` | `api` | URL de cada fuente; vacía → `SIMULADORES_URL` |
| `FUENTE_TIMEOUT_S` | `api` | Timeout por fuente (por defecto 3) |
| `SIMULADORES_URL` | `api` | Ya existía; ahora se puede sobreescribir desde `infra/.env` |
| `SIM_FOTOS_DIR` | `simuladores` | Carpeta de origen de las fotos (en compose: `/fotos-origen`) |
| `SIM_FOTOS_LLAVE` | `simuladores` | Llave AES-GCM, base64 de 32 bytes. Nunca se versiona |
| `SIM_FOTOS_ALMACEN` | `simuladores` | Almacenamiento cifrado (en compose: `/datos/fotos`, volumen `fotos-galeria`). Interna, no está en el contrato |
| `SIM_FOTOS_ORIGEN` | host | Carpeta del host que monta `infra/docker-compose.fotos.yml` |

Sin migraciones.

## Avisos para el LEAD

1. ~~Conflicto en el §8~~: resuelto en v2 (C2) y v4 (C7).
2. **Arnés de pruebas:** la imagen del simulador ahora necesita `cryptography`, `pyyaml` y `jsonschema` (se instalan con `pip install ".[dev]"` en el Dockerfile; hay que reconstruir la imagen con `--build`). Los yaml están en `$CONTRATOS_FUENTES_DIR`. `docker compose run --rm simuladores pytest` monta el volumen `fotos-galeria` y recibe `SIM_FOTOS_DIR=/fotos-origen`, que no existe sin el override: la galería arranca vacía. Una prueba que defina su propio `SIM_FOTOS_DIR` lo verá reflejado sin reiniciar.
3. **`.gitignore`:** ignora `*.jpg` y `*.jpeg`, pero no `*.png`. No está en mis rutas de este contrato; sugiero agregar `*.png` para reforzar la regla 8.
