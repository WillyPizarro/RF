# ENTREGA ARCH — 2026-11-18

**Qué se entrega:** [`TECH-DESIGN.md`](TECH-DESIGN.md) y 14 ADRs en [`adrs/`](adrs/), aprobados por el usuario el 2026-11-18.

**Contexto:** MVP móvil para el MININTER (consulta de placas y verificación facial con requisitoria), con datos sintéticos y simuladores, en un plazo de 30 a 40 días.

## Decisiones clave que acotan el trabajo de los demás

- La app (Expo dev build, Android) **solo habla con la API FastAPI**, incluido el login. Nunca habla con Supabase ni con los simuladores (ADR-0001, ADR-0003).
- Tres roles: `agente`, `revisor` y `supervisor`. Los usuarios se crean con un script de carga y no hay pantalla de administración (ADR-0003).
- Biometría: **lista acotada**, como máximo 3 candidatos, bandas `candidato`, `no_concluyente`, `sin_coincidencia` y `captura_rechazada`, y umbrales calibrados con FMR ≤ 0,1 % y FNMR ≤ 5 %. "Identificado" no existe en ninguna parte (ADR-0004).
- Bitácora de solo inserción (permisos y trigger) y **fail-closed**: sin registro no hay resultado. El supervisor la consulta desde la app (ADR-0005).
- Simuladores como servicio HTTP con contratos OpenAPI en `contratos/fuentes/`. El contrato entre la app y la API es el OpenAPI generado por FastAPI (ADR-0006, ADR-0007).
- La app es solo en línea y no guarda nada en el dispositivo salvo el token (ADR-0010, ADR-0013).
- Valores provisionales: sesión de 10 min, bloqueo tras 5 intentos por 15 min, placa con p95 ≤ 2 s, rostro con p95 ≤ 5 s, OCR ≥ 90 %, motivo de catálogo más "Otro" (ADR-0011).

## Cambios que afectan documentos de otros roles

- **BA / PM: la regla de negocio 3 queda precisada** (ADR-0008). La captura facial se borra tras la comparación **o tras la revisión humana**: si el resultado es candidato, se retiene cifrada hasta la decisión o un máximo de 24 h, para cumplir HU-06 E1 (revisión lado a lado). Hay que alinear HU-05 (supuestos) y el PRD.
- **BA:** el revisor se modela como un rol distinto del agente, y un agente no puede decidir sobre su propia consulta. Si el PA #2 responde lo contrario, hay que volver a abrir el ADR-0003.
- **BA / PM:** la respuesta provisional al PA #23 es que, a las 24 h sin revisión, la revisión pasa a "vencida" y el agente ve "No concluyente". Respuestas de diseño provisionales: PA #7 (lista acotada), PA #11 (solo en línea), PA #12 (Android), PA #21 (catálogo más "Otro") y PA #22 (máximo 3 candidatos). Faltan confirmar con el MININTER.
- **UX:** las pantallas por rol son agente (placa, rostro, estado de la consulta), revisor (cola y vista lado a lado con motivo obligatorio) y supervisor (bitácora con filtros). Hay que mostrar los textos exactos de las bandas y el formato de placa esperado en el error.
- **PM:** el consentimiento firmado ampliado de las fotos del equipo (nube del proveedor, evaluación y borrado al cierre) debe estar listo **antes del día 6**. Hay un costo mensual de VPS (alrededor de US$ 6–12) que no estaba en "herramientas gratuitas".

## Puntos abiertos que pueden bloquear o hacer rehacer trabajo

- **PA #17 / #8 (bloqueante):** aceptación escrita de la propuesta (stack e infraestructura del proveedor, simuladores, entrega con compose).
- PA #7 (1:1 frente a lista), PA #2 (quién revisa), PA #6 (fuentes y campos reales), PA #4 (metas definitivas), PA #16 (retención en producción) y PA #20 (formatos de placa: la expresión regular está **NO VERIFICADA**).
- Licencias de YuNet y SFace sin verificar contra opencv_zoo (Sprint 0).
- ~~Diagramas C4 y de secuencia pendientes~~: **entregados el 2026-11-18** en [`diagramas/`](diagramas/) y enlazados desde la sección "Diagramas" del TDD. Falta la revisión automática en el navegador (Chrome no se conecta desde el entorno) y una revisión visual.
