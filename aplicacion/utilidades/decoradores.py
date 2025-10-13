"""
Decoradores para Evolve Soluciones
==================================

Contiene decoradores personalizados para control de acceso,
validación y funcionalidades transversales.
"""

from functools import wraps
from flask import request, jsonify, flash, redirect, url_for
from flask_login import current_user
from aplicacion.modelos.modulo import Modulo


def acceso_empresa_requerido(f):
    """
    Decorador que verifica que el usuario tenga acceso a funciones de empresa

    Args:
        f: Función a decorar

    Returns:
        function: Función decorada
    """
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Autenticación requerida'}), 401
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('autenticacion.iniciar_sesion'))

        # Aquí podrías agregar lógica adicional de control de acceso por empresa
        # Por ahora, permitir acceso a todos los usuarios autenticados

        return f(*args, **kwargs)

    return funcion_decorada


def solo_administradores(f):
    """
    Decorador que permite acceso solo a administradores

    Args:
        f: Función a decorar

    Returns:
        function: Función decorada
    """
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Autenticación requerida'}), 401
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('autenticacion.iniciar_sesion'))

        if not current_user.es_administrador():
            if request.is_json:
                return jsonify({'error': 'Permisos insuficientes'}), 403
            flash('No tienes permisos para acceder a esta página.', 'error')
            return redirect(url_for('consolidado.dashboard'))

        return f(*args, **kwargs)

    return funcion_decorada


