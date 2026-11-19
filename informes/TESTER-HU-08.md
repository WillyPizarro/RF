# Informe TESTER — HU-08 Simuladores de fuentes

**Contrato:** `docs/contratos/CONTRATO-HU-08.md` **v4** · **Encargo:** `docs/contratos/ENCARGO-HU-08.md` (M-1 a M-3) · **Rama:** `hu-08`
**Estado:** pruebas ajustadas a la v4 (C1 a C7); **corrida definitiva pendiente** de la entrega del DEV de C5 y C6 (M-2). Docker ya está disponible. Los estados de abajo son de corridas parciales mientras se trabajaba; no son hallazgos.

## Cómo se corren

| Forma | Comando | Qué cubre |
|---|---|---|
| Dentro de la red (encargo, SPRINT0 §5) | `docker compose -f infra/docker-compose.yml run --rm simuladores pytest` | §1 a §6 por HTTP, más C5 y C6 (yaml en `CONTRATOS_FUENTES_DIR`). Se omiten las que leen `infra/`, `apps/` o git, y la carga de fotos |
| Anfitrión, sistema arrancado con fotos | `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env up -d --build`, luego `pip install -r services/simuladores/tests/requirements-pruebas.txt` y `pytest services/simuladores/tests --integracion` | **Todo el contrato**, incluida §4 bis: escribe un PNG generado en `SIM_FOTOS_ORIGEN` y lo borra. Las peticiones salen desde dentro del contenedor `api`, que es el camino que permite §8 |
| Además, determinismo | `pytest services/simuladores/tests --integracion --reinicio` | Reinicia `simuladores` (unos segundos sin servicio) |
| Mock de §7 | Incluido en `--integracion`; necesita `npx` (Node) y descarga `@stoplight/prism-cli@5` la primera vez | §7 "Segunda implementación" |

`requirements-pruebas.txt` (ruta del TESTER) es para el anfitrión. Dentro del contenedor, las dependencias las pone el DEV (C5).

## Caso del contrato → prueba

Archivos en `services/simuladores/tests/`. Las formas que exige el contrato están escritas desde el contrato en `ayudas_contrato.py`.

