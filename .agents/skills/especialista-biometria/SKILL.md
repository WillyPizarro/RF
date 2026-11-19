---
name: especialista-biometria
description: Guía de especialista en verificación biométrica facial para prototipos con revisión humana - pipeline de captura con control de calidad, detección y comparación con OpenCV (YuNet + SFace), elección y documentación de umbrales, estados de resultado (candidato / no concluyente / sin coincidencia), pantalla de revisión humana y evaluación biométrica documentada (FMR, FNMR, falla de captura, subgrupos). Use when the DEV implements face capture, face matching or the human-review flow, when the TESTER or ARCH plans or writes the biometric quality evaluation, or when anyone asks about thresholds, false positives, face quality, synthetic face data or face-model licensing.
type: skill
tags: [biometria, reconocimiento-facial, opencv, evaluacion, revision-humana]
---

# Especialista en biometría facial

## Goal

Que la verificación facial del prototipo sea **defendible**: que nunca presente una coincidencia
como identificación, que rechace capturas malas antes de comparar, y que su desempeño quede
medido y documentado con sus límites. Esta skill no es un rol: la cargan el DEV, el TESTER o el
ARCH cuando su trabajo toca biometría.

## Principios que no se negocian

1. **El sistema propone, una persona decide.** El resultado máximo es "candidato"; la palabra
   "identificado" no aparece en la UI, en la API ni en la bitácora.
2. **Sin búsqueda masiva.** Solo 1:1 (¿es quien dice ser?) o contra una lista acotada y
   autorizada, siempre partiendo de un caso concreto con motivo registrado. Nunca contra toda la
   base ni sobre video continuo.
3. **Mala captura = no se compara.** Una captura que no pasa control de calidad se rechaza con un
   motivo y se pide repetir; no se envía al comparador "a ver qué sale".
4. **Ante la duda, no concluyente.** Entre el umbral de rechazo y el de candidato existe una banda
   explícita de "no concluyente". Se prefiere un falso rechazo a un falso positivo.
5. **Todo umbral se documenta** con el valor, de dónde salió y con qué datos se midió.

## Pipeline de referencia

```
Captura (móvil) → Control de calidad (móvil) → Envío cifrado (HTTPS) →
Detección + alineación (YuNet) → Embedding (SFace) → Comparación (coseno) →
Banda de decisión → Revisión humana → Bitácora → Borrado de la captura
```

### 1. Captura y control de calidad (móvil)

- Detección en el dispositivo con **ML Kit Face Detection** (modo clasificación activado).
- Rechazar con motivo explícito si:
  - no hay rostro, o hay más de uno;
  - ángulo de cabeza fuera de rango (yaw/pitch/roll; definir límite y documentarlo);
  - ojos cerrados (probabilidad de ojo abierto bajo el límite definido);
  - rostro muy pequeño en la imagen (tamaño mínimo definido en píxeles);
  - imagen borrosa (p. ej. varianza del Laplaciano bajo un límite, medido en el backend si el
    móvil no lo calcula) o sobre/subexpuesta.
- Los límites se fijan midiendo con capturas reales del equipo, no se copian de internet.
  Referencia conceptual: ISO/IEC 29794-5 (calidad de imagen facial).
- Mostrar guía visual (óvalo, "acérquese", "mire de frente") en vez de errores técnicos.

### 2. Detección, alineación y comparación (backend, Python + OpenCV)

- Detector: **YuNet** (`cv2.FaceDetectorYN`, modelo `face_detection_yunet_*.onnx` del
  repositorio opencv_zoo).
- Reconocedor: **SFace** (`cv2.FaceRecognizerSF`, modelo `face_recognition_sface_*.onnx`).
  Flujo: `alignCrop` → `feature` → `match` con `FR_COSINE`.
- Punto de partida de umbral: la muestra oficial de OpenCV usa **coseno ≥ 0.363** como "misma
  identidad" (y L2 ≤ 1.128). Es solo un punto de partida: el umbral del prototipo se recalibra
  con los datos propios y se fija más estricto para reducir falsos positivos.
- **Licencias:** antes de usar, verificar el archivo LICENSE de cada modelo en opencv_zoo
  (a la fecha de redacción YuNet es MIT y SFace Apache 2.0). **No usar** modelos preentrenados de
  InsightFace u otros marcados "non-commercial / research only" en un servicio contratado.
