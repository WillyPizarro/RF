# VEREDICTO PARCIAL — DESPLIEGUE-01, fase B1 (NGINX local, descarga del APK y verificación de red de ML Kit)

**Veredicto: VERDE para B1.** La fase B2 (el VPS) queda **NO VERIFICADA** y sigue en una rama aparte.
**Fecha:** 2026-11-25 · **LEAD**
**Contrato:** `docs/contratos/CONTRATO-DESPLIEGUE-01.md` **v2.2**, con la anotación `DESCARGA_APK_DIR`. **Encargo:** M-1 a M-6 (M-6 puntos 1 a 8).
**Rama y commit evaluado:** `despliegue-01` @ `6f870ad`, rebasada sobre `main` `889a91b`.
**Lo que va a `main`:** la rama completa en `6f870ad`, por decisión del humano (vía PM, 2026-11-25: opción B, merge de B1). Lo del VPS ya está escrito, pero **no tiene efecto en local** y su verificación es la fase B2 (ver "NO VERIFICADO"). No hay nada a medias.

## 1. Entregas

| Rol | Entrega | Commit |
|---|---|---|
| DEV | Fase A: compose del VPS, `desplegar.ps1` y `docs/despliegue/` | `297dc61` |
| DEV | B1: NGINX `1.30.8-alpine` + openssl, CA local, `certbot` para el VPS, `/descargas/movil-buscador.apk` con basic auth, `publicar-apk.ps1`, sin EAS ni Caddy | `71b5ef0` |
| TESTER | Fase A (VPS, se omite sin `URL_VPS`), M-3 y M-4 (NGINX local), regresión 78/78 y guion | `ef8917d`, `1e7e41f`, `4ce5e65`, `67a39e2`, `ca73d42` |
| TESTER | Informe de la sesión 1 del teléfono | `46c4088`, `8a86df5` |

Los dos trabajaron sobre la misma versión del contrato: v2.1 en la entrega y v2.2 en el criterio "Sin EAS", aplicado sin cambiar el código ni las pruebas (`ca73d42`).

## 2. Corridas del LEAD (no se confía en los informes)

Todas sobre `6f870ad`, con el compose arriba desde `-despliegue` y NGINX como `proxy`.

| Corrida | Resultado |
|---|---|
| Regresión B1 del TESTER (`test_proxy_nginx.py`, `test_hu04_sin_cache.py`, la clave fuera de los logs del proxy y `test_compose_vps.py`) | **78 passed** en 31,6 s |
| Suite completa de la API (`services/api/tests --integracion`) | **257 passed, 23 skipped, 1 failed** en 617,8 s |
| El rojo, repetido solo (`test_hu01_bloqueo.py`, el archivo entero) | **10 passed** en 133,5 s |

**El rojo:** `test_hu01_bloqueo.py::test_valores_por_defecto_5_intentos_15_min` dio `401` en el 5.º fallo, donde esperaba `423`. Solo, el archivo pasa entero. El código de bloqueo de HU-01 no está en la rama (B1 no lo toca: `git diff main...despliegue-01` no incluye `services/api/app/` salvo `supabase_auth.py`, que es la URL de Auth). Lo leo como una **inestabilidad de la suite completa**: la prueba recrea `api` con la configuración por defecto y depende del orden y del tiempo. **No es un rojo de B1.** Queda como hallazgo para el TESTER (§5).

Las 23 omitidas son las pruebas contra el VPS (`URL_VPS` sin definir) y las que dependen de un modo del entorno.

## 3. Resultado por caso del contrato

