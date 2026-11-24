# ADR 0020: Keycloak al final del MVP, con Supabase Auth mientras tanto

## Estado

**Propuesto (2026-11-24).** Lo pidió el PM (PRD PA #38: "se deja para el final del MVP", decisión del humano). Si se acepta, **precisa el punto 3 del [ADR-0003](0003-autenticacion-roles.md)** (con qué se valida la clave) y el punto 2 del [ADR-0009](0009-despliegue.md). No cambia los tres roles, ni que el inicio de sesión pase por la API, ni la bitácora. Las preguntas del PA #38 (¿Keycloak del MININTER o uno propio?, ¿los roles viven en Keycloak?) y el PA #3 siguen abiertos.

## Contexto

- **PA #37 y #38:** Keycloak es el estándar de identidad del MININTER. El humano decidió dejarlo para el final del MVP y mantener Supabase Auth mientras tanto.
- **Cómo funciona hoy (evidencia):** la app nunca habla con Supabase. La API recibe usuario y clave, **solo valida la clave** contra Supabase Auth (GoTrue) con el *grant* `password`, y cierra de inmediato la sesión de Supabase. La sesión de la app la emite y la controla la API: tokens propios, inactividad, bloqueo por intentos y bitácora (`services/api/app/supabase_auth.py`, líneas 1 a 5; `services/api/app/sesion.py`). El rol se lee de la tabla propia `usuario_perfil` (`services/api/app/auth.py:94`).
- Consecuencia: **Supabase Auth es solo el verificador de claves**. Cambiarlo por Keycloak toca un módulo de la API y el script de carga, no la app ni el contrato.
- **PA #3:** ¿hay un rol de administrador que cree usuarios, o la gestión de identidades viene de un sistema institucional? Brecha 4 de TECH-DESIGN: identidad institucional, MFA y administración de usuarios.

## Decisión (propuesta)

1. **Hasta el final del MVP, Supabase Auth sigue como está** (ADR-0003). Ninguna HU nueva depende de Supabase Auth.
2. **Desde ahora, el DEV deja la verificación de la clave detrás de una interfaz** de la API (por ejemplo, `VerificadorCredenciales.verificar(usuario, clave)`), con la implementación de Supabase como la única. Es un cambio interno, sin cambio de contrato. Lo hace en la primera HU que toque la API.
3. **Al final del MVP, se agrega la implementación con Keycloak**, con el mismo patrón que hoy:
   - Un cliente confidencial de Keycloak para la API, con *Direct Access Grants* (el *grant* `password` de OAuth 2.0) habilitado solo para ese cliente.
   - La API valida la clave contra el endpoint de token del *realm* y cierra de inmediato esa sesión de Keycloak. La sesión de la app sigue siendo la de la API.
   - El bloqueo por intentos sigue en la API (ADR-0003, ADR-0011), para que haya un solo lugar que registre en la bitácora. La detección de fuerza bruta de Keycloak se deja apagada en el MVP o con un umbral mayor que el de la API, para que no bloquee antes con otra regla.
   - Los roles siguen en `usuario_perfil` mientras no se responda el PA #38b.
4. **Keycloak propio o del MININTER (PA #38a):**
   - **Propio, en el VPS del demo:** contenedor oficial de Keycloak con su propia base en Postgres, en la red interna y sin puerto público (la API es su único cliente). Los usuarios sintéticos se crean con el script de carga por la API de administración de Keycloak, o con un *realm* exportado sin claves; las claves vienen de variables de entorno (regla 8).
   - **Del MININTER:** hace falta que el VPS del demo llegue a su Keycloak por la red, un cliente registrado por ellos y usuarios de prueba que no sean personas reales. No se puede estimar sin esas respuestas.

## Alternativas consideradas

- **A. Login OIDC estándar (Authorization Code con PKCE) desde la app,** con la pantalla de inicio de sesión de Keycloak en el navegador del sistema (`flutter_appauth`). Es lo que recomienda OAuth 2.1 (el *grant* `password` está desaconsejado) y lo que pediría la seguridad de producción, con MFA. Se descarta para el MVP porque:
  - cambia la app, la pantalla AUTH-01 y los contratos de HU-01 y HU-02;
  - la API deja de ver los intentos fallidos, así que la bitácora de HU-01 E2 tendría que leer los eventos de Keycloak, y el bloqueo pasaría a Keycloak (cambia el ADR-0003);
  - suma unos 3 a 4 días al estimado.

  Queda como **recomendación para producción** (brecha 4).
- **B. Keycloak desde ahora, en lugar de Supabase Auth.** Evita hacer el trabajo al final. Se descarta porque el humano decidió dejarlo para el final y porque el PA #38a no está respondido: si se monta uno propio y luego el MININTER da el suyo, se hace dos veces.
- **C. Los roles en Keycloak (*realm roles*) y no en `usuario_perfil`.** Es lo natural si el MININTER administra las identidades (PA #3). Se descarta hasta que se responda el PA #38b, porque obliga a leer el rol del token de Keycloak en cada solicitud o a sincronizarlo al iniciar sesión.

## Relación con el PA #3

- Si el MININTER da **su** Keycloak con identidades institucionales, la respuesta al PA #3 es "la gestión de identidades viene de un sistema institucional": las altas, las bajas y la MFA son de ellos, y la brecha 4 se cierra en buena parte. Queda definir dónde viven los roles (PA #38b).
- Si se monta **uno propio** en el demo, el PA #3 sigue como hoy: sin pantalla de administración y con usuarios por script (ADR-0003). La consola de Keycloak permitiría administrar usuarios, pero se usaría solo para operar, no como funcionalidad del prototipo, y nada de lo que se haga ahí queda en la bitácora.

## Consecuencias

- El cambio de Supabase Auth a Keycloak queda acotado a un módulo de la API y al script de carga: ni la app ni el contrato cambian.
- **Costo (Keycloak propio):** unos 2 a 3 días de DEV, 1 a 1,5 del TESTER (volver a correr HU-01 y HU-02 con el verificador nuevo) y medio del LEAD. Keycloak pide unos 512 MB a 1 GB de RAM: hay que revisar que el VPS de 4 GB alcance con la API, el motor y los simuladores.
- **Costo:** el *grant* `password` hace que la clave pase por la API, como ya pasa hoy (ADR-0003). No es lo que se haría en producción, y así se documenta.
- **Riesgo:** si el Keycloak es del MININTER y no es alcanzable desde el VPS, se queda Supabase Auth hasta el cierre y Keycloak se entrega solo documentado.
- **Riesgo de cronograma:** al ser lo último, es lo primero que se cae si el plazo se aprieta. El humano decide si Keycloak se construye o se entrega documentado (ver la [evaluación](../evaluaciones/PA-37-39-stack-mininter.md)).