- Fijar versiones exactas de OpenCV y de los archivos `.onnx` (con hash) para que la evaluación
  sea reproducible.

### 3. Bandas de decisión

| Banda | Condición | Qué muestra la app |
|---|---|---|
| Candidato | score ≥ umbral alto | "Posible coincidencia — requiere revisión" + foto de referencia |
| No concluyente | umbral bajo ≤ score < umbral alto | "No concluyente — verifique por otros medios" |
| Sin coincidencia | score < umbral bajo | "Sin coincidencia en la lista consultada" (no "persona sin requisitoria") |
| Captura rechazada | no pasó calidad | Motivo y opción de repetir |

- En lista acotada: devolver como máximo los **3 mejores** candidatos sobre el umbral alto,
  nunca un ranking completo.
- No mostrar el score crudo al agente en campo; sí guardarlo en la bitácora para auditoría.

### 4. Revisión humana

- Pantalla lado a lado: captura vs. referencia, datos mínimos del caso, banda de resultado.
- El revisor elige **Confirmar / Descartar / No concluyente** y escribe un motivo obligatorio.
- Nada se dispara automáticamente (alertas, acciones) antes de la decisión del revisor.
- Bitácora: usuario, revisor, fecha-hora, motivo de consulta, banda, score, decisión, motivo de
  decisión, versión del modelo y del umbral.

### 5. Datos y privacidad en el prototipo

- La captura se borra tras la comparación o tras la revisión humana. Si no hay candidato, vive
  solo en memoria. Si hay candidato, se guarda cifrada hasta la decisión del revisor o un plazo
  máximo (24 h en este proyecto, ADR-0008), y cada borrado queda en la bitácora. Nunca se guarda
  en el dispositivo.
- Galería de referencia: **rostros sintéticos o fotos del equipo con consentimiento firmado**,
  con variedad de edad, tono de piel, iluminación y accesorios (lentes, gorra, mascarilla).
- Guardar embeddings de la galería, no reprocesar fotos en cada consulta.
- Marcar todo como data de prueba (campo `es_sintetico = true`).

## Evaluación biométrica documentada

Producirla como documento entregable (lo exige el encargo). Estructura:

1. **Alcance y límites** — prototipo, data sintética/consentida, N personas, N imágenes; no
   extrapolable a producción.
2. **Configuración** — versiones de OpenCV y modelos (con hash), umbrales, reglas de calidad.
3. **Protocolo** (inspirado en ISO/IEC 19795-1):
   - pares genuinos (misma persona) e impostores (personas distintas), separados del set usado
     para fijar el umbral;
   - capturas en condiciones de campo: día/noche, ángulo, distancia, accesorios.
4. **Métricas**:
   - **FMR** (falsa coincidencia) y **FNMR** (falsa no coincidencia) en el umbral elegido;
   - **FTA** (falla de captura/adquisición): % de capturas rechazadas por calidad;
   - % de resultados en banda "no concluyente";
   - curva DET o tabla FMR/FNMR para varios umbrales, justificando el elegido;
   - **resultados por subgrupo** (sexo, rango de edad, tono de piel, accesorios) para detectar sesgo;
   - tiempo de respuesta de la comparación (p50, p95).
5. **Honestidad estadística** — con pocos datos, declarar el intervalo: si hubo 0 falsas
   coincidencias en N comparaciones impostoras, el límite superior al 95 % es ≈ 3/N
   ("regla de 3"). Nunca reportar "0 % de falsos positivos".
6. **Conclusión y brechas para producción** — qué faltaría (datos reales autorizados, prueba de
   vida/anti-suplantación, evaluación independiente, etc.).

## Checklist antes de entregar

- [ ] Ningún texto de UI, API o bitácora dice "identificado"
- [ ] Capturas de mala calidad se rechazan antes de comparar, con motivo visible
- [ ] Existen las tres bandas (candidato / no concluyente / sin coincidencia) con umbrales documentados
- [ ] La revisión humana es obligatoria y queda en bitácora con motivo
- [ ] La captura se borra tras la comparación (o tras la revisión, con plazo máximo) y el borrado queda en bitácora
- [ ] Licencias de modelos verificadas y anotadas en el documento técnico
- [ ] Versiones de librerías y modelos fijadas con hash
- [ ] Evaluación con FMR, FNMR, FTA, subgrupos e intervalo honesto
- [ ] Límites del prototipo declarados (no apto para producción sin evaluación con datos reales)