| § | Caso | Prueba | Estado |
|---|---|---|---|
| 1 | Placa con requisitoria (`ZZA-101`) | `test_fuente_placas.py::test_placa_con_requisitoria` | VERDE (parcial) |
| 1 | Placa sin requisitoria (`ZZB-201`), misma forma | `::test_placa_sin_requisitoria`, `::test_misma_forma_con_y_sin_requisitoria` | VERDE (parcial) |
| 1 | Placa no registrada → 404 `PLACA_NO_REGISTRADA` + mensaje exacto | `::test_placa_no_registrada` | VERDE (parcial) |
| 1 | Minúsculas → 404 (no normaliza) | `::test_minusculas_no_se_normalizan` | VERDE (parcial) |
| 1 | El simulador no valida el formato (no está → 404) | `::test_formato_invalido_no_se_valida_en_el_simulador` | VERDE (parcial) |
| 2 | Persona con requisitoria (`SIM-P-0001`) | `test_fuente_personas.py::test_persona_con_requisitoria` | VERDE (parcial) |
| 2 | Persona no registrada → 404 `PERSONA_NO_REGISTRADA` | `::test_persona_no_registrada` | VERDE (parcial) |
| 2 | Foto no cargada → 404 `FOTO_NO_DISPONIBLE` | `::test_foto_no_cargada` | VERDE (parcial) |
| 2 | Foto cargada → 200 `image/png`, bytes descifrados | `::test_fotos_cargadas_se_sirven_como_imagen` (fotos ya cargadas) y `test_carga_fotos.py::test_agregar_cambiar_y_quitar_una_foto` (bytes servidos = bytes escritos) | Pendiente. JPEG: **NO VERIFICADO** (generarlo exige una biblioteca de imágenes) |
| 3 | Galería: forma | `test_fuente_galeria.py::test_galeria_forma` | VERDE (parcial) |
| 3 | Solo personas con foto; sin fotos → `[]`; coincide con la fuente de personas | `::test_solo_personas_con_foto` | VERDE (parcial) |
| 3 | Versión estable | `::test_version_estable` | VERDE (parcial) |
| 3 | `version` cambia si cambian las fotos | `test_carga_fotos.py::test_agregar_cambiar_y_quitar_una_foto` (agregar, cambiar, quitar) | Pendiente |
| 4 | ≥ 200 placas, ≥ 20 con requisitoria vigente | `test_datos_sinteticos.py::test_volumen_de_placas`, `::test_placas_con_requisitoria` (recorre las 36 000 placas `ZZ?-???`) | Pendiente |
| 4 | Placas reservadas `ZZ` + regex | `::test_placas_reservadas`; lado negativo **por muestra** (1 005 placas fuera de `ZZ` → 404) `::test_muestra_fuera_de_zz_no_existe` | Pendiente. Probar que no existe **ninguna** placa fuera de `ZZ` no es posible por caja negra |
| 4 | Placas fijas `ZZA-101` / `ZZB-201` / `ZZZ-999` | `::test_placas_fijas` | Pendiente |
| 4 | 20 a 30 personas, `SIM-P-0001` existe, todas con requisitoria, documento `SIM-` + 8 dígitos | `::test_volumen_de_personas`, `::test_todas_las_personas_cumplen_la_forma` | Pendiente |
| 4 | Datos deterministas entre arranques | `test_reinicio.py` (`--reinicio`) | Pendiente |
| 4 | La semilla es un archivo versionado de `services/simuladores/` | — | **NO VERIFICADO** por caja negra (exige mirar las rutas del DEV). Lo puede comprobar el LEAD en el veredicto |
| 4 | Sin imágenes versionadas fuera de `apps/movil/assets/` (v2 C3) | `test_repositorio.py` (extensión y firma de bytes sobre `git ls-files`) | VERDE (parcial) |
| 4 bis | Origen: `SIM_FOTOS_DIR=/fotos-origen`, montado desde `SIM_FOTOS_ORIGEN` (fuera del repositorio) con `docker-compose.fotos.yml` | `test_carga_fotos.py::test_origen_montado_en_fotos_origen`, fixture `origen` | Pendiente |
| 4 bis | Nombre `<persona_id>__<n>.png`, `foto_id` = `<persona_id>__<n>`; nombres inválidos y personas inexistentes se ignoran | `::test_agregar_cambiar_y_quitar_una_foto`, `::test_nombres_que_no_cumplen_se_ignoran` (6 nombres) | Pendiente |
| 4 bis | Se carga en cada solicitud, sin reiniciar: aparece, cambia y desaparece en las tres rutas | `::test_agregar_cambiar_y_quitar_una_foto` | Pendiente |
| 4 bis | `version` igual entre reinicios con las mismas fotos y llave | `test_reinicio.py` (`--reinicio`). Con `SIM_FOTOS_LLAVE` vacía la llave es aleatoria y no se exige | Pendiente |
| 4 bis | Fotos cifradas en el volumen | `test_carga_fotos.py::test_foto_guardada_cifrada`: mete una marca única en el PNG y la busca en todo el sistema de archivos del contenedor salvo `/fotos-origen`. No debe aparecer en claro | Pendiente. El algoritmo y la llave quedan fuera del contrato |
| 5 | Lectura (C4): `GET /control/modos` → 200, tres claves, `{"modo","latencia_ms"}` | `test_modos_falla.py::test_get_control_modos_lista_las_tres_fuentes` | Pendiente |
| 5 | Cambio válido (C4): `PUT` → 200 `{"modo","latencia_ms"}` (`null` salvo en `latencia`, por defecto 5000), y se refleja en el `GET` | `::test_put_modo_valido_responde_y_se_refleja_en_get` (15 combinaciones) | Pendiente |
| 5 | Al arrancar, todo en `normal` | `test_reinicio.py` (`--reinicio`) | Pendiente |
| 5 | `normal` sin latencia artificial (< 1 s) | `::test_normal_sin_latencia_artificial` | Pendiente |
| 5 | `latencia` con `latencia_ms` y por defecto 5000 | `::test_latencia_configurable`, `::test_latencia_por_defecto_5000` | Pendiente |
| 5 | `error_500` en cada ruta de la fuente, código y mensaje exactos | `::test_error_500_en_cada_ruta` | Pendiente |
| 5 | `malformada` → 200 que no cumple la forma ni valida contra el yaml | `::test_malformada`, `::test_malformada_placas_falta_campo_o_vigente_no_booleano`, `test_contratos_yaml.py::test_malformada_no_valida_contra_yaml` | Pendiente |
| 5 | Fuente inválida → 404 `FUENTE_DESCONOCIDA` | `::test_fuente_invalida` | Pendiente |
| 5 | Modo inválido → 422 `SOLICITUD_INVALIDA` | `::test_modo_invalido` | Pendiente |
| 5 | Aislamiento entre fuentes; `/salud` 200 en cualquier modo; volver a `normal` sin reiniciar | `::test_un_modo_no_altera_las_otras_fuentes`, `::test_salud_200_en_cualquier_modo`, `::test_volver_a_normal` | Pendiente |
| C5 | `pyyaml` y `jsonschema` dentro del contenedor | `test_herramientas.py::test_c5_dependencias_de_prueba_en_el_contenedor` | Pendiente (trabajo del DEV, M-2) |
| C6 | Yaml montados en solo lectura en `/app/contratos/fuentes`, con `CONTRATOS_FUENTES_DIR` | `test_herramientas.py::test_c6_*` (dentro del contenedor y en `docker compose config`) | Pendiente (trabajo del DEV, M-2) |
| 6 | Existen y son OpenAPI 3.1 válidos | `test_contratos_yaml.py::test_existe`, `::test_openapi_31_valido` (el validador completo, solo en el anfitrión) | VERDE (parcial, anfitrión) |
| 6 | Campos, códigos de error, un ejemplo por respuesta JSON, tiempo de respuesta | `::test_documenta_los_campos`, `::test_documenta_los_codigos_de_error`, `::test_un_ejemplo_por_respuesta`, `::test_documenta_tiempo_de_respuesta`, `::test_rutas_del_contrato` | VERDE (parcial, anfitrión) |
| 6 | Respuestas 200 y 404 en `normal` validan contra el yaml | `::test_respuesta_normal_valida_contra_yaml`, `::test_foto_cargada_valida_contra_yaml` | Pendiente |
| 6 | Sin palabra prohibida | `::test_sin_palabra_prohibida` (yaml) y en cada fuente (respuestas) | VERDE (parcial) |
| 6 | `/control/*` fuera de los yaml | `::test_sin_ruta_de_control` | VERDE (parcial, anfitrión) |
| 7 | Mock generado solo desde el yaml valida contra el mismo contrato | `test_reemplazo_y_config.py::test_mock_desde_el_yaml_cumple_el_mismo_contrato` (Prism) | Pendiente |
| 7 | `FUENTE_*_URL` en `.env.example` con comentario | `::test_url_por_fuente_en_env_example_con_comentario` | VERDE (parcial) |
| 7 | `FUENTE_TIMEOUT_S` = 3 en `.env.example` | `::test_timeout_por_defecto_3` | VERDE (parcial) |
| 7 | La API usa `FUENTE_*_URL` con `SIMULADORES_URL` de respaldo | — | **NO VERIFICADO** en HU-08: no es observable sin `/v1/consultas/placa` (decisión 1; se prueba en HU-03) |
| 8 | Sin puerto publicado | `test_aislamiento.py::test_simuladores_sin_puerto_publicado` (`docker compose config`) | Pendiente |
| 8 | El Caddyfile no enruta a `simuladores` | `::test_caddyfile_no_enruta_a_simuladores` | VERDE (parcial) |
| 8 | `apps/movil/src/` sin los textos exactos `//simuladores`, `simuladores:8001`, `:8001`, `/placas/` (C7) | `::test_app_no_conoce_el_simulador` | VERDE (parcial) |
| 8 | Desde la API sí | `::test_desde_la_api_si` | Pendiente |
| 8 | `GET /v1/salud` intacta | Pruebas del Sprint 0 de la API: `docker compose -f infra/docker-compose.yml run --rm api pytest` | Verificable por comando |

