# Prototipo navegable — HU-01 a HU-09

Rol: UX. Fecha: 2026-11-19. Encargo: PM → UX "Prototipo navegable (H1)". Revisión interna: viernes 27-nov-2026. Validación con el área usuaria: martes 1-dic-2026.

## Proyecto / herramienta

- Herramienta: un único archivo HTML local (`index.html`) con HTML, CSS y JavaScript, sin dependencias ni servicios externos, y sin red (decisión del humano, 2026-11-19: no se usa bolt.new). `../bolt-prompt.md` queda solo como referencia.
- Cómo abrirlo: doble clic en `index.html`, que se abre en Chrome o Edge. Al recargar, se reinicia todo.
- Canal/formato: app móvil Android vertical, dentro de un marco de teléfono (412 × 915). En pantallas de menos de 500 px de ancho ocupa toda la pantalla, sin el marco.
- Idioma: español (Perú). Datos 100 % sintéticos: los rostros son siluetas SVG dibujadas en el archivo y no hay ninguna foto.
- Usuarios: `jperez` (agente), `revisor1` (revisor) y `supervisor1` (supervisor). La clave es `demo123`.
- Guion de la sesión: [GUION-VALIDACION.md](GUION-VALIDACION.md).

## Pantallas implementadas (inventario aprobado el 2026-11-18)

Todas las del inventario de `../README.md`: AUTH-01 a 04, HOME-01, ERR-01, PLA-01 a 08, OCR-01 a 04, ROS-01 a 09, VER-01/02, REV-01 a 04, BIT-01/02 y el panel de demo. Cada pantalla lleva su ID en el código. Para la revisión interna, "⚙ Demo → Mostrar ID de pantalla" muestra el ID en una esquina.

| Pedido del encargo | Dónde se ve |
|---|---|
| Los tres resultados de rostro, con su texto literal | ROS-05, ROS-06, ROS-07 |
| Rechazo por calidad con su motivo | ROS-03 ("La captura no se envió a comparar") |
| Motivo obligatorio antes de consultar | PLA-02 (no consulta) y ROS-01 (no abre la cámara) |
| Cola del revisor; un agente nunca revisa su propia consulta | REV-01 (solo para el rol revisor). Si el agente entra por un enlace directo, ve ERR-01 y el intento se registra |
| Bitácora de solo lectura | BIT-01/02, sin controles de edición, borrado ni exportación |
| Sin permiso de cámara en rostro (HU-05 E6/E7) | ROS-09: sin galería ni otra vía de captura; nada se compara; ningún resultado facial. Se fuerza con "⚙ Demo → Cámara (rostro)". Marcas PA 29 (registro en la bitácora) y PA 30 (motivo al volver de ajustes), sin asumirlos |
| Placa no registrada (CONTRATO-HU-03 decisión 3) | PLA-08 con `XYZ-999` (o cualquier placa válida que no esté en la lista), o "⚙ Demo → Respuesta de placa: Forzar placa no registrada". Neutro; ni "sin requisitoria" ni error. "Volver" regresa con la placa y el motivo cargados |
| Errores de fuente que nunca se muestran como negativos | PLA-07, ROS-08 y el error "respuesta fuera de contrato" (HU-08 E3) |
| Sin la palabra "identificado" | Verificado con una búsqueda en el archivo: 0 apariciones |
| Foto con varias personas (HU-05 E8 a E10, aprobado 2026-11-20, sin desarrollo) | "⚙ Demo → Personas en la foto: Tres" → ROS-10, se elige un rostro y "Comparar este rostro". "Repetir captura" o "←" descartan la foto sin registrar nada (E9). "Seis" → ROS-03 "Hay más de 5 personas en la foto" (E10, PA 33). "Respuesta de rostro: Recorte: rostros muy juntos" → ROS-03 (ADR-0015). BIT-02 muestra "Rostros en la foto: N" |
| Aviso simulado al 105 (HU-09, aprobado 2026-11-20, sin desarrollo) | Botón en PLA-05 (`ABC-123`) y en VER-02 de `V-0005` (confirmada). AVI-00 permiso, AVI-01 vista previa ("Cancelar" no registra), AVI-02 registrado, AVI-03 error. Opciones "Permiso de ubicación", "Lectura de la ubicación" y "Registro del aviso" en el panel. Un aviso por consulta; la bitácora guarda "Ubicación disponible: sí/no", sin coordenadas |
| Valores provisionales | Motivo: lista "Opción 1/2/3 (por definir)" + "Otro" con 10 caracteres o más (PA 21). Máximo 3 candidatos (PA 22). Placa con "Solo estado" por defecto (PA 15). Espacio reservado para el aviso de tratamiento de datos en ROS-02 (PA 25) |

