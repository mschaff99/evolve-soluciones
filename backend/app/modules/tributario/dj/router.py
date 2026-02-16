from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.core.dependencies import get_current_user
from app.modules.tributario.dj import service

router = APIRouter(prefix="/dj", tags=["Declaraciones Juradas"])


def _get_db(user: dict, base_datos: Optional[str] = None) -> str:
    db = base_datos or user.get("base_datos_mysql")
    if not db:
        raise HTTPException(status_code=400, detail="Base de datos no especificada")
    if user["rol"] != "administrador" and db != user.get("base_datos_mysql"):
        raise HTTPException(status_code=403, detail="Sin acceso a esta base de datos")
    return db


@router.get("/empresas")
async def list_empresas_dj(
    base_datos: Optional[str] = None,
    auditor: Optional[str] = None,
    grupo: Optional[str] = None,
    busqueda: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    usuario_auditor = None
    if user["rol"] != "administrador":
        usuario_auditor = user.get("auditor_mysql") or user.get("nombre_usuario")
    return await service.get_empresas_con_dj(
        db, auditor=auditor, grupo=grupo, busqueda=busqueda,
        usuario_auditor=usuario_auditor,
    )


@router.get("/empresa/{rut}")
async def get_dj_empresa(
    rut: str,
    base_datos: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    return await service.get_dj_por_rut(db, rut)


@router.get("/estadisticas")
async def get_estadisticas(
    base_datos: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    usuario_auditor = None
    if user["rol"] != "administrador":
        usuario_auditor = user.get("auditor_mysql") or user.get("nombre_usuario")
    return await service.get_estadisticas(db, usuario_auditor)
