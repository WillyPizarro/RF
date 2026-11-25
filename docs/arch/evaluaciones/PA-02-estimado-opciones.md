# Estimado: opciones B, C y E del PA #2 frente a la A

**Rol / fecha:** ARCH, 2026-11-24. Encargo del PM del 2026-11-24 (punto 2). **Es solo informativo:** el [ADR-0003](../adrs/0003-autenticacion-roles.md) no se reabre hasta que responda el MININTER.
**Fuente de las opciones:** PRD › PA #2 (opción E agregada en `ffaacfb`).
**Estimados:** del ARCH, en días de trabajo de un agente, sin contrato. Los valida el LEAD. Valen igual con Expo o con Flutter.

## Línea base: opción A (diseño actual, HU-06 sin construir)

Cola de pendientes del revisor, pantalla de comparación lado a lado, decisión con motivo (Confirmar, Descartar, No concluyente), borrado de la captura y su registro, vencimiento a 24 h (ADR-0008) y estado "Pendiente de revisión" para el agente.

**A = unos 4 a 5 días de DEV y 3 a 4 del TESTER, en paralelo: unos 5 días de calendario.**

## Diferencia de cada opción frente a la A

| Opción | Qué cambia en la construcción | DEV | TESTER | Otros roles | Calendario frente a la A |
|---|---|---|---|---|---|
| **B. El mismo agente revisa** | Sin cola ni rol revisor en el flujo facial. La pantalla de comparación se reutiliza en el flujo del agente, justo después del resultado. La captura se borra en minutos, no en horas. Se quita la regla "nadie revisa su propia consulta" | −1,5 | −1 | BA y UX: HU-05 y HU-06, 1 día cada uno. ARCH: reabrir el ADR-0003. Humano o LEAD: regla 4 de `AGENTS.md` | **Unos 1,5 días menos** |
| **C. Modo operativo con ratificación** | Todo lo de la A (la cola sirve para ratificar), más una HU nueva: el supervisor activa y cierra el modo (¿por agente, por zona, por horario?), el agente decide en campo con motivo, la bitácora marca "autorrevisión" y un revisor ratifica después | +3 a +4 | +2 a +3 | BA: HU nueva y escenario de ratificación (1 a 2). UX: pantallas de activar y cerrar el modo (1). ARCH: reabrir el ADR-0003 | **Unos 4 días más** |
| **E. Autorrevisión según el motivo, sin medidas** | Todo lo de la A (los demás motivos van al revisor), más el camino del motivo "Operativo": el agente ve la comparación y decide con motivo. El motivo ya es un catálogo cerrado que incluye "operativo" (ADR-0011; `GET /v1/motivos` en `services/api/app/placas.py`), así que no hay que crearlo; sí hay que decidir con el área usuaria si ese motivo del catálogo es el que activa la autorrevisión (PA #21) | +1,5 a +2 | +1 | BA y UX: medio día cada uno. ARCH: reabrir el ADR-0003. Humano o LEAD: regla 4 | **Unos 2 días más** |
| E + (a) la bitácora marca "autorrevisión" | Un valor más en el evento de la decisión | +0,25 | +0,25 | — | +0,5 |
| E + (b) un revisor ratifica después | Estado "por ratificar" en la cola de la A y pantalla de ratificación (reutiliza la de revisión). La captura se retiene hasta la ratificación o 24 h | +1,5 a +2 | +1 | UX: medio día | +2 |
| E + (c) el supervisor ve cuántas veces usa cada agente el motivo "Operativo" | Filtro por motivo en la bitácora (HU-07) y un conteo por agente | +0,5 a +1 | +0,5 | UX: medio día | +1 |
| E + (d) solo ciertos agentes pueden elegir "Operativo" | Un atributo en la carga de usuarios (ADR-0003), control en la API y lista de motivos según el usuario | +0,5 | +0,5 | — | +0,5 |
| **E con todas las medidas** | — | +4 a +5 | +3 | — | **Unos 4 a 5 días más (como la C)** |
| D. Revisor central en tiempo real | No se estima: depende de personal y procesos del MININTER. Técnicamente es la A con un tiempo de respuesta en minutos y quizá notificaciones push (brecha 9) | — | — | — | — |

## Precisión para el PRD (para el PM)

El PRD dice que la E "sin ratificación, el esfuerzo se parece al de la B; con ratificación, queda entre la B y la C". **Desde la construcción no es así:** la E siempre incluye la A completa, porque con cualquier motivo que no sea "Operativo" la consulta va al revisor. Por eso:

- La **B** es la única opción **más barata** que la A: elimina la cola.
- La **E sin medidas** cuesta **más que la A** (unos 2 días), y la **E con ratificación** se parece a la **C** (unos 4 días más que la A).

Lo que sí es cierto es que la E no necesita la pantalla para activar un modo, que es lo que encarece la C.

Además, el PRD dice que la E obliga a "agregar el motivo 'Operativo' a la lista (PA #21)". Ese motivo **ya está** en el catálogo inicial del ADR-0011 ("control vehicular, intervención policial, denuncia, operativo"). Lo que falta es otra cosa: confirmar con el área usuaria que ese motivo del catálogo sea el que lleva a la autorrevisión, porque hoy cualquier agente lo elige en una consulta de placa sin ninguna consecuencia.

## Riesgos técnicos que conviene que el MININTER conozca (no cambian el ADR-0003)

- En B y en E, quien consulta decide su propia coincidencia. El control contra falsos positivos pasa a ser el criterio del agente, con sesgo de confirmación en operativo. La bitácora lo deja registrado, pero no lo evita.
- En E, el agente elige el motivo y con eso decide si lo revisan. La medida (c), el conteo por agente, es la única que permite detectar el abuso.
- En B y en E, la captura de un candidato se borra en minutos en vez de esperar hasta 24 h, lo que reduce el riesgo principal de la evaluación de impacto (TECH-DESIGN › Riesgos).
