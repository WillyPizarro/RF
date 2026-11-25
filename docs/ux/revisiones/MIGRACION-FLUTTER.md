# Revisión UX — Migración a Flutter (rama `migracion-flutter`, entrega DEV `1382d13`)

Rol: UX. Fecha: 2026-11-24. Encargo: LEAD → UX (CONTRATO-MIGRACION-FLUTTER v1.3 §4 y §10).

**Resultado de las capturas de `flutter_test`: aprobado, con 3 observaciones (0 BLOQUEA).** Dos son regresiones de presentación frente a la app Expo y la tercera pide dos capturas que faltan. Ningún texto cambia y ninguna observación pide una versión nueva de contrato.

**§4 (safe area): pendiente.** Se aprueba solo con las capturas del S23 Ultra de la mini sesión del **miércoles 25-nov** (adelantada por el LEAD). La lista de capturas está en la sección "Capturas del S23 Ultra para el guion del TESTER".

## Qué se revisó

- **Capturas de `flutter_test`** (390 × 844 dp, ×3), en `Movil_Buscador_capturas/MIGRACION-FLUTTER/flutter_test` (fuera del repositorio). Son 30: AUTH-01, AUTH-01-vacios, AUTH-02, AUTH-03, AUTH-04, AUTH-otro-error, HOME-01-agente, HOME-revisor, HOME-supervisor, ERR-01, PLA-01, PLA-02-sin-motivo, PLA-02-otro-corto-y-PLA-03-formato, PLA-04-consultando, PLA-05-con-requisitoria, PLA-06-sin-requisitoria, PLA-07-error, PLA-08-no-registrada, PLA-01-con-placa-leida, OCR-01-aviso-mlkit, OCR-01, OCR-01-leyendo, OCR-02, OCR-03, OCR-04, BIT-01, BIT-01-filtros, BIT-01-vacia, BIT-01-error y BIT-02.
- **Comparadas con las capturas de Expo** ya aprobadas (`Movil_Buscador_capturas/HU-01-02`, `HU-01-02-v4`, `HU-03-07` y `HU-04`), para encontrar regresiones.
- **Referencias:**
  - Wireframes: `docs/ux/wireframes/HU-01-iniciar-sesion.md`, `HU-02-acceso-por-rol.md`, `HU-03-consultar-placa.md`, `HU-07-bitacora-consultas.md` y `HU-04-capturar-placa-ocr.md` (con el aviso de telemetría de OCR-01).
  - Revisiones anteriores: `HU-01-02.md`, `HU-03-07.md` y `HU-04.md` de esta carpeta.
  - Contratos: CONTRATO-HU-01 v6, HU-02 v4, HU-03 v5, HU-07 v5 y HU-04 v6, más CONTRATO-MIGRACION-FLUTTER v1.3 §4 y §10.
  - Avisos del DEV: `informes/DEV-MIGRACION-FLUTTER.md` §3.
- **Fuente, solo como apoyo** para ubicar la causa de las observaciones: `apps/movil/lib/app.dart`, `lib/pantallas/pantalla_ocr.dart`, `pantalla_bitacora.dart` y `comunes.dart`.

## Avisos del DEV (§3 del informe)

### 1. Mayúsculas de los botones: se aceptan como están escritos

**Decisión UX: no se piden mayúsculas.** Los botones quedan con el texto del contrato tal cual ("Ingresar", "Consultar", "Entendido", "Capturar"…).

- Es el estilo por defecto de Material 3 en Android, así que se ve como el resto del teléfono.
- Un texto en mayúscula y minúscula se lee más rápido que uno en mayúsculas sostenidas, sobre todo al sol y de un vistazo.
- No hace falta tocar el texto ni las pruebas (`find.text('Ingresar')` sigue igual).
- Los botones primarios se siguen distinguiendo por el fondo azul lleno, el alto y la negrita; los secundarios, por el borde. La jerarquía no dependía de las mayúsculas.
- **Wireframes:** las mayúsculas de los dibujos ASCII (`[ INGRESAR ]`, `[ ENTENDIDO ]`) son solo una notación de "botón". No se cambian; esta decisión deja constancia de que la app los muestra con el texto del contrato.

Si más adelante alguien pide mayúsculas, la única forma sin romper el contrato es mostrar `texto.toUpperCase()` y dejar el texto original en `Semantics(label: …)`. **No se recomienda:** las pruebas que buscan el texto visible tendrían que cambiar.

