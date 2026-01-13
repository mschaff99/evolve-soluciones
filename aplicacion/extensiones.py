"""
Extensiones globales de Flask
============================
Centraliza la inicialización de extensiones Flask para evitar imports circulares
"""
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_compress import Compress
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Instanciar extensiones globales
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()
compress = Compress()
cors = CORS()
jwt = JWTManager()


def inicializar_extensiones_api(app):
    """
    Inicializa extensiones para API REST con JWT
    
    Args:
        app: Instancia de Flask
    """
    # JWT para autenticación de API
    jwt.init_app(app)
    
    # CORS para permitir requests desde frontend React
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",      # React dev server
                "http://localhost:5173",      # Vite dev server
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })
    
    # Bcrypt para hashing de contraseñas
    bcrypt.init_app(app)
    
    # Compress para compresión Gzip de respuestas
    compress.init_app(app)
    
    print("✅ Extensiones de API inicializadas")
