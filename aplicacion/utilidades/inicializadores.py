"""
Inicializadores de extensiones para Evolve Soluciones
=====================================================

Este módulo contiene funciones para inicializar todas las extensiones
de Flask necesarias para el funcionamiento de la aplicación.
"""

from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect, CSRFError

# Instancias globales de extensiones
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()


def inicializar_extensiones(aplicacion):
    """
    Inicializa todas las extensiones de Flask
    
    Args:
        aplicacion (Flask): Instancia de la aplicación Flask
    """
    
    # Configurar Flask-Login
    inicializar_flask_login(aplicacion)
    
    # Configurar Bcrypt para encriptación de contraseñas
    bcrypt.init_app(aplicacion)
    
    # Configurar CSRF Protection
    csrf.init_app(aplicacion)


def inicializar_flask_login(aplicacion):
    """
    Configura Flask-Login para manejo de autenticación
    
    Args:
        aplicacion (Flask): Instancia de la aplicación Flask
    """
    login_manager.init_app(aplicacion)
    login_manager.login_view = 'autenticacion.iniciar_sesion'
    login_manager.login_message = 'Debes iniciar sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'
    login_manager.session_protection = "strong"
    login_manager.remember_cookie_duration = 86400  # 24 horas
    
    # User loader para Flask-Login
    @login_manager.user_loader
    def cargar_usuario(id_usuario):
        """Carga un usuario por su ID"""
        print(f"Cargando usuario con ID: {id_usuario}")
        
        try:
            from aplicacion.modelos.usuario import Usuario
            usuario = Usuario.obtener_por_id(int(id_usuario))
            if usuario:
                print(f"Usuario cargado: {usuario.nombre_usuario}")
            else:
                print(f"Usuario no encontrado con ID: {id_usuario}")
            return usuario
        except Exception as e:
            print(f"Error cargando usuario {id_usuario}: {e}")
            return None
