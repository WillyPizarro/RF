"""Migraciones y clave de api_app, antes de arrancar la API (ADR-0005 §1, ADR-0012).

Uso: python -m app.migrar (lo corre el contenedor api al arrancar, y app.cargar_usuarios).

- Aplica `alembic upgrade head` con MIGRACION_DATABASE_URL (el dueño de las tablas).
- Si hay API_APP_CLAVE, le da login a api_app con esa clave. La clave viaja como parametro y nunca
  aparece en el texto de una sentencia ni en los logs.

La API en marcha se conecta con DATABASE_URL, que usa api_app.
"""

import asyncio
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config as ConfigAlembic
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import url_migraciones


def aplicar_migraciones() -> None:
    raiz = Path(__file__).resolve().parent.parent
    configuracion = ConfigAlembic(str(raiz / "alembic.ini"))
    configuracion.set_main_option("script_location", str(raiz / "alembic"))
    command.upgrade(configuracion, "head")


async def fijar_clave_api_app(clave: str) -> None:
    motor = create_async_engine(url_migraciones())
    try:
        async with motor.begin() as cx:
            await cx.execute(text("SELECT set_config('movil.clave_api_app', :clave, true)"), {"clave": clave})
            await cx.execute(
                text(
                    "DO $$ BEGIN EXECUTE format('ALTER ROLE api_app LOGIN PASSWORD %L', "
                    "current_setting('movil.clave_api_app')); END $$"
                )
            )
    finally:
        await motor.dispose()


def main() -> int:
    if not url_migraciones():
        print("Falta MIGRACION_DATABASE_URL (o DATABASE_URL)", file=sys.stderr)
        return 1
    aplicar_migraciones()
    clave = os.environ.get("API_APP_CLAVE", "")
    if clave:
        asyncio.run(fijar_clave_api_app(clave))
        print("api_app: clave fijada")
    return 0


if __name__ == "__main__":
    sys.exit(main())
