# Movil Buscador — Guía para probadores

Esta es una **app de prueba** (prototipo). **Todos los datos son ficticios**: placas, personas y
requisitorias son inventados. Nada de lo que vea corresponde a personas o vehículos reales.

Necesita un **celular Android** con internet (datos o Wi-Fi). En iPhone no funciona.

## 1. Instalar la app

1. **Abrir el enlace.** En su celular, abra el enlace que le enviaron (lo comparte el responsable del demo) y toque **Instalar** o **Descargar**. Se descarga un archivo que termina en `.apk`.
2. **Permitir la instalación.** Android pide permiso porque la app no viene de Play Store. Es normal.
   - **Samsung (Android 16):** cuando aparezca el aviso, toque **Ajustes**, active **Permitir de esta fuente** para la app con la que abrió el enlace (por ejemplo, Chrome o Mis archivos) y vuelva atrás. Si aparece **Auto Blocker** y bloquea la instalación, desactívelo un momento en **Ajustes › Seguridad y privacidad › Auto Blocker**, instale la app y vuelva a activarlo.
   - **Otros Android:** busque en **Ajustes** la opción **Instalar apps desconocidas** (o **Fuentes desconocidas**) y permítala para el navegador o el gestor de archivos que usó.
3. **Instalar.** Toque **Instalar**. Si Play Protect avisa que la app es desconocida, toque **Más detalles › Instalar de todas formas**.
4. **Abrir.** Abra la app **Movil Buscador**. Arriba verá la franja amarilla "DATOS SINTÉTICOS · PROTOTIPO".

## 2. Usuarios de prueba

| Usuario | Qué puede hacer |
|---|---|
| `agente1` | Consultar placas |
| `revisor1` | Ver su pantalla de inicio (la revisión llega más adelante) |
| `supervisor1` | Ver la bitácora de todo lo que se hizo |

**La clave se la da el responsable del demo**, por un canal privado. No la anote en grupos ni la
comparta.

Varias personas pueden usar el mismo usuario. Si alguien escribe mal la clave **5 veces seguidas**,
ese usuario queda bloqueado unos minutos **para todos**. Escriba la clave con cuidado.

## 3. Qué probar

**Con `agente1`:**

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

**Con `supervisor1`:**

1. Toque **Bitácora**.
2. Verá cada consulta y cada inicio de sesión, del más reciente al más antiguo.
3. Toque un registro para ver su detalle. La bitácora **no se puede editar ni borrar**.

Para cambiar de usuario, toque **Salir**. Si deja la app sin usar unos minutos, la sesión se cierra
sola y tiene que volver a entrar.

## 4. Lo que todavía NO funciona

- **Leer la placa con la cámara** (el botón 📷): llega en el próximo despliegue.
- **Verificar un rostro**: llega más adelante.
- **Revisión** (revisor) y **Mis verificaciones** (agente): llegan más adelante.

Si ve "No se pudo completar la consulta; intente nuevamente", espere unos segundos y toque
**Reintentar**. Si sigue igual, avise al responsable del demo.

## 5. Desinstalar la app

Cuando termine la prueba, o cuando se lo pidan:

1. Mantenga presionado el ícono de **Movil Buscador**.
2. Toque **Desinstalar** y confirme.

En Samsung también puede ir a **Ajustes › Aplicaciones › Movil Buscador › Desinstalar**. Al
desinstalarla no queda nada de la app en el celular.
