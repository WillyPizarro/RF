# Guion de recorrido — Validación con el área usuaria (15 min)

Sesión virtual del martes 1-dic-2026. El facilitador comparte pantalla con `docs/ux/prototipo/index.html` abierto en el navegador local. No se envía ningún enlace ni archivo a los participantes.

## Antes de la sesión (5 min, sin público)

1. Abrir `index.html` en Chrome o Edge y recargar (el prototipo arranca limpio en cada recarga).
2. En **⚙ Demo**, dejar: placa "Según placa sintética", rostro "Posible coincidencia", cámara "Permiso concedido", lectura "Lee ABC-123", PA 7 "Lista acotada", PA 15 "Solo estado". "Mostrar marcas de PA": **activado** (las marcas sirven para hacer las preguntas). "Mostrar ID de pantalla": desactivado.
3. Tener a mano la lista de preguntas del final de este guion.
4. Usuarios: `jperez` (agente), `revisor1` (revisor) y `supervisor1` (supervisor). La clave de los tres es `demo123`.

## Mensajes que se dicen al empezar (1 min)

- Es un **prototipo**: todo lo que se ve son datos sintéticos (franja superior). No hay personas ni placas reales, y los rostros son siluetas.
- No consulta ninguna fuente real. Las respuestas las genera un simulador que el facilitador controla con el botón "Demo", que no forma parte de la app.
- Las etiquetas ámbar punteadas "PA nn" marcan **decisiones que les toca tomar a ustedes**. Al final se las preguntamos.
- La app **nunca identifica a una persona**. Como mucho dice "Posible coincidencia — requiere revisión", y esa coincidencia la valida otra persona.

## Recorrido

| Min | Rol / acción | Pantallas | Qué hacer notar |
|---|---|---|---|
| 0–1 | Introducción | — | Mensajes de arriba. |
| 1–2 | Login con `jperez` y una clave equivocada, luego con la correcta | AUTH-02 → HOME-01 | El mensaje no dice si falló el usuario o la clave. El agente ve solo dos funciones. (Mencionar sin mostrar: a los 5 fallos seguidos, la cuenta se bloquea 15 min, **PA 19**.) |
| 2–4 | Consultar placa: tocar **Consultar** con todo vacío; escribir `HOLA`; luego `ABC-123` + motivo "Opción 1" | PLA-02 + PLA-03 → PLA-04 → PLA-05 | **El motivo es obligatorio**: sin motivo no se consulta. El error de formato muestra el formato esperado (**PA 20**). El resultado muestra **solo el estado** (**PA 15**). |
| 4–5 | Nueva consulta: `DEF-456`, luego `GHI-789` | PLA-06, PLA-07 | "Sin requisitoria registrada **en la fuente consultada**", sin verde. Si la fuente falla, el mensaje es "No se pudo completar…": **un error nunca se muestra como resultado negativo**. |
| 5–6 | Botón de cámara junto a la placa → Capturar → Usar esta placa | OCR-01 → OCR-02 → PLA-01 | Una sola foto al tocar Capturar; no hay lectura continua. La lectura **no consulta sola**: el agente confirma la placa, elige el motivo y toca Consultar. |
| 6–9 | Verificar rostro: intentar continuar sin motivo; elegir motivo; Capturar con Demo en "Calidad: Más luz"; repetir con Demo en "Posible coincidencia" | ROS-01 → ROS-02 → ROS-03 → ROS-04 → ROS-05 | Sin motivo, la cámara no se abre. Espacio reservado para el aviso a la persona (**PA 25**). Una captura de mala calidad se rechaza con su motivo y **no se compara**. El resultado dice "Posible coincidencia — requiere revisión", **"Esto no es una identificación"** y no muestra el score. |
| 9–10 | Mostrar rápido los otros resultados (Demo → "No concluyente", "Sin coincidencia", "Error del servicio") | ROS-06, ROS-07, ROS-08 | Solo existen tres textos de resultado. "Sin coincidencia **en la lista consultada**" no significa "persona sin requisitoria". |
| 10–11 | Demo → "Abrir enlace directo a una función de otro rol" | ERR-01 | El agente no puede entrar a la revisión: **un agente nunca revisa su propia consulta**. El intento queda registrado. |
| 11–13 | Salir. Login con `revisor1` → abrir la primera pendiente → Guardar sin decidir → elegir "Descartar" + motivo → Guardar | REV-01 → REV-02 → REV-03 → REV-04 | Cola sin alarmas ni sonidos (**nada automático**). Captura y referencia lado a lado, con un máximo de 3 candidatos (**PA 22**). El score no se muestra (**PA 26**). La decisión exige un motivo. |
| 13–14 | Demo → "Vencer pendientes" · Salir · Login `jperez` → Mis verificaciones | VER-01 → VER-02 | El agente ve la decisión del revisor (redacción, **PA 28**) y no ve su motivo (**PA 27**). Si nadie revisa en 24 h, el agente ve "No concluyente — verifique por otros medios" (**PA 23**). |
| 14–15 | Salir · Login `supervisor1` → abrir un registro de rostro | BIT-01 → BIT-02 | Bitácora de **solo lectura**: no se puede editar, borrar ni exportar. Cada consulta queda con usuario, fecha, motivo y resultado. En rostro se guardan el ID de captura y el score, **nunca la imagen**. Aparecen "Revisión vencida" y "Captura eliminada". |

