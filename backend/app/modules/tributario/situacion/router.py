from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.core.dependencies import get_current_user
from app.modules.tributario.situacion import service

router = APIRouter(prefix="/situacion-tributaria", tags=["Situacion Tributaria"])


def _get_db(user: dict, base_datos: Optional[str] = None) -> str:
    db = base_datos or user.get("base_datos_mysql")
    if not db:
        raise HTTPException(status_code=400, detail="Base de datos no especificada")
    if user["rol"] != "administrador" and db != user.get("base_datos_mysql"):
        raise HTTPException(status_code=403, detail="Sin acceso a esta base de datos")
    return db


@router.get("/empresas")
async def list_empresas(
    base_datos: Optional[str] = None,
    busqueda: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    usuario_auditor = None
    if user["rol"] != "administrador":
        usuario_auditor = user.get("auditor_mysql") or user.get("nombre_usuario")
    return await service.get_empresas_con_situacion(db, usuario_auditor, busqueda)


@router.get("/{rut}")
async def get_situacion(
    rut: str,
    base_datos: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    situacion = await service.get_situacion_tributaria(db, rut)
    if not situacion:
        raise HTTPException(status_code=404, detail="Situacion tributaria no encontrada")
    return situacion
