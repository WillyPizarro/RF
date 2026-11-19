# ADR 0012: Acceso a datos con SQLAlchemy 2 (async) y migraciones con Alembic

## Estado

Aceptado (2026-11-18)

## Contexto

- ADR-0001: la API FastAPI es la única que accede a Postgres (Supabase). ADR-0005: la API usa un rol propio `api_app` con permisos mínimos, y la bitácora tiene un trigger y permisos revocados que deben quedar versionados.
- ADR-0009: al cierre se entrega un paquete que puede instalarse con Supabase en la nube, Supabase autoalojado u otro Postgres.
- ADR-0007: el contrato de la API son los modelos Pydantic, que deben mantenerse separados del esquema de la base.

## Decisión

- **Acceso a datos:** SQLAlchemy 2 en modo asíncrono (driver `asyncpg`), conectado como `api_app`. La API **no** usa `supabase-py` ni PostgREST para los datos. Usa Supabase Auth solo a través de su API de autenticación (ADR-0003).
- **Migraciones:** Alembic, en el repositorio de la API. El esquema, los roles, los `GRANT`/`REVOKE` y el trigger de la bitácora se escriben como SQL explícito (`op.execute`) dentro de las migraciones. El esquema `auth` de Supabase no se toca.
- **Modelos separados:** los modelos de base de datos (SQLAlchemy) y los del contrato (Pydantic, ADR-0007) son clases distintas.
- La versión de Python, FastAPI, SQLAlchemy y Alembic se fija en el Sprint 0 (LEAD).

## Alternativas consideradas

- **Supabase CLI con SQL directo por `asyncpg`.** Era lo más nativo de Supabase. Se descartó porque ata el despliegue a la CLI de Supabase y complica instalar sobre un Postgres sin Supabase.
- **SQLModel con Alembic.** Reducía código. Se descartó porque es menos maduro en modo asíncrono y mezcla el contrato de la API con el esquema de la base.

## Consecuencias

- Las migraciones corren igual en cualquier Postgres, así que el paquete de entrega es portable.
- La inalterabilidad de la bitácora queda versionada y se puede probar desde una base vacía.
- **Costo:** Supabase no ve estas migraciones como suyas. El panel de Supabase sirve para mirar, pero no para cambiar el esquema; cualquier cambio en el panel queda fuera de control.
- **Costo:** hay que escribir y mantener dos capas de modelos (SQLAlchemy y Pydantic), más código que con SQLModel.
