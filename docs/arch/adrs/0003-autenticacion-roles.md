# ADR 0003: Autenticación vía API, tres roles y usuarios por script de carga

## Estado

Aceptado (2026-11-18). **Precisión documentada (2026-11-24, PA #38):** el [ADR-0020](0020-keycloak-al-final.md) (aceptado) describe cómo cambiar el verificador de la clave del punto 3 de Supabase Auth a Keycloak después del MVP, sin cambiar los roles ni que el inicio de sesión pase por la API. En el MVP este ADR rige sin cambios. El PA #2 (opciones B, C y E) **no** reabre este ADR hasta que responda el MININTER ([estimado](../evaluaciones/PA-02-estimado-opciones.md)).

## Contexto

- HU-01: inicio de sesión con usuario y clave. El intento fallido queda en la bitácora (E2), la sesión vence por inactividad (E3) y la cuenta se bloquea tras varios intentos fallidos (punto abierto).
- HU-02: cada usuario ve y usa solo las funciones de su rol, y el control se aplica en el backend. El supuesto de HU-02 (conflicto C1) es que los roles se asignan en la carga inicial, sin pantalla de administración.
- HU-06: el revisor es un actor distinto del usuario en campo (C2, PA #2).
- HU-07: alguien tiene que poder consultar la bitácora (punto abierto: ¿quién?). PA #9 pregunta qué roles existen además del usuario en campo.
- ADR-0001 deja la autenticación en Supabase Auth. Pero si la app inicia sesión directamente contra Supabase, la API no ve los intentos fallidos, y Supabase no trae de serie el bloqueo de cuenta por intentos.

## Decisión

1. **Tres roles:**

   | Rol | Puede | No puede |
   |---|---|---|
   | `agente` | Consultar placas (HU-03, HU-04), verificar rostros (HU-05) y ver el estado de sus propias consultas | Revisar coincidencias, ver la bitácora |
   | `revisor` | Ver la cola de coincidencias pendientes y decidir (HU-06) | Hacer consultas, ver la bitácora completa |
   | `supervisor` | Consultar la bitácora con filtros (HU-07) | Hacer consultas, revisar coincidencias |

   Un usuario tiene un solo rol. Quien consulta nunca aprueba su propia coincidencia.

2. **Administración de usuarios:** un **script de carga inicial versionado** crea los usuarios sintéticos en Supabase Auth y les asigna su rol. No se construye una pantalla de administración. La administración de usuarios en producción (alta, baja, cambio de rol, integración con el directorio institucional) queda documentada en el informe de brechas.

3. **El inicio de sesión pasa por la API:** la app envía usuario y clave a `POST /auth/login` de la API. La API los valida contra Supabase Auth, registra el intento en la bitácora (exitoso o fallido), aplica el bloqueo por intentos fallidos y devuelve el token a la app. La renovación y el cierre de sesión también pasan por la API. **Esto ajusta el ADR-0001: la app no habla directamente con Supabase en ningún caso.**

4. En cada solicitud, la API valida la firma, el emisor y el vencimiento del JWT, y resuelve el rol del usuario en el servidor. Si el rol no está permitido, responde 403 y registra el intento en la bitácora (HU-02 E2).

5. El tiempo de inactividad (PA #18) y el número de intentos y la duración del bloqueo (PA #19) son parámetros configurables. Sus valores provisionales se fijan en el ADR de umbrales.

## Alternativas consideradas

- **Dos roles (agente y revisor).** Era más simple. Se descartó porque quien toma las decisiones que quedan en la bitácora sería también quien la audita.
- **Cuatro roles (más auditor y admin).** Era lo más parecido a producción. Se descartó porque obliga a construir la administración de usuarios (C1), que no está en ninguna HU.
- **Crear usuarios desde el panel de Supabase.** Era rápido. Se descartó porque no se puede reproducir al instalar en el ambiente del MININTER y no deja rastro en la bitácora.
- **Pantalla de administración mínima.** Cerraba C1 en el prototipo. Se descartó porque agrega una HU y entre 2 y 3 días de trabajo fuera del alcance aprobado.
- **Login directo contra Supabase más un hook o trigger que escriba la bitácora.** Mantenía el ADR-0001 sin cambios. Se descartó porque la bitácora se escribiría desde dos lugares y el bloqueo por intentos quedaría en SQL o en un hook, fuera de la API.

## Consecuencias

- Todo el ciclo de sesión (login, fallo, bloqueo, renovación, cierre, 403) queda en la bitácora desde un solo lugar.
- La separación de funciones entre agente y revisor es un control contra falsos positivos (HU-06).
- **Costo:** la clave del usuario pasa por la API en tránsito (sobre HTTPS). La API nunca la guarda ni la registra, y las pruebas de seguridad deben verificar que no aparezca en logs.
- **Costo:** la API reimplementa una capa delgada sobre Supabase Auth (login, renovación, cierre de sesión), y el bloqueo por intentos se guarda en tablas propias.
- **Costo:** para cambiar un rol hay que volver a correr el script. Si el área usuaria pide gestionar usuarios durante la validación, hay que abrir una HU nueva.
- **Abierto:** si el MININTER confirma que el revisor es el mismo usuario en campo (PA #2), el rol `revisor` se fusiona con `agente` y se pierde la separación de funciones. En ese caso hay que volver a abrir este ADR.
