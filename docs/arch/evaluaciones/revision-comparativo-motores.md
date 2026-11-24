# Revisión técnica del comparativo de motores (PM, 24-nov)

**Rol / fecha:** ARCH, 2026-11-24. Encargo del PM del 2026-11-24 (punto 3).
**Qué se revisó:** el comparativo publicado (https://claude.ai/artifact/P13csYEFam4gmLg7VRHuzo), leído entero, y el Claude Doc del 23-nov "Preparación de reunión: stack, biometría y datos" (https://claude.ai/artifact/SU7nLy2CSD9taHMxXUmovw), leído entero. Las referencias son los ADR-0002, 0004, 0008, 0009 y los propuestos 0017 y 0019.
**Lo que no se hizo:** no se republicó el comparativo ni se editó el Doc. Los precios marcados "terceros" no se volvieron a consultar: siguen por confirmar.

## 1. Errores técnicos del comparativo (hay que corregirlos)

| # | Dónde | Dice | Problema | Cambiar por |
|---|---|---|---|---|
| 1 | Resumen, tarjeta "Los datos no salen" | "El rostro se compara en nuestro servidor" (y se da a entender que no sale del Perú) | **Contradice el ADR-0009 y el ADR-0008.** La captura de un candidato se guarda cifrada hasta 24 h en `captura_pendiente`, en el Postgres de Supabase en la nube (región de referencia: São Paulo). Además, el país del VPS todavía no está definido. Lo cierto es que **ningún tercero procesa ni compara el rostro**, no que el dato se quede en el Perú | "El rostro lo compara nuestro servidor; ningún tercero lo procesa. En el MVP, la captura de una posible coincidencia se guarda cifrada hasta 24 h en una base en la nube fuera del Perú (brecha 8); en producción, todo puede ir a servidores del MININTER." |
| 2 | Resumen, tarjeta "Cero en licencias" | "El único costo es el servidor del demo, de unos US$ 6 a 12 al mes" | El ADR-0009 también prevé quizá un mes de Supabase Pro (para que no se pause en la semana de validación) y un dominio | "…el servidor del demo (unos US$ 6 a 12 al mes), el dominio y, quizá, un mes del plan pago de la base de datos." |
| 3 | Resumen, tarjeta "Motor reemplazable", y respuesta "¿Por qué no usan un motor comercial…?" | "se puede cambiar por uno comercial o por el de RENIEC tocando solo el servidor, sin cambiar la app" | **RENIEC no es un cambio de motor:** es 1:1 contra el DNI declarado. La app tendría que pedir el número de DNI y el flujo cambia (PA #7; el Doc del 23-nov lo dice bien en "RENIEC u otro servicio del Estado") | "Se puede cambiar por un motor comercial o propio tocando solo el servidor. RENIEC es otro caso: compara contra el DNI declarado (1:1), cambia el flujo y depende del PA #7." |
| 4 | Fila de Azure AI Face, "Por 10 000" | "≈ US$ 10 a 20" | Una búsqueda contra una lista son **dos transacciones** (detectar e identificar), como dice la misma fila. A US$ 1 por 1.000, son unos **US$ 20**, más el almacenamiento de los rostros de la lista (centavos) | "≈ US$ 20" con la nota "2 transacciones por búsqueda" |
| 5 | Fila de Amazon Rekognition, "Por 10 000" | "≈ US$ 10" | Para buscar contra una lista se usa una colección: hay que **indexar** la galería una vez y pagar el **almacenamiento** de los rostros por mes. Con 20 personas son centavos, pero hay que decirlo (el Doc del 23-nov dice "≈ US$ 10 a 20 con indexado") | "≈ US$ 10 más el indexado de la lista y su almacenamiento (centavos con 20 personas)". Unificar la cifra con el Doc |
| 6 | Fila de Plate Recognizer, "Para tener en cuenta" | "En la nube, la foto de la placa sale del celular, lo que contradice HU-04" | Da a entender que **instalado en un servidor** sí cumple. No: instalado en nuestro servidor, la foto también sale del celular, y eso contradice el ADR-0002 ("la foto de la placa nunca sale del dispositivo") igual. Además, es un producto de lectura automática de placas (ALPR), y la regla 6 la excluye | "En la nube o instalado en un servidor, la foto de la placa sale del celular (contradice el ADR-0002 y HU-04). Es un producto de lectura automática de placas, que el MVP excluye (regla 6)." |
| 7 | Fila de Plate Recognizer, "Cómo se paga" | "Mismo precio en la nube o instalado" | **NO VERIFICADO** por el ARCH. El SDK instalado suele licenciarse por equipo o cámara, aparte de la API en la nube | Marcarlo "por confirmar" o quitarlo |
| 8 | Fila de VeriLook, "Precisión", y fila de Innovatrics y otros | "Comercial, evaluado por el NIST" / "Los más precisos del mercado según el NIST" | Los puestos en el NIST los publica cada fabricante; no se verificaron en los resultados oficiales (el Doc del 23-nov ya lo advierte) | "Según el fabricante, entre los primeros en NIST FRTE (no verificado en los resultados oficiales)." |
| 9 | Fila de OpenCV, "Precisión" | "No evaluado por el NIST" | **NO VERIFICADO**: no se revisó la lista de participantes de FRTE. Es probable, pero no está comprobado | "No aparece entre los evaluados por el NIST (a confirmar)." |
| 10 | Pie de página | "a partir del ADR-0002 y el ADR-0004" | Con el paso a Flutter (ADR-0017, propuesto), ML Kit **se mantiene** igual. Conviene decirlo para que no parezca que el comparativo quedó viejo | "…a partir de los ADR-0002 y 0004. Con la app en Flutter (ADR-0017, propuesto), ML Kit se mantiene igual." |

## 2. Lo que falta en el comparativo y está en el Doc del 23-nov

- **InsightFace.** Lo van a preguntar porque es técnicamente mejor que SFace. Sugerencia de fila: "Código MIT, pero los modelos entrenados (buffalo_l, antelopev2) son solo para investigación no comercial; para un servicio contratado hay que licenciarlos. No publica precios." Es la misma frase del Doc.
- **Lo que cuesta más que la licencia.** El Doc lo dice y el comparativo no: la integración, la **recalibración y la evaluación con fotos autorizadas y representativas**, la prueba de vida y el mantenimiento anual (del 15 al 20 % de la licencia). Con el **PA #40** esto pesa más: cualquier motor, incluido el actual, hay que recalibrarlo con fotos de referencia reales antes de producción. Sugerencia de nota bajo la tabla de rostro: "Cambiar de motor no ahorra la calibración: los umbrales se vuelven a fijar con fotos de referencia representativas (PA #40)."
- **Rango de licencias empresariales** (ARSA como referencia: US$ 34.000 perpetua para varios servidores, más un 18 % anual). Es opcional, pero ayuda a dimensionar "por cotizar".

## 3. Diferencias entre los dos documentos (conciliar)

| Tema | Comparativo (24-nov) | Doc (23-nov) | Qué hacer |
|---|---|---|---|
| Vigencia de los precios de VeriLook | "vigentes desde el 18-feb-2026" | "vigentes desde el 3-mar-2026" | Confirmar en la página de Neurotechnology y usar una sola fecha |
| Rekognition por 10.000 | ≈ US$ 10 | ≈ US$ 10 a 20, con indexado | Ver el error 5 |
| Precio de VeriLook | € 339 a 859 (SDK) | Lo mismo, más Face Verification a € 1.390 con 1.000 transacciones | Opcional: sumar el dato al comparativo |

**El Doc del 23-nov quedó viejo con el PA #37 y la opción E** (no es parte del encargo, pero el PM lo va a usar en la reunión):

- "Stack tecnológico: App Android con Expo (TypeScript)… con Caddy": pasa a ser **Flutter, NGINX y Keycloak al final** (ADR-0017, 0018 y 0020, propuestos), con la API en Python a negociar (ADR-0019).
- Tabla "Librerías de visión": `@react-native-ml-kit/text-recognition` y `react-native-vision-camera` pasan a `google_mlkit_text_recognition` y `camera`. ML Kit sigue igual.
- "¿Lo podemos operar nosotros?… Python y TypeScript": pasa a **Python y Dart**, con el argumento de que lo que queda en Python es interno y tiene contrato (ADR-0019).
- "¿Por qué la base de datos está fuera del Perú?… el login de Supabase Auth sí se rehace": con el ADR-0020, el cambio a Keycloak está **acotado a la API**: ni la app ni el contrato cambian.
- "¿Dependen de servicios gratuitos?… La cuota gratuita de EAS": con Flutter, EAS desaparece.
- Tabla del PA #2: falta la **opción E**. Su costo frente a la A está en la [estimación del PA #2](PA-02-estimado-opciones.md).
- Respuesta "Motor reemplazable": si se acepta el ADR-0019, el motor pasa a ser un **servicio aparte**, y reemplazarlo es cambiar ese servicio.

## 4. Lo que está bien y no hay que tocar

- RENIEC: S/ 0,70 por consulta (S/ 7.000 por 10.000) y "solo 1:1".
- Cloud Vision: US$ 1,50 por 1.000 con 1.000 gratis al mes da US$ 13,50 por 10.000.
- Las licencias de YuNet (MIT) y SFace (Apache 2.0), y el 99,40 % en LFW según opencv_zoo, con la nota de que LFW es fácil.
- La acotación de Azure (acceso limitado y aprobación de Microsoft) y que ML Kit no cobra.
- La respuesta sobre la Ley 29733 y el flujo transfronterizo, que remite al área legal.
- La respuesta sobre la prueba de vida: el MVP no la tiene y figura como brecha.
