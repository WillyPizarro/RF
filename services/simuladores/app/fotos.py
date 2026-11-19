"""Fotos de la galeria, cifradas con AES-GCM en el almacenamiento del simulador (ADR-0008 §2).

Entrada: el directorio SIM_FOTOS_DIR (fuera del repositorio), con archivos
<persona_id>__<n>.<jpg|png>. El almacenamiento cifrado (SIM_FOTOS_ALMACEN, un volumen) es un
espejo de ese directorio: lo que se agrega o cambia se cifra, y lo que se quita se borra.
Si SIM_FOTOS_DIR no esta definida, el almacenamiento se usa tal cual esta.

La llave (SIM_FOTOS_LLAVE, 32 bytes en base64) viene del entorno y nunca se versiona. Si falta,
se usa una llave aleatoria en memoria: las fotos se vuelven a cifrar en cada arranque.
"""

import base64
import binascii
import hashlib
import logging
import os
import re
import secrets
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

log = logging.getLogger("simuladores.fotos")

_NOMBRE_ORIGEN = re.compile(r"^(SIM-P-\d{4})__(\d{1,4})\.(jpg|png)$", re.IGNORECASE)
_NOMBRE_CIFRADO = re.compile(r"^(SIM-P-\d{4}__\d{1,4})\.(jpg|png)\.enc$")
_TIPOS = {"jpg": "image/jpeg", "png": "image/png"}
_ALMACEN_POR_DEFECTO = "/datos/fotos"
_NONCE = 12
_AAD = b"movil-buscador/galeria/v1"


@dataclass(frozen=True)
class Foto:
    foto_id: str
    persona_id: str
    numero: int
    extension: str
    ruta: Path
    huella: str  # sha256 del archivo cifrado

    @property
    def tipo(self) -> str:
        return _TIPOS[self.extension]


