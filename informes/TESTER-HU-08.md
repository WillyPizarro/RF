# Informe TESTER — HU-08 Simuladores de fuentes

**Contrato:** `docs/contratos/CONTRATO-HU-08.md` **v1** · **Encargo:** `docs/contratos/ENCARGO-HU-08.md` (sin M-n) · **Rama:** `hu-08`
**Estado:** pruebas escritas; **corrida definitiva pendiente** (Docker Desktop no corre en este equipo y la v2 del contrato está pendiente por las preguntas 1 y 2). Lo que se muestra abajo es una corrida parcial en el anfitrión, sin el sistema arrancado y con el trabajo del DEV en curso.

## Cómo se corren

| Forma | Comando | Qué cubre |
|---|---|---|
| Dentro de la red (encargo, SPRINT0 §5) | `docker compose -f infra/docker-compose.yml run --rm simuladores pytest` | §1 a §5 por HTTP. Las pruebas que leen el repositorio se omiten (el contenedor no tiene `contratos/` ni `infra/`) |
| Anfitrión, sistema arrancado | `pip install -r services/simuladores/tests/requirements-pruebas.txt` y luego `pytest services/simuladores/tests --integracion` | **Todo el contrato.** Las peticiones salen desde dentro del contenedor `api` (`docker compose exec -T api python`), que es el camino que permite §8 |
| Además, determinismo | `pytest services/simuladores/tests --integracion --reinicio` | Reinicia `simuladores` (unos segundos sin servicio) |
| Mock de §7 | Incluido en `--integracion`; necesita `npx` (Node) y descarga `@stoplight/prism-cli@5` la primera vez | §7 "Segunda implementación" |

Las dependencias de anfitrión (`pyyaml`, `jsonschema`, `openapi-spec-validator`) viven en `services/simuladores/tests/requirements-pruebas.txt` (ruta del TESTER). No toqué dependencias del DEV.

## Caso del contrato → prueba

Archivos en `services/simuladores/tests/`. Las formas que exige el contrato están escritas desde el contrato en `ayudas_contrato.py`.

