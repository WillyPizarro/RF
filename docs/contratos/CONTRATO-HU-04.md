# CONTRATO — HU-04 Capturar la placa con la cámara

**Tipo:** Feature
**Versión:** v3
**Estado:** Aprobado (v1 a v3: 2026-11-19, humano vía PM)
**Origen:** `docs/hus/HU-04-capturar-placa-ocr.md` · encargo PM → LEAD (2026-11-19), Iteración 2, contrato 1
**Rama de trabajo:** `hu-04`, desde `main` `fa75945` (humano vía PM, 2026-11-19)
**Pasa por UX:** sí. Pantallas OCR-01 a OCR-04 (`docs/ux/wireframes/HU-04-capturar-placa-ocr.md`) y el botón 📷 de PLA-01. El UX revisa con capturas de Jest y, si hay dispositivo, con capturas del dev build.

---

## Paquete de contexto

| Fuente | Por qué entra |
|---|---|
| HU-04 | Historia, escenarios 1 a 3, supuestos (lectura en el dispositivo, la foto no se guarda, nunca se consulta sin confirmar) |
| Wireframes OCR-01 a OCR-04 | Pantallas, textos y botones; "Abrir ajustes" aprobado el 2026-11-18 |
| ADR-0002 | Expo **dev build** (no Expo Go), `react-native-vision-camera` como referencia, ML Kit Text Recognition en el dispositivo, nada de imágenes en disco |
| ADR-0010 | Android primero, con un celular de referencia; el OCR funciona sin red; iOS no se prueba hasta el PA #12 |
| ADR-0011 | Precisión provisional del OCR: ≥ 90 % de lecturas exactas de día en ≥ 100 imágenes con el celular de referencia; de noche o en ángulo se mide y se reporta (PA #4) |
| ADR-0013 | Estado de la app solo en memoria; se limpia al cerrar la sesión |
| TECH-DESIGN.md › Criterios › Consulta de placa (HU-03, HU-04) y matriz de tratamiento | "El OCR deja el texto en un campo editable y no se envía ninguna consulta sin la confirmación del usuario"; la imagen de la placa no se guarda y se procesa en el dispositivo |
| CONTRATO-HU-03 v4 | PLA-01 (el botón 📷 queda deshabilitado hasta HU-04), `formato_placa` de `GET /v1/motivos` y el resto de la consulta, **sin cambios** |
| CONTRATO-HU-08 v4 | Placas sintéticas con prefijo `ZZ` (`ZZA-101`, `ZZB-201`, `ZZZ-999`…) |
| AGENTS.md, reglas 2, 6, 7 y 8 | Motivo obligatorio; sin lectura automática de placas; ningún error se convierte en un negativo; ninguna foto en el repositorio |

## Interfaz observable

1. **App (Jest):** se monta el export por defecto de `App.tsx`, como en CONTRATO-HU-01 §4 bis. La cámara y el OCR se reemplazan por el **módulo de borde** del §1, simulado.
2. **App (dispositivo):** dev build en un Android real. Lo que solo se ve ahí está en el §6.
3. **API:** sin cambios. La consulta sigue siendo `POST /v1/consultas/placa` de CONTRATO-HU-03 v4.

## Comportamiento

### 1. Módulo de borde para las pruebas (DECISIÓN PROPUESTA 1)

La cámara y ML Kit son módulos nativos y no corren en Jest. El DEV expone toda la cámara y el OCR a través de **un solo módulo**, `apps/movil/src/camara/lectorPlaca.ts`, con esta forma (TypeScript). El TESTER lo simula con `jest.mock`:

```ts
export type PermisoCamara = 'concedido' | 'denegado';
/** Si nunca se pidió, lo pide al sistema. No abre la cámara. */
export function asegurarPermisoCamara(): Promise<PermisoCamara>;
/** El visor en vivo de OCR-01. No lee nada por su cuenta. */
export function VisorCamara(props: { activo: boolean }): JSX.Element;
/** Toma UNA foto, la lee con OCR en el dispositivo, borra la foto y devuelve solo el texto.
 *  `texto` es null si no se reconoció ningún texto. Rechaza (throw) si la cámara falla. */
export function capturarYLeer(): Promise<{ texto: string | null }>;
/** Abre los ajustes de la app en el sistema (OCR-04). */
export function abrirAjustes(): Promise<void>;
```

Nada fuera de este módulo importa directamente la librería de cámara ni la de ML Kit (se comprueba con `grep` en `apps/movil/src`). Ninguna función del módulo devuelve una ruta de archivo ni una imagen.

### 2. Entrada desde PLA-01

| Caso | Acción | Resultado visible | Origen |
|---|---|---|---|
| Botón habilitado | PLA-01 | El botón 📷 (`accessibilityLabel="Leer con cámara"`) queda **habilitado** | CONTRATO-HU-03 §6 (deshabilitado hasta HU-04), wireframe HU-03 |
| Permiso concedido | Tocar 📷; `asegurarPermisoCamara()` → `concedido` | OCR-01 | Gherkin esc. 1 |
| Permiso denegado | Tocar 📷; `asegurarPermisoCamara()` → `denegado` | OCR-04. `capturarYLeer` nunca se llama | Gherkin esc. 3 |

### 3. Captura (OCR-01 → OCR-02 u OCR-03)

| Caso | Entrada | Resultado visible | Origen |
|---|---|---|---|
| Visor | Se abre OCR-01 | "Leer placa", el visor (`VisorCamara` con `activo` en `true`), "Encuadre la placa y toque Capturar", "Capturar", "Ingresar manualmente" y "✕". **`capturarYLeer` no se llama** mientras no se toque "Capturar", por más tiempo que pase | OCR-01, regla 6 |
| Una sola foto | Tocar "Capturar" | `capturarYLeer` se llama **exactamente una vez** por toque. Mientras espera, "Capturar" queda desactivado (un segundo toque no dispara otra lectura) | OCR-01, regla 6 |
| Lectura con placa | `texto` contiene un candidato que cumple `formato_placa.regex` (§4) | OCR-02 con ese candidato en el campo editable | Gherkin esc. 1 |
| Lectura sin placa | `texto` es `null`, vacío o no tiene ningún candidato que cumpla la regex | OCR-03 | Gherkin esc. 2 · DECISIÓN PROPUESTA 2 |
| Falla de la cámara | `capturarYLeer` rechaza | OCR-03 (nunca una pantalla en blanco ni un resultado) | Gherkin esc. 2, regla 7 |
| Salir | "✕" en OCR-01 | Vuelve a PLA-01 **sin cambios** (la placa y el motivo quedan como estaban) | OCR-01 |
| Ingreso manual | "Ingresar manualmente" (en OCR-01, OCR-03 u OCR-04) | Vuelve a PLA-01 sin cambios, con el foco en el campo "Placa" | OCR-01, OCR-03, OCR-04 |
| Sin red | En el dispositivo, en modo avión | OCR-01 a OCR-03 funcionan igual (la lectura es local). La consulta posterior se comporta como en HU-03 sin red (PLA-07) | ADR-0010 |

### 4. Del texto leído a la placa propuesta (DECISIÓN PROPUESTA 2)

La app pasa el texto a mayúsculas y lo separa en líneas. En cada línea busca candidatos que cumplan `formato_placa.regex` (de `GET /v1/motivos`, CONTRATO-HU-03 v3), probando primero el texto tal cual y después con los espacios o el punto entre los dos grupos cambiados por un guion. Propone **el primer candidato** que cumpla. Con la regex por defecto, los ejemplos que fijan el resultado (el TESTER los usa en Jest) son:

| `texto` de `capturarYLeer` | Pantalla y valor del campo |
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
| Nunca consulta sola | "Usar esta placa" | Vuelve a PLA-01 con la placa cargada. **El motivo queda como estaba antes de abrir la cámara**: si estaba vacío, sigue vacío. **No se envía ninguna solicitud**: entre el toque de 📷 y el de "Consultar" en PLA-01, el `fetch` simulado no recibe ninguna llamada | Encargo PM, HU-04 supuestos, TECH-DESIGN · DECISIÓN PROPUESTA 3 |
| Sigue HU-03 | En PLA-01, el agente elige el motivo y toca "Consultar" | Todo sigue igual que en CONTRATO-HU-03 v4: validación local de PLA-02 y PLA-03 (también con lo corregido), PLA-04 a PLA-08 | CONTRATO-HU-03 v4 |
| Volver a capturar | "Volver a capturar" | OCR-01 (el valor leído se descarta) | OCR-02 |
| Reintentar | "Volver a intentar" en OCR-03 | OCR-01 | OCR-03, Gherkin esc. 2 |
| Abrir ajustes | "Abrir ajustes" en OCR-04 | Se llama `abrirAjustes()` | OCR-04 |
| Volver con permiso | Después de OCR-04, el usuario da el permiso en Ajustes y vuelve a tocar 📷 | `asegurarPermisoCamara()` → `concedido` → OCR-01 | Gherkin esc. 3 |

### 6. Nada se guarda ni sale del dispositivo

| Caso | Cómo se observa | Dónde | Origen |
|---|---|---|---|
| La foto no llega a la API | En todo el flujo de OCR-01 a OCR-03, el `fetch` simulado no recibe ninguna llamada; y en la consulta posterior, el cuerpo de `POST /v1/consultas/placa` es el de HU-03 (sin imagen ni campos nuevos) | Jest | HU-04 supuestos, ADR-0002 |
| Nada en el almacenamiento | Después de leer, el `expo-secure-store` simulado no tiene ninguna clave nueva | Jest | ADR-0013 |
| La foto se borra | En el dev build, después de 10 capturas seguidas, `adb shell run-as pe.prototipo.movilbuscador find . -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png"` no devuelve ningún archivo de captura (en `files/` ni en `cache/`). La galería del teléfono no tiene fotos nuevas | Dispositivo | ADR-0002, HU-04 supuestos, TECH-DESIGN (matriz de tratamiento) |
| Sin lectura continua | En el dev build, con la cámara apuntando a una placa impresa durante 30 s sin tocar "Capturar", no aparece OCR-02 | Dispositivo | Regla 6 |
| La placa se lee | En el dev build, una placa sintética impresa (§7) se lee y aparece en OCR-02 | Dispositivo | Gherkin esc. 1 |
| Permiso real | En el dev build, negar el permiso de cámara en el diálogo del sistema muestra OCR-04, y "Abrir ajustes" abre la pantalla de la app en Ajustes | Dispositivo | Gherkin esc. 3 |

### 7. Precisión del OCR y placas de prueba (provisional, PA #4)

| Caso | Salida esperada | Origen |
|---|---|---|
| Placas de prueba | Solo **placas sintéticas impresas** con el prefijo `ZZ` de HU-08 (por ejemplo `ZZA-101`, `ZZB-201`, `ZZZ-999` y otras de la semilla), en papel y del tamaño de una placa, con la leyenda **"PRUEBA — NO VÁLIDA"** en letra chica. **Nunca placas de vehículos reales** | Encargo PM, regla 8 · DECISIÓN PROPUESTA 4 |
| Precisión de día | ≥ 90 % de lecturas exactas (lo que muestra OCR-02 es igual a la placa impresa, antes de corregir) en ≥ 100 capturas de día con el celular de referencia | ADR-0011 · **v2: va aparte**, en la fase de pruebas del 16 al 26-dic (como el p95 de HU-03), **no en este veredicto** |
| De noche o en ángulo | Se mide y se reporta, sin meta, en la misma medición aparte | ADR-0011 · v2 |
| Registro | Las capturas no se guardan. Se registra solo la placa impresa, lo leído, la condición (día, noche, ángulo, distancia) y si coincide, en `pruebas/datos/ocr-precision.csv`. **Ninguna imagen** | Regla 8, ADR-0002 |

### 8. Conexión del dev build con la API local (v3)

El dev build en el S23 Ultra llega a la API local por HTTPS, con la CA local de Caddy (opción B del humano, 2026-11-19).

| Caso | Salida esperada | Dónde | Origen |
|---|---|---|---|
| Conexión | Con la CA local de Caddy instalada en el teléfono como certificado del usuario y `adb reverse tcp:8443 tcp:8443`, el dev build (con `EXPO_PUBLIC_API_URL=https://localhost:8443`) inicia sesión y carga `GET /v1/motivos` | Dispositivo | Humano (vía PM) · **v3** |
| Confianza solo en depuración | El `network_security_config` de Android confía en los certificados del usuario **solo dentro de `<debug-overrides>`**. El `base-config` confía únicamente en los certificados del sistema y no permite texto plano | Archivo generado (`npx expo prebuild` en una copia fuera del repositorio) | Humano (vía PM) · **v3** |
| El build de release no incluye el override | En la variante `release`, la app no es depurable (`android:debuggable` no es `true`), así que Android ignora `<debug-overrides>`. Si se genera un APK de release, `aapt dump xmltree` (o `apkanalyzer`) sobre su manifiesto lo confirma | Archivo generado o APK de release | Condición 3 del humano · **v3** |
| Sin secretos | La CA de Caddy y su llave privada **nunca** se versionan. `git ls-files` no muestra ningún `.crt`, `.pem`, `.key` ni `.der`, y `.gitignore` los excluye | Repositorio | Condición 2 del humano, regla 8 · **v3** |
| Pasos para el humano | En `informes/DEV-HU-04.md`: pasos numerados en español simple, para Samsung con Android 16, para **exportar** la CA desde el contenedor `proxy`, **instalarla** en el teléfono, usar `adb reverse` y **borrarla** al cierre del proyecto | Informe del DEV | Condición 1 del humano · **v3** |

## Nombres que no se negocian

| Tipo | Valor exacto |
|---|---|
| Módulo de borde | `apps/movil/src/camara/lectorPlaca.ts` · `asegurarPermisoCamara` · `VisorCamara` · `capturarYLeer` · `abrirAjustes` · `'concedido'` · `'denegado'` |
| Botón de PLA-01 | `accessibilityLabel="Leer con cámara"` (📷) |
| OCR-01 | "Leer placa" · "Encuadre la placa y toque Capturar" · "Capturar" · "Ingresar manualmente" |
| OCR-02 | "Placa leída" · "Confirme o corrija la placa antes de consultar." · "Usar esta placa" · "Volver a capturar" |
| OCR-03 | "No se pudo leer la placa. Pruebe de frente y con más luz." · "Volver a intentar" · "Ingresar manualmente" |
| OCR-04 | "La app no tiene permiso para usar la cámara." · "Para darlo: Ajustes › Aplicaciones › Movil Buscador › Permisos › Cámara." · "Abrir ajustes" · "Ingresar manualmente" |
| Archivo de precisión | `pruebas/datos/ocr-precision.csv` |
| API | Sin cambios (CONTRATO-HU-03 v4) |

## Qué se prueba dónde

| Parte | Jest (OCR simulado con el módulo de borde) | Android real con dev build |
|---|---|---|
| Botón 📷 habilitado, entrada por permiso (§2) | Sí | Permiso real del sistema (§6) |
| Una sola lectura por toque, nada sin tocar (§3) | Sí, contando las llamadas a `capturarYLeer` | Sí, 30 s sin tocar (§6) |
| Texto → placa propuesta (§4) | Sí, la tabla completa | — |
| Confirmar, corregir, volver; nunca consulta sola (§5) | Sí, contando las llamadas a `fetch` | Paso a paso, una vez |
| Nada en SecureStore ni a la API (§6) | Sí | — |
| La foto se borra del disco (§6) | No (no hay disco) | Sí, con `adb` |
| La placa impresa se lee de verdad (§6) | No | Sí |
| Precisión (§7) | No | **Aparte**, en la fase de pruebas (v2) |
| Sin red (§3) | No | Sí, en modo avión |
| Conexión a la API local con la CA de Caddy (§8) | No | Sí |
| Override solo en depuración; sin secretos (§8) | No (no hay build) | Archivo generado o APK de release, y `git ls-files` |

**Expo Go no sirve** (ADR-0002): todo lo de la columna derecha exige el dev build. Si no hay dispositivo o dev build a tiempo, esa columna queda `NO VERIFICADO` y se escala.

## Rutas de cada rol

| Rol | Rutas | Origen |
|---|---|---|
| TESTER | `apps/movil/__tests__/`, `apps/movil/.maestro/` (si se usa en el dev build), `pruebas/datos/` (el CSV de precisión y el guion de las pruebas físicas, sin imágenes), `informes/TESTER-*.md` | AGENTS.md |
| DEV | `apps/movil/` (salvo `__tests__/` y `.maestro/`), incluidos `app.json` (permiso de cámara, plugins) y `package.json`; `informes/DEV-*.md` | AGENTS.md |

Las placas impresas y las capturas de pantalla del dispositivo quedan **fuera del repositorio**.

## Avisos de contexto

- **Riesgo (ADR-0002):** ML Kit lee texto y no conoce las placas peruanas. Por eso la app valida con la regex y el usuario siempre confirma (§4 y §5).
- **Versión del SDK:** los módulos nativos atan la app a Expo SDK 58 (ADR-0002). No se actualiza el SDK en esta HU.
- **Cuota y tiempos de build:** cada cambio nativo exige un dev build nuevo (EAS o local).
- **iOS** queda fuera hasta el PA #12 (ADR-0010).

## Decisiones propuestas (no venían en la tarea)

| # | Decisión | Por qué hace falta | Estado |
|---|---|---|---|
| 1 | Módulo de borde `src/camara/lectorPlaca.ts` con 4 funciones fijas, que el TESTER simula en Jest | Sin una interfaz fija, la prueba tendría que conocer la librería que elija el DEV (como pasó en HU-01, §4 bis) | Aprobada por el humano (vía PM, 2026-11-19) |
| 2 | La placa propuesta es el primer candidato que cumple `formato_placa.regex` (con los espacios o el punto cambiados por guion). Si no hay ninguno, OCR-03, y la app no adivina caracteres (`O`/`0`) | Ni la HU ni el wireframe dicen qué hacer con texto que no es una placa. Mostrarlo igual invitaría a consultar basura | Aprobada por el humano (vía PM, 2026-11-19) |
| 3 | "Usar esta placa" conserva el motivo que ya estaba elegido; si no había, queda vacío | El wireframe dice "donde falta el motivo", pero no aclara si se borra uno ya elegido | Aprobada por el humano (vía PM, 2026-11-19) |
| 4 | Placas impresas en papel con el prefijo `ZZ` y la leyenda "PRUEBA — NO VÁLIDA" | Pedido del PM: nada de placas reales, y que la impresa no pueda confundirse con una placa oficial | Aprobada por el humano (vía PM, 2026-11-19) |
| 5 | La medición de precisión (≥ 100 capturas de día, ≥ 90 %) **va aparte**, en la fase de pruebas del 16 al 26-dic, como el p95 de HU-03. En el veredicto de HU-04 entra solo el paso a paso físico en el S23 Ultra (Android 16) | ADR-0011 la fija como criterio, pero depende de que el humano tome ≥ 100 fotos | Aprobada por el humano (vía PM, 2026-11-19) · **v2** |

## Fuera del contrato (decide el DEV)

- Las librerías concretas de cámara y de ML Kit, dentro del ADR-0002 (referencia: `react-native-vision-camera` y un wrapper de ML Kit Text Recognition compatible con Expo SDK 58), y cómo se borra la foto temporal.
- La resolución de la foto y el recorte al marco.
- Cómo se genera el dev build (EAS o local), según la respuesta a la pregunta 2.

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
