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

### M-2 (2026-11-19) — CONTRATO-HU-04 v2

**Reemplaza** la versión del encabezado: el documento de trabajo ahora es CONTRATO-HU-04 **v2**, aprobado por el humano (vía PM). **La precisión del OCR va aparte** (fase de pruebas del 16 al 26-dic, anotada en `PENDIENTES.md`). En el veredicto de HU-04 entra solo el **paso a paso físico** en el S23 Ultra (Android 16), con las fotos que toma el humano.

- **TESTER:** el guion de la etapa 2 cubre solo los casos "Dispositivo" del §6. La plantilla del CSV de precisión queda preparada para la fase de pruebas.
- **DEV:** sin cambios.

### M-3 (2026-11-19) — CONTRATO-HU-04 v3: conexión del teléfono a la API local

**Reemplaza** a M-2 en la versión: el documento de trabajo ahora es CONTRATO-HU-04 **v3**. Hay un §8 nuevo. El humano eligió la **opción B**: la CA local de Caddy se instala en el S23 Ultra, el `network_security_config` lleva `debug-overrides` **solo para depuración** y se usa `adb reverse tcp:8443`.

- **DEV:**
  - **Configuración del dev build:** aplica la configuración del §8 desde `app.json`, con un plugin de configuración en `apps/movil/`.
  - **Secretos:** asegura en `.gitignore` (solo agregando) que no se versione ningún `.crt`, `.pem`, `.key` ni `.der`.
  - **Pasos para el humano:** agrega a `informes/DEV-HU-04.md` pasos numerados, en español simple, para Samsung con Android 16:
    - exportar la CA desde el contenedor `proxy` a una carpeta **fuera del repositorio**;
    - pasarla al teléfono e instalarla como certificado del usuario;
    - `adb reverse tcp:8443 tcp:8443`;
    - generar el dev build con `EXPO_PUBLIC_API_URL=https://localhost:8443`;
    - **borrar el certificado al cierre del proyecto** (va al acta de eliminación, en `PENDIENTES.md`).

  Al terminar: `ENTREGA DEV` con el commit.
- **TESTER:** agrega la verificación del §8 que no necesita el teléfono:
  - corre `npx expo prebuild --platform android` en una **copia de `apps/movil` fuera del repositorio**;
  - comprueba que los certificados del usuario aparecen solo dentro de `<debug-overrides>`, que el `base-config` no permite texto plano y que `release` no es depurable;
  - comprueba con `git ls-files` que no hay certificados ni llaves versionados.

  La conexión real queda para el guion de la etapa 2.

### M-4 (2026-11-19) — Revisión del UX

**No reemplaza nada.** El UX aprobó la etapa 1 con 1 observación MEJORA (`docs/ux/revisiones/HU-04.md`, commit `dcd0445`).

- **DEV:** en OCR-01, mientras `capturarYLeer` está en curso, muestra el indicador de carga que ya usa la app (`ActivityIndicator` con `accessibilityLabel="Cargando"`), junto al botón o sobre el visor. No agrega ningún texto visible. Entrégalo junto con la M-3, en una sola `ENTREGA DEV`, con una captura nueva de OCR-01 en espera.
- **TESTER:** sin cambios. La suite completa de la etapa 1 espera su M-n.

### M-5 (2026-11-19) — Suite completa de la etapa 1

**No reemplaza nada.** El UX dio su aprobación final de la etapa 1 (`docs/ux/revisiones/HU-04.md`, commit `af8ea94`). El commit definitivo del DEV para la etapa 1 es `3367787`, sobre CONTRATO-HU-04 **v3**.

- **TESTER:** antes de correr, termina la verificación del §8 que no necesita el teléfono (M-3): `debug-overrides`, el `base-config` sin texto plano, `release` no depurable y `git ls-files` sin certificados. Si el prebuild se cuelga, usa otra forma observable y documéntala; si no hay ninguna, queda `NO VERIFICADO` con el motivo. Después corre la suite completa **una sola vez** sobre la punta de `hu-04`:
  - **Arranque:** con `--build`, los dos archivos de compose, el proxy en el puerto alterno y `PROXY_DISPONIBLE=1`.
  - **Jest** completo de la app.
  - **pytest de la API**, como regresión.
  - **pytest de los simuladores**, en el contenedor y en el anfitrión.
  - **Al terminar:** `api` vuelve a `infra/.env`, y mandas `ENTREGA TESTER` con el informe. Los casos "Dispositivo" quedan como pendientes de la etapa 2, no como `NO VERIFICADO`.
