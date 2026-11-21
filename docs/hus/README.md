# Historias de Usuario — Movil Buscador (MININTER)

Fuente: `PRD.md` (2026-11-18). Rol: BA. Skill: `escribir-hus`. Estado: **aprobado por el usuario el 2026-11-18**.

## Índice

| HU | Título | Actor | Módulo del PRD |
|---|---|---|---|
| [HU-01](HU-01-iniciar-sesion.md) | Iniciar sesión y mantener una sesión segura | Usuario en campo | Seguridad y acceso |
| [HU-02](HU-02-acceso-por-rol.md) | Acceder solo a las funciones de mi rol | Responsable del servicio | Seguridad y acceso |
| [HU-03](HU-03-consultar-placa.md) | Consultar si una placa tiene requisitoria | Usuario en campo | Consulta de placas |
| [HU-04](HU-04-capturar-placa-ocr.md) | Capturar la placa con la cámara | Usuario en campo | Consulta de placas |
| [HU-05](HU-05-verificar-rostro.md) | Verificar un rostro y recibir posibles coincidencias | Usuario en campo | Verificación biométrica |
| [HU-06](HU-06-revisar-coincidencia.md) | Revisar una posible coincidencia facial | Revisor humano | Verificación biométrica |
| [HU-07](HU-07-bitacora-consultas.md) | Registrar cada consulta en una bitácora | Responsable del servicio | Trazabilidad |
| [HU-08](HU-08-simuladores-fuentes.md) | Consultar fuentes a través de servicios con simuladores | Área técnica | Servicios e interoperabilidad |
| [HU-09](HU-09-aviso-simulado-105.md) | Avisar al 105 (simulado) tras una placa con requisitoria o una coincidencia confirmada | Usuario en campo | Aviso simulado al 105 (decisión del 2026-11-20) |
| [HU-10](HU-10-consultas-complementarias-placa.md) | Consultar datos del vehículo y papeletas de una placa (simulado) | Usuario en campo | Consultas complementarias de placa (decisión del 2026-11-20) |

## Decisiones de redacción

- **Las HUs cubren las funcionalidades del Componente 2.** Los entregables del Componente 1 (diagnóstico, matriz de fuentes, arquitectura, documentos OSIGP-FR), las pruebas, la evaluación biométrica y el despliegue son entregables, no funcionalidades de usuario: se gestionan en el plan, no como HUs.
- **Reglas transversales como escenarios borde**, no como HUs aparte:
  - Motivo de consulta obligatorio → HU-03, HU-05.
  - Gestión de errores → HU-03, HU-04, HU-08 (y registro en HU-07).
  - Registro en bitácora → HU-01, HU-02, HU-03, HU-05, HU-06.
  - Lenguaje prudente ("posible coincidencia", nunca "identificado") → HU-05, HU-06.
- **Consulta de placa dividida en dos HUs** (manual y por cámara): son dos capacidades distintas que se construyen y prueban por separado; HU-04 termina entregando la placa confirmada al flujo de HU-03.
- Gherkin en español (`# language: es`).

## Conflictos del PRD (documentados, no resueltos)

| # | Conflicto | Qué se hace mientras tanto | Qué falta confirmar |
|---|---|---|---|
| C1 | El PRD implica un "Administrador de accesos" ("control de acceso por roles") pero no lo describe | HU-02 asigna roles en la carga inicial de datos sintéticos; no se construye pantalla de administración | PA #3 y #9 |
| C2 | El revisor humano puede ser el mismo usuario en campo u otro rol | HU-06 se escribe como actor separado; si es el mismo, se fusiona con HU-05 | PA #2 |
| C3 | "Integración con las fuentes autorizadas" está en Incluye, pero el MVP excluye la integración real | HU-08 construye servicios con contrato y simuladores, preparados para conectar la fuente real después | PA #6 y #17 |
| C4 | Los criterios de éxito no tienen umbrales medibles | Los escenarios hablan de "umbral definido" sin fijar valores | PA #4 |
| C5 | El aviso simulado al 105 muestra el código de requisitoria y el nombre sintético, pero el PA #15 no decidió qué datos muestra el resultado | HU-09 los incluye porque la decisión del 2026-11-20 los nombra; con datos sintéticos no hay riesgo | PA #15 y #32 |
| C7 | HU-10 muestra datos del vehículo (SUNARP) a pedido, pero el PA #15 no decidió si el resultado de placa muestra algo más que "con/sin requisitoria" | Solo a pedido y nunca datos del propietario (decisión del 2026-11-20) | PA #15 y #35 |
| C6 | La foto con varias personas (2026-11-20) contradice ADR-0002 y ADR-0004, que exigen "un solo rostro" en el dispositivo y en el servidor | HU-05 E2 deja de rechazar por varios rostros; ARCH debe actualizar los ADR | Nada de negocio: es tarea de ARCH |

## Puntos abiertos nuevos (surgidos al escribir las HUs)

Agregados al PRD como Puntos Abiertos #18 a #24:

1. ¿Cuál es el tiempo máximo de inactividad antes de cerrar la sesión? (HU-01)
2. ¿Cuántos intentos fallidos se permiten antes de bloquear la cuenta, y por cuánto tiempo? (HU-01)
3. ¿Qué formatos de placa debe aceptar la validación (particulares, motos, antiguas, diplomáticas, temporales)? (HU-03)
4. ¿El motivo de consulta es texto libre o una lista cerrada? Si es lista, ¿cuáles? (HU-03, HU-05)
5. ¿Cuántos candidatos como máximo se muestran en una posible coincidencia? (HU-05)
6. ¿Qué pasa si una coincidencia no se revisa en un tiempo determinado? (HU-06)
7. ¿Quién consulta la bitácora, desde dónde y con qué filtros? (HU-07)

