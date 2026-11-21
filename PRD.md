# PRD — Movil Buscador (MININTER)

Prototipo de solución móvil para la búsqueda y localización de vehículos y personas con requisitoria, mediante consulta de placas y verificación biométrica facial. Cliente: Ministerio del Interior del Perú. Fuente de insumos: `Empezar.txt` y decisiones del equipo (2026-11-18).

**Enfoque MVP:** entrega rápida con data sintética, simuladores y herramientas gratuitas; las políticas de seguridad se documentan y solo se construye el mínimo que el encargo exige como módulo.

**Plazo y entrega:** plazo total de 30 a 40 días. El proveedor define el stack y aloja el desarrollo y el demo; el MININTER recibe código fuente y manual de instalación al cierre (pendiente de aceptación → Puntos Abiertos #8 y #17).

**Cronograma comprometido con el cliente (2026-11-19):** inicio el 2026-11-19, entrega final el 2026-12-30 (día 42) y plazo máximo de 45 días calendario (2027-01-02), con hitos el 23-nov, 2-dic, 21-dic, 28-dic y 30-dic. El estimado interno de trabajo sigue siendo de 30 a 40 días; la diferencia es reserva. Supuesto de trabajo vigente: el MININTER acepta el stack y el enfoque del proveedor (PA #8 y #17) hasta recibir la respuesta escrita, pedida para el 2026-11-23. Documentos: "Cronograma de implementación — Móvil Buscador (MVP)" y "Acta de inicio — Móvil Buscador (MVP)".

**Despliegue temprano (decisión del 2026-11-19):** para que el MININTER y el equipo prueben desde sus propios celulares en la demo del 2026-12-10, se despliega en el VPS una versión de prueba con lo construido en la Iteración 1 (inicio de sesión y roles, consulta de placa manual, bitácora y simuladores, solo con datos sintéticos), más un APK instalable por enlace y una guía para probadores (`docs/contratos/CONTRATO-DESPLIEGUE-01.md`). No cambia los hitos comprometidos: el despliegue y la prueba de aceptación siguen del 24 al 28-dic. Depende de que el proveedor contrate el VPS, un dominio y Supabase a más tardar el 2026-12-02. La lista de probadores se define antes del 2026-12-08.

## Problema

El MININTER necesita que su personal autorizado pueda verificar, desde un dispositivo móvil, si un vehículo (por su placa) o una persona (por su rostro) tiene requisitoria. Según el equipo, hoy no existe una solución hecha. El encargo pide además diagnosticar los procesos actuales de consulta y verificación, sus fuentes, restricciones de acceso y brechas tecnológicas.

Datos concretos del dolor actual (tiempos, volumen de consultas, errores) no fueron proporcionados → ver Puntos Abiertos #1.

## Actores

- **Usuario autorizado (personal en campo)**: se autentica, consulta placas (manual u OCR) y captura rostros para verificación; registra el motivo de cada consulta.
- **Revisor humano de coincidencias**: revisa las coincidencias biométricas antes de que se tome una decisión. No se indicó si es el mismo usuario en campo u otro rol → Punto Abierto #2.
- **Áreas usuarias y técnicas del MININTER**: aportan requerimientos y validan el prototipo navegable.
- **Fuentes de datos habilitadas (sistemas externos)**: responden consultas de placas, requisitorias y biometría; donde no haya autorización o ambiente, se reemplazan por simuladores.
- **Administrador de accesos**: implícito en "control de acceso por roles" y "gestión de sesiones", pero no descrito por el equipo → Punto Abierto #3.

## Alcance — Incluye

**Componente 1 — Diagnóstico, análisis y diseño**
- Levantamiento y análisis de requerimientos funcionales, no funcionales y de seguridad con las áreas usuarias y técnicas.
- Diagnóstico de los procesos actuales de consulta y verificación de requisitorias de vehículos y personas: fuentes, restricciones de acceso y brechas tecnológicas.
- Matriz de fuentes de datos e interoperabilidad: responsables, campos, mecanismos de autorización y dependencias.
- Diseño de flujos de consulta por placa y de verificación biométrica facial, con revisión humana de coincidencias, manejo de resultados no concluyentes y prevención de falsos positivos.
- Arquitectura móvil y de servicios, modelo de datos, perfiles de acceso, bitácoras, cifrado, conservación y eliminación de datos, y controles de protección de datos personales.
- Prototipo navegable validado con el área usuaria.
- Documentación OSIGP-FR-01 a FR-04.

**Componente 2 — Prototipo móvil funcional (con data sintética)**
- Seguridad y acceso: autenticación de usuarios autorizados, control de acceso por roles y gestión de sesiones.
- Consulta de placas: ingreso manual o captura con la cámara (OCR), consulta a la fuente habilitada o simulador, y visualización controlada del resultado.
- Verificación biométrica facial: captura del rostro con control de calidad, verificación contra fuentes habilitadas o datos sintéticos de prueba, y presentación de coincidencias para revisión humana.
  - Foto con varias personas (decisión del humano, 2026-11-20): la captura puede incluir a más de una persona; la app marca los rostros detectados y el usuario elige **uno solo**, con su motivo de consulta. Solo ese rostro se compara; los demás no se comparan, no se guardan ni se registran. No es identificación masiva: sigue siendo una consulta por persona. (Variante de HU-05.)
- Aviso simulado al 105 (decisión del humano, 2026-11-20): cuando una placa tiene requisitoria o el revisor confirma una posible coincidencia facial, el usuario puede pulsar "Avisar al 105 (simulado)". La app muestra en el mismo celular el mensaje que se enviaría: ubicación del dispositivo, placa o código de requisitoria, nombre (sintético) de la persona con la redacción "Posible coincidencia — requiere revisión" e ID de la consulta; nunca la foto. No se construye una aplicación del 105 ni se llama ni se envía nada a una central real. El envío nunca es automático y queda en la bitácora. Si no hay permiso de ubicación, el aviso lo dice y no inventa una ubicación. Ver Punto Abierto #32.
- Trazabilidad: bitácora de consultas con usuario, fecha, hora, motivo de consulta y resultado; gestión de errores.
- Servicios e interoperabilidad: servicios de consulta e integración con fuentes autorizadas; simuladores documentados cuando no existan autorizaciones o ambientes.
- Pruebas unitarias, funcionales, de integración, de seguridad y de desempeño.
- Evaluación documentada de la calidad biométrica.
- Despliegue en ambiente autorizado.

## Alcance — No incluye (por ahora)

- Identificación masiva por reconocimiento facial.
- Vigilancia indiscriminada.

Exclusiones decididas por el equipo para el MVP:

- Integración con fuentes reales: el MVP usa solo data sintética y simuladores documentados, como el encargo permite cuando no hay autorización o ambiente (requiere aceptación escrita → Punto Abierto #17).
- Implementación de políticas de seguridad avanzadas (gestión de dispositivos, manejo de llaves, integración con el directorio institucional): se documentan, no se construyen.

Se mantienen construidos, en versión mínima, los módulos que el encargo exige: inicio de sesión, roles, bitácora con motivo, revisión humana de coincidencias y conexión segura.

**Retención de la captura facial (ADR-0008, aprobado 2026-11-18):** se borra tras la comparación o tras la revisión humana. La captura de un candidato se conserva cifrada hasta la decisión del revisor o un máximo de 24 h. La galería del demo usa fotos del equipo con consentimiento ampliado (incluye procesamiento en el servidor del proveedor durante el proyecto) y todo el ambiente se elimina al cierre, con acta. El demo corre en un VPS pagado (alrededor de US$ 6–12 al mes, ADR-0009).

Paso a producción, soporte y modo sin conexión siguen como Puntos Abiertos #10 y #11, no como exclusiones asumidas.

## Criterios de éxito

Los insumos definen entregables, no métricas. Criterios derivados directamente del encargo:

- El prototipo navegable queda validado por el área usuaria.
- La documentación OSIGP-FR-01 a FR-04 queda entregada.
- Los cinco módulos del prototipo funcional operan con data sintética y/o fuentes habilitadas.
- Las pruebas unitarias, funcionales, de integración, seguridad y desempeño están ejecutadas y documentadas.
- La evaluación de calidad biométrica está documentada.
- El prototipo está desplegado en el ambiente autorizado.

Umbrales medibles (tiempo de respuesta, tasa de falsos positivos aceptable, calidad mínima de captura, precisión del OCR) no fueron dados → Punto Abierto #4.

## Puntos Abiertos

1. ¿Qué datos describen el problema actual (cómo se consulta hoy una requisitoria, cuánto tarda, cuántas consultas al día, qué errores ocurren)?
2. ¿El revisor de coincidencias biométricas es el mismo usuario en campo, un supervisor o una central? ¿Debe revisar en tiempo real? Opciones a presentar al MININTER (el diseño actual es la A, ADR-0003):
   - **A. Revisor separado:** otro usuario revisa desde una cola. Control alto; lento si no hay revisor disponible.
   - **B. El mismo agente revisa:** decide ahí mismo. Inmediato; control bajo (sesgo de confirmación en operativo). Requiere reabrir ADR-0003.
   - **C. Autorrevisión en modo operativo con ratificación:** un supervisor activa el "modo operativo"; el agente decide en campo con motivo obligatorio, la bitácora marca "autorrevisión" y un revisor la ratifica después. Inmediato con auditoría. Requiere reabrir ADR-0003 y una HU nueva (activar y cerrar el modo operativo) más un escenario de ratificación.
   - **D. Revisor central en tiempo real:** una central revisa en minutos mientras el agente espera. Control alto; requiere personal dedicado.
   - Nota: con "Posible coincidencia" el agente ya puede verificar identidad por otros medios (DNI, protocolo propio); la revisión no es requisito para actuar, pero el sistema nunca debe usarse como prueba de identidad.
3. ¿Existe un rol de administrador que cree usuarios y asigne roles dentro del prototipo, o la gestión de identidades viene de un sistema institucional existente?
4. ¿Qué umbrales cuantitativos definen el éxito (tiempo máximo de respuesta, tasa máxima de falsa aceptación, precisión mínima de OCR, usuarios concurrentes en pruebas de desempeño)?
5. Resuelto (2026-11-20): el MININTER envió las plantillas OSIGP-FR-01 a FR-07 y FR-10 (`entregables/osigp/plantillas/`). Faltan datos que solo da el cliente: nombre oficial y siglas del proyecto, N.º de solicitud, área usuaria, integrantes y sus áreas, y firmantes.
6. ¿Qué fuentes concretas debe consultar el prototipo (placas, requisitorias vehiculares, requisitorias de personas, biometría)? ¿Alguna tiene convenio o autorización vigente?
7. La verificación facial, ¿es 1:1 (confirmar identidad declarada) o comparación contra una lista acotada de personas requisitoriadas? Si es lista, ¿quién la define y de qué tamaño es?
8. ¿Acepta el MININTER que el desarrollo y el demo se alojen en infraestructura del proveedor, recibiendo al cierre el código fuente y el manual de instalación para desplegarlo en su ambiente autorizado?
9. ¿Qué perfiles de acceso (roles) debe tener el prototipo además del usuario en campo?
10. ¿El paso a producción, la operación y el soporte posteriores están fuera de este servicio?
11. ¿El prototipo debe funcionar con conectividad limitada o sin conexión?
12. ¿Qué dispositivos móviles usará el personal (Android/iOS, institucionales o personales)?
13. Resuelto: inicio el 2026-11-19; plazo comprometido con el cliente de 45 días calendario, con entrega final el 2026-12-30 (estimado interno: 30 a 40 días).
14. ¿El contrato permite usar herramientas de IA en la nube (p. ej. bolt.new) con información del proyecto?
15. ¿Qué datos se muestran en la "visualización controlada del resultado" de placa (solo "con/sin requisitoria" o también datos del propietario/vehículo)?
16. ¿Cuánto tiempo se conservan la bitácora, las imágenes de rostro y las de placa, y quién autoriza su eliminación?
17. ¿El MININTER acepta por escrito que el MVP se valide solo con data sintética y simuladores, que las políticas de seguridad avanzadas se entreguen documentadas pero no implementadas, y que el stack lo defina el proveedor? (Supuesto de trabajo desde 2026-11-19: se asume aceptado; la carta pide la respuesta escrita a más tardar el 2026-11-23. Si se rechaza, se reprograma el cronograma.)
18. ¿Cuál es el tiempo máximo de inactividad antes de cerrar la sesión? (HU-01)
19. ¿Cuántos intentos fallidos se permiten antes de bloquear la cuenta, y por cuánto tiempo? (HU-01)
20. ¿Qué formatos de placa debe aceptar la validación (particulares, motos, antiguas, diplomáticas, temporales)? (HU-03)
21. ¿El motivo de consulta es texto libre o una lista cerrada? Si es lista, ¿cuáles? (HU-03, HU-05)
22. ¿Cuántos candidatos como máximo se muestran en una posible coincidencia facial? (HU-05)
23. ¿Qué pasa si una posible coincidencia no se revisa en un tiempo determinado: vence, escala o queda pendiente? (HU-06)
24. ¿Quién consulta la bitácora, desde dónde (app o web) y con qué filtros? (HU-07)
25. ¿Se debe informar a la persona fotografiada antes de capturar su rostro (aviso de tratamiento de datos) y cómo? (HU-05; protección de datos, Ley N.º 29733)
26. ¿El revisor de coincidencias debe ver el score de similitud? (HU-06)
27. ¿El usuario en campo debe ver el motivo de la decisión del revisor, o solo la decisión? (HU-06)
28. ¿Con qué redacción se comunica una coincidencia confirmada por el revisor, para que no se lea como "identificado"? (HU-06; validar con área legal)
29. ¿Se registra en la bitácora un intento de verificación facial que no llegó a la captura por falta de permiso de cámara? Si se registra, ¿con qué datos (usuario, fecha, hora, motivo indicado) y qué figura como resultado? Lo único firme es que no se registra como comparación. (HU-05 E6 y E7)
30. Si el usuario da el permiso de cámara desde los ajustes y vuelve a la app, ¿se conserva el motivo que ya indicó o debe indicarlo de nuevo? (HU-05 E6 y E7)
31. ML Kit (lectura de placa en HU-04 y calidad facial en HU-05) envía a Google métricas técnicas de uso (modelo del teléfono, paquete y versión de la app, latencia, errores y un identificador por instalación) a servidores fuera del Perú; según Google no envía la imagen ni el texto leído, y no hay una forma oficial de desactivarlo. En el MVP se mantiene, se documenta y se avisa al usuario (decisión del 2026-11-20; `docs/arch/evaluaciones/HU-04-telemetria-mlkit.md`). ¿El MININTER acepta este envío en el prototipo? Para producción, ¿exige bloquearlo (MDM) o un OCR y una detección facial sin telemetría? (HU-04, HU-05; relacionado con el PA #14)
32. El aviso simulado al 105 no estaba en el encargo: ¿el MININTER lo acepta en el prototipo y con qué redacción y datos (ubicación, nombre, código de requisitoria)? ¿Se envía la ubicación GPS del dispositivo (pide un permiso nuevo y es un dato personal del agente) o se ingresa a mano? Supuesto de trabajo: ubicación del dispositivo con permiso, mostrada solo en el celular.

## Próximo paso

Historias de Usuario aprobadas el 2026-11-18 (`docs/hus/`); UX, diseño técnico y Sprint 0 completos. Siguiente (2026-11-19): UX construye el prototipo navegable para validarlo el 2026-12-01, y LEAD escribe los contratos de la iteración 1 (HU-08, HU-01, HU-02, HU-03, HU-07).

Histórico: entrega al Agente BA para iniciar Historias de Usuario. Los Puntos Abiertos deben quedar reflejados en cada HU afectada (en especial #2, #4, #7, #15, #16 y #17 en las HUs de biometría, placas y trazabilidad).