### 2. Símbolos que salen como cuadrados en `flutter_test`

Se acepta la explicación (sin fuentes de respaldo en `flutter_test`). En todas las capturas los símbolos están **en su lugar** (←, ✕, 📷, 🚗, ○/◉, ◉, ⚠, ⓘ, 🔒, ⛔, 📷✕, ▾), con el tamaño y el color esperados, pero su dibujo queda **NO VERIFICADO**. Se confirma con las capturas del S23 Ultra (lista abajo). Mientras tanto, el estado elegido de las opciones del motivo y de los filtros se distingue igual por el fondo celeste, así que la captura alcanza para revisar el resto.

### 3. Margen seguro simulado

Se acepta como vista previa, **no como aprobación de la §4**. Lo que sí se ve en las capturas y en `lib/app.dart`:

- La franja "DATOS SINTÉTICOS · PROTOTIPO" empieza debajo de la barra simulada de 40 dp, y la barra se pinta del mismo fondo oscuro, con íconos claros (`statusBarIconBrightness: Brightness.light`). Es la opción que pidió la obs. 2 de `HU-04.md`.
- El margen se resuelve **una sola vez** en la raíz (dos `SafeArea`: arriba sobre el fondo de la franja y abajo sobre el fondo de la app). Cumple "Una sola vez" de la §4.
- En OCR-01, "Capturar" e "Ingresar manualmente" quedan por encima de la franja simulada de gestos.

## Textos contra los contratos

Todos los textos visibles coinciden carácter por carácter con los contratos vigentes y con lo aprobado en Expo. **Ningún texto pide un cambio de contrato.**

| Pantalla | Qué pide el contrato o el wireframe | En la captura |
|---|---|---|
| Todas | "DATOS SINTÉTICOS · PROTOTIPO" | ✔ |
| AUTH-01 | "Movil Buscador" · "Usuario" · "Clave" · "Ingresar" | ✔ |
| AUTH-01 vacío | "Ingrese su usuario y su clave", ámbar, sin ícono | ✔ Igual que Expo v4 |
| AUTH-02 | ⚠ "Usuario o clave incorrectos"; usuario escrito, clave vacía | ✔ Rojo, con el ícono (cuadrado en `flutter_test`) |
| AUTH-03 | ⓘ "Su sesión se cerró por inactividad. Ingrese de nuevo." | ✔ Azul informativo, usuario vacío |
| AUTH-04 | 🔒 "Cuenta bloqueada temporalmente. Podrá volver a intentar a las HH:MM (en N min)." | ✔ "a las 21:26 (en 15 min)", ámbar |
| Otro error | "No se pudo completar la operación; intente nuevamente", gris neutro | ✔ |
| HOME-01 | "Hola, <nombre>" · "Rol: Agente" · "Salir" · 🚗 "Consultar placa" · "Verificar rostro" y "Mis verificaciones" deshabilitadas | ✔ "Salir" y "Mis verificaciones" de 48 dp de alto |
| Inicio del revisor / supervisor | "Rol: Revisor" · "Pendientes de revisión" (deshabilitada) / "Rol: Supervisor" · "Bitácora" | ✔ |
| ERR-01 | ⛔ · "No tiene permiso para usar esta función." · "El intento quedó registrado." · "Volver al inicio" | ✔ |
| PLA-01 | ← "Consultar placa" · "Placa" monoespaciada · 📷 habilitado · "Motivo de consulta *" como lista de opciones · "Consultar" | ✔ |
| PLA-02 / PLA-03 | "Indique el motivo de la consulta." · "Describa el motivo *" · "Describa el motivo (mínimo 10 caracteres)." · "El formato de placa no es válido. Formato esperado: …" · los dos mensajes juntos | ✔ Borde rojo y ⚠ bajo cada campo. El "Formato esperado: ABC-123" sale corto porque así viene la descripción en el catálogo simulado de la captura; la app la toma de la API |
| PLA-04 | "Consultando…" con la placa; el botón desactivado | ✔ |
| PLA-05 | ← "Resultado" · bloque rojo, placa y "TIENE REQUISITORIA" · "Motivo:" · "Consultado: dd/mm/aaaa hh:mm" · "Nueva consulta" | ✔ |
| PLA-06 | Gris neutro, "Sin requisitoria registrada en la fuente consultada", sin verde ni ✓ | ✔ |
| PLA-07 | ⚠ "No se pudo completar la consulta; intente nuevamente" · "Reintentar" · "Volver" | ✔ Ámbar, distinto de los resultados |
| PLA-08 | Gris azulado, "Placa no registrada en la fuente consultada. Verifique la placa." · solo "Volver" | ✔ Distinto de PLA-06 |
| OCR-01 aviso | "Antes de leer la placa" · el cuerpo de HU-04 v5 · "Entendido" · "Capturar" desactivado · "Ingresar manualmente" activo | ✔ El cuerpo se ve completo |
| OCR-01 | ✕ "Leer placa" · visor con marco · "Encuadre la placa y toque Capturar" · ◉ "Capturar" · "Ingresar manualmente" | ✔ |
| OCR-01 leyendo | Indicador "Cargando" sobre el visor; "Capturar" desactivado | ✔ con la observación 1 |
| OCR-02 | "Placa leída" · campo editable · "Confirme o corrija la placa antes de consultar." · "Usar esta placa" · "Volver a capturar" · ninguna imagen | ✔ |
| OCR-03 | ⚠ "No se pudo leer la placa. Pruebe de frente y con más luz." · "Volver a intentar" · "Ingresar manualmente" | ✔ |
| OCR-04 | 📷✕ "La app no tiene permiso para usar la cámara." · "Para darlo: Ajustes › Aplicaciones › Movil Buscador › Permisos › Cámara." · "Abrir ajustes" · "Ingresar manualmente" | ✔ |
| BIT-01 | `dd/mm hh:mm · usuario` · tipo · placa · resultado · "SINTÉTICO" · "Filtros" con "PA 24" · "Cargar más" | ✔ |
| BIT-01 filtros | "Usuario" · "Desde" · "Hasta" · "dd/mm/aaaa" · "Tipo" (9) · "Resultado" (4) · "Aplicar filtros" | ✔ los textos; la presentación tiene la observación 2 |
| BIT-01 vacía | "No hay registros para estos filtros." | ✔ |
| BIT-01 error | ⚠ "No se pudo cargar la bitácora; intente nuevamente" · "Reintentar" | ✔ Distinto de la lista vacía (regla 7) |
| BIT-02 | "Registro #<8 caracteres>" · 🔒 "Registro de solo lectura" · "ID:" completo · usuario, fecha y hora, tipo, placa, motivo y resultado · "Origen: datos sintéticos" | ✔ Igual que HU-07 v3 |