| § | Caso | Prueba | Estado |
|---|---|---|---|
| 1 | Placa con requisitoria (`ZZA-101`) | `test_fuente_placas.py::test_placa_con_requisitoria` | NO EJECUTADA |
| 1 | Placa sin requisitoria (`ZZB-201`), misma forma | `::test_placa_sin_requisitoria`, `::test_misma_forma_con_y_sin_requisitoria` | NO EJECUTADA |
| 1 | Placa no registrada → 404 `PLACA_NO_REGISTRADA` + mensaje exacto | `::test_placa_no_registrada` | NO EJECUTADA |
| 1 | Minúsculas → 404 (no normaliza) | `::test_minusculas_no_se_normalizan` | NO EJECUTADA |
| 1 | El simulador no valida el formato (no está → 404) | `::test_formato_invalido_no_se_valida_en_el_simulador` | NO EJECUTADA |
| 2 | Persona con requisitoria (`SIM-P-0001`) | `test_fuente_personas.py::test_persona_con_requisitoria` | NO EJECUTADA |
| 2 | Persona no registrada → 404 `PERSONA_NO_REGISTRADA` | `::test_persona_no_registrada` | NO EJECUTADA |
| 2 | Foto no cargada → 404 `FOTO_NO_DISPONIBLE` | `::test_foto_no_cargada` | NO EJECUTADA |
| 2 | Foto cargada → 200 `image/jpeg`/`image/png`, bytes descifrados (firma de imagen) | `::test_fotos_cargadas_se_sirven_como_imagen` | **NO VERIFICADO** si no hay fotos cargadas (se omite). Pregunta 1 |
| 3 | Galería: forma | `test_fuente_galeria.py::test_galeria_forma` | NO EJECUTADA |
| 3 | Solo personas con foto; sin fotos → `[]`; coincide con la fuente de personas | `::test_solo_personas_con_foto` | NO EJECUTADA |
| 3 | Versión estable | `::test_version_estable` | NO EJECUTADA |
| 3 | `version` cambia si cambia el conjunto de fotos | `::test_version_cambia_si_cambian_las_fotos` | **NO VERIFICADO** (marcada `skip`). Pregunta 1 |
| 4 | ≥ 200 placas, ≥ 20 con requisitoria vigente | `test_datos_sinteticos.py::test_volumen_de_placas`, `::test_placas_con_requisitoria` (recorre las 36 000 placas `ZZ?-???`) | NO EJECUTADA |
| 4 | Placas reservadas `ZZ` + regex | `::test_placas_reservadas`; lado negativo **por muestra** (1 005 placas fuera de `ZZ` → 404) `::test_muestra_fuera_de_zz_no_existe` | NO EJECUTADA. Probar que no existe **ninguna** placa fuera de `ZZ` no es posible por caja negra |
| 4 | Placas fijas `ZZA-101` / `ZZB-201` / `ZZZ-999` | `::test_placas_fijas` | NO EJECUTADA |
| 4 | 20 a 30 personas, `SIM-P-0001` existe, todas con requisitoria | `::test_volumen_de_personas`, `::test_todas_las_personas_cumplen_la_forma` | NO EJECUTADA |
| 4 | Documento `SIM-` + 8 dígitos | dentro de `problemas_persona` (todas las personas) | NO EJECUTADA |
| 4 | Datos deterministas entre arranques | `test_reinicio.py::test_mismos_datos_y_modos_normales_tras_reiniciar` (`--reinicio`) | NO EJECUTADA |
| 4 | La semilla es un archivo versionado de `services/simuladores/` | — | **NO VERIFICADO** por caja negra (exige mirar las rutas del DEV). Lo puede comprobar el LEAD en el veredicto |
| 4 | Sin imágenes en el repositorio | `test_repositorio.py` (extensión y firma de bytes sobre `git ls-files`) | **ROJO** — ver hallazgo H1 |
| 5 | `GET /control/modos` lista las tres fuentes | `test_modos_falla.py::test_get_control_modos_lista_las_tres_fuentes` | NO EJECUTADA |
| 5 | `PUT` de cada modo en cada fuente se refleja en el `GET` | `::test_put_modo_valido_se_refleja_en_get` (12 combinaciones) | NO EJECUTADA |
| 5 | Al arrancar, todo en `normal` | `test_reinicio.py` (`--reinicio`) | NO EJECUTADA |
| 5 | `normal` sin latencia artificial (< 1 s) | `::test_normal_sin_latencia_artificial` | NO EJECUTADA |
| 5 | `latencia` con `latencia_ms` y por defecto 5000 | `::test_latencia_configurable`, `::test_latencia_por_defecto_5000` | NO EJECUTADA |
| 5 | `error_500` en cada ruta de la fuente, código y mensaje exactos | `::test_error_500_en_cada_ruta` | NO EJECUTADA |
| 5 | `malformada` → 200 que no cumple la forma / no valida contra el yaml; ejemplo de placas | `::test_malformada`, `::test_malformada_placas_falta_campo_o_vigente_no_booleano`, `test_contratos_yaml.py::test_malformada_no_valida_contra_yaml` | NO EJECUTADA |
| 5 | Fuente inválida → 404 `FUENTE_DESCONOCIDA` | `::test_fuente_invalida` | NO EJECUTADA |
| 5 | Modo inválido → 422 `SOLICITUD_INVALIDA` | `::test_modo_invalido` | NO EJECUTADA |
| 5 | Aislamiento entre fuentes; `/salud` 200 en cualquier modo; volver a `normal` sin reiniciar | `::test_un_modo_no_altera_las_otras_fuentes`, `::test_salud_200_en_cualquier_modo`, `::test_volver_a_normal` | NO EJECUTADA |
| 6 | Existen y son OpenAPI 3.1 válidos | `test_contratos_yaml.py::test_existe`, `::test_openapi_31_valido` | Pendiente de corrida definitiva (el DEV trabaja en los yaml) |
| 6 | Campos, códigos de error, un ejemplo por respuesta JSON, tiempo de respuesta | `::test_documenta_los_campos`, `::test_documenta_los_codigos_de_error`, `::test_un_ejemplo_por_respuesta`, `::test_documenta_tiempo_de_respuesta`, `::test_rutas_del_contrato` | Pendiente |
| 6 | Respuestas 200 y 404 en `normal` validan contra el yaml | `::test_respuesta_normal_valida_contra_yaml`, `::test_foto_cargada_valida_contra_yaml` | NO EJECUTADA (`--integracion`). Si faltan las dependencias: NO VERIFICADO (indicación del LEAD) |
| 6 | Sin palabra prohibida | `::test_sin_palabra_prohibida` (yaml) y en cada fuente (respuestas) | Pendiente |
| 6 | `/control/*` fuera de los yaml | `::test_sin_ruta_de_control` | Pendiente |
| 7 | Mock generado solo desde el yaml valida contra el mismo contrato | `test_reemplazo_y_config.py::test_mock_desde_el_yaml_cumple_el_mismo_contrato` (Prism) | NO EJECUTADA |
| 7 | `FUENTE_*_URL` en `.env.example` con comentario | `::test_url_por_fuente_en_env_example_con_comentario` | Pendiente (el DEV trabaja en el archivo) |
| 7 | `FUENTE_TIMEOUT_S` = 3 en `.env.example` | `::test_timeout_por_defecto_3` | Pendiente |
| 7 | La API usa `FUENTE_*_URL` con `SIMULADORES_URL` de respaldo | — | **NO VERIFICADO** en HU-08: no es observable sin `/v1/consultas/placa` (decisión 1; se prueba en HU-03) |
| 8 | Sin puerto publicado | `test_aislamiento.py::test_simuladores_sin_puerto_publicado` (`docker compose config`) | NO EJECUTADA |
| 8 | El Caddyfile no enruta a `simuladores` | `::test_caddyfile_no_enruta_a_simuladores` | VERDE (corrida parcial) |
| 8 | `apps/movil/src/` sin `simuladores`, `8001`, `/placas/` | `::test_app_no_conoce_el_simulador` | **ROJO** — ver hallazgo H2 |
| 8 | Desde la API sí | `::test_desde_la_api_si` | NO EJECUTADA |
| 8 | `GET /v1/salud` intacta | Pruebas del Sprint 0 de la API: `docker compose -f infra/docker-compose.yml run --rm api pytest` | Verificable por comando |