def validar_json(campos_requeridos=None):
    """
    Decorador que valida que la request tenga JSON válido y campos requeridos

    Args:
        campos_requeridos (list): Lista de campos que deben estar presentes

    Returns:
        function: Decorador
    """
    def decorador(f):
        @wraps(f)
        def funcion_decorada(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type debe ser application/json'}), 400

            data = request.get_json()
            if not data:
                return jsonify({'error': 'JSON inválido o vacío'}), 400

            if campos_requeridos:
                campos_faltantes = []
                for campo in campos_requeridos:
                    if campo not in data or data[campo] is None or data[campo] == '':
                        campos_faltantes.append(campo)

                if campos_faltantes:
                    return jsonify({
                        'error': 'Campos requeridos faltantes',
                        'campos_faltantes': campos_faltantes
                    }), 400

            return f(*args, **kwargs)

        return funcion_decorada
    return decorador


def manejar_errores(f):
    """
    Decorador que maneja errores de forma consistente

    Args:
        f: Función a decorar

    Returns:
        function: Función decorada
    """
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            print(f"Error de validación en {f.__name__}: {e}")
            if request.is_json:
                return jsonify({'error': str(e)}), 400
            flash(str(e), 'error')
            return redirect(request.referrer or url_for('consolidado.dashboard'))
        except PermissionError as e:
            print(f"Error de permisos en {f.__name__}: {e}")
            if request.is_json:
                return jsonify({'error': 'Permisos insuficientes'}), 403
            flash('No tienes permisos para realizar esta acción.', 'error')
            return redirect(url_for('consolidado.dashboard'))
        except Exception as e:
            print(f"Error interno en {f.__name__}: {e}")
            import traceback
            traceback.print_exc()
            if request.is_json:
                return jsonify({'error': 'Error interno del servidor'}), 500
            flash('Ha ocurrido un error interno. Intenta nuevamente.', 'error')
            return redirect(request.referrer or url_for('consolidado.dashboard'))

    return funcion_decorada


def limitar_intentos(max_intentos=5, ventana_minutos=15):
    """
    Decorador para limitar intentos de acceso (útil para login)

    Args:
        max_intentos (int): Máximo número de intentos permitidos
        ventana_minutos (int): Ventana de tiempo en minutos

    Returns:
        function: Decorador
    """
    def decorador(f):
        @wraps(f)
        def funcion_decorada(*args, **kwargs):
            # Obtener IP del cliente
            ip_cliente = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if ip_cliente:
                ip_cliente = ip_cliente.split(',')[0].strip()

            # Aquí podrías implementar lógica de rate limiting
            # usando Redis, base de datos o memoria
            # Por ahora, simplemente ejecutar la función

            return f(*args, **kwargs)

        return funcion_decorada
    return decorador


def registrar_auditoria(accion):
    """
    Decorador que registra acciones para auditoría

    Args:
        accion (str): Descripción de la acción realizada

    Returns:
        function: Decorador
    """
    def decorador(f):
        @wraps(f)
        def funcion_decorada(*args, **kwargs):
            # Ejecutar función original
            resultado = f(*args, **kwargs)

            # Registrar auditoría
            try:
                if current_user.is_authenticated:
                    print(f"AUDITORÍA: Usuario {current_user.nombre_usuario} realizó: {accion}")
                    # Aquí podrías guardar en base de datos para auditoría
                else:
                    print(f"AUDITORÍA: Usuario anónimo realizó: {accion}")
            except Exception as e:
                print(f"Error registrando auditoría: {e}")

            return resultado

        return funcion_decorada
    return decorador


def cache_resultado(tiempo_cache=300):
    """
    Decorador simple para cachear resultados de funciones

    Args:
        tiempo_cache (int): Tiempo de cache en segundos

    Returns:
        function: Decorador
    """
    def decorador(f):
        cache = {}

        @wraps(f)
        def funcion_decorada(*args, **kwargs):
            from datetime import datetime, timedelta

            # Crear clave de cache
            clave_cache = str(args) + str(sorted(kwargs.items()))

            # Verificar si existe en cache y no ha expirado
            if clave_cache in cache:
                resultado, timestamp = cache[clave_cache]
                if datetime.now() - timestamp < timedelta(seconds=tiempo_cache):
                    return resultado

            # Ejecutar función y cachear resultado
            resultado = f(*args, **kwargs)
            cache[clave_cache] = (resultado, datetime.now())

            return resultado

        return funcion_decorada
    return decorador


def requiere_modulo(codigo_modulo):
    """
    Decorador para verificar que el módulo esté habilitado para la BD del usuario

    Verifica en PostgreSQL (auth.modulos_habilitados_bd) si el módulo especificado
    está habilitado para la base de datos MySQL asignada al usuario actual.

    Args:
        codigo_modulo (str): Código del módulo (ej: 'consulta_f29', 'consolidado')

    Returns:
        function: Decorador que valida acceso al módulo

    Ejemplo de uso:
        @app.route('/consulta-f29')
        @login_required
        @requiere_modulo('consulta_f29')
        def vista_consulta():
            return render_template('consulta.html')
    """
    def decorador(f):
        @wraps(f)
        def funcion_decorada(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'error': 'Autenticación requerida'}), 401
                flash('Debes iniciar sesión para acceder a esta página.', 'warning')
                return redirect(url_for('autenticacion.iniciar_sesion'))

            # Obtener BD del usuario
            base_datos = current_user.base_datos_mysql

            # Verificar si el módulo está habilitado
            try:
                if not Modulo.verificar_modulo_habilitado(base_datos, codigo_modulo):
                    # Detectar si es petición AJAX/API
                    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({
                            'error': f'El módulo no está disponible para esta base de datos',
                            'modulo': codigo_modulo,
                            'base_datos': base_datos
                        }), 403

                    flash(f'El módulo solicitado no está disponible para tu base de datos.', 'warning')
                    return redirect(url_for('rutas_dinamicas.inicio_base_datos',
                                           base_datos=base_datos))
            except Exception as e:
                print(f"Error verificando módulo {codigo_modulo}: {e}")
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'error': 'Error verificando permisos del módulo'}), 500
                flash('Error al verificar permisos. Intenta nuevamente.', 'error')
                return redirect(url_for('rutas_dinamicas.inicio_base_datos',
                                       base_datos=base_datos))

            return f(*args, **kwargs)
        return funcion_decorada
    return decorador


def validar_parametros(**validadores):
    """
    Decorador que valida parámetros de la request usando funciones de validación

    Args:
        **validadores: Diccionario de validadores por parámetro

    Returns:
        function: Decorador
    """
    def decorador(f):
        @wraps(f)
        def funcion_decorada(*args, **kwargs):
            # Obtener parámetros según el método
            if request.method == 'GET':
                parametros = request.args
            else:
                parametros = request.form if request.form else request.get_json() or {}

            # Validar cada parámetro
            errores = []
            for nombre_param, validador in validadores.items():
                valor = parametros.get(nombre_param)
                if not validador(valor):
                    errores.append(f"Parámetro '{nombre_param}' inválido")

            if errores:
                if request.is_json:
                    return jsonify({'error': 'Parámetros inválidos', 'detalles': errores}), 400
                flash('Algunos parámetros son inválidos.', 'error')
                return redirect(request.referrer or url_for('consolidado.dashboard'))

            return f(*args, **kwargs)

        return funcion_decorada
    return decorador
