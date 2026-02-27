from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.core.dependencies import get_current_user
from app.modules.empresas import service
from app.modules.empresas.schemas import (
    EmpresaResponse,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaEstadisticas,
)

router = APIRouter(prefix="/empresas", tags=["Empresas"])


def _get_db(user: dict, base_datos: Optional[str] = None) -> str:
    db = base_datos or user.get("base_datos_mysql")
    if not db:
        raise HTTPException(status_code=400, detail="Base de datos no especificada")
    if user["rol"] != "administrador" and db != user.get("base_datos_mysql"):
        raise HTTPException(status_code=403, detail="Sin acceso a esta base de datos")
    return db


@router.get("/")
async def list_empresas(
    base_datos: Optional[str] = None,
    auditor: Optional[str] = None,
    grupo: Optional[str] = None,
    busqueda: Optional[str] = None,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    usuario_auditor = None
    if user["rol"] != "administrador":
        usuario_auditor = user.get("auditor_mysql") or user.get("nombre_usuario")

    return await service.get_empresas(
        db, auditor=auditor, grupo=grupo, busqueda=busqueda,
        usuario_auditor=usuario_auditor, pagina=pagina, por_pagina=por_pagina,
    )


@router.get("/estadisticas", response_model=EmpresaEstadisticas)
async def get_estadisticas(
    base_datos: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    usuario_auditor = None
    if user["rol"] != "administrador":
        usuario_auditor = user.get("auditor_mysql") or user.get("nombre_usuario")
    return await service.get_estadisticas(db, usuario_auditor)


@router.get("/auditores")
async def get_auditores(
    base_datos: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    return await service.get_auditores(db)


@router.get("/grupos")
async def get_grupos(
    base_datos: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    return await service.get_grupos(db)


@router.get("/{rut}", response_model=EmpresaResponse)
async def get_empresa(
    rut: str,
    base_datos: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    empresa = await service.get_empresa_by_rut(db, rut)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return empresa


@router.post("/", response_model=EmpresaResponse, status_code=201)
async def create_empresa(
    body: EmpresaCreate,
    base_datos: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    existing = await service.get_empresa_by_rut(db, body.run_rut)
    if existing:
        raise HTTPException(status_code=409, detail="Empresa ya existe con ese RUT")
    return await service.create_empresa(db, body.model_dump())


@router.put("/{rut}", response_model=EmpresaResponse)
async def update_empresa(
    rut: str,
    body: EmpresaUpdate,
    base_datos: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    existing = await service.get_empresa_by_rut(db, rut)
    if not existing:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return await service.update_empresa(db, rut, body.model_dump(exclude_none=True))


@router.delete("/{rut}")
async def delete_empresa(
    rut: str,
    base_datos: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    db = _get_db(user, base_datos)
    existing = await service.get_empresa_by_rut(db, rut)
    if not existing:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    await service.delete_empresa(db, rut)
    return {"message": "Empresa eliminada"}
