"""Simuladores de fuentes (ADR-0006). Sprint 0: solo GET /salud, sin datos ni fuentes."""

from fastapi import FastAPI

app = FastAPI(
    title="Movil Buscador Simuladores",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get("/salud")
async def salud() -> dict[str, str]:
    return {"estado": "ok"}
