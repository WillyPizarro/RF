# Anexo HU-04 — Aviso de datos técnicos que ML Kit envía a Google

- **Fecha:** 2026-11-20 · **Rol:** BA, con UX (coordina) · **Pedido por:** LEAD (M-11, opción A aprobada por el humano)
- **Base:** `docs/arch/evaluaciones/HU-04-telemetria-mlkit.md` (fuentes de Google consultadas por ARCH el 2026-11-20)
- **Estado:** aprobado por el humano, 2026-11-20 (vía PM). El texto final entra en CONTRATO-HU-04 v5 (LEAD).
- **Quién lo usa:** el texto breve va en la pantalla OCR-01 (UX). El detalle va en la guía de probadores, que UX cita en `docs/ux/revisiones/HU-04.md`.

## 1. Aviso breve en OCR-01

**Título:** Antes de leer la placa

**Cuerpo:**
> Para leer la placa, la app usa ML Kit, una herramienta de Google que funciona en este teléfono. Según Google, ML Kit no le envía la foto ni la placa leída, pero sí le envía datos técnicos de uso y un código de esta instalación.

**Botón:** Entendido

Cuándo aparece: lo define UX en OCR-01 y lo fija la HU-04, Escenario 4.

Por qué el texto dice "ML Kit no le envía" en vez de "no salen del teléfono": la placa leída **sí sale** del teléfono cuando el usuario la confirma y consulta (HU-03). La que no sale hacia Google es la que procesa ML Kit. La afirmación se atribuye a Google porque el equipo no la verificó.

## 2. Detalle para la guía de probadores

### Datos técnicos que la app envía a Google al leer la placa

**Qué es.** Para leer la placa con la cámara, la app usa **Google ML Kit** (reconocimiento de texto). Viene dentro de la app y hace la lectura en el teléfono.

**Qué no se envía a Google, según Google.**
- La foto de la placa.
- El texto que se lee (la placa).

Fuente: términos de ML Kit, <https://developers.google.com/ml-kit/terms> (modificados el 14-may-2025): *"processing of the input data (e.g. images, video, text) fully happens on-device"* y *"ML Kit does not send that data and the resultant outputs to Google servers"*.

Aparte de eso, la app no guarda la foto de la placa ni la envía al servidor del proyecto (HU-04, CONTRATO-HU-04 §6). La placa que usted **confirma y consulta** sí va al servidor del proyecto, como en el ingreso manual (HU-03).

**Qué se envía a Google, según Google.** Son datos técnicos de uso y rendimiento:
- Marca y modelo del teléfono, versión del sistema y aceleradores de ML disponibles.
- Nombre y versión de la app.
- Un **código de esta instalación** de la app (Google lo llama *per-installation identifier*). Según Google, ese código "no está pensado para" reconocer a un usuario ni a un teléfono concreto.
- Tiempos de respuesta y configuración de la lectura (por ejemplo, el formato y la resolución de la imagen).
- Tamaño de la entrada y de la salida, y versión de la herramienta.
- Tipo de evento (inicio, lectura, cierre) y códigos de error.

Según Google, estos datos sirven para medir el rendimiento, corregir fallas, mantener y mejorar la herramienta y detectar mal uso. Google dice que viajan cifrados (HTTPS) a sus servidores, que están fuera del Perú, y que no los pasa a terceros. ML Kit también puede conectarse a Google de vez en cuando para recibir correcciones y modelos actualizados.

Fuentes: <https://developers.google.com/ml-kit/android-data-disclosure> (modificada el 14-may-2025) y <https://developers.google.com/ml-kit/ios-data-disclosure> (sin fecha visible).

**¿Se puede apagar?** No. Google no ofrece ninguna opción oficial para desactivar el envío. La placa se puede ingresar siempre a mano, pero **no está verificado** que, si no se usa la lectura por cámara, la app deje de enviar estos datos.

**Qué no verificó el equipo.**
- Todo lo anterior lo **afirma Google**. El equipo no capturó el tráfico de red para comprobarlo.
- En el teléfono hay una cola local de eventos (`com.google.android.datatransport.events`). Su contenido se está revisando (encargo M-11). Si aparece la foto o el texto leído, la decisión se reabre.

**En este prototipo (MVP).** Se usan solo datos sintéticos y teléfonos de prueba. No hay ciudadanos reales. Para producción queda como brecha abierta: bloqueo de red por MDM o firewall, o cambio de OCR. El área legal define la base legal, el flujo de datos fuera del país y cómo se informa al usuario.

**Si nota algo raro** (por ejemplo, que la app pide subir fotos o muestra la placa en otro lugar), anótelo en su informe de prueba con la fecha y la hora.

## 3. Puntos abiertos (resueltos por el humano, vía PM, 2026-11-20)

1. **Validación legal del texto:** queda como brecha de producción en `docs/contratos/PENDIENTES.md`. En el MVP se usa el texto aprobado. (ARCH, sección 3: "Normativa"; Ley N.º 29733, a validar.)
2. **Constancia de "Entendido":** en el MVP **no** se guarda en la bitácora; el aviso solo se lleva en memoria. Se decide en producción junto con la validación legal.
3. **HU-05:** tendrá su propio aviso, definido en su contrato (sujeto a que ARCH confirme que ML Kit Face Detection no envía la imagen ni datos derivados; `PENDIENTES.md`).

## 4. Nota de redacción

El texto que ve el usuario no usa "identificador": contiene la raíz de la palabra prohibida (regla 1 de `AGENTS.md`), y las pruebas del TESTER rechazan cualquier texto con `identificad` (por ejemplo, `services/api/tests/ayudas_hu01.py:31` y `apps/movil/__tests__/HU03_HU07.test.tsx:462`). Por eso se usa "código de esta instalación".
