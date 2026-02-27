from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_token
from app.core.database import get_pg_connection

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
        )

    async with get_pg_connection() as conn:
        user = await conn.fetchrow(
            """
            SELECT id, nombre_usuario, email, rol, base_datos_mysql, activo
            FROM auth.usuarios WHERE id = $1
            """,
            int(user_id),
        )

    if user is None or not user["activo"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )

    return dict(user)


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["rol"] != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador",
        )
    return user


async def require_module(module_code: str, user: dict = Depends(get_current_user)):
    db_name = user.get("base_datos_mysql")
    if not db_name:
        raise HTTPException(status_code=403, detail="Sin base de datos asignada")

    async with get_pg_connection() as conn:
        result = await conn.fetchval(
            """
            SELECT COUNT(*) FROM auth.modulos_habilitados_bd mh
            JOIN auth.modulos_sistema ms ON ms.id = mh.id_modulo
            WHERE mh.nombre_base_datos = $1 AND ms.codigo = $2 AND ms.activo = true
            """,
            db_name,
            module_code,
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Modulo '{module_code}' no habilitado para esta base de datos",
        )
    return user
