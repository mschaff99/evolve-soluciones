from pydantic import BaseModel
from typing import Optional, Any


class F29EmpresaResponse(BaseModel):
    run_rut: str
    empresa: Optional[str] = None
    auditor: Optional[str] = None
    grupo: Optional[str] = None
    periodos: list[str] = []
    ultimo_periodo: Optional[str] = None
    total_periodos: int = 0


class F29DatosResponse(BaseModel):
    rut: str
    periodo: str
    datos: dict[str, Any] = {}
    tabla_resultados: Optional[str] = None


class F29ObservacionResponse(BaseModel):
    id: Optional[int] = None
    rut: str
    periodo: str
    observacion: Optional[str] = None
    estado: Optional[str] = None
    fecha: Optional[str] = None


class F29Filtros(BaseModel):
    auditor: Optional[str] = None
    grupo: Optional[str] = None
    periodo: Optional[str] = None
    busqueda: Optional[str] = None


class F29EstadisticasResponse(BaseModel):
    total_empresas: int = 0
    total_periodos: int = 0
    con_observaciones: int = 0
    sin_observaciones: int = 0
