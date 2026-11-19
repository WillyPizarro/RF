# ADR 0006: Simuladores de fuentes como servicio HTTP con contrato OpenAPI

## Estado

Aceptado (2026-11-18)

## Contexto

- HU-08: la app consulta las fuentes a través del servicio, nunca directo al simulador (E1). Cambiar un simulador por otra implementación que cumpla el mismo contrato no requiere cambios en la app (E2). Una respuesta fuera de contrato produce un error controlado y queda en la bitácora (E3).
- Conflicto C3 / PA #6 / PA #17: el alcance incluye "integración con las fuentes autorizadas", pero el MVP excluye la integración real. Todavía no se sabe qué fuentes concretas existen ni qué campos devuelven.
- Regla de negocio 4 del encargo: sin fuentes reales; servicios con contrato y simuladores reemplazables.
- ADR-0001: la API es la única que habla con las fuentes. ADR-0004: la galería biométrica es una lista cerrada de personas con requisitoria.
- Los contratos de los simuladores se entregan al MININTER al cierre, para conectar las fuentes reales después (análisis de factibilidad, Propuesta de negociación).

## Decisión

1. Un contenedor **`simuladores`** (FastAPI) expone **un grupo de endpoints por fuente**, cada uno con su **contrato OpenAPI 3.1** versionado, que vive en `contratos/fuentes/<fuente>.yaml`:

   | Fuente simulada | Qué responde | Usada por |
   |---|---|---|
   | `placas` | Datos del vehículo y si tiene requisitoria vehicular vigente | HU-03 |
   | `requisitorias-personas` | Persona con requisitoria simulada: datos mínimos y fotos de referencia | HU-05, HU-06 |
   | `galeria` | Lista cerrada de personas habilitadas para la comparación (versión y fotos) | HU-05 (ADR-0004) |

   Los campos son provisionales hasta que el MININTER entregue "los campos que muestra hoy una consulta de requisitoria". Cada contrato documenta los campos, los códigos de error, los ejemplos y el tiempo de respuesta simulado.

2. La API tiene **un adaptador por fuente** (`FuentePlacas`, `FuenteRequisitorias`, `FuenteGaleria`) detrás de una interfaz. La URL, el timeout y las credenciales de cada fuente vienen de la configuración del entorno. Reemplazar el simulador por la fuente real es escribir otro adaptador o cambiar la URL, y en ningún caso tocar la app.

3. La API **valida cada respuesta contra el contrato** (modelos Pydantic generados desde o alineados con el OpenAPI). Si la respuesta no calza, timeout o error 5xx, la API devuelve un error controlado (`FUENTE_NO_DISPONIBLE` o `FUENTE_RESPUESTA_INVALIDA`) y lo registra en la bitácora. Nunca convierte un error en "sin requisitoria".

4. Los simuladores tienen **modos de falla configurables** (latencia, error 500, respuesta malformada) para que el TESTER pueda probar HU-03 E3 y HU-08 E3 sin tocar código.

5. Los datos sintéticos de los simuladores están en su propio esquema de base de datos o en archivos semilla versionados, separados de las tablas de la API, y todos llevan `es_sintetico = true`. Las fotos reales de las personas del equipo no van en el repositorio (ver el ADR de datos personales).

6. El simulador no es accesible desde fuera: solo la API lo alcanza, por la red interna de contenedores.

## Alternativas consideradas

- **Adaptadores internos que leen tablas `sim_*`.** Eran más rápidos de construir. Se descartaron porque no prueban la red (timeouts, caídas) y el contrato que se entregaría sería una interfaz Python, no un contrato de servicio que la fuente real pueda cumplir.
- **Mocks Mockoon o Prism generados desde el OpenAPI.** Se arman en horas. Se descartaron porque las respuestas son estáticas y no sostienen cientos de placas sintéticas coherentes con las requisitorias y la galería.

## Consecuencias

- HU-08 E2 se puede probar: una segunda implementación del contrato, por ejemplo un mock de Prism, debe funcionar sin cambios en la app.
- Al cierre se entregan contratos OpenAPI que sirven de punto de partida para la matriz de fuentes e interoperabilidad (Componente 1).
- **Costo:** hay un contenedor más y hay que mantener sincronizados los contratos, los datos sintéticos y los adaptadores.
- **Costo / riesgo:** los contratos se diseñan sin conocer las fuentes reales. Cuando el MININTER dé los campos, puede haber que reescribir contratos y adaptadores, aunque nunca la app.
- La galería se obtiene desde el simulador. La API calcula los embeddings al arrancar o cuando cambia la versión de la galería, y los guarda en caché (ADR-0004). Una fuente biométrica real podría hacer la comparación ella misma, en cuyo caso se reemplaza la implementación de `MotorBiometrico`, no solo el adaptador.
