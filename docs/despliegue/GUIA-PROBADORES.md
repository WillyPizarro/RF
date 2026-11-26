# Movil Buscador — Guía para probadores

Esta es una **app de prueba** (prototipo). **Todos los datos son ficticios**: placas, personas y
requisitorias son inventados. Nada de lo que vea corresponde a personas o vehículos reales.

Necesita un **celular Android** con internet (datos o Wi-Fi). En iPhone no funciona.

## 1. Si ya tiene una versión anterior, desinstálela primero

Si en su celular ya está **Movil Buscador** (por ejemplo, la versión de una prueba anterior),
desinstálela **antes** de instalar la nueva: la versión nueva no se instala encima de la anterior.

1. Mantenga presionado el ícono de **Movil Buscador**.
2. Toque **Desinstalar** y confirme.

## 2. Descargar la app

1. En el celular, abra el navegador (por ejemplo, Chrome) y entre a:

   `https://<DOMINIO>/descargas/movil-buscador.apk`

   El responsable del demo le dice la dirección exacta.
2. El navegador pide un **usuario y una clave de la descarga**. Se los da el responsable del demo
   **por otro canal** (no vienen junto con la dirección). Escríbalos y toque **Iniciar sesión** o
   **Aceptar**. No los comparta.
3. Se descarga un archivo llamado `movil-buscador.apk`. Si el navegador avisa que el archivo puede
   ser dañino, toque **Descargar de todas formas**.

## 3. Permitir la instalación e instalar

Android pide permiso porque la app no viene de Play Store. Es normal.

- **Samsung (Android 16):** abra el archivo descargado (desde el aviso de la descarga o desde
  **Mis archivos › Descargas**). Cuando aparezca el aviso, toque **Ajustes**, active
  **Permitir de esta fuente** para la app con la que lo abrió (Chrome o Mis archivos) y vuelva
  atrás. Si aparece **Auto Blocker** y bloquea la instalación, desactívelo un momento en
  **Ajustes › Seguridad y privacidad › Auto Blocker**, instale la app y vuelva a activarlo.
- **Otros Android:** busque en **Ajustes** la opción **Instalar apps desconocidas** (o **Fuentes
  desconocidas**) y permítala para el navegador o el gestor de archivos que usó.

Toque **Instalar**. Si Play Protect avisa que la app es desconocida, toque **Más detalles ›
Instalar de todas formas**.

## 4. Abrir la app

Abra **Movil Buscador**. Arriba verá la franja amarilla "DATOS SINTÉTICOS · PROTOTIPO".

## 5. Usuarios de prueba

| Usuario | Qué puede hacer |
|---|---|
| `agente1` | Consultar placas, escribiéndolas o leyéndolas con la cámara |
| `revisor1` | Ver su pantalla de inicio (la revisión llega más adelante) |
| `supervisor1` | Ver la bitácora de todo lo que se hizo |

**La clave de estos usuarios se la da el responsable del demo**, por un canal privado. Es distinta
del usuario y la clave de la descarga. No la anote en grupos ni la comparta.

Varias personas pueden usar el mismo usuario. Si alguien escribe mal la clave **5 veces seguidas**,
ese usuario queda bloqueado unos minutos **para todos**. Escriba la clave con cuidado.

## 6. Qué probar

**Con `agente1`, escribiendo la placa:**

1. Toque **Consultar placa**.
2. Escriba la placa y elija un **motivo** (es obligatorio).
3. Toque **Consultar**.

| Placa | Qué debería ver |
|---|---|
| `ZZA-101` | Recuadro rojo: **TIENE REQUISITORIA** |
| `ZZB-201` | Recuadro gris: **Sin requisitoria registrada en la fuente consultada** |
| `ZZZ-999` | Recuadro gris azulado: **Placa no registrada en la fuente consultada. Verifique la placa.** |

También puede probar una placa mal escrita (por ejemplo `HOLA`) o consultar sin motivo: la app le
avisa y no consulta.

**Con `agente1`, leyendo la placa con la cámara:**

1. En **Consultar placa**, toque el botón 📷. La primera vez, la app pide permiso para usar la
   cámara y muestra un aviso sobre ML Kit (vea la sección 8); toque **Entendido**.
2. Apunte a una **placa impresa de prueba** (se la da el responsable del demo), de frente y con
   buena luz, y toque **Capturar**.
3. Revise la placa leída, corríjala si hace falta y toque **Usar esta placa**. Elija un motivo y
   toque **Consultar**.

La app no guarda la foto: solo usa el texto que usted confirma.

**Con `supervisor1`:**

