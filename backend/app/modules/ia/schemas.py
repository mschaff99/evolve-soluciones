from pydantic import BaseModel
from typing import Optional, Any


class BalanceRequest(BaseModel):
    empresa_rut: str
    anio_inicio: int
    mes_inicio: int
    anio_fin: int
    mes_fin: int


class AnalisisRequest(BaseModel):
    empresa_rut: str
    datos_balance: dict[str, Any]
    tipo_analisis: str = "general"


class IAResponse(BaseModel):
    exito: bool
    mensaje: str
    datos: Optional[dict[str, Any]] = None
    analisis: Optional[str] = None