- **DEV:** no hagas más commits en `hu-04` salvo que el LEAD te los pida.

### M-6 (2026-11-19) — Corrección del informe del DEV (comandos de EAS)

**No reemplaza nada.** Aviso del PM: el paquete npm `eas` no es el de Expo (es un motor de plantillas). El de Expo es **`eas-cli`** (hoy en la 27.11.0). En la etapa 2, el PM ya dejó `adb` 37.0.3 instalado y el S23 Ultra (SM-S918B, Android 16) conectado y autorizado.

- **DEV — único commit permitido en `hu-04` durante la suite:** en `informes/DEV-HU-04.md`, cambia todos los `npx eas …` por `npx eas-cli@27.11.0 …`: `login`, `init`, `build` y los demás. El login va como `! npx eas-cli@27.11.0 login`. **Solo el informe:** no agregues `eas-cli` como dependencia ni toques `package.json` mientras corre la suite. Avisa con `ENTREGA DEV` y el commit.

### M-7 (2026-11-19) — Proyecto EAS y dev build (etapa 2)

**No reemplaza nada.** Decisión del humano (vía PM): el proyecto EAS va en la cuenta de equipo **`willypizarros-team`**. El humano ya inició sesión, y la sesión vive en su perfil de Windows, no en el repositorio. **DEV: no empieces hasta que el LEAD te avise que el TESTER terminó la suite de la etapa 1**, para no pisarse en la misma carpeta.

- **DEV:**
  1. En `apps/movil/app.json`, `"owner": "willypizarros-team"`.
  2. `npx eas-cli@27.11.0 init` para vincular el proyecto. Escribe `extra.eas.projectId`, que es público y sí va en el repositorio.
  3. Commit `[DEV]` en `hu-04`, sin `Co-Authored-By`.
  4. `npx eas-cli@27.11.0 build --profile development --platform android --non-interactive`. Pásale al LEAD **el enlace o el QR del APK**, nunca un token ni una credencial.
  - **Si el build falla por ML Kit** (`not linked` u otro error): aplica tu alternativa `expo-text-extractor` **dentro de `src/camara/lectorPlaca.ts`**, sin cambiar la forma del §1 del contrato. Infórmame del cambio antes de seguir, porque obliga a repetir el Jest de la etapa 1.
  - **Al terminar:** `ENTREGA DEV` con el commit, el enlace del APK y el informe actualizado.

### M-8 (2026-11-19) — Etapa 2: paso a paso en el S23 Ultra

**No reemplaza nada.** La etapa 1 está en verde (`informes/VEREDICTO-HU-04.md`). El dev build de EAS está listo (`977fb18`; el enlace está en el informe del DEV). La etapa 2 sigue `pruebas/datos/GUION-HU-04-dispositivo.md` y **necesita al humano frente al teléfono**: el PM coordina el momento.

- **Orden:**
  1. **Docker:** el TESTER termina la regresión local de DESPLIEGUE-01, porque el proyecto de compose es el mismo en las dos carpetas.
  2. **Preparación del DEV, en la carpeta principal (rama `hu-04`):**
     - levanta el sistema con los dos archivos de compose y el proxy en 8443;
     - exporta la CA de Caddy a una carpeta **fuera del repositorio**;
     - deja `apps/movil/.env` (no se versiona) con `https://localhost:8443`;
     - corre `adb reverse` de 8443 y 8081 y arranca `npx expo start --dev-client`.

     Avisa al PM cuando esté listo.
  3. **Humano:** instala el APK del enlace y la CA, siguiendo los pasos del DEV, y opera el teléfono según el guion. Toma las fotos de las placas impresas `ZZ`.
  4. **TESTER:**
     - corre los comandos `adb` del guion: la galería antes y después, la búsqueda de `*.jpg` con `run-as`, `aapt` sobre el APK;
     - anota cada paso en verde, rojo o `NO VERIFICADO`;
     - deja las capturas **fuera del repositorio**;
     - termina con `ENTREGA TESTER` y el informe actualizado.
- **La clave de los usuarios** la dicta el humano. No se escribe en ningún archivo.
- **Al terminar,** el DEV deja el sistema con `infra/.env` y quita `adb reverse`. **La CA queda instalada** hasta el cierre del proyecto, como dice el acta.