## Verificación hecha

- Recorrido automatizado en jsdom (script fuera del repositorio) de los flujos de los tres roles: 50 comprobaciones en verde (2026-11-19). Entre ellas: PLA-08 (por placa y forzada desde el panel de demo, con su registro en la bitácora y "Volver" con la placa cargada) y ROS-09 por permiso negado (E6) y retirado (E7), sin resultados faciales y sin nuevos registros en la bitácora.
- Capturas en Chrome sin interfaz de AUTH-01, HOME-01, PLA-01 con errores, PLA-05, ROS-02, REV-02, BIT-01 y el panel de demo.

## Decisiones de diseño aplicadas

- **Un solo archivo HTML sin dependencias**, para que funcione sin red y sin instalar nada, y para que no salga información del proyecto (PA 14).
- **Botón "⚙ Demo" en la franja superior**, no flotando sobre el contenido: así no tapa los botones principales.
- **Disparador de cámara blanco**, no rojo: el rojo queda reservado para "TIENE REQUISITORIA".
- **El visor de rostro solo muestra el óvalo guía**, sin silueta, para no sugerir a una persona.
- **"Volver" en PLA-07** regresa al formulario con la placa y el motivo cargados.
- **Placas que no están en la lista sintética** (por ejemplo `XYZ-999`): desde el 2026-11-19 el simulador responde "placa no registrada" (PLA-08), según CONTRATO-HU-03 decisión 3. Antes respondía "sin requisitoria", lo que contradecía la regla 7.
- **Bitácora**: se registran los inicios de sesión, intentos fallidos, bloqueos, consultas de placa, verificaciones de rostro, decisiones, revisiones vencidas, capturas eliminadas (tras una decisión o por vencimiento, ADR-0008), accesos denegados y errores. El rechazo por calidad no se registra como comparación.
- **Bloqueo por intentos**: se cuenta por el nombre de usuario escrito, exista o no, para no revelar qué usuarios existen (observación de HU-01 para ARCH).

## Escalado: diferencias con el inventario aprobado (respuesta del PM, 2026-11-19)

1. **PA 2, variante B ("mismo usuario revisa", botón "Revisar ahora" en ROS-05) — EXCLUIDA (confirmado por el PM el 2026-11-19).** El inventario la preveía como opción del panel de demo, marcada "requiere reabrir ADR-0003". No se muestra el 1-dic: la regla 4 de `AGENTS.md` y el ADR-0003 no se reabren desde una demo. La pregunta del PA 2 del guion se mantiene igual. Si el área usuaria pide que el mismo agente revise, se anota como pedido y se escala, sin prometer nada.
2. **Permiso de cámara denegado en la verificación de rostro — RESUELTO.** El humano aprobó HU-05 E6 y E7 (commit BA `9ebc9bf`). Se agregó ROS-09 (prototipo y `../wireframes/HU-05-verificar-rostro.md`) y la opción "Cámara (rostro)" en el panel de demo. Los PA 29 y 30 quedan marcados en la pantalla, sin asumirlos, y sus preguntas se agregaron al guion.

## Elementos no solicitados (aprobados por el PM el 2026-11-19)

Son herramientas del facilitador o textos de apoyo. No agregan funciones del producto:

- En el panel de demo: "Mostrar ID de pantalla", "Abrir enlace directo a una función de otro rol" (sirve para mostrar ERR-01) y "Reiniciar prototipo".
- En BIT-01, la franja "🔒 Registros de solo lectura". El wireframe tenía el candado solo en BIT-02.
- En VER-01, el texto "Verificaciones que terminaron en posible coincidencia".
- En OCR-04, al tocar "Abrir ajustes", la nota "En el prototipo este botón no abre los ajustes".
- El usuario sintético `lrojas` (L. Rojas): no puede iniciar sesión y solo sirve para que la cola del revisor tenga una pendiente de otro agente.

## Puntos abiertos que afectan el diseño

Los mismos de `../README.md` (PA 2, 7, 15, 18 a 28) y los PA 29 y 30 de ROS-09. Las preguntas exactas para la sesión están en el guion.

## Fuera de alcance respetado

No hay identificación masiva, video continuo, lectura automática de placas, carga desde galería, administración de usuarios, exportación de la bitácora ni acciones automáticas tras una coincidencia. Tampoco hay fuentes reales.