| § | Caso | Prueba o evidencia | Resultado |
|---|---|---|---|
| 1 | Servicios, puertos, salud, mismo comportamiento **en el VPS** | `test_despliegue_vps.py` (se omite) | NO VERIFICADO (B2) |
| 1 | Solo `/v1/*` y el APK; 404 al resto | `test_rutas_fuera_de_v1_y_del_apk_dan_404`, `test_v1_sigue_llegando_a_la_api` (local) | 🟢 local · VPS en B2 |
| 1 | El servicio se sigue llamando `proxy` | Comandos `logs proxy` de la regresión y de la sesión 1 | 🟢 |
| 2 | Certificado de Let's Encrypt con `certbot` y renovación | — | NO VERIFICADO (B2) |
| 2 | HTTP → HTTPS | `test_http_redirige_a_https` | 🟢 local |
| 2 | Solo TLS 1.2 y 1.3 | `test_tls_12_y_13_completan`, `test_tls_10_y_11_no_completan` | 🟢 |
| 2 | Cabeceras de seguridad | `test_cabeceras_de_seguridad_en_toda_respuesta` | 🟢 |
| 2 | Cabeceras hacia la API | Suite de la API sin cambios (257 verdes) | 🟢 |
| 2 | Cuerpo máximo de 5 MB | `test_cuerpo_de_mas_de_5_mb_recibe_413_del_proxy`, `test_cuerpo_de_menos_de_5_mb_llega_a_la_api` | 🟢 |
| 2 | Registro sin secretos | `test_la_clave_no_queda_en_los_logs_del_proxy`, `test_la_credencial_de_la_descarga_no_queda_en_los_logs_del_proxy` y la a.9 de la sesión 1 (0 coincidencias) | 🟢 local |
| 2 | Local: NGINX con la CA local | Sesión 1 (a): CA `14:74:99:F3…98:D2` en el S23, login de agente1 y `ZZA-101` → PLA-05 por NGINX, HTTP/2 y OkHttp | 🟢 |
| 2 | Imagen oficial `nginx` con versión fijada | `test_proxy_es_nginx_con_version_fijada`, `test_proxy_del_vps_es_nginx_fijado` (arbitraje M-4) | 🟢 |
| 2 | Caddy desaparece | `test_no_queda_el_caddyfile` y la sesión 1 (a.1, a.2: CA y volúmenes de Caddy borrados) | 🟢 |
| 3 | Migraciones, `api_app`, solo inserción, Auth y usuarios **en Supabase** | `test_despliegue_vps.py` (se omite) | NO VERIFICADO (B2) |
| 3 | La credencial de administración, solo para la carga | `test_la_api_no_recibe_credenciales_de_administracion` (compose del VPS) | 🟢 configuración · ejecución en B2 |
| 4 | Secretos fuera del repositorio | `.gitignore` y `.env.example` (revisados en la regresión) | 🟢 |
| 4 | La clave no queda en los logs **del VPS** | — | NO VERIFICADO (B2) |
| 4 | Solo datos sintéticos; nada en el teléfono | Suite de la API · `test_sin_fotos_ni_pruebas_montadas` · CONTRATO-MIGRACION-FLUTTER | 🟢 |
| 5 | Sin credencial → 401 Basic · credencial incorrecta → 401 · con credencial → 200 y el mismo SHA-256 | `test_descarga_sin_credencial_401_con_basic`, `test_descarga_con_credencial_incorrecta_401`, `test_descarga_con_credencial_200_y_mismo_sha256` | 🟢 local |
| 5 | Otras rutas de `/descargas/` → 404 | `test_otras_rutas_de_descargas_dan_404_tambien_con_credencial` | 🟢 |
| 5 | Volumen de solo lectura | `test_volumen_de_la_descarga_es_de_solo_lectura`, `test_descarga_del_apk_de_solo_lectura_en_el_proxy` | 🟢 |
| 5 | Solo por HTTPS · la clave no queda en los logs | `test_http_redirige_a_https` · prueba de la credencial en los logs | 🟢 local |
| 5 | `htpasswd` generado en el arranque | La descarga con credencial funciona en local (`DESCARGA_APK_USUARIO` y `DESCARGA_APK_CLAVE`) | 🟢 local |
| 5 | El APK no se versiona | `.gitignore` y `git ls-files` sin `.apk` | 🟢 |
| 5 | Build de release no depurable | Entrega DEV de la migración (release `48f8117a`, `65799fb6`) | 🟢 (heredado de MIGRACION v1.5) |
| 5 | **Funciona sin cable** (descarga e instalación en el S23) | Guion, sección (d) | NO VERIFICADO (sesión 2, B2) |
| 6 | `desplegar.ps1` y `publicar-apk.ps1` contra el VPS, idempotentes | — | NO VERIFICADO (B2) |
| 6 | Sin EAS (v2.2) | `git grep -niw eas -- apps/movil docs/despliegue` → solo `apps/movil/test/repositorio_test.dart`, la excepción aceptada | 🟢 |
| 7 | Guía para probadores, dominio y manual | `docs/despliegue/` escritos; el dominio está pendiente | 🟢 escrito · el dominio en B2 |
| 8 | Borrado al cierre | Acta parcial de la sesión 1 (M-6 punto 8) | En curso (al cierre del MVP) |
| M-3 | Verificación de red de ML Kit, niveles 1 y 2 | Sesión 1 (b) y (c), informe del TESTER §5. Nivel 1: la app solo se conecta a `firebaselogging.googleapis.com`, y solo con el job forzado; desde gms solo `mtalk` (FCM). Nivel 2: JSON con gzip, sin imagen ni `ZZ`. Evaluación del ARCH en `5930ddc`, mergeada a `main` en `739db3a` | 🟢 |

## 4. Propiedad de rutas

`git log main..despliegue-01 --name-only`, agrupado por prefijo:

- **[DEV]** `infra/`, `scripts/`, `docs/despliegue/`, `services/api/app/supabase_auth.py`, `informes/DEV-*`, `README.md`, `.gitignore` y `apps/movil/eas.json` (borrado): todo en sus rutas.
- **[TESTER]** `services/api/tests/`, `pruebas/datos/` e `informes/TESTER-*`: en sus rutas. **Hallazgo:** `pruebas/despliegue/COMANDOS-VPS.md` (`ef8917d`) está fuera de las rutas que `AGENTS.md` le da al TESTER (`pruebas/carga/`, `pruebas/datos/`). Es una guía de comandos para la prueba del VPS, sin código ni secretos. Propuesta: moverlo a `pruebas/datos/` en B2, o agregar `pruebas/despliegue/` al mapa con la aprobación del humano.
- **[LEAD]** solo `docs/contratos/` e `informes/VEREDICTO-*`.
- **Incidente de rutas del LEAD**, corregido antes del veredicto: `37741a9` arrastró los `git rm` del DEV. Se rehízo como `235882f`, con pathspec.

