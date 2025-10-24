"""
Configuración principal de la aplicación Evolve Soluciones
==========================================================

Contiene todas las configuraciones necesarias para el funcionamiento
de la aplicación, incluyendo bases de datos, APIs y seguridad.
"""

import os
import secrets
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class ConfiguracionBase:
    """Configuración base compartida por todos los entornos"""

    # Configuración básica de Flask
    SECRET_KEY = os.getenv('SECRET_KEY') or 'clave-secreta-desarrollo-2024'

    # Configuración de sesiones y cookies
    SERVER_NAME = os.getenv('SERVER_NAME') or None
    SESSION_COOKIE_DOMAIN = os.getenv('SESSION_COOKIE_DOMAIN') or (f".{SERVER_NAME.split(':')[0]}" if SERVER_NAME else None)
    # Si SERVER_NAME está definido, asumimos que estamos detrás de un proxy con HTTPS
    # y las cookies deben ser seguras.
    is_proxied_https = True if SERVER_NAME else False
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', str(is_proxied_https)).lower() == 'true'
    REMEMBER_COOKIE_SECURE = os.getenv('REMEMBER_COOKIE_SECURE', str(is_proxied_https)).lower() == 'true'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = int(os.getenv('REMEMBER_COOKIE_DURATION', 86400))  # 24 horas
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_COOKIE_NAME = 'evolve_session'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 horas

    # Configuración CSRF
    WTF_CSRF_ENABLED = os.getenv('WTF_CSRF_ENABLED', 'True').lower() == 'true'
    WTF_CSRF_TIME_LIMIT = int(os.getenv('WTF_CSRF_TIME_LIMIT', 3600))  # 1 hora
    WTF_CSRF_SSL_STRICT = os.getenv('WTF_CSRF_SSL_STRICT', 'False').lower() == 'true'
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    WTF_CSRF_FIELD_NAME = 'csrf_token'
    WTF_CSRF_HEADERS = ['X-CSRFToken', 'X-CSRF-Token']

    # Configuración de PostgreSQL (Sistema de Autenticación)
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))

    # Configuración de base de datos local MySQL (Gestión Empresarial)
    DB_HOST = os.getenv('DB_HOST')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    DB_PORT = int(os.getenv('DB_PORT', 3306))

    # Configuración de base de datos remota (para consolidados)
    REMOTE_DB_HOST = os.getenv('REMOTE_DB_HOST', '192.168.0.2')
    REMOTE_DB_USER = os.getenv('REMOTE_DB_USER', 'audytax')
    REMOTE_DB_PASSWORD = os.getenv('REMOTE_DB_PASSWORD', '2904')
    REMOTE_DB_NAME = os.getenv('REMOTE_DB_NAME', 'evolve')
    REMOTE_DB_PORT = int(os.getenv('REMOTE_DB_PORT', 3306))

    # Configuración de MongoDB
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'consolidado_archivos')

    # Configuración de archivos
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_EXTENSIONS = os.getenv('UPLOAD_EXTENSIONS', '.xls,.xlsx,.csv').split(',')

    # Configuración de API de Google Sheets
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credenciales.json')
    GOOGLE_SHEETS_SCOPES = [os.getenv('GOOGLE_SHEETS_SCOPES', 'https://www.googleapis.com/auth/spreadsheets')]

    # Configuración de Google Gemini AI
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro')
    GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models'
    GEMINI_TIMEOUT = int(os.getenv('GEMINI_TIMEOUT', 120))  # 2 minutos
    REQUEST_TIMEOUT = 180  # 3 minutos para requests HTTP largos


class ConfiguracionDesarrollo(ConfiguracionBase):
    """Configuración específica para el entorno de desarrollo"""

    DEBUG = True
    TESTING = False

    # Configuración menos estricta para desarrollo
    WTF_CSRF_SSL_STRICT = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class ConfiguracionPruebas(ConfiguracionBase):
    """Configuración específica para ejecutar pruebas"""

    DEBUG = False
    TESTING = True

    # Base de datos en memoria para pruebas
    DB_NAME = 'evolve_test'

    # Desactivar CSRF para pruebas
    WTF_CSRF_ENABLED = False


class ConfiguracionProduccion(ConfiguracionBase):
    """Configuración específica para el entorno de producción"""

    DEBUG = False
    TESTING = False

    # Configuración estricta de seguridad
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True

    # Clave secreta obligatoria desde variable de entorno
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("La variable SECRET_KEY es obligatoria en producción")


# Mapeo de configuraciones por entorno
configuraciones = {
    'desarrollo': ConfiguracionDesarrollo,
    'pruebas': ConfiguracionPruebas,
    'produccion': ConfiguracionProduccion,
    'default': ConfiguracionDesarrollo
}


def obtener_configuracion(nombre_entorno=None):
    """
    Obtiene la configuración apropiada según el entorno especificado

    Args:
        nombre_entorno (str): Nombre del entorno ('desarrollo', 'pruebas', 'produccion')

    Returns:
        class: Clase de configuración correspondiente
    """
    if not nombre_entorno:
        nombre_entorno = os.getenv('FLASK_ENV', 'desarrollo')

    return configuraciones.get(nombre_entorno, configuraciones['default'])
