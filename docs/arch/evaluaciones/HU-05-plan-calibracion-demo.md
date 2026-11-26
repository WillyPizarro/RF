# Plan ARCH + TESTER — Calibración de demo de los umbrales faciales (HU-05 P1)

- **Fecha:** 2026-11-25. Coincide con la corrección final conjunta que el LEAD le pasó al PM el 25-nov.
- **Pedido por:** LEAD, a pedido del PM (pregunta 1 de CONTRATO-HU-05). Lo armaron el TESTER y el ARCH en respuestas conjuntas que coordinó el TESTER.
- **Aprobado por el humano (vía LEAD, 25-nov):** el plan (5 personas, de 10 a 12 fotos en 2 días y 1 foto de galería) y la opción (b) para los recortes. **Pendiente:** la regla del umbral alto (sección 4).
- **Tipo:** plan, sin código. **No cambia el ADR-0004**: es una calibración **de demo**, provisional y con una muestra chica. La calibración del ADR-0004 §3 (unas 20 personas) y la recalibración de producción (TECH-DESIGN, brecha 6) siguen vigentes.

## 1. Alcance y límites

- Hay **5 personas** del equipo con consentimiento ampliado (ADR-0008). La fecha de firma todavía no está. **Sin consentimiento firmado no se toma ninguna foto**, ni siquiera las del piloto.
- Los umbrales que salgan valen **solo para la demo** y se marcan **PROVISIONALES, n = 5**.
- **No se puede demostrar FMR ≤ 0,1 %**, la meta del ADR-0004 §3 y del criterio de aceptación de TECH-DESIGN ("Umbrales"). Para eso hacen falta al menos 3.000 pares impostores independientes, y con 5 personas no los hay. El criterio queda **sin cumplir en la demo**, y se dice así.

## 2. Fotos

| Qué | Plan |
|---|---|
| Por persona | **6 + 6** fotos de prueba en **2 días distintos** (como mínimo 5 + 5), más **1 foto de galería** tipo ficha, fuera de los dos sets |
| Separación (ADR-0004 §3) | **Por día:** el día 1 calibra y el día 2 evalúa. Con 5 personas no se puede separar por persona |
| Galería | De frente, expresión neutra, luz pareja y fondo liso. Conviene tomarla **en otro momento** que el día 1. Si se toma ese día, se anota, porque los genuinos del día 1 contra la galería salen mejores que los del día 2 |
| Variación | Luz interior, exterior a la sombra y contraluz suave; con y sin lentes; fondos distintos en cada foto de prueba (y distintos del de la galería); giros e inclinaciones **dentro** de lo que acepta la app (≤ 20°), con una foto por día cerca del borde (15° a 20°). El día 2, los giros van al lado contrario |
| Encuadre (corrige la versión inicial del plan) | La app rechaza un rostro que ocupa menos del 20 % del ancho de la foto (CONTRATO-HU-05 §5, "Acérquese más"). A 1 m o 1,5 m con la cámara en 1x, el rostro queda muy por debajo de eso, según una estimación sin medir. Por eso la distancia se fija **por encuadre, no en metros**: con el teléfono en **vertical**, el rostro ocupa entre un cuarto y un tercio del ancho de la foto (a ojo, de 40 a 65 cm), y hay **1 foto por día cerca del 20 %**. Con el piloto, el DEV mide con ML Kit qué porcentaje del ancho ocupa el rostro |
| Piloto (2 o 3 fotos por persona) | Es un **set aparte**. Sirve **solo** para comprobar que el recorte de la opción (b) sale idéntico al de la app y para ver los primeros scores. **No cuenta para el día 1**, ni en la calibración ni en la evaluación. Después se borra con acta o queda como set piloto |

## 3. Toma y recortes (opción b)

1. **El S23 de prueba, cámara trasera principal en 1x**, igual que ROS-02. Sin zoom, sin modo retrato, sin filtros ni "belleza" y sin flash. La foto la toma otra persona del equipo.
2. **Ajustes del S23:**
   - Formato **JPEG**, no HEIF ("Imágenes de alta eficiencia" apagado).
   - Apagados: el optimizador de escenas, el HDR automático, las fotos en movimiento y las **etiquetas de ubicación** (sin GPS en el EXIF; ADR-0008).
   - La copia en la nube de la galería, también apagada.
3. **Resolución y relación de aspecto:** las confirma el DEV, iguales a las de la app. Mientras el DEV no la confirme, se asume **720p si la app usa `ResolutionPreset.high`**. Como la cámara del S23 no saca fotos a esa resolución, se toma con la **misma relación de aspecto** que la app y la PC reduce cada foto a la resolución de la app **antes** de reproducir el recorte.
4. **En la PC, en este orden:**
   - Se aplica la orientación del EXIF (se rota la imagen), igual que hace la app.
   - Se borra el resto del EXIF.
   - Se reduce a la resolución de la app.
   - Se reproduce el recorte de la app con el mismo código (Dart o Python) y se codifica en JPEG de ≤ 1 MB.
