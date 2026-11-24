# ADR 0019: API y simuladores en Python, y el motor biométrico como servicio interno aislado y reemplazable

## Estado

**Aceptado (2026-11-24),** con el motor separado desde ahora. Propuesto por el ARCH a pedido del PM (PRD PA #37) y aceptado por el humano el mismo día. Es la posición técnica que el humano lleva a la **negociación con el MININTER**: lo de Python sigue siendo supuesto de trabajo hasta que responda el MININTER. **Precisa el punto 2 del [ADR-0004](0004-verificacion-facial.md)** (el motor pasa de módulo dentro de la API a servicio propio) y agrega el servicio `motor` al [ADR-0009](0009-despliegue.md). El resto del ADR-0004 (lista acotada, bandas, umbrales y modelos fijados) no cambia.

## Contexto

- **PA #37:** el estándar del MININTER para el backend es **Java 21**. El humano negocia que la API, los simuladores y el motor biométrico sigan en Python (FastAPI, OpenCV con YuNet y SFace), con el motor como servicio interno aislado y reemplazable (por ejemplo, por RENIEC o por un motor propio).
- **Lo que existe hoy (rama `main`):** unas 2.570 líneas de Python propias en `services/api/` y `services/simuladores/`, más migraciones Alembic. Cuatro HU aceptadas usan la API: HU-01, HU-02, HU-03, HU-07, más HU-08 (simuladores). Hay unas 4.700 líneas de pruebas del TESTER. Fuente: `wc -l`, 2026-11-24.
- **Las pruebas de la API son de caja negra:** "hablan con el sistema solo por su interfaz observable: HTTP a través del proxy … No importan código de la API" (`services/api/tests/conftest.py`, líneas 1 a 4). Valen igual para una API escrita en otro lenguaje que cumpla el mismo contrato.
- El contrato app ↔ API es OpenAPI (ADR-0007) y las fuentes tienen sus contratos en `contratos/fuentes/` (ADR-0006). La app no sabe en qué lenguaje está la API.
- ADR-0004, punto 2: el motor ya está detrás de la interfaz `MotorBiometrico` (`comparar(captura) -> ResultadoComparacion`). La alternativa "motor como servicio separado" se descartó el 2026-11-18 por ser una pieza más que desplegar y un salto de red más. **HU-05 todavía no se construyó**: separar el motor hoy no rehace código.
- OpenCV también tiene una interfaz para Java (`FaceDetectorYN` y `FaceRecognizerSF` existen en sus *bindings*). Que el motor esté en Python no es una imposición técnica, sino el ecosistema donde están probados los modelos, la calibración y la evaluación biométrica (numpy, métricas FMR y FNMR).

## Decisión

1. **La API y los simuladores siguen en Python (FastAPI) hasta el cierre del MVP.** No se reescriben en Java dentro del MVP.
2. **El motor biométrico pasa a ser un servicio interno propio, `motor`,** en su propio contenedor (Python, OpenCV 5.1 y los `.onnx` fijados en el ADR-0004):
   - Solo está en la red interna, sin puerto público, y lo llama **solo la API** (igual que los simuladores, ADR-0006).
   - Tiene su propio contrato OpenAPI en `contratos/motor/` con dos operaciones: evaluar la calidad y comparar un recorte contra la galería. Devuelve las bandas del ADR-0004, nunca "identificado" (regla 1).
   - **No guarda nada**: recibe la imagen, responde y la descarta. La retención de la captura de un candidato sigue en la API y en `captura_pendiente` (ADR-0008).
   - Los embeddings de la galería los calcula el motor al arrancar, a partir del simulador, y los mantiene en memoria.
   - Si el motor no responde o falla, la API devuelve un error controlado. **Nunca "Sin coincidencia"** (regla 7, ADR-0014).
3. **Reemplazar el motor = cambiar el servicio `motor`, no la API ni la app.** Un motor comercial (con su SDK en Java o C) o uno propio del MININTER se pone detrás del mismo contrato. RENIEC **no** es un reemplazo directo: es 1:1 contra el DNI y cambia el flujo (PA #7, ADR-0004).
4. **Lo que se entrega para negociar Java en producción:** los contratos OpenAPI (app ↔ API, API ↔ fuentes, API ↔ motor), el esquema y las migraciones de Postgres, y las pruebas de caja negra del TESTER. Con eso, el MININTER puede reescribir la API en Java 21 y comprobar que hace lo mismo corriendo las mismas pruebas.

## Argumentos para la negociación con el MININTER

1. **Es un prototipo con fecha de cierre.** El MVP valida flujos con datos sintéticos (PA #17) y el paso a producción está fuera de este servicio (PA #10). Reescribir en Java ahora no cambia nada de lo que el MININTER puede validar el 30-dic.
2. **El costo es real y desplaza alcance.** Reescribir la API en Java (Spring Boot) cuesta unos 8 a 10 días de DEV y 1 o 2 del LEAD y del TESTER. Sumado a la migración a Flutter (ADR-0017), no alcanza el cronograma sin sacar HU-05 y HU-06, que son el centro del encargo (ver la [evaluación](../evaluaciones/PA-37-39-stack-mininter.md)).
3. **La pieza en Python es justo la que el MININTER cambiaría.** El motor biométrico es un modelo académico sin certificar (SFace). Para producción se recomienda un motor evaluado por el NIST, en servidores del MININTER (PA #40, brecha 6). Ese motor vendrá con su propio SDK. Aislado detrás de un contrato, el lenguaje del motor del prototipo deja de importar.
4. **Los simuladores son desechables por diseño.** Se reemplazan por adaptadores a las fuentes reales (ADR-0006). Reescribirlos en Java es trabajo que se tira.
5. **La API ya está descrita de forma independiente del lenguaje.** Contrato OpenAPI, esquema SQL y pruebas de caja negra por HTTP: el MININTER recibe una especificación ejecutable para reescribirla en Java 21 cuando pase a producción, con una prueba objetiva de equivalencia.
6. **La parte del stack que ve el usuario sí cambia.** App en Flutter, NGINX y Keycloak (ADR-0017, ADR-0018 y ADR-0020): lo que se queda en Python es interno y no tiene puertos públicos.

**Lo que el humano debe admitir si lo preguntan (trade-offs reales):**

- El área técnica del MININTER tendría que operar y parchar un *runtime* más (Python) durante la validación.
- La revisión de seguridad de dependencias de Python (FastAPI, OpenCV, numpy) es trabajo para su equipo si no la hacen hoy.
- Si el MININTER exige Java en el MVP sin excepción, la salida de menor costo es **mantener solo el motor en Python** (la parte difícil, aislada por contrato) y reescribir la API en Java, aceptando que algo del alcance sale del MVP.

## Alternativas consideradas

- **A. Reescribir la API en Java 21 dentro del MVP y dejar el motor en Python.** Cumple el estándar en todo lo que no es biometría. Se descarta como propuesta por el costo (8 a 10 días de DEV) en un cronograma que ya absorbe Flutter. Es la salida si el MININTER no acepta.
- **B. Todo en Java, incluido el motor (OpenCV para Java).** Técnicamente posible. Se descarta: rehace la calibración y la evaluación biométrica en otro lenguaje y suma riesgo al módulo más delicado, sin ganar precisión.
- **C. Mantener el motor dentro de la API (ADR-0004 vigente).** Es más simple: un contenedor menos y sin salto de red. Se descarta como propuesta porque debilita el argumento 3: "reemplazable" sería un cambio en el código de la API, no un cambio de servicio. Es la opción si el humano prefiere ahorrar ese día y medio.

## Consecuencias

- La negociación tiene un argumento concreto: lo que se queda en Python es interno, tiene contrato y tiene pruebas que sirven para reescribirlo.
- **Costo:** separar el motor suma unos 1,5 días de DEV y medio día del TESTER dentro de HU-05 (contenedor, contrato, manejo de errores y una prueba de que el motor no tiene puerto público). Hacerlo ahora, antes de HU-05, es lo más barato.
- **Costo:** la captura hace un salto de red interno más (API → motor) y queda unos milisegundos más en memoria en otro proceso. Viaja por la red interna de docker, sin cifrar en el MVP; en producción, mTLS (brecha).
- **Costo:** el motor carga los modelos y la galería al arrancar. Mientras no esté listo, la API responde error controlado, nunca un resultado.
- **Abierto:** si el MININTER rechaza Python en el MVP (PA #37), este ADR se reemplaza por la alternativa A o B, y hay que recortar alcance.

## Decisiones del humano (2026-11-24, vía PM)

1. La API y los simuladores siguen en Python. El humano lo negocia con el MININTER con los argumentos de este ADR.
2. El motor se separa **ahora**, dentro de HU-05 (alternativa C descartada).