## Fuera de alcance respetado

- Identificación masiva y vigilancia indiscriminada: excluidas explícitamente en HU-04 y HU-05.
- Integración con fuentes reales y políticas de seguridad avanzadas: excluidas del MVP en HU-01, HU-02, HU-03, HU-05, HU-07 y HU-08.

## Próximo paso

1. ~~Aprobación humana~~ (hecho).
2. ~~Agregar puntos abiertos al PRD~~ (hecho, #18 a #24).
3. Entregadas a UX (prototipo navegable) y ARCH (diseño técnico).

## Cambios tras la revisión de UX (aprobados por el usuario el 2026-11-18)

- HU-03: nuevo Escenario 5 "Sin requisitoria registrada en la fuente consultada" (el flujo lo necesitaba y no tenía escenario).
- HU-05: nuevo Escenario 5 "Error del servicio de comparación" (la gestión de errores es transversal).
- PRD: nuevos Puntos Abiertos #25 a #28 (aviso a la persona fotografiada, score al revisor, motivo del revisor visible, redacción de coincidencia confirmada).

También aprobados los 8 elementos no solicitados por las HUs que propuso UX (`docs/ux/README.md` → "Elementos no solicitados").

## Cambios tras la entrega de ARCH (2026-11-18)

- HU-05 y HU-06: la regla de borrado de la captura queda precisada por ADR-0008 (se borra tras comparar o tras la revisión, máximo 24 h).
- HU-06: supuestos provisionales de ADR-0003 (revisor distinto del agente; PA #2) y ADR-0008 (revisión vencida a las 24 h; PA #23).
- HU-01 Escenario 4 (cuenta bloqueada, provisional PA #19) y HU-06 Escenario 4 (revisión vencida, provisional PA #23): aprobados por el usuario el 2026-11-18.
- PRD PA #2: se agregan las opciones A a D (revisor separado, mismo agente, autorrevisión en modo operativo con ratificación, central en tiempo real) para decisión del MININTER.

## Cambios tras el escalado de UX (aprobados por el usuario el 2026-11-19)

- HU-05: nuevos Escenarios 6 (permiso de cámara denegado) y 7 (permiso retirado antes de capturar). OCR-04 solo cubría la placa (HU-04 E3). Sin captura no hay comparación, no se muestra ningún resultado facial y nada se registra como comparación.
- HU-05 y PRD: Puntos Abiertos #29 y #30: si el intento sin captura se registra en la bitácora (y con qué datos), y si el motivo se conserva al volver de los ajustes.

## Cambios por las decisiones del humano del 2026-11-20 (aprobados por el humano el 2026-11-20)

Aprobados HU-05 E8 y E9, HU-09 y la propuesta de UX (vista previa con confirmación y fecha y hora en el aviso). Siguen **sin desarrollo** (sin contrato, código ni pruebas) hasta que el PM lo autorice.

- HU-05: el Escenario 2 ya no rechaza una foto por tener varios rostros. Nuevos Escenarios 8 (el usuario elige un solo rostro; solo ese se compara y se conserva) y 9 (sale sin elegir: no se compara nada y la foto se descarta). PRD PA #33.
- HU-09 nueva: aviso simulado al 105. Cinco escenarios: placa, coincidencia confirmada, sin permiso de ubicación, resultados que no lo habilitan, cancelar en la vista previa. PRD PA #32 (propagado) y #34.
- Pantallas coordinadas con UX: ROS-10 "Elija un rostro"; botón en PLA-05 y VER-02; AVI-01 (vista previa) y AVI-02 (confirmación). La vista previa con confirmación y la fecha y hora en el mensaje son propuestas de UX, no pedidas por el PRD; aprobadas el 2026-11-20.
- Conflictos C5 y C6.

### Supuestos de trabajo del humano (2026-11-20), vigentes hasta que responda el MININTER

- PA #33: la bitácora registra solo la cantidad de rostros; con más de 5 rostros se rechaza la captura (HU-05 E10 nuevo). ADR-0015 opción A: solo viaja el recorte del rostro elegido.
- PA #34 (ADR-0016): solo el agente que hizo la consulta; coordenadas sin geocodificar; sin coordenadas en la bitácora; un aviso por consulta; ubicación al pulsar (HU-09 E6 y E7 nuevos).
- Siguen sin desarrollo hasta que el PM lo autorice.
- Detalles de UX del aviso aprobados por el humano (2026-11-20): tarjeta "SIMULACIÓN" con "No incluye fotos.", precisión y hora de la lectura, y AVI-03 (error al registrar), que pasa a ser HU-09 E8.

## HU-10 consultas complementarias de placa (decisión del humano, 2026-11-20; pendiente de aprobación)

- HU-10 nueva, siete escenarios: datos del vehículo sin el propietario, papeletas solo de Lima, cero papeletas ("Sin papeletas pendientes registradas en SAT Lima"), error de la fuente (nunca "sin papeletas"), la marca "No coincide con lo registrado" (nunca "placa clonada"), nada automático, y la placa no registrada en SUNARP (propuesta de UX).
- PRD: PA #35 (del PM) propagado y PA #36 nuevo (PLA-08, detalle de la marca y si se puede deshacer, repetición de la consulta). Conflicto C7 con el PA #15.
- Pantallas coordinadas con UX: sección en PLA-05 y PLA-06, COM-01 a COM-05. Pendientes de aprobación: la confirmación previa de la marca (COM-03) y el estado "Placa no registrada en SUNARP (simulado)".
- OSIGP: RU009 / RF013. Sin desarrollo hasta que el PM lo autorice.
