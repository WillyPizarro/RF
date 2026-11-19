---
name: datos-personales-peru
description: Checklist documental de protección de datos personales bajo la normativa peruana (Ley N.º 29733 y su reglamento) aplicada a un sistema con datos sensibles como biometría facial, placas y requisitorias - produce la sección de protección de datos del diseño, la matriz de tratamiento, la política de retención y eliminación y la lista de brechas para producción, sin asesoría legal. Use when the ARCH, PM or BA documents personal-data controls, retention, consent, purpose limitation or security measures for a Peruvian public-sector system, or when asked about Ley 29733, datos sensibles, biometría y privacidad, or how to document privacy for the MVP.
type: skill
tags: [privacidad, datos-personales, peru, ley-29733, biometria, documentacion]
---

# Protección de datos personales — Perú

## Goal

Dejar **documentado** cómo el sistema cumple (o cumpliría en producción) la normativa peruana de
protección de datos personales, con foco en datos sensibles. En el MVP la mayoría de controles se
documentan y solo los mínimos se implementan (ver enfoque MVP del proyecto).

> **Aviso:** esta skill organiza el trabajo documental; **no es asesoría legal**. Toda cita
> normativa se marca "a validar" y la revisa el área legal del cliente antes de entregarse. Antes
> de citar artículos o el reglamento, verificar la versión vigente en fuentes oficiales
> (El Peruano, portal del MINJUSDH / Autoridad Nacional de Protección de Datos Personales).

## Marco de referencia (verificar vigencia)

- **Ley N.º 29733**, Ley de Protección de Datos Personales.
- **Reglamento vigente** de la Ley 29733 (verificar número y fecha del decreto supremo vigente).
- **Autoridad Nacional de Protección de Datos Personales (ANPD)**, adscrita al MINJUSDH.
- Normativa de seguridad de la información aplicable a entidades públicas (verificar con el
  cliente cuál exige: p. ej. NTP-ISO/IEC 27001 y lineamientos de gobierno y confianza digital).

Conceptos clave a aplicar:
- Los **datos biométricos** que identifican a una persona son **datos sensibles**.
- Principios: legalidad, consentimiento, finalidad, proporcionalidad, calidad, seguridad,
  disposición de recurso y nivel de protección adecuado.
- Una entidad pública puede tratar datos sin consentimiento cuando es necesario para sus
  funciones legales — **la base legal concreta la confirma el área legal**, no se asume.

## Proceso

1. **Inventario de datos** — listar cada dato que el sistema toca, de dónde viene y si es
   sintético o real. Clasificar: identificativo, sensible (biometría), vinculado a requisitoria,
   técnico (bitácora, dispositivo).
2. **Matriz de tratamiento** — una fila por tratamiento (ver plantilla).
3. **Retención y eliminación** — cuánto vive cada dato y quién autoriza borrarlo. Lo que no se
   necesita conservar se borra al terminar la operación (p. ej. la captura facial).
4. **Medidas de seguridad** — separar *implementadas en el MVP* de *documentadas para producción*.
5. **Derechos del titular** — cómo se atenderían acceso, rectificación, cancelación y oposición
   (ARCO) en producción; en el MVP, declarar que no hay titulares reales.
6. **Brechas para producción** — lista explícita de lo que falta para operar con datos reales.
7. **Puntos abiertos** — toda decisión legal no confirmada va como pregunta exacta al cliente,
   nunca como supuesto.

## Plantilla — Matriz de tratamiento

| Dato | Categoría | Finalidad | Base legal (a validar) | Origen | Dónde se guarda | Retención | Quién accede | MVP |
|---|---|---|---|---|---|---|---|---|
| Captura facial | Sensible | Verificar contra lista acotada | Función de la entidad | Cámara del móvil | No se guarda | Se borra tras comparar | Nadie | Sintético/consentido |
| Galería de referencia | Sensible | Comparación | ... | Fuente autorizada | ... | ... | Servicio de comparación | Sintético |
| Placa consultada | Identificativo indirecto | Verificar requisitoria | ... | Ingreso/OCR | Bitácora | ... | Agente, auditor | Sintético |
| Bitácora | Técnico + personal | Trazabilidad y auditoría | ... | Sistema | Backend | ... | Auditor | Sintético |

## Controles: MVP vs. producción

| Control | MVP (implementado) | Producción (documentado) |
|---|---|---|
| Autenticación y roles | Usuario/clave, 2–3 roles | Identidad institucional, MFA |
| Bitácora | Solo inserción, con motivo | Inalterable, firmada, retención legal |
| Cifrado en tránsito | HTTPS | HTTPS + certificados gestionados |
| Cifrado en reposo | El que da el proveedor de nube | Gestión de llaves de la entidad |
| Minimización | Captura facial no se guarda | Ídem + revisión periódica |
| Dispositivo | No guardar fotos en el móvil | MDM, borrado remoto |
| Evaluación de impacto | Documento borrador | Evaluación formal aprobada |
| Registro del banco de datos | No aplica (sintético) | Inscripción ante la ANPD si corresponde |

## Entregables que produce

- Sección "Protección de datos personales" del documento técnico.
- Matriz de tratamiento.
- Política de retención y eliminación.
- Borrador de evaluación de impacto (con la biometría como riesgo principal).
- Lista de brechas para producción.

## Checklist

- [ ] Cada dato del sistema está en la matriz, con categoría y retención
- [ ] La biometría está tratada como dato sensible en todo el documento
- [ ] Toda cita legal dice "a validar" y la fuente oficial fue verificada o queda como punto abierto
- [ ] Queda claro qué está implementado en el MVP y qué solo documentado
- [ ] El MVP declara que usa solo datos sintéticos o consentidos por escrito
- [ ] Las brechas para producción están listadas
- [ ] No hay ninguna conclusión legal presentada como certeza sin revisión del área legal