La palabra prohibida no aparece en ninguna captura.

## Observaciones

| # | Gravedad | Pantalla | Observación | Quién la resuelve |
|---|---|---|---|---|
| 1 | No bloquea (MEJORA, regresión) | OCR-01 leyendo | **El círculo oscuro del indicador de carga ocupa todo el visor** (unos 390 dp de diámetro) y tapa parte del marco. En Expo era un círculo chico, centrado en el marco (obs. 1 de `HU-04.md`, resuelta en `3367787`). Causa probable: `Espera` envuelve el indicador en un `Center`, que se expande, y el `Container` circular de `pantalla_ocr.dart` (~l. 212) toma todo el espacio. Basta con fijarle un tamaño al círculo (por ejemplo, 76 × 76 dp: 40 del indicador más 18 de margen por lado) o sacar el `Center` de `Espera` en ese uso. Sin texto nuevo | DEV |
| 2 | No bloquea (MEJORA, regresión) | BIT-01 filtros | **Las opciones de "Tipo" y "Resultado" ocupan cada una todo el ancho, una por fila.** En Expo se agrupaban varias por fila, como etiquetas. Ahora el panel crece hasta casi dos pantallas y "Aplicar filtros" queda fuera de la vista: el supervisor tiene que desplazarse para aplicar. Causa probable: en `_Chips` (`pantalla_bitacora.dart`, ~l. 430), el `Container` con `alignment: Alignment.center` se estira al ancho disponible dentro del `Wrap`. Basta con quitar el `alignment` (o envolver el texto en un `Center(widthFactor: 1)`) para que cada opción mida lo que su texto. Sin texto nuevo. Mantener el alto mínimo de 36 dp y, si se puede, subirlo a 48 dp para uso con guantes | DEV |
| 3 | No bloquea | PLA-01 sin catálogo y BIT-01 fecha inválida | **Faltan dos capturas de `flutter_test`** de estados que fija el contrato y que se aprobaron en Expo: PLA-01 cuando falla `GET /v1/motivos` (HU-03 v4: ⚠, "No se pudo completar la consulta; intente nuevamente", "Reintentar" y "Volver", sin formulario) y BIT-01 con una fecha que no existe (HU-07 v3: "Use fechas con el formato dd/mm/aaaa."). Pido las dos para cerrar la revisión de textos | DEV (las genera su paquete de capturas) |

