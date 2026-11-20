# ENCARGO LEAD → TESTER y DEV — HU-04

**Documento de trabajo:** `docs/contratos/CONTRATO-HU-04.md` **v1**, aprobado por el humano (vía PM) el 2026-11-19. Es la única spec: lo que no dice no se supone, se pregunta. Los contratos anteriores siguen vigentes y no se pueden romper, en especial CONTRATO-HU-03 v4: la consulta no cambia.
**Rama:** `hu-04`, desde `main` `fa75945`. El TESTER y el DEV trabajan en la misma rama, cada uno en sus rutas.
**Pasa por UX:** sí. Pantallas OCR-01 a OCR-04 y el botón 📷 de PLA-01, con capturas de Jest. Las del dev build se suman cuando exista la parte física.

## Reglas

1. Solo tocas las rutas que `AGENTS.md` asigna a tu rol (las repite el contrato en "Rutas de cada rol").
2. Commits solo de tus rutas, con prefijo `[TESTER]` o `[DEV]` y **sin** la línea `Co-Authored-By`. Sin push y sin merge.
3. Las dudas van al LEAD: `herdr agent prompt lead "PREGUNTA <ROL>: <pregunta>"`.
4. No toques `Empezar.txt` ni lo incluyas en commits.
5. **Ninguna foto de placa en el repositorio ni guardada en el dispositivo.** Solo placas sintéticas con el prefijo `ZZ`; nunca placas de vehículos reales. Ningún token ni secreto en el repositorio: el login de EAS lo hace el humano con `! npx eas login`.
6. Reglas de negocio de `AGENTS.md`:
   - la 2: el motivo es obligatorio;
   - la 6: sin lectura continua ni automática;
   - la 7: ningún error se convierte en un negativo;
   - la 8: ninguna foto en el repositorio.
7. Arranque de la API, si lo necesitas: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env up -d --build`, siempre con los dos archivos.

## Etapas

**Etapa 1 — Jest (ahora).** Todo lo que el contrato marca como "Jest" en "Qué se prueba dónde". El módulo de borde `src/camara/lectorPlaca.ts` (§1) es la frontera: el TESTER lo simula con `jest.mock` y el DEV lo implementa con las librerías nativas.

**Etapa 2 — Android real con dev build (espera).** Va en un Samsung Galaxy S23 Ultra por USB. **No empieza hasta que el humano responda la pregunta 3 del contrato** (quién hace las capturas físicas y si la precisión entra en este veredicto). El LEAD avisa con una M-n.

## Qué entrega cada uno

- **DEV (etapa 1):**
  - **Módulo de borde:** `src/camara/lectorPlaca.ts`, con la forma exacta del §1, implementado con una librería de cámara y ML Kit Text Recognition compatibles con Expo SDK 58 (ADR-0002).
  - **Pantallas y flujo:** OCR-01 a OCR-04, el botón 📷 habilitado en PLA-01, la regla de texto a placa del §4 y el flujo del §5 (nunca consulta sola).
  - **Configuración:** el permiso de cámara en `app.json` y la configuración del dev build. `eas.json` lleva el perfil `development` (APK interno, sin secretos) y va en `apps/movil/`.
  - **Que siga compilando:** `tsc` limpio y que la app siga corriendo en Jest.
  - **Informe** en `informes/DEV-HU-04.md`, con:
    - qué librerías eligió y por qué;
    - cómo se genera el dev build con EAS (los comandos que corre el humano, empezando por `! npx eas login`) y, como respaldo, en local;
    - **las instrucciones para esta PC:**
      - instalar Android **platform-tools** (`adb`) y agregarlo al `PATH`;
      - instalar el **driver USB de Samsung**, si Windows no reconoce el teléfono;
      - activar la **depuración USB** en el S23 Ultra;
      - comprobarlo con `adb devices`.

    No instales nada en la PC por tu cuenta: el humano ejecuta esos pasos o los autoriza.
  - **Capturas de Jest para el UX**, fuera del repositorio, con la ruta indicada en el informe.
- **TESTER (etapa 1):**
  - **Pruebas de Jest** de todo lo que el contrato marca como "Jest":
    - §2;
    - §3, contando las llamadas a `capturarYLeer` por toque y comprobando que no hay ninguna sin tocar;
    - §4, la tabla completa;
    - §5, comprobando que no hay ninguna llamada a `fetch` entre 📷 y "Consultar", y que el motivo se conserva;
    - §6, lo de SecureStore y el cuerpo de la consulta.
  - **Una búsqueda en `apps/movil/src`** que compruebe que la librería de cámara y la de ML Kit solo se importan desde `src/camara/lectorPlaca.ts` (§1).
  - **Para la etapa 2, sin ejecutarla:**
    - el **guion de las pruebas físicas** en `pruebas/datos/`, que cubra los casos "Dispositivo" del §6, el §7 y los comandos `adb` exactos;
    - la **plantilla vacía** de `pruebas/datos/ocr-precision.csv`, con las columnas placa impresa, leída, condición y coincide;
    - el **diseño de las placas impresas**, con el prefijo `ZZ` y la leyenda "PRUEBA — NO VÁLIDA", como texto o SVG sin fotos.
  - **Informe** en `informes/TESTER-HU-04.md`, con cada caso en verde, rojo o `NO VERIFICADO`, y la evidencia.

## Orden del cierre (etapa 1)

1. `ENTREGA DEV` con el informe y las capturas.
2. El LEAD pasa las capturas al UX. Si hay correcciones, vuelven al DEV como una M-n.
3. Con la aprobación del UX, el LEAD da la orden (en una M-n) de la suite completa, una sola vez: Jest completo más la regresión de la API y de los simuladores.
4. `ENTREGA TESTER` con el informe.

La etapa 2 se agrega con su propia M-n cuando llegue la respuesta del humano.

## Aviso de vuelta

`herdr agent prompt lead "ENTREGA <ROL>: <resumen corto> — informes/<ROL>-HU-04.md"`.

## Instrucciones del ciclo (M-n)

Aquí se agregan las aclaraciones durante el ciclo. Cada una dice qué reemplaza.

### M-1 (2026-11-19) — Hoja de placas para imprimir

**No reemplaza nada.** Respuestas del humano (vía PM): el S23 Ultra tiene **Android 16**, y las fotos físicas **las toma el humano**. Sigue pendiente si la precisión entra en este veredicto.

- **TESTER**, en `pruebas/datos/` (es parte del material de la etapa 2, sin ejecutarla):
  - **La hoja:** una hoja **A4 imprimible**, en HTML o en un PDF generado por un script, **sin imágenes de placas reales**.
  - **Las placas:** de **6 a 8 placas sintéticas de la semilla `ZZ`** de HU-08 (por ejemplo `ZZA-101`, `ZZB-201`, `ZZZ-999` y otras de la semilla). Las de `semilla.json` se leen, no se copian a mano.
  - **Tamaño:** cercano al real, unos **30 × 15 cm**. Si no cabe en A4, escalada (por ejemplo, una o dos por página en horizontal). Indica la escala en la hoja.
  - **Aspecto:** **fondo blanco**, **texto negro grueso** y la placa con el formato `ZZA-101`.
  - **Leyenda:** **"PRUEBA — NO VÁLIDA"**, **fuera del recuadro de los caracteres**, para que el OCR no la lea como placa.
  - **Para imprimir:** una **instrucción de una línea** (por ejemplo, abrir el HTML en el navegador e imprimir en A4 al 100 %, sin ajustar a la página).

  Al terminar: `ENTREGA TESTER: hoja de placas — <ruta>` con el commit. Lo demás de la etapa 1 sigue igual.
