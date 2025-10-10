import os
import socket
from flask import Flask, redirect, url_for, request, session, make_response, jsonify, flash
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_compress import Compress
from datetime import datetime

# Importaciones locales
from configuracion.configuracion import obtener_configuracion
from aplicacion.utilidades.inicializadores import inicializar_extensiones
from aplicacion.utilidades.manejadores_errores import registrar_manejadores_errores
from aplicacion.utilidades.logging_detallado import configurar_logging_detallado


def crear_aplicacion(nombre_entorno=None):
    """
    Factory function para crear la aplicación Flask

    Args:
        nombre_entorno (str): Entorno de configuración a usar

    Returns:
        Flask: Instancia configurada de la aplicación
    """
    # Crear instancia de Flask
    aplicacion = Flask(__name__,
                      template_folder='aplicacion/plantillas',
                      static_folder='aplicacion/estaticos',
                      static_url_path='/static')

    # Cargar configuración
    config_class = obtener_configuracion(nombre_entorno)
    aplicacion.config.from_object(config_class)

    # Configurar timeouts para requests largos
    aplicacion.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    aplicacion.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 horas

    # Configurar compresión Gzip
    aplicacion.config['COMPRESS_ALGORITHM'] = 'gzip'
    aplicacion.config['COMPRESS_LEVEL'] = 6  # Balance entre compresión y velocidad (1-9)
    aplicacion.config['COMPRESS_MIN_SIZE'] = 500  # Solo comprimir archivos > 500 bytes
    aplicacion.config['COMPRESS_MIMETYPES'] = [
        'text/html',
        'text/css',
        'text/xml',
        'application/json',
        'application/javascript',
        'text/javascript'
    ]

    # Inicializar compresión
    Compress(aplicacion)

    # Inicializar extensiones
    inicializar_extensiones(aplicacion)

    # Configurar sistema de logging detallado
    configurar_logging_detallado(aplicacion)

    # Registrar manejadores de errores
    registrar_manejadores_errores(aplicacion)

    # Registrar blueprints
    registrar_blueprints(aplicacion)

    # Registrar context processors
    registrar_context_processors(aplicacion)

    # Registrar middleware
    registrar_middleware(aplicacion)

    return aplicacion


def registrar_blueprints(aplicacion):
    """Registra todos los blueprints de la aplicación"""

    # Importar blueprints existentes
    from aplicacion.controladores.autenticacion import autenticacion_bp
    from aplicacion.controladores.consulta_integral_f29 import consulta_integral_f29_bp
    from aplicacion.controladores.rutas_dinamicas import rutas_dinamicas_bp

    # Importaciones comentadas - controladores pendientes de crear
    # from aplicacion.controladores.consolidado import consolidado_bp
    # from aplicacion.controladores.sesiones import sesiones_bp
    # from aplicacion.controladores.tareas import tareas_bp
    # from aplicacion.controladores.email_rutas import email_bp
    # from aplicacion.controladores.rutas_ia import ia_bp
    # from aplicacion.controladores.proveedores_rutas import proveedores_bp

    # Registrar blueprints existentes
    aplicacion.register_blueprint(autenticacion_bp)
    aplicacion.register_blueprint(consulta_integral_f29_bp)
    aplicacion.register_blueprint(rutas_dinamicas_bp)

    # Registros comentados - blueprints pendientes de crear
    # aplicacion.register_blueprint(consolidado_bp)
    # aplicacion.register_blueprint(sesiones_bp)
    # aplicacion.register_blueprint(tareas_bp)
    # aplicacion.register_blueprint(email_bp)
    # aplicacion.register_blueprint(ia_bp)
    # aplicacion.register_blueprint(proveedores_bp)


def registrar_context_processors(aplicacion):
    """Registra context processors globales para templates"""

    @aplicacion.context_processor
    def inyectar_csrf_token():
        """Hace el token CSRF disponible en todos los templates"""
        from flask_wtf.csrf import generate_csrf
        try:
            token = generate_csrf()
            if not token:
                print("WARNING: CSRF token generado está vacío")
            else:
                print(f"CSRF token generado: {token[:10]}...")
            return dict(csrf_token=lambda: token)
        except Exception as e:
            print(f"ERROR generando CSRF token: {e}")
            return dict(csrf_token=lambda: '')

    @aplicacion.context_processor
    def inyectar_usuario():
        """Inyecta información del usuario actual y año en templates"""
        return dict(
            current_user=current_user,
            current_year=datetime.now().year
        )


