"""Escritura en la bitacora (ADR-0005). Fail-closed: quien llama escribe dentro de su transaccion
y, si la escritura falla, no entrega el resultado.

Nunca se registran claves, tokens ni imagenes en `parametros`.
"""

import json
from typing import Any

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

_INSERTAR = text(
    """
    INSERT INTO bitacora
        (usuario_id, rol, tipo_evento, motivo, parametros, resultado, consulta_id, codigo_error, id_traza)
    VALUES (:usuario_id, :rol, :tipo_evento, :motivo, CAST(:parametros AS jsonb), :resultado,
            CAST(:consulta_id AS uuid), :codigo_error, :id_traza)
    """
)


async def registrar(
    conexion: AsyncConnection,
    request: Request,
    tipo_evento: str,
    *,
    usuario_id: Any = None,
    rol: str | None = None,
    parametros: dict[str, Any] | None = None,
    codigo_error: str | None = None,
    motivo: str | None = None,
    resultado: str | None = None,
    consulta_id: Any = None,
) -> None:
    await conexion.execute(
        _INSERTAR,
        {
            "usuario_id": str(usuario_id) if usuario_id else None,
            "rol": rol,
            "tipo_evento": tipo_evento,
            "parametros": json.dumps(parametros, ensure_ascii=False) if parametros is not None else None,
            "codigo_error": codigo_error,
            "motivo": motivo,
            "resultado": resultado,
            "consulta_id": str(consulta_id) if consulta_id else None,
            "id_traza": getattr(request.state, "id_traza", None),
        },
    )
