# ADR 0015: Foto con varias personas: se compara solo el rostro elegido, recortado en el dispositivo

## Estado

**Propuesto (2026-11-21).** Espera la aprobación del humano (vía PM). Resuelve el conflicto **C6** (`docs/hus/README.md`). Si se aprueba, **precisa** el ADR-0002 (calidad facial en el dispositivo) y el punto 3 del ADR-0004 (calidad en dos pasos). No cambia el resto de esos ADRs ni el ADR-0008.

Es solo documental. HU-05 E8 y E9 **no se desarrollan** hasta que el PM lo autorice.

## Contexto

- **Decisión del humano (2026-11-20, PRD › Alcance › Componente 2 › Foto con varias personas):** "la app marca los rostros detectados y el usuario elige **uno solo**, con su motivo de consulta. Solo ese rostro se compara; los demás no se comparan, no se guardan ni se registran. No es identificación masiva: sigue siendo una consulta por persona".
- HU-05 E8 y E9 (BA, `4b2f009`): E8 deja de rechazar por "más de un rostro". En E9 el usuario sale sin elegir y la foto se descarta. Notas del BA: "una sola comparación por foto"; lo que se conserva para el revisor (ADR-0008) es "solo el rostro elegido, no la foto completa"; y "cómo se recorta lo decide ARCH".
- **Conflicto C6:** el ADR-0002 (Contexto, HU-05 E2) y el punto 3 del ADR-0004 piden "un solo rostro" en el dispositivo (ML Kit) y "exactamente un rostro" en el servidor (YuNet).
- Regla de negocio 6 (`AGENTS.md`): sin identificación masiva. Regla 5 y ADR-0008: la captura se borra tras comparar, o tras la revisión si hay un candidato.
- ML Kit Face Detection ya está en el ADR-0002 y devuelve **un recuadro por cada rostro** detectado. Según los términos de ML Kit, no envía la imagen ni sus resultados (ADR-0002 en la rama `hu-04`, commit `decf3be`).
- Pedido del PM: evaluar YuNet para detectar varios rostros. YOLO queda descartado porque detecta personas, no reconoce identidad, y Ultralytics se distribuye con licencia AGPL-3.0.
- PRD PA #33 (abierto): ¿la bitácora puede registrar cuántos rostros tenía la foto? ¿Hay un máximo de rostros por foto?

## Decisión propuesta

