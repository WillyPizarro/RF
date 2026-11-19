"""DoD criterio 8 — Logs estructurados sin secretos (ADR-0014).

SPRINT0.md §5: una solicitud genera una línea de log JSON con `id_traza`; ninguna
línea contiene el valor de `DATABASE_URL` ni de otras variables secretas.
Los secretos se leen de `infra/.env` (local, no versionado).
"""

import json
import time

import pytest

from conftest import CABECERA_TRAZA, RUTA_SALUD, valores_secretos

SERVICIOS_CON_LOG = ["api", "simuladores"]


def _lineas_json(texto: str) -> list[dict]:
    lineas = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea.startswith("{"):
            continue
        try:
            obj = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            lineas.append(obj)
    return lineas


def _contiene_traza(obj: object, traza: str) -> bool:
    if isinstance(obj, dict):
        if obj.get("id_traza") == traza:
            return True
        return any(_contiene_traza(v, traza) for v in obj.values())
    if isinstance(obj, list):
        return any(_contiene_traza(v, traza) for v in obj)
    return False


@pytest.mark.parametrize("ruta", [RUTA_SALUD, "/v1/no-existe"])
def test_solicitud_genera_linea_json_con_id_traza(sistema_sano, compose, ruta):
    # When
    traza = sistema_sano.get(ruta).cabecera(CABECERA_TRAZA)
    assert traza, f"Falta {CABECERA_TRAZA}"
    # Then (los logs pueden tardar un instante en volcarse)
    for _ in range(10):
        lineas = _lineas_json(compose.logs("api"))
        if any(_contiene_traza(l, traza) for l in lineas):
            return
        time.sleep(1)
    pytest.fail(f"Ninguna línea JSON del log de api tiene id_traza={traza}")


def test_hay_secretos_que_buscar():
    """Precondición del criterio: infra/.env define DATABASE_URL."""
    assert "DATABASE_URL" in valores_secretos(), (
        "infra/.env no existe o no define DATABASE_URL: no se puede verificar el criterio 8"
    )


@pytest.mark.parametrize("servicio", SERVICIOS_CON_LOG)
def test_logs_no_contienen_secretos(sistema_sano, compose, servicio):
    # Given: hubo tráfico, incluidos errores
    sistema_sano.get(RUTA_SALUD)
    sistema_sano.get("/v1/no-existe")
    secretos = valores_secretos()
    if not secretos:
        pytest.fail("No hay secretos que buscar (falta infra/.env)")
    # Then
    texto = compose.logs(servicio)
    filtrados = [nombre for nombre, valor in secretos.items() if valor in texto]
    assert not filtrados, f"El log de {servicio} contiene el valor de: {filtrados}"