## Notas (sin observación)

- **PLA-02 con la placa vacía** muestra también "El formato de placa no es válido…". Es igual que en Expo (`PantallaPlaca.tsx` validaba la placa vacía con la misma expresión) y cumple el contrato ("Si faltan el motivo y el formato, se muestran los dos mensajes").
- **OCR-01 leyendo:** el degradado gris sobre "Capturar" es la animación del toque (*ripple*) congelada en la captura. No es un estado de la pantalla.
- **OCR-01:** el visor de `flutter_test` es gris oscuro y el de Expo era negro. Sin cámara no hay imagen en ninguno de los dos; en el teléfono se ve la cámara.
- **BIT-01:** el borde del panel de filtros pasó de punteado (Expo) a continuo. Se acepta.
- **Accesibilidad** (no se ve en una captura; según el informe del DEV, §3): etiquetas exactas en los campos, "Atrás", "Cerrar" y "Leer con cámara" en los botones de un símbolo, y "Ingresando" y "Cargando" en los indicadores. Las comprueba el TESTER con `find.bySemanticsLabel`.

## Capturas del S23 Ultra para el guion del TESTER (mini sesión del miércoles 25-nov)

Van a `Movil_Buscador_capturas/MIGRACION-FLUTTER/s23/` (fuera del repositorio), con el APK de depuración contra la API local, **datos sintéticos** y placas `ZZ…`. Captura de pantalla completa del teléfono (con la barra de estado y la de navegación), no del área de la app.

**Antes de empezar:** anotar en el guion el modo de navegación del teléfono (Ajustes › Pantalla › Barra de navegación: "Gestos de deslizar" o "Botones").

### A. Para aprobar la §4 (safe area) — obligatorias

Si alguna falla, la §4 queda **BLOQUEA** (misma observación 2 de `HU-04.md`).

| # | Pantalla | Qué tiene que verse |
|---|---|---|
| S1 | HOME-01 (agente) | La hora, la señal y la batería completas y legibles en claro sobre el fondo oscuro; la franja "DATOS SINTÉTICOS · PROTOTIPO" entera, justo debajo, sin superponerse |
| S2 | PLA-01 (sin teclado) | Lo mismo arriba; "Consultar" lejos de la barra de abajo |
| S3 | OCR-01 con el visor de la cámara (después de "Entendido") | Lo mismo arriba; "Capturar" e "Ingresar manualmente" enteros y por encima de la línea de gestos o de los botones de navegación |
| S4 | OCR-02 | Lo mismo arriba; "Usar esta placa" y "Volver a capturar" visibles |
| S5 | OCR-01 en el **otro** modo de navegación (si el teléfono estaba en gestos, cambiar a botones, o al revés) | Los botones de abajo no quedan bajo la barra de navegación, que en modo botones es más alta |

### B. Otras pantallas en el teléfono — no bloquean la §4, cierran puntos pendientes

| # | Pantalla | Qué se mira | Pendiente que cierra |
|---|---|---|---|
| S6 | OCR-01 con el aviso de ML Kit | La tarjeta sobre el visor atenuado; el cuerpo completo | Aviso de telemetría (HU-04 v5) |
| S7 | OCR-01 con el aviso y la **letra del sistema al máximo** (Ajustes › Pantalla › Tamaño y estilo de fuente) | El cuerpo del aviso se lee completo, sin cortes; "Entendido" a la vista o alcanzable desplazando | Accesibilidad del aviso (`HU-04.md`) |
| S8 | OCR-01 leyendo, con la cámara apuntando a una placa impresa, de día | El indicador de carga se ve sobre la imagen real (y con la observación 1 ya resuelta, chico y centrado en el marco) | Etapa 2 de `HU-04.md` |
| S9 | OCR-01 con el visor sobre una placa impresa a la distancia habitual (1 a 2 m) | El contraste del marco blanco sobre la imagen real y que la placa entre en el marco | Etapa 2 de `HU-04.md` |
| S10 | OCR-04 y la pantalla a la que lleva "Abrir ajustes" (dos capturas) | El 📷✕ se dibuja; "Abrir ajustes" abre la información de la app, con "Permisos" a mano | Etapa 2 de `HU-04.md` y aviso 2 del DEV |
| S11 | PLA-01 con una opción de motivo elegida y el teclado abierto en "Placa" | Se dibujan ←, 📷 y ○/◉; el teclado sale en mayúsculas; "Consultar" se alcanza desplazando | Aviso 2 del DEV |
| S12 | PLA-02 + PLA-03 (placa inválida y sin motivo) | Se dibuja el ⚠ en los dos mensajes | Aviso 2 del DEV |
| S13 | AUTH-02 (clave errada) | Se dibuja el ⚠ | Aviso 2 del DEV |
| S14 | BIT-01 con los filtros abiertos y el teclado de "Desde" (supervisor) | El teclado es numérico con "/" (obs. 4 de `HU-03-07.md`); las opciones de "Tipo" agrupadas (con la observación 2 resuelta) | `HU-03-07.md` obs. 4 y observación 2 |
| S15 | BIT-02 | Se dibuja el 🔒 | Aviso 2 del DEV |

