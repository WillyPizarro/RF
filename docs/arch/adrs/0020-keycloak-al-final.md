# ADR 0020: Keycloak documentado para después del MVP, con Supabase Auth en el MVP

## Estado

**Aceptado (2026-11-24), ajustado por el humano.** Lo propuso el ARCH a pedido del PM (PRD PA #37 y #38), con Keycloak construido al final del MVP. El humano lo aceptó con un ajuste: **en el MVP Keycloak no se construye**. Se mantiene Supabase Auth y Keycloak se entrega **documentado**, con sus dos variantes descritas sin elegir ninguna. Los unos 3 días que costaba se usan para construir HU-09 (PRD `7cec298`).

**Precisa** el [ADR-0003](0003-autenticacion-roles.md) (punto 3, con qué se valida la clave) solo como camino documentado para después del MVP. En el MVP, el ADR-0003 y el [ADR-0009](0009-despliegue.md) (punto 2) rigen sin cambios. Siguen abiertos el PA #38 (¿Keycloak del MININTER o uno propio?, ¿los roles se definen en Keycloak?) y el PA #3.

## Contexto

- **PA #37 y #38:** Keycloak es el estándar de identidad del MININTER. **Decisión del humano (2026-11-24):** en el MVP se entrega solo documentado, sin construir.
- **Cómo funciona hoy (evidencia):** la app nunca habla con Supabase. La API recibe usuario y clave, **solo valida la clave** contra Supabase Auth (GoTrue) con el *grant* `password`, y cierra de inmediato la sesión de Supabase. La sesión de la app la emite y la controla la API: tokens propios, inactividad, bloqueo por intentos y bitácora (`services/api/app/supabase_auth.py`, líneas 1 a 5; `services/api/app/sesion.py`). El rol se lee de la tabla propia `usuario_perfil` (`services/api/app/auth.py:94`).
- Consecuencia: **Supabase Auth es solo el verificador de claves**. Cambiarlo por Keycloak después del MVP toca un módulo de la API y el script de carga, no la app ni el contrato.
- **PA #3:** ¿hay un rol de administrador que cree usuarios, o la gestión de identidades viene de un sistema institucional? Brecha 4 de TECH-DESIGN: identidad institucional, MFA y administración de usuarios.

## Decisión

1. **En el MVP, Supabase Auth sigue como está** (ADR-0003). No se construye nada de Keycloak: ni contenedor, ni cliente, ni configuración.
2. **Preparación sin costo:** cuando una HU toque el inicio de sesión de la API, el DEV deja la verificación de la clave detrás de una interfaz interna (por ejemplo, `VerificadorCredenciales.verificar(usuario, clave)`), con Supabase como la única implementación. Es un cambio interno, sin cambio de contrato, y no se abre trabajo solo para esto.
3. **Lo que se entrega documentado** (en el manual de instalación y en el informe de brechas, brecha 4): cómo reemplazar Supabase Auth por Keycloak con el mismo patrón de hoy.
   - Un cliente confidencial de Keycloak para la API, con *Direct Access Grants* (el *grant* `password` de OAuth 2.0) habilitado solo para ese cliente.
   - La API valida la clave contra el endpoint de token del *realm* y cierra de inmediato esa sesión de Keycloak. La sesión de la app sigue siendo la de la API.
   - El bloqueo por intentos sigue en la API (ADR-0003, ADR-0011), para que un solo lugar registre en la bitácora. La detección de fuerza bruta de Keycloak se deja apagada, o con un umbral mayor que el de la API, para que no bloquee antes con otra regla.
   - Para producción se recomienda el login OIDC estándar con MFA (alternativa A), que cambia la app y el ADR-0003.
4. **Las dos variantes se documentan sin elegir ninguna** (PA #38a, a responder por el MININTER):

   | | Keycloak del MININTER | Keycloak propio en el ambiente del demo |
   |---|---|---|
   | Qué es | El Keycloak institucional, con su *realm* | El contenedor oficial de Keycloak, con su propia base en Postgres, en la red interna y sin puerto público (la API es su único cliente) |
   | Usuarios | Los da el MININTER. Para el prototipo, usuarios de prueba que no sean personas reales | Usuarios sintéticos creados con el script de carga por la API de administración de Keycloak, o con un *realm* exportado sin claves. Las claves vienen de variables de entorno (regla 8) |
   | Qué hace falta | Que el ambiente llegue a su Keycloak por la red, y un cliente registrado por ellos | Unos 512 MB a 1 GB más de RAM en el servidor (revisar junto con la API, el motor y los simuladores) |
   | PA #3 | La gestión de identidades viene de un sistema institucional: altas, bajas y MFA son del MININTER, y la brecha 4 se cierra en buena parte | Sigue como hoy: usuarios por script, sin pantalla de administración. La consola de Keycloak serviría para operar, no como funcionalidad, y lo que se haga ahí no queda en la bitácora |
   | Estimado si se construye | No se puede estimar sin las respuestas sobre la red, el cliente y los usuarios | Unos 2 a 3 días de DEV, 1 a 1,5 del TESTER y medio del LEAD |

5. **Dónde viven los roles (PA #38b):** queda como **pregunta para el MININTER**. Hoy, en `usuario_perfil` (ADR-0003). Si se definen en Keycloak (*realm roles*), la API los leería del token de Keycloak al iniciar sesión y los copiaría a su sesión. Ese cambio se documenta, pero no se elige.

## Alternativas consideradas

- **A. Login OIDC estándar (Authorization Code con PKCE) desde la app,** con la pantalla de inicio de sesión de Keycloak en el navegador del sistema (`flutter_appauth`). Es lo que recomienda OAuth 2.1 (el *grant* `password` está desaconsejado) y lo que pediría la seguridad de producción, con MFA. Se descarta para el paso de Supabase a Keycloak porque cambia la app, la pantalla AUTH-01 y los contratos de HU-01 y HU-02; porque la API dejaría de ver los intentos fallidos, y la bitácora de HU-01 E2 tendría que leer los eventos de Keycloak; y porque el bloqueo pasaría a Keycloak (cambia el ADR-0003). Suma unos 3 a 4 días. Queda como **recomendación para producción** (brecha 4).
- **B. Construir Keycloak al final del MVP** (la propuesta original del ARCH). Se descarta por decisión del humano: sus días se usan para HU-09.
- **C. Keycloak desde ahora, en lugar de Supabase Auth.** Se descarta: el PA #38a no está respondido, y si se monta uno propio y luego el MININTER da el suyo, se hace dos veces.

## Consecuencias

- El MVP no gasta días en identidad. HU-09 entra al MVP.
- El cambio a Keycloak queda descrito y acotado a un módulo de la API y al script de carga: ni la app ni el contrato cambian.
- **Costo:** el MVP se entrega con un componente que no es del stack del MININTER (Supabase Auth). Hay que decirlo en la entrega y en la brecha 4.
- **Costo:** el *grant* `password` hace que la clave pase por la API, como ya pasa hoy (ADR-0003). No es lo que se haría en producción, y así se documenta.
- **Riesgo:** el documento de Keycloak no se prueba en el MVP. Los pasos quedan marcados **NO VERIFICADO** hasta que alguien los ejecute.

## Decisiones del humano (2026-11-24, vía PM)

1. Se acepta con un ajuste: en el MVP Keycloak no se construye y sigue Supabase Auth.
2. El documento describe las dos variantes (Keycloak del MININTER o propio) sin elegir ninguna.
3. Dónde viven los roles (en Keycloak o en la base de la API) queda como pregunta del PA #38.
4. Los unos 3 días de Keycloak se usan para construir HU-09.
