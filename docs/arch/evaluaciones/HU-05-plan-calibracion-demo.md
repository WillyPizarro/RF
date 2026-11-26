# Plan ARCH + TESTER — Umbrales faciales de la demo: no calibrados, con verificación de sanidad (HU-05)

- **Fecha:** 2026-11-26. Reemplaza la versión del 2026-11-25 (calibración de demo con 5 personas), que está en el historial de git.
- **Pedido por:** LEAD, a pedido del PM. Las decisiones salen de CONTRATO-HU-05 v1.5 (`ffa1af0`, punto 9 de las respuestas), aprobadas por el humano el 2026-11-26.
- **Por qué cambió:** solo hay **2 integrantes del equipo** cerca para fotografiar. Con 2 personas no se puede calibrar: hay una sola pareja de identidades para los impostores reales y los genuinos son de 2 personas (respuesta conjunta del TESTER y el ARCH, 25-nov).
- **Tipo:** plan, sin código. **No cambia el ADR-0004.** La calibración del ADR-0004 §3 (unas 20 personas) y la recalibración de producción (TECH-DESIGN, brecha 6) siguen pendientes.

## 1. Lo que decidió el humano (v1.5, punto 9)

| Tema | Decisión |
|---|---|
| Umbral alto | **0,363, NO CALIBRADO**: la referencia que publica OpenCV para SFace |
| Umbral bajo | Lo propone el ARCH con una justificación desde lo publicado para SFace, declarado **arbitrario**. Se revisa con la sanidad y vuelve al humano (sección 3) |
| Sanidad, no calibración | Solo hechos: scores genuinos, A contra B, contra SFHQ y cuántas búsquedas darían un candidato falso. **Ni FMR ni FNMR.** Nunca se presenta como calibración |
| Galería de la demo | Al menos 5 personas: las 2 con consentimiento y caras sintéticas de SFHQ. La cantidad la proponen el TESTER y el ARCH (sección 4) |
| Voluntarios que no son del equipo | Quedan como **mejora**. La precisión del ADR-0008 §2 que hace falta para ellos **no se redacta** hasta que el humano la pida |

**Consecuencia para TECH-DESIGN:** el criterio "Umbrales" (FMR ≤ 0,1 % y FNMR ≤ 5 % en el set de calibración) queda **sin cumplir** en la demo. Los umbrales de la demo son de referencia y arbitrarios, no medidos.

## 2. Lo que está publicado para SFace (consultado el 2026-11-26)

| Fuente | Qué dice |
|---|---|
| `opencv_zoo`, `models/face_recognition_sface/sface.py` (Apache 2.0) | `self._threshold_cosine = 0.363` y `self._threshold_norml2 = 1.128`. Mismo rostro si `cosine_score >= 0.363` o si `norml2_distance <= 1.128`. **No** dice de qué datos salen ni a qué tasa de falsos aceptados corresponden |
| `opencv_zoo`, README de `face_recognition_sface` | Exactitud de 0,9940 (SFace), 0,9942 (*block*) y 0,9932 (*quant*) con su herramienta de evaluación. **No nombra el conjunto de datos** ni da umbrales. Modelo `face_recognition_sface_2021dec.onnx`, Apache 2.0 |
| Tutorial de OpenCV, `tutorial_dnn_face` | **No se pudo leer** (403). Lo que diga queda NO VERIFICADO |
| Artículo de SFace (Zhong et al., IEEE TIP 2021, enlazado desde el README) | No se consultó |

**Lo que se deduce:** los dos umbrales publicados son **el mismo punto de operación**. Con vectores normalizados, la distancia L2 y el coseno cumplen d² = 2 − 2·cos. Entonces d = 1,128 equivale a cos = 1 − 1,128²/2 ≈ 0,364. **No hay un segundo punto publicado** que sirva de umbral bajo, ni una tasa de error asociada al primero. Cualquier umbral bajo es **arbitrario**, y por eso se declara así.

## 3. Umbral bajo propuesto (ARCH)

**Propuesta: `MOTOR_UMBRAL_BAJO` = 0,28, arbitrario.** Equivale a una distancia L2 de 1,20 entre vectores normalizados. La banda "No concluyente" queda entre 0,28 y 0,363.

**Por qué ese valor:**

1. **Qué error se evita.** Con un umbral alto sin calibrar, el error más caro es mostrar "Sin coincidencia en la lista consultada" a una persona que **sí** está en la lista pero con una captura difícil (luz, ángulo, lentes). Es un resultado negativo falso, el que más se acerca a lo que prohíbe la regla 7. Por eso conviene una banda **ancha**, que mande los casos dudosos a "No concluyente — verifique por otros medios".
2. **Qué error se tolera.** Una banda demasiado ancha haría que muchas búsquedas de personas que no están en la lista terminen en "No concluyente". Eso es molesto para el agente, pero no es un falso negativo.
3. **El número:** 0,08 debajo del umbral publicado (más o menos un 22 % de 0,363). Es un margen **elegido**, no derivado de ningún dato. Lo que lo confirma o lo corrige es la sanidad.

