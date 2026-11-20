"""CONTRATO-HU-03 v3 §4 (reemplazo de la fuente por un mock del contrato) y CONTRATO-HU-02 v3 §2
(matriz de 403 SIN_PERMISO + ACCESO_DENEGADO, ahora que hay rutas por rol: HU-03 y HU-07).

§4: el mock es Prism (`stoplight/prism:5`), generado SOLO desde `contratos/fuentes/placas.yaml`,
como contenedor en la red interna del compose. La API se recrea con FUENTE_PLACAS_URL apuntando
a él (sin tocar código ni la app) y al final vuelve a infra/.env. Si la imagen no se puede
descargar, el caso queda NO VERIFICADO con el motivo (lo permite el contrato).
"""

from __future__ import annotations

import json
import subprocess
import time
import uuid

import pytest

from ayudas_hu01 import firma_error, problemas_error, tipos
from ayudas_hu03 import (
    PLACA_CON, RESULTADOS, RUTA_BITACORA, RUTA_MOTIVOS, RUTA_PLACA, consulta,
)

IMAGEN_PRISM = "stoplight/prism:5"


def _docker(*args, timeout=600):
    return subprocess.run(["docker", *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)


@pytest.fixture
def mock_placas(sistema):
    """Prism con placas.yaml en la red interna. Devuelve su URL interna."""
    sistema.configurar({})
    redes = _docker("inspect", "movil-buscador-api-1", "--format",
                    "{{json .NetworkSettings.Networks}}")
    assert redes.returncode == 0, redes.stderr
    red = next((n for n in json.loads(redes.stdout) if n.endswith("interna")), None)
    assert red, f"no se encuentra la red interna: {redes.stdout}"
    if _docker("pull", IMAGEN_PRISM).returncode != 0:
        pytest.skip(f"NO VERIFICADO: no se pudo descargar {IMAGEN_PRISM} (CONTRATO-HU-03 §4)")
    nombre = "tester-prism-" + uuid.uuid4().hex[:6]
    yaml_dir = str(sistema.raiz / "contratos" / "fuentes")
    r = _docker("run", "-d", "--rm", "--name", nombre, "--network", red,
                "-v", f"{yaml_dir}:/contratos:ro", IMAGEN_PRISM,
                "mock", "-h", "0.0.0.0", "-p", "4010", "/contratos/placas.yaml")
    assert r.returncode == 0, r.stderr
    url = f"http://{nombre}:4010"
    try:
        limite = time.monotonic() + 120
        while True:
            (p,) = sistema.lote([{"metodo": "GET", "url": f"{url}/placas/{PLACA_CON}"}])
            if p.estado is not None:
                break
            assert time.monotonic() < limite, f"Prism no arrancó: {_docker('logs', nombre).stdout[-1500:]}"
            time.sleep(2)
        sistema.configurar({"FUENTE_PLACAS_URL": url})
        yield sistema
    finally:
        _docker("rm", "-f", nombre)
        sistema.configurar({})


def test_mock_del_contrato(mock_placas):
    """§4 'Mock del contrato' (HU-08 esc. 2): con FUENTE_PLACAS_URL en el mock y la API
    reiniciada, una consulta válida responde 200 con un resultado válido."""
    tok = mock_placas.token("agente1")
    r = mock_placas.pedir("POST", RUTA_PLACA, json=consulta(PLACA_CON), token=tok)
    assert r.estado == 200, r
    assert r.json()["resultado"] in RESULTADOS, r.json()


# --- CONTRATO-HU-02 §2: matriz de 403 --------------------------------------------------------

MATRIZ = [  # (método, ruta, cuerpo, rol permitido)
    ("GET", RUTA_MOTIVOS, None, "agente"),
    ("POST", RUTA_PLACA, consulta(PLACA_CON), "agente"),
    ("GET", RUTA_BITACORA, None, "supervisor"),
]
USUARIO_DE = {"agente": "agente1", "revisor": "revisor1", "supervisor": "supervisor1"}


@pytest.mark.parametrize("metodo,ruta,cuerpo,permitido", MATRIZ, ids=[m[1] for m in MATRIZ])
@pytest.mark.parametrize("rol", ["agente", "revisor", "supervisor"])
def test_matriz_de_roles(config_defecto, metodo, ruta, cuerpo, permitido, rol):
    """CONTRATO-HU-02 §2 'Ruta de otro rol': el rol permitido pasa; los demás reciben 403
    SIN_PERMISO con ACCESO_DENEGADO (usuario_id, rol, la ruta y el método en parametros) y la
    ruta no ejecuta nada (ningún otro evento con esa traza)."""
    s = config_defecto
    s.modo_placas("normal")
    tok = s.token(USUARIO_DE[rol])
    kw = {"json": cuerpo} if cuerpo is not None else {}
    r = s.pedir(metodo, ruta, token=tok, **kw)
    if rol == permitido:
        assert r.estado == 200, r
        return
    assert problemas_error(r, "SIN_PERMISO") == []
    ev = s.eventos(r.traza)
    assert tipos(ev) == ["ACCESO_DENEGADO"], ev  # 'Sin efecto': nada más
    e = ev[0]
    assert e["usuario_id"] and e["rol"] == rol
    params = json.dumps(e["parametros"])
    assert ruta in params and metodo in params, e["parametros"]


@pytest.mark.parametrize("metodo,ruta,cuerpo,_p", MATRIZ, ids=[m[1] for m in MATRIZ])
def test_sin_token_401_antes_que_403(config_defecto, metodo, ruta, cuerpo, _p):
    """CONTRATO-HU-02 §2 'Primero autenticación': sin token → 401 NO_AUTENTICADO, sin
    ACCESO_DENEGADO."""
    kw = {"json": cuerpo} if cuerpo is not None else {}
    r = config_defecto.pedir(metodo, ruta, **kw)
    assert problemas_error(r, "NO_AUTENTICADO") == []
    assert "ACCESO_DENEGADO" not in tipos(config_defecto.eventos(r.traza))


def test_403_identico_entre_rutas(config_defecto):
    """El 403 es el mismo (código y mensaje) en todas las rutas de rol."""
    s = config_defecto
    tok = s.token("revisor1")
    a = s.pedir("GET", RUTA_MOTIVOS, token=tok)
    b = s.pedir("GET", RUTA_BITACORA, token=tok)
    assert firma_error(a) == firma_error(b)