1. **Detección y elección en el dispositivo.** ML Kit Face Detection marca todos los rostros de la foto, y el usuario toca **uno solo** (HU-05 E8). Ninguna marca se envía ni se guarda.
2. **Recorte en el dispositivo, en memoria.** La app recorta el recuadro del rostro elegido con un margen que deja a YuNet y SFace la frente y el mentón para alinear. Como referencia, un 40 % del lado del recuadro, que el DEV calibra en la prueba biométrica. El margen se reduce para que el recorte **no entre en el recuadro de ningún otro rostro**. Si no se puede (rostros superpuestos), la captura se rechaza en el dispositivo con el motivo "Los rostros están muy juntos: acérquese a la persona y repita la captura" y no se envía (regla 3).
3. **Solo sale el recorte.** La API recibe solo el recorte, con el mismo contrato de una captura de un rostro. La foto completa se descarta de la memoria de la app en cuanto existe el recorte, o al salir sin elegir (E9). Ningún archivo queda en disco: los temporales de la cámara y del recorte se borran con el mismo tratamiento que la captura de HU-05 (ADR-0008, punto 1).
4. **El servidor no cambia.** YuNet sigue exigiendo **exactamente un rostro** en lo que recibe (ADR-0004, punto 3). Si en el recorte aparece parte de otra persona y YuNet detecta dos rostros, la respuesta es `captura_rechazada` y no se compara. Así, el servidor nunca procesa a un tercero aunque el recorte falle.
5. **Retención.** Lo que se guarda en `captura_pendiente` y lo que ve el revisor (HU-06) es el recorte. La foto completa nunca existe en el servidor. El ADR-0008 no cambia.
6. **Calidad.** Al rostro elegido se le aplican los mismos controles de ADR-0002 y ADR-0004: ángulo, ojos abiertos y tamaño mínimo en el dispositivo; nitidez y exposición en el servidor. El tamaño mínimo se mide sobre el rostro, no sobre la foto: un rostro lejano y pequeño se rechaza con su motivo (HU-05 E2).
7. **Bitácora.** No se registra nada de los otros rostros. Si el PA #33 autoriza registrar **solo la cantidad**, se agrega un campo `rostros_en_foto` (entero) en `parametros` de `CONSULTA_ROSTRO`, sin coordenadas ni recortes. Mientras no se responda, no se registra.
8. **Máximo de rostros (PA #33).** Provisional, hasta que responda el MININTER: **sin máximo propio**. El límite real lo pone el tamaño mínimo del rostro (punto 6): en una multitud, los rostros salen pequeños y se rechazan. Si el MININTER fija un máximo, lo aplica el dispositivo antes de la elección. **Lo decide el humano.**

## Alternativas consideradas

- **B. Enviar la foto completa con las coordenadas del rostro elegido; YuNet detecta todos los rostros en el servidor y compara solo el que coincide con la marca** (la opción que pidió evaluar el PM). Ventaja: un solo detector, el del servidor, es la referencia, y la app no recorta. Se descarta porque:
  - Los rostros de las otras personas, que son **datos sensibles de terceros sin finalidad**, viajan a la API y se procesan (se detectan) en el servidor. Eso va contra la minimización y contra el "no se guardan ni se registran" del humano, porque pasan por la memoria y los logs de un sistema más.
  - Para el candidato, habría que recortar igual en el servidor antes de guardar.
  - Los recuadros de ML Kit y de YuNet no coinciden exactamente. Hace falta una regla de coincidencia (por ejemplo, IoU ≥ 0,5) y un caso de error más: la marca no coincide con ningún rostro, o coincide con dos.
- **C. YOLO (Ultralytics) para detectar a las personas.** Se descarta: detecta cuerpos o rostros pero no reconoce identidad, así que haría falta SFace igual. Agrega un modelo más que fijar y evaluar. Y la licencia AGPL-3.0 de Ultralytics obliga a publicar el código del servicio o a pagar una licencia comercial, lo que choca con la regla 6 (licencia apta para un servicio contratado).
- **D. Seguir rechazando las fotos con dos o más rostros** (el ADR vigente). Era lo más simple y lo más seguro. Se descarta porque contradice la decisión del humano del 2026-11-20.
- **E. Comparar todos los rostros y mostrar solo el elegido.** Se descarta sin discusión: es identificación masiva (regla 6) y viola "los demás no se comparan".

## Consecuencias

- Las otras personas de la foto nunca salen del celular, y en el servidor se mantiene el invariante "exactamente un rostro". C6 se resuelve **sin cambiar el contrato** de la API ni el ADR-0008.
- Se mantiene "una consulta por persona": cada rostro de la misma escena exige otra consulta, con su motivo y su captura (nota del BA a E8).
- **Costo:** la app tiene que recortar imágenes en el dispositivo (una librería de manipulación de imagen compatible con el dev build, que confirma el LEAD con el contrato). Esa librería puede escribir temporales en la caché, y hay que borrarlos y probarlo igual que con la captura (prueba del TESTER: ningún archivo de imagen tras E8 y E9).
- **Costo:** dos pantallas nuevas, la de marcar y elegir un rostro (wireframe del UX) y la del rechazo por rostros muy juntos, más sus pruebas.
- **Riesgo:** un margen de recorte demasiado chico empeora la alineación de SFace y puede aumentar los "No concluyente". Se calibra con la prueba biométrica (ADR-0004), y la evaluación reporta por separado las capturas de E8.
- **Riesgo:** la detección del dispositivo (ML Kit) y la del servidor (YuNet) pueden discrepar: ML Kit ve un rostro y YuNet ve dos, o ninguno. El resultado es `captura_rechazada` con su motivo, nunca un resultado negativo (regla 7).
- **Telemetría:** la detección en el dispositivo usa ML Kit Face Detection. Aplican el aviso del PA #31 y la brecha 10 de TECH-DESIGN.

## Decisiones que pide al humano

1. ¿Se aprueba la opción A (recorte en el dispositivo) o se prefiere la B (foto completa y YuNet en el servidor)?
2. PA #33: ¿se registra la cantidad de rostros (`rostros_en_foto`) o no queda ninguna huella? ¿Hay un máximo de rostros por foto?