1. Toque **Bitácora**.
2. Verá cada consulta y cada inicio de sesión, del más reciente al más antiguo. Puede filtrar por
   fecha (`dd/mm/aaaa`), usuario y tipo.
3. Toque un registro para ver su detalle. La bitácora **no se puede editar ni borrar**.

Para cambiar de usuario, toque **Salir**. Si deja la app sin usar unos minutos, la sesión se cierra
sola y tiene que volver a entrar.

Si ve "No se pudo completar la consulta; intente nuevamente", espere unos segundos y toque
**Reintentar**. Si sigue igual, avise al responsable del demo.

## 7. Lo que todavía NO funciona

- **Verificar un rostro**: llega más adelante (HU-05).
- **Revisión** (revisor) y **Mis verificaciones** (agente): llegan más adelante.

## 8. Lectura de la placa con la cámara: datos técnicos que se envían a Google

Se aplica a esta versión, que ya trae la lectura con la cámara (HU-04).

### Datos técnicos que la app envía a Google al leer la placa

**Qué es.** Para leer la placa con la cámara, la app usa **Google ML Kit** (reconocimiento de texto). Viene dentro de la app y hace la lectura en el teléfono.

**Qué no se envía a Google, según Google.**
- La foto de la placa.
- El texto que se lee (la placa).

Fuente: términos de ML Kit, <https://developers.google.com/ml-kit/terms> (modificados el 14-may-2025): *"processing of the input data (e.g. images, video, text) fully happens on-device"* y *"ML Kit does not send that data and the resultant outputs to Google servers"*.

Aparte de eso, la app no guarda la foto de la placa ni la envía al servidor del proyecto (HU-04, CONTRATO-HU-04 §6). La placa que usted **confirma y consulta** sí va al servidor del proyecto, como en el ingreso manual (HU-03).

**Qué se envía a Google, según Google.** Son datos técnicos de uso y rendimiento:
- Marca y modelo del teléfono, versión del sistema y aceleradores de ML disponibles.
- Nombre y versión de la app.
- Un **código de esta instalación** de la app (Google lo llama *per-installation identifier*). Según Google, ese código "no está pensado para" reconocer a un usuario ni a un teléfono concreto.
- Tiempos de respuesta y configuración de la lectura (por ejemplo, el formato y la resolución de la imagen).
- Tamaño de la entrada y de la salida, y versión de la herramienta.
- Tipo de evento (inicio, lectura, cierre) y códigos de error.

Según Google, estos datos sirven para medir el rendimiento, corregir fallas, mantener y mejorar la herramienta y detectar mal uso. Google dice que viajan cifrados (HTTPS) a sus servidores, que están fuera del Perú, y que no los pasa a terceros. ML Kit también puede conectarse a Google de vez en cuando para recibir correcciones y modelos actualizados.

Fuentes: <https://developers.google.com/ml-kit/android-data-disclosure> (modificada el 14-may-2025) y <https://developers.google.com/ml-kit/ios-data-disclosure> (sin fecha visible).

**¿Se puede apagar?** No. Google no ofrece ninguna opción oficial para desactivar el envío. La placa se puede ingresar siempre a mano, pero **no está verificado** que, si no se usa la lectura por cámara, la app deje de enviar estos datos.

**Qué no verificó el equipo.**
- Todo lo anterior lo **afirma Google**. El equipo no capturó el tráfico de red para comprobarlo.
- En el teléfono hay una cola local de eventos (`com.google.android.datatransport.events`). Su contenido se está revisando (encargo M-11). Si aparece la foto o el texto leído, la decisión se reabre.

**En este prototipo (MVP).** Se usan solo datos sintéticos y teléfonos de prueba. No hay ciudadanos reales. Para producción queda como brecha abierta: bloqueo de red por MDM o firewall, o cambio de OCR. El área legal define la base legal, el flujo de datos fuera del país y cómo se informa al usuario.

**Si nota algo raro** (por ejemplo, que la app pide subir fotos o muestra la placa en otro lugar), anótelo en su informe de prueba con la fecha y la hora.

## 9. Todos los datos son ficticios

Las placas (`ZZ…`), las personas, las requisitorias y los usuarios son de prueba. Nada corresponde
a ciudadanos ni vehículos reales. No escriba datos reales en la app.

## 10. Desinstalar la app

Cuando termine la prueba, o cuando se lo pidan:

1. Mantenga presionado el ícono de **Movil Buscador**.
2. Toque **Desinstalar** y confirme.

En Samsung también puede ir a **Ajustes › Aplicaciones › Movil Buscador › Desinstalar**. Al
desinstalarla no queda nada de la app en el celular. Puede borrar también el archivo
`movil-buscador.apk` de **Mis archivos › Descargas**.
