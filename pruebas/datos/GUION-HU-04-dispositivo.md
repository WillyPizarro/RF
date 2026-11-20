# Guion de la etapa 2 — HU-04 en el Samsung Galaxy S23 Ultra (Android 16)

**Contrato:** `docs/contratos/CONTRATO-HU-04.md` **v3**. **Encargo:** `docs/contratos/ENCARGO-HU-04.md` (M-1 a M-3).
**Quién:** el humano toma las fotos y opera el teléfono; el TESTER guía, corre los comandos y anota.
**Cuándo:** cuando el LEAD dé la orden de la etapa 2 (M-n). **Este guion no se ejecutó.**

**Qué cubre (M-2):**
- los casos "Dispositivo" del §6;
- el uso sin red del §3;
- la conexión del §8 (M-3);
- el paso a paso del §5, una vez.

La **precisión del OCR (§7) no entra**: va en la fase de pruebas del 16 al 26-dic, con `pruebas/datos/ocr-precision.csv`.

## Reglas durante la prueba

- **Placas:** solo las de `pruebas/datos/hoja-placas-prueba.html`, impresas, con prefijo `ZZ` y la leyenda "PRUEBA — NO VÁLIDA". **Nunca** se apunta la cámara a un vehículo real.
- **Capturas de pantalla:** van **fuera del repositorio**, por ejemplo en `C:\Willy\Trabajo\MININTER\hu04-capturas\`. Nunca se hace commit de imágenes ni de fotos.
- **Certificados:** la CA de Caddy no se copia nunca dentro del repositorio.
- **Comandos:** se corren en PowerShell, desde cualquier carpeta, con `adb` en el `PATH` (ver `informes/DEV-HU-04.md`).
- **Paquete de la app:** `pe.prototipo.movilbuscador`.

## 0. Preparación (una vez)

| Paso | Comando o acción | Esperado |
|---|---|---|
| 0.1 | Imprimir `pruebas/datos/hoja-placas-prueba.html`: abrirlo en el navegador e imprimir en A4 horizontal al 100 % | 8 hojas, una placa por hoja |
| 0.2 | `adb devices` | El S23 Ultra aparece como `device` (no `unauthorized`) |
| 0.3 | `adb shell getprop ro.build.version.release` | `16` |
| 0.4 | Sistema arrancado: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.fotos.yml --env-file infra/.env up -d --build` | `proxy` sano en `https://localhost:8443` |
| 0.5 | La CA de Caddy instalada en el teléfono como certificado del usuario (pasos del DEV en `informes/DEV-HU-04.md`) | — |
| 0.6 | `adb reverse tcp:8443 tcp:8443` | Sin error. `adb reverse --list` muestra `tcp:8443 tcp:8443` |
| 0.7 | El dev build instalado (`EXPO_PUBLIC_API_URL=https://localhost:8443`): `adb shell pm list packages pe.prototipo.movilbuscador` | `package:pe.prototipo.movilbuscador` |
| 0.8 | Contar las fotos de la galería antes de empezar: `adb shell "ls /sdcard/DCIM/Camera 2>/dev/null \| wc -l"` y `adb shell "ls /sdcard/Pictures 2>/dev/null \| wc -l"` | Anotar los dos números (G0 y P0) |

## 1. Conexión con la API local (§8, "Conexión")

| Paso | Acción | Esperado | Resultado |
|---|---|---|---|
| 1.1 | Abrir la app e iniciar sesión con `agente1` (clave de `CLAVE_USUARIOS_PRUEBA`, dictada por el humano; no se escribe en ningún archivo) | HOME-01 con "Rol: Agente" | |
| 1.2 | Tocar "Consultar placa" | PLA-01 con el catálogo de motivos (llegó `GET /v1/motivos`) | |

## 2. Permiso real del sistema (§6, "Permiso real")

| Paso | Acción o comando | Esperado | Resultado |
|---|---|---|---|
| 2.1 | Dejar el permiso sin decidir: `adb shell pm revoke pe.prototipo.movilbuscador android.permission.CAMERA` y `adb shell pm clear-permission-flags pe.prototipo.movilbuscador android.permission.CAMERA user-set user-fixed` | Sin error | |
| 2.2 | En PLA-01, tocar 📷 ("Leer con cámara") | Aparece el diálogo del sistema que pide el permiso de cámara | |
| 2.3 | Elegir "No permitir" | OCR-04: "La app no tiene permiso para usar la cámara." | |
| 2.4 | Tocar "Abrir ajustes" y después `adb shell "dumpsys activity activities \| grep -E 'topResumedActivity\|mResumedActivity'"` | Se abre la ficha de la app en Ajustes: el comando muestra `com.android.settings` con la información de `pe.prototipo.movilbuscador` | |
| 2.5 | En Ajustes › Permisos › Cámara, elegir "Permitir solo mientras se usa la app"; volver a la app y tocar 📷 | OCR-01 con el visor en vivo | |

