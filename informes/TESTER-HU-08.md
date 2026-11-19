# Informe TESTER — HU-08 Simuladores de fuentes

**Contrato:** `docs/contratos/CONTRATO-HU-08.md` **v4** · **Encargo:** `docs/contratos/ENCARGO-HU-08.md` (M-1 a M-4) · **Rama:** `hu-08`
**Vuelta 1 (M-5):** ver la sección del mismo nombre.
**Corrida definitiva (M-4):** 2026-11-19, sobre la punta de `hu-08` (`bfacf34`, que incluye el commit definitivo del DEV `d08b907` y mis pruebas `8f3b8a5`). Imágenes reconstruidas con `up -d --build`, arrancadas con `infra/docker-compose.fotos.yml`. `SIM_FOTOS_ORIGEN` apunta a una carpeta fuera del repositorio y `SIM_FOTOS_LLAVE` está definida, las dos en `infra/.env` local (no versionado).

## Resultado

| Corrida | Comando | Resultado |
|---|---|---|
| Dentro de la red | `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env run --rm -T simuladores pytest -rA` | **115 en verde, 0 rojos, 28 omitidas.** Las omitidas leen el repositorio o docker y se cubren en la corrida del anfitrión; además, 3 de `openapi-spec-validator`, que no forma parte de C5 |
| Anfitrión, todo el contrato | `pytest services/simuladores/tests --integracion --reinicio -rA` (con `requirements-pruebas.txt`) | **136 en verde, 0 rojos, 7 omitidas** (7 min 55 s). Las omitidas: 4 de `test_herramientas.py` que solo corren dentro del contenedor (allí, en verde), y 3 que se describen abajo |

**Ningún caso del contrato quedó en rojo.** Las imágenes de prueba se generaron en tiempo de ejecución y se borraron: la carpeta de origen quedó vacía al terminar. No se versionó ninguna.

Las 3 omitidas del anfitrión que no eran de C5/C6 (estado de la corrida de M-4; la vuelta 1 de abajo las resuelve):
- `test_fuente_personas.py::test_fotos_cargadas_se_sirven_como_imagen`: recorre las fotos que ya estén en el origen. Sigue omitiéndose por diseño cuando el origen está vacío; el caso lo cubre `test_carga_fotos.py`.
- `test_contratos_yaml.py::test_foto_cargada_valida_contra_yaml` y `test_fuente_galeria.py::test_version_cambia_si_cambian_las_fotos`: corregidas en la vuelta 1 (A1).

## Vuelta 1 del veredicto (M-5, arbitraje A1: se apartó la prueba)

- **A1:** la validación de una foto cargada contra `requisitorias-personas.yaml` pasó a `test_carga_fotos.py::test_foto_cargada_valida_contra_yaml`. La prueba carga su propia foto (PNG generado en tiempo de ejecución), valida la respuesta `200` de `/personas/{id}/fotos/{foto_id}` contra el yaml (estado y `Content-Type` documentados, bytes = los escritos) y valida también la ficha `/personas/{id}` con esa foto en `foto_ids`. Se quitó la versión de `test_contratos_yaml.py`, que dependía de fotos precargadas.
- **Skips obsoletos:** se borró el esqueleto `test_fuente_galeria.py::test_version_cambia_si_cambian_las_fotos` (lo cubre `test_carga_fotos.py::test_agregar_cambiar_y_quitar_una_foto`), y se actualizó el motivo de `test_fuente_personas.py:48`.
- **Arnés:** el fixture `origen` ahora comprueba que el contenedor `simuladores` en marcha tenga `/fotos-origen` montado y, si no, falla con un mensaje claro. Pasó en esta vuelta: el contenedor se había recreado sin `docker-compose.fotos.yml` y las pruebas de fotos daban 404 sin explicar por qué. Se volvió a arrancar con `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env up -d simuladores`.
- **Corrida de lo tocado:** anfitrión `pytest services/simuladores/tests/{test_carga_fotos,test_fuente_galeria,test_fuente_personas,test_contratos_yaml}.py --integracion` → **58 en verde, 0 rojos, 1 omitida** (la de fotos precargadas, por diseño). Contenedor (`run --rm simuladores pytest` de esos cuatro archivos) → **45 en verde, 0 rojos, 14 omitidas** (las de anfitrión). El origen quedó vacío.

