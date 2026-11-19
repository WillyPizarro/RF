"""Acceso a Postgres con SQLAlchemy 2 async + asyncpg (ADR-0012)."""

from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import obtener_config


@lru_cache
def obtener_motor() -> AsyncEngine:
    config = obtener_config()
    return create_async_engine(
        config.database_url,
        pool_pre_ping=True,
        connect_args={"timeout": config.timeout_salud_s},
    )


async def bd_responde() -> None:
    """Lanza una excepcion si la base no responde."""
    async with obtener_motor().connect() as conexion:
        await conexion.execute(text("SELECT 1"))
