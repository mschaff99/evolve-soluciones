from pydantic import BaseModel
from typing import Optional


class EmpresaResponse(BaseModel):
    run_rut: str
    empresa: Optional[str] = None
    auditor: Optional[str] = None
    grupo: Optional[str] = None
    tiene_credencial: bool = False
    rut_credencial: Optional[str] = None


class EmpresaCreate(BaseModel):
    run_rut: str
    empresa: str
    auditor: Optional[str] = None
    grupo: Optional[str] = None


class EmpresaUpdate(BaseModel):
    empresa: Optional[str] = None
    auditor: Optional[str] = None
    grupo: Optional[str] = None


class EmpresaEstadisticas(BaseModel):
    total_empresas: int = 0
    total_auditores: int = 0
    total_grupos: int = 0
    con_credencial: int = 0
    sin_credencial: int = 0


class EmpresaFiltros(BaseModel):
    auditor: Optional[str] = None
    grupo: Optional[str] = None
    busqueda: Optional[str] = None
    pagina: int = 1
    por_pagina: int = 50
