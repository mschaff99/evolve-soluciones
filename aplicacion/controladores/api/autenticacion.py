"""
Controlador de Autenticación API
================================
Endpoints de autenticación con JWT para frontend React
"""
from flask import request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity
)
from marshmallow import ValidationError

from aplicacion.controladores.api import api_v1
from aplicacion.esquemas.usuario_esquema import LoginEsquema, UsuarioEsquema
from aplicacion.modelos.usuario import Usuario
from aplicacion.extensiones import bcrypt


@api_v1.route('/auth/login', methods=['POST'])
def login():
    """
    Endpoint de login para API
    
    POST /api/v1/auth/login
    {
        "nombre_usuario": "usuario",
        "contrasena": "contraseña"
    }
    
    Returns:
        JSON con tokens y datos de usuario
    """
    try:
        # Validar datos de entrada
        esquema = LoginEsquema()
        datos = esquema.load(request.get_json())
        
        # Buscar usuario
        usuario = Usuario.obtener_por_nombre_usuario(datos['nombre_usuario'])
        
        if not usuario or not usuario.verificar_contraseña(datos['contrasena']):
            return jsonify({"error": "Credenciales inválidas"}), 401
        
        if not usuario.activo:
            return jsonify({"error": "Usuario inactivo"}), 401
        
        # Crear tokens JWT
        access_token = create_access_token(identity=usuario.id)
        refresh_token = create_refresh_token(identity=usuario.id)
        
        # Actualizar último acceso
        usuario.actualizar_ultimo_acceso()
        
        # Preparar datos de usuario
        usuario_dict = usuario.to_dict()
        
        # Agregar módulos disponibles si existe la funcionalidad
        try:
            from aplicacion.modelos.modulo import Modulo
            if usuario.base_datos_mysql:
                modulos = Modulo.obtener_modulos_habilitados_bd(usuario.base_datos_mysql)
                usuario_dict['modulos'] = modulos
        except Exception as e:
            print(f"Advertencia: No se pudieron cargar módulos: {e}")
            usuario_dict['modulos'] = []
        
        # Retornar respuesta
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_sesion": "session_token",  # Para compatibilidad
            "usuario": usuario_dict
        }), 200
        
    except ValidationError as err:
        return jsonify({"error": "Datos inválidos", "detalles": err.messages}), 400
    except Exception as e:
        print(f"Error en login: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500


@api_v1.route('/auth/me', methods=['GET'])
@jwt_required()
def obtener_usuario_actual():
    """
    Obtiene datos del usuario autenticado actual
    
    GET /api/v1/auth/me
    Headers: Authorization: Bearer <token>
    
    Returns:
        JSON con datos del usuario
    """
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.obtener_por_id(usuario_id)
        
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        # Preparar datos de usuario
        usuario_dict = usuario.to_dict()
        
        # Agregar módulos disponibles
        try:
            from aplicacion.modelos.modulo import Modulo
            if usuario.base_datos_mysql:
                modulos = Modulo.obtener_modulos_habilitados_bd(usuario.base_datos_mysql)
                usuario_dict['modulos'] = modulos
        except Exception as e:
            print(f"Advertencia: No se pudieron cargar módulos: {e}")
            usuario_dict['modulos'] = []
        
        esquema = UsuarioEsquema()
        return jsonify(esquema.dump(usuario_dict)), 200
        
    except Exception as e:
        print(f"Error obteniendo usuario actual: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500


@api_v1.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Cierra sesión del usuario (invalida token en cliente)
    
    POST /api/v1/auth/logout
    Headers: Authorization: Bearer <token>
    
    Returns:
        JSON con mensaje de confirmación
    """
    return jsonify({"mensaje": "Sesión cerrada correctamente"}), 200


@api_v1.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresca el access token usando el refresh token
    
    POST /api/v1/auth/refresh
    Headers: Authorization: Bearer <refresh_token>
    
    Returns:
        JSON con nuevo access token
    """
    try:
        usuario_id = get_jwt_identity()
        nuevo_access_token = create_access_token(identity=usuario_id)
        
        return jsonify({
            "access_token": nuevo_access_token
        }), 200
        
    except Exception as e:
        print(f"Error refrescando token: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
