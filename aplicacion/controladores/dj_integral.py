"""
Controlador de DJ Integral para Evolve Soluciones
=================================================

Maneja todas las rutas relacionadas con la consulta de Declaraciones Juradas (DJ),
incluyendo visualización de datos y filtros.
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import pymysql

from aplicacion.servicios.servicio_dj_integral import ServicioDJIntegral

# Crear blueprint para DJ Integral
dj_integral_bp = Blueprint('dj_integral', __name__, url_prefix='/dj-integral')


@dj_integral_bp.route('/')
@login_required
def inicio_dj_integral():
    """Ruta principal para DJ Integral - Redirige a dashboard"""
    if current_user.is_authenticated:
        base_datos = current_user.base_datos_mysql
        return redirect(f'/{base_datos}/dj-integral')
    else:
        return redirect(url_for('autenticacion.iniciar_sesion'))


@dj_integral_bp.route('/api/dj/<rut>')
@login_required
def obtener_dj_empresa(rut):
    """
    Obtener todas las DJ de una empresa específica

    Args:
        rut (str): RUT de la empresa

    Returns:
        JSON: Lista de DJ con sus estados por año
    """
    try:
        base_datos = current_user.base_datos_mysql
        servicio = ServicioDJIntegral(base_datos)

        dj_empresa = servicio.obtener_dj_por_rut(rut)

        return jsonify({
            'exito': True,
            'dj': dj_empresa
        })

    except Exception as e:
        print(f"ERROR: Error obteniendo DJ para RUT {rut}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'exito': False,
            'error': str(e)
        }), 500


@dj_integral_bp.route('/api/estadisticas')
@login_required
def obtener_estadisticas():
    """
    Obtener estadísticas generales de DJ

    Returns:
        JSON: Estadísticas de DJ
    """
    try:
        base_datos = current_user.base_datos_mysql
        servicio = ServicioDJIntegral(base_datos)

        estadisticas = servicio.obtener_estadisticas()

        return jsonify({
            'exito': True,
            'estadisticas': estadisticas
        })

    except Exception as e:
        print(f"ERROR: Error obteniendo estadísticas: {e}")
        return jsonify({
            'exito': False,
            'error': str(e)
        }), 500
