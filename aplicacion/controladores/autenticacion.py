"""
Controlador de Autenticación para Evolve Soluciones
===================================================

Maneja todas las rutas relacionadas con autenticación de usuarios:
inicio de sesión, cierre de sesión y registro.
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify, current_app, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from aplicacion.modelos.usuario import Usuario
from aplicacion.modelos.sesion import SesionUsuario
from aplicacion.utilidades.validadores import validar_email, validar_contraseña
from aplicacion.utilidades.herramientas_ip import obtener_ip_real_cliente
from aplicacion.utilidades.logging_detallado import (
    log_intento_login,
    log_creacion_sesion,
    log_acceso_bloqueado,
    log_diagnostico_cookies,
    detectar_problema_cookies_chrome
)

# Crear blueprint para autenticación
autenticacion_bp = Blueprint('autenticacion', __name__, url_prefix='/auth')


@autenticacion_bp.route('/iniciar-sesion', methods=['GET', 'POST'])
def iniciar_sesion():
    """Maneja el inicio de sesión de usuarios"""

    # Si el usuario ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        base_datos = current_user.base_datos_mysql
        return redirect(f'/{base_datos}')

    # GET request - Verificar si hay problema de cookies ANTES de mostrar el form
    if request.method == 'GET':
        # Registrar diagnóstico de cookies para usuarios con problemas
        diagnostico = detectar_problema_cookies_chrome()

        # Si el detector especializado identifica un problema típico de Chrome,
        # redirigimos automáticamente al endpoint de limpieza que borra cookies
        # y regresa al login. Esto evita que el usuario deba limpiar cookies manualmente.
        if diagnostico['problema_detectado']:
            log_diagnostico_cookies()
            return redirect(url_for('autenticacion.limpiar_sesion'))

        # Medida adicional: si existe una cookie de sesión enviada por el navegador
        # pero no existe cookie CSRF ni hay sesión válida en servidor, entonces
        # asumimos que hay cookies corruptas/duplicadas y forzamos limpieza.
        # Esto cubre escenarios donde el detector específico no haya marcado el problema.
        has_evolve = 'evolve_session' in request.cookies
        has_csrf_cookie = 'csrf_token' in request.cookies
        has_server_session = bool(session.get('session_token'))

        if has_evolve and (not has_csrf_cookie or not has_server_session):
            # Registrar diagnóstico ligero y limpiar automáticamente
            log_diagnostico_cookies()
            return redirect(url_for('autenticacion.limpiar_sesion'))

    if request.method == 'POST':
        nombre_usuario = request.form.get('nombre_usuario', '').strip()
        contraseña = request.form.get('contraseña', '')
        recordarme = bool(request.form.get('recordarme'))

        # Validar campos requeridos
        if not nombre_usuario or not contraseña:
            flash('Por favor, completa todos los campos.', 'error')
            return render_template('paginas/iniciar_sesion.html')

        # Buscar usuario
        usuario = Usuario.obtener_por_nombre_usuario(nombre_usuario)

        if not usuario:
            # Registrar intento fallido en BD
            SesionUsuario.registrar_intento_login(
                nombre_usuario=nombre_usuario,
                direccion_ip=obtener_ip_real_cliente(),
                exitoso=False,
                mensaje="Usuario no encontrado"
            )
            # Registrar en log detallado
            log_intento_login(
                usuario=nombre_usuario,
                exito=False,
                razon="Usuario no encontrado en la base de datos"
            )
            flash('Credenciales inválidas.', 'error')
            return render_template('paginas/iniciar_sesion.html')

        # Verificar contraseña
        if not usuario.verificar_contraseña(contraseña):
            # Registrar intento fallido en BD
            SesionUsuario.registrar_intento_login(
                nombre_usuario=nombre_usuario,
                direccion_ip=obtener_ip_real_cliente(),
                exitoso=False,
                mensaje="Contraseña incorrecta"
            )
            # Registrar en log detallado
            log_intento_login(
                usuario=nombre_usuario,
                exito=False,
                razon="Contraseña incorrecta"
            )
            flash('Credenciales inválidas.', 'error')
            return render_template('paginas/iniciar_sesion.html')

        # Verificar que el usuario esté activo en PostgreSQL
        if not usuario.es_activo():
            # Registrar acceso bloqueado
            log_acceso_bloqueado(
                usuario=nombre_usuario,
                razon="Cuenta desactivada en PostgreSQL"
            )
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
            return render_template('paginas/iniciar_sesion.html')

        # NUEVA VALIDACIÓN: Verificar acceso en MySQL (usuarios_acceso)
        tiene_acceso, auditor, tipo_usuario, mensaje = usuario.validar_acceso_mysql()

        if not tiene_acceso:
            # Registrar acceso bloqueado por MySQL
            log_acceso_bloqueado(
                usuario=nombre_usuario,
                razon=f"Acceso denegado en MySQL: {mensaje}"
            )
            SesionUsuario.registrar_intento_login(
                nombre_usuario=nombre_usuario,
                direccion_ip=obtener_ip_real_cliente(),
                exitoso=False,
                mensaje=mensaje
            )
            flash(f'Acceso denegado: {mensaje}', 'error')
            return render_template('paginas/iniciar_sesion.html')

        # Si llegamos aquí, el usuario está autorizado en ambos sistemas
        print(f"INFO: Usuario {nombre_usuario} autorizado - Auditor: {auditor} - Tipo: {tipo_usuario}")

        # Guardar información adicional en la sesión de Flask
        session['auditor_mysql'] = auditor
        session['tipo_usuario_mysql'] = tipo_usuario

        try:
            # Crear sesión única en la base de datos (cierra sesiones previas)
            ip_cliente = obtener_ip_real_cliente()
            user_agent = request.headers.get('User-Agent', 'Desconocido')

            # CAMBIO IMPORTANTE: Usar crear_sesion_unica en lugar de crear_sesion
            # Esto garantiza que solo haya una sesión activa por usuario
            sesion_usuario = SesionUsuario.crear_sesion_unica(
                id_usuario=usuario.id,
                direccion_ip=ip_cliente,
                user_agent=user_agent
            )

            # Registrar creación de sesión en log detallado
            sesiones_cerradas = sesion_usuario.get('sesiones_cerradas', 0) if isinstance(sesion_usuario, dict) else 0
            log_creacion_sesion(
                usuario=usuario.nombre_usuario,
                token=sesion_usuario.token_sesion if hasattr(sesion_usuario, 'token_sesion') else 'N/A',
                ip=ip_cliente,
                sesiones_cerradas=sesiones_cerradas
            )

            # Iniciar sesión con Flask-Login
            login_user(usuario, remember=recordarme)

            # Guardar token de sesión
            session['session_token'] = sesion_usuario.token_sesion

            # Actualizar último acceso del usuario
            usuario.actualizar_ultimo_acceso()

            print(f"Usuario {usuario.nombre_usuario} ha iniciado sesion exitosamente")

            # Registrar intento exitoso en BD
            SesionUsuario.registrar_intento_login(
                nombre_usuario=usuario.nombre_usuario,
                direccion_ip=ip_cliente,
                exitoso=True,
                mensaje="Inicio de sesion exitoso"
            )

            # Registrar en log detallado
            log_intento_login(
                usuario=usuario.nombre_usuario,
                exito=True
            )

            flash(f'¡Bienvenido, {usuario.nombre_usuario}!', 'success')

            # Redirigir a la página solicitada o al dashboard con base de datos del usuario
            siguiente = request.args.get('next')
            if siguiente:
                return redirect(siguiente)
            else:
                # Redirigir a la URL con la base de datos del usuario
                base_datos = usuario.base_datos_mysql or 'default'
                return redirect(f'/{base_datos}')

        except Exception as e:
            print(f"Error durante inicio de sesion: {e}")
            flash('Error interno. Intenta nuevamente.', 'error')
            return render_template('paginas/iniciar_sesion.html')

    # GET request - mostrar formulario de inicio de sesión
    return render_template('paginas/iniciar_sesion.html')


@autenticacion_bp.route('/cerrar-sesion')
@login_required
def cerrar_sesion():
    """Cierra la sesión del usuario actual"""

    try:
        # Cerrar sesión en la base de datos
        token_sesion = session.get('session_token')
        if token_sesion:
            sesion = SesionUsuario.obtener_por_token(token_sesion)
            if sesion:
                sesion.cerrar_sesion()

        # Limpiar datos de sesión
        session.pop('session_token', None)

        print(f"Usuario {current_user.nombre_usuario} ha cerrado sesion")

        # Cerrar sesión con Flask-Login
        logout_user()

        flash('Has cerrado sesión exitosamente.', 'info')

    except Exception as e:
        print(f"Error durante cierre de sesion: {e}")
        logout_user()  # Cerrar sesion de todas formas

    return redirect(url_for('autenticacion.iniciar_sesion'))


@autenticacion_bp.route('/limpiar-sesion')
def limpiar_sesion():
    """
    Limpia completamente la sesión del navegador
    Útil cuando hay cookies corruptas o problemas de CSRF
    Especialmente diseñado para Chrome con problemas de cookies
    """
    try:
        # Registrar diagnóstico de cookies ANTES de limpiar
        log_diagnostico_cookies()

        # Detectar si es el problema típico de Chrome
        diagnostico = detectar_problema_cookies_chrome()

        # Cerrar sesión de Flask-Login si existe
        if current_user.is_authenticated:
            usuario_nombre = current_user.nombre_usuario
            logout_user()
            print(f"Usuario {usuario_nombre} cerró sesión vía limpiar-sesion")

        # Limpiar toda la sesión de Flask
        session.clear()

        # Mensajes específicos según el diagnóstico
        if diagnostico['problema_detectado']:
            flash(' Problema detectado: Cookies corruptas en Chrome/Edge.', 'warning')
            flash('Sesión limpiada exitosamente. Intenta iniciar sesión nuevamente.', 'success')
            flash(' Si el problema persiste:', 'info')
            flash('1. Presiona Ctrl+Shift+Delete → Eliminar cookies del sitio', 'info')
            flash('2. O usa modo incógnito temporalmente', 'info')
        else:
            flash('Tu sesión ha sido limpiada exitosamente. Ahora puedes iniciar sesión nuevamente.', 'success')

    except Exception as e:
        print(f"Error limpiando sesión: {e}")
        # Limpiar de todas formas
        session.clear()
        flash('Sesión limpiada. Intenta iniciar sesión nuevamente.', 'info')

    # Crear respuesta renderizando la plantilla de login y adjuntando
    # los headers para forzar la limpieza de cookies. Esto rompe el bucle de redirección.
    response = make_response(render_template('paginas/iniciar_sesion.html'))

    # Construir lista de variantes de dominio para borrar cookies.
    # Incluimos, en orden de preferencia:
    #  - SESSION_COOKIE_DOMAIN configurado (con y sin punto)
    #  - el host actual (request.host sin puerto) y su variante con '.'
    domain_variants = []

    configured_domain = current_app.config.get('SESSION_COOKIE_DOMAIN')
    if configured_domain:
        if configured_domain.startswith('.'):
            domain_variants.extend([configured_domain, configured_domain.lstrip('.')])
        else:
            domain_variants.extend([configured_domain, '.' + configured_domain])

    # Añadir host actual (por ejemplo portal.evolveasesores.cl)
    try:
        host = request.host.split(':')[0]
    except Exception:
        host = None

    if host:
        # Evitar duplicados
        if host not in domain_variants:
            domain_variants.append(host)
        if ('.' + host) not in domain_variants:
            domain_variants.append('.' + host)

    # Asegurar unicidad y orden consistente
    seen = set()
    domain_variants_unique = []
    for d in domain_variants:
        if d and d not in seen:
            seen.add(d)
            domain_variants_unique.append(d)

    cookie_names = ['evolve_session', 'session', 'csrf_token']

    # Intentar eliminar cookies para cada variante de dominio (si existe)
    for d in domain_variants_unique:
        for cname in cookie_names:
            try:
                response.set_cookie(cname, '', expires=0, path='/', domain=d)
            except Exception:
                # No detener el flujo por errores al fijar cookies; seguir con otras variantes
                pass

    # Además, eliminar sin especificar domain (host-only cookie)
    for cname in cookie_names:
        response.set_cookie(cname, '', expires=0, path='/')

    # Headers para prevenir caché
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response


@autenticacion_bp.route('/ayuda-navegador')
def ayuda_navegador():
    """
    Página de ayuda para usuarios con problemas de navegador
    Especialmente diseñada para problemas de cookies en Chrome
    """
    return render_template('paginas/ayuda_navegador.html')


@autenticacion_bp.route('/forzar-cookies-prueba')
def forzar_cookies_prueba():
    """
    Endpoint temporal de prueba que fuerza el envío de Set-Cookie
    para varias variantes de dominio (con y sin punto) y host-only.
    Útil para diagnosticar si el navegador acepta cookies con el dominio
    configurado por la aplicación / proxy.
    """
    # Valor de ejemplo para las cookies (no sensible)
    prueba_valor = 'test_cookie_val_' + (current_app.config.get('ENV', 'dev'))

    # Construir respuesta simple HTML (no depender de plantillas que pueden faltar)

    # Preparar variantes de dominio antes de construir la información diagnóstica
    domain = current_app.config.get('SESSION_COOKIE_DOMAIN')
    domain_variants = []
    if domain:
        if domain.startswith('.'):
            domain_variants.append(domain)
            domain_variants.append(domain.lstrip('.'))
        else:
            domain_variants.append(domain)
            domain_variants.append('.' + domain)

    # Información diagnóstica que mostraremos en la página
    info = {
        'session_cookie_domain_config': domain,
        'domain_variants': domain_variants,
        'request_cookies': dict(request.cookies)
    }

    html = [
        '<!doctype html><html><head><meta charset="utf-8"><title>Prueba cookies</title></head><body>',
        '<h2>Prueba de cookies (temporal)</h2>',
        '<p>Este endpoint intenta fijar cookies de prueba para diagnosticar aceptación por el navegador.</p>',
        '<h3>Información detectada por el servidor</h3>',
        f"<pre>{info}</pre>",
        '<p>Revisa DevTools → Application → Cookies para ver las cookies seteadas.</p>',
        '</body></html>'
    ]

    response = make_response('\n'.join(html))

    cookie_names = {
        'evolve_session': prueba_valor,
        'csrf_token': prueba_valor + '_csrf_test'
    }

    domain_variants = []
    if domain:
        if domain.startswith('.'):
            domain_variants.append(domain)
            domain_variants.append(domain.lstrip('.'))
        else:
            domain_variants.append(domain)
            domain_variants.append('.' + domain)

    # Set-Cookie para cada variante de dominio
    for d in domain_variants:
        for cname, cval in cookie_names.items():
            try:
                # Usar SameSite=None y Secure para simular producción
                response.set_cookie(cname, cval, path='/', domain=d, secure=True, samesite='None')
            except Exception:
                pass

    # También setear host-only cookies (sin domain)
    for cname, cval in cookie_names.items():
        response.set_cookie(cname, cval + '_host', path='/', secure=True, samesite='None')

    # Añadir header informativo
    response.headers['X-Debug-Note'] = 'Cookies set for domain variants and host-only (temporary diagnostic)'

    return response


@autenticacion_bp.route('/registrar', methods=['GET', 'POST'])
def registrar():
    """Maneja el registro de nuevos usuarios (solo administradores)"""

    # Solo administradores pueden registrar usuarios
    if not current_user.is_authenticated or not current_user.es_administrador():
        flash('No tienes permisos para registrar usuarios.', 'error')
        return redirect(url_for('autenticacion.iniciar_sesion'))

    if request.method == 'POST':
        nombre_usuario = request.form.get('nombre_usuario', '').strip()
        email = request.form.get('email', '').strip()
        contraseña = request.form.get('contraseña', '')
        confirmar_contraseña = request.form.get('confirmar_contraseña', '')
        rol = request.form.get('rol', 'usuario')

        # Validar campos requeridos
        if not all([nombre_usuario, email, contraseña, confirmar_contraseña]):
            flash('Por favor, completa todos los campos.', 'error')
            return render_template('paginas/registrar.html')

        # Validar formato de email
        if not validar_email(email):
            flash('El formato del email no es válido.', 'error')
            return render_template('paginas/registrar.html')

        # Validar contraseñas coincidan
        if contraseña != confirmar_contraseña:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('paginas/registrar.html')

        # Validar fortaleza de contraseña
        if not validar_contraseña(contraseña):
            flash('La contraseña debe tener al menos 8 caracteres, incluir mayúsculas, minúsculas y números.', 'error')
            return render_template('paginas/registrar.html')

        # Validar rol
        if rol not in ['usuario', 'administrador']:
            flash('Rol inválido.', 'error')
            return render_template('paginas/registrar.html')

        try:
            # Crear usuario
            nuevo_usuario = Usuario.crear_usuario(
                nombre_usuario=nombre_usuario,
                email=email,
                contraseña=contraseña,
                rol=rol
            )

            print(f"Usuario {nombre_usuario} registrado exitosamente por {current_user.nombre_usuario}")

            flash(f'Usuario {nombre_usuario} registrado exitosamente.', 'success')
            return redirect(url_for('autenticacion.listar_usuarios'))

        except ValueError as e:
            flash(str(e), 'error')
            return render_template('paginas/registrar.html')
        except Exception as e:
            print(f"Error registrando usuario: {e}")
            flash('Error interno. Intenta nuevamente.', 'error')
            return render_template('paginas/registrar.html')

    # GET request - mostrar formulario de registro
    return render_template('paginas/registrar.html')


@autenticacion_bp.route('/usuarios')
@login_required
def listar_usuarios():
    """Lista todos los usuarios (solo administradores)"""

    if not current_user.es_administrador():
        flash('No tienes permisos para ver esta página.', 'error')
        base_datos = current_user.base_datos_mysql
        return redirect(f'/{base_datos}')

    try:
        usuarios = Usuario.obtener_todos_usuarios()
        return render_template('paginas/listar_usuarios.html', usuarios=usuarios)
    except Exception as e:
        print(f"Error obteniendo usuarios: {e}")
        flash('Error cargando usuarios.', 'error')
        base_datos = current_user.base_datos_mysql
        return redirect(f'/{base_datos}')


@autenticacion_bp.route('/cambiar-contraseña', methods=['GET', 'POST'])
@login_required
def cambiar_contraseña():
    """Permite al usuario cambiar su contraseña"""

    if request.method == 'POST':
        contraseña_actual = request.form.get('contraseña_actual', '')
        nueva_contraseña = request.form.get('nueva_contraseña', '')
        confirmar_nueva = request.form.get('confirmar_nueva', '')

        # Validar campos requeridos
        if not all([contraseña_actual, nueva_contraseña, confirmar_nueva]):
            flash('Por favor, completa todos los campos.', 'error')
            return render_template('paginas/cambiar_contraseña.html')

        # Verificar contraseña actual
        if not current_user.verificar_contraseña(contraseña_actual):
            flash('La contraseña actual es incorrecta.', 'error')
            return render_template('paginas/cambiar_contraseña.html')

        # Validar que las nuevas contraseñas coincidan
        if nueva_contraseña != confirmar_nueva:
            flash('Las nuevas contraseñas no coinciden.', 'error')
            return render_template('paginas/cambiar_contraseña.html')

        # Validar fortaleza de la nueva contraseña
        if not validar_contraseña(nueva_contraseña):
            flash('La nueva contraseña debe tener al menos 8 caracteres, incluir mayúsculas, minúsculas y números.', 'error')
            return render_template('paginas/cambiar_contraseña.html')

        try:
            # Cambiar contraseña
            current_user.cambiar_contraseña(nueva_contraseña)

            # Cerrar todas las otras sesiones del usuario
            token_actual = session.get('session_token')
            SesionUsuario.cerrar_todas_sesiones_usuario(current_user.id, excepto_token=token_actual)

            print(f"Usuario {current_user.nombre_usuario} cambio su contraseña")

            flash('Contraseña cambiada exitosamente.', 'success')
            base_datos = current_user.base_datos_mysql
            return redirect(f'/{base_datos}')

        except Exception as e:
            print(f"Error cambiando contraseña: {e}")
            flash('Error interno. Intenta nuevamente.', 'error')
            return render_template('paginas/cambiar_contraseña.html')

    # GET request - mostrar formulario
    return render_template('paginas/cambiar_contraseña.html')


@autenticacion_bp.route('/api/verificar-sesion')
@login_required
def verificar_sesion():
    """API endpoint para verificar si la sesión está activa"""

    try:
        token_sesion = session.get('session_token')
        if not token_sesion:
            return jsonify({'activa': False, 'mensaje': 'No hay token de sesión'}), 401

        sesion = SesionUsuario.obtener_por_token(token_sesion)
        if not sesion:
            return jsonify({'activa': False, 'mensaje': 'Sesión no encontrada'}), 401

        if sesion.esta_expirada():
            sesion.cerrar_sesion()
            return jsonify({'activa': False, 'mensaje': 'Sesión expirada'}), 401

        # Actualizar actividad de la sesión
        sesion.actualizar_actividad()

        return jsonify({
            'activa': True,
            'usuario': current_user.nombre_usuario,
            'rol': current_user.rol
        })

    except Exception as e:
        print(f"Error verificando sesion: {e}")
        return jsonify({'activa': False, 'mensaje': 'Error interno'}), 500


@autenticacion_bp.route('/api/mis-sesiones')
@login_required
def obtener_mis_sesiones():
    """API endpoint para obtener las sesiones activas del usuario"""

    try:
        sesiones = SesionUsuario.obtener_sesiones_usuario(current_user.id, solo_activas=True)
        sesiones_data = [sesion.to_dict() for sesion in sesiones]

        return jsonify({
            'exito': True,
            'sesiones': sesiones_data,
            'total': len(sesiones_data)
        })

    except Exception as e:
        print(f"Error obteniendo sesiones: {e}")
        return jsonify({
            'exito': False,
            'error': 'Error interno'
        }), 500