### M-9 (2026-11-20) — Revisión del UX: safe area (BLOQUEA)

**No reemplaza nada.** En la prueba física, el UX encontró que la franja "DATOS SINTÉTICOS · PROTOTIPO" tapa la barra de estado de Android en **todas** las pantallas. Lo clasificó **BLOQUEA** (`docs/ux/revisiones/HU-04.md`, observación 2, commit `bc63ffd`). No cambia el contrato.

- **DEV:** **empieza cuando el PM avise que terminó la sesión física con el humano.** Metro está sirviendo el JS al teléfono, y un cambio a mitad de la sesión se recargaría en vivo. Sin tocar ningún texto:
  - **Safe area superior e inferior,** con `react-native-safe-area-context`, resuelta **una sola vez** para todas las pantallas.
  - **La zona de la barra de estado** con el fondo de la franja e íconos claros.
  - **Que Jest siga pasando:** si el proveedor del safe area necesita una simulación en Jest, dilo en el informe. El TESTER la agrega en sus rutas.
  - **Capturas del S23**, fuera del repositorio, de OCR-01, OCR-02, PLA-01 y HOME-01.

  Al terminar: `ENTREGA DEV` con el commit y las capturas.
- **TESTER:** cuando llegue la entrega, corre el Jest completo. Si hace falta simular `react-native-safe-area-context`, la simulación va en `apps/movil/__tests__/` o en el `setup` de Jest que esté en tus rutas.

### M-10 (2026-11-20) — CONTRATO-HU-04 v4: sin caché HTTP

**Reemplaza** a M-3 en la versión: el documento de trabajo ahora es CONTRATO-HU-04 **v4**, aprobado por el humano (vía PM). En la prueba física apareció la caché HTTP de Android guardando en disco `/v1/me` y `/v1/motivos` (hallazgo B). Además, "Abrir ajustes" puede abrir la pantalla de permisos de la app (hallazgo D, ya cumplido).

- **DEV:** junto con la M-9, y **después de la sesión física**:
  - **API:** `Cache-Control: no-store` en **todas** las respuestas de `/v1/*`, incluidas las de error y las `401`, `403`, `404` y `422`.
  - **App:** `cache: 'no-store'` en las opciones de cada `fetch` a la API.

  Al terminar: una sola `ENTREGA DEV` con la M-9 y la M-10.
- **TESTER:**
  - **pytest:** la cabecera en las respuestas de `/v1`, en éxito y en error, por la red interna y por el proxy.
  - **Jest:** que cada llamada a la API lleve `cache: 'no-store'`.
  - **Guion:** agrega el paso del dispositivo (`run-as … ls -R cache/http-cache` sin entradas de `/v1/`) para la **mini sesión física**, que el LEAD coordina con el PM.

### M-11 (2026-11-20) — Telemetría de ML Kit: opción A y verificación práctica

**No reemplaza nada.** Decisión del humano (vía PM, 2026-11-20) sobre el hallazgo C (`docs/arch/evaluaciones/HU-04-telemetria-mlkit.md`): **opción A**. Se mantiene ML Kit, se documenta y se avisa al usuario. El texto exacto del aviso lo redactan el UX y el BA, y entra en CONTRATO-HU-04 **v5**, que llega en una M-n siguiente. **Si en la verificación aparece la imagen o el texto leído, la decisión se reabre.**

- **DEV:**
  - Confirma de dónde viene `com.google.android.datatransport` con `./gradlew :app:dependencies`, en una copia fuera del repositorio.
  - Si el prebuild se cuelga, usa otra forma: el log del build de EAS, o los `build.gradle` de las dependencias en `node_modules`. Documéntala.
  - Va en tu informe, junto con la M-9 y la M-10.
  - **No implementes el aviso todavía:** espera la v5.
- **TESTER:** agrega al guion de la mini sesión la revisión de la cola. La corre el PM con `adb`; tú das los comandos exactos.
  - **Copia:** `adb exec-out run-as pe.prototipo.movilbuscador cat databases/com.google.android.datatransport.events`, a un archivo **fuera del repositorio**.
  - **Lectura:** las tablas y los eventos, con `sqlite3` si está disponible o con un script de Python con `-I`.
  - **Qué se busca:** ninguna imagen (cabeceras JPEG o PNG), ningún texto de placa leído (`ZZ…`) y ningún dato que no esté en la divulgación de Google.

  El resultado va a tu informe. La copia de la base **no se versiona** y se borra al terminar.
