"""API Movil Buscador: unico punto de entrada de la app (ADR-0001)."""

from fastapi import FastAPI

from app.config import obtener_config
from app.errores import registrar_manejadores
from app.auth import router as router_auth
from app.consulta_bitacora import router as router_bitacora
from app.perfil import router as router_perfil
from app.placas import router as router_placas
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
    app.include_router(router_auth)
    app.include_router(router_perfil)
    app.include_router(router_placas)
    app.include_router(router_bitacora)
    return app


app = crear_app()
