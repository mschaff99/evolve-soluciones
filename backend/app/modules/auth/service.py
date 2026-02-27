from typing import Optional
from datetime import datetime, timezone

from app.core.database import get_pg_connection, mysql_query
from app.core.security import verify_password, hash_password


async def authenticate_user(nombre_usuario: str, contraseña: str) -> Optional[dict]:
    async with get_pg_connection() as conn:
        user = await conn.fetchrow(
            """
            SELECT id, nombre_usuario, email, rol, base_datos_mysql,
                   activo, "hash_contraseña"
            FROM auth.usuarios WHERE nombre_usuario = $1
            """,
            nombre_usuario,
        )

    if not user:
        return None

    if not user["activo"]:
        return None

    if not verify_password(contraseña, user["hash_contraseña"]):
        return None

    # Validate MySQL access
    auditor_mysql = None
    tipo_usuario_mysql = None

    if user["base_datos_mysql"]:
        try:
            mysql_user = await mysql_query(
                user["base_datos_mysql"],
                "SELECT auditor, tipo_usuario FROM usuarios_acceso WHERE usuario = %s AND estado = 'V' LIMIT 1",
                (nombre_usuario,),
                fetch_one=True,
            )
            if mysql_user:
                auditor_mysql = mysql_user.get("auditor")
                tipo_usuario_mysql = mysql_user.get("tipo_usuario")
        except Exception:
            pass

    # Update last access
    async with get_pg_connection() as conn:
        await conn.execute(
            "UPDATE auth.usuarios SET fecha_ultimo_acceso = $1 WHERE id = $2",
            datetime.now(timezone.utc),
            user["id"],
        )

    return {
        "id": user["id"],
        "nombre_usuario": user["nombre_usuario"],
        "email": user["email"],
        "rol": user["rol"],
        "base_datos_mysql": user["base_datos_mysql"],
        "activo": user["activo"],
        "auditor_mysql": auditor_mysql,
        "tipo_usuario_mysql": tipo_usuario_mysql,
    }


async def get_user_by_id(user_id: int) -> Optional[dict]:
    async with get_pg_connection() as conn:
        user = await conn.fetchrow(
            """
            SELECT id, nombre_usuario, email, rol, base_datos_mysql, activo
            FROM auth.usuarios WHERE id = $1
            """,
            user_id,
        )
    return dict(user) if user else None


async def create_user(
    nombre_usuario: str,
    email: str,
    contraseña: str,
    rol: str,
    base_datos_mysql: str,
) -> dict:
    hashed = hash_password(contraseña)
    async with get_pg_connection() as conn:
        user_id = await conn.fetchval(
            """
            INSERT INTO auth.usuarios (nombre_usuario, email, "hash_contraseña", rol, base_datos_mysql)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            nombre_usuario,
            email,
            hashed,
            rol,
            base_datos_mysql,
        )
    return await get_user_by_id(user_id)


async def change_password(user_id: int, current_password: str, new_password: str) -> bool:
    async with get_pg_connection() as conn:
        user = await conn.fetchrow(
            'SELECT "hash_contraseña" FROM auth.usuarios WHERE id = $1',
            user_id,
        )
    if not user or not verify_password(current_password, user["hash_contraseña"]):
        return False

    hashed = hash_password(new_password)
    async with get_pg_connection() as conn:
        await conn.execute(
            'UPDATE auth.usuarios SET "hash_contraseña" = $1 WHERE id = $2',
            hashed,
            user_id,
        )
    return True


async def get_user_modules(db_name: str) -> list[dict]:
    async with get_pg_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT ms.id, ms.codigo, ms.nombre, ms.descripcion,
                   ms.icono, ms.orden_menu, ms.url_base, ms.activo
            FROM auth.modulos_sistema ms
            JOIN auth.modulos_habilitados_bd mh ON ms.id = mh.id_modulo
            WHERE mh.nombre_base_datos = $1 AND ms.activo = true
            ORDER BY ms.orden_menu
            """,
            db_name,
        )
    return [dict(r) for r in rows]


async def get_user_databases() -> list[dict]:
    async with get_pg_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT id, nombre_base_datos, nombre_cliente, rut_cliente, estado, plan, activo
            FROM auth.bases_datos_mysql
            WHERE activo = true
            ORDER BY nombre_cliente
            """
        )
    return [dict(r) for r in rows]


async def log_login_attempt(
    nombre_usuario: str, ip: str, exitoso: bool, mensaje: str = ""
):
    try:
        async with get_pg_connection() as conn:
            await conn.execute(
                """
                INSERT INTO auth.intentos_login (nombre_usuario, direccion_ip, exitoso, mensaje)
                VALUES ($1, $2, $3, $4)
                """,
                nombre_usuario,
                ip,
                exitoso,
                mensaje,
            )
    except Exception:
        pass
