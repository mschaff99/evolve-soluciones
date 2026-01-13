"""
Esquemas de Usuario
==================
Esquemas Marshmallow para serialización de usuarios y autenticación
"""
from marshmallow import Schema, fields, validate


class LoginEsquema(Schema):
    """Esquema para validar datos de login"""
    nombre_usuario = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=50),
        error_messages={'required': 'El nombre de usuario es requerido'}
    )
    contrasena = fields.Str(
        required=True,
        load_only=True,
        error_messages={'required': 'La contraseña es requerida'}
    )


class UsuarioEsquema(Schema):
    """Esquema para serializar datos de usuario"""
    id = fields.Int(dump_only=True)
    nombre_usuario = fields.Str()
    email = fields.Email(allow_none=True)
    rol = fields.Str()
    activo = fields.Bool()
    base_datos_mysql = fields.Str(allow_none=True)
    fecha_creacion = fields.DateTime(dump_only=True)
    fecha_ultimo_acceso = fields.DateTime(dump_only=True, allow_none=True)
    
    # Campo virtual para módulos disponibles (se llenará en el controlador)
    modulos = fields.List(fields.Dict(), dump_only=True)
