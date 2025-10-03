"""
Controlador para rutas dinámicas basadas en la base de datos del usuario
Permite URLs como /stratex, /otra-base, etc.
"""

from flask import Blueprint, render_template, request, redirect, url_for, current_app, session, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from aplicacion.utilidades.filtros_empresas import obtener_empresas_usuario
from aplicacion.servicios.servicio_consulta_integral import ServicioConsultaIntegral

# Blueprint para rutas dinámicas
rutas_dinamicas_bp = Blueprint('rutas_dinamicas', __name__)


def validar_base_datos_usuario(base_datos):
    """
    Valida que el usuario tenga acceso a la base de datos especificada

    Args:
        base_datos (str): Nombre de la base de datos

    Returns:
        bool: True si el usuario tiene acceso, False si no
    """
    if not current_user.is_authenticated:
        return False

    # Si es administrador, puede acceder a cualquier base de datos
    if current_user.es_administrador():
        return True

    # Si no es administrador, solo puede acceder a su base de datos asignada
    return current_user.base_datos_mysql == base_datos


@rutas_dinamicas_bp.route('/<base_datos>')
@login_required
def dashboard_base_datos(base_datos):
    """
    Dashboard principal para una base de datos específica
    URL: /<base_datos> (ej: /stratex, /otra-base)
    """
    # Validar acceso a la base de datos
    if not validar_base_datos_usuario(base_datos):
        from flask import flash
        flash(f'No tienes acceso a la base de datos "{base_datos}"', 'error')
        return redirect(url_for('autenticacion.iniciar_sesion'))

    # Obtener empresas para esta base de datos
    try:
        empresas = obtener_empresas_usuario(current_user, campos="run_rut, empresa, auditor")

        # Estadísticas básicas
        total_empresas = len(empresas)
        empresas_por_auditor = {}
        for empresa in empresas:
            auditor = empresa.get('auditor', 'Sin asignar')
            empresas_por_auditor[auditor] = empresas_por_auditor.get(auditor, 0) + 1

        return render_template('paginas/dashboard_base_datos.html',
                             base_datos=base_datos,
                             total_empresas=total_empresas,
                             empresas_por_auditor=empresas_por_auditor,
                             empresas=empresas[:10])  # Mostrar solo las primeras 10

    except Exception as e:
        print(f"Error cargando dashboard para base {base_datos}: {e}")
        from flask import flash
        flash(f'Error cargando datos de la base de datos "{base_datos}"', 'error')
        return redirect(url_for('autenticacion.iniciar_sesion'))


@rutas_dinamicas_bp.route('/<base_datos>/consulta-integral-f29')
@login_required
def consulta_integral_f29_base_datos(base_datos):
    """
    Consulta Integral F29 para una base de datos específica
    URL: /<base_datos>/consulta-integral-f29
    """
    # Validar acceso a la base de datos
    if not validar_base_datos_usuario(base_datos):
        from flask import flash
        flash(f'No tienes acceso a la base de datos "{base_datos}"', 'error')
        return redirect(url_for('autenticacion.iniciar_sesion'))

    try:
        # Inicializar servicio
        servicio = ServicioConsultaIntegral()

        # Aplicar filtros según el rol del usuario
        filtros = {}

        # Si NO es administrador, filtrar por su usuario
        if not current_user.es_administrador():
            filtros['usuario_filtro'] = current_user.nombre_usuario

        # Obtener datos completos de empresas con períodos usando el servicio
        resultados = servicio.obtener_datos_empresas_con_periodos(filtros)

        # Obtener lista única de usuarios para el filtro
        usuarios = sorted(list(set(
            empresa.get('usuario')
            for empresa in resultados
            if empresa.get('usuario')
        )))

        # Obtener códigos únicos de observaciones para el filtro
        codigos_observaciones = servicio.obtener_codigos_observaciones_unicos()

        # Obtener años disponibles (de los períodos existentes)
        años_disponibles = set()
        for empresa in resultados:
            for (año, mes) in empresa.get('periodos', {}).keys():
                años_disponibles.add(año)
        años_disponibles = sorted(list(años_disponibles), reverse=True)

        # Si no hay años, usar el año actual por defecto
        if not años_disponibles:
            años_disponibles = [datetime.now().year]

        # Meses del año para las filas de detalle
        meses_del_año = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]

        # Renderizar el template directamente con todos los datos necesarios
        return render_template('paginas/consulta_integral_f29.html',
                             base_datos=base_datos,
                             resultados=resultados,
                             usuarios=usuarios,
                             codigos_observaciones=codigos_observaciones,
                             años_disponibles=años_disponibles,
                             meses_del_año=meses_del_año,
                             periodo_actual=int(f"{datetime.now().year}{datetime.now().month:02d}"))

    except Exception as e:
        print(f"Error cargando Consulta Integral F29 para {base_datos}: {e}")
        import traceback
        traceback.print_exc()
        from flask import flash
        flash('Error cargando la consulta integral', 'error')
        return redirect(url_for('rutas_dinamicas.dashboard_base_datos', base_datos=base_datos))


