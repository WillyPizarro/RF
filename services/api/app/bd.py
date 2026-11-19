"""Acceso a Postgres con SQLAlchemy 2 async + asyncpg (ADR-0012)."""

import asyncio
import weakref

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import obtener_config

# Un motor por bucle de eventos: las conexiones de asyncpg no se comparten entre bucles
# (uvicorn usa uno solo; un cliente de pruebas en proceso puede usar varios).
_motores: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, AsyncEngine]" = weakref.WeakKeyDictionary()


def obtener_motor() -> AsyncEngine:
    bucle = asyncio.get_running_loop()
    motor = _motores.get(bucle)
    if motor is None:
        config = obtener_config()
        motor = create_async_engine(
            config.database_url,
            pool_pre_ping=True,
            connect_args={"timeout": config.timeout_salud_s},
        )
        _motores[bucle] = motor
    return motor


async def bd_responde() -> None:
    """Lanza una excepcion si la base no responde."""
    async with obtener_motor().connect() as conexion:
        await conexion.execute(text("SELECT 1"))