## Hallazgos resueltos por el contrato

- **H1** (PNG de `apps/movil/assets/`): v2 C3 los excluye, y la prueba también.
- **H2** (`simuladores` en `apps/movil/src/api/esquema.ts`): v2 C2 y v4 C7 fijan los textos exactos, y la prueba usa los de la v4.
- `/control/modos` sin forma fija → C4. Fotos → C1. Dependencias y montaje de los yaml → C5 y C6.

## Lo que el contrato no fija y por eso no verifico

- `malformada` en la ruta de fotos (respuesta binaria): en esa ruta solo pruebo `error_500`.

## Arreglo del arnés

Con `docker compose run --rm simuladores pytest`, el contenedor de pruebas también recibe el alias de red `simuladores`, así que ese nombre puede resolver al propio contenedor, donde no corre el servidor. El resultado era `Connection refused` intermitente, y ya pasaba con el arnés del Sprint 0. Ahora `conftest.py` descarta las direcciones propias y usa la del servicio. Con el arreglo, el subconjunto de §1 a §3 dentro del contenedor da 21 en verde y 2 omitidas (fotos no cargadas).

## Cambio sobre el Sprint 0

Se retiró `test_salud_simuladores.py::test_sin_endpoints_de_fuentes` (SPRINT0 §6 "NO se crea"): desde HU-08 esas rutas existen por contrato. Se amplió `conftest.py` (PUT, peticiones en lote, bytes de imagen, alias de red) y se mantiene la fixture `get_simuladores` del Sprint 0.
