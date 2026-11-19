-- Prepara el Postgres local para Supabase Auth (GoTrue), SOLO en desarrollo y pruebas
-- (CONTRATO-HU-01, decision 1). En el VPS se usa el proyecto Supabase, que ya trae todo esto.
-- Idempotente: se corre en cada arranque desde el servicio auth-preparar.
-- Variable de psql: clave_auth (la clave del usuario supabase_auth_admin, desde AUTH_DB_CLAVE).

-- Sin eco: la clave no debe quedar en los logs del contenedor.
\o /dev/null
SELECT set_config('movil.clave_auth', :'clave_auth', false);
\o

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'supabase_auth_admin') THEN
        EXECUTE format('CREATE ROLE supabase_auth_admin LOGIN NOINHERIT CREATEROLE PASSWORD %L',
                       current_setting('movil.clave_auth'));
    ELSE
        EXECUTE format('ALTER ROLE supabase_auth_admin LOGIN PASSWORD %L',
                       current_setting('movil.clave_auth'));
    END IF;
    -- Las migraciones de GoTrue otorgan permisos al rol "postgres", que aqui no es el superusuario.
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'postgres') THEN
        CREATE ROLE postgres NOLOGIN;
    END IF;
END
$$;

CREATE SCHEMA IF NOT EXISTS auth AUTHORIZATION supabase_auth_admin;
GRANT CREATE ON DATABASE :"base" TO supabase_auth_admin;
ALTER ROLE supabase_auth_admin SET search_path = auth;