Si sobra tiempo: Demo → "Cerrar sesión por inactividad" (AUTH-03, **PA 18**) y Demo → PA 7 "1:1" para mostrar el campo "Identidad declarada".

## Preguntas al área usuaria (registrar la respuesta en el acta)

| PA | Pregunta | Dónde se vio |
|---|---|---|
| 2 | ¿Quién revisa una posible coincidencia: un revisor aparte (lo que muestra el prototipo), un supervisor o una central? ¿Necesitan la revisión en tiempo real? | REV-01 |
| 7 | ¿El agente compara contra una lista acotada o contra una identidad declarada (1:1)? | ROS-01, REV-02 |
| 15 | En el resultado de placa, ¿basta con el estado o necesitan datos del vehículo o del requisitoriado? ¿Cuáles? | PLA-05/06 |
| 18 | ¿Después de cuántos minutos sin uso se debe cerrar la sesión? | AUTH-03 |
| 19 | ¿5 intentos fallidos y 15 min de bloqueo les parece adecuado? | AUTH-04 |
| 20 | ¿Qué formatos de placa existen además de `ABC-123`? | PLA-03 |
| 21 | ¿Cuáles son los motivos de consulta de la lista? ¿Se mantiene "Otro" con texto libre? | PLA-01, ROS-01 |
| 22 | ¿Cuántos candidatos debe ver el revisor como máximo (hoy, 3)? | REV-02 |
| 23 | Si nadie revisa en 24 h, ¿es correcto que el agente vea "No concluyente"? | VER-01/02 |
| 24 | ¿Quién consulta la bitácora, desde dónde y con qué filtros? | BIT-01 |
| 25 | ¿Se avisa a la persona antes de fotografiar su rostro? ¿Cómo? | ROS-02 |
| 26 | ¿El revisor debe ver el score? | REV-02 |
| 27 | ¿El agente debe ver el motivo del revisor? | VER-02 |
| 28 | ¿Qué redacción usar cuando el revisor confirma la coincidencia? (validar con el área legal) | VER-02 |

## Reglas que no se discuten en la sesión

Si alguien pide alguna de estas cosas, se anota como pedido y se escala al PM. No se promete nada:

- Que la app diga "identificado" o algo equivalente.
- Que la consulta funcione sin motivo, o que una captura de mala calidad se compare igual.
- Alertas, sonidos o acciones automáticas tras una coincidencia.
- Video continuo, lectura automática de placas o búsquedas masivas.
- Que el agente revise su propia coincidencia.