## 5. Arbitrajes, trampas y hallazgos

| # | Rojo | Desenlace | Destinatario | Vuelta |
|---|---|---|---|---|
| 1 | La imagen del proxy por `build:` y no por `image:` (`f098f9a`) | **Se apartó la prueba**: el contrato pide la imagen oficial con versión fijada, y un `FROM nginx:x.y.z` lo cumple (M-4) | TESTER | 1, cerrado en `4ce5e65` |
| 2 | "Sin EAS" con un `grep -r` que encontraba `node_modules` | **El contrato no lo decía** → v2.2 aprobada por el humano | — | 0 |
| 3 | El nivel 2 de ML Kit era obligatorio | **Decisión del humano**: el nivel 2 pasa a ser condicional (M-6); se corrió, porque hubo tráfico | — | — |

- **Trampas:** no se encontraron. Las pruebas de NGINX afirman lo que dice el contrato (códigos, cabeceras, SHA-256, versiones de TLS), y entre vueltas no se cambió ninguna prueba sin un arbitraje (M-4) o una versión nueva del contrato (v2.2).
- **Hallazgo 1:** la inestabilidad de `test_valores_por_defecto_5_intentos_15_min` en la suite completa (§2). Va al TESTER como observación; no bloquea.
- **Hallazgo 2:** el incidente del pcap enviado por correo en la sesión 1 (M-6 punto 7). Quedó borrado y en el acta.
- **Hallazgo 3:** `pruebas/despliegue/` está fuera del mapa de rutas (§4).

## 6. NO VERIFICADO (fase B2: espera el VPS, el dominio y Supabase)

Lo que sigue queda escrito en la rama y pasa a `main` sin efecto en local. Se verifica en B2, en una rama nueva desde `main`:

- §1 y §3 en el VPS: servicios, puertos, salud, Supabase, `api_app`, migraciones y usuarios.
- §2: el certificado de Let's Encrypt y su renovación.
- §4: la clave fuera de los logs del proxy **del VPS** (obligatorio, `PENDIENTES.md`).
- §5: la sesión 2 en el S23, con la descarga por el enlace y sin cable.
- §6: `desplegar.ps1` y `publicar-apk.ps1` contra el VPS, idempotentes.
- La subida automática de la telemetría de ML Kit, sin forzar el job: no se observó en la sesión 1.

## 7. Matriz de trazabilidad

| Criterio (encargo v1 y contrato v2.2) | Caso | Prueba | Resultado |
|---|---|---|---|
| Probar desde los propios celulares en la demo del 10-dic | §1, §5 en el VPS | `test_despliegue_vps.py`, sesión 2 | NO VERIFICADO (B2) |
| NGINX en lugar de Caddy (ADR-0018, stack del MININTER) | §2 | `test_proxy_nginx.py`, `test_compose_vps.py`, sesión 1 (a) | 🟢 |
| APK por enlace protegido, sin EAS | §5, §6 | Pruebas de la descarga, `git grep` de EAS | 🟢 local · VPS en B2 |
| La clave no queda en los logs | §2, §4 | Pruebas de logs y la a.9 | 🟢 local · VPS en B2 |
| Verificar qué envía ML Kit (decisión del humano, M-3) | M-3 | Sesión 1 (b) y (c), evaluación del ARCH | 🟢 |
| Borrado al cierre | §8 | Acta parcial (M-6 p.8) | En curso |

## 8. Acta parcial de eliminación (sesión 1, 2026-11-25)

- **Borrado:** la CA de Caddy (en el S23, `ca-local` y los volúmenes `movil-buscador_caddy-datos` y `movil-buscador_caddy-config`); la CA de mitmproxy (en el S23 y su llave en `flutter-capturas\red`); PCAPdroid; los 2 pcap del teléfono, las 2 copias de la PC y el correo con el pcap (Enviados, Entrada y papelera, en el teléfono y en la PC, confirmado por el humano vía PM); y `flutter-capturas\red\` entero.
- **Queda en el S23 hasta el cierre del MVP:** la CA local de NGINX y el APK de depuración `5f62f6a4`.
- **Queda en la PC:** el registro `Movil_Buscador_capturas\DESPLIEGUE-01\resultados-sesion1.md`, sin identificadores.
- **Incidente:** el pcap de la corrida 2 salió al correo propio del humano. No llevaba datos reales, solo la telemetría de un teléfono de prueba. Se borró. Desde ahora, los pcap salen solo por `adb pull`.

## 9. Para el PR y el merge (los hace el PM con la autorización del humano)

1. `git push --force-with-lease origin despliegue-01`. `origin` tiene la historia de antes del rebase; el humano lo autorizó.
2. PR de `despliegue-01` (`6f870ad` más este veredicto) hacia `main`, con este informe en la descripción.
3. Después del merge: B2 en una rama nueva desde `main`, y `hu-05` rebasada sobre `main`.