## Caso del contrato → prueba → estado

Archivos en `services/simuladores/tests/`. Las formas que exige el contrato están escritas desde el contrato en `ayudas_contrato.py`.

| § | Caso | Prueba | Estado |
|---|---|---|---|
| 1 | Placa con requisitoria (`ZZA-101`) | `test_fuente_placas.py::test_placa_con_requisitoria` | VERDE |
| 1 | Placa sin requisitoria (`ZZB-201`), misma forma | `::test_placa_sin_requisitoria`, `::test_misma_forma_con_y_sin_requisitoria` | VERDE |
| 1 | Placa no registrada → 404 `PLACA_NO_REGISTRADA` + mensaje exacto | `::test_placa_no_registrada` | VERDE |
| 1 | Minúsculas → 404 (no normaliza) | `::test_minusculas_no_se_normalizan` | VERDE |
| 1 | El simulador no valida el formato (no está → 404) | `::test_formato_invalido_no_se_valida_en_el_simulador` | VERDE |
| 2 | Persona con requisitoria (`SIM-P-0001`) | `test_fuente_personas.py::test_persona_con_requisitoria` | VERDE |
| 2 | Persona no registrada → 404 `PERSONA_NO_REGISTRADA` | `::test_persona_no_registrada` | VERDE |
| 2 | Foto no cargada → 404 `FOTO_NO_DISPONIBLE` | `::test_foto_no_cargada` | VERDE |
| 2 | Foto cargada → 200 `image/png`, bytes descifrados (bytes servidos = bytes escritos) | `test_carga_fotos.py::test_agregar_cambiar_y_quitar_una_foto` | VERDE en PNG. JPEG: **NO VERIFICADO** (generarlo exige una biblioteca de imágenes) |
| 3 | Galería: forma | `test_fuente_galeria.py::test_galeria_forma` | VERDE |
| 3 | Solo personas con foto; sin fotos → `[]`; coincide con la fuente de personas | `::test_solo_personas_con_foto` | VERDE |
| 3 | Versión estable | `::test_version_estable` | VERDE |
| 3 | `version` cambia si cambian las fotos (agregar, cambiar, quitar) | `test_carga_fotos.py::test_agregar_cambiar_y_quitar_una_foto` | VERDE |
| 4 | ≥ 200 placas, ≥ 20 con requisitoria vigente | `test_datos_sinteticos.py::test_volumen_de_placas`, `::test_placas_con_requisitoria` (recorre las 36 000 placas `ZZ?-???`) | VERDE |
| 4 | Cada placa cumple la forma y `es_sintetico` | `::test_cada_placa_cumple_la_forma` | VERDE |
| 4 | Placas reservadas `ZZ` + regex | `::test_placas_reservadas`; lado negativo **por muestra** (1 005 placas fuera de `ZZ` → 404) `::test_muestra_fuera_de_zz_no_existe` | VERDE. Que no exista **ninguna** placa fuera de `ZZ` no se puede probar por caja negra |
| 4 | Placas fijas `ZZA-101` / `ZZB-201` / `ZZZ-999` | `::test_placas_fijas` | VERDE |
| 4 | 20 a 30 personas, `SIM-P-0001` existe, todas con requisitoria, documento `SIM-` + 8 dígitos | `::test_volumen_de_personas`, `::test_todas_las_personas_cumplen_la_forma` | VERDE |
| 4 | Mismos datos en cada arranque | `test_reinicio.py::test_mismos_datos_y_modos_normales_tras_reiniciar`: compara todas las placas y personas, y `/galeria` con su `version`, antes y después de `docker compose restart simuladores` | VERDE |
| 4 | La semilla es un archivo versionado de `services/simuladores/` | — | **NO VERIFICADO** por caja negra (exige mirar las rutas del DEV). Lo puede comprobar el LEAD en el veredicto |
| 4 | Sin imágenes versionadas fuera de `apps/movil/assets/` (C3) | `test_repositorio.py` (extensión y firma de bytes sobre `git ls-files`) | VERDE |
| 4 bis | Origen `/fotos-origen`, montado desde `SIM_FOTOS_ORIGEN` (fuera del repositorio) | `test_carga_fotos.py::test_origen_montado_en_fotos_origen`, fixture `origen` | VERDE |
| 4 bis | Nombre `<persona_id>__<n>.png` y `foto_id` = `<persona_id>__<n>` | `::test_agregar_cambiar_y_quitar_una_foto` | VERDE |
| 4 bis | Se ignoran los nombres inválidos y las personas inexistentes | `::test_nombres_que_no_cumplen_se_ignoran` (`basura.png`, `SIM-P-9999__1.png`, `SIM-P-0001_1.png`, `SIM-P-0001__x.png`, `SIM-P-0001__1.gif`, `sim-p-0001__1.png`) | VERDE |
| 4 bis | Se carga en cada solicitud, sin reiniciar: aparece, cambia y desaparece en las tres rutas | `::test_agregar_cambiar_y_quitar_una_foto` | VERDE |
| 4 bis | `version` igual entre reinicios con las mismas fotos y llave | `test_reinicio.py` (con `SIM_FOTOS_LLAVE` definida) | VERDE |
| 4 bis | Fotos cifradas en el volumen | `test_carga_fotos.py::test_foto_guardada_cifrada`: mete una marca única en el PNG y la busca en todo el sistema de archivos del contenedor salvo `/fotos-origen`, `/proc`, `/sys` y `/dev`. No aparece | VERDE. El algoritmo y la llave quedan fuera del contrato |
| 5 | Lectura (C4): `GET /control/modos` → 200, tres claves, `{"modo","latencia_ms"}` | `test_modos_falla.py::test_get_control_modos_lista_las_tres_fuentes` | VERDE |
| 5 | Cambio válido (C4): `PUT` → 200 `{"modo","latencia_ms"}` (`null` salvo en `latencia`, por defecto 5000), y se refleja en el `GET` | `::test_put_modo_valido_responde_y_se_refleja_en_get` (15 combinaciones) | VERDE |
| 5 | Al arrancar, todo en `normal` | `test_reinicio.py` (pone las tres en `error_500`, reinicia y lee) | VERDE |
| 5 | `normal` sin latencia artificial (< 1 s) | `::test_normal_sin_latencia_artificial` | VERDE |
| 5 | `latencia` con `latencia_ms` (1500) y por defecto 5000 | `::test_latencia_configurable`, `::test_latencia_por_defecto_5000` | VERDE |
| 5 | `error_500` en cada ruta de la fuente, código y mensaje exactos | `::test_error_500_en_cada_ruta` | VERDE |
| 5 | `malformada` → 200 que no cumple la forma ni valida contra el yaml | `::test_malformada`, `::test_malformada_placas_falta_campo_o_vigente_no_booleano`, `test_contratos_yaml.py::test_malformada_no_valida_contra_yaml` | VERDE |
| 5 | Fuente inválida → 404 `FUENTE_DESCONOCIDA` | `::test_fuente_invalida` (`otra`, `personas`, `PLACAS`) | VERDE |
| 5 | Modo inválido → 422 `SOLICITUD_INVALIDA`, y la fuente no cambia | `::test_modo_invalido` (4 cuerpos) | VERDE |
| 5 | Aislamiento entre fuentes; `/salud` 200 en cualquier modo; volver a `normal` sin reiniciar | `::test_un_modo_no_altera_las_otras_fuentes`, `::test_salud_200_en_cualquier_modo`, `::test_volver_a_normal` | VERDE |
| C5 | `pyyaml` y `jsonschema` dentro del contenedor | `test_herramientas.py::test_c5_dependencias_de_prueba_en_el_contenedor` | VERDE |
| C6 | Yaml en `/app/contratos/fuentes` (solo lectura), con `CONTRATOS_FUENTES_DIR` | `test_herramientas.py::test_c6_variable_y_yaml_montados`, `::test_c6_montaje_de_solo_lectura` (contenedor), `::test_c6_en_el_compose` (anfitrión) | VERDE |
| 6 | Existen y son OpenAPI 3.1 válidos | `test_contratos_yaml.py::test_existe`, `::test_openapi_31_valido` (validador completo en el anfitrión) | VERDE |
| 6 | Rutas, campos, códigos de error, un ejemplo por respuesta JSON, tiempo de respuesta | `::test_rutas_del_contrato`, `::test_documenta_los_campos`, `::test_documenta_los_codigos_de_error`, `::test_un_ejemplo_por_respuesta`, `::test_documenta_tiempo_de_respuesta` | VERDE |
| 6 | Respuestas 200 y 404 en `normal` validan contra el yaml | `::test_respuesta_normal_valida_contra_yaml` (8 respuestas, en el contenedor y en el anfitrión) | VERDE |
| 6 | Foto cargada (200 de `/fotos/{foto_id}`) valida contra el yaml | `test_carga_fotos.py::test_foto_cargada_valida_contra_yaml` (vuelta 1, A1) | VERDE |
| 6 | Sin palabra prohibida | `::test_sin_palabra_prohibida` (yaml) y en las respuestas de cada fuente | VERDE |
| 6 | `/control/*` fuera de los yaml | `::test_sin_ruta_de_control` | VERDE |
| 7 | Mock generado solo desde el yaml valida contra el mismo contrato | `test_reemplazo_y_config.py::test_mock_desde_el_yaml_cumple_el_mismo_contrato` (`@stoplight/prism-cli@5`) | VERDE |
| 7 | `FUENTE_*_URL` en `.env.example` con comentario | `::test_url_por_fuente_en_env_example_con_comentario` | VERDE |
| 7 | `FUENTE_TIMEOUT_S` = 3 en `.env.example` | `::test_timeout_por_defecto_3` | VERDE |
| 7 | La API usa `FUENTE_*_URL` con `SIMULADORES_URL` de respaldo | — | **NO VERIFICADO** en HU-08: no es observable sin `/v1/consultas/placa` (decisión 1; se prueba en HU-03) |
| 8 | Sin puerto publicado | `test_aislamiento.py::test_simuladores_sin_puerto_publicado` (`docker compose config`) | VERDE |
| 8 | El Caddyfile no enruta a `simuladores` | `::test_caddyfile_no_enruta_a_simuladores` | VERDE |
| 8 | `apps/movil/src/` sin los textos exactos `//simuladores`, `simuladores:8001`, `:8001`, `/placas/` (C7) | `::test_app_no_conoce_el_simulador` | VERDE |
| 8 | Desde la API sí | `::test_desde_la_api_si` (petición hecha dentro del contenedor `api`) | VERDE |
| 8 | `GET /v1/salud` intacta | `services/api/tests/test_salud.py --integracion` (Sprint 0) | **NO VERIFICADO (entorno):** el servicio `proxy` no arrancó porque el puerto 80 del equipo lo ocupa el sistema (PID 4, `http.sys` de Windows): `bind: An attempt was made to access a socket in a way forbidden by its access permissions`. Las pruebas de salud llegan por el proxy y fallan por tiempo de espera (`/v1/salud no volvió a 200 en 90s (última: None)`). No es un resultado del código; hay que repetirla con el puerto 80 libre |

