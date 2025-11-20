"""
Sistema de logging detallado para diagnóstico de autenticación y sesiones

Este módulo proporciona funciones especializadas para registrar eventos
relacionados con autenticación, errores CSRF, sesiones y accesos bloqueados.
Permite diagnosticar problemas como usuarios con navegadores bloqueados.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from flask import request, session
from flask_login import current_user


def configurar_logging_detallado(app):
    """
    Configura sistema de logging detallado con archivos especializados

    Args:
        app: Instancia de Flask
    """
    # Crear carpeta logs si no existe
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # Formato detallado para todos los logs
    formato_detallado = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. Logger de autenticación (login/logout)
    logger_autenticacion = logging.getLogger('autenticacion')
    logger_autenticacion.setLevel(logging.INFO)
    handler_autenticacion = RotatingFileHandler(
        os.path.join(logs_dir, 'autenticacion.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    handler_autenticacion.setFormatter(formato_detallado)
    logger_autenticacion.addHandler(handler_autenticacion)

    # 2. Logger de errores CSRF
    logger_csrf = logging.getLogger('csrf')
    logger_csrf.setLevel(logging.ERROR)
    handler_csrf = RotatingFileHandler(
        os.path.join(logs_dir, 'csrf_errors.log'),
        maxBytes=10*1024*1024,
        backupCount=10,
        encoding='utf-8'
    )
    handler_csrf.setFormatter(formato_detallado)
    logger_csrf.addHandler(handler_csrf)

    # 3. Logger de sesiones (creación/invalidación)
    logger_sesiones = logging.getLogger('sesiones')
    logger_sesiones.setLevel(logging.INFO)
    handler_sesiones = RotatingFileHandler(
        os.path.join(logs_dir, 'sesiones.log'),
        maxBytes=10*1024*1024,
        backupCount=10,
        encoding='utf-8'
    )
    handler_sesiones.setFormatter(formato_detallado)
    logger_sesiones.addHandler(handler_sesiones)

    # 4. Logger general de aplicación
    logger_app = logging.getLogger('aplicacion')
    logger_app.setLevel(logging.INFO)
    handler_app = RotatingFileHandler(
        os.path.join(logs_dir, 'aplicacion.log'),
        maxBytes=10*1024*1024,
        backupCount=10,
        encoding='utf-8'
    )
    handler_app.setFormatter(formato_detallado)
    logger_app.addHandler(handler_app)

    app.logger.info(f"Sistema de logging detallado configurado en: {logs_dir}")


def obtener_ip_real_cliente():
    """
    Obtiene la IP real del cliente considerando proxies

    Returns:
        str: IP del cliente
    """
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()

    x_real_ip = request.headers.get('X-Real-IP')
    if x_real_ip:
        return x_real_ip

    return request.remote_addr or 'IP desconocida'


def log_intento_login(usuario, exito, razon=None, ip=None, user_agent=None, cookies=None):
    """
    Registra intento de inicio de sesión con detalles completos

    Args:
        usuario: Nombre de usuario o email
        exito: Boolean indicando si el login fue exitoso
        razon: Razón del fallo (si aplica)
        ip: IP del cliente (opcional, se detecta automáticamente)
        user_agent: User agent del navegador (opcional)
        cookies: Cookies presentes en la request (opcional)
    """
    logger = logging.getLogger('autenticacion')

    ip_cliente = ip or obtener_ip_real_cliente()
    user_agent_info = user_agent or request.headers.get('User-Agent', 'Desconocido')
    cookies_info = cookies or ', '.join(request.cookies.keys()) if request.cookies else 'Ninguna'

    estado = "EXITOSO" if exito else "FALLIDO"

    mensaje = f"""
{'='*80}
INTENTO DE LOGIN - {estado}
Timestamp: {datetime.now().isoformat()}
Usuario: {usuario}
IP Cliente: {ip_cliente}
User Agent: {user_agent_info}
Referer: {request.headers.get('Referer', 'Ninguno')}
Cookies presentes: {cookies_info}
Session ID actual: {session.get('_id', 'None')}
"""

    if not exito and razon:
        mensaje += f"Razón del fallo: {razon}\n"

    mensaje += f"{'='*80}"

    if exito:
        logger.info(mensaje)
    else:
        logger.warning(mensaje)


def log_error_csrf_detallado(request_obj=None):
    """
    Registra error CSRF con TODO el contexto posible

    Args:
        request_obj: Objeto request de Flask (opcional, se usa el actual si no se provee)
    """
    logger = logging.getLogger('csrf')
    req = request_obj or request

    # Obtener token CSRF del formulario y de la sesión
    csrf_token_form = req.form.get('csrf_token', 'No presente en formulario')
    csrf_token_session = session.get('csrf_token', 'No presente en sesión')

    # Detectar si es Chrome/Edge en modo normal (no incógnito)
    user_agent = req.headers.get('User-Agent', 'Desconocido')
    es_chrome = 'Chrome' in user_agent or 'Edg' in user_agent

    # Detectar cookies de sesión problemáticas
    cookies_presentes = list(req.cookies.keys())
    tiene_session_cookie = 'session' in cookies_presentes
    tiene_csrf_cookie = any('csrf' in c.lower() for c in cookies_presentes)

    # DIAGNÓSTICO ESPECÍFICO: Chrome modo normal vs incógnito
    diagnostico = ""
    if es_chrome and not tiene_csrf_cookie:
        diagnostico = """
