from pydantic import BaseModel
from typing import Optional, Any


class DJResponse(BaseModel):
    id: Optional[int] = None
    rut: str
    empresa: Optional[str] = None
    tipo_dj: Optional[str] = None
    periodo: Optional[str] = None
    estado: Optional[str] = None
    fecha_presentacion: Optional[str] = None
    datos: dict[str, Any] = {}


class DJEmpresaResponse(BaseModel):
    run_rut: str
    empresa: Optional[str] = None
    auditor: Optional[str] = None
    grupo: Optional[str] = None
    total_dj: int = 0
    declaraciones: list[DJResponse] = []


class DJEstadisticasResponse(BaseModel):
    total_empresas: int = 0
    total_declaraciones: int = 0
    presentadas: int = 0
    pendientes: int = 0
