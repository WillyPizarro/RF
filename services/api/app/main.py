"""API Movil Buscador: unico punto de entrada de la app (ADR-0001)."""

from fastapi import FastAPI

from app.config import obtener_config
from app.errores import registrar_manejadores
from app.salud import router as router_salud
from app.traza import registrar_middleware_traza


def crear_app() -> FastAPI:
    app = FastAPI(
        title="Movil Buscador API",
        version=obtener_config().version,
        docs_url=None,
        redoc_url=None,
    )
    registrar_manejadores(app)
    registrar_middleware_traza(app)
    app.include_router(router_salud)
    return app


app = crear_app()
