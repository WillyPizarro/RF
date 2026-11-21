# ADR 0002: App móvil con Expo (dev build) y ML Kit en el dispositivo

## Estado

Aceptado (2026-11-18)

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
