"""GET /v1/me: perfil y rol del usuario, resueltos en el servidor (CONTRATO-HU-02 §1, ADR-0007)."""

from fastapi import APIRouter, Depends

from app.auth import Perfil
from app.errores import respuestas_error
from app.sesion import UsuarioSesion, usuario_actual

router = APIRouter(prefix="/v1", tags=["sesion"])


@router.get("/me", response_model=Perfil, responses=respuestas_error(401, 503))
async def mi_perfil(usuario: UsuarioSesion = Depends(usuario_actual)) -> dict[str, str]:
    return usuario.perfil()
