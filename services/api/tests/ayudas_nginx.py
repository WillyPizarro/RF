"""NGINX oficial con versión fijada — CONTRATO-DESPLIEGUE-01 v2.1 §1 y ADR-0018 §1, según el
arbitraje de la M-4 del encargo (vuelta 1): lo que se verifica es que el proxy sea **NGINX de la
librería oficial de Docker Hub con una versión `x.y.z` fijada**, sin importar si el compose lo
declara con `image:` o con `build:`.

Formas aceptadas para el servicio `proxy` de `docker compose config --format json`:
- `image: nginx:<x.y.z[-variante]>` (también `docker.io/nginx`, `docker.io/library/nginx` o
  `library/nginx`, con un `@sha256:` opcional);
- `build:` con un `Dockerfile` cuya **etapa final** salga de `FROM nginx:<x.y.z[-variante]>` (las
  mismas formas; si la etapa final sale de otra etapa del mismo archivo, se sigue hasta su origen).

No se aceptan `latest`, `stable`, `mainline`, una etiqueta sin versión completa (`1.30`,
`alpine`, `1-alpine`), otro registro ni una variable (`FROM nginx:${VERSION}`). Del `Dockerfile` se
leen solo las líneas `FROM` (es la interfaz que fijó la M-4).
"""

from __future__ import annotations

import re
from pathlib import Path

_IMAGEN = re.compile(
    r"(?:docker\.io/)?(?:library/)?nginx:(?P<version>\d+\.\d+\.\d+)(?P<variante>-[a-z0-9.]+)?"
    r"(?:@sha256:[0-9a-f]{64})?"
)
_FROM = re.compile(r"^\s*FROM\s+(?:--platform=\S+\s+)?(?P<imagen>\S+)(?:\s+AS\s+(?P<alias>\S+))?\s*$",
                   re.IGNORECASE)


def _version_de_imagen(imagen: str, donde: str) -> str:
    m = _IMAGEN.fullmatch(imagen.strip())
    assert m, (f"{donde}: {imagen!r} no es nginx oficial con versión x.y.z fijada "
               "(ni latest, ni stable, ni mainline, ni otra etiqueta u otro registro)")
    return m.group("version")


def _version_de_dockerfile(dockerfile: Path) -> str:
    assert dockerfile.is_file(), f"no existe el Dockerfile del proxy: {dockerfile}"
    etapas: dict[str, str] = {}
    final = ""
    for linea in dockerfile.read_text(encoding="utf-8").splitlines():
        m = _FROM.match(linea)
        if not m:
            continue
        imagen = m.group("imagen")
        while imagen.lower() in etapas:  # la etapa sale de otra etapa del mismo archivo
            imagen = etapas[imagen.lower()]
        if m.group("alias"):
            etapas[m.group("alias").lower()] = imagen
        final = imagen
    assert final, f"{dockerfile} no tiene ninguna línea FROM"
    return _version_de_imagen(final, f"FROM final de {dockerfile.name}")


def version_fijada_del_proxy(servicio: dict) -> str:
    """La versión `x.y.z` de NGINX que fija el servicio `proxy` (de `docker compose config`)."""
    build = servicio.get("build")
    if build:
        if isinstance(build, str):
            contexto, nombre = Path(build), "Dockerfile"
        else:
            contexto, nombre = Path(str(build.get("context", "."))), str(build.get("dockerfile") or "Dockerfile")
        assert "dockerfile_inline" not in (build if isinstance(build, dict) else {}), \
            "Dockerfile en línea: no se puede leer el FROM"
        ruta = Path(nombre) if Path(nombre).is_absolute() else contexto / nombre
        return _version_de_dockerfile(ruta)
    imagen = str(servicio.get("image") or "")
    assert imagen, "el proxy no declara image: ni build:"
    return _version_de_imagen(imagen, "image del proxy")


_EN_MARCHA = re.compile(r"nginx version:\s*nginx/(\d+\.\d+\.\d+)")


def version_en_marcha(salida_nginx_v: str) -> str | None:
    """La versión de la salida de `nginx -v` (va por stderr), o None si no se reconoce."""
    m = _EN_MARCHA.search(salida_nginx_v)
    return m.group(1) if m else None