class AlmacenFotos:
    def __init__(self) -> None:
        self._candado = threading.Lock()
        self._llave_temporal = AESGCM.generate_key(bit_length=256)
        # Cache de lo ya verificado, para no descifrar en cada solicitud.
        self._origen_visto: dict[str, tuple[int, int]] = {}
        self._cifrado_valido: dict[str, tuple[int, int, bool]] = {}

    # --- configuracion (se lee en cada uso: sin reiniciar) -------------------------------------

    def _llave(self) -> bytes:
        texto = os.environ.get("SIM_FOTOS_LLAVE", "").strip()
        if not texto:
            return self._llave_temporal
        try:
            llave = base64.b64decode(texto, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise RuntimeError("SIM_FOTOS_LLAVE no es base64 valido") from exc
        if len(llave) != 32:
            raise RuntimeError("SIM_FOTOS_LLAVE debe tener 32 bytes")
        return llave

    @staticmethod
    def _almacen() -> Path:
        ruta = Path(os.environ.get("SIM_FOTOS_ALMACEN", "").strip() or _ALMACEN_POR_DEFECTO)
        try:
            ruta.mkdir(parents=True, exist_ok=True)
            if os.access(ruta, os.W_OK):
                return ruta
        except OSError:
            pass
        respaldo = Path(tempfile.gettempdir()) / "movil-buscador-sim-fotos"
        respaldo.mkdir(parents=True, exist_ok=True)
        return respaldo

    # --- cifrado ------------------------------------------------------------------------------

    def _cifrar(self, datos: bytes, llave: bytes) -> bytes:
        nonce = secrets.token_bytes(_NONCE)
        return nonce + AESGCM(llave).encrypt(nonce, datos, _AAD)

    def _descifrar(self, contenido: bytes, llave: bytes) -> bytes:
        return AESGCM(llave).decrypt(contenido[:_NONCE], contenido[_NONCE:], _AAD)

    @staticmethod
    def _escribir(ruta: Path, contenido: bytes) -> None:
        temporal = ruta.with_name(ruta.name + ".tmp")
        temporal.write_bytes(contenido)
        os.replace(temporal, ruta)

    # --- sincronizacion -----------------------------------------------------------------------

    def _sincronizar_origen(self, origen: Path, almacen: Path, llave: bytes, personas: set[str]) -> None:
        esperados: dict[str, Path] = {}  # nombre cifrado -> archivo de origen
        if origen.is_dir():
            for archivo in sorted(origen.iterdir()):
                coincide = _NOMBRE_ORIGEN.match(archivo.name)
                if not coincide or not archivo.is_file():
                    continue
                persona_id, numero, extension = coincide.groups()
                if persona_id not in personas:
                    continue
                extension = extension.lower()
                foto_id = f"{persona_id}__{int(numero)}"
                # Un foto_id por persona y numero: si hay jpg y png, gana el ultimo en orden.
                for ext in _TIPOS:
                    esperados.pop(f"{foto_id}.{ext}.enc", None)
                esperados[f"{foto_id}.{extension}.enc"] = archivo
        else:
            log.warning("SIM_FOTOS_DIR no existe: la galeria queda sin fotos")

        for nombre, archivo in esperados.items():
            estado = archivo.stat()
            destino = almacen / nombre
            visto = self._origen_visto.get(nombre)
            if visto == (estado.st_size, estado.st_mtime_ns) and destino.exists():
                continue
            datos = archivo.read_bytes()
            if not self._mismo_contenido(destino, datos, llave):
                self._escribir(destino, self._cifrar(datos, llave))
            self._origen_visto[nombre] = (estado.st_size, estado.st_mtime_ns)

        for archivo in almacen.iterdir():
            if archivo.name.endswith(".enc") and archivo.name not in esperados:
                archivo.unlink(missing_ok=True)
                self._origen_visto.pop(archivo.name, None)

    def _mismo_contenido(self, destino: Path, datos: bytes, llave: bytes) -> bool:
        if not destino.exists():
            return False
        try:
            return self._descifrar(destino.read_bytes(), llave) == datos
        except (InvalidTag, ValueError):
            return False

    def _indice(self, almacen: Path, llave: bytes, personas: set[str]) -> dict[str, Foto]:
        fotos: dict[str, Foto] = {}
        for archivo in sorted(almacen.iterdir()):
            coincide = _NOMBRE_CIFRADO.match(archivo.name)
            if not coincide:
                continue
            foto_id, extension = coincide.groups()
            persona_id, numero = foto_id.split("__")
            if persona_id not in personas:
                continue
            contenido = archivo.read_bytes()
            estado = archivo.stat()
            clave_cache = archivo.name
            cache = self._cifrado_valido.get(clave_cache)
            if cache and cache[:2] == (estado.st_size, estado.st_mtime_ns):
                valido = cache[2]
            else:
                try:
                    self._descifrar(contenido, llave)
                    valido = True
                except (InvalidTag, ValueError):
                    log.warning("Foto cifrada que no se puede descifrar con la llave actual: %s", foto_id)
                    valido = False
                self._cifrado_valido[clave_cache] = (estado.st_size, estado.st_mtime_ns, valido)
            if valido:
                fotos[foto_id] = Foto(
                    foto_id=foto_id,
                    persona_id=persona_id,
                    numero=int(numero),
                    extension=extension,
                    ruta=archivo,
                    huella=hashlib.sha256(contenido).hexdigest(),
                )
        return fotos

    def sincronizar(self, personas: set[str]) -> dict[str, Foto]:
        """Refleja SIM_FOTOS_DIR en el almacenamiento cifrado y devuelve las fotos disponibles."""
        with self._candado:
            llave = self._llave()
            almacen = self._almacen()
            origen = os.environ.get("SIM_FOTOS_DIR", "").strip()
            if origen:
                self._sincronizar_origen(Path(origen), almacen, llave, personas)
            return self._indice(almacen, llave, personas)

    def leer(self, foto: Foto) -> bytes:
        return self._descifrar(foto.ruta.read_bytes(), self._llave())


def fotos_por_persona(fotos: dict[str, Foto]) -> dict[str, list[str]]:
    resultado: dict[str, list[Foto]] = {}
    for foto in fotos.values():
        resultado.setdefault(foto.persona_id, []).append(foto)
    return {
        persona_id: [f.foto_id for f in sorted(lista, key=lambda f: f.numero)]
        for persona_id, lista in sorted(resultado.items())
    }


def version_galeria(fotos: dict[str, Foto]) -> str:
    resumen = hashlib.sha256()
    for foto_id in sorted(fotos):
        resumen.update(f"{foto_id}:{fotos[foto_id].huella}\n".encode())
    return "g-" + resumen.hexdigest()[:16]


almacen_fotos = AlmacenFotos()
