from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user, require_admin
from app.modules.auth import service
from app.modules.auth.schemas import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UsuarioResponse,
    UsuarioCreate,
    CambiarContraseña,
    ModuloResponse,
)

router = APIRouter(prefix="/auth", tags=["Autenticacion"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request):
    ip = request.client.host if request.client else "unknown"

    user = await service.authenticate_user(body.nombre_usuario, body.contraseña)
    if not user:
        await service.log_login_attempt(body.nombre_usuario, ip, False, "Credenciales invalidas")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
        )

    await service.log_login_attempt(body.nombre_usuario, ip, True, "Login exitoso")

    token_data = {
        "sub": str(user["id"]),
        "nombre_usuario": user["nombre_usuario"],
        "rol": user["rol"],
        "base_datos_mysql": user["base_datos_mysql"],
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        usuario=UsuarioResponse(**user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido",
        )

    user = await service.get_user_by_id(int(payload["sub"]))
    if not user or not user["activo"]:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    token_data = {
        "sub": str(user["id"]),
        "nombre_usuario": user["nombre_usuario"],
        "rol": user["rol"],
        "base_datos_mysql": user.get("base_datos_mysql"),
    }
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        usuario=UsuarioResponse(**user),
    )


@router.get("/me", response_model=UsuarioResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UsuarioResponse(**user)


@router.get("/modules", response_model=list[ModuloResponse])
async def get_modules(user: dict = Depends(get_current_user)):
    db_name = user.get("base_datos_mysql")
    if not db_name:
        return []
    modules = await service.get_user_modules(db_name)
    return [ModuloResponse(**m) for m in modules]


@router.get("/databases")
async def get_databases(user: dict = Depends(require_admin)):
    return await service.get_user_databases()


@router.post("/users", response_model=UsuarioResponse)
async def create_user(body: UsuarioCreate, user: dict = Depends(require_admin)):
    new_user = await service.create_user(
        body.nombre_usuario, body.email, body.contraseña, body.rol, body.base_datos_mysql
    )
    return UsuarioResponse(**new_user)


@router.post("/change-password")
async def change_password(
    body: CambiarContraseña, user: dict = Depends(get_current_user)
):
    ok = await service.change_password(
        user["id"], body.contraseña_actual, body.nueva_contraseña
    )
    if not ok:
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    return {"message": "Contraseña actualizada exitosamente"}
