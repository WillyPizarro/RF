# Pendientes para contratos de HU

- **HU-01:** incluir la prueba de 422 `SOLICITUD_INVALIDA` con formato de error estándar (SPRINT0 M-2).
- **HU-05:** la búsqueda automatizada de la palabra prohibida se limita a `apps/`, `services/` y `contratos/`; los documentos la citan para prohibirla.
- **HU-05:** repetir la verificación de la API de OpenCV 5.1 (YuNet + SFace, `cv.FaceRecognizerSF_FR_COSINE`) dentro de la imagen Linux del contenedor `api`, con los `.onnx` y hashes fijados en TECH-DESIGN.md › Modelos biométricos fijados.
- **HU-03 (desde HU-08, decisión 1):** con `POST /v1/consultas/placa`, probar la mitad de la API de HU-08: modo `latencia` o `error_500` de la fuente `placas` → `FUENTE_NO_DISPONIBLE` (máx. 1 reintento); modo `malformada` → `FUENTE_RESPUESTA_INVALIDA`; nunca `sin_requisitoria`. Escenario 2: con `FUENTE_PLACAS_URL` apuntando a un mock generado desde `contratos/fuentes/placas.yaml`, las pruebas funcionales pasan sin cambiar la app.
- **HU-03 (desde HU-08, decisión 3):** decidir cómo ve el agente una placa `PLACA_NO_REGISTRADA` (404 del simulador); no puede mostrarse como "sin requisitoria".
- **HU-07 (desde HU-08, decisión 1):** cada `FUENTE_NO_DISPONIBLE` y `FUENTE_RESPUESTA_INVALIDA` deja un evento `ERROR_FUENTE` con su `codigo_error` en la bitácora.