## Hallazgos para que arbitre el LEAD

**H1 — Imágenes versionadas (§4 "Sin fotos en el repositorio": "Ningún archivo de imagen en el repositorio").** `git ls-files` incluye 6 PNG del Sprint 0: `apps/movil/assets/android-icon-background.png`, `android-icon-foreground.png`, `android-icon-monochrome.png`, `favicon.png`, `icon.png`, `splash-icon.png` (íconos de la app Expo, no rostros). El contrato dice "ningún archivo de imagen" sin excepción; AGENTS.md regla 8 dice "ninguna foto". La prueba quedó literal al contrato y sale roja. Que el contrato diga si los íconos de la app son excepción.

**H2 — `apps/movil/src/api/esquema.ts` contiene `simuladores`** (§8 "Ni la app"). La prueba busca el texto literal que fija el contrato, sin mirar el contexto. Que el LEAD decida si es una desviación del código o si el contrato debe precisar qué cuenta.

## Lo que el contrato no fija y por eso no verifico

- El código de estado de un `PUT /control/modos/{fuente}` válido: acepto cualquier 2xx.
- La forma interna de cada valor de `GET /control/modos` (`{...}`): solo exijo un objeto que refleje el modo puesto.
- `malformada` en la ruta de fotos (respuesta binaria): solo pruebo `error_500` en esa ruta.

## Preguntas abiertas (enviadas al LEAD el 2026-11-19)

1. Cómo y cuándo se cargan las fotos de `SIM_FOTOS_DIR` en pruebas → escalada al humano, llega en v2.
2. Dependencias para validar contra los yaml → se corren desde el anfitrión con `requirements-pruebas.txt`; sin ellas, NO VERIFICADO.
3. Docker Desktop no corre en este equipo → escalado al humano.

## Cambio sobre el Sprint 0

`test_salud_simuladores.py::test_sin_endpoints_de_fuentes` (SPRINT0 §6 "NO se crea") se retiró: desde HU-08 esas rutas existen por contrato. `conftest.py` se amplió (PUT, peticiones en lote, bytes de imagen) y mantiene la fixture `get_simuladores` del Sprint 0.