@rutas_dinamicas_bp.route('/<base_datos>/api/exportar-observaciones-excel')
@login_required
def exportar_observaciones_excel_base_datos(base_datos):
    """
    Exporta las observaciones del usuario actual a Excel
    URL: /<base_datos>/api/exportar-observaciones-excel
    """
    from flask import send_file
    from datetime import datetime

    # Validar acceso a la base de datos
    if not validar_base_datos_usuario(base_datos):
        return jsonify({
            'exito': False,
            'error': 'No tienes acceso a esta base de datos'
        }), 403

    try:
        # Determinar si es administrador para exportar todas las observaciones
        es_admin = current_user.es_administrador()
        nombre_usuario = current_user.nombre_usuario

        if es_admin:
            print(f"[EXPORT] Administrador exportando TODAS las observaciones en BD: {base_datos}")
        else:
            print(f"[EXPORT] Exportando observaciones para usuario: {nombre_usuario} en BD: {base_datos}")

        # Generar Excel
        servicio = ServicioConsultaIntegral()
        buffer_excel = servicio.exportar_observaciones_usuario_excel(
            nombre_usuario=nombre_usuario,
            es_administrador=es_admin
        )

        if not buffer_excel:
            return jsonify({
                'exito': False,
                'error': 'No se encontraron observaciones para exportar'
            }), 404

        # Generar nombre del archivo
        fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
        if es_admin:
            nombre_archivo = f'Observaciones_TODAS_{fecha_actual}.xlsx'
        else:
            nombre_archivo = f'Observaciones_{nombre_usuario}_{fecha_actual}.xlsx'

        print(f"[OK] Excel generado exitosamente: {nombre_archivo}")

        # Enviar archivo
        return send_file(
            buffer_excel,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=nombre_archivo
        )

    except Exception as error:
        print(f"[ERROR] Error exportando observaciones: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'exito': False,
            'error': str(error)
        }), 500


@rutas_dinamicas_bp.route('/<base_datos>/consolidado')
@login_required
def consolidado_base_datos(base_datos):
    """
    Consolidado para una base de datos específica
    URL: /<base_datos>/consolidado
    """
    # Validar acceso a la base de datos
    if not validar_base_datos_usuario(base_datos):
        from flask import flash
        flash(f'No tienes acceso a la base de datos "{base_datos}"', 'error')
        return redirect(url_for('autenticacion.iniciar_sesion'))

    # Redirigir al controlador original pero con contexto de base de datos
    return redirect(url_for('consolidado.dashboard'))


@rutas_dinamicas_bp.route('/<base_datos>/tareas')
@login_required
def tareas_base_datos(base_datos):
    """
    Gestión de tareas para una base de datos específica
    URL: /<base_datos>/tareas
    """
    # Validar acceso a la base de datos
    if not validar_base_datos_usuario(base_datos):
        from flask import flash
        flash(f'No tienes acceso a la base de datos "{base_datos}"', 'error')
        return redirect(url_for('autenticacion.iniciar_sesion'))

    # Redirigir al controlador original pero con contexto de base de datos
    return redirect(url_for('tareas.dashboard'))


@rutas_dinamicas_bp.route('/<base_datos>/observaciones')
@login_required
def observaciones_base_datos(base_datos):
    """
    Observaciones para una base de datos específica
    URL: /<base_datos>/observaciones
    """
    # Validar acceso a la base de datos
    if not validar_base_datos_usuario(base_datos):
        from flask import flash
        flash(f'No tienes acceso a la base de datos "{base_datos}"', 'error')
        return redirect(url_for('autenticacion.iniciar_sesion'))

    # Redirigir al controlador original pero con contexto de base de datos
    return redirect(url_for('observaciones.dashboard'))


@rutas_dinamicas_bp.before_request
def configurar_base_datos_contexto():
    """
    Middleware para configurar el contexto de la base de datos en la sesión
    """
    if current_user.is_authenticated and request.endpoint and request.endpoint.startswith('rutas_dinamicas'):
        # Extraer la base de datos de la URL
        if request.view_args:
            base_datos = request.view_args.get('base_datos')
            if base_datos:
                # Guardar en la sesión para que otros controladores puedan usarla
                session['base_datos_actual'] = base_datos
