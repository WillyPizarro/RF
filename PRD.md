# PRD — Movil Buscador (MININTER)

Prototipo de solución móvil para la búsqueda y localización de vehículos y personas con requisitoria, mediante consulta de placas y verificación biométrica facial. Cliente: Ministerio del Interior del Perú. Fuente de insumos: `Empezar.txt` y decisiones del equipo (2026-11-18).

**Enfoque MVP:** entrega rápida con data sintética, simuladores y herramientas gratuitas; las políticas de seguridad se documentan y solo se construye el mínimo que el encargo exige como módulo.

**Plazo y entrega:** plazo total de 30 a 40 días. El proveedor define el stack y aloja el desarrollo y el demo; el MININTER recibe código fuente y manual de instalación al cierre (pendiente de aceptación → Puntos Abiertos #8 y #17).

**Cronograma comprometido con el cliente (2026-11-19):** inicio el 2026-11-19, entrega final el 2026-12-30 (día 42) y plazo máximo de 45 días calendario (2027-01-02), con hitos el 23-nov, 2-dic, 21-dic, 28-dic y 30-dic. El estimado interno de trabajo sigue siendo de 30 a 40 días; la diferencia es reserva. Supuesto de trabajo vigente: el MININTER acepta el stack y el enfoque del proveedor (PA #8 y #17) hasta recibir la respuesta escrita, pedida para el 2026-11-23. Documentos: "Cronograma de implementación — Móvil Buscador (MVP)" y "Acta de inicio — Móvil Buscador (MVP)".

**Despliegue temprano (decisión del 2026-11-19):** para que el MININTER y el equipo prueben desde sus propios celulares en la demo del 2026-12-10, se despliega en el VPS una versión de prueba con lo construido en la Iteración 1 (inicio de sesión y roles, consulta de placa manual, bitácora y simuladores, solo con datos sintéticos), más un APK instalable por enlace y una guía para probadores (`docs/contratos/CONTRATO-DESPLIEGUE-01.md`). No cambia los hitos comprometidos: el despliegue y la prueba de aceptación siguen del 24 al 28-dic. Depende de que el proveedor contrate el VPS, un dominio y Supabase a más tardar el 2026-12-02. La lista de probadores se define antes del 2026-12-08.

**Alcance del MVP con el stack del MININTER (decisión del humano, 2026-11-24):** antes del 30-dic se construyen la migración a Flutter (HU-01, 02, 03, 04 y 07 en la app nueva), NGINX, HU-05 escenarios 1 a 7 con el motor separado, HU-06 (opción A del PA #2, mientras el MININTER no responda) y **HU-09 (aviso simulado al 105)**. **Quedan definidas y aprobadas, pero fuera de la construcción del MVP:** HU-05 escenarios 8 a 10 (foto con varias personas) y HU-10 (SUNARP y SAT). Keycloak se entrega documentado. Estimado de ARCH en `docs/arch/evaluaciones/PA-37-39-stack-mininter.md`; los días los valida el LEAD.

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
  - Foto con varias personas (decisión del humano, 2026-11-20): la captura puede incluir a más de una persona; la app marca los rostros detectados y el usuario elige **uno solo**, con su motivo de consulta. Solo ese rostro se compara; los demás no se comparan, no se guardan ni se registran. No es identificación masiva: sigue siendo una consulta por persona. (HU-05, escenarios 8 y 9, aprobados el 2026-11-20; sin desarrollo hasta nueva orden del PM.)
- Aviso simulado al 105 (decisión del humano, 2026-11-20): cuando una placa tiene requisitoria o el revisor confirma una posible coincidencia facial, el usuario puede pulsar "Avisar al 105 (simulado)". La app muestra en el mismo celular el mensaje que se enviaría: ubicación del dispositivo, placa o código de requisitoria, nombre (sintético) de la persona con la redacción "Posible coincidencia — requiere revisión" e ID de la consulta; nunca la foto. No se construye una aplicación del 105 ni se llama ni se envía nada a una central real. El envío nunca es automático y queda en la bitácora. Si no hay permiso de ubicación, el aviso lo dice y no inventa una ubicación. Ver Punto Abierto #32. HU-09 aprobada el 2026-11-20, con vista previa y confirmación antes de registrar el aviso, y fecha y hora en el mensaje; sin desarrollo hasta nueva orden del PM.
- Consultas complementarias de placa, simuladas (decisión del humano, 2026-11-20): después del resultado de requisitoria, el usuario puede pedir, una por una, "Datos del vehículo (SUNARP, simulado)" —marca, modelo, color, año y estado registral, sin nombre ni DNI del propietario— y "Papeletas (SAT Lima, simulado)" —cantidad, monto pendiente y si hay alguna grave; cubre solo Lima—. La app nunca concluye "placa clonada": muestra las características registradas para que el usuario las compare con el vehículo y, si no coinciden, él marca "No coincide con lo registrado". Cada consulta y esa marca quedan en la bitácora con el mismo motivo. Un error de la fuente nunca se muestra como "sin papeletas" ni "sin observaciones". (HU-10, aprobada el 2026-11-20: dos fuentes simuladas separadas, sin propietario por esquema cerrado; en la bitácora solo los eventos, sin guardar los datos devueltos. Se define, no se desarrolla todavía.) Ver Punto Abierto #35.
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
   - **E. Autorrevisión según el motivo (propuesta del humano, 2026-11-24):** si el agente elige el motivo "Operativo", la posible coincidencia no va a la cola: el agente ve la comparación y decide él mismo, con motivo obligatorio. Con cualquier otro motivo pasa a un revisor, como en la A. El sistema nunca decide solo; lo único automático es el camino. Inmediato en operativos y control alto en los demás casos, sin pantalla para activar un modo. Riesgo: el motivo lo elige el propio agente, así que él decide si lo revisan. Requiere reabrir ADR-0003 y cambiar la regla 4 de `AGENTS.md`. El motivo "operativo" ya está en el catálogo inicial (ADR-0011); falta confirmar con el área usuaria que ese motivo sea el que lleva a la autorrevisión (PA #21), porque hoy no tiene ninguna consecuencia. Preguntas para el MININTER si la eligen: (a) ¿la bitácora marca esas decisiones como "autorrevisión"? (b) ¿un revisor las ratifica después, como en la C? (c) ¿el supervisor ve cuántas veces usa cada agente el motivo "Operativo"? Es la única medida que permite detectar el abuso. (d) ¿solo ciertos agentes pueden elegir ese motivo? Esfuerzo (estimado de ARCH, `docs/arch/evaluaciones/PA-02-estimado-opciones.md`): la E siempre incluye la A completa, porque los demás motivos van al revisor. Sin medidas cuesta unos 2 días más que la A; con todas, unos 4 a 5 más, como la C. Solo la B cuesta menos que la A (unos 1,5 días menos).
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
32. El aviso simulado al 105 no estaba en el encargo: ¿el MININTER lo acepta en el prototipo y con qué redacción y datos (ubicación, nombre, código de requisitoria)? ¿Se envía la ubicación GPS del dispositivo (pide un permiso nuevo y es un dato personal del agente) o se ingresa a mano? Supuesto de trabajo: ubicación del dispositivo con permiso, mostrada solo en el celular. (HU-09)
33. Foto con varias personas: ¿la bitácora puede registrar que la foto tenía varios rostros (solo la cantidad, sin ningún dato de las otras personas), o no debe quedar ninguna huella de ellos? ¿Hay un máximo de rostros por foto (por ejemplo, una multitud) por encima del cual la captura se rechaza y se pide acercarse a una sola persona? **Supuesto de trabajo vigente (humano, 2026-11-20), hasta que responda el MININTER:** la bitácora registra solo la cantidad de rostros, sin datos de las otras personas; con más de 5 rostros la captura se rechaza y se pide acercarse a una sola persona. El celular recorta el rostro elegido y solo el recorte viaja (ADR-0015, opción A). (HU-05 E8 a E10)
34. Aviso simulado al 105: (a) en la coincidencia facial, ¿lo pulsa solo el agente que hizo la consulta o también el revisor que la confirmó? (b) ¿La ubicación se muestra como coordenadas o como dirección (una dirección requiere un servicio externo de geocodificación)? (c) ¿La ubicación se guarda en la bitácora o solo se muestra en el celular? (d) ¿Se puede registrar más de un aviso por la misma consulta? (e) Si la revisión llega horas después (PA #2, opción A), ¿la ubicación es la del momento en que se pulsa el aviso o la de la captura? **Supuesto de trabajo vigente (humano, 2026-11-20; ADR-0016), hasta que responda el MININTER:** (a) solo el agente que hizo la consulta, y en el caso facial tras la confirmación del revisor; (b) coordenadas, sin geocodificar; (c) la bitácora no guarda las coordenadas, solo si hubo ubicación; (d) un solo aviso por consulta; (e) la ubicación del momento en que se pulsa. (HU-09)
35. Consultas complementarias de placa (HU-10): ¿el MININTER acepta incluirlas en el prototipo? ¿Qué campos de SUNARP y del SAT puede ver el personal en campo, y es aceptable mostrar solo Lima para papeletas o debe simularse una fuente nacional (municipalidades, SUTRAN)? Supuesto de trabajo: solo datos del vehículo, sin propietario (relacionado con PA #15), y papeletas solo de Lima.
36. Consultas complementarias de placa (HU-10): (a) ¿se ofrecen también cuando la placa no está registrada en la fuente de requisitorias (PLA-08)? (b) ¿la marca "No coincide con lo registrado" debe decir qué característica no coincide (marca, modelo, color, año) o admitir un comentario? ¿Se puede deshacer? (c) ¿se puede repetir una consulta complementaria sobre la misma consulta de placa, y cada repetición queda en la bitácora? Mientras tanto, el prototipo muestra la variante mínima (no en PLA-08, marca sin detalle y sin deshacer, y el resultado ya consultado se vuelve a mostrar sin otra consulta), sin darla por decidida.
37. Stack del MININTER (informado el 2026-11-24, obligatorio en el MVP): Java 21, Angular 22+, Keycloak para la gestión de identidad, NGINX para publicar y Flutter para la app móvil. Esto reemplaza el supuesto del PA #17 de que el stack lo define el proveedor. ¿El MININTER acepta que la API, los simuladores y el motor biométrico sigan en Python (FastAPI, OpenCV con YuNet y SFace)? El motor va como un servicio interno aislado y reemplazable (por ejemplo, por un motor de RENIEC o uno propio). **Decisión del humano (2026-11-24), hasta que responda el MININTER:** la app móvil pasa de Expo a Flutter dentro del MVP. El humano negocia que la API se quede en Python. NGINX reemplaza a Caddy. ARCH evaluó el impacto (`docs/arch/evaluaciones/PA-37-39-stack-mininter.md`). **Decisiones del humano (2026-11-24, tras la evaluación):** (1) escenario 1, migrar ya: la app pasa a Flutter desde el 25-nov y HU-04 no se termina en Expo; (2) se aceptan los ADR-0017 (Flutter y ML Kit), 0018 (NGINX), 0019 (API, simuladores y motor en Python, con el motor como servicio interno aislado) y 0020 (Keycloak, ajustado a solo documentado); (3) de la rama `hu-04` se llevan a `main` solo los documentos, no el código Expo, y la rama se conserva como referencia; (4) el APK de la demo se descarga desde una ruta protegida del VPS, sin EAS; (5) las pruebas de la app pasan a `apps/movil/test/` e `apps/movil/integration_test/` (cambio de `AGENTS.md`, a cargo del humano o del LEAD). El 0019 sigue sujeto a que el MININTER acepte Python.
38. Keycloak (stack del MININTER): **En el MVP se entrega solo documentado, sin construir (decisión del humano, 2026-11-24, tras la evaluación de ARCH).** Se mantiene Supabase Auth (ADR-0003, ADR-0020). Los unos 3 días que costaba se usan para construir HU-09. El documento describe las dos variantes, sin suponer ninguna. ¿Usamos un Keycloak del MININTER o montamos uno propio en el ambiente del demo? ¿Los roles (agente, revisor, supervisor) se definen en Keycloak? (Relacionado con el PA #3.)
39. Angular 22+ (stack del MININTER): el MVP no tiene aplicación web. ¿El MININTER espera alguna pantalla web (por ejemplo, revisión de coincidencias, supervisión o consulta de la bitácora, PA #24), o solo informa su estándar para lo que se construya en web? Nada web entra al alcance hasta que se responda.
40. Fotos de referencia de las personas con requisitoria (2026-11-24): ¿Qué fotos de referencia existen de cada persona con requisitoria: cuántas, de qué fuente (DNI de RENIEC, ficha policial, requisitoria judicial), de qué antigüedad y con qué calidad (resolución, de frente)? ¿Se pueden usar fotos representativas de esas fuentes, anonimizadas o con autorización, para calibrar los umbrales antes de producción? Contexto: el MVP calibra con fotos del equipo con consentimiento (ADR-0004), así que esos umbrales no se pueden usar tal cual en producción. Con una sola foto de referencia, vieja o de baja calidad, habrá más resultados "No concluyente". **Ampliación (2026-11-25, decisión del humano):** ¿Se puede hacer una calibración real en el ambiente del MININTER, con sus fotos de referencia y su autorización, antes de pasar a producción? La calibración de la demo (5 personas, `docs/arch/evaluaciones/HU-05-plan-calibracion-demo.md`) solo da umbrales provisionales. ¿Se piensa usar fotos de redes sociales como referencia? Si es así, ¿con qué base legal (Ley 29733, finalidad y origen del dato)? El equipo no las da por buenas, por su calidad (filtros, ángulos, baja resolución) y por la base legal. Relacionado con los PA #4, #6 y #7. (HU-05, HU-06)

## Próximo paso

Historias de Usuario aprobadas el 2026-11-18 (`docs/hus/`); UX, diseño técnico y Sprint 0 completos. Siguiente (2026-11-19): UX construye el prototipo navegable para validarlo el 2026-12-01, y LEAD escribe los contratos de la iteración 1 (HU-08, HU-01, HU-02, HU-03, HU-07).

Histórico: entrega al Agente BA para iniciar Historias de Usuario. Los Puntos Abiertos deben quedar reflejados en cada HU afectada (en especial #2, #4, #7, #15, #16 y #17 en las HUs de biometría, placas y trazabilidad).
