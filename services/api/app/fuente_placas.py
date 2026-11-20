"""Adaptador de la fuente de placas (ADR-0006 §2 y §3, ADR-0014, CONTRATO-HU-03 §3 y §4).

- URL y timeout salen de la configuracion (FUENTE_PLACAS_URL, FUENTE_TIMEOUT_S). Reemplazar la
  fuente es cambiar la URL por otra implementacion de contratos/fuentes/placas.yaml.
- Cada respuesta se valida contra el contrato de la fuente con modelos Pydantic estrictos,
  alineados con placas.yaml (Vehiculo, Requisitoria y Error).
- Caida, 5xx o timeout: un solo reintento tras ~200 ms; si vuelve a fallar, FuenteNoDisponible.
- Respuesta fuera de contrato: FuenteRespuestaInvalida, sin reintento (CONTRATO-HU-03 decision 8).
- Nunca se convierte un error en "sin requisitoria" (AGENTS.md regla 7).
"""

import asyncio
import logging
from datetime import date
from typing import Literal
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from app.config import obtener_config

log = logging.getLogger("api.fuente_placas")

ESPERA_REINTENTO_S = 0.2

ResultadoPlaca = Literal["con_requisitoria", "sin_requisitoria", "placa_no_registrada"]


class _Estricto(BaseModel):
    model_config = ConfigDict(strict=True)


class _Requisitoria(_Estricto):
    codigo: str
    motivo: str
    autoridad: str
    # format: date en el yaml; en JSON llega como texto ISO.
    fecha_emision: str

    def model_post_init(self, _contexto: object) -> None:
        date.fromisoformat(self.fecha_emision)


class _Vehiculo(_Estricto):
    placa: str
    marca: str
    modelo: str
    color: str
    tipo: str
    requisitoria_vigente: bool
    requisitoria: _Requisitoria | None
    es_sintetico: Literal[True]


class _ErrorFuente(_Estricto):
    codigo: Literal["PLACA_NO_REGISTRADA", "ERROR_SIMULADO"]
    mensaje: str


class FuenteNoDisponible(Exception):
    """Caida, 5xx o timeout, despues del reintento."""


class FuenteRespuestaInvalida(Exception):
    """La fuente respondio algo que no calza con su contrato."""


class _Reintentable(Exception):
    pass


def _interpretar(respuesta: httpx.Response) -> ResultadoPlaca:
    if respuesta.status_code >= 500:
        raise _Reintentable(f"estado {respuesta.status_code}")
    # Validacion en modo JSON: tipos estrictos de JSON (sin conversiones de texto a booleano, etc.).
    try:
        if respuesta.status_code == 200:
            vehiculo = _Vehiculo.model_validate_json(respuesta.content)
            return "con_requisitoria" if vehiculo.requisitoria_vigente else "sin_requisitoria"
        if respuesta.status_code == 404:
            error = _ErrorFuente.model_validate_json(respuesta.content)
            if error.codigo == "PLACA_NO_REGISTRADA":
                return "placa_no_registrada"
    except (ValidationError, ValueError) as exc:
        raise FuenteRespuestaInvalida("respuesta fuera de contrato") from exc
    raise FuenteRespuestaInvalida(f"estado {respuesta.status_code} no previsto")


class FuentePlacas:
    async def consultar(self, placa: str) -> ResultadoPlaca:
        """Consulta una placa ya normalizada. Lanza FuenteNoDisponible o FuenteRespuestaInvalida."""
        config = obtener_config()
        url = f"{config.fuente_placas_url}/placas/{quote(placa, safe='')}"
        async with httpx.AsyncClient(timeout=config.fuente_timeout_s) as cliente:
            for intento in (1, 2):
                try:
                    return _interpretar(await cliente.get(url, headers={"Accept": "application/json"}))
                except (_Reintentable, httpx.TimeoutException, httpx.TransportError) as exc:
                    log.warning("fuente_falla", extra={"fuente": "placas", "intento": intento, "tipo": type(exc).__name__})
                    if intento == 2:
                        raise FuenteNoDisponible(type(exc).__name__) from exc
                    await asyncio.sleep(ESPERA_REINTENTO_S)
                except FuenteRespuestaInvalida as exc:
                    log.warning("fuente_respuesta_invalida", extra={"fuente": "placas", "detalle": str(exc)})
                    raise
        raise FuenteNoDisponible("sin respuesta")  # no se alcanza


def obtener_fuente_placas() -> FuentePlacas:
    return FuentePlacas()
