"""Carga idempotente de los usuarios sinteticos (ADR-0003 §2, CONTRATO-HU-01 §6).

Uso (en el contenedor api):
  docker compose -f infra/docker-compose.yml run --rm api python -m app.cargar_usuarios

Aplica las migraciones pendientes, crea o actualiza cada usuario en Supabase Auth con la clave de
CLAVE_USUARIOS_PRUEBA y crea o actualiza su perfil (nombre, rol y si esta activo). Nunca imprime
la clave.
"""

import asyncio
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config as ConfigAlembic
from sqlalchemy import text

from app.bd import obtener_motor
from app.supabase_auth import asegurar_usuario_auth

# usuario, nombre, rol, activo
USUARIOS = (
    ("agente1", "A. Prueba", "agente", True),
    ("agente2", "B. Ensayo", "agente", True),
    ("revisor1", "R. Muestra", "revisor", True),
    ("supervisor1", "S. Ejemplo", "supervisor", True),
    ("inactivo1", "I. Ficticio", "agente", False),
)

_UPSERT = text(
    """
    INSERT INTO usuario_perfil (id, usuario, nombre, rol, activo)
    VALUES (:id, :usuario, :nombre, :rol, :activo)
    ON CONFLICT (usuario) DO UPDATE
    SET id = EXCLUDED.id, nombre = EXCLUDED.nombre, rol = EXCLUDED.rol, activo = EXCLUDED.activo
    """
)


def _migrar() -> None:
    raiz = Path(__file__).resolve().parent.parent
    configuracion = ConfigAlembic(str(raiz / "alembic.ini"))
    configuracion.set_main_option("script_location", str(raiz / "alembic"))
    command.upgrade(configuracion, "head")


async def _guardar_perfiles(ids: dict[str, str]) -> None:
    motor = obtener_motor()
    async with motor.begin() as cx:
        for usuario, nombre, rol, activo in USUARIOS:
            await cx.execute(
                _UPSERT, {"id": ids[usuario], "usuario": usuario, "nombre": nombre, "rol": rol, "activo": activo}
            )
    await motor.dispose()


def main() -> int:
    clave = os.environ.get("CLAVE_USUARIOS_PRUEBA", "")
    if len(clave) < 8:
        print("Falta CLAVE_USUARIOS_PRUEBA (minimo 8 caracteres) en infra/.env", file=sys.stderr)
        return 1
    _migrar()
    ids = {usuario: asegurar_usuario_auth(usuario, clave) for usuario, *_ in USUARIOS}
    asyncio.run(_guardar_perfiles(ids))
    for usuario, _, rol, activo in USUARIOS:
        print(f"{usuario}: rol={rol} activo={'si' if activo else 'no'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
