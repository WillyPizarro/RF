# VEREDICTO — HU-08 Simuladores de fuentes

**Contrato:** `docs/contratos/CONTRATO-HU-08.md` **v4** (aprobado por el humano el 2026-11-19)
**Rama:** `hu-08` (base `main` 2ef0829) · **Código del DEV:** `d08b907` · **Pruebas del TESTER:** `8f3b8a5`, informe `0eac363`
**Fecha:** 2026-11-19 · **LEAD**, skill `veredicto`
**Resultado:** **VERDE tras la vuelta 1** (A1 cerrado en `7e6be45`). Ningún rojo del código. Quedan dos `NO VERIFICADO` de entorno o herramienta (§7) para aceptación del humano.

---

## 1. Propiedad de rutas

`git log main..hu-08 --name-only`, agrupado por prefijo:

| Rol | Commits | Archivos | ¿Dentro de sus rutas? |
|---|---|---|---|
| `[DEV]` | `84208cd`, `d08b907` | `services/simuladores/` (salvo `tests/`), `contratos/fuentes/`, `infra/`, `services/api/app/config.py`, `informes/DEV-HU-08.md` | Sí |
| `[TESTER]` | `38c6972`, `8f3b8a5`, `0eac363` | `services/simuladores/tests/`, `informes/TESTER-HU-08.md` | Sí |
| `[LEAD]` | 8 commits | `docs/contratos/` | Sí |

Ningún commit sin prefijo y ninguno con `Empezar.txt`. **Sin hallazgos.**

## 2. Versión del contrato

El DEV (`d08b907`, M-1 a M-3) y el TESTER (`8f3b8a5`, M-3) trabajaron sobre la **v4**. El veredicto es válido.

## 3. Corrida del LEAD (no se confió en los informes)

Sistema arrancado con `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env up -d --build db simuladores api`:

| Corrida | Comando | Resultado |
|---|---|---|
| Contenedor | `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env run --rm -T simuladores pytest` | **115 en verde, 28 omitidas** (las mismas cifras que el TESTER) |
| Anfitrión | `pytest services/simuladores/tests --integracion --reinicio` (venv con `requirements-pruebas.txt`) | **136 en verde, 7 omitidas, 0 rojos** (7 min 39 s) |
| `/v1/salud` desde la red interna | `docker compose … exec api` → `GET http://localhost:8000/v1/salud` | `200 {"estado":"ok","bd":"ok","simuladores":"ok","version":"0.1.0"}` con `X-Id-Traza` |
| Semilla versionada | `git ls-files services/simuladores/app/datos/` | `semilla.json` |

Omitidas en el anfitrión: 4 de `test_herramientas.py` (corren y pasan en el contenedor) y **3 que dependen de fotos precargadas** (ver §5).

## 4. Matriz de trazabilidad

| Criterio de aceptación (HU-08) | Caso del contrato | Prueba | Resultado |
|---|---|---|---|
| Esc. 1: la respuesta llega con el formato del contrato documentado | §1 a §3 (placas, personas, galería) | `test_fuente_placas.py`, `test_fuente_personas.py`, `test_fuente_galeria.py` | 🟢 |
| Esc. 1 | §4 datos sintéticos (volumen, prefijo `ZZ`, `SIM-`, datos fijos, determinismo) | `test_datos_sinteticos.py`, `test_reinicio.py` | 🟢 |
| Esc. 1 | §4 semilla versionada | LEAD: `git ls-files` | 🟢 |
| Esc. 1 | §4 sin imágenes fuera de `apps/movil/assets/` (C3) | `test_repositorio.py` | 🟢 |
| Esc. 1 | §4 bis carga de fotos (C1): origen, nombres, sin reinicio, versión, cifrado | `test_carga_fotos.py`, `test_reinicio.py` | 🟢 (PNG). JPEG: `NO VERIFICADO` |
| Esc. 1 | §6 contratos existen, son OpenAPI 3.1 y documentan lo pedido | `test_contratos_yaml.py` | 🟢 |
| Esc. 1 | §6 las respuestas validan contra el yaml: JSON 200/404 | `::test_respuesta_normal_valida_contra_yaml` | 🟢 |
| Esc. 1 | §6 las respuestas validan contra el yaml: **foto cargada** | `::test_foto_cargada_valida_contra_yaml` | 🟢 tras la vuelta 1 (`test_carga_fotos.py::test_foto_cargada_valida_contra_yaml`) |
| Esc. 1: la app no se conecta directo al simulador | §8 sin puerto, Caddyfile, textos de C7 en la app, desde la API sí | `test_aislamiento.py` | 🟢 |
| Esc. 1 | §8 `/v1/salud` intacta | LEAD, desde la red interna | 🟢 sin el proxy. A través del proxy: `NO VERIFICADO` (entorno: puerto 80 ocupado por `http.sys`, igual que en el Sprint 0) |
| Esc. 2: otra implementación del contrato | §7 mock solo desde el yaml (Prism) | `test_reemplazo_y_config.py::test_mock_desde_el_yaml_cumple_el_mismo_contrato` | 🟢 |
| Esc. 2 | §7 `FUENTE_*_URL` y `FUENTE_TIMEOUT_S` documentadas | `test_reemplazo_y_config.py` | 🟢 |
| Esc. 2 | §7 la API usa `FUENTE_*_URL` | — | Diferido a HU-03 (decisión 1, `PENDIENTES.md`) |
| Esc. 3: respuesta fuera de contrato → error controlado y bitácora | §5 modos de falla (mitad del simulador) | `test_modos_falla.py`, `test_contratos_yaml.py::test_malformada_no_valida_contra_yaml` | 🟢 |
| Esc. 3 | Error controlado y bitácora en la API | — | Diferido a HU-03 y HU-07 (decisión 1, `PENDIENTES.md`) |
| — | C5 y C6: herramientas de prueba en el contenedor | `test_herramientas.py` | 🟢 |

