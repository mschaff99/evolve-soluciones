"""
Manejadores de errores para Evolve Soluciones
=============================================

Define manejadores personalizados para diferentes tipos de errores
que pueden ocurrir en la aplicación.
"""

from flask import request, jsonify, redirect, url_for, flash, session, make_response, render_template_string
from flask_wtf.csrf import CSRFError
from aplicacion.utilidades.logging_detallado import log_error_csrf_detallado, detectar_problema_cookies_chrome


def registrar_manejadores_errores(aplicacion):
    """
    Registra todos los manejadores de errores personalizados

    Args:
        aplicacion (Flask): Instancia de la aplicación Flask
    """

    @aplicacion.errorhandler(CSRFError)
    def manejar_error_csrf(e):
        """Maneja errores de CSRF con respuesta apropiada según el tipo de request"""

        # Registrar error CSRF detallado en log
        log_error_csrf_detallado(request)

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
            # Detectar si es el problema típico de Chrome con cookies corruptas
            diagnostico = detectar_problema_cookies_chrome()

            # Limpiar sesión corrupta completamente
            session.clear()

            # Log para debugging
            print(f"[CSRF ERROR] Sesión limpiada automáticamente para IP: {request.remote_addr}")
            print(f"[CSRF ERROR] Diagnóstico: Problema Chrome detectado={diagnostico['problema_detectado']}")

            # Si es el problema típico de Chrome, aplicar solución automática
            if diagnostico['problema_detectado']:
                # Crear respuesta HTML que limpia cookies automáticamente y recarga
                html_auto_fix = """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Reparando sesión...</title>
                    <style>
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            min-height: 100vh;
                            margin: 0;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                        }
                        .container {
                            text-align: center;
                            padding: 2rem;
                            background: rgba(255,255,255,0.1);
                            border-radius: 10px;
                            backdrop-filter: blur(10px);
                        }
                        .spinner {
                            border: 4px solid rgba(255,255,255,0.3);
                            border-radius: 50%;
                            border-top: 4px solid white;
                            width: 50px;
                            height: 50px;
                            margin: 20px auto;
                            animation: spin 1s linear infinite;
                        }
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="spinner"></div>
                        <h2>🔧 Reparando tu sesión...</h2>
                        <p>Detectamos un problema con las cookies del navegador.</p>
                        <p>Estamos limpiando automáticamente. Espera un momento...</p>
                    </div>
                    <script>
                        // Función para eliminar TODAS las cookies del dominio actual
                        function eliminarTodasLasCookies() {
                            const cookies = document.cookie.split(";");

                            for (let i = 0; i < cookies.length; i++) {
                                const cookie = cookies[i];
                                const eqPos = cookie.indexOf("=");
                                const nombre = eqPos > -1 ? cookie.substr(0, eqPos).trim() : cookie.trim();

                                // Eliminar cookie con diferentes configuraciones de path
                                document.cookie = nombre + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
                                document.cookie = nombre + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=" + window.location.hostname;
                                document.cookie = nombre + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=." + window.location.hostname;
                            }

                            console.log(" Cookies eliminadas automáticamente");
                        }

                        // Ejecutar limpieza inmediatamente
                        eliminarTodasLasCookies();

                        // Limpiar localStorage y sessionStorage también
                        try {
                            localStorage.clear();
                            sessionStorage.clear();
                            console.log(" Storage limpiado");
                        } catch(e) {
                            console.log("⚠️ No se pudo limpiar storage:", e);
                        }

                        // Esperar 2 segundos y recargar la página
                        setTimeout(function() {
                            console.log("🔄 Recargando página...");
                            window.location.href = "{{ url_for('autenticacion.iniciar_sesion') }}";
                        }, 2000);
                    </script>
                </body>
                </html>
                """

                # Renderizar template con Flask
                response = make_response(render_template_string(html_auto_fix))

                # Eliminar cookies desde el servidor también
                response.set_cookie('session', '', expires=0, path='/')
                response.set_cookie('csrf_token', '', expires=0, path='/')
                response.set_cookie('_csrf_token', '', expires=0, path='/')

                print("[CSRF ERROR]  Aplicando solución automática de limpieza de cookies")
                return response

            # Si no es Chrome o no se detectó el problema, flujo normal
            flash('Tu sesión ha sido limpiada automáticamente. Intenta iniciar sesión nuevamente.', 'warning')
            return redirect(url_for('autenticacion.iniciar_sesion'))

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
