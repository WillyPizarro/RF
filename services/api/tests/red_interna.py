"""Arnés de HU-01/HU-02: la API por la red interna, la tabla `bitacora` y la configuración.

ENCARGO-HU-01-02, regla 8: el puerto 80 lo ocupa http.sys de Windows y el proxy puede no
arrancar. Lo que se puede probar dentro de la red interna se prueba ahí, en `http://api:8000`:
- HTTP: los pedidos se ejecutan DENTRO del contenedor `api` (`docker compose exec -T api python`),
  en lote, en el orden dado.
- Bitácora: `psql` dentro del contenedor `db` (CONTRATO-HU-01, decisión 2: las pruebas leen la
  tabla directamente).
- Configuración (CONTRATO-HU-01 §6): se recrea SOLO el contenedor `api` (`--no-deps`) con un
  archivo de entorno temporal, fuera del repositorio, para probar que cambiar los parámetros no
  exige tocar código. Al final de la sesión se vuelve a `infra/.env`.

Regla 7 del encargo: siempre con `infra/docker-compose.yml` + `infra/docker-compose.fotos.yml`.
Solo biblioteca estándar más pytest.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

URL_API = "http://api:8000"
CABECERA_TRAZA = "X-Id-Traza"

_TRABAJADOR = r'''
import base64, json, sys, time, urllib.request, urllib.error
def una(p):
    cab = dict(p.get("cabeceras") or {})
    datos = None
    if p.get("crudo") is not None:
        datos = base64.b64decode(p["crudo"])
        cab.setdefault("Content-Type", "application/json")
    elif "json" in p:
        datos = json.dumps(p["json"]).encode("utf-8")
        cab["Content-Type"] = "application/json"
    if p.get("token"):
        cab["Authorization"] = "Bearer " + p["token"]
    if p.get("esperar_s"):
        time.sleep(p["esperar_s"])
    req = urllib.request.Request(p["url"], data=datos, method=p.get("metodo", "GET"), headers=cab)
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=p.get("timeout", 20))
        s, h, b = r.status, dict(r.headers.items()), r.read()
    except urllib.error.HTTPError as e:
        s, h, b = e.code, dict(e.headers.items()), e.read()
    except Exception as e:
        return {"s": None, "h": {}, "b": "", "t0": t0, "error": repr(e)}
    return {"s": s, "h": h, "b": base64.b64encode(b).decode("ascii"), "t0": t0}
ps = json.loads(sys.stdin.read())
sys.stdout.write(json.dumps([una(p) for p in ps]))
'''


class RespuestaApi:
    def __init__(self, d: dict) -> None:
        self.estado: int | None = d["s"]
        self.cabeceras: dict[str, str] = d["h"]
        self.cuerpo: bytes = base64.b64decode(d["b"]) if d["b"] else b""
        self.error: str | None = d.get("error")
        self.enviada_en: float = d.get("t0", 0.0)

    @property
    def texto(self) -> str:
        return self.cuerpo.decode("utf-8", errors="replace")

    def cabecera(self, nombre: str) -> str | None:
        return next((v for k, v in self.cabeceras.items() if k.lower() == nombre.lower()), None)

    @property
    def traza(self) -> str | None:
        return self.cabecera(CABECERA_TRAZA)

    def json(self):
        return json.loads(self.texto)

    def __repr__(self) -> str:
        return f"<{self.estado} {self.texto[:300]!r}{' ' + self.error if self.error else ''}>"


def leer_env(ruta: Path) -> dict[str, str]:
    valores: dict[str, str] = {}
    if ruta.is_file():
        for ln in ruta.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                valores[k.strip().removeprefix("export ").strip()] = v.strip().strip('"').strip("'")
    return valores


class Sistema:
    """Acceso a la API (red interna), a la bitácora y a la configuración de la API."""

    def __init__(self, raiz: Path, espera_max: float) -> None:
        self.raiz = raiz
        self.espera_max = espera_max
        self.env_base = raiz / "infra" / ".env"
        self.env_actual = self.env_base
        self.overrides_actuales: dict[str, str] = {}
        self._tmp = Path(tempfile.mkdtemp(prefix="tester-hu01-"))

    # ---------------------------------------------------------------- compose
    def _base(self, env: Path | None = None) -> list[str]:
        cmd = ["docker", "compose", "-f", str(self.raiz / "infra" / "docker-compose.yml")]
        fotos = self.raiz / "infra" / "docker-compose.fotos.yml"
        if fotos.is_file():
            cmd += ["-f", str(fotos)]
        env = env or self.env_actual
        if env.is_file():
            cmd += ["--env-file", str(env)]
        return cmd

    def compose(self, *args: str, entrada: str | None = None, timeout: float = 300,
                env: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            self._base(env) + list(args), cwd=self.raiz, input=entrada, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )

    # ------------------------------------------------------------------- HTTP
    def lote(self, peticiones: list[dict]) -> list[RespuestaApi]:
        """Ejecuta las peticiones en orden dentro del contenedor api. Cada una:
        {metodo, ruta, json?, crudo(bytes)?, token?, cabeceras?, esperar_s?}."""
        ps = []
        for p in peticiones:
            q = dict(p)
            q["url"] = URL_API + q.pop("ruta")
            if isinstance(q.get("crudo"), (bytes, bytearray)):
                q["crudo"] = base64.b64encode(q["crudo"]).decode("ascii")
            ps.append(q)
        timeout = 120 + sum(float(p.get("esperar_s") or 0) for p in ps)
        r = self.compose("exec", "-T", "api", "python", "-c", _TRABAJADOR,
                         entrada=json.dumps(ps), timeout=timeout)
        assert r.returncode == 0, f"No se pudo ejecutar en api:\n{r.stderr[-2000:]}"
        return [RespuestaApi(d) for d in json.loads(r.stdout)]

    def pedir(self, metodo: str, ruta: str, **kw) -> RespuestaApi:
        return self.lote([{"metodo": metodo, "ruta": ruta, **kw}])[0]

    def login(self, usuario: str, clave: str, **kw) -> RespuestaApi:
        return self.pedir("POST", "/v1/auth/login", json={"usuario": usuario, "clave": clave}, **kw)

    def me(self, token: str | None) -> RespuestaApi:
        return self.pedir("GET", "/v1/me", token=token)

    def esperar_api(self) -> None:
        limite = time.monotonic() + self.espera_max
        ultima = None
        while time.monotonic() < limite:
            try:
                ultima = self.pedir("GET", "/v1/salud")
                if ultima.estado == 200:
                    return
            except AssertionError as e:  # el contenedor todavía no acepta exec
                ultima = e
            time.sleep(2)
        pytest.fail(f"La API no respondió /v1/salud 200 en {self.espera_max}s: {ultima}")

    # ------------------------------------------------------------- bitácora
    def sql_json(self, consulta: str) -> list[dict]:
        """Filas de una consulta, como dicts (row_to_json)."""
        env = leer_env(self.env_base)
        sql = f"select row_to_json(t) from ({consulta}) t"
        r = self.compose("exec", "-T", "db", "psql", "-U", env.get("POSTGRES_USER", "postgres"),
                         "-d", env.get("POSTGRES_DB", "postgres"), "-At", "-v", "ON_ERROR_STOP=1",
                         "-c", sql)
        assert r.returncode == 0, f"psql falló:\n{r.stderr[-2000:]}"
        return [json.loads(ln) for ln in r.stdout.splitlines() if ln.strip()]

    def eventos(self, id_traza: str) -> list[dict]:
        assert id_traza, "la respuesta no trae X-Id-Traza"
        t = id_traza.replace("'", "''")
        return self.sql_json(f"select * from bitacora where id_traza::text = '{t}' order by id")

    def bitacora_contiene(self, texto: str) -> int:
        t = texto.replace("'", "''")
        filas = self.sql_json(
            f"select count(*) as n from bitacora b where b::text like '%{t}%'")
        return filas[0]["n"]

    # --------------------------------------------------------- configuración
    def configurar(self, overrides: dict[str, str]) -> None:
        """Recrea solo `api` con infra/.env + overrides (archivo temporal fuera del repo)."""
        if overrides == self.overrides_actuales:
            return
        if overrides:
            valores = leer_env(self.env_base)
            valores.update(overrides)
            env = self._tmp / f"env-{int(time.time() * 1000)}"
            env.write_text("".join(f"{k}={v}\n" for k, v in valores.items()), encoding="utf-8")
        else:
            env = self.env_base
        r = self.compose("up", "-d", "--no-deps", "--force-recreate", "api", env=env, timeout=600)
        assert r.returncode == 0, f"No se pudo recrear api:\n{r.stderr[-2000:]}"
        self.env_actual = env
        self.overrides_actuales = dict(overrides)
        self.esperar_api()

    def clave_pruebas(self) -> str:
        clave = os.environ.get("CLAVE_USUARIOS_PRUEBA") or leer_env(self.env_base).get(
            "CLAVE_USUARIOS_PRUEBA")
        if not clave:
            pytest.fail("CLAVE_USUARIOS_PRUEBA no está en infra/.env ni en el entorno "
                        "(CONTRATO-HU-01 §6): la prueba la lee de la misma variable")
        return clave
