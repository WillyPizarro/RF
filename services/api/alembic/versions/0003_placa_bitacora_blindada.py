"""Consulta de placa y bitacora de solo insercion (HU-03, HU-07).

- motivo_catalogo: catalogo configurable de motivos (ADR-0011, provisional PA #21). "otro" va
  siempre al final de la lista.
- consulta: una fila por consulta (TECH-DESIGN, modelo de datos). Nunca guarda imagenes.
- api_app: rol con el que la API se conecta a Postgres (ADR-0005 §1). Se crea sin login si no
  existe; la clave la fija app.migrar desde API_APP_CLAVE, nunca esta migracion.
- bitacora: api_app solo tiene INSERT y SELECT; un trigger rechaza UPDATE, DELETE y TRUNCATE para
  cualquier rol, incluido el dueño (CONTRATO-HU-07 §1, decision 2).

Ninguna migracion posterior puede quitar estos triggers sin un ADR nuevo (ADR-0005 §1).

Revision ID: 0003_placa_bitacora_blindada
Revises: 0002_sesion_bitacora
Create Date: 2026-11-19
"""

from alembic import op

revision = "0003_placa_bitacora_blindada"
down_revision = "0002_sesion_bitacora"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE motivo_catalogo (
            codigo text PRIMARY KEY,
            descripcion text NOT NULL,
            activo boolean NOT NULL DEFAULT true,
            orden integer NOT NULL DEFAULT 100
        )
        """
    )
    op.execute(
        """
        INSERT INTO motivo_catalogo (codigo, descripcion, orden) VALUES
            ('control_vehicular', 'Control vehicular', 10),
            ('intervencion_policial', 'Intervención policial', 20),
            ('denuncia', 'Denuncia', 30),
            ('operativo', 'Operativo', 40),
            ('otro', 'Otro', 1000)
        """
    )
    op.execute(
        """
        CREATE TABLE consulta (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tipo text NOT NULL CHECK (tipo IN ('placa', 'rostro')),
            agente_id uuid NOT NULL REFERENCES usuario_perfil (id),
            motivo_codigo text NOT NULL,
            motivo_texto text NULL,
            placa text NULL,
            resultado text NOT NULL,
            estado text NOT NULL
                CHECK (estado IN ('completada', 'pendiente_revision', 'revisada', 'vencida', 'error')),
            version_modelo text NULL,
            version_umbral text NULL,
            creada_en timestamptz NOT NULL DEFAULT now(),
            es_sintetico boolean NOT NULL DEFAULT true
        )
        """
    )
    op.execute("CREATE INDEX consulta_agente_id_idx ON consulta (agente_id)")

    # Indices para los filtros y el cursor de GET /v1/bitacora (ADR-0005 §3).
    op.execute("CREATE INDEX bitacora_orden_idx ON bitacora (ocurrido_en DESC, id DESC)")
    op.execute("CREATE INDEX bitacora_tipo_evento_idx ON bitacora (tipo_evento)")

    # Solo insercion, para cualquier rol (incluido el dueño de la tabla).
    op.execute(
        """
        CREATE FUNCTION bitacora_solo_insercion() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'bitacora es de solo insercion (% rechazado)', TG_OP
                USING ERRCODE = 'insufficient_privilege';
        END
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER bitacora_sin_modificar
        BEFORE UPDATE OR DELETE ON bitacora
        FOR EACH ROW EXECUTE FUNCTION bitacora_solo_insercion()
        """
    )
    op.execute(
        """
        CREATE TRIGGER bitacora_sin_truncar
        BEFORE TRUNCATE ON bitacora
        FOR EACH STATEMENT EXECUTE FUNCTION bitacora_solo_insercion()
        """
    )

    # Rol de la API. Sin login hasta que app.migrar le fije la clave (API_APP_CLAVE).
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'api_app') THEN
                CREATE ROLE api_app NOLOGIN;
            END IF;
        END
        $$
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            EXECUTE format('GRANT CONNECT ON DATABASE %I TO api_app', current_database());
        END
        $$
        """
    )
    op.execute("GRANT USAGE ON SCHEMA public TO api_app")
    op.execute("REVOKE ALL ON bitacora FROM api_app")
    op.execute("GRANT SELECT, INSERT ON bitacora TO api_app")
    op.execute("GRANT SELECT ON usuario_perfil, motivo_catalogo, alembic_version TO api_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON control_acceso, sesion, consulta TO api_app")


def downgrade() -> None:
    op.execute("REVOKE ALL ON usuario_perfil, motivo_catalogo, alembic_version FROM api_app")
    op.execute("REVOKE ALL ON control_acceso, sesion, consulta, bitacora FROM api_app")
    op.execute("REVOKE USAGE ON SCHEMA public FROM api_app")
    op.execute(
        """
        DO $$
        BEGIN
            EXECUTE format('REVOKE CONNECT ON DATABASE %I FROM api_app', current_database());
        END
        $$
        """
    )
    op.execute("DROP TRIGGER bitacora_sin_truncar ON bitacora")
    op.execute("DROP TRIGGER bitacora_sin_modificar ON bitacora")
    op.execute("DROP FUNCTION bitacora_solo_insercion()")
    op.execute("DROP INDEX bitacora_tipo_evento_idx")
    op.execute("DROP INDEX bitacora_orden_idx")
    op.execute("DROP TABLE consulta")
    op.execute("DROP TABLE motivo_catalogo")