[DIAGNOSTICO] PROBABLE: Cookies corruptas en Chrome modo normal
- Chrome/Edge detectado
- Cookie CSRF ausente (probablemente bloqueada o corrupta)
- SOLUCIÓN: Usuario debe limpiar cookies del sitio o usar incógnito
- ACCIÓN AUTOMÁTICA: Redirigir a /auth/limpiar-sesion
"""

    mensaje = f"""
{'='*80}
ERROR CSRF DETECTADO
Timestamp: {datetime.now().isoformat()}
Método: {req.method}
Ruta: {req.path}
IP Cliente: {obtener_ip_real_cliente()}
User Agent: {user_agent}
Navegador: {'Chrome/Edge' if es_chrome else 'Otro'}
Referer: {req.headers.get('Referer', 'Ninguno')}
Origin: {req.headers.get('Origin', 'Ninguno')}

SESIÓN:
Session ID: {session.get('_id', 'None')}
Usuario autenticado: {current_user.nombre_usuario if current_user.is_authenticated else 'No autenticado'}
CSRF Token en sesión: {csrf_token_session}

FORMULARIO:
CSRF Token en formulario: {csrf_token_form}

COOKIES PRESENTES ({len(cookies_presentes)} total):
  - Session cookie presente: {'SÍ' if tiene_session_cookie else 'NO'}
  - CSRF cookie presente: {'SÍ' if tiene_csrf_cookie else 'NO'}
{chr(10).join([f"  - {nombre}: {valor[:50]}..." if len(valor) > 50 else f"  - {nombre}: {valor}" for nombre, valor in req.cookies.items()])}
{diagnostico}
HEADERS COMPLETOS:
{chr(10).join([f"  {nombre}: {valor}" for nombre, valor in req.headers.items()])}
{'='*80}
"""

    logger.error(mensaje)
def log_sesion_invalidada(usuario, token, razon):
    """
    Registra cuando una sesión es invalidada

    Args:
        usuario: Nombre de usuario
        token: Token de sesión invalidado
        razon: Razón de la invalidación
    """
    logger = logging.getLogger('sesiones')

    mensaje = f"""
{'='*80}
SESIÓN INVALIDADA
Timestamp: {datetime.now().isoformat()}
Usuario: {usuario}
Token de sesión: {token}
Razón: {razon}
IP Cliente: {obtener_ip_real_cliente()}
Session ID Flask: {session.get('_id', 'None')}
{'='*80}
"""

    logger.warning(mensaje)


def log_creacion_sesion(usuario, token, ip=None, sesiones_cerradas=0):
    """
    Registra cuando se crea una nueva sesión

    Args:
        usuario: Nombre de usuario
        token: Token de sesión creado
        ip: IP del cliente (opcional)
        sesiones_cerradas: Número de sesiones cerradas al crear esta (para sesión única)
    """
    logger = logging.getLogger('sesiones')

    ip_cliente = ip or obtener_ip_real_cliente()

    mensaje = f"""
{'='*80}
NUEVA SESIÓN CREADA
Timestamp: {datetime.now().isoformat()}
Usuario: {usuario}
Token de sesión: {token}
IP Cliente: {ip_cliente}
User Agent: {request.headers.get('User-Agent', 'Desconocido')}
Session ID Flask: {session.get('_id', 'None')}
Sesiones previas cerradas: {sesiones_cerradas}
{'='*80}
"""

    logger.info(mensaje)


def log_validacion_sesion(usuario, token, valida, razon=None):
    """
    Registra validación de sesión

    Args:
        usuario: Nombre de usuario
        token: Token de sesión validado
        valida: Boolean indicando si la sesión es válida
        razon: Razón si no es válida (opcional)
    """
    logger = logging.getLogger('sesiones')

    estado = "VÁLIDA" if valida else "INVÁLIDA"

    mensaje = f"""
