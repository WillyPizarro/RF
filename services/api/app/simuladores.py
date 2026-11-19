"""Cliente HTTP hacia el contenedor de simuladores, por la red interna (ADR-0006)."""

import httpx

from app.config import obtener_config


async def simuladores_responden() -> None:
    """Lanza una excepcion si los simuladores no responden 200 en GET /salud."""
    config = obtener_config()
    async with httpx.AsyncClient(timeout=config.timeout_salud_s) as cliente:
        respuesta = await cliente.get(f"{config.simuladores_url}/salud")
        respuesta.raise_for_status()
