# Evaluación: stack del MININTER en el MVP (PA #37, #38 y #39)

**Rol / fecha:** ARCH, 2026-11-24. Encargo del PM del 2026-11-24 (punto 1). Solo documental: sin contratos, código ni pruebas.
**ADR:** [ADR-0017](../adrs/0017-app-movil-flutter-mlkit.md) (Flutter), [ADR-0018](../adrs/0018-proxy-nginx.md) (NGINX), [ADR-0019](../adrs/0019-servicios-python-motor-aislado.md) (Python y motor aislado) y [ADR-0020](../adrs/0020-keycloak-al-final.md) (Keycloak). **Los cuatro quedaron aceptados el 2026-11-24** (decisiones del humano vía PM, PRD `7cec298`). El ADR-0020 se aceptó con un ajuste: Keycloak se entrega solo documentado. El plan decidido está en la sección 5 y las decisiones, en la sección 6. Las secciones 1 a 4 conservan el análisis que llevó a esas decisiones.
**Estimados:** son del ARCH, en días de trabajo de un agente, y los tiene que validar el LEAD. Los rangos de HU-05 y HU-06 se calcularon sin contrato.

## 1. Resumen

| Punto | Impacto | Días (DEV / TESTER / LEAD) | ADR |
|---|---|---|---|
| (a) Expo → Flutter | Alto: se rehace la app (cinco pantallas, la sesión y HU-04) y sus pruebas. La API, los contratos de la API y la bitácora no cambian | 8 / 6 / 2 (de 7 a 10 en DEV) | 0017 |
| (b) Caddy → NGINX | Bajo: el proxy, los certificados y los pasos de la CA en el teléfono | 1 / 0,5 / 0,5 | 0018 |
| (c) Python se queda | Ninguno si se acepta. Separar el motor cuesta 1,5 / 0,5 dentro de HU-05. Reescribir la API en Java costaría 8 a 10 de DEV | 0 (+1,5 / 0,5 por el motor) | 0019 |
| (d) Keycloak al final | Bajo y acotado a la API: Supabase Auth ya es solo el verificador de claves | 2 a 3 / 1 a 1,5 / 0,5 (propio) | 0020 |
| PA #39 Angular | Ninguno: nada web entra al alcance hasta que se responda | 0 | — |

**Conclusión:** (b), (c) y (d) son baratos. El costo está en (a): unos **10 días de calendario** con DEV y TESTER en paralelo, que consumen la reserva del cronograma. Con todo el stack del MININTER, **HU-05 E1 a E7 y HU-06 caben, pero no HU-05 E8 a E10, HU-09 ni HU-10** (sección 5).

## 2. Impacto de pasar a Flutter (a)

Por pieza, contra lo que ya está decidido:

| Pieza | Qué cambia | Qué no cambia | Riesgo |
|---|---|---|---|
| ML Kit, OCR de placa (HU-04) | Plugin `google_mlkit_text_recognition` en vez de `@react-native-ml-kit/text-recognition` | En el dispositivo, sin red; el usuario confirma o corrige (HU-04 E1); la meta de OCR (≥ 90 %, ADR-0011) | Bajo: el plugin envuelve el mismo SDK nativo |
| ML Kit, calidad facial (HU-05 E2) | Plugin `google_mlkit_face_detection` | Los mismos controles: ángulo, ojos, tamaño, número de rostros | Bajo |
| Cámara | Plugin `camera`, `takePicture()` | Una foto por toque, nunca un flujo continuo (regla 6); el JPEG temporal se borra y se prueba | Bajo |
| Recorte del rostro elegido (ADR-0015) | Paquete `image` en memoria, en un *isolate*; ya no hay temporales del recorte | Solo viaja el recorte; margen del 40 %, rechazo por rostros juntos y por más de 5 | Medio: decodificar 12 MP en Dart es lento. Mitigación: resolución menor, *isolate*. Cuidar la orientación EXIF y que las coordenadas de ML Kit estén en el mismo sistema que la imagen decodificada |
| Ubicación del aviso al 105 (ADR-0016) | `geolocator`, con `forceLocationManager: true` y `timeLimit` | Permiso en primer plano al pulsar, una lectura, coordenadas solo en memoria | Baja el riesgo NO VERIFICADO del ADR-0016: la app ya no usa el proveedor de Google Play services |
| Telemetría (PA #31) | Nada | Los plugins usan los mismos SDK de ML Kit, así que la decisión A, el aviso de OCR-01 y la brecha 10 siguen igual | **NO VERIFICADO:** que los plugins usen la variante empaquetada. Lo confirma el DEV en su `build.gradle` |
| Sesión y token (ADR-0013) | `flutter_secure_storage` y estado con Riverpod o `ChangeNotifier` | Nada en disco salvo el token; limpieza al cerrar sesión; inactividad de 10 min en el servidor | Bajo |
| Cliente de la API (ADR-0007) | Generado en Dart desde `contratos/api/openapi.json` | El contrato | Bajo |
| Build y entrega | Sin EAS: APK firmado en la máquina del proyecto; la llave de firma es un secreto nuevo, fuera del repositorio | APK interno, fuera de las tiendas | Medio: hay que decidir cómo se entrega el APK de la demo del 10-dic (decisión 4) |
| iOS (PA #12) | Requeriría macOS y Xcode o un build en la nube con macOS | Android como referencia (ADR-0010) | Solo si el PA #12 confirma iOS |

## 3. Qué pasa con lo construido en Expo

Fuente: rama `hu-04` (`125cabe`) y `main`, 2026-11-24.

| Qué | Estado | Qué pasa |
|---|---|---|
| API y simuladores (HU-01, 02, 03, 07 y 08) | Aceptados | **Se conservan sin cambios.** Las pruebas de la API son de caja negra por HTTP y siguen valiendo |
| App: HU-01 y HU-02 (login, sesión, roles, ERR-01) | Aceptadas en Expo | Se rehacen en Flutter con los **mismos contratos**. El LEAD saca versiones nuevas de las secciones que nombran Jest, `expo-secure-store` o el `App.tsx`. Hace falta un veredicto nuevo de la parte de la app |
| App: HU-03 y HU-07 (placa manual, bitácora del supervisor) | Aceptadas en Expo | Igual que HU-01 y HU-02 |
| App: HU-04 (OCR, WIP `125cabe`, build EAS `a3380e39`) | En pausa; el rojo del segundo login del TESTER está sin resolver | **No se termina en Expo.** Se construye directo en Flutter. Se reutilizan: la normalización y la validación de la placa (`src/camara/placaLeida.ts`), los textos y estados de OCR-01, el aviso de telemetría y la lista de casos del TESTER |
| Pruebas de la app (unas 2.500 líneas de Jest) | Del TESTER | Se reescriben en `flutter_test`. Los casos se mantienen; el código no |
| Prototipo de UX (`docs/ux/prototipo/`) | HTML | No cambia: nunca fue Expo |
| `apps/movil/eas.json`, `app.json`, `plugins/` | Configuración de Expo | Desaparecen con la migración |

**Decidido (humano, 2026-11-24):** de `hu-04` van a `main` **solo los documentos**. Las pruebas de la app pasan a `apps/movil/test/` e `integration_test/` (el cambio de `AGENTS.md` lo hace el humano).

**Recomendación original del ARCH:** no mergear el código Expo de `hu-04` a `main`. La rama se conserva (con una etiqueta) como referencia. `main` mantiene la app Expo aceptada hasta que se acepte la versión en Flutter, y el DEV la reemplaza en un solo commit, de modo que el historial conserva la versión anterior. Antes de cerrar `hu-04`, se mergean sus documentos (`docs/arch/`, la evaluación de telemetría, los informes), que siguen vigentes.

## 4. Argumentos sobre Python (c) y Keycloak (d)

Están en el [ADR-0019](../adrs/0019-servicios-python-motor-aislado.md) (sección "Argumentos para la negociación") y en el [ADR-0020](../adrs/0020-keycloak-al-final.md) ("Relación con el PA #3"). En una línea:

- **Python:** lo que se queda en Python es interno, no tiene puertos públicos, tiene contrato y pruebas de caja negra que permiten reescribirlo en Java para producción. La pieza más grande, el motor, es justo la que el MININTER cambiaría por un motor certificado.
- **Keycloak:** el cambio está acotado a un módulo de la API, porque Supabase Auth hoy solo verifica la clave; la sesión, el bloqueo y la bitácora ya son de la API.

## 5. Estimado contra el cronograma (entrega final el 30-dic)

**Supuestos:** un DEV y un TESTER en paralelo, días corridos, desde el 25-nov. Los hitos están en el PRD: demo con APK el 10-dic, pruebas del 16 al 26-dic, despliegue y aceptación del 24 al 28-dic, entrega el 30-dic. Quedan 36 días de calendario.

### Plan decidido (humano, 2026-11-24): escenario 1 con HU-09 en lugar de Keycloak

| Fechas (aprox.) | Trabajo | Días |
|---|---|---|
| 25 y 26-nov | LEAD: contrato de la migración (versiones nuevas de HU-01 a HU-04 y HU-07, interfaces Dart de los bordes, pruebas en `apps/movil/test/` e `integration_test/`) | 1 a 2 |
| 26-nov al 5-dic | DEV: app Flutter con HU-01, 02, 03 y 07, y HU-04 terminada. TESTER, en paralelo: pruebas en `flutter_test` | 8 / 6 |
| 5 y 6-dic | LEAD: veredicto de la migración | 1 |
| 6 al 8-dic | DEV: NGINX (ADR-0018) y DESPLIEGUE-01 con el APK de Flutter, descargable desde la ruta protegida del VPS (ADR-0018, punto 5) | 1,5 |
| 10-dic | Demo con APK | — |
| 9 al 17-dic | HU-05 E1 a E7, con el motor separado (ADR-0019) y la calibración | 7 a 8 |
| 17 al 22-dic | HU-06 (opción A del PA #2, mientras el MININTER no responda) | 4 a 5 |
| **22 al 24-dic** | **HU-09, aviso simulado al 105 (ADR-0016)**, en lugar de construir Keycloak | unos 2 a 3 |
| 24 al 28-dic | Despliegue, pruebas de desempeño, evaluación biométrica, aceptación | — |
| Hasta el 30-dic | Keycloak documentado (ADR-0020): manual y brecha 4, con sus dos variantes | ARCH y DEV, en los documentos de entrega |

**Fuera de la construcción del MVP** (definidas y aprobadas): HU-05 E8 a E10 y HU-10.

**Riesgos del plan:**
- La demo del 10-dic queda sin margen. Si la migración se atrasa más de 2 días, la demo se hace con el último APK de Expo (DESPLIEGUE-01 tal como está).
- HU-09 queda pegada a la fase de despliegue. Si HU-05 o HU-06 se atrasan, HU-09 es lo primero que se mueve, hasta el plazo máximo (2-ene) o fuera del MVP. Eso lo decide el humano.
- HU-09 necesita el permiso de ubicación y la prueba en el teléfono real (Samsung Galaxy S23 Ultra, Android 16), con el GPS adentro y afuera. Hay que reservar ese tiempo en el veredicto.

### Escenario 1 original: migrar ya (recomendado por el ARCH, base del plan decidido)

| Fechas (aprox.) | Trabajo | Días |
|---|---|---|
| 25 y 26-nov | LEAD: contrato de la migración (versiones nuevas de HU-01 a HU-04 y HU-07, interfaces Dart de los bordes) | 1 a 2 |
| 26-nov al 5-dic | DEV: app Flutter con HU-01, 02, 03 y 07, y HU-04 terminada. TESTER, en paralelo: pruebas en `flutter_test` | 8 / 6 |
| 5 y 6-dic | LEAD: veredicto de la migración | 1 |
| 6 al 8-dic | DEV: NGINX (ADR-0018) y DESPLIEGUE-01 con el APK de Flutter | 1,5 |
| 10-dic | Demo con APK | — |
| 9 al 17-dic | HU-05 E1 a E7, con el motor separado (ADR-0019) y la calibración | 7 a 8 |
| 17 al 22-dic | HU-06 (opción A del PA #2) | 4 a 5 |
| 22 al 24-dic | Keycloak propio (ADR-0020), o entregarlo documentado | 3 |
| 24 al 28-dic | Despliegue, pruebas de desempeño, evaluación biométrica, aceptación | — |

**Lo que no cabe:** HU-05 E8 a E10 (foto con varias personas, de 2 a 3 días), HU-09 (aviso al 105, unos 2) y HU-10 (unos 3). Hoy ninguna de las tres está autorizada para desarrollo. Si el humano las quiere en el MVP, hay que sacar Keycloak o pedir el plazo máximo (2-ene).

**Riesgos del escenario:** la demo del 10-dic queda sin margen. Si la migración se atrasa más de 2 días, la demo se hace con el último APK de Expo (DESPLIEGUE-01 tal como está).

### Escenario 2: Expo hasta la demo del 10-dic y migrar después

La demo queda protegida, pero HU-04 se termina en Expo (unos 2 días) y después se rehace. La migración (del 11 al 20-dic) choca con HU-05 y HU-06. **Resultado:** HU-06 o Keycloak no caben. No se recomienda.

### Escenario 3: Flutter después del MVP (argumento de negociación)

No cuesta días: el MVP se entrega en Expo y la app en Flutter queda como trabajo para producción. Contradice la decisión del humano del 2026-11-24 y el "obligatorio en el MVP" del PA #37. Es la opción que el humano puede poner sobre la mesa si el MININTER prioriza HU-05 E8 a E10, HU-09 o HU-10.

### Comparación

| Escenario | Días de stack | Demo del 10-dic | Qué sale del MVP |
|---|---|---|---|
| 1. Migrar ya | unos 14 (Flutter, NGINX y Keycloak) | En Flutter, sin margen | E8 a E10, HU-09 y HU-10 |
| 2. Migrar después | unos 16 (HU-04 se hace dos veces) | En Expo | Además, HU-06 o Keycloak |
| 3. Flutter después del MVP | unos 4 (NGINX y Keycloak) | En Expo | Nada; entra E8 a E10 o HU-09 |
| Java en la API además (si el MININTER no acepta Python) | +8 a 10 | — | Además, HU-06 |

## 6. Decisiones del humano (2026-11-24, vía PM)

| # | Pregunta | Decisión |
|---|---|---|
| 1 | ADR-0017 a 0020 | Aceptados. El 0020 con ajuste: Keycloak no se construye en el MVP |
| 2 | Escenario de cronograma | Escenario 1, migrar ya. Los días de Keycloak van a HU-09, que entra al MVP. HU-05 E8 a E10 y HU-10 quedan fuera de la construcción |
| 3 | Rama `hu-04` | A `main` van solo los documentos |
| 4 | Entrega del APK de la demo | Opción (a): descarga desde una ruta protegida del VPS, por NGINX (ADR-0018, punto 5) |
| 5 | Motor | Se separa ahora (ADR-0019) |
| 6 | Ruta de las pruebas de la app | `apps/movil/test/` e `integration_test/`. El cambio de `AGENTS.md` lo hace el humano |
| 7 | Keycloak propio o del MININTER; roles | Abierto (PA #38). El ADR-0020 describe las dos variantes sin elegir |

## 7. Lo que se verifica después (NO VERIFICADO hoy)

- Que `google_mlkit_text_recognition` y `google_mlkit_face_detection` usan la variante empaquetada de ML Kit (DEV, en el contrato de la migración).
- Que `geolocator` con `forceLocationManager` funciona en el Samsung Galaxy S23 Ultra con Android 16 (DEV, al autorizarse HU-09).
- Que el módulo ACME nativo de NGINX está en la imagen estable fijada (DEV, ADR-0018).
- El consumo de memoria de Keycloak junto con el motor en el VPS de 4 GB (DEV, al final del MVP).
