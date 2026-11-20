"""Nombres y formas de CONTRATO-HU-03 v3 y CONTRATO-HU-07 v2 (escritas desde el contrato)."""

from __future__ import annotations

from ayudas_hu01 import ERRORES, PALABRA_PROHIBIDA, iso_utc

RUTA_MOTIVOS = "/v1/motivos"
RUTA_PLACA = "/v1/consultas/placa"
RUTA_BITACORA = "/v1/bitacora"

PLACA_CON, PLACA_SIN, PLACA_NO_REG = "ZZA-101", "ZZB-201", "ZZZ-999"  # CONTRATO-HU-08

CATALOGO = [
    {"codigo": "control_vehicular", "descripcion": "Control vehicular"},
    {"codigo": "intervencion_policial", "descripcion": "Intervención policial"},
    {"codigo": "denuncia", "descripcion": "Denuncia"},
    {"codigo": "operativo", "descripcion": "Operativo"},
    {"codigo": "otro", "descripcion": "Otro"},
]
RESULTADOS = ("con_requisitoria", "sin_requisitoria", "placa_no_registrada")
FORMATO_REGEX = "^[A-Z0-9]{3}-[0-9]{3}$"
FORMATO_DESCRIPCION = "ABC-123 (3 letras o números, guion, 3 números)"

ERRORES.update({
    "MOTIVO_REQUERIDO": (422, None),  # dos mensajes posibles; se verifica aparte
    "PLACA_FORMATO_INVALIDO": (422, None),
    "FUENTE_NO_DISPONIBLE": (503, "No se pudo completar la consulta; intente nuevamente"),
    "FUENTE_RESPUESTA_INVALIDA": (502, "No se pudo completar la consulta; intente nuevamente"),
    "METODO_NO_PERMITIDO": (405, None),
})
MSG_SIN_MOTIVO = "Indique el motivo de la consulta"
MSG_OTRO_CORTO = "Describa el motivo (mínimo 10 caracteres)"
MSG_FORMATO = "El formato de placa no es válido. Formato esperado: "

COLUMNAS_BITACORA = ("id", "ocurrido_en", "usuario_id", "rol", "tipo_evento", "motivo",
                     "parametros", "resultado", "score", "version_modelo", "version_umbral",
                     "captura_id", "consulta_id", "codigo_error", "id_traza", "es_sintetico")
CAMPOS_REGISTRO_API = {"id", "ocurrido_en", "usuario", "rol", "tipo_evento", "motivo",
                       "parametros", "resultado", "score", "captura_id", "consulta_id",
                       "codigo_error", "es_sintetico"}
TIPOS_ITERACION = ("LOGIN_OK", "LOGIN_FALLIDO", "CUENTA_BLOQUEADA", "LOGOUT", "SESION_VENCIDA",
                   "ACCESO_DENEGADO", "CONSULTA_PLACA", "ERROR_FUENTE", "CONSULTA_BITACORA")


def consulta(placa: str, motivo: str | None = "control_vehicular", texto=None, **extra) -> dict:
    cuerpo = {"placa": placa, "motivo_codigo": motivo, "motivo_texto": texto}
    cuerpo.update(extra)
    return cuerpo


def problemas_resultado(r, placa: str, resultado: str, motivo: str = "control_vehicular",
                        texto=None) -> list[str]:
    """§2: 200 {consulta_id, placa, resultado, motivo{codigo,texto}, consultado_en (ISO UTC)}."""
    if r.estado != 200:
        return [f"estado {r.estado}: {r.texto[:300]}"]
    d = r.json()
    p = []
    if not isinstance(d.get("consulta_id"), str) or not d["consulta_id"]:
        p.append("consulta_id vacío")
    if d.get("placa") != placa:
        p.append(f"placa {d.get('placa')!r}, se esperaba {placa!r}")
    if d.get("resultado") != resultado:
        p.append(f"resultado {d.get('resultado')!r}, se esperaba {resultado!r}")
    m = d.get("motivo")
    if not isinstance(m, dict) or m.get("codigo") != motivo or m.get("texto") != texto:
        p.append(f"motivo {m!r}, se esperaba codigo={motivo!r} texto={texto!r}")
    try:
        iso_utc(d.get("consultado_en") or "")
    except (AssertionError, ValueError) as e:
        p.append(f"consultado_en: {e}")
    if PALABRA_PROHIBIDA in r.texto.lower():
        p.append("contiene la palabra prohibida")
    # Variante "Solo estado" (decisión 4): sin datos del vehículo ni de la requisitoria.
    for prohibido in ("marca", "modelo", "color", "requisitoria", "autoridad"):
        if prohibido in d:
            p.append(f"expone {prohibido!r} (variante 'Solo estado')")
    return p
