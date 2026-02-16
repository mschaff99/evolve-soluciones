from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    nombre_usuario: str
    contraseña: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: "UsuarioResponse"


class RefreshRequest(BaseModel):
    refresh_token: str


class UsuarioResponse(BaseModel):
    id: int
    nombre_usuario: str
    email: Optional[str] = None
    rol: str
    base_datos_mysql: Optional[str] = None
    activo: bool
    auditor_mysql: Optional[str] = None
    tipo_usuario_mysql: Optional[str] = None


class UsuarioCreate(BaseModel):
    nombre_usuario: str
    email: str
    contraseña: str
    rol: str = "usuario"
    base_datos_mysql: str


class CambiarContraseña(BaseModel):
    contraseña_actual: str
    nueva_contraseña: str


class ModuloResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    icono: Optional[str] = None
    orden_menu: int = 0
    url_base: Optional[str] = None
    activo: bool = True
