"""
Controlador de Situación Tributaria
===================================

Pantalla unificada que muestra, para una empresa, su situación en F29 y DJ.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user

from aplicacion.utilidades.decoradores import requiere_modulo
from aplicacion.servicios.servicio_situacion_tributaria import ServicioSituacionTributaria


situacion_tributaria_bp = Blueprint('situacion_tributaria', __name__)


@situacion_tributaria_bp.route('/<base_datos>/situacion-tributaria')
@login_required
@requiere_modulo('empresas')
def situacion_tributaria_inicio(base_datos):
    """
    Vista principal de Situación Tributaria.
    - Muestra formulario de búsqueda por RUT.
    - Opción de cambiar base de datos via URL segmentada.
    """
    rut = request.args.get('rut', '').strip()
    datos = None

    if rut:
        servicio = ServicioSituacionTributaria(base_datos)
        datos = servicio.obtener_situacion_por_rut(rut)

    return render_template(
        'paginas/situacion_tributaria.html',
        base_datos=base_datos,
        rut_busqueda=rut,
        datos=datos
    )


@situacion_tributaria_bp.route('/<base_datos>/situacion-tributaria/api/<rut>')
@login_required
@requiere_modulo('empresas')
def api_situacion_tributaria(base_datos, rut):
    """API: retorna JSON consolidado (F29 + DJ) para un RUT"""
    try:
        servicio = ServicioSituacionTributaria(base_datos)
        datos = servicio.obtener_situacion_por_rut(rut)
        return jsonify({'exito': True, 'datos': datos})
    except Exception as e:
        return jsonify({'exito': False, 'error': str(e)}), 500


