from pydantic import BaseModel
from typing import Optional, Any


class SituacionTributariaResponse(BaseModel):
    rut: str
    empresa: Optional[str] = None
    razon_social: Optional[str] = None
    actividades: list[dict[str, Any]] = []
    inicio_actividades: Optional[str] = None
    estado_contribuyente: Optional[str] = None
    datos_adicionales: dict[str, Any] = {}
