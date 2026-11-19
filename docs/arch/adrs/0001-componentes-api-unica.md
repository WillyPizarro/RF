# ADR 0001: API propia como único punto de entrada de la app

## Estado

Aceptado (2026-11-18)

## Contexto

El prototipo tiene cinco módulos: seguridad, placas, biometría, trazabilidad e interoperabilidad (PRD › Componente 2). Tres requisitos condicionan cómo se conectan los componentes:

- HU-08 E1: "la app no se conecta directo al simulador". HU-08 E2: cambiar un simulador por otra implementación no debe requerir cambios en la app.
- HU-02, supuestos: "el control se aplica en el servicio (backend), no solo ocultando botones en la app".
- HU-07: cada consulta, decisión y error queda en la bitácora, y nadie puede modificar los registros. Si las escrituras salen de varios lugares, aparecen huecos en la bitácora.

También pesa el PA #8: al cierre, el MININTER recibe el código y el manual para instalarlo en su ambiente. Por eso conviene depender lo menos posible de un servicio en la nube que no se pueda reemplazar.

Proyecto greenfield. Plazo total de 30 a 40 días.

## Decisión

La app móvil solo habla con una **API propia (FastAPI)**, que es el único punto de entrada. La API se encarga de:

- validar el token de sesión y el rol en cada solicitud;
- consultar los simuladores (o, más adelante, las fuentes reales) mediante adaptadores con contrato;
- invocar el motor biométrico;
- escribir la bitácora.

Supabase se usa solo para dos cosas: **Auth** (emitir y renovar el token) y **Postgres** (datos y bitácora). La app no lee ni escribe tablas de Supabase directamente. El ADR-0003 extiende esto al login: la app no habla con Supabase en ningún caso, y el inicio de sesión, la renovación y el cierre de sesión también pasan por la API.

```
[App Expo] ──HTTPS + JWT──► [API FastAPI] ──► [Motor biométrico]
                                │  └────────► [Simuladores con contrato]
                                ▼
                     [Supabase: Auth + Postgres]
```

## Alternativas consideradas

- **App directo a Supabase (PostgREST con RLS y Edge Functions) más FastAPI solo para biometría.** Era la opción más rápida de construir. Se descartó porque el control de acceso queda repartido entre políticas RLS, Edge Functions y FastAPI; la bitácora se escribe desde dos lugares, lo que dificulta garantizar HU-07; y el prototipo queda atado a Supabase, lo que complica la entrega al MININTER.
- **Monolito FastAPI con autenticación propia y Postgres en contenedor.** Era la opción más portable. Se descartó porque obliga a construir a mano el login, el bloqueo por intentos fallidos y la renovación de sesión, días que no caben en el plazo. Queda documentada como camino de migración si el MININTER no acepta Supabase (ver Consecuencias).

## Consecuencias

- Hay un solo lugar donde aplicar el rol (HU-02) y escribir la bitácora (HU-07). Las pruebas de seguridad atacan una sola superficie.
- Cambiar un simulador por la fuente real se hace en un adaptador de la API, sin tocar la app (HU-08 E2).
- **Costo:** hay que escribir y mantener más código de backend que en la opción de Supabase directo (endpoints, validación, adaptadores), y cada pantalla nueva necesita su endpoint.
- **Costo:** se sigue dependiendo de Supabase Auth. Para instalar en el ambiente del MININTER hay que levantar Supabase en sus propios servidores (con Docker) o reemplazar Auth por otro proveedor OIDC. La API debe validar el JWT de forma estándar (firma y emisor configurables) para que ese cambio no afecte al resto.
- La app depende de la disponibilidad de la API: si la API cae, no hay consultas. Esto es aceptable porque no se muestra un resultado sin fuente (HU-03 E3).
