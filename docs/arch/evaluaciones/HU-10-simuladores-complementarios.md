# Evaluación ARCH — Simuladores de las consultas complementarias de placa (HU-10)

- **Fecha:** 2026-11-20
- **Pedido por:** PM (decisión del humano del 2026-11-20; PRD `c200dc9`, PA #35)
- **Rama:** `entregables-osigp`
- **Tipo:** evaluación documental. **Sin desarrollo:** HU-10 se define, no se construye. Los contratos `contratos/fuentes/*.yaml` son del DEV; aquí solo se propone su forma para cuando el PM autorice el desarrollo.
- **HU-10:** todavía no existe (la escribe el BA). Esta evaluación se revisa contra ella cuando llegue, y recién entonces se actualizan FR-03 y FR-04.

## Resumen

1. **Encaja en el ADR-0006 sin ADR nuevo.** Son dos fuentes más, del mismo tipo que las tres que ya existen: servicio HTTP con contrato OpenAPI, datos sintéticos, modos de falla y un adaptador en la API. No cambia ninguna decisión vigente.
2. **Recomendación:** dos contratos nuevos y separados, `registro-vehicular.yaml` (SUNARP, simulado) y `papeletas.yaml` (SAT Lima, simulado). No conviene ampliar `placas.yaml`.
3. **Sin tabla nueva.** Cada consulta complementaria y la marca "No coincide con lo registrado" van a la **bitácora**, enlazadas a la consulta de placa original por `consulta_id` y con el mismo motivo.
4. **Regla 7:** los contratos distinguen tres casos: "la fuente no conoce la placa", "la conoce y no tiene papeletas" y "la fuente falló". Un error nunca llega a la app como "sin papeletas" ni "sin observaciones".
5. **Tres decisiones para el humano** (al final). Todo lo demás se resuelve dentro de los ADR vigentes.

## 1. Lo que dice la decisión

PRD, Alcance › Componente 2 › Consultas complementarias de placa: después del resultado de requisitoria, el usuario puede pedir, **una por una**:

- **"Datos del vehículo (SUNARP, simulado)":** marca, modelo, color, año y estado registral, **sin nombre ni DNI del propietario**.
- **"Papeletas (SAT Lima, simulado)":** cantidad, monto pendiente y si hay alguna grave. **Solo cubre Lima.**

Además:

- La app **nunca concluye "placa clonada"**. El usuario compara lo registrado con el vehículo y, si no coincide, marca "No coincide con lo registrado".
- Cada consulta y la marca van a la bitácora con el mismo motivo.
- El error de una fuente nunca se muestra como "sin papeletas" ni "sin observaciones".

## 2. Opciones evaluadas

| Opción | Qué es | A favor | En contra |
|---|---|---|---|
| **A. Dos fuentes nuevas y separadas** (recomendada) | `registro-vehicular.yaml` y `papeletas.yaml`, cada una con su ruta en el contenedor `simuladores`, su adaptador en la API y su URL configurable (`FUENTE_REGISTRO_VEHICULAR_URL`, `FUENTE_PAPELETAS_URL`) | Cada una corresponde a una fuente real distinta, con convenio, disponibilidad y campos propios (PA #6). Una se puede reemplazar o apagar sin tocar la otra. `placas.yaml` (requisitoria, HU-03) no cambia, así que HU-03 no se vuelve a probar | Dos adaptadores y dos contratos más que mantener |
| B. Ampliar `placas.yaml` con año, estado registral y papeletas | Una sola respuesta con todo | Una sola llamada | Mezcla tres fuentes reales en un contrato que no existe así en la realidad. Obliga a pedir siempre todo, cuando la decisión dice "a pedido, una por una": eso es traer más datos de los necesarios (minimización). Cambia el contrato de HU-03, que ya está aceptada |
| C. Una sola fuente "complementaria" con las dos rutas | Un contrato, dos rutas | Menos archivos | Mismos problemas de B al reemplazarla por las reales: SUNARP y SAT son dos proveedores distintos |

## 3. Forma propuesta de los contratos (estilo HU-08)

Igual que las fuentes actuales: OpenAPI 3.1, `servers` con `http://simuladores:8001` (red interna, sin publicar), `x-tiempo-respuesta-ms`, ejemplos, `es_sintetico: true` y errores `{codigo, mensaje}`. Placas sintéticas con el prefijo `ZZ`, normalizadas (mayúsculas y guion). El consumidor aplica el timeout de 3 s y un reintento en las lecturas (ADR-0014).

### 3.1 `registro-vehicular.yaml` — `GET /registro-vehicular/{placa}`

| Respuesta | Cuándo | Cuerpo |
|---|---|---|
| `200` | La fuente conoce la placa | `placa`, `marca`, `modelo`, `color`, `anio` (entero), `estado_registral` (enumeración provisional: `vigente`, `baja_definitiva`, `en_tramite`), `es_sintetico: true`. **Sin propietario:** el esquema no tiene ningún campo de persona, y una respuesta con campos extra es `FUENTE_RESPUESTA_INVALIDA` (`additionalProperties: false`, igual que hoy) |
| `404 PLACA_NO_REGISTRADA` | No la conoce | No significa "sin observaciones" |
| `500 ERROR_SIMULADO` | Falla | — |

Los valores de `estado_registral` son provisionales hasta conocer los de la fuente real (PA #6 y #35). No incluyen nada que repita la requisitoria (por ejemplo, "robado"): esa es la fuente de HU-03.

### 3.2 `papeletas.yaml` — `GET /papeletas/{placa}`

| Respuesta | Cuándo | Cuerpo |
|---|---|---|
| `200` | Consulta válida en la fuente | `placa`, `cobertura: "Lima Metropolitana"`, `cantidad` (entero ≥ 0), `monto_pendiente` (decimal en soles, cadena con 2 decimales para no perder precisión), `hay_grave` (booleano), `es_sintetico: true` |
| `500 ERROR_SIMULADO` | Falla | — |

- `cantidad: 0` es un resultado válido **solo** con un `200`. La app lo muestra como "Sin papeletas registradas en SAT Lima (la fuente solo cubre Lima)". La redacción final es de UX y BA. Nunca dice solo "Sin papeletas", porque la cobertura no es nacional.
- **No hay `404`:** el SAT responde "sin registros" para una placa que no tiene papeletas en Lima. Si la fuente real distingue "placa desconocida", se agrega cuando se conozca (PA #6).

### 3.3 Datos sintéticos

- **Una sola semilla.** Hay que extender `generar_semilla.py` (DEV) para que la marca, el modelo y el color de `registro-vehicular` sean **los mismos** que los de `placas` para la misma placa, y agregar el año. Si no coinciden, el simulador haría parecer "clonada" una placa por error de los datos de prueba.
- **Casos que debe cubrir la semilla:**
  - con y sin papeletas;
  - con una papeleta grave;
  - una placa conocida por `placas` pero no por `registro-vehicular` (`404`);
  - estado `baja_definitiva`.
- **Modos de falla:** se agregan `registro-vehicular` y `papeletas` a la lista `FUENTES` de `modos.py`, con los mismos cuatro modos: `normal`, `latencia`, `error_500` y `malformada`.

## 4. API, bitácora y datos

- **Endpoints propuestos** (el contrato lo decide el LEAD cuando se autorice HU-10): `POST /v1/consultas/{consulta_id}/vehiculo` y `POST /v1/consultas/{consulta_id}/papeletas`, y `POST /v1/consultas/{consulta_id}/no-coincide` para la marca. Solo el agente dueño de una consulta de **placa** ya resuelta puede usarlos (403 en otro caso). El motivo se toma de esa consulta: no se vuelve a pedir y no se puede cambiar.
- **Bitácora** (ADR-0005, fail-closed: sin registro no hay resultado). Eventos nuevos:
  - `CONSULTA_VEHICULO_REGISTRAL` y `CONSULTA_PAPELETAS`, con `consulta_id`, motivo y resultado;
  - `MARCA_NO_COINCIDE`, con `consulta_id`;
  - `ERROR_FUENTE`, que ya existe, para las fallas.
- **Sin tabla nueva.** La tabla `consulta` se mantiene: una fila por consulta de requisitoria. Las complementarias son eventos de esa consulta. El supervisor ya filtra la bitácora por tipo de evento (HU-07).
- **Errores:** `FUENTE_NO_DISPONIBLE` y `FUENTE_RESPUESTA_INVALIDA`, como hoy. Ninguno se convierte en "sin papeletas" (regla 7).
- **Matriz de tratamiento** (TECH-DESIGN, cuando se apruebe):
  - "Datos registrales del vehículo (sin propietario)": identificativo indirecto, a pedido del agente; no se guardan, solo el evento en la bitácora.
  - "Papeletas del vehículo": cantidad, monto y si hay grave. Mismo tratamiento.
  - Ninguno de los dos incluye datos de personas. Si el MININTER pide mostrar el propietario (PA #15 y #35), esta evaluación se reabre: es un dato personal más y cambia la matriz.

## 5. ¿Hace falta un ADR?

**No hace falta un ADR nuevo.** La extensión cabe dentro del ADR-0006 (simuladores con contrato), del ADR-0005 (bitácora), del ADR-0014 (timeout y reintento) y del ADR-0007 (contrato de la API). Si el humano aprueba esta evaluación:

- **ADR-0006:** una precisión con la lista de cinco fuentes.
- **TECH-DESIGN:** los eventos nuevos, las dos filas de la matriz y el inventario.
- **FR-03 y FR-04:** se actualizan cuando el BA entregue HU-10:
  - FR-03: diagrama de paquetes (adaptadores), estados y nota del diccionario (sin tabla nueva).
  - FR-04: inventario de servicios, despliegue y estructura de proyectos.

## Decisiones que pide al humano

1. ¿Dos fuentes separadas (opción A, recomendada) o ampliar `placas.yaml` (opción B)?
2. ¿Las consultas complementarias y la marca "No coincide" quedan solo como eventos de la bitácora enlazados a la consulta de placa (sin tabla nueva), como se propone?
3. Papeletas de una placa sin registros en Lima: ¿se acepta `200` con `cantidad: 0` y el texto "Sin papeletas registradas en SAT Lima (la fuente solo cubre Lima)"? La alternativa es no mostrar nada cuando no hay registros.
