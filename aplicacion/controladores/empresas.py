"""
Controlador de Gestión de Empresas para Evolve Soluciones
==========================================================

Maneja las rutas para gestión de empresas y credenciales SII.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from aplicacion.servicios.servicio_empresas import ServicioEmpresas
from aplicacion.utilidades.decoradores import requiere_modulo
from aplicacion.servicios.servicio_integracion_gci import ejecutar_automatico_opciones_1_y_3

# Crear blueprint sin url_prefix (se manejará en cada ruta)
empresas_bp = Blueprint('empresas', __name__)


@empresas_bp.route('/<base_datos>/empresas')
@login_required
@requiere_modulo('empresas')
def listar_empresas(base_datos):
    """
    Lista todas las empresas con sus credenciales SII

    URL: /<base_datos>/empresas
    """
    try:
        # Inicializar servicio
        servicio = ServicioEmpresas(base_datos)

        # Aplicar filtros según rol del usuario
        filtros = {}
        if not current_user.es_administrador():
            filtros['usuario_filtro'] = current_user.nombre_usuario

        # Obtener búsqueda si existe
        buscar = request.args.get('buscar', '').strip()
        if buscar:
            filtros['buscar'] = buscar

        # Obtener empresas
        empresas = servicio.obtener_todas_empresas_con_credenciales(filtros)

        # Obtener estadísticas
        estadisticas = servicio.obtener_estadisticas()

        return render_template(
            'paginas/empresas/listar.html',
            base_datos=base_datos,
            empresas=empresas,
            estadisticas=estadisticas,
            buscar=buscar
        )

    except Exception as e:
        print(f"Error listando empresas: {e}")
        import traceback
        traceback.print_exc()
        flash('Error cargando empresas', 'error')
        return redirect(url_for('rutas_dinamicas.inicio_base_datos', base_datos=base_datos))


@empresas_bp.route('/<base_datos>/empresas/nueva')
@login_required
@requiere_modulo('empresas')
def nueva_empresa(base_datos):
    """
    Formulario para crear nueva empresa

    URL: /<base_datos>/empresas/nueva
    """
    servicio = ServicioEmpresas(base_datos)
    auditores = servicio.obtener_auditores_activos()

    return render_template(
        'paginas/empresas/formulario.html',
        base_datos=base_datos,
        empresa=None,
        auditores=auditores,
        accion='crear'
    )


@empresas_bp.route('/<base_datos>/empresas/editar/<rut>')
@login_required
@requiere_modulo('empresas')
def editar_empresa(base_datos, rut):
    """
    Formulario para editar empresa existente

    URL: /<base_datos>/empresas/editar/<rut>
    """
    try:
        servicio = ServicioEmpresas(base_datos)
        empresa = servicio.obtener_empresa_por_rut(rut)
        auditores = servicio.obtener_auditores_activos()

        if not empresa:
            flash(f'Empresa con RUT {rut} no encontrada', 'error')
            return redirect(url_for('empresas.listar_empresas', base_datos=base_datos))

        return render_template(
            'paginas/empresas/formulario.html',
            base_datos=base_datos,
            empresa=empresa,
            auditores=auditores,
            accion='editar'
        )

    except Exception as e:
        print(f"Error cargando empresa {rut}: {e}")
        flash('Error cargando empresa', 'error')
        return redirect(url_for('empresas.listar_empresas', base_datos=base_datos))


@empresas_bp.route('/<base_datos>/empresas/api/crear', methods=['POST'])
@login_required
@requiere_modulo('empresas')
def api_crear_empresa(base_datos):
    """
    API para crear nueva empresa

    URL: /<base_datos>/empresas/api/crear
    Method: POST
    """
    try:
        datos = request.get_json()

        if not datos or not datos.get('run_rut') or not datos.get('empresa'):
            return jsonify({
                'exito': False,
                'error': 'RUT y nombre de empresa son obligatorios'
            }), 400

        servicio = ServicioEmpresas(base_datos)
        exito = servicio.crear_empresa(datos, current_user.nombre_usuario)

        if exito:
            return jsonify({
                'exito': True,
                'mensaje': 'Empresa creada exitosamente',
                'rut': datos.get('run_rut')
            })
        else:
            return jsonify({
                'exito': False,
                'error': 'Error al crear empresa'
            }), 500

    except Exception as e:
        print(f"Error en API crear empresa: {e}")
        return jsonify({
            'exito': False,
            'error': str(e)
        }), 500


@empresas_bp.route('/<base_datos>/empresas/api/actualizar/<rut>', methods=['PUT', 'POST'])
@login_required
@requiere_modulo('empresas')
def api_actualizar_empresa(base_datos, rut):
    """
    API para actualizar empresa existente

    URL: /<base_datos>/empresas/api/actualizar/<rut>
    Method: PUT/POST
    """
    try:
        datos = request.get_json()

        if not datos:
            return jsonify({
                'exito': False,
                'error': 'No se recibieron datos'
            }), 400

        # Validar que la empresa existe
        servicio = ServicioEmpresas(base_datos)
        empresa_existe = servicio.obtener_empresa_por_rut(rut)

        if not empresa_existe:
            return jsonify({
                'exito': False,
                'error': f'La empresa con RUT {rut} no existe. Use el endpoint /api/crear para crear nuevas empresas.'
            }), 404

        # Actualizar empresa
        exito = servicio.actualizar_empresa(rut, datos)

        if exito:
            return jsonify({
                'exito': True,
                'mensaje': 'Empresa actualizada exitosamente'
            })
        else:
            return jsonify({
                'exito': False,
                'error': 'No se pudo actualizar la empresa. Revise los logs del servidor.'
            }), 500

    except Exception as e:
        print(f"ERROR: Error en API actualizar empresa {rut}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'exito': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500


@empresas_bp.route('/<base_datos>/empresas/api/credencial/<rut>', methods=['POST'])
@login_required
@requiere_modulo('empresas')
def api_guardar_credencial(base_datos, rut):
    """
    API para guardar/actualizar credencial SII

    URL: /<base_datos>/empresas/api/credencial/<rut>
    Method: POST
    """
    try:
        datos = request.get_json()
        clave = datos.get('clave', '').strip()

        if not clave:
            return jsonify({
                'exito': False,
                'error': 'La clave no puede estar vacía'
            }), 400

        servicio = ServicioEmpresas(base_datos)
        exito = servicio.guardar_credencial_sii(rut, clave)

        if exito:
            try:
                # Disparar en segundo plano la opción 5 (no bloquear respuesta)
                ejecutar_automatico_opciones_1_y_3(rut, base_datos)
            except Exception:
                # No interrumpir la respuesta al cliente por errores en el disparo
                pass

            return jsonify({
                'exito': True,
                'mensaje': 'Credencial SII guardada. Opción 5 ejecutándose en segundo plano.'
            })
        else:
            return jsonify({
                'exito': False,
                'error': 'Error al guardar credencial'
            }), 500

    except Exception as e:
        print(f"Error en API guardar credencial: {e}")
        return jsonify({
            'exito': False,
            'error': str(e)
        }), 500


@empresas_bp.route('/<base_datos>/empresas/api/credencial/<rut>', methods=['DELETE'])
@login_required
@requiere_modulo('empresas')
def api_eliminar_credencial(base_datos, rut):
    """
    API para eliminar credencial SII

    URL: /<base_datos>/empresas/api/credencial/<rut>
    Method: DELETE
    """
    try:
        servicio = ServicioEmpresas(base_datos)
        exito = servicio.eliminar_credencial_sii(rut)

        if exito:
            return jsonify({
                'exito': True,
                'mensaje': 'Credencial SII eliminada'
            })
        else:
            return jsonify({
                'exito': False,
                'error': 'Error al eliminar credencial'
            }), 500

    except Exception as e:
        print(f"Error en API eliminar credencial: {e}")
        return jsonify({
            'exito': False,
            'error': str(e)
        }), 500


@empresas_bp.route('/<base_datos>/empresas/api/obtener/<rut>')
@login_required
@requiere_modulo('empresas')
def api_obtener_empresa(base_datos, rut):
    """
    API para obtener datos de una empresa

    URL: /<base_datos>/empresas/api/obtener/<rut>
    Method: GET
    """
    try:
        servicio = ServicioEmpresas(base_datos)
        empresa = servicio.obtener_empresa_por_rut(rut)

        if empresa:
            return jsonify({
                'exito': True,
                'empresa': empresa
            })
        else:
            return jsonify({
                'exito': False,
                'error': 'Empresa no encontrada'
            }), 404

    except Exception as e:
        print(f"Error en API obtener empresa: {e}")
        return jsonify({
            'exito': False,
            'error': str(e)
        }), 500


@empresas_bp.route('/<base_datos>/empresas/api/gci_status/<rut>')
@login_required
@requiere_modulo('empresas')
def api_gci_status(base_datos, rut):
    """
    Devuelve el estado de ejecución de GCI (opción 1 = F29, opción 3 = DJ) para un RUT,
    inspeccionando los archivos de logs generados en ./logs. Esto permite al cliente
    mostrar progreso mientras los procesos se ejecutan en segundo plano.
    """
    import glob
    import os

    try:
        logs_dir = os.path.join(os.getcwd(), 'logs')
        resultado = {
            'op1': {'exists': False, 'finished': False, 'log': ''},
            'op3': {'exists': False, 'finished': False, 'log': ''}
        }

        if not os.path.isdir(logs_dir):
            return jsonify(resultado)

        # Buscar el archivo más reciente para cada opción
        pattern1 = os.path.join(logs_dir, f"gci_opcion1_{rut}_*.log")
        pattern3 = os.path.join(logs_dir, f"gci_opcion3_{rut}_*.log")

        files1 = glob.glob(pattern1)
        files3 = glob.glob(pattern3)

        def inspect_latest(files):
            if not files:
                return {'exists': False, 'finished': False, 'log': ''}
            latest = max(files, key=os.path.getmtime)
            # Leer últimas líneas del log
            try:
                with open(latest, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                content = ''

            finished = False
            # Marcas que indican fin de ejecución
            markers = ['returncode=', 'ejecución secuencial finalizada', 'Proceso finalizado', 'Referencias internas limpiadas', 'Navegador cerrado']
            for m in markers:
                if m in content:
                    finished = True
                    break

            return {'exists': True, 'finished': finished, 'log': content[-8000:]}

        resultado['op1'] = inspect_latest(files1)
        resultado['op3'] = inspect_latest(files3)

        return jsonify(resultado)

    except Exception as e:
        print(f"Error obteniendo estado GCI para {rut}: {e}")
        return jsonify({'op1': {'exists': False, 'finished': False, 'log': ''}, 'op3': {'exists': False, 'finished': False, 'log': ''}}), 500
