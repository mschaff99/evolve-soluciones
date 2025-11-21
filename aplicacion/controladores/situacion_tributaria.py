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


@situacion_tributaria_bp.route('/<base_datos>/situacion-tributaria/debug/<rut>')
@login_required
@requiere_modulo('empresas')
def debug_situacion_tributaria(base_datos, rut):
    """Debug: muestra los datos crudos que se pasan al template"""
    try:
        servicio = ServicioSituacionTributaria(base_datos)
        datos = servicio.obtener_situacion_por_rut(rut)

        # Extraer información de DJ para debug
        debug_info = {
            'resumen_anual': datos.get('dj', {}).get('resumen_anual', {}),
            'dj_numeros': []
        }

        # Simular lo que hace el template
        resumen_anual = datos.get('dj', {}).get('resumen_anual', {})
        dj_numeros_set = set()

        for anio, djs_anio in resumen_anual.items():
            for dj in djs_anio:
                if dj['dj_numero'] not in dj_numeros_set:
                    dj_numeros_set.add(dj['dj_numero'])

                    # Buscar el DJ con título
                    encontrado = None
                    for a in sorted(resumen_anual.keys(), reverse=True):
                        for d in resumen_anual[a]:
                            if d['dj_numero'] == dj['dj_numero']:
                                encontrado = d
                                break
                        if encontrado:
                            break

                    debug_info['dj_numeros'].append({
                        'dj_numero': dj['dj_numero'],
                        'titulo': encontrado.get('titulo', 'NO ENCONTRADO') if encontrado else 'ENCONTRADO ES NONE',
                        'encontrado_completo': encontrado
                    })

        return jsonify({'exito': True, 'debug': debug_info})
    except Exception as e:
        import traceback
        return jsonify({'exito': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500

