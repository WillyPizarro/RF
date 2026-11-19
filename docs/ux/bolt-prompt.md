# Prompt para bolt.new — Prototipo navegable

> ⛔ **NO ENVIAR TODAVÍA.** El PA 14 (si el contrato permite usar herramientas de IA en la nube con información del proyecto) está abierto. Este prompt solo se pega en bolt.new cuando el usuario lo confirme por escrito.
>
> **Versión neutra**: el prompt no nombra al cliente ni a la institución, no incluye el PRD, contratos ni datos reales. Usa solo datos sintéticos inventados. Aun así, describe el producto; la decisión de enviarlo sigue sujeta al PA 14.
>
> **Después de generar**: revisar el resultado contra `README.md` → "Elementos no solicitados" y "Cómo se aplican las reglas de negocio clave". Reportar todo lo extra que haya agregado bolt (pantallas, campos, textos, colores verdes, la palabra "identificado").

---

## Prompt (copiar desde aquí)

```text
Construye un PROTOTIPO NAVEGABLE (solo frontend, sin backend real) de una app móvil en español (Perú) para personal autorizado que consulta si una placa de vehículo tiene requisitoria y verifica rostros contra una lista de prueba. TODO es simulado con datos sintéticos en memoria.

STACK
- React + Vite + TypeScript + Tailwind. Sin librerías de reconocimiento facial ni OCR reales: los resultados vienen de un simulador local.
- Plataforma de referencia: Android. Mostrar la app dentro de un marco de teléfono Android (412x915, con barra de estado y barra de navegación de Android), centrado en escritorio y a pantalla completa en móvil. Usar convenciones visuales de Android (Material) sin depender de una librería pesada.
- Navegación con estado interno o React Router. Sin persistencia: al recargar se reinicia.
- No usar fotos de personas reales: usar siluetas SVG o avatares ilustrados genéricos.

REGLAS DE TEXTO Y COLOR (obligatorias)
1. La palabra "identificado" (o "identificada", "identificación positiva") NO debe aparecer en ninguna parte. Los únicos resultados faciales son, literalmente:
   - "Posible coincidencia — requiere revisión" (ámbar)
   - "No concluyente — verifique por otros medios" (gris azulado)
   - "Sin coincidencia en la lista consultada" (gris neutro)
2. No usar color verde ni íconos de check en ningún resultado sobre placas o personas. Rojo solo para "TIENE REQUISITORIA". El check solo se permite para "Decisión registrada".
3. Los errores de servicio usan un ícono de advertencia y el texto "No se pudo completar la consulta; intente nuevamente" (o "...la verificación..."). Nunca deben parecer un resultado.
4. Nada automático: sin alertas, sonidos, notificaciones ni acciones tras una coincidencia.
5. Cámaras: una sola captura al tocar "Capturar". Sin video continuo, sin lectura automática, sin carga desde galería, sin lotes.
6. Franja superior fija en todas las pantallas: "DATOS SINTÉTICOS · PROTOTIPO".
7. No agregues pantallas, campos, botones ni textos que no estén en esta especificación (ni "olvidé mi clave", "recordarme", mapas, compartir, exportar, llamar, perfil, ajustes, estadísticas, onboarding).

MARCAS DE PUNTO ABIERTO
Las zonas que dependen de decisiones pendientes llevan una etiqueta pequeña ámbar con borde punteado "PA nn — pendiente". Un interruptor del panel de demo las oculta o las muestra (por defecto, visibles).

USUARIOS SINTÉTICOS (login con usuario/clave)
- jperez / demo123 → rol "Agente"
- revisor1 / demo123 → rol "Revisor"
- supervisor1 / demo123 → rol "Supervisor"

PLACAS SINTÉTICAS
- ABC-123 → tiene requisitoria
- DEF-456 → sin requisitoria
- GHI-789 → la fuente no responde (error)
- Validación provisional de formato: 3 alfanuméricos + "-" + 3 dígitos (/^[A-Z0-9]{3}-\d{3}$/, aceptar sin guion y normalizar). Etiqueta "PA 20".

BITÁCORA EN MEMORIA
Cada evento agrega un registro inmutable (no hay edición ni borrado): fecha-hora, usuario, tipo (Inicio de sesión, Intento fallido, Cuenta bloqueada, Consulta de placa, Verificación de rostro, Decisión de revisión, Revisión vencida, Captura eliminada, Acceso denegado, Error), motivo, resultado, y en rostro: "ID de captura" (aleatorio) y "Score" (número simulado). Nunca guardar ni mostrar la imagen. Cada registro lleva la marca "SINTÉTICO". Precargar unos 8 registros de ejemplo, entre ellos "Revisión vencida" y "Captura eliminada" (causa: vencimiento 24 h) de V-0002, hechos por el usuario "sistema" y con la etiqueta "PA 23".

PANTALLAS (IDs entre corchetes; mantener los IDs como comentario en el código)

[AUTH-01] Login: título "Movil Buscador", subtítulo "Acceso solo para personal autorizado", campos Usuario y Clave, botón "INGRESAR". Lleva a la pantalla inicial del rol.
[AUTH-02] Error de login: alerta "Usuario o clave incorrectos" (no decir cuál falló), conserva el usuario y vacía la clave, registra "Intento fallido". No mostrar cuántos intentos quedan. Contar los fallos seguidos por usuario: al 5.º fallo seguido, la cuenta queda bloqueada 15 min (valores en constantes de configuración) y se pasa a AUTH-04.
[AUTH-03] Sesión cerrada: alerta informativa azul "Su sesión se cerró por inactividad. Ingrese de nuevo." + etiqueta "PA 18". Al cerrarse por inactividad (simulada desde el panel de demo) se borra todo el estado de navegación y no se puede volver con "atrás".
[AUTH-04] Cuenta bloqueada temporalmente: alerta ámbar con candado, "Cuenta bloqueada temporalmente. Podrá volver a intentar a las HH:MM (en N min)." (hora calculada al fin del bloqueo), con la etiqueta "PA 19". Mientras dure el bloqueo, CUALQUIER intento de ese usuario, con clave correcta o incorrecta, muestra este mismo mensaje y vacía la clave. Nunca indicar si la clave era correcta. "INGRESAR" sigue activo. No decir cuántos intentos hubo ni ofrecer desbloqueo. Registrar "Cuenta bloqueada" en la bitácora.

[HOME-01] Inicio de "Agente": encabezado "Hola, J. Pérez", "Rol: Agente" y botón "Salir". Dos botones grandes a todo el ancho: "CONSULTAR PLACA" y "VERIFICAR ROSTRO". Abajo, enlace secundario "Mis verificaciones (n pend.)".
[ERR-01] "No tiene permiso para usar esta función. El intento quedó registrado." + "VOLVER AL INICIO". Se dispara si un rol abre por URL o ruta una pantalla de otro rol (por ejemplo, jperez abre /revision). Registra "Acceso denegado".

COMPONENTE "Motivo de consulta *" (compartido, etiqueta "PA 21 — provisional"):
- Select con "Opción 1 (por definir)", "Opción 2 (por definir)", "Opción 3 (por definir)" y "Otro". No inventar motivos reales: las opciones del catálogo siguen por definir.
- Si elige "Otro", aparece el campo de texto obligatorio "Describa el motivo *", de 10 caracteres como mínimo.
Errores: vacío → "Indique el motivo de la consulta."; "Otro" con menos de 10 caracteres → "Describa el motivo (mínimo 10 caracteres)."

[PLA-01] "Consultar placa": campo Placa en mayúsculas y monoespaciado (etiqueta "PA 20"), con botón de cámara "Leer con cámara" al lado; componente Motivo; botón "CONSULTAR".
[PLA-02] Sin motivo: error inline en Motivo y no se envía.
[PLA-03] Formato inválido: error inline "El formato de placa no es válido. Formato esperado: ABC-123 (3 letras o números, guion, 3 números)." y no se envía. Si faltan los dos, mostrar ambos errores.
[PLA-04] "Consultando…" con spinner por ~1,5 s y el botón deshabilitado.
[PLA-05] Resultado rojo grande: placa + "TIENE REQUISITORIA". Debajo, bloque punteado "Datos adicionales (campos por definir)" con etiqueta "PA 15", visible solo si la variante PA 15 es "Estado + datos". Luego Motivo y "Consultado: fecha hora". Botón "NUEVA CONSULTA". Sin otros botones de acción.
[PLA-06] Resultado gris: placa + "Sin requisitoria registrada en la fuente consultada", mismo bloque PA 15, Motivo, fecha y "NUEVA CONSULTA". Sin verde.
[PLA-07] Error: "No se pudo completar la consulta; intente nuevamente", botón "REINTENTAR" (conserva placa y motivo) y "Volver". Registra Error.

[OCR-01] Visor de cámara simulado (fondo oscuro con marco rectangular de placa), texto "Encuadre la placa y toque Capturar", botón redondo "CAPTURAR" y enlace "Ingresar manualmente".
[OCR-02] "Placa leída" en un campo editable precargado según el panel de demo, texto "Confirme o corrija la placa antes de consultar.", botón "USAR ESTA PLACA" (vuelve a PLA-01 con la placa cargada; NO consulta) y "Volver a capturar". No mostrar foto.
[OCR-03] "No se pudo leer la placa. Pruebe de frente y con más luz." con "VOLVER A INTENTAR" e "Ingresar manualmente".
[OCR-04] Si el panel de demo marca "Permiso denegado": "La app no tiene permiso para usar la cámara. Para darlo: Ajustes › Aplicaciones › Movil Buscador › Permisos › Cámara." con "ABRIR AJUSTES" (sin efecto en el prototipo) e "Ingresar manualmente".

[ROS-01] "Verificar rostro — 1 de 2": componente Motivo. Si la variante PA 7 es "1:1", agregar un bloque punteado "Identidad declarada" con un campo de texto, la nota "tipo de dato por definir" y la etiqueta "PA 7". Botón "CONTINUAR A CÁMARA" (no avanza sin motivo).
[ROS-02] "2 de 2": visor simulado con óvalo guía, texto "Rostro de frente, buena luz, una sola persona.", un bloque punteado "Aviso a la persona — por definir" con etiqueta "PA 25" (sin contenido de aviso ni casilla de consentimiento) y botón "CAPTURAR".
[ROS-03] Captura rechazada (si el panel de demo elige un motivo de calidad): ícono de advertencia, motivo en grande ("Mire de frente" | "Más luz" | "Imagen borrosa" | "Solo debe aparecer una persona" | "No se detectó un rostro"), texto "La captura no se envió a comparar." y botón "REPETIR CAPTURA". No se registra comparación.
[ROS-04] "Comparando con la lista de prueba…" (~2 s).
[ROS-05] Tarjeta ámbar "Posible coincidencia — requiere revisión". Debajo: "Esto no es una identificación. Un revisor debe validar la coincidencia." Luego "Estado: Pendiente de revisión", un bloque punteado "Datos del candidato — no se muestran por ahora" con etiquetas "PA 15" y "PA 22", y Motivo, fecha-hora e ID (V-000n). No mostrar score. Botones según PA 2: "Revisor separado" → "VER EN MIS VERIFICACIONES"; "Mismo usuario" → "REVISAR AHORA" (abre REV-02), con la etiqueta "requiere reabrir ADR-0003" junto al botón. Siempre "NUEVA VERIFICACIÓN". Crea un pendiente en la cola de revisión.
[ROS-06] Tarjeta gris azulada "No concluyente — verifique por otros medios" + "NUEVA VERIFICACIÓN".
[ROS-07] Tarjeta gris "Sin coincidencia en la lista consultada", texto "La comparación se hizo solo contra la lista disponible." con etiqueta "PA 7", y "NUEVA VERIFICACIÓN". Nunca decir "sin requisitoria".
[ROS-08] Error: "No se pudo completar la verificación; intente nuevamente" con "REPETIR CAPTURA" y "Volver".

[VER-01] "Mis verificaciones" (agente): lista de sus verificaciones que terminaron en posible coincidencia, con estado "Pendiente de revisión" o "Revisada". Si pasaron 24 h sin revisión (simulado), la verificación muestra "No concluyente — verifique por otros medios", con la etiqueta "PA 23". Precargar 1 vencida (V-0002).
[VER-02] Detalle: "Resultado inicial: Posible coincidencia — requiere revisión". Si fue revisada: "Revisión: coincidencia confirmada por el revisor" | "Revisión: descartada por el revisor" | "Revisión: no concluyente según el revisor" (etiqueta "PA 28" junto a esa línea), con fecha-hora, y un bloque punteado "Motivo del revisor — por definir" con etiqueta "PA 27". Si sigue pendiente: "Estado: Pendiente de revisión". Si venció: en lugar del resultado de la revisión mostrar "No concluyente — verifique por otros medios", con la etiqueta "PA 23".

[REV-01] Inicio del "Revisor": "Pendientes de revisión" (etiqueta "PA 2"), tarjetas con ID, fecha-hora, usuario y motivo, las más antiguas primero. Sin badges rojos ni sonidos. Si está vacía: "No hay coincidencias pendientes". Precargar 2 pendientes sintéticos. Las vencidas (24 h sin revisión) NO aparecen en esta pantalla: salen de la cola y no hay ninguna sección de vencidas.
[REV-02] "Revisar V-000n": arriba el motivo original, el usuario y la hora. Dos imágenes del mismo tamaño lado a lado: "CAPTURA" y "REFERENCIA" (siluetas distintas). Selector "Candidato ‹ 1 de 3 ›" solo si PA 7 = "Lista" (etiquetas "PA 22" y "PA 7"). Bloques punteados "Datos de la referencia (por definir)" (PA 15) y "Score — por definir" (PA 26). Radios sin preselección: "Confirmar coincidencia", "Descartar", "No concluyente". Textarea obligatoria "Motivo de la decisión *". Botón "GUARDAR DECISIÓN".
[REV-03] Validación: "Elija una decisión." y/o "Escriba el motivo de su decisión." No guarda.
[REV-04] Check + "Decisión registrada", ID · decisión · hora, y "VOLVER A PENDIENTES". Registra "Decisión de revisión" y actualiza VER-02 del agente.

[BIT-01] Inicio del "Supervisor": "Bitácora" (etiqueta "PA 24"). Barra de filtros punteada (Fecha, Usuario, Tipo) con etiqueta "PA 24" que filtra en memoria. Lista en orden cronológico inverso con tarjetas: fecha-hora, usuario, tipo, motivo y resultado, más la marca "SINTÉTICO". Sin editar, borrar ni exportar.
[BIT-02] Detalle con un candado y "Registro de solo lectura": todos los campos. En rostro: "ID de captura", "Score" e "Imagen: no almacenada". "Origen: datos sintéticos".

PANEL DE DEMO (herramienta del prototipo, no del producto)
Botón flotante pequeño "⚙ Demo" en todas las pantallas, que abre una hoja inferior con:
- Respuesta de placa: "Según placa sintética" | "Forzar fuente caída" | "Forzar respuesta inválida" (ambas llevan a PLA-07).
- Respuesta de rostro: "Posible coincidencia" | "No concluyente" | "Sin coincidencia" | "Error" | "Calidad: Mire de frente" | "Calidad: Más luz" | "Calidad: Imagen borrosa" | "Calidad: Varias personas" | "Calidad: Sin rostro".
- Cámara: "Permiso concedido" | "Permiso denegado".
- OCR: "Lee ABC-123" | "Lee DEF-456" | "Lee GHI-789" | "Falla la lectura".
- PA 2: "Revisor separado" (por defecto, ADR-0003) | "Mismo usuario — requiere reabrir ADR-0003".
- PA 7: "Lista acotada" | "1:1".
- PA 15: "Solo estado" | "Estado + datos".
- Interruptor "Mostrar marcas de PA".
- Botón "Cerrar sesión por inactividad" (lleva a AUTH-03).
- Botón "Bloquear cuenta (simular 5 intentos)": bloquea al usuario jperez por 15 min y lleva a AUTH-04. Botón "Desbloquear cuentas": reinicia los contadores y bloqueos.
- Botón "Vencer pendientes (simular 24 h)": pasa todas las pendientes a vencidas (PA 23). Desaparecen de REV-01, el agente las ve como "No concluyente — verifique por otros medios" y se registran "Revisión vencida" y "Captura eliminada" en la bitácora.

ESTILO
Sobrio e institucional neutro, sin logotipos ni escudos. Fondo claro, texto oscuro, alto contraste para uso al aire libre. Botones táctiles de al menos 48 px de alto. Tipografía de sistema; placa en monoespaciada. Ámbar #B45309 para revisión pendiente, rojo #B91C1C para requisitoria, gris #475569 para neutro y errores, azul #1D4ED8 para acciones primarias e información. Nada de verde.
```
