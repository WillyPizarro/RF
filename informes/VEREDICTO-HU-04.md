# VEREDICTO — HU-04 Capturar la placa con la cámara

**Contrato:** `docs/contratos/CONTRATO-HU-04.md` **v3** (aprobado por el humano vía PM, 2026-11-19)
**Rama:** `hu-04` (base `main` `fa75945`) · **Código del DEV:** `21657f4`, `3367787` (etapa 1); `977fb18` (proyecto EAS) · **Pruebas del TESTER:** `777a9ed`, `37c38b7`, informe `7b5d9c6`
**Fecha:** 2026-11-19 · **LEAD**, skill `veredicto`
**Resultado:** **etapa 1 (Jest y verificaciones sin teléfono) en VERDE, sin rojos.** La etapa 2, el paso a paso físico en el S23 Ultra, está **pendiente**, así que el veredicto final todavía no se dicta.

---

## 1. Propiedad de rutas

`git log main..hu-04 --name-only`, agrupado por prefijo:

| Rol | Commits | Archivos | ¿Dentro de sus rutas? |
|---|---|---|---|
| `[DEV]` | `21657f4`, `3367787`, `759e938`, `977fb18`, `c2406d1` | `apps/movil/` (sin `__tests__/`), incluidos `app.json`, `eas.json` y `plugins/`; `.gitignore` (solo agregó entradas); `informes/DEV-HU-04.md` | Sí |
| `[TESTER]` | `777a9ed`, `37c38b7`, `7b5d9c6` | `apps/movil/__tests__/`, `pruebas/datos/`, `informes/TESTER-HU-04.md` | Sí |
| `[UX]` | `dcd0445`, `af8ea94` | `docs/ux/revisiones/HU-04.md` | Sí |
| `[LEAD]` | `docs/contratos/` | — | Sí |

**Sin hallazgos.** No hay imágenes, certificados ni llaves en la rama (`git ls-files`).

## 2. Versión del contrato

El DEV (`3367787`, M-3 y M-4) y el TESTER (`7b5d9c6`, M-5) trabajaron sobre la **v3**. Es válido.

## 3. Corrida del LEAD (etapa 1)

| Corrida | Resultado |
|---|---|
| `npx jest --ci` (punta `7b5d9c6`) | **111 de 111 en verde** (6 archivos; HU-04: 36) |
| API, con el proxy en 8080/8443 y `PROXY_DISPONIBLE=1` | **181 en verde, 0 rojos**, 2 omitidas (los marcadores de HU-01/02, cubiertos en HU-03/07) |
| Simuladores, contenedor y anfitrión | **115** y **136 en verde** |
| `pruebas/datos/verificar_prebuild_hu04.py` (§8 sin teléfono) | **27 OK, 0 FALLA** |
| Estado final de `api` | `infra/.env` (600 / 5) |

**Nota:** `977fb18` (M-7) llegó después de la suite. Solo cambia la configuración de EAS en `app.json` (`owner`, `projectId` y el permiso `CAMERA`, que ya pedía el plugin) y no toca código que corra en Jest. El dev build de EAS compiló sin errores con ML Kit.

## 4. Matriz de trazabilidad (etapa 1)

| Criterio (HU-04) | Caso del contrato | Prueba | Resultado |
|---|---|---|---|
| Esc. 1: la cámara lee y el usuario confirma | §2 📷 habilitado, permiso concedido → OCR-01 | Jest `HU04_ocr` | 🟢 |
| Esc. 1 | §3 una sola lectura por toque, ninguna sin tocar, "Capturar" desactivado mientras lee | Jest (cuenta las llamadas a `capturarYLeer`) | 🟢 |
| Esc. 1 | §4 tabla de texto → placa (8 filas) | Jest | 🟢 |
| Esc. 1 | §5 confirmar, corregir, conservar el motivo, **nunca consulta sola** (0 llamadas a `fetch`), sigue HU-03 v4 | Jest | 🟢 |
| Esc. 2: lectura fallida | §3 texto sin placa o falla de la cámara → OCR-03; reintentar o ingreso manual | Jest | 🟢 |
| Esc. 3: sin permiso | §2 y §5 OCR-04, "Abrir ajustes", volver con el permiso | Jest | 🟢 |
| Supuesto: la foto no se guarda | §6 sin `fetch` en el flujo, sin claves nuevas en SecureStore | Jest | 🟢 |
| Supuesto | §1 las librerías nativas solo se importan desde `lectorPlaca.ts` | `grep` del TESTER | 🟢 |
| Etapa 2 (v3) | §8 `debug-overrides`, `base-config` del sistema sin texto plano, release no depurable, sin certificados versionados | `verificar_prebuild_hu04.py` (forma c: plantilla de Expo con los mods base y solo el plugin local, porque el prebuild completo se cuelga en este equipo) | 🟢 |
| Regresión | HU-08 v4, HU-01 v5, HU-02 v3, HU-03 v4, HU-07 v4 | API, Jest y simuladores | 🟢 |
| Esc. 1, 2 y 3 en el dispositivo | §6 permiso real, 30 s sin lectura, la foto borrada (`adb`), la placa impresa leída; §3 sin red; §8 conexión | `pruebas/datos/GUION-HU-04-dispositivo.md` | **Pendiente, etapa 2** |
| Precisión | §7 | — | **Aparte**: fase de pruebas del 16 al 26-dic (v2, `PENDIENTES.md`) |

## 5. Arbitraje

Sin rojos.

## 6. Trampas

- **Código sin casos especiales:** ni para las placas `ZZ` ni para los textos de la tabla del §4. La regla está en `placaLeida.ts` y usa `formato_placa.regex`.
- **Las pruebas del §5:** cuentan de verdad las llamadas a `fetch` y verifican que el motivo se conserva.
- **La verificación del §8 por la forma c:** no ejecuta el prebuild completo, pero sí corre el plugin real (`./plugins/redDepuracion`) sobre la plantilla de Expo y lee el XML generado. Es una evidencia equivalente para lo que fija el §8. El APK del dev build se puede revisar además con `aapt` en la etapa 2.
- **Sin trampas detectadas.**

## 7. Siguiente paso

**Etapa 2** (M-8 del encargo): el paso a paso físico con el dev build de EAS en el S23 Ultra, siguiendo el guion del TESTER. El humano opera el teléfono, el TESTER corre los comandos y anota, y el DEV prepara el entorno. Después se cierra el veredicto.