## 3. Sin lectura continua (§6, regla 6)

| Paso | Acción | Esperado | Resultado |
|---|---|---|---|
| 3.1 | En OCR-01, apuntar a la placa impresa `ZZA-101` durante **30 s** (cronómetro), **sin tocar "Capturar"** | No aparece OCR-02; el visor sigue en vivo | |

## 4. La placa se lee y el paso a paso (§6, "La placa se lee"; §5 una vez)

| Paso | Acción | Esperado | Resultado |
|---|---|---|---|
| 4.1 | En PLA-01, **no** elegir motivo. Tocar 📷, apuntar a `ZZA-101` de frente, con buena luz, y tocar "Capturar" | Mientras lee, "Capturar" queda desactivado y se ve el indicador de carga; después aparece OCR-02 "Placa leída" con `ZZA-101` en el campo. **No se muestra ninguna imagen** | |
| 4.2 | Corregir el campo a `ZZB-201` y tocar "Usar esta placa" | PLA-01 con `ZZB-201`; el motivo sigue vacío y **no se consultó nada** | |
| 4.3 | Tocar "Consultar" | "Indique el motivo de la consulta." (no se envía) | |
| 4.4 | Elegir "Control vehicular" y tocar "Consultar" | PLA-06: "Sin requisitoria registrada en la fuente consultada" (`ZZB-201`) | |
| 4.5 | Repetir 4.1 con `ZZZ-999` y consultar con un motivo | OCR-02 con `ZZZ-999`; después PLA-08 "Placa no registrada en la fuente consultada. Verifique la placa." | |
| 4.6 | En OCR-01, tapar la cámara con la mano y tocar "Capturar" | OCR-03: "No se pudo leer la placa. Pruebe de frente y con más luz." | |
| 4.7 | Captura de pantalla de OCR-02 (fuera del repositorio): `adb exec-out screencap -p > C:\Willy\Trabajo\MININTER\hu04-capturas\ocr-02.png` | Archivo creado fuera del repositorio | |

## 5. La foto se borra (§6, "La foto se borra")

| Paso | Acción o comando | Esperado | Resultado |
|---|---|---|---|
| 5.1 | Hacer **10 capturas seguidas** (OCR-01 → "Capturar" → "Volver a capturar"), alternando las placas impresas | Cada una termina en OCR-02 u OCR-03 | |
| 5.2 | `adb shell run-as pe.prototipo.movilbuscador find . -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png"` | **Ningún archivo de captura** (ni en `files/` ni en `cache/`). Si aparece algo, anotar la ruta completa | |
| 5.3 | `adb shell "ls /sdcard/DCIM/Camera 2>/dev/null \| wc -l"` y `adb shell "ls /sdcard/Pictures 2>/dev/null \| wc -l"` | Los mismos números G0 y P0 del paso 0.8: la galería no tiene fotos nuevas | |

## 6. Sin red (§3, "Sin red")

| Paso | Acción o comando | Esperado | Resultado |
|---|---|---|---|
| 6.1 | Modo avión: `adb shell cmd connectivity airplane-mode enable` (o desde el panel rápido). El Wi-Fi también queda apagado | Icono de avión | |
| 6.2 | En PLA-01, tocar 📷 y capturar `ZZA-101` | OCR-01, OCR-02 y OCR-03 funcionan igual: la lectura es local | |
| 6.3 | "Usar esta placa", elegir motivo y "Consultar" | PLA-07: "No se pudo completar la consulta; intente nuevamente". **Nunca** "sin requisitoria" | |
| 6.4 | `adb shell cmd connectivity airplane-mode disable` | Vuelve la red | |

> **Nota:** `adb reverse` va por USB y puede seguir funcionando con el modo avión activo. Si en 6.3 la consulta funciona, repetir 6.2 y 6.3 con `adb reverse --remove tcp:8443`. Después restaurarlo con `adb reverse tcp:8443 tcp:8443`.

## 7. Al terminar

| Paso | Comando | Esperado |
|---|---|---|
| 7.1 | `adb reverse --remove-all` | Sin error |
| 7.2 | Anotar los resultados en `informes/TESTER-HU-04.md` (etapa 2), sin imágenes | — |
| 7.3 | La CA de Caddy queda instalada hasta el cierre del proyecto: se borra según el acta de eliminación (`docs/contratos/PENDIENTES.md`) | — |
