# CONTRATO — HU-04 Capturar la placa con la cámara

**Tipo:** Feature
**Versión:** v6
**Estado:** v1 a v3 aprobadas (2026-11-19) · v4 y v5 aprobadas (2026-11-20, humano vía PM) · **v6 aprobada (humano vía PM, 2026-11-24)** (se construye directo en Flutter, CONTRATO-MIGRACION-FLUTTER v1)
**Origen:** `docs/hus/HU-04-capturar-placa-ocr.md` · encargo PM → LEAD (2026-11-19), Iteración 2, contrato 1
**Rama de trabajo:** `migracion-flutter`, desde `main` `47ace7b` (**v6**). La rama `hu-04` y el código Expo quedan como referencia en la etiqueta `hu-04-expo-referencia` y no se mergean (decisión 3 del humano, 2026-11-24)
**Pasa por UX:** sí. Pantallas OCR-01 a OCR-04 (`docs/ux/wireframes/HU-04-capturar-placa-ocr.md`) y el botón 📷 de PLA-01. **v6:** el UX revisa con capturas de `flutter_test` y del S23 Ultra, junto con el resto de la app (CONTRATO-MIGRACION-FLUTTER §10).

---

## Paquete de contexto

| Fuente | Por qué entra |
|---|---|
| HU-04 | Historia, escenarios 1 a 3, supuestos (lectura en el dispositivo, la foto no se guarda, nunca se consulta sin confirmar) |
| Wireframes OCR-01 a OCR-04 | Pantallas, textos y botones; "Abrir ajustes" aprobado el 2026-11-18 |
| ADR-0017 (**v6**; reemplaza al ADR-0002) | Flutter: `camera` con `takePicture()` (nunca `startImageStream`), `google_mlkit_text_recognition` en el dispositivo, la cámara y ML Kit detrás de una interfaz Dart, el JPEG temporal se borra en un `finally`, telemetría sin cambios (opción A) |
| CONTRATO-MIGRACION-FLUTTER v1 | Interfaz de la app para las pruebas (§2), build y secretos (§6), variante empaquetada de ML Kit (§7), safe area (§4) y orden del cierre (§10) (**v6**) |
| ADR-0010 | Android primero, con un celular de referencia; el OCR funciona sin red; iOS no se prueba hasta el PA #12 |
| ADR-0011 | Precisión provisional del OCR: ≥ 90 % de lecturas exactas de día en ≥ 100 imágenes con el celular de referencia; de noche o en ángulo se mide y se reporta (PA #4) |
| ADR-0013 | Estado de la app solo en memoria; se limpia al cerrar la sesión |
| TECH-DESIGN.md › Criterios › Consulta de placa (HU-03, HU-04) y matriz de tratamiento | "El OCR deja el texto en un campo editable y no se envía ninguna consulta sin la confirmación del usuario"; la imagen de la placa no se guarda y se procesa en el dispositivo |
| CONTRATO-HU-03 v4 | PLA-01 (el botón 📷 queda deshabilitado hasta HU-04), `formato_placa` de `GET /v1/motivos` y el resto de la consulta, **sin cambios** |
| CONTRATO-HU-08 v4 | Placas sintéticas con prefijo `ZZ` (`ZZA-101`, `ZZB-201`, `ZZZ-999`…) |
| AGENTS.md, reglas 2, 6, 7 y 8 | Motivo obligatorio; sin lectura automática de placas; ningún error se convierte en un negativo; ninguna foto en el repositorio |

## Interfaz observable

1. **App (`flutter_test`):** se monta `MovilBuscadorApp` (CONTRATO-MIGRACION-FLUTTER §2). La cámara y el OCR se reemplazan por un doble del **borde** `LectorPlaca` del §1 (**v6**).
2. **App (dispositivo):** APK de depuración de Flutter en el S23 Ultra (Android 16). Lo que solo se ve ahí está en el §6 (**v6**).
3. **API:** sin cambios. La consulta sigue siendo `POST /v1/consultas/placa` de CONTRATO-HU-03 v4.

## Comportamiento

### 1. Módulo de borde para las pruebas (DECISIÓN PROPUESTA 1; v6: Dart)

La cámara y ML Kit son código nativo y no corren en `flutter_test`. El DEV expone toda la cámara y el OCR a través de **una sola interfaz Dart**, `LectorPlaca`, que la app recibe en `Dependencias.lectorPlaca`. La forma exacta (con `PermisoCamara` y `LecturaPlaca`) está en **CONTRATO-MIGRACION-FLUTTER §2** y equivale, función por función, a la de Expo:

| Expo (v1 a v5, `src/camara/lectorPlaca.ts`) | Flutter (v6, `lib/bordes/`) |
|---|---|
| `asegurarPermisoCamara(): Promise<'concedido' \| 'denegado'>` | `Future<PermisoCamara> asegurarPermisoCamara()` → `PermisoCamara.concedido` o `PermisoCamara.denegado` |
| `VisorCamara({ activo })` | `Widget visorCamara({required bool activo})` |
| `capturarYLeer(): Promise<{ texto: string \| null }>`; rechaza si la cámara falla | `Future<LecturaPlaca> capturarYLeer()` (`texto` es `null` si no se reconoció nada); lanza una excepción si la cámara falla |
| `abrirAjustes(): Promise<void>` | `Future<void> abrirAjustes()` |

Fuera de `apps/movil/lib/bordes/`, ningún archivo importa `package:camera` ni `package:google_mlkit_*` (se comprueba con `grep` en `apps/movil/lib/`). Ninguna función del borde devuelve una ruta de archivo ni una imagen. En la §2 a la §5, "`capturarYLeer` se llama" significa una llamada al doble; "`texto`" es `LecturaPlaca.texto`.

### 2. Entrada desde PLA-01

| Caso | Acción | Resultado visible | Origen |
|---|---|---|---|
| Botón habilitado | PLA-01 | El botón 📷 (etiqueta de accesibilidad "Leer con cámara"; **v6**) queda **habilitado** | CONTRATO-HU-03 §6 (deshabilitado hasta HU-04), wireframe HU-03 |
| Permiso concedido | Tocar 📷; `asegurarPermisoCamara()` → `concedido` | OCR-01 | Gherkin esc. 1 |
| Permiso denegado | Tocar 📷; `asegurarPermisoCamara()` → `denegado` | OCR-04. `capturarYLeer` nunca se llama | Gherkin esc. 3 |

### 3. Captura (OCR-01 → OCR-02 u OCR-03)

| Caso | Entrada | Resultado visible | Origen |
|---|---|---|---|
| Visor | Se abre OCR-01 | "Leer placa", el visor (`visorCamara(activo: true)`, **v6**), "Encuadre la placa y toque Capturar", "Capturar", "Ingresar manualmente" y "✕". **`capturarYLeer` no se llama** mientras no se toque "Capturar", por más tiempo que pase | OCR-01, regla 6 |
| Aviso de telemetría (**v5**) | La **primera vez que se abre OCR-01 en cada sesión** | Sobre el visor aparece una tarjeta con "Antes de leer la placa", el texto "Para leer la placa, la app usa ML Kit, una herramienta de Google que funciona en este teléfono. Según Google, ML Kit no le envía la foto ni la placa leída, pero sí le envía datos técnicos de uso y un código de esta instalación." y el botón "Entendido". Mientras se ve, "Capturar" está **desactivado** (`capturarYLeer` no se llama) e "Ingresar manualmente" sigue activo. Tocar fuera de la tarjeta no hace nada | Decisión del humano sobre la telemetría de ML Kit (opción A); texto del UX y el BA (`docs/ux/revisiones/HU-04.md`) · **v5** |
| Cerrar el aviso (**v5**) | "Entendido" | La tarjeta desaparece y "Capturar" se activa. **En esa sesión no vuelve a aparecer**, aunque se salga y se vuelva a entrar a OCR-01 | **v5** |
| Salir sin verlo (**v5**) | "✕", "atrás" del sistema (`handlePopRoute`, **v6**) o "Ingresar manualmente" con la tarjeta a la vista | Sale de OCR-01 como siempre (§3) **sin darlo por visto**: la próxima vez que se abra OCR-01 en esa sesión, aparece de nuevo | **v5** |
| Solo en memoria (**v5**) | Cerrar la sesión (por "Salir" o por inactividad) y volver a entrar | El aviso aparece otra vez la primera vez que se abre OCR-01. Nada se guarda en el teléfono por el aviso: el almacenamiento seguro no tiene ninguna clave nueva (`almacen.leerTodo()`, **v6**), y HU-01 AUTH-03 sigue igual | ADR-0013, CONTRATO-HU-01 AUTH-03 · **v5** |
| Sin permiso (**v5**) | Permiso denegado → OCR-04 | El aviso no aparece en OCR-04 | **v5** |
| Una sola foto | Tocar "Capturar" | `capturarYLeer` se llama **exactamente una vez** por toque. Mientras espera, "Capturar" queda desactivado (un segundo toque no dispara otra lectura) | OCR-01, regla 6 |
| Lectura con placa | `texto` contiene un candidato que cumple `formato_placa.regex` (§4) | OCR-02 con ese candidato en el campo editable | Gherkin esc. 1 |
| Lectura sin placa | `texto` es `null`, vacío o no tiene ningún candidato que cumpla la regex | OCR-03 | Gherkin esc. 2 · DECISIÓN PROPUESTA 2 |
| Falla de la cámara | `capturarYLeer` rechaza | OCR-03 (nunca una pantalla en blanco ni un resultado) | Gherkin esc. 2, regla 7 |
| Salir | "✕" en OCR-01 | Vuelve a PLA-01 **sin cambios** (la placa y el motivo quedan como estaban) | OCR-01 |
| Ingreso manual | "Ingresar manualmente" (en OCR-01, OCR-03 u OCR-04) | Vuelve a PLA-01 sin cambios, con el foco en el campo "Placa" | OCR-01, OCR-03, OCR-04 |
| Sin red | En el dispositivo, en modo avión | OCR-01 a OCR-03 funcionan igual (la lectura es local). La consulta posterior se comporta como en HU-03 sin red (PLA-07) | ADR-0010 |

### 4. Del texto leído a la placa propuesta (DECISIÓN PROPUESTA 2)

La app pasa el texto a mayúsculas y lo separa en líneas. En cada línea busca candidatos que cumplan `formato_placa.regex` (de `GET /v1/motivos`, CONTRATO-HU-03 v3), probando primero el texto tal cual y después con los espacios o el punto entre los dos grupos cambiados por un guion. Propone **el primer candidato** que cumpla. Con la regex por defecto, los ejemplos que fijan el resultado (el TESTER los usa en `flutter_test`; **v6**) son:

| `texto` de `capturarYLeer` (`LecturaPlaca.texto`) | Pantalla y valor del campo |
|---|---|
| `"ZZA-101"` | OCR-02, `ZZA-101` |
| `"zza-101"` | OCR-02, `ZZA-101` |
| `"ZZA 101"` | OCR-02, `ZZA-101` |
| `"ZZA.101"` | OCR-02, `ZZA-101` |
| `"PERU\nZZB-201\nLIMA"` | OCR-02, `ZZB-201` |
| `"ZZA-101 ZZB-201"` | OCR-02, `ZZA-101` (el primero) |
| `"ZZA-1O1"` (letra O) | OCR-03 (no cumple la regex; la app no adivina caracteres) |
| `"PERU"` · `""` · `null` | OCR-03 |

Si la API cambia `formato_placa.regex`, cambia lo que se acepta, sin tocar el código.

### 5. Confirmar y volver a la consulta (OCR-02 → PLA-01)

| Caso | Acción | Resultado visible | Origen |
|---|---|---|---|
| Confirmar | OCR-02 | "Placa leída", el campo editable con la placa, "Confirme o corrija la placa antes de consultar.", "Usar esta placa" y "Volver a capturar". **No se muestra ninguna imagen** | OCR-02, Gherkin esc. 1 |
| Corregir | El usuario edita el campo y toca "Usar esta placa" | PLA-01 con **el texto corregido** en "Placa" | Gherkin esc. 1 |
| Nunca consulta sola | "Usar esta placa" | Vuelve a PLA-01 con la placa cargada. **El motivo queda como estaba antes de abrir la cámara**: si estaba vacío, sigue vacío. **No se envía ninguna solicitud**: entre el toque de 📷 y el de "Consultar" en PLA-01, el `MockClient` no recibe ninguna solicitud (**v6**) | Encargo PM, HU-04 supuestos, TECH-DESIGN · DECISIÓN PROPUESTA 3 |
| Sigue HU-03 | En PLA-01, el agente elige el motivo y toca "Consultar" | Todo sigue igual que en CONTRATO-HU-03 v4: validación local de PLA-02 y PLA-03 (también con lo corregido), PLA-04 a PLA-08 | CONTRATO-HU-03 v4 |
| Volver a capturar | "Volver a capturar" | OCR-01 (el valor leído se descarta) | OCR-02 |
| Reintentar | "Volver a intentar" en OCR-03 | OCR-01 | OCR-03, Gherkin esc. 2 |
| Abrir ajustes | "Abrir ajustes" en OCR-04 | Se llama `abrirAjustes()` | OCR-04 |
| Volver con permiso | Después de OCR-04, el usuario da el permiso en Ajustes y vuelve a tocar 📷 | `asegurarPermisoCamara()` → `concedido` → OCR-01 | Gherkin esc. 3 |

### 6. La foto y el texto leído no se guardan ni salen del dispositivo (título v5)

**Excepción conocida (v5):** ML Kit guarda en el almacenamiento privado de la app una cola de telemetría (`databases/com.google.android.datatransport.events`) y envía a Google métricas técnicas de uso y un código de esta instalación. Según Google, no envía la imagen ni el texto leído. Lo decidió el humano (opción A, 2026-11-20; `docs/arch/evaluaciones/HU-04-telemetria-mlkit.md`). La verificación de la cola en el teléfono está en la fila "Cola de telemetría". **v6:** el plugin `google_mlkit_text_recognition` usa el mismo SDK nativo, así que la excepción no cambia; la variante empaquetada la confirma el DEV (CONTRATO-MIGRACION-FLUTTER §7).


| Caso | Cómo se observa | Dónde | Origen |
|---|---|---|---|
| La foto no llega a la API | En todo el flujo de OCR-01 a OCR-03, el `MockClient` no recibe ninguna solicitud; y en la consulta posterior, el cuerpo de `POST /v1/consultas/placa` es el de HU-03 (sin imagen ni campos nuevos) | `flutter_test` | HU-04 supuestos, ADR-0017 · **v6** |
| Nada en el almacenamiento | Después de leer, `almacen.leerTodo()` no tiene ninguna clave nueva | `flutter_test` | ADR-0013 · **v6** |
| Sin caché HTTP: la API (**v4**) | Toda respuesta de `/v1/*` (éxito o error, autenticada o no) lleva la cabecera `Cache-Control: no-store` | pytest (red interna y proxy) | ADR-0013, hallazgo B de la prueba física · **v4** |
| Sin caché HTTP: la app (**v4**, **v6**) | La app no usa ninguna caché HTTP: `apps/movil/pubspec.yaml` no declara ningún paquete de caché (`dio_cache_interceptor`, `flutter_cache_manager`, `http_cache*`, `cached_network_image`) y toda la red pasa por `clienteHttp` (CONTRATO-MIGRACION-FLUTTER §2) | Repositorio (`grep`) | ADR-0013 · **v6** (reemplaza al `fetch` con `cache: 'no-store'`) |
| Sin caché HTTP en disco (**v4**, **v6**) | En el APK de depuración, después de iniciar sesión, abrir PLA-01 y consultar una placa, en una copia de `cache/` y `files/` de la app (`adb shell run-as pe.prototipo.movilbuscador …`, fuera del repositorio y borrada al terminar) no hay ningún archivo que contenga `/v1/` ni una respuesta de la API (por ejemplo, `"resultado"` o `token_acceso`) | Dispositivo (mini sesión) | Hallazgo B · **v4** · **v6** (en Flutter no hay `http-cache` de OkHttp ni Metro) |
| Cola de telemetría (**v5**) | En el APK de depuración (**v6**), después de leer al menos una placa, la copia de `databases/com.google.android.datatransport.events` (fuera del repositorio, borrada al terminar) **no contiene** ninguna imagen (cabeceras JPEG o PNG, crudas o en base64) ni el texto de la placa leída (`ZZ…`). Si aparece alguna de las dos, la decisión se reabre | Dispositivo (mini sesión, `pruebas/datos/revisar_datatransport.py`) | Decisión del humano (5) · **v5** |
| La foto se borra | En el APK de depuración (**v6**), después de 10 capturas seguidas, `adb shell run-as pe.prototipo.movilbuscador find . -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png"` no devuelve ningún archivo de captura (en `files/` ni en `cache/`). La galería del teléfono no tiene fotos nuevas | Dispositivo | ADR-0017 regla 2, HU-04 supuestos, TECH-DESIGN (matriz de tratamiento) |
| Sin lectura continua | En el APK de depuración (**v6**), con la cámara apuntando a una placa impresa durante 30 s sin tocar "Capturar", no aparece OCR-02 | Dispositivo; y `grep -r startImageStream apps/movil/lib` vacío (**v6**) | Regla 6, ADR-0017 alternativa D |
| La placa se lee | En el APK de depuración (**v6**), una placa sintética impresa (§7) se lee y aparece en OCR-02 | Dispositivo | Gherkin esc. 1 |
| Permiso real | En el APK de depuración (**v6**), negar el permiso de cámara en el diálogo del sistema muestra OCR-04, y "Abrir ajustes" abre la pantalla de la app en Ajustes **o su pantalla de permisos** (en Samsung con Android 16, `com.google.android.permissioncontroller`; **v4**) | Dispositivo | Gherkin esc. 3 · **v4** |

### 7. Precisión del OCR y placas de prueba (provisional, PA #4)

| Caso | Salida esperada | Origen |
|---|---|---|
| Placas de prueba | Solo **placas sintéticas impresas** con el prefijo `ZZ` de HU-08 (por ejemplo `ZZA-101`, `ZZB-201`, `ZZZ-999` y otras de la semilla), en papel y del tamaño de una placa, con la leyenda **"PRUEBA — NO VÁLIDA"** en letra chica. **Nunca placas de vehículos reales** | Encargo PM, regla 8 · DECISIÓN PROPUESTA 4 |
| Precisión de día | ≥ 90 % de lecturas exactas (lo que muestra OCR-02 es igual a la placa impresa, antes de corregir) en ≥ 100 capturas de día con el celular de referencia | ADR-0011 · **v2: va aparte**, en la fase de pruebas del 16 al 26-dic (como el p95 de HU-03), **no en este veredicto** |
| De noche o en ángulo | Se mide y se reporta, sin meta, en la misma medición aparte | ADR-0011 · v2 |
| Registro | Las capturas no se guardan. Se registra solo la placa impresa, lo leído, la condición (día, noche, ángulo, distancia) y si coincide, en `pruebas/datos/ocr-precision.csv`. **Ninguna imagen** | Regla 8, ADR-0017 |

### 8. Conexión del APK de depuración con la API local (v3, v6)

El APK de depuración en el S23 Ultra llega a la API local por HTTPS, con la CA local del proxy (opción B del humano, 2026-11-19). **v6:** mientras el proxy local siga siendo Caddy (hasta DESPLIEGUE-01 v2), es la CA local de Caddy; después, la CA local que genera el script de `infra/` para NGINX (CONTRATO-DESPLIEGUE-01 v2). Sin Metro: solo hace falta `adb reverse tcp:8443 tcp:8443`.

| Caso | Salida esperada | Dónde | Origen |
|---|---|---|---|
| Conexión | Con la CA local del proxy instalada en el teléfono como certificado del usuario y `adb reverse tcp:8443 tcp:8443`, el APK de depuración (compilado con `--dart-define=API_URL=https://localhost:8443`) inicia sesión y carga `GET /v1/motivos` | Dispositivo | Humano (vía PM) · **v3** · **v6** |
| Confianza solo en depuración | `apps/movil/android/app/src/main/res/xml/network_security_config.xml`, escrito a mano: confía en los certificados del usuario **solo dentro de `<debug-overrides>`**. El `base-config` confía únicamente en los certificados del sistema y no permite texto plano | Archivo del repositorio (**v6**: sin `prebuild`) | Humano (vía PM) · **v3** · ADR-0017 regla 4 |
| El build de release no incluye el override | `flutter build apk --release` da un APK no depurable (sin `application-debuggable`), así que Android ignora `<debug-overrides>`. `aapt dump badging` (o `apkanalyzer`) sobre el APK lo confirma | APK de release (**v6**) | Condición 3 del humano · **v3** |
| Sin secretos | La CA local del proxy y su llave privada, y la llave de firma del APK (**v6**), **nunca** se versionan. `git ls-files` no muestra ningún `.crt`, `.pem`, `.key`, `.der`, `.jks` ni `.keystore`, y `.gitignore` los excluye | Repositorio | Condición 2 del humano, regla 8 · **v3** |
| Pasos para el humano | En `informes/DEV-MIGRACION-FLUTTER.md` (**v6**): pasos numerados en español simple, para Samsung con Android 16, para **desinstalar** la app de Expo (otra firma), **exportar** la CA desde el contenedor `proxy`, **instalarla** en el teléfono, usar `adb reverse` y **borrarla** al cierre del proyecto | Informe del DEV | Condición 1 del humano · **v3** |

## Nombres que no se negocian

| Tipo | Valor exacto |
|---|---|
| Borde (**v6**) | `LectorPlaca` en `apps/movil/lib/bordes/` (`package:movil_buscador/bordes/bordes.dart`) · `asegurarPermisoCamara` · `visorCamara` · `capturarYLeer` · `abrirAjustes` · `PermisoCamara.concedido` · `PermisoCamara.denegado` · `LecturaPlaca.texto` (CONTRATO-MIGRACION-FLUTTER §2) |
| Botón de PLA-01 | Etiqueta de accesibilidad "Leer con cámara" (📷) (**v6**) |
| OCR-01 | "Leer placa" · "Encuadre la placa y toque Capturar" · "Capturar" · "Ingresar manualmente" |
| Aviso de OCR-01 (v5) | "Antes de leer la placa" · "Para leer la placa, la app usa ML Kit, una herramienta de Google que funciona en este teléfono. Según Google, ML Kit no le envía la foto ni la placa leída, pero sí le envía datos técnicos de uso y un código de esta instalación." · "Entendido" |
| OCR-02 | "Placa leída" · "Confirme o corrija la placa antes de consultar." · "Usar esta placa" · "Volver a capturar" |
| OCR-03 | "No se pudo leer la placa. Pruebe de frente y con más luz." · "Volver a intentar" · "Ingresar manualmente" |
| OCR-04 | "La app no tiene permiso para usar la cámara." · "Para darlo: Ajustes › Aplicaciones › Movil Buscador › Permisos › Cámara." · "Abrir ajustes" · "Ingresar manualmente" |
| Archivo de precisión | `pruebas/datos/ocr-precision.csv` |
| API | Sin cambios (CONTRATO-HU-03 v4) |

## Qué se prueba dónde

| Parte | `flutter_test` (OCR con el doble de `LectorPlaca`; **v6**) | S23 Ultra con el APK de depuración (**v6**) |
|---|---|---|
| Botón 📷 habilitado, entrada por permiso (§2) | Sí | Permiso real del sistema (§6) |
| Una sola lectura por toque, nada sin tocar (§3) | Sí, contando las llamadas a `capturarYLeer` | Sí, 30 s sin tocar (§6) |
| Texto → placa propuesta (§4) | Sí, la tabla completa | — |
| Confirmar, corregir, volver; nunca consulta sola (§5) | Sí, contando las solicitudes del `MockClient` | Paso a paso, una vez |
| Nada en el almacenamiento seguro ni a la API (§6) | Sí | — |
| Aviso de telemetría (§3, v5) | Sí: primera vez por sesión, "Capturar" desactivado, salir sin verlo, después de cerrar la sesión, sin permiso | Una vez, en la mini sesión (capturas para el UX) |
| Cola de telemetría (§6, v5) | No | Sí, en la mini sesión |
| Sin caché HTTP (§6, v4, v6) | La cabecera en pytest; el `pubspec.yaml` sin paquetes de caché (`grep`) | `cache/` y `files/` sin respuestas de `/v1/` (mini sesión) |
| La foto se borra del disco (§6) | No (no hay disco) | Sí, con `adb` |
| La placa impresa se lee de verdad (§6) | No | Sí |
| Precisión (§7) | No | **Aparte**, en la fase de pruebas (v2) |
| Sin red (§3) | No | Sí, en modo avión |
| Conexión a la API local con la CA del proxy (§8) | No | Sí |
| Override solo en depuración; sin secretos (§8) | No (no hay build) | `network_security_config.xml`, APK de release y `git ls-files` |

**v6:** todo lo de la columna derecha exige el APK de Flutter en el S23 Ultra. Si no hay dispositivo o build a tiempo, esa columna queda `NO VERIFICADO` y se escala. Una parte se puede automatizar con `integration_test` (CONTRATO-MIGRACION-FLUTTER §8).

## Rutas de cada rol

| Rol | Rutas | Origen |
|---|---|---|
| TESTER | `apps/movil/test/`, `apps/movil/integration_test/`, `apps/movil/.maestro/` (si lo usa), `pruebas/datos/` (el CSV de precisión y el guion de las pruebas físicas, sin imágenes), `informes/TESTER-*.md` (**v6**) | AGENTS.md |
| DEV | `apps/movil/` (salvo `test/`, `integration_test/` y `.maestro/`), incluidos `pubspec.yaml`, `pubspec.lock` y `android/` (permiso de cámara en el manifiesto, `network_security_config.xml`); `informes/DEV-*.md` (**v6**) | AGENTS.md |

Las placas impresas y las capturas de pantalla del dispositivo quedan **fuera del repositorio**.

## Avisos de contexto

- **Riesgo (ADR-0002, sigue en el ADR-0017):** ML Kit lee texto y no conoce las placas peruanas. Por eso la app valida con la regex y el usuario siempre confirma (§4 y §5).
- **Versión de Flutter (v6):** se fija al empezar y no se cambia hasta el cierre (CONTRATO-MIGRACION-FLUTTER §6).
- **Build (v6):** sin EAS. El APK se compila en la máquina del proyecto (`flutter build apk`); la llave de firma vive fuera del repositorio.
- **iOS** queda fuera hasta el PA #12 (ADR-0010).

## Decisiones propuestas (no venían en la tarea)

| # | Decisión | Por qué hace falta | Estado |
|---|---|---|---|
| 1 | Módulo de borde con 4 funciones fijas, que el TESTER simula (v1 a v5: `src/camara/lectorPlaca.ts` en Jest; **v6**: la interfaz `LectorPlaca` en `flutter_test`, CONTRATO-MIGRACION-FLUTTER decisión 1) | Sin una interfaz fija, la prueba tendría que conocer la librería que elija el DEV (como pasó en HU-01, §4 bis) | Aprobada por el humano (vía PM, 2026-11-19) |
| 2 | La placa propuesta es el primer candidato que cumple `formato_placa.regex` (con los espacios o el punto cambiados por guion). Si no hay ninguno, OCR-03, y la app no adivina caracteres (`O`/`0`) | Ni la HU ni el wireframe dicen qué hacer con texto que no es una placa. Mostrarlo igual invitaría a consultar basura | Aprobada por el humano (vía PM, 2026-11-19) |
| 3 | "Usar esta placa" conserva el motivo que ya estaba elegido; si no había, queda vacío | El wireframe dice "donde falta el motivo", pero no aclara si se borra uno ya elegido | Aprobada por el humano (vía PM, 2026-11-19) |
| 4 | Placas impresas en papel con el prefijo `ZZ` y la leyenda "PRUEBA — NO VÁLIDA" | Pedido del PM: nada de placas reales, y que la impresa no pueda confundirse con una placa oficial | Aprobada por el humano (vía PM, 2026-11-19) |
| 5 | La medición de precisión (≥ 100 capturas de día, ≥ 90 %) **va aparte**, en la fase de pruebas del 16 al 26-dic, como el p95 de HU-03. En el veredicto de HU-04 entra solo el paso a paso físico en el S23 Ultra (Android 16) | ADR-0011 la fija como criterio, pero depende de que el humano tome ≥ 100 fotos | Aprobada por el humano (vía PM, 2026-11-19) · **v2** |

## Fuera del contrato (decide el DEV)

- Cómo usa `camera` y `google_mlkit_text_recognition` dentro del ADR-0017 (la versión exacta la fija CONTRATO-MIGRACION-FLUTTER §6), y cómo se borra la foto temporal (siempre en un `finally`) (**v6**).
- La resolución de la foto y el recorte al marco.
- Cómo compila el APK de depuración en la máquina del proyecto (**v6**: ya no hay EAS; la respuesta 2 de abajo queda como historia).

## Preguntas abiertas para el humano

Respuestas del humano (vía PM, 2026-11-19):

1. **Dispositivo (PA #12):** un **Samsung Galaxy S23 Ultra**, que se puede conectar por USB, con **Android 16** (confirmado por el humano vía PM, 2026-11-19). Faltan en esta PC `adb` (Android platform-tools) y quizá el driver USB de Samsung; las instrucciones van en el encargo.
2. **Dev build:** **A, con EAS** (el humano tiene cuenta de Expo). Si se complica, B en local. El login lo hace el humano con `! npx eas login`; **nadie guarda el token en el repositorio**.
3. **Capturas físicas y precisión:** las fotos **las toma el humano**. La **precisión va aparte**, en la fase de pruebas del 16 al 26-dic; en este veredicto entra solo el paso a paso físico en el S23 Ultra (Android 16). Respuesta completa del humano (vía PM, 2026-11-19) → **v2**.
4. **PA #4 y PA #16:** se confirman los provisionales (≥ 90 % de día; la foto no se guarda).
5. **Decisiones 1 a 4:** aprobadas tal cual.

## Changelog

| Versión | Fecha | Cambio | Motivo | Aprobado por |
|---|---|---|---|---|
| v1 | 2026-11-19 | Versión inicial | Encargo PM → LEAD, Iteración 2, contrato 1 | Humano (vía PM), 2026-11-19 |
| v2 | 2026-11-19 | §7, "Qué se prueba dónde" y decisión 5: la precisión del OCR va aparte, en la fase de pruebas del 16 al 26-dic; en el veredicto entra solo el paso a paso físico en el S23 Ultra (Android 16), con las fotos tomadas por el humano | Respuesta del humano a la pregunta 3 | Humano (vía PM), 2026-11-19 |
| v3 | 2026-11-19 | §8 nuevo: el dev build llega a la API local por HTTPS con la CA de Caddy instalada en el teléfono, `network_security_config` con `debug-overrides` solo para depuración, `adb reverse tcp:8443`; el build de release no incluye el override; la CA y su llave nunca se versionan; pasos para el humano, incluido el borrado al cierre | Respuesta del humano a la ESCALA de la etapa 2 (opción B y sus 3 condiciones) | Humano (vía PM), 2026-11-19 |
| v4 | 2026-11-20 | §6: sin caché HTTP (`Cache-Control: no-store` en toda respuesta de `/v1`, la app con `fetch` y `cache: 'no-store'`, y `cache/http-cache` sin `/v1/` en el dispositivo); "Abrir ajustes" puede abrir la pantalla de permisos de la app | Hallazgos B y D de la prueba física en el S23 Ultra | Humano (vía PM), 2026-11-20 |
| v5 | 2026-11-20 | §3: aviso de telemetría de ML Kit en OCR-01 (la primera vez por sesión, solo en memoria; textos del UX y el BA); §6: título precisado (la foto y el texto leído) con la telemetría como excepción conocida, y la revisión de la cola en el dispositivo | Decisión del humano sobre el hallazgo C (opción A, puntos 3 y 5) | Humano (vía PM), 2026-11-20. No se guarda en la bitácora la constancia de "Entendido" en el MVP |
| v6 | 2026-11-24 | Se construye directo en Flutter: §1 con la interfaz Dart `LectorPlaca` (CONTRATO-MIGRACION-FLUTTER §2); `flutter_test` en lugar de Jest; §6 sin caché HTTP por `pubspec.yaml` y sin respuestas de `/v1/` en `cache/` y `files/` del teléfono, y `startImageStream` prohibido; §8 con el APK de depuración, `network_security_config.xml` a mano, la llave de firma fuera del repositorio y la CA del proxy (Caddy hasta DESPLIEGUE-01 v2); rutas del TESTER en `apps/movil/test/` e `integration_test/`. Los textos, las pantallas y los casos de §2 a §5 y §7 no cambian | Migración de la app a Flutter (ADR-0017, decisión del humano del 2026-11-24); HU-04 no se termina en Expo | Humano (vía PM), 2026-11-24 (con CONTRATO-MIGRACION-FLUTTER v1) |