**Cómo se revisa con la sanidad** (2 personas, 2 días, de 10 a 12 fotos por día) **antes de volver al humano:**

| Si en la sanidad… | Entonces |
|---|---|
| Algún genuino (foto de prueba contra la galería de la misma persona) da **menos de 0,28** | Esa persona habría visto "Sin coincidencia". Se propone **bajar** el umbral bajo por debajo del genuino mínimo observado y se reporta cuántas fotos fueron |
| Algún genuino da entre 0,28 y 0,363 | Habría visto "No concluyente". Se reporta cuántas fotos fueron. No cambia nada, porque es el comportamiento buscado |
| Muchas búsquedas sin la persona correcta en la galería (sección 4, galerías sin A o sin B) o muchas comparaciones contra SFHQ caen **en la banda** | Habría demasiados "No concluyente". Se reporta la proporción y se considera **subir** el umbral bajo |
| Alguna comparación de una persona contra otra (A contra B, o contra SFHQ) da **0,363 o más** | Sería un candidato falso. Se reporta. El umbral alto no se toca, porque lo fijó el humano: vuelve al humano con el dato |

## 4. Galería de la demo (acordada por el TESTER y el ARCH, 26-nov)

- **20 personas: las 2 reales y 18 de SFHQ.** Es el tamaño que asume el ADR-0004 ("unas 20 personas") y su advertencia de N × FMR.
- **Aparte**, otras 60 o más caras de SFHQ que **no** entran a la galería se usan solo en la sanidad, como impostores por comparación. Se reportan como "contra sintéticos" y nunca como FMR, porque los sintéticos sesgan a la baja.
- **Fuera de línea, para la sanidad:** se corre también con una galería **sin B**, para probar a B como persona que no está en la lista, y otra **sin A**. Es el único caso con caras reales de "alguien que no está en la lista da un candidato". La galería de la demo lleva a las dos.
- **Licencia de SFHQ: NO VERIFICADA todavía.** El humano la anota desde la página de Kaggle **antes** de bajarla, y solo se acepta **CC0, MIT o dominio público** (regla del LEAD). El ADR-0008 descartó en su momento los rostros generados por las licencias no comerciales de muchos generadores. Ninguna imagen va al repositorio.

## 5. Fotos y toma (se mantiene de la versión del 25-nov)

- **Por persona:** de 10 a 12 fotos por día en **2 días**, más **1 foto de galería** tipo ficha, que no entra en la sanidad. Ya no hay un set de calibración y otro de evaluación: los dos días son de **sanidad**, y se reportan por separado y juntos.
- **Piloto** de 2 o 3 fotos: un set aparte para comprobar el recorte de la opción (b). No cuenta para la sanidad.
- **Variación, encuadre, ajustes del S23, recortes en la PC (opción b, con la a de respaldo) y custodia:** igual que en la versión del 25-nov. Es decir: cámara trasera en 1x; rostro entre un cuarto y un tercio del ancho de la foto; JPEG; sin optimizador, HDR, fotos en movimiento ni ubicación; en la PC, rotar por EXIF, borrar el EXIF, reducir a la resolución de la app y recortar; las fotos salen solo por USB a `PRUEBAS_ROSTROS_DIR`, fuera del repositorio, y se borran con acta.
- **Sin consentimiento firmado no se toma ninguna foto**, ni siquiera las del piloto (ADR-0008 §2).

## 6. Qué se reporta (informe de sanidad del TESTER)

- Por persona y por día: el mínimo, el máximo y la mediana de los genuinos contra su galería, y cuántas fotos quedan debajo de 0,28, entre 0,28 y 0,363, y por encima.
- A contra B: el score máximo.
- Contra SFHQ (las de fuera de la galería): el máximo, la mediana y cuántas comparaciones caen en la banda o por encima.
- Búsquedas contra la galería de la demo (1:N): cuántas darían un candidato que no es la persona, con la galería completa y con las galerías sin A y sin B.
- **Encabezado obligatorio:** "Umbrales de demo NO CALIBRADOS: el alto es la referencia de OpenCV y el bajo es arbitrario. Sanidad con 2 personas: no es una tasa de error ni vale fuera de esta demo."

## 7. Quién hace qué

| Rol | Tarea |
|---|---|
| Humano | Los consentimientos, la toma de las fotos, la custodia de la lista de códigos y la aprobación final del umbral bajo |
| DEV | La resolución de la app, la extracción por USB, el script del recorte de la (b) y los umbrales en `MOTOR_UMBRAL_ALTO`, `MOTOR_UMBRAL_BAJO` y `MOTOR_UMBRAL_VERSION`, marcados como de demo |
| TESTER | La galería con SFHQ, los scores y el informe de sanidad de la sección 6 |
| ARCH | Revisar el informe contra la sección 3, proponer el ajuste del umbral bajo y llevarlo al humano |
| PM | El instructivo de fotos, ajustado a 2 personas y 2 días |