**Casos sin criterio de la HU** (el negocio los aprobó como decisiones del contrato): la ruta `/control/modos` (decisión 7) y los prefijos `ZZ` y `SIM-` (decisión 5).

## 5. Arbitraje

| # | Caso | Contrato | Prueba | Código | Desenlace | Destinatario | Vuelta |
|---|---|---|---|---|---|---|---|
| A1 | §6 "Coinciden con lo desplegado", la respuesta `200` de `/personas/{id}/fotos/{foto_id}` | Toda respuesta del simulador en modo `normal` valida contra el yaml de su fuente | `test_foto_cargada_valida_contra_yaml` se omite si no hay fotos precargadas, y nunca las hay: `test_carga_fotos.py` agrega su foto y la quita. El motivo de la omisión todavía dice "pendiente de contrato v2", pero C1 (v2) ya define cómo cargarla | El DEV la sirve (verde en `test_carga_fotos.py`), pero falta validarla contra el yaml | **Se apartó la prueba**: el caso quedó sin verificar | **TESTER** | 1 |

Ajustes menores para la misma vuelta (sin cambio de resultado): `test_fuente_galeria.py::test_version_cambia_si_cambian_las_fotos` sigue con `skip` "pendiente de contrato v2", aunque el caso ya está cubierto por `test_carga_fotos.py`. Hay que borrarla o actualizar su motivo, y lo mismo con `test_fuente_personas.py:48`.

## 6. Trampas

- El código no menciona las placas ni las personas de prueba: solo aparecen en `semilla.json`.
- Todas las pruebas tienen aserciones sobre lo que dice el contrato.
- Las pruebas que cambiaron entre `38c6972` y `8f3b8a5` lo hicieron para seguir a la v2, la v3 y la v4, que el humano aprobó.
- **Sin trampas detectadas.**

## 7. NO VERIFICADO (para aceptación del humano)

1. Foto en JPEG (solo se probó PNG; generar un JPEG exige una biblioteca de imágenes).
2. `/v1/salud` a través del proxy (el puerto 80 lo ocupa `http.sys` de Windows). Verificado desde la red interna.
3. Uso de `FUENTE_*_URL` por la API, y error controlado más bitácora: diferidos a HU-03 y HU-07 por la decisión 1 del contrato.

## 7 bis. Vuelta 1 (2026-11-19)

- `7e6be45 [TESTER]`: solo toca `services/simuladores/tests/` e `informes/TESTER-HU-08.md` (sus rutas).
- Corrida del LEAD, siempre con `-f infra/docker-compose.yml -f infra/docker-compose.fotos.yml`:
  - anfitrión, archivos tocados (`--integracion`): **58 en verde, 1 omitida por diseño** (`test_fuente_personas.py:48`, cubierta por `test_carga_fotos.py`);
  - contenedor, la suite completa: **115 en verde, 27 omitidas** (las de anfitrión).
- **A1 cerrado: 🟢.**
- Nota de entorno: en la vuelta 0, el LEAD corrió `run api pytest` sin `docker-compose.fotos.yml` y eso recreó `simuladores` sin el montaje. Para cualquier corrida con fotos, arrancar siempre con los dos archivos.

## 7 ter. Aceptación del humano (vía PM, 2026-11-19)

Los `NO VERIFICADO` 1 (JPEG) y 2 (`/v1/salud` a través del proxy) quedan **aceptados**, con una condición: el contrato de HU-05 debe exigir una prueba de carga de un JPEG antes de cargar las fotos reales con consentimiento. Anotado en `docs/contratos/PENDIENTES.md`.

## 8. Siguiente paso

Aceptados los `NO VERIFICADO`, el LEAD prepara el PR `hu-08 → main` con esta matriz. El merge lo hace el humano.
