# Wireframes — HU-09: Avisar al 105 (simulado)

> **Estado: aprobado por el humano el 2026-11-20 (vía PM)**, junto con HU-09 y la propuesta de UX: vista previa con confirmación, fecha y hora en el mensaje, tarjeta "SIMULACIÓN" con "No incluye fotos", precisión y hora de la ubicación, y AVI-03. Base: `docs/hus/HU-09-aviso-simulado-105.md` (BA, `4b2f009` y `0f96761`, escenarios E1 a E7) y ADR-0016. Supuestos de trabajo del humano del 2026-11-20, hasta que responda el MININTER, para PA 34: a) solo el agente que hizo la consulta; b) coordenadas sin geocodificar; c) la bitácora guarda solo si la ubicación estaba disponible, sin coordenadas; d) un solo aviso por consulta; e) ubicación leída al pulsar. **No se desarrolla** hasta nueva orden del PM (sin contrato, código ni pruebas).

## Proyecto / herramienta
- Herramienta: texto estructurado + prototipo local `../prototipo/index.html`.
- Canal/formato: app móvil Android (referencia, ADR-0010), vertical. Todo ocurre dentro del mismo celular.

## Pantallas

| # | Pantalla / Estado | Escenario Gherkin (HU-09) | ID |
|---|---|---|---|
| 1 | Botón "Avisar al 105 (simulado)" en el resultado de placa con requisitoria | E1 (Dado / Cuando) | PLA-05 (cambio) |
| 2 | Botón en el detalle de una verificación confirmada por el revisor | E2 (Dado / Cuando) | VER-02 (cambio) |
| 3 | Permiso de ubicación del sistema (la primera vez) | E1 a E3 (antes de la vista previa) | AVI-00 |
| 4 | Vista previa del mensaje, con ubicación | E1 y E2 (Entonces) | AVI-01 |
| 5 | Vista previa del mensaje, sin permiso de ubicación | E3 | AVI-01 · sin ubicación |
| 6 | Aviso simulado registrado | E1 a E3 (registro en la bitácora) | AVI-02 |
| 7 | No se pudo registrar el aviso | Regla 7 (error ≠ resultado) | AVI-03 |
| 8 | Resultados sin el botón | E4 | PLA-06/07/08, ROS-05 a ROS-08, VER-02 (pendiente, descartada, no concluyente, vencida) |
| 9 | Cancelar en la vista previa | E5 | AVI-01 → vuelve al resultado |
| 10 | Aviso ya registrado para esa consulta | E6 (un aviso por consulta) | PLA-05 / VER-02 · aviso registrado |
| 11 | Solo el agente que consultó ve el botón | E7 | VER-02 (el revisor no tiene el botón en REV-02 ni en REV-04) |

### PLA-05 — Placa con requisitoria (se agrega un botón)
```
│ ┌──────────────────────────┐ │
│ │ RESULTADO DE LA CONSULTA │ │
│ │ ABC-123                  │ │
│ │ TIENE REQUISITORIA       │ │  ← rojo, sin cambios
│ └──────────────────────────┘ │
│ Motivo / Consultado          │
│                              │
│ [ AVISAR AL 105 (SIMULADO) ] │  ← secundario (borde), no rojo
│ [     NUEVA CONSULTA      ]  │
```

### VER-02 — Verificación confirmada por el revisor (se agrega un botón)
```
│ V-0005 · 20/11/2026 14:02    │
│ Resultado inicial            │
│ Posible coincidencia —       │
│ requiere revisión            │
│ ──────────────────────────── │
│ Revisión: coincidencia       │
│ confirmada por el revisor    │
│                    [PA 28]   │
│ [ AVISAR AL 105 (SIMULADO) ] │  ← solo si la decisión es "Confirmar"
```
- Solo lo ve el agente que hizo la consulta (E7, PA 34 a). El revisor no tiene el botón.
- No aparece en ROS-05 (pendiente de revisión) ni en VER-02 pendiente, descartada, no concluyente o vencida (E4, regla 4).

