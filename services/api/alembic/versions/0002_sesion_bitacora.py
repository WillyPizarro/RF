"""Sesion, acceso y bitacora (HU-01, HU-02).

- usuario_perfil: perfil y rol de cada usuario de Supabase Auth (ADR-0003).
- control_acceso: intentos fallidos y bloqueo, por el texto del usuario exista o no (ADR-0011,
  CONTRATO-HU-01 decision 5).
- sesion: sesiones emitidas por la API, con su ultima actividad (CONTRATO-HU-01 decision 6).
- bitacora: columnas del TDD. El trigger y los permisos de solo insercion llegan en HU-07
  (CONTRATO-HU-01 decision 2).

Revision ID: 0002_sesion_bitacora
Revises: 0001_inicial
Create Date: 2026-11-19
"""

from alembic import op

revision = "0002_sesion_bitacora"
down_revision = "0001_inicial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE usuario_perfil (
            id uuid PRIMARY KEY,
            usuario text NOT NULL UNIQUE,
            nombre text NOT NULL,
            rol text NOT NULL CHECK (rol IN ('agente', 'revisor', 'supervisor')),
            activo boolean NOT NULL DEFAULT true,
            es_sintetico boolean NOT NULL DEFAULT true
        )
        """
    )
    op.execute(
        """
        CREATE TABLE control_acceso (
            usuario text PRIMARY KEY,
            usuario_id uuid NULL,
            intentos_fallidos integer NOT NULL DEFAULT 0,
            bloqueado_hasta timestamptz NULL,
            es_sintetico boolean NOT NULL DEFAULT true
        )
        """
    )
    op.execute(
        """
        CREATE TABLE sesion (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            usuario_id uuid NOT NULL REFERENCES usuario_perfil (id),
            token_renovacion_hash text NOT NULL UNIQUE,
            creada_en timestamptz NOT NULL DEFAULT now(),
            ultima_actividad timestamptz NOT NULL DEFAULT now(),
            estado text NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa', 'cerrada', 'vencida')),
            es_sintetico boolean NOT NULL DEFAULT true
        )
        """
    )
    op.execute(
        """
        CREATE TABLE bitacora (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            ocurrido_en timestamptz NOT NULL DEFAULT clock_timestamp(),
            usuario_id uuid NULL,
            rol text NULL,
            tipo_evento text NOT NULL,
            motivo text NULL,
            parametros jsonb NULL,
            resultado text NULL,
            score double precision NULL,
            version_modelo text NULL,
            version_umbral text NULL,
            captura_id uuid NULL,
            consulta_id uuid NULL,
            codigo_error text NULL,
            id_traza text NULL,
            es_sintetico boolean NOT NULL DEFAULT true
        )
        """
    )
    op.execute("CREATE INDEX bitacora_ocurrido_en_idx ON bitacora (ocurrido_en)")
    op.execute("CREATE INDEX bitacora_usuario_id_idx ON bitacora (usuario_id)")


def downgrade() -> None:
    op.execute("DROP TABLE bitacora")
    op.execute("DROP TABLE sesion")
    op.execute("DROP TABLE control_acceso")
    op.execute("DROP TABLE usuario_perfil")
