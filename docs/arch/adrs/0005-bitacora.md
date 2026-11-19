# ADR 0005: Bitácora de solo inserción, sin resultado sin registro y consultable desde la app

## Estado

Aceptado (2026-11-18)

## Contexto

- HU-07: cada consulta, decisión y error queda registrado con usuario, fecha, hora, tipo, motivo y resultado. Nadie puede modificar ni borrar los registros (E2). La imagen del rostro no se guarda; solo su identificador y el score (E3).
- HU-01, HU-02, HU-03, HU-05 y HU-06 generan registros: login, fallo, bloqueo, 403, consulta, error de la fuente, resultado biométrico y decisión del revisor.
- Regla de negocio 2 del encargo: la bitácora es de solo inserción y lleva motivo.
- PRD › Enfoque MVP: la inalterabilidad avanzada (firma, sellado de tiempo) se documenta, no se construye.
- Punto abierto de HU-07 / PA #24: ¿quién consulta la bitácora y desde dónde? ADR-0003 asigna esa función al rol `supervisor`.
- ADR-0001: solo la API escribe la bitácora.

## Decisión

1. **Inalterabilidad por permisos y trigger.**
   - Tabla `bitacora` en Postgres. La API se conecta con un rol de base de datos propio (`api_app`), no con el `service_role` de Supabase.
   - `api_app` solo tiene `INSERT` y `SELECT` sobre `bitacora`; `UPDATE`, `DELETE` y `TRUNCATE` están revocados.
   - Un trigger `BEFORE UPDATE OR DELETE` lanza una excepción para cualquier rol, incluido el dueño de la tabla. `TRUNCATE` se bloquea con un trigger de sentencia.
   - Ninguna migración posterior puede quitar el trigger sin un ADR nuevo.

2. **No hay resultado sin registro (fail-closed).** La API escribe el registro de la bitácora antes de responder y solo entrega el resultado si esa escritura se confirmó. Si la escritura falla, la app recibe "No se pudo completar la consulta; intente nuevamente" y no ve el resultado. Los errores de la fuente o del simulador también se registran (HU-03 E3, HU-08 E3).

3. **Consulta desde la misma app.** El rol `supervisor` tiene una pantalla de solo lectura en la app Expo, con filtros por usuario, rango de fechas, tipo de evento y resultado. Es paginada (la API pagina con cursor). No se construye un panel web.

4. **Contenido mínimo de cada registro:** id, fecha y hora del servidor (UTC), usuario, rol, tipo de evento, motivo (obligatorio en consultas y decisiones), parámetros de la consulta (la placa; nunca la imagen), resultado o banda, score, versión del modelo y del umbral (en eventos biométricos), id de la captura, id de la consulta relacionada (para vincular una decisión con su consulta), código de error y `es_sintetico = true`.

## Alternativas consideradas

- **Agregar un hash encadenado entre registros.** Detectaba incluso una manipulación por superusuario. Se descartó porque cuesta alrededor de un día más, obliga a serializar las inserciones y es la "inalterabilidad avanzada" que el PRD manda documentar. Queda en el informe de brechas como recomendación para producción.
- **Solo permisos, sin trigger.** Era lo mínimo. Se descartó porque el rol dueño de la tabla o una migración podían alterar registros sin que nada lo impidiera.
- **Responder primero y reintentar el registro después.** Daba más disponibilidad. Se descartó porque si la cola se pierde queda una consulta sin rastro, justo lo que HU-07 prohíbe.
- **Panel web para la bitácora.** Era más cómodo para auditar. Se descartó porque es un segundo frontend dentro del plazo.
- **Solo exportar un CSV.** Era lo más barato. Se descartó porque el supervisor no tendría nada navegable para la validación del área usuaria.

## Consecuencias

- Se puede verificar con una prueba automatizada: un `UPDATE` o `DELETE` sobre `bitacora` falla con cualquier rol (HU-07 E2).
- No existe una consulta que el agente haya visto sin su registro.
- **Costo:** la disponibilidad de las consultas queda atada a la de Postgres; si la base cae, el servicio entero deja de responder.
- **Costo:** alguien con acceso de superusuario a Postgres puede desactivar el trigger y alterar registros sin dejar rastro. Es un límite declarado del MVP.
- **Costo:** revisar muchos registros desde un celular es incómodo. Si el área usuaria lo pide en la validación, el panel web pasa a ser una HU nueva.
- La bitácora crece sin límite hasta que se defina la retención (PA #16, ver ADR de datos personales).