def registrar_middleware(aplicacion):
    """Registra middleware para la aplicación"""

    # Middleware para manejar headers de proxy (IIS, Nginx, etc.)
    # Esto permite obtener la IP real del cliente detrás de un reverse proxy
    from werkzeug.middleware.proxy_fix import ProxyFix
    aplicacion.wsgi_app = ProxyFix(
        aplicacion.wsgi_app,
        x_for=1,      # Número de proxies que agregan X-Forwarded-For
        x_proto=1,    # Confía en X-Forwarded-Proto (HTTP/HTTPS)
        x_host=1,     # Confía en X-Forwarded-Host
        x_prefix=1    # Confía en X-Forwarded-Prefix
    )

    @aplicacion.before_request
    def detectar_y_reparar_cookies_chrome():
        """
        Detecta automáticamente problemas de cookies en Chrome y los repara
        sin intervención del usuario
        """
        # Solo actuar en el endpoint de login en POST (cuando intenta autenticarse)
        if request.path == '/auth/iniciar-sesion' and request.method == 'POST':
            from aplicacion.utilidades.logging_detallado import detectar_problema_cookies_chrome

            diagnostico = detectar_problema_cookies_chrome()

            # Si detectamos el problema, limpiar sesión preventivamente
            if diagnostico['problema_detectado']:
                session.clear()
                print(f"[AUTO-FIX] Cookies corruptas detectadas y limpiadas preventivamente")

    @aplicacion.before_request
    def validar_sesion_unica():
        """
        Valida que la sesión del usuario siga siendo la única activa

        Si otro dispositivo/navegador inició sesión con el mismo usuario,
        esta sesión será invalidada automáticamente.
        """
        # Manejar preflight requests de navegadores modernos
        if request.method == 'OPTIONS':
            return '', 200

        # Solo validar si el usuario está autenticado y tenemos un token de sesión
        if current_user.is_authenticated and session.get('session_token'):
            # Evitar validar en solicitudes de recursos estáticos
            if not request.path.startswith('/static/'):
                try:
                    from aplicacion.modelos.sesion import SesionUsuario
                    from flask_login import logout_user

                    token_sesion = session.get('session_token')

                    # Validar que existe el token
                    if not token_sesion:
                        logout_user()
                        session.clear()
                        return redirect(url_for('autenticacion.iniciar_sesion'))

                    # Validar que la sesión siga siendo única y válida
                    if not SesionUsuario.validar_sesion_unica(token_sesion):
                        # La sesión ha sido invalidada por otro login
                        token_preview = token_sesion[:10] if token_sesion else "unknown"
                        print(f"[SEGURIDAD] Sesion invalidada automaticamente: {token_preview}...")

                        # Cerrar sesión del usuario actual
                        logout_user()
                        session.clear()

                        # Redirigir al login con mensaje
                        flash('Tu sesión ha sido cerrada porque iniciaste sesión desde otro dispositivo.', 'warning')
                        return redirect(url_for('autenticacion.iniciar_sesion'))

                    # Si la sesión es válida, actualizar timestamp
                    SesionUsuario.actualizar_sesion(token_sesion)

                except Exception as e:
                    print(f"Error al validar sesión única: {e}")
                    # En caso de error, mantener la sesión pero loggear el problema

    @aplicacion.after_request
    def despues_de_request(response):
        """Headers para optimizar performance y seguridad"""

        # Cache estratégico según tipo de recurso
        if request.path.startswith('/static/'):
            # Cache largo para recursos estáticos (1 año)
            # immutable indica que el recurso no cambiará
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        elif request.path.startswith('/api/'):
            # No cache para APIs
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        else:
            # No cache para páginas HTML dinámicas
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

        # Headers de seguridad
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        return response


# Crear instancia de la aplicación
app = crear_aplicacion()


# Rutas principales
@app.route('/')
def inicio():
    """Ruta principal - redirige según estado de autenticación"""
    if current_user.is_authenticated:
        # Si está autenticado, redirigir a su base de datos
        base_datos = current_user.base_datos_mysql or 'default'
        return redirect(f'/{base_datos}')
    else:
        # Si no está autenticado, redirigir a login
        return redirect(url_for('autenticacion.iniciar_sesion'))


@app.route('/salud')
def verificacion_salud():
    """Endpoint para verificar que la aplicación está funcionando"""
    return {
        "estado": "OK",
        "mensaje": "Evolve Soluciones - Sistema de Gestión Empresarial",
        "version": "1.0.0"
    }


@app.route('/diagnostico')
def diagnostico():
    """Endpoint para diagnosticar conectividad y estado del sistema"""
    import platform
    from datetime import datetime

    def obtener_ip_cliente():
        """Obtiene la IP real del cliente"""
        try:
            from aplicacion.utilidades.herramientas_ip import obtener_ip_real_cliente
            return obtener_ip_real_cliente()
        except Exception as e:
            print(f"Error al obtener IP real: {e}")
            return request.remote_addr

    cliente_ip = obtener_ip_cliente()
    info_servidor = {
        "estado": "OK",
        "timestamp": datetime.now().isoformat(),
        "plataforma_servidor": platform.system(),
        "hostname_servidor": socket.gethostname(),
        "ip_cliente": cliente_ip or "Desconocida",
        "user_agent": request.headers.get('User-Agent', 'Desconocido'),
        "metodo_conexion": (
            "Directa" if cliente_ip and cliente_ip.startswith('192.168')
            else "ZeroTier" if cliente_ip and cliente_ip.startswith('172.25')
            else "Desconocida"
        )
    }

    return info_servidor


@app.route('/api/usuario_actual')
def obtener_usuario_actual():
    """Endpoint para obtener información del usuario actual"""
    if current_user.is_authenticated:
        return {
            "id": current_user.id,
            "nombre_usuario": current_user.nombre_usuario,
            "rol": current_user.rol,
            "activo": current_user.activo
        }
    return {"error": "No autenticado"}, 401


if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()

    print("=" * 60)
    print("Evolve Soluciones - Sistema de Gestión Empresarial")
    print("=" * 60)
    print("Iniciando servidor Flask...")
    print("URLs de acceso:")
    print(f"  - Local: http://127.0.0.1:5000")
    print(f"  - Hostname: http://{hostname}:5000")
    print("=" * 60)

    # Configuración robusta para conexiones de red
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True,
        use_reloader=False,
    )