## Hallazgos resueltos por el contrato durante el ciclo

- **H1** (PNG de `apps/movil/assets/`) → v2 C3. **H2** (`simuladores` en `esquema.ts`) → v2 C2 y v4 C7.
- Forma de `/control/modos` → C4. Carga de fotos → C1. Dependencias y montaje de los yaml → C5 y C6.

## Lo que el contrato no fija y por eso no verifico

- `malformada` en la ruta de fotos (respuesta binaria): en esa ruta solo pruebo `error_500`.

## Arreglo del arnés

Con `docker compose run --rm simuladores pytest`, el contenedor de pruebas también recibe el alias de red `simuladores`, así que ese nombre puede resolver al propio contenedor, donde no corre el servidor. El resultado era `Connection refused` intermitente, y ya pasaba con el arnés del Sprint 0. Ahora `conftest.py` descarta las direcciones propias y usa la del servicio.

## Cambio sobre el Sprint 0

Se retiró `test_salud_simuladores.py::test_sin_endpoints_de_fuentes` (SPRINT0 §6 "NO se crea"): desde HU-08 esas rutas existen por contrato. Se amplió `conftest.py` (PUT, peticiones en lote, bytes de imagen, alias de red) y se mantiene la fixture `get_simuladores` del Sprint 0.
