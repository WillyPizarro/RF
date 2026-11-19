# ADR 0014: Resiliencia, con timeout por fuente, un reintento en lecturas y errores controlados

## Estado

Aceptado (2026-11-18)

## Contexto

- HU-03 E3: si la fuente no responde, la app muestra "No se pudo completar la consulta; intente nuevamente", **nunca** "sin requisitoria", y el error queda en la bitácora.
- HU-08 E3: una respuesta fuera de contrato produce un error controlado y queda en la bitácora.
- ADR-0006: hay adaptadores HTTP por fuente y simuladores con modos de falla. ADR-0005: no hay resultado sin registro. ADR-0011: placa con p95 ≤ 2 s.
- En el MVP, las fuentes son simuladores propios. Una fuente real puede ser más inestable.

## Decisión

- **Timeout de 3 s por llamada a una fuente**, configurable.
- **Un reintento** con espera corta (alrededor de 200 ms), solo en las **lecturas idempotentes** de placa y requisitoria.
- **La comparación facial no se reintenta automáticamente.** Si falla, la respuesta es un error controlado y el agente decide si repite la captura.
- Todo fallo (timeout, 5xx, respuesta fuera de contrato, error del motor) termina en un **código de error estable** (ADR-0007), registrado en la bitácora con el id de traza. **Ningún error se convierte en un resultado negativo** ("sin requisitoria" o "sin coincidencia").
- Logs estructurados (JSON) con un id de traza por solicitud, **sin** claves, tokens ni imágenes.
- No hay circuit breaker en el MVP.

## Alternativas consideradas

- **Sin reintentos.** Era lo más simple. Se descartó porque un fallo momentáneo de la red o del simulador obliga al agente a repetir a mano.
- **Reintentos con backoff y circuit breaker por fuente.** Era más robusto frente a una fuente real inestable. Se descartó porque sobra para simuladores propios y costaba alrededor de un día más. Queda como recomendación para producción.

## Consecuencias

- Las fallas se ven, quedan registradas y nunca se leen como "limpio", que es el error más grave en este dominio.
- **Costo:** si la fuente se cuelga, el peor caso de una consulta de placa es de unos 6,2 s (dos timeouts más la espera), muy por encima del p95 ≤ 2 s. La meta de p95 se mide con el simulador sano, y los casos de falla se miden aparte.
- **Costo:** sin circuit breaker, si una fuente cae, cada consulta espera su timeout completo. Es aceptable con 20 usuarios, pero no en producción.
