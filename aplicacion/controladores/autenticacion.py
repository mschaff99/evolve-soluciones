"""
Controlador de Autenticación para Evolve Soluciones
===================================================

Maneja todas las rutas relacionadas con autenticación de usuarios:
inicio de sesión, cierre de sesión y registro.
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from aplicacion.modelos.usuario import Usuario
from aplicacion.modelos.sesion import SesionUsuario
from aplicacion.utilidades.validadores import validar_email, validar_contraseña
from aplicacion.utilidades.herramientas_ip import obtener_ip_real_cliente

# Crear blueprint para autenticación
autenticacion_bp = Blueprint('autenticacion', __name__, url_prefix='/auth')


@autenticacion_bp.route('/iniciar-sesion', methods=['GET', 'POST'])
def iniciar_sesion():
    """Maneja el inicio de sesión de usuarios"""

    # Si el usuario ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        base_datos = current_user.base_datos_mysql or 'stratex'
        return redirect(f'/{base_datos}')

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
            # Registrar intento fallido
            SesionUsuario.registrar_intento_login(
                nombre_usuario=nombre_usuario,
                direccion_ip=obtener_ip_real_cliente(),
                exitoso=False,
                mensaje="Usuario no encontrado"
            )
            flash('Credenciales inválidas.', 'error')
            return render_template('paginas/iniciar_sesion.html')

        # Verificar contraseña
        if not usuario.verificar_contraseña(contraseña):
            # Registrar intento fallido
            SesionUsuario.registrar_intento_login(
                nombre_usuario=nombre_usuario,
                direccion_ip=obtener_ip_real_cliente(),
                exitoso=False,
                mensaje="Contraseña incorrecta"
            )
            flash('Credenciales inválidas.', 'error')
            return render_template('paginas/iniciar_sesion.html')

        # Verificar que el usuario esté activo
        if not usuario.es_activo():
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
            return render_template('paginas/iniciar_sesion.html')

        try:
            # Crear sesión en la base de datos
            ip_cliente = obtener_ip_real_cliente()
            user_agent = request.headers.get('User-Agent', 'Desconocido')

            sesion_usuario = SesionUsuario.crear_sesion(
                id_usuario=usuario.id,
                direccion_ip=ip_cliente,
                user_agent=user_agent
            )

            # Iniciar sesión con Flask-Login
            login_user(usuario, remember=recordarme)

            # Guardar token de sesión
            session['session_token'] = sesion_usuario.token_sesion

            # Actualizar último acceso del usuario
            usuario.actualizar_ultimo_acceso()

            print(f"Usuario {usuario.nombre_usuario} ha iniciado sesion exitosamente")

            # Registrar intento exitoso
            SesionUsuario.registrar_intento_login(
                nombre_usuario=usuario.nombre_usuario,
                direccion_ip=ip_cliente,
                exitoso=True,
                mensaje="Inicio de sesion exitoso"
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
        base_datos = current_user.base_datos_mysql or 'stratex'
        return redirect(f'/{base_datos}')

    try:
        usuarios = Usuario.obtener_todos_usuarios()
        return render_template('paginas/listar_usuarios.html', usuarios=usuarios)
    except Exception as e:
        print(f"Error obteniendo usuarios: {e}")
        flash('Error cargando usuarios.', 'error')
        base_datos = current_user.base_datos_mysql or 'stratex'
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
            base_datos = current_user.base_datos_mysql or 'stratex'
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
