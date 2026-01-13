"""
Configuración JWT
================
Configuración para Flask-JWT-Extended
"""
import os
from datetime import timedelta


class ConfiguracionJWT:
    """Configuración JWT para autenticación de API"""
    
    # Clave secreta para firmar tokens JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', os.getenv('SECRET_KEY', 'jwt-secret-key'))
    
    # Duración de tokens
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Ubicación de tokens
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Mensajes de error
    JWT_ERROR_MESSAGE_KEY = 'mensaje'
    
    @staticmethod
    def aplicar_configuracion(app):
        """
        Aplica la configuración JWT a la aplicación Flask
        
        Args:
            app: Instancia de Flask
        """
        app.config['JWT_SECRET_KEY'] = ConfiguracionJWT.JWT_SECRET_KEY
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = ConfiguracionJWT.JWT_ACCESS_TOKEN_EXPIRES
        app.config['JWT_REFRESH_TOKEN_EXPIRES'] = ConfiguracionJWT.JWT_REFRESH_TOKEN_EXPIRES
        app.config['JWT_TOKEN_LOCATION'] = ConfiguracionJWT.JWT_TOKEN_LOCATION
        app.config['JWT_HEADER_NAME'] = ConfiguracionJWT.JWT_HEADER_NAME
        app.config['JWT_HEADER_TYPE'] = ConfiguracionJWT.JWT_HEADER_TYPE
        
        print("✅ Configuración JWT aplicada")
