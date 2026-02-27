from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, require_admin
from app.modules.ia import service
from app.modules.ia.schemas import BalanceRequest, AnalisisRequest, IAResponse

router = APIRouter(prefix="/ia", tags=["Inteligencia Artificial"])


@router.get("/test-gemini")
async def test_gemini(user: dict = Depends(require_admin)):
    return await service.test_gemini_connection()


@router.post("/generar-balance", response_model=IAResponse)
async def generar_balance(
    body: BalanceRequest,
    user: dict = Depends(get_current_user),
):
    db_name = user.get("base_datos_mysql")
    if not db_name:
        return IAResponse(exito=False, mensaje="Sin base de datos asignada")

    result = await service.generar_balance(
        db_name, body.empresa_rut,
        body.anio_inicio, body.mes_inicio,
        body.anio_fin, body.mes_fin,
    )
    return IAResponse(**result)


@router.post("/analizar-balance", response_model=IAResponse)
async def analizar_balance(
    body: AnalisisRequest,
    user: dict = Depends(get_current_user),
):
    result = await service.analizar_balance(body.datos_balance, body.tipo_analisis)
    return IAResponse(**result)