### AVI-00 — Permiso de ubicación (diálogo del sistema, solo la primera vez)
```
│ ┌──────────────────────────┐ │
│ │ ¿Permitir que Movil      │ │
│ │ Buscador acceda a la     │ │
│ │ ubicación del            │ │
│ │ dispositivo?             │ │
│ │ [Mientras se usa la app] │ │
│ │ [Solo esta vez]          │ │
│ │ [No permitir]            │ │
│ └──────────────────────────┘ │
```
- Lo muestra Android al tocar "Avisar al 105 (simulado)", no al iniciar la app: el permiso se pide en el momento en que se usa.
- Texto de propósito propuesto (para `app.json`): "Movil Buscador usa la ubicación solo para mostrarla en el aviso simulado al 105. No se envía a ninguna central."
- Si se niega, se sigue a AVI-01 · sin ubicación (E3). No se vuelve a insistir en la misma consulta.

### AVI-01 — Vista previa del mensaje
```
┌──────────────────────────────┐
│ DATOS SINTÉTICOS · PROTOTIPO │
│ ✕  Aviso al 105 (simulado)   │
├──────────────────────────────┤
│ ┌──────────────────────────┐ │
│ │ ⓘ SIMULACIÓN             │ │  ← info (azul), no rojo
│ │ Esto no llama ni envía   │ │
│ │ nada al 105 ni a ninguna │ │
│ │ central. Solo se muestra │ │
│ │ en este celular.         │ │
│ └──────────────────────────┘ │
│ Mensaje que se enviaría      │
│ ┌──────────────────────────┐ │
│ │ Ubicación del dispositivo│ │
│ │ -12.04637, -77.04279     │ │
│ │ (± 15 m) · 14:32 [PA 34b]│ │
│ │ Placa: ABC-123           │ │  ← caso placa
│ │ Código de requisitoria:  │ │
│ │ REQ-SINT-0001  [PA 15]   │ │
│ │ ID de la consulta: C-0118│ │
│ │ Fecha y hora: 20/11 14:32│ │
│ │ No incluye fotos.        │ │
│ └──────────────────────────┘ │
│ [ REGISTRAR AVISO SIMULADO ] │
│ [ Cancelar ]                 │
└──────────────────────────────┘
```
Caso facial (E2): el bloque cambia a
```
│ │ Código de requisitoria:  │ │
│ │ REQ-SINT-0007            │ │
│ │ Persona: Nombre Sintético│ │
│ │ Cinco                    │ │
│ │ Posible coincidencia —   │ │  ← redacción fija, aunque el
│ │ requiere revisión        │ │     revisor haya confirmado
│ │ ID de la consulta: V-0005│ │
```
- **Nunca** la captura ni la foto de referencia (no hay ninguna imagen en la pantalla), ni la palabra prohibida.
- Para la placa no se muestra nombre de persona (supuesto de la HU).
- Mientras se obtiene la ubicación, el bloque dice "Obteniendo ubicación…" y "Registrar aviso simulado" queda desactivado. Si el GPS está apagado o no responde a tiempo, pasa a "Ubicación no disponible.", nunca a una ubicación anterior.
- La ubicación se lee **al pulsar** el aviso (PA 34 e), no al capturar; se muestra en coordenadas con su precisión, sin dirección (PA 34 b, ADR-0016).

### AVI-01 · sin ubicación (E3)
```
│ │ Ubicación del dispositivo│ │
│ │ Ubicación no disponible: │ │  ← sin permiso
│ │ la app no tiene permiso  │ │
│ │ de ubicación.            │ │
│ │ Placa: ABC-123 …         │ │  ← el resto, igual
```
- Con el GPS apagado o sin respuesta a tiempo dice solo "Ubicación no disponible." La causa se indica solo cuando es la falta de permiso.
- Sin coordenadas aproximadas, anteriores ni inventadas. Sin campo para escribir la ubicación a mano (PA 32 abierto).
- Se puede registrar igual (E3).

