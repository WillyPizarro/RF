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