VALIDACIÓN DE SESIÓN - {estado}
Timestamp: {datetime.now().isoformat()}
Usuario: {usuario}
Token: {token}
IP Cliente: {obtener_ip_real_cliente()}
"""

    if not valida and razon:
        mensaje += f"Razón de invalidez: {razon}\n"

    if valida:
        logger.info(mensaje)
    else:
        logger.warning(mensaje)


def log_acceso_bloqueado(usuario, razon, ip=None, ruta=None):
    """
    Registra cuando se bloquea un acceso

    Args:
        usuario: Nombre de usuario o identificador
        razon: Razón del bloqueo
        ip: IP del cliente (opcional)
        ruta: Ruta a la que intentaba acceder (opcional)
    """
    logger = logging.getLogger('aplicacion')

    ip_cliente = ip or obtener_ip_real_cliente()
    ruta_acceso = ruta or request.path

    mensaje = f"""
{'='*80}
ACCESO BLOQUEADO
Timestamp: {datetime.now().isoformat()}
Usuario: {usuario}
IP Cliente: {ip_cliente}
Ruta solicitada: {ruta_acceso}
Razón del bloqueo: {razon}
User Agent: {request.headers.get('User-Agent', 'Desconocido')}
Referer: {request.headers.get('Referer', 'Ninguno')}
{'='*80}
"""

    logger.warning(mensaje)


def detectar_problema_cookies_chrome():
    """
    Detecta si hay un problema típico de cookies en Chrome
    (funciona en incógnito pero no en modo normal)

    Returns:
        dict: Información sobre el problema detectado
    """
    user_agent = request.headers.get('User-Agent', '')
    es_chrome = 'Chrome' in user_agent or 'Edg' in user_agent

    cookies_presentes = list(request.cookies.keys())
    tiene_session_cookie = 'session' in cookies_presentes
    tiene_csrf_cookie = any('csrf' in c.lower() for c in cookies_presentes)

    # Problema típico: Chrome sin cookies de sesión/CSRF
    problema_detectado = es_chrome and not (tiene_session_cookie or tiene_csrf_cookie)

    return {
        'problema_detectado': problema_detectado,
        'es_chrome': es_chrome,
        'tiene_session_cookie': tiene_session_cookie,
        'tiene_csrf_cookie': tiene_csrf_cookie,
        'total_cookies': len(cookies_presentes),
        'navegador': 'Chrome/Edge' if es_chrome else 'Otro',
        'recomendacion': 'Limpiar cookies del sitio o usar modo incógnito' if problema_detectado else 'OK'
    }


def log_diagnostico_cookies():
    """
    Registra diagnóstico completo de cookies del navegador
    Útil para identificar problemas de Chrome modo normal vs incógnito
    """
    logger = logging.getLogger('csrf')

    diagnostico = detectar_problema_cookies_chrome()
    user_agent = request.headers.get('User-Agent', 'Desconocido')

    mensaje = f"""
{'='*80}
DIAGNÓSTICO DE COOKIES
Timestamp: {datetime.now().isoformat()}
IP Cliente: {obtener_ip_real_cliente()}
User Agent: {user_agent}

ANÁLISIS:
- Navegador: {diagnostico['navegador']}
- Problema detectado: {'SÍ [ADVERTENCIA]' if diagnostico['problema_detectado'] else 'No'}
- Session cookie presente: {'SÍ' if diagnostico['tiene_session_cookie'] else 'NO [ADVERTENCIA]'}
- CSRF cookie presente: {'SÍ' if diagnostico['tiene_csrf_cookie'] else 'NO [ADVERTENCIA]'}
- Total de cookies: {diagnostico['total_cookies']}

RECOMENDACIÓN: {diagnostico['recomendacion']}

COOKIES ACTUALES:
{chr(10).join([f"  - {nombre}" for nombre in request.cookies.keys()]) if request.cookies else "  (Ninguna cookie presente)"}
{'='*80}
"""

    if diagnostico['problema_detectado']:
        logger.warning(mensaje)
    else:
        logger.info(mensaje)
