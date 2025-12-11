"""
Controlador de Suscripciones y Pagos - Evolve Soluciones SaaS
============================================================

Maneja rutas públicas y privadas relacionadas con suscripciones y pagos.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from datetime import datetime
from aplicacion.modelos.plan import Plan
from aplicacion.modelos.suscripcion import Suscripcion
from aplicacion.servicios.servicio_pagos import ServicioPagos
from aplicacion.utilidades.decoradores import solo_administradores

# Crear blueprint
suscripciones_bp = Blueprint('suscripciones', __name__, url_prefix='/suscripciones')


# =====================================================
# RUTAS PÚBLICAS - Landing y Planes
# =====================================================

@suscripciones_bp.route('/planes')
def ver_planes():
    """
    Página pública de planes de suscripción
    Muestra todos los planes disponibles con sus características
    """
    try:
        planes = Plan.obtener_planes_activos()
        
        # Enriquecer planes con información de módulos
        for plan in planes:
            plan.modulos = Plan.obtener_modulos_plan(plan.id)
        
        return render_template('paginas/suscripciones/planes.html', 
                             planes=planes,
                             titulo='Planes y Precios')
    except Exception as e:
        print(f"Error mostrando planes: {e}")
        flash('Error al cargar planes. Por favor intenta más tarde.', 'error')
        return redirect(url_for('autenticacion.iniciar_sesion'))


@suscripciones_bp.route('/comparar')
def comparar_planes():
    """
    Página de comparación detallada de planes
    """
    try:
        planes = Plan.obtener_planes_activos()
        
        # Preparar matriz de comparación
        for plan in planes:
            plan.modulos = Plan.obtener_modulos_plan(plan.id)
        
        return render_template('paginas/suscripciones/comparar_planes.html',
                             planes=planes,
                             titulo='Comparar Planes')
    except Exception as e:
        print(f"Error en comparación de planes: {e}")
        return redirect(url_for('suscripciones.ver_planes'))


# =====================================================
# RUTAS DE CHECKOUT Y PAGO
# =====================================================

@suscripciones_bp.route('/checkout/<string:codigo_plan>')
@login_required
def iniciar_checkout(codigo_plan):
    """
    Inicia el proceso de checkout para un plan
    
    Args:
        codigo_plan: Código del plan seleccionado
    """
    try:
        # Obtener plan
        plan = Plan.obtener_por_codigo(codigo_plan)
        if not plan:
            flash('Plan no encontrado.', 'error')
            return redirect(url_for('suscripciones.ver_planes'))
        
        # Obtener período desde query params (default: mensual)
        periodo = request.args.get('periodo', 'mensual')
        if periodo not in ['mensual', 'anual']:
            periodo = 'mensual'
        
        # Calcular precio
        precio = plan.precio_mensual if periodo == 'mensual' else plan.precio_anual
        
        return render_template('paginas/suscripciones/checkout.html',
                             plan=plan,
                             periodo=periodo,
                             precio=precio,
                             titulo=f'Checkout - Plan {plan.nombre}')
    
    except Exception as e:
        print(f"Error en checkout: {e}")
        flash('Error al iniciar proceso de pago.', 'error')
        return redirect(url_for('suscripciones.ver_planes'))


@suscripciones_bp.route('/procesar-pago', methods=['POST'])
@login_required
def procesar_pago():
    """
    Procesa el pago y crea la sesión en la pasarela
    """
    try:
        # Obtener datos del formulario
        id_plan = request.form.get('id_plan', type=int)
        periodo = request.form.get('periodo', 'mensual')
        pasarela = request.form.get('pasarela', 'stripe')
        
        if not id_plan:
            return jsonify({'success': False, 'error': 'Plan no especificado'})
        
        # Obtener información del usuario con validación
        id_base_datos = None
        if hasattr(current_user, 'base_datos_mysql') and current_user.base_datos_mysql:
            # Validar que el nombre de BD sea seguro (solo letras y guiones bajos)
            import re
            if not re.match(r'^[a-z0-9_]+$', current_user.base_datos_mysql):
                return jsonify({'success': False, 'error': 'Nombre de base de datos inválido'})
            
            # Obtener ID de la base de datos
            from aplicacion.modelos.base_datos import ejecutar_consulta_postgres
            consulta = "SELECT id FROM auth.bases_datos_mysql WHERE nombre_base_datos = %s AND activo = TRUE"
            resultado = ejecutar_consulta_postgres(consulta, (current_user.base_datos_mysql,), obtener_uno=True)
            if resultado:
                id_base_datos = resultado['id']
        
        if not id_base_datos:
            return jsonify({'success': False, 'error': 'Base de datos no encontrada o inactiva'})
        
        # Crear servicio de pagos
        servicio_pagos = ServicioPagos(pasarela=pasarela)
        
        # Crear sesión de checkout
        resultado = servicio_pagos.crear_checkout(
            id_plan=id_plan,
            id_base_datos=id_base_datos,
            periodo=periodo,
            email_cliente=current_user.email,
            success_url=url_for('suscripciones.pago_exitoso', _external=True),
            cancel_url=url_for('suscripciones.pago_cancelado', _external=True)
        )
        
        if resultado['success']:
            # Guardar información en sesión para confirmar después
            session['checkout_id'] = resultado.get('session_id') or resultado.get('preference_id')
            session['id_plan'] = id_plan
            session['periodo'] = periodo
            
            return jsonify({
                'success': True,
                'checkout_url': resultado['checkout_url']
            })
        else:
            return jsonify({
                'success': False,
                'error': resultado.get('error', 'Error al crear sesión de pago')
            })
    
    except Exception as e:
        print(f"Error procesando pago: {e}")
        return jsonify({'success': False, 'error': str(e)})


@suscripciones_bp.route('/pago-exitoso')
@login_required
def pago_exitoso():
    """Página de confirmación de pago exitoso"""
    return render_template('paginas/suscripciones/pago_exitoso.html',
                         titulo='¡Pago Exitoso!')


@suscripciones_bp.route('/pago-cancelado')
@login_required
def pago_cancelado():
    """Página cuando el usuario cancela el pago"""
    flash('El pago fue cancelado. Puedes intentar nuevamente cuando quieras.', 'info')
    return redirect(url_for('suscripciones.ver_planes'))


# =====================================================
# WEBHOOKS DE PASARELAS DE PAGO
# =====================================================

@suscripciones_bp.route('/webhook/stripe', methods=['POST'])
def webhook_stripe():
    """
    Webhook para procesar eventos de Stripe
    """
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        servicio_pagos = ServicioPagos(pasarela='stripe')
        resultado = servicio_pagos.procesar_webhook(payload, {'stripe-signature': sig_header})
        
        if resultado['success']:
            return jsonify({'received': True}), 200
        else:
            return jsonify({'error': resultado.get('error')}), 400
    
    except Exception as e:
        print(f"Error en webhook de Stripe: {e}")
        return jsonify({'error': str(e)}), 400


@suscripciones_bp.route('/webhook/mercadopago', methods=['POST'])
def webhook_mercadopago():
    """
    Webhook para procesar eventos de MercadoPago
    """
    try:
        payload = request.get_json()
        sig_header = request.headers.get('x-signature')
        
        servicio_pagos = ServicioPagos(pasarela='mercadopago')
        resultado = servicio_pagos.procesar_webhook(payload, {'x-signature': sig_header})
        
        if resultado['success']:
            return jsonify({'received': True}), 200
        else:
            return jsonify({'error': resultado.get('error')}), 400
    
    except Exception as e:
        print(f"Error en webhook de MercadoPago: {e}")
        return jsonify({'error': str(e)}), 400


# =====================================================
# PANEL DE GESTIÓN DE SUSCRIPCIÓN (Usuario)
# =====================================================

@suscripciones_bp.route('/mi-suscripcion')
@login_required
def mi_suscripcion():
    """
    Panel de gestión de suscripción del usuario actual
    Muestra información del plan actual, próximo cobro, etc.
    """
    try:
        # Obtener suscripción activa del tenant
        suscripcion = None
        if hasattr(current_user, 'base_datos_mysql') and current_user.base_datos_mysql:
            suscripcion = Suscripcion.obtener_por_base_datos(current_user.base_datos_mysql)
        
        plan_actual = None
        modulos_disponibles = []
        
        if suscripcion:
            plan_actual = Plan.obtener_por_id(suscripcion.id_plan)
            if plan_actual:
                modulos_disponibles = Plan.obtener_modulos_plan(plan_actual.id)
        
        # Obtener planes disponibles para upgrade/downgrade
        todos_planes = Plan.obtener_planes_activos()
        
        return render_template('paginas/suscripciones/mi_suscripcion.html',
                             suscripcion=suscripcion,
                             plan_actual=plan_actual,
                             modulos_disponibles=modulos_disponibles,
                             todos_planes=todos_planes,
                             titulo='Mi Suscripción')
    
    except Exception as e:
        print(f"Error mostrando suscripción: {e}")
        flash('Error al cargar información de suscripción.', 'error')
        return redirect(url_for('inicio'))


@suscripciones_bp.route('/cambiar-plan', methods=['POST'])
@login_required
def cambiar_plan():
    """
    Cambia el plan de suscripción del usuario (upgrade/downgrade)
    """
    try:
        nuevo_id_plan = request.form.get('nuevo_id_plan', type=int)
        aplicar_inmediatamente = request.form.get('inmediato', 'false') == 'true'
        
        if not nuevo_id_plan:
            return jsonify({'success': False, 'error': 'Plan no especificado'})
        
        # Obtener suscripción actual
        if not hasattr(current_user, 'base_datos_mysql') or not current_user.base_datos_mysql:
            return jsonify({'success': False, 'error': 'No se encontró base de datos'})
        
        suscripcion = Suscripcion.obtener_por_base_datos(current_user.base_datos_mysql)
        if not suscripcion:
            return jsonify({'success': False, 'error': 'No se encontró suscripción activa'})
        
        # Cambiar plan
        exito = Suscripcion.cambiar_plan(
            suscripcion.id,
            nuevo_id_plan,
            aplicar_inmediatamente
        )
        
        if exito:
            mensaje = 'Plan actualizado exitosamente' if aplicar_inmediatamente else 'El cambio se aplicará en la próxima renovación'
            return jsonify({'success': True, 'mensaje': mensaje})
        else:
            return jsonify({'success': False, 'error': 'Error al cambiar plan'})
    
    except Exception as e:
        print(f"Error cambiando plan: {e}")
        return jsonify({'success': False, 'error': str(e)})


@suscripciones_bp.route('/cancelar', methods=['POST'])
@login_required
def cancelar_suscripcion():
    """
    Cancela la suscripción del usuario
    """
    try:
        motivo = request.form.get('motivo', '')
        cancelar_inmediatamente = request.form.get('inmediato', 'false') == 'true'
        
        # Obtener suscripción actual
        if not hasattr(current_user, 'base_datos_mysql') or not current_user.base_datos_mysql:
            return jsonify({'success': False, 'error': 'No se encontró base de datos'})
        
        suscripcion = Suscripcion.obtener_por_base_datos(current_user.base_datos_mysql)
        if not suscripcion:
            return jsonify({'success': False, 'error': 'No se encontró suscripción activa'})
        
        # Cancelar suscripción
        exito = Suscripcion.cancelar_suscripcion(
            suscripcion.id,
            motivo,
            cancelar_inmediatamente
        )
        
        if exito:
            mensaje = 'Suscripción cancelada' if cancelar_inmediatamente else 'Tu suscripción se cancelará al final del período actual'
            return jsonify({'success': True, 'mensaje': mensaje})
        else:
            return jsonify({'success': False, 'error': 'Error al cancelar suscripción'})
    
    except Exception as e:
        print(f"Error cancelando suscripción: {e}")
        return jsonify({'success': False, 'error': str(e)})


# =====================================================
# PANEL DE ADMINISTRACIÓN (Solo Administradores)
# =====================================================

@suscripciones_bp.route('/admin/dashboard')
@login_required
@solo_administradores
def admin_dashboard():
    """
    Dashboard de administración de suscripciones
    Métricas de MRR, churn, clientes, etc.
    """
    try:
        from aplicacion.modelos.base_datos import ejecutar_consulta_postgres
        
        # Calcular MRR
        consulta_mrr = "SELECT auth.calcular_mrr() as mrr"
        mrr_resultado = ejecutar_consulta_postgres(consulta_mrr, obtener_uno=True)
        mrr = mrr_resultado['mrr'] if mrr_resultado else 0
        
        # Contar suscripciones activas
        consulta_activas = """
            SELECT COUNT(*) as total
            FROM auth.suscripciones
            WHERE estado IN ('activa', 'periodo_prueba')
        """
        activas = ejecutar_consulta_postgres(consulta_activas, obtener_uno=True)
        total_activas = activas['total'] if activas else 0
        
        # Suscripciones por vencer (próximos 7 días)
        suscripciones_por_vencer = Suscripcion.obtener_suscripciones_por_vencer(dias=7)
        
        # Distribución por plan
        consulta_distribucion = """
            SELECT p.nombre, COUNT(s.id) as total
            FROM auth.suscripciones s
            INNER JOIN auth.planes_suscripcion p ON s.id_plan = p.id
            WHERE s.estado IN ('activa', 'periodo_prueba')
            GROUP BY p.nombre
            ORDER BY total DESC
        """
        distribucion_planes = ejecutar_consulta_postgres(consulta_distribucion)
        
        return render_template('paginas/suscripciones/admin_dashboard.html',
                             mrr=mrr,
                             total_activas=total_activas,
                             suscripciones_por_vencer=suscripciones_por_vencer,
                             distribucion_planes=distribucion_planes,
                             titulo='Dashboard de Suscripciones')
    
    except Exception as e:
        print(f"Error en dashboard admin: {e}")
        flash('Error al cargar dashboard.', 'error')
        return redirect(url_for('inicio'))


@suscripciones_bp.route('/admin/suscripciones')
@login_required
@solo_administradores
def admin_listar_suscripciones():
    """
    Lista todas las suscripciones para administradores
    """
    try:
        from aplicacion.modelos.base_datos import ejecutar_consulta_postgres
        
        consulta = """
            SELECT s.*, bd.nombre_cliente, bd.nombre_base_datos, p.nombre as nombre_plan
            FROM auth.suscripciones s
            INNER JOIN auth.bases_datos_mysql bd ON s.id_base_datos = bd.id
            INNER JOIN auth.planes_suscripcion p ON s.id_plan = p.id
            ORDER BY s.fecha_creacion DESC
        """
        suscripciones = ejecutar_consulta_postgres(consulta)
        
        return render_template('paginas/suscripciones/admin_suscripciones.html',
                             suscripciones=suscripciones,
                             titulo='Gestión de Suscripciones')
    
    except Exception as e:
        print(f"Error listando suscripciones: {e}")
        flash('Error al cargar suscripciones.', 'error')
        return redirect(url_for('suscripciones.admin_dashboard'))
