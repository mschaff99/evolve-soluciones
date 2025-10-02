"""
Controlador de Consulta Integral F29 para Evolve Soluciones
===========================================================

Maneja todas las rutas relacionadas con la consulta integral de formularios F29,
incluyendo visualización de datos, filtros y observaciones.
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
# from flask_login import login_required, current_user  # Comentado temporalmente
from datetime import datetime
import pymysql

# from aplicacion.utilidades.decoradores import acceso_empresa_requerido  # Comentado temporalmente
from aplicacion.servicios.servicio_consulta_integral import ServicioConsultaIntegral

# Crear blueprint para consulta integral F29
consulta_integral_f29_bp = Blueprint('consulta_integral_f29', __name__, url_prefix='/consulta-integral-f29')


@consulta_integral_f29_bp.route('/probar-conexion')
# @login_required  # Comentado temporalmente
def probar_conexion():
    """Endpoint para probar la conexión a la base de datos evolve"""
    try:
        servicio_consulta = ServicioConsultaIntegral()
        conexion = servicio_consulta.obtener_conexion_evolve()

        with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT COUNT(*) as total_empresas FROM empresas LIMIT 1")
            resultado = cursor.fetchone()

        conexion.close()

        return jsonify({
            'exito': True,
            'mensaje': 'Conexión exitosa a base de datos evolve',
            'total_empresas': resultado['total_empresas'] if resultado else 0
        })

    except Exception as error:
        return jsonify({
            'exito': False,
            'error': str(error)
        }), 500


@consulta_integral_f29_bp.route('/')
# @login_required  # Comentado temporalmente
# @acceso_empresa_requerido  # Comentado temporalmente
def inicio_consulta_integral():
    """Ruta principal para la Consulta Integral F29 - Redirige a dashboard"""
    from flask_login import current_user
    if current_user.is_authenticated:
        base_datos = current_user.base_datos_mysql or 'stratex'
        return redirect(f'/{base_datos}/consulta-integral-f29')
    else:
        return redirect(url_for('autenticacion.iniciar_sesion'))


# RUTA ELIMINADA - Causaba bucle de redirección
# La vista principal ahora se maneja en rutas_dinamicas.py
# @consulta_integral_f29_bp.route('/vista', methods=['GET', 'POST'])
# def vista_principal():
#     ...eliminada...


@consulta_integral_f29_bp.route('/api/observaciones/<rut>/<int:periodo>')
# @login_required  # Comentado temporalmente
# @acceso_empresa_requerido  # Comentado temporalmente
def obtener_observaciones(rut, periodo):
    """Obtener observaciones de un período específico"""
    try:
        servicio_consulta = ServicioConsultaIntegral()
        conexion = servicio_consulta.obtener_conexion_evolve()

        # Limpiar el RUT para que coincida con el formato en BD
        rut_limpio = servicio_consulta.limpiar_rut(rut)

        print(f"[DEBUG] Buscando observaciones para RUT: {rut} -> {rut_limpio}, Periodo: {periodo}")

        with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
            # Primero verificar si existe el registro en consulta_integral
            sql_verificacion = """
            SELECT id, rut, periodo
            FROM stratex.consulta_integral
            WHERE rut = %s AND periodo = %s
            """

            # Probar diferentes formatos de RUT
            formatos_rut = [
                rut,  # Original
                rut_limpio,  # Sin puntos
                rut.replace('.', '').replace('-', '')  # Sin puntos ni guión
            ]

            consulta_id = None
            rut_encontrado = None

            for formato in formatos_rut:
                print(f"[DEBUG] Probando formato: '{formato}'")
                cursor.execute(sql_verificacion, [formato, periodo])
                resultado = cursor.fetchone()

                if resultado:
                    consulta_id = resultado['id']
                    rut_encontrado = formato
                    print(f"[DEBUG] Encontrado consulta_integral.id = {consulta_id} para RUT: {formato}")
                    break

            if not consulta_id:
                print(f"[WARN] No se encontro registro en consulta_integral para RUT: {rut} / Periodo: {periodo}")
                return jsonify({
                    'exito': True,
                    'observaciones': [],
                    'total': 0,
                    'rut': rut,
                    'periodo': periodo,
                    'mensaje': 'No se encontró el período en consulta_integral'
                })

            # Consulta para obtener observaciones
            sql_observaciones = """
            SELECT a.*, b.rut as consulta_rut, b.periodo as consulta_periodo
            FROM stratex.observaciones a
            INNER JOIN consulta_integral b ON a.consulta_id = b.id
            WHERE a.consulta_id = %s
            ORDER BY a.fecha_creacion DESC
            """

            cursor.execute(sql_observaciones, [consulta_id])
            observaciones = cursor.fetchall()

            print(f"[DEBUG] Encontradas {len(observaciones)} observaciones para consulta_id: {consulta_id}")

        conexion.close()

        return jsonify({
            'exito': True,
            'observaciones': observaciones,
            'total': len(observaciones),
            'rut': rut,
            'periodo': periodo,
            'consulta_id': consulta_id,
            'rut_encontrado': rut_encontrado
        })

    except Exception as error:
        print(f"[ERROR] Error obteniendo observaciones: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'exito': False,
            'error': str(error)
        }), 500


@consulta_integral_f29_bp.route('/api/empresa/<rut>/detalles')
# @login_required  # Comentado temporalmente
# @acceso_empresa_requerido  # Comentado temporalmente
def obtener_detalles_empresa(rut):
    """API endpoint para obtener detalles específicos de una empresa"""
    try:
        servicio_consulta = ServicioConsultaIntegral()
        detalles = servicio_consulta.obtener_detalles_empresa_por_rut(rut)

        return jsonify({
            'exito': True,
            'datos': detalles
        })

    except Exception as error:
        print(f"Error obteniendo detalles de empresa {rut}: {error}")
        return jsonify({
            'exito': False,
            'error': str(error)
        }), 500


@consulta_integral_f29_bp.route('/api/exportar', methods=['POST'])
# @login_required  # Comentado temporalmente
# @acceso_empresa_requerido  # Comentado temporalmente
def exportar_datos():
    """API endpoint para exportar datos de consulta integral a Excel"""
    try:
        filtros = request.json if request.is_json else {}
        servicio = ServicioConsultaIntegral()
        # Obtener datos según filtros para exportar
        datos_empresas = servicio.obtener_datos_empresas_con_periodos(filtros)
        buffer_excel = servicio.exportar_a_excel(datos_empresas)
        if buffer_excel is None:
            return jsonify({'exito': False, 'error': 'No se pudo generar el Excel'}), 500

        # Nota: Aquí podríamos enviar el archivo directamente como attachment, pero
        # para mantenerlo simple respondemos con un indicador de éxito y el tamaño.
        tamaño = len(buffer_excel.getvalue()) if hasattr(buffer_excel, 'getvalue') else 0
        return jsonify({'exito': True, 'mensaje': 'Datos exportados exitosamente', 'bytes': tamaño})

    except Exception as error:
        print(f"Error exportando datos: {error}")
        return jsonify({'exito': False, 'error': str(error)}), 500


@consulta_integral_f29_bp.route('/api/estadisticas')
# @login_required  # Comentado temporalmente
# @acceso_empresa_requerido  # Comentado temporalmente
def obtener_estadisticas_generales():
    """API endpoint para obtener estadísticas generales de la consulta integral"""
    try:
        servicio_consulta = ServicioConsultaIntegral()
        estadisticas = servicio_consulta.obtener_estadisticas_generales()

        return jsonify({
            'exito': True,
            'estadisticas': estadisticas
        })

    except Exception as error:
        print(f"Error obteniendo estadísticas: {error}")
        return jsonify({
            'exito': False,
            'error': str(error)
        }), 500


@consulta_integral_f29_bp.route('/api/exportar-observaciones-excel')
# @login_required  # Comentado temporalmente
def exportar_observaciones_excel():
    """
    Exporta las observaciones del usuario actual a Excel

    Returns:
        Archivo Excel con las observaciones
    """
    from flask_login import current_user
    from flask import send_file
    from datetime import datetime

    try:
        # Verificar autenticación
        if not current_user.is_authenticated:
            return jsonify({
                'exito': False,
                'error': 'Usuario no autenticado'
            }), 401

        # Obtener nombre de usuario
        nombre_usuario = current_user.nombre_usuario

        print(f"📊 Exportando observaciones para usuario: {nombre_usuario}")

        # Generar Excel
        servicio_consulta = ServicioConsultaIntegral()
        buffer_excel = servicio_consulta.exportar_observaciones_usuario_excel(nombre_usuario)

        if not buffer_excel:
            return jsonify({
                'exito': False,
                'error': 'No se encontraron observaciones para exportar'
            }), 404

        # Generar nombre del archivo
        fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f'Observaciones_{nombre_usuario}_{fecha_actual}.xlsx'

        print(f"✅ Excel generado exitosamente: {nombre_archivo}")

        # Enviar archivo
        return send_file(
            buffer_excel,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=nombre_archivo
        )

    except Exception as error:
        print(f"❌ Error exportando observaciones: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'exito': False,
            'error': str(error)
        }), 500
