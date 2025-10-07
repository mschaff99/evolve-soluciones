"""
Manejadores de errores para Evolve Soluciones
=============================================

Define manejadores personalizados para diferentes tipos de errores
que pueden ocurrir en la aplicación.
"""

from flask import request, jsonify, redirect, url_for, flash, session
from flask_wtf.csrf import CSRFError


def registrar_manejadores_errores(aplicacion):
    """
    Registra todos los manejadores de errores personalizados

    Args:
        aplicacion (Flask): Instancia de la aplicación Flask
    """

    @aplicacion.errorhandler(CSRFError)
    def manejar_error_csrf(e):
        """Maneja errores de CSRF con respuesta apropiada según el tipo de request"""
        # Determinar si la solicitud espera JSON
        espera_json = (
            request.is_json or
            (request.headers.get('Content-Type') == 'application/json') or
            request.path.startswith('/api/')
        )

        payload = {
            'estado': 'error',
            'mensaje': 'Token CSRF inválido o ausente',
            'razon': getattr(e, 'description', 'Validación CSRF falló')
        }

        if espera_json:
            return jsonify(payload), 400

        # Para formularios web (como login), limpiar sesión y redirigir
        if request.path.startswith('/auth/iniciar-sesion') and request.method == 'POST':
            # Limpiar sesión corrupta completamente
            session.clear()

            # Log para debugging
            print(f"[CSRF ERROR] Sesión limpiada automáticamente para IP: {request.remote_addr}")

            # Mensaje claro para el usuario
            flash('Tu sesión ha sido limpiada automáticamente. Intenta iniciar sesión nuevamente.', 'warning')

            # Redirigir de vuelta al login con parámetro para limpiar cookies en el navegador
            return redirect(url_for('autenticacion.iniciar_sesion', limpiar_cookies='1'))

        return (
            f"Error CSRF: {payload['razon']}",
            400,
            {'Content-Type': 'text/plain; charset=utf-8'}
        )

    @aplicacion.errorhandler(404)
    def pagina_no_encontrada(e):
        """Maneja errores 404 - Página no encontrada"""
        if request.path.startswith('/api/'):
            return jsonify({
                'estado': 'error',
                'mensaje': 'Endpoint no encontrado',
                'codigo': 404
            }), 404

        # Para requests HTML, podrías renderizar un template personalizado
        return "Página no encontrada", 404

    @aplicacion.errorhandler(500)
    def error_interno_servidor(e):
        """Maneja errores 500 - Error interno del servidor"""
        if request.path.startswith('/api/'):
            return jsonify({
                'estado': 'error',
                'mensaje': 'Error interno del servidor',
                'codigo': 500
            }), 500

        return "Error interno del servidor", 500

    @aplicacion.errorhandler(403)
    def acceso_prohibido(e):
        """Maneja errores 403 - Acceso prohibido"""
        if request.path.startswith('/api/'):
            return jsonify({
                'estado': 'error',
                'mensaje': 'Acceso prohibido',
                'codigo': 403
            }), 403

        return "Acceso prohibido", 403