5. **Comprobación de la (b):** con el piloto, el recorte de la PC tiene que salir **idéntico** al de la app (o con una diferencia que el DEV mida y declare) y pasar el mismo filtro de ML Kit. Si no sale idéntico, se pasa a la **opción (a)**: un modo solo de depuración que escriba los recortes, fuera del release y con una prueba de que el release no tiene ese código (CONTRATO-HU-05 v1.4, decisión del humano).
6. **Custodia:** cada persona tiene un código (P1 a P5) y la lista de nombres queda en papel, junto a los consentimientos. Las fotos salen del S23 **solo por cable USB**, nunca por correo, Drive, mensajería ni "compartir". Después se borran del S23 y de su papelera. En la PC quedan **solo en `PRUEBAS_ROSTROS_DIR`**, fuera del repositorio, y se borran al cierre con acta (regla 8 y ADR-0008).

## 4. Pares, límites y umbrales

**Esquema principal (todos contra todos dentro de cada set, 6 fotos por persona):**

| Set | Genuinos | Impostores | Límite con la regla de 3 si no hay errores (95 %) |
|---|---|---|---|
| Calibración (día 1) | 5 × C(6,2) = **75** | C(30,2) − 75 = **360** | FNMR ≤ 4 % · FMR ≤ 0,83 % |
| Evaluación (día 2) | **75** | **360** | ídem |
| Con 5 + 5 | 50 por set | 250 por set | FNMR ≤ 6 % (la meta del 5 % **no** se puede demostrar) · FMR ≤ 1,2 % |

- **Validación cruzada (propuesta del TESTER):** se calibra con el día 1 y se evalúa con el día 2, y después al revés. Se reportan las dos vueltas y el resultado combinado: cada par se evalúa una sola vez en su vuelta de prueba. Con 6 + 6, el combinado da 150 genuinos (FNMR ≤ 2 %) y 720 impostores (FMR ≤ 0,42 %).
- **Esquema contra la galería (más fiel a la operación):** cada foto de prueba se compara con la galería. La comparación con la propia foto de galería es un genuino y con las de los demás, un impostor. Con 6 pruebas por persona, cada set da 30 genuinos y 120 impostores. Se reporta aparte.
- **Advertencia obligatoria en el informe:** los impostores salen de **solo 10 parejas de personas** y los genuinos, de 5 personas. Los pares **no son independientes**, así que los límites de la regla de 3 son **nominales y optimistas**. Además del límite, se reporta el **score impostor máximo de cada pareja** y el **score genuino mínimo de cada persona**.

**Regla de los umbrales de demo (propuesta del ARCH, la decide el humano):**

- **Umbral alto:** el **mayor** entre (a) el score impostor máximo de la calibración más un margen y (b) el 0,363 de referencia de OpenCV (ADR-0004 §3). El margen lo propone el TESTER cuando vea la dispersión del piloto. **PROVISIONAL**.
- **Umbral bajo:** el valor que da FNMR ≤ 5 % sobre los genuinos de la calibración (ADR-0004 §3). Si queda mayor o igual que el alto, la banda "No concluyente" queda vacía y se reporta como hallazgo, sin forzarla.
- Los dos van a `MOTOR_UMBRAL_ALTO` y `MOTOR_UMBRAL_BAJO` con su `MOTOR_UMBRAL_VERSION`, marcados como de demo (CONTRATO-HU-05, "Umbrales configurables").

## 5. Impostores sintéticos de SFHQ (llegan el 26-nov; solo con aprobación del humano)

- **Sirven como resultado aparte, nunca como la FMR de la demo.** Son caras generadas (StyleGAN), de alta calidad, frontales, con otra distribución demográfica y sin la cámara del S23. Contra el equipo dan scores más bajos que un impostor real, así que la FMR saldría **subestimada**.
- **Dos usos válidos:**
  - La "FMR contra sintéticos", como control.
  - Si la galería de la demo tiene personas de SFHQ, los pares de una foto del equipo contra esa galería son los **impostores operativos de la demo**, y miden la **tasa de candidatos falsos contra esa galería**.
- No se usan para fijar el umbral alto ni para afirmar FMR ≤ 0,1 %.
- **La licencia de SFHQ está NO VERIFICADA:** la confirma quien la proponga, antes de usarla. Ninguna imagen va al repositorio.

## 6. Quién hace qué

| Rol | Tarea |
|---|---|
| Humano | Consentimientos, la toma de las fotos y la custodia de la lista P1 a P5 |
| DEV | Confirmar la resolución y la relación de aspecto de la app, sacar las fotos por USB y escribir el script del recorte de la (b) con su comprobación contra el piloto |
| TESTER | El cálculo de los scores, los dos esquemas, la validación cruzada y el informe con la advertencia n = 5 |
| ARCH | Revisar que el informe cumpla este plan y el ADR-0004, y llevar los umbrales a TECH-DESIGN como de demo |
| PM | El instructivo de fotos para el humano (fuera del repositorio), corregido con este plan |