**No hace falta en el teléfono:** AUTH-03, AUTH-04, ERR-01 ni PLA-05 a PLA-08. Sus textos y colores ya se aprobaron con `flutter_test`, y sus símbolos usan la misma fuente de respaldo que los de S10 a S15. Si en S10 a S15 algún símbolo sale como cuadrado, entonces sí hay que revisar todos.

## Qué falta para el aprobado final

1. Las capturas S1 a S5 (§4).
2. La corrección de las observaciones 1 y 2 y las dos capturas de la observación 3; se confirman con capturas nuevas de `flutter_test` (y S8 y S14 en el teléfono, si la corrección llega antes del miércoles).
3. S6 a S15 cierran los pendientes de la etapa 2 de HU-04 y el aviso 2 del DEV.

## Confirmación (entrega DEV `0724e88`, M-7, 2026-11-24)

**Resultado: observaciones 1 a 3 cerradas.** Las capturas de `flutter_test` quedan aprobadas. La §4 (safe area) sigue **pendiente** de las capturas S1 a S5 del S23 Ultra (mini sesión del miércoles 25-nov).

- **Qué se revisó:** las capturas nuevas OCR-01-leyendo, BIT-01-filtros, PLA-01-sin-catalogo y BIT-01-fecha-invalida (ahora son 32), y el diff de `0724e88` (`pantalla_ocr.dart` y `pantalla_bitacora.dart`).
- **Contra qué:** las observaciones 1 a 3 de esta revisión, CONTRATO-HU-03 v5 y HU-07 v5, y las capturas de Expo aprobadas.

| # | Observación | Estado | Comprobación |
|---|---|---|---|
| 1 | Círculo del indicador en OCR-01 leyendo | ✔ Resuelta | El círculo mide 76 × 76 dp y queda centrado dentro del marco, sin taparlo ni cubrir el visor. "Capturar" queda desactivado e "Ingresar manualmente" sigue activo. Sin texto nuevo |
| 2 | Opciones de filtro en BIT-01 | ✔ Resuelta | Cada opción mide lo que su texto y caben dos por fila, como en Expo. Además subieron a 48 dp de alto (lo que se pidió "si se puede"). Con 48 dp el panel queda algo más largo que en Expo, así que "Aplicar filtros" se alcanza con un desplazamiento corto (se ve en BIT-01-fecha-invalida). Se acepta: el alto táctil vale más para el uso con guantes. Sin texto nuevo |
| 3 | Capturas que faltaban | ✔ Resuelta | **PLA-01 sin catálogo:** ⚠, "No se pudo completar la consulta; intente nuevamente", "Reintentar" y "Volver", sin el formulario, en ámbar. Coincide con HU-03 v4 y con Expo, y cumple la regla 7. **BIT-01 con fecha inválida:** "31/02/2026" en "Desde", con borde de foco y "Use fechas con el formato dd/mm/aaaa." en rojo bajo el campo. Coincide con HU-07 v3 |

- **Regresiones:** no se ven en las pantallas recapturadas. El resto del diff de `0724e88` es solo formato (cortes de línea en `pantalla_bitacora.dart`) y no cambia nada visible.
- **Para el teléfono:** S8 y S14 de la lista confirman estas dos correcciones sobre la cámara real y con el teclado abierto.