### AVI-02 — Aviso simulado registrado
```
│            ✓                 │
│ Aviso simulado registrado    │
│ No se envió nada a ninguna   │
│ central. Quedó en la         │
│ bitácora.                    │
│ C-0118 · 14:33               │
│  [ VOLVER AL RESULTADO ]     │
```
- Al volver, el botón del resultado muestra "Aviso simulado registrado · 14:33", desactivado (E6: un solo aviso por consulta, PA 34 d). Al volver a abrir esa consulta se ve igual.

### AVI-03 — No se pudo registrar
```
│            ⚠                 │
│ No se pudo registrar el      │
│ aviso simulado; intente      │
│ nuevamente.                  │
│ [ REINTENTAR ]  [ Volver ]   │
```
- Nunca dice que se registró (regla 7). Gris, como los demás errores.

## Reglas de pantalla
- **Nunca automático:** el aviso solo existe tras dos toques del usuario ("Avisar al 105 (simulado)" y "Registrar aviso simulado"). La vista previa no registra nada; "Cancelar", "✕" y Atrás tampoco (E5).
- **Solo dos entradas:** PLA-05 y VER-02 con decisión "Confirmar" (E4).
- **Simulación evidente:** el título lleva "(simulado)" y la tarjeta "SIMULACIÓN" está siempre arriba. No se usa rojo ni sirena, para que no parezca una alarma real.
- **Bitácora:** un evento "Aviso simulado al 105" con usuario, fecha, hora, ID de la consulta y "Ubicación disponible: sí/no". **Las coordenadas no se guardan** (PA 34 c, ADR-0016).
- **Accesibilidad:** el foco va al título; la tarjeta "SIMULACIÓN" se lee antes que el mensaje; los botones miden al menos 48 × 48.

## Decisiones de diseño aplicadas
- Vista previa + "Registrar aviso simulado" (paso de confirmación) y la fecha y hora en el mensaje: propuesta de UX **aprobada por el humano el 2026-11-20**.
- Coordenadas con precisión y hora de la lectura, sin dirección (PA 34 b, ADR-0016).
- La ubicación es la del momento en que se pulsa el aviso (PA 34 e).
- El permiso de ubicación se pide la primera vez que se pulsa el aviso, no al iniciar la app.

## Elementos no solicitados (todos aprobados por el humano el 2026-11-20)
1. Paso de confirmación AVI-01 → "Registrar aviso simulado".
2. Fecha y hora dentro del mensaje.
3. Tarjeta "SIMULACIÓN" y la línea "No incluye fotos."
4. Precisión (± m) y hora de la lectura de la ubicación.
5. AVI-03 (error al registrar; aplica la regla 7).

El estado "Aviso simulado registrado · hh:mm" ya no está en esta lista: lo pide HU-09 E6.

## Puntos abiertos que afectan el diseño
- PA 32: aceptación del MININTER, redacción y datos; GPS o ubicación escrita a mano (supuesto: GPS del dispositivo con permiso).
- PA 34 a–e: resueltos como supuestos de trabajo del humano (ver "Estado"). Siguen abiertos ante el MININTER; si cambian, cambian el botón de VER-02 (a), el bloque de ubicación (b, e), el evento de la bitácora (c) o el estado del botón tras registrar (d).
- PA 15: el código de requisitoria y el nombre aparecen aquí aunque el resultado no los muestre.
- PA 28: redacción de la coincidencia confirmada.

## Fuera de alcance respetado
- Ninguna llamada, SMS, notificación ni envío de red a una central; ninguna "app del 105".
- Ninguna foto en el mensaje.
- Ningún aviso antes de la revisión humana en el caso facial.
