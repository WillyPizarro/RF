# ADR 0011: Valores provisionales de sesión, desempeño y OCR, y motivo de consulta

## Estado

Aceptado (2026-11-18). Los valores son **provisionales** y se reemplazan cuando el MININTER responda los PA #4, #18, #19, #20 y #21.

## Contexto

- Conflicto C4 / PA #4: los criterios de éxito no tienen umbrales medibles. Las HU hablan de un "umbral definido" sin dar valores.
- HU-01: tiempo máximo de inactividad (PA #18) y bloqueo por intentos fallidos (PA #19).
- HU-03: formatos de placa aceptados (PA #20) y el motivo de consulta, que puede ser texto libre o lista (PA #21).
- El encargo exige pruebas de desempeño. ADR-0009 fija el ambiente: un VPS de 2 vCPU y 4 GB. ADR-0010 fija un celular Android de gama media como referencia.
- Las metas biométricas ya están en el ADR-0004.

## Decisión

Todos los valores son **parámetros de configuración**, no constantes en el código.

| Parámetro | Valor provisional | Origen |
|---|---|---|
| Inactividad antes de cerrar la sesión | 10 min | PA #18 |
| Vigencia del token de acceso | 15 min (renovable mientras haya actividad) | HU-01 |
| Bloqueo por intentos fallidos | 5 intentos consecutivos → bloqueo de 15 min | PA #19 |
| Carga de la prueba de desempeño | 20 usuarios concurrentes (k6) en el VPS de referencia | PA #4 |
| Consulta de placa | p95 ≤ 2 s, de punta a punta en la API, con el simulador sin latencia artificial | PA #4 |
| Consulta de rostro (subida, calidad, comparación y respuesta) | p95 ≤ 5 s | PA #4 |
| Tasa de errores bajo carga | < 1 % | PA #4 |
| Precisión del OCR de día | ≥ 90 % de placas leídas exactamente (antes de que el usuario corrija) en un set de ≥ 100 imágenes, con el celular de referencia | PA #4 |
| Precisión del OCR de noche o en ángulo | Se mide y se reporta, sin meta | PA #4 |
| Formato de placa | Expresión regular configurable. Valor inicial: el formato vigente de autos (3 caracteres alfanuméricos, guion, 3 dígitos), **NO VERIFICADO** contra la normativa de placas. El resto de formatos espera al PA #20 | PA #20 |
| Motivo de consulta | **Catálogo cerrado configurable más "Otro"**. "Otro" exige un texto de ≥ 10 caracteres. El catálogo inicial (control vehicular, intervención policial, denuncia, operativo) se valida con el área usuaria | PA #21 |

## Alternativas consideradas

- **Paquete estricto** (5 min de inactividad, 3 intentos, placa con p95 ≤ 1 s, rostro con p95 ≤ 3 s, 50 usuarios, OCR ≥ 95 %). Era más cercano a producción. Se descartó porque, con un VPS pequeño y OpenCV en la API, hay un riesgo real de no cumplir el p95 del rostro por limitaciones del ambiente y no del diseño.
- **Paquete holgado** (15 min, 10 intentos, placa con p95 ≤ 3 s, rostro con p95 ≤ 8 s, 10 usuarios, OCR ≥ 80 %). Era fácil de cumplir. Se descartó porque el área usuaria podría verlo como poco exigente.
- **Motivo como texto libre.** Era lo más simple. Se descartó porque no permite filtrar ni hacer estadísticas en la bitácora (HU-07).
- **Solo lista cerrada.** Era lo más rápido en campo. Se descartó porque un caso que no está en la lista queda mal registrado.

## Consecuencias

- El TESTER y el DEV tienen números contra los cuales verificar (resuelve C4 de forma provisional).
- **Costo:** si el MININTER responde con valores distintos, hay que ajustar la configuración y repetir las pruebas de desempeño y OCR. El código no cambia.
- **Costo:** hay que armar un set de al menos 100 imágenes de placas sintéticas o de vehículos del equipo, sin datos de terceros. Ese trabajo va en el plan del TESTER.
- **Riesgo:** la expresión regular de placas no está verificada. Si rechaza placas válidas, el agente no puede consultar. Mientras no se responda el PA #20, la app debe mostrar el formato esperado en el mensaje de error.
