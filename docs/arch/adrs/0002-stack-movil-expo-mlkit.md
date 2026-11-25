# ADR 0002: App móvil con Expo (dev build) y ML Kit en el dispositivo

## Estado

**Reemplazado por el [ADR-0017](0017-app-movil-flutter-mlkit.md) (2026-11-24):** la app pasa a Flutter (PA #37, decisión del humano). Aceptado el 2026-11-18. Siguen vigentes, a través del ADR-0017, el OCR y la calidad facial con ML Kit en el dispositivo, la decisión sobre la telemetría (PA #31) y el riesgo del OCR de placas.

## Contexto

- HU-04: el OCR de la placa se hace en el dispositivo y la foto de la placa no se guarda.
- HU-05 E2: el control de calidad facial (rostro presente, de frente, con luz suficiente, un solo rostro) ocurre antes de enviar la captura.
- Enfoque MVP del PRD: "HTTPS y no guardar fotos en el celular".
- La cámara con procesamiento en el dispositivo requiere módulos nativos. No funciona en Expo Go ni en la vista previa de bolt.new (análisis de factibilidad, sección "¿Sirve bolt.new?").
- PA #12: todavía no se sabe qué dispositivos usará el personal, por lo que la app debe poder funcionar en Android y en iOS.
- El backend es Python (ADR-0001). El equipo es pequeño y el plazo, de 30 a 40 días.

## Decisión

La app se construye con **React Native + Expo en modo dev build** (con EAS Build) y TypeScript. Para la cámara y el procesamiento en el dispositivo:

- **Cámara:** una librería de cámara compatible con dev build (referencia: `react-native-vision-camera`).
- **OCR de placa:** Google ML Kit Text Recognition, en el dispositivo.
- **Calidad facial:** Google ML Kit Face Detection, en el dispositivo. Mide el número de rostros, el ángulo, si los ojos están abiertos y el tamaño del rostro en el cuadro.
  - *Precisión propuesta en el [ADR-0015](0015-foto-varias-personas-rostro-elegido.md) (C6, aceptado el 2026-11-20, opción A):* en una foto con varias personas, ML Kit marca todos los rostros, el usuario elige uno y la app envía solo el recorte de ese rostro. "Más de un rostro" deja de ser un motivo de rechazo en el dispositivo; con más de 5 rostros, la captura se rechaza.
- **Token de sesión:** almacenamiento seguro del sistema (`expo-secure-store`). Nada de imágenes en disco.

El LEAD confirma en el Sprint 0 qué paquetes exactos usar (los wrappers de ML Kit) y su compatibilidad con la versión del SDK de Expo.

## Alternativas consideradas

- **Flutter con ML Kit.** La integración con ML Kit es madura. Se descartó porque agrega Dart como segundo lenguaje junto al Python del backend y no permite aprovechar el código del prototipo navegable si UX lo genera en Expo.
- **PWA web.** No requiere builds ni tiendas. Se descartó porque el OCR y el control de calidad en el navegador son más lentos y menos precisos; resolverlo en el servidor obligaría a enviar la foto de la placa, lo que contradice HU-04; y la cámara web en iOS es limitada.

## Consecuencias

- Una sola base de código TypeScript para Android e iOS, y las pantallas del navegable se pueden reutilizar.
- El OCR y la calidad facial funcionan sin red y sin costo por uso; la foto de la placa nunca sale del dispositivo.
- **Costo:** los módulos nativos atan la app a la versión del SDK de Expo. Actualizar el SDK durante el proyecto puede romper la cámara, así que se fija una versión en el Sprint 0 y no se cambia hasta el cierre.
- **Costo:** se usa un build propio en lugar de Expo Go. Cada cambio nativo exige un build nuevo (cuota gratuita de EAS limitada). Para iOS hace falta una cuenta Apple Developer de pago, que se pide solo si PA #12 confirma iOS.
- **Riesgo:** ML Kit no reconoce específicamente placas peruanas: lee texto. El formato de placa se valida en la app y el usuario siempre confirma o corrige el texto (HU-04 E1).
- **Costo (agregado el 2026-11-20, opción A del humano):** ML Kit envía a Google **métricas técnicas de uso y rendimiento** y un **identificador por instalación**. No envía la imagen ni el texto leído. Los datos van a servidores de Google, fuera del Perú. **No hay una opción oficial para desactivarlo.** En el teléfono queda una cola local (`databases/com.google.android.datatransport.events`). Los términos de ML Kit obligan a **informar al usuario**: lo hace el aviso de OCR-01 (HU-04 v5, Escenario 4). Fuentes: [términos de ML Kit](https://developers.google.com/ml-kit/terms) y [divulgación de datos en Android](https://developers.google.com/ml-kit/android-data-disclosure), ambas con última modificación del 14-may-2025. El detalle y las alternativas están en la [evaluación](../evaluaciones/HU-04-telemetria-mlkit.md). En producción queda como brecha (TECH-DESIGN › Brechas, n.º 10). Bloquear el transporte o cambiar el motor de OCR (opciones B y C) exigiría un ADR nuevo.
- **Face Detection (HU-05):** usa el mismo transporte, así que **vale la misma decisión**. Según los términos de ML Kit, que cubren todas sus APIs, el procesamiento de la entrada ocurre por completo en el dispositivo, y ML Kit no envía ni la imagen ni sus resultados: *"processing of the input data (e.g. images, video, text) fully happens on-device"* y *"ML Kit does not send that data and the resultant outputs to Google servers"*. Los contornos y los *landmarks* son resultados, así que tampoco salen. Las páginas de divulgación de Android e iOS **no** ponen a Face Detection entre las funciones que envían datos adicionales. Límites de esta confirmación: es la palabra del proveedor, no está verificada con tráfico de red, y la guía de Face Detection no lo dice de forma específica para rostros. **Recomendación ARCH (pendiente de decisión en el contrato de HU-05):** usar la variante **empaquetada** `com.google.mlkit:face-detection`, porque con ella solo sale el identificador por instalación y no el identificador del dispositivo que agrega la variante de Google Play services. Su costo es de unos 6,9 MB más en el APK.
