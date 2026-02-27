from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.core.dependencies import get_current_user
from app.modules.tributario.f29 import service

router = APIRouter(prefix="/f29", tags=["Formulario 29"])


def _get_db(user: dict, base_datos: Optional[str] = None) -> str:
    db = base_datos or user.get("base_datos_mysql")
    if not db:
        raise HTTPException(status_code=400, detail="Base de datos no especificada")
    if user["rol"] != "administrador" and db != user.get("base_datos_mysql"):
        raise HTTPException(status_code=403, detail="Sin acceso a esta base de datos")
    return db


@router.get("/empresas")
async def list_empresas_f29(
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

    return await service.get_empresas_con_periodos(
        db, auditor=auditor, grupo=grupo, busqueda=busqueda,
        usuario_auditor=usuario_auditor,
    )


@router.get("/datos/{rut}/{periodo}")
async def get_datos_f29(
    rut: str,
    periodo: str,
    base_datos: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    datos = await service.get_datos_f29(db, rut, periodo)
    if not datos:
        raise HTTPException(status_code=404, detail="Datos F29 no encontrados")
    return datos


@router.get("/observaciones/{rut}/{periodo}")
async def get_observaciones(
    rut: str,
    periodo: str,
    base_datos: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    return await service.get_observaciones(db, rut, periodo)


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


@router.get("/periodos")
async def get_periodos(
    base_datos: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    return await service.get_periodos_disponibles(db)
