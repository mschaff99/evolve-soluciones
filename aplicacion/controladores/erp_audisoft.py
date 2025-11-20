from flask import Blueprint, jsonify, render_template, redirect, url_for, flash
import os
import pymysql
from flask_login import login_required, current_user
from aplicacion.utilidades.inicializadores import csrf


def obtener_conexion_vicat(schema=None):
    """Intenta crear una conexión directa al servidor Vicat usando variables de entorno.

    Si no están definidas las variables de entorno para Vicat, retorna None.
    """
    host = os.getenv('DB_HOST_Vicat')
    if not host:
        return None

    user = os.getenv('DB_USER_Vicat', '')
    password = os.getenv('DB_PASSWORD_Vicat', '')
    port = int(os.getenv('DB_PORT_Vicat', 3306))
    # Si se entrega schema explícito, usarlo; si no, usar la DB configurada en env
    database = schema or os.getenv('DB_NAME_Vicat')

    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset='utf8',
            connect_timeout=30,
            autocommit=False
        )
        return conn
    except Exception:
        # Dejar que el llamador maneje el error (500)
        raise


erp_audisoft_bp = Blueprint('erp_audisoft', __name__)


@erp_audisoft_bp.route('/<base_datos>/erp-audisoft')
@login_required
def erp_audisoft_base_datos_view(base_datos):
    """Vista tenant-aware que renderiza la UI del módulo ERP Audisoft.

    Si el usuario no tiene acceso al tenant (y no es administrador), redirige al login.
    """
    try:
        # Validación simple: si no es admin y la base de datos del usuario no coincide, negar
        if not current_user.es_administrador() and getattr(current_user, 'base_datos_mysql', None) != base_datos:
            flash(f'No tienes acceso a la base de datos "{base_datos}"', 'error')
            return redirect(url_for('autenticacion.iniciar_sesion'))

        return render_template('erp_audisoft/reporte.html', base_datos=base_datos)
    except Exception as e:
        print(f"Error cargando ERP Audisoft para {base_datos}: {e}")
        return redirect(url_for('autenticacion.iniciar_sesion'))



@erp_audisoft_bp.route('/api/asignacion-datos', methods=['POST'])
@csrf.exempt
def api_asignacion_datos_root():
    """Endpoint global para ejecutar la asignación de datos.

    Este endpoint hace lo mismo que la implementación histórica en `app.py`.
    Se mantiene aquí para compatibilidad con la UI que realiza POST a `/api/asignacion-datos`.
    """
    # Permitir deshabilitar por configuración de entorno
    if os.getenv('ENABLE_ASIGNACION_DATOS', 'true').lower() != 'true':
        return jsonify({'success': False, 'error': 'Endpoint deshabilitado por configuración'}), 404

    # Schema/DB objetivo (por defecto intentar leer de env, si no usar DB configurada)
    target_schema = os.getenv('ASIGNACION_DB', os.getenv('DB_NAME_Vicat', os.getenv('DB_NAME', 'd76893540')))

    try:
        # Preferir conexión a Vicat si está configurada; si no, usar conexión local
        connection = None
        used_source = 'none'
        try:
            connection = obtener_conexion_vicat(target_schema)
            used_source = 'vicat'
        except Exception:
            connection = None

        if connection is None:
            from aplicacion.modelos.base_datos import obtener_conexion_local
            connection = obtener_conexion_local(target_schema)
            used_source = 'local'

        print(f"[ERP_AUDISOFT] asignacion-datos -> usando conexión: {used_source}, schema: {target_schema}")
        cursor = connection.cursor()

        # Verificar tablas necesarias
        required_tables = ['documentoscompras', 'asociar_oc_ingreso', 'cont_egresosautomaticos']
        missing = []
        for t in required_tables:
            cursor.execute(
                "SELECT COUNT(*) as cnt FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
                (target_schema, t)
            )
            r = cursor.fetchone()
            # r puede ser tuple o dict según cursor; manejar ambas posibilidades
            cnt = None
            if isinstance(r, dict):
                cnt = r.get('cnt', 0)
            elif isinstance(r, (list, tuple)) and len(r) > 0:
                cnt = r[0]
            else:
                # Fallback: considerar inexistente
                cnt = 0

            if not cnt:
                missing.append(t)

        if missing:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                connection.close()
            except Exception:
                pass
            
            error_msg = f"Módulo ERP Audisoft no disponible para la base de datos '{target_schema}'. "
            error_msg += f"Tablas faltantes: {', '.join(missing)}. "
            error_msg += "Este módulo solo funciona con bases de datos que tengan el esquema ERP Audisoft instalado."
            
            print(f"ADVERTENCIA: {error_msg}")
            
            return jsonify({
                'success': False,
                'error': error_msg,
                'missing_tables': missing,
                'schema': target_schema,
                'used_source': used_source,
                'help': 'Verifique que esté accediendo al tenant correcto o configure ASIGNACION_DB en las variables de entorno'
            }), 400

        try:
            connection.begin()

            sql1 = f"""
            UPDATE {target_schema}.documentoscompras a
                JOIN {target_schema}.asociar_oc_ingreso b
                ON a.codigo_documentoscompras = b.tipo
                   AND a.numero_documentoscompras = b.numero
                   AND a.proveedor_documentoscompras = b.rut
                SET a.observacion = CONCAT('OC ', CAST(b.numero_oc AS CHAR))
                WHERE b.tipo_oc = %s
                   AND a.periodocontable_documentoscompras > %s
            """

            try:
                cursor.execute(sql1, (801, 202503))
            except pymysql.err.ProgrammingError as pe:
                if getattr(pe, 'args', None) and pe.args[0] == 1146:
                    connection.rollback()
                    return jsonify({'success': False, 'error': 'Tabla requerida no existe en la base de datos', 'code': 1146}), 400
                raise

            affected1 = cursor.rowcount

            sql2 = f"""
            UPDATE {target_schema}.cont_egresosautomaticos a
            LEFT JOIN {target_schema}.documentoscompras b
            ON a.tipodoc=b.codigo_documentoscompras
               AND a.numerodoc=b.numero_documentoscompras
               AND a.rut_documento=b.proveedor_documentoscompras
            SET a.glosa=b.observacion
            WHERE a.numeroegreso=0
            """

            try:
                cursor.execute(sql2)
            except pymysql.err.ProgrammingError as pe:
                if getattr(pe, 'args', None) and pe.args[0] == 1146:
                    connection.rollback()
                    return jsonify({'success': False, 'error': 'Tabla requerida no existe en la base de datos', 'code': 1146}), 400
                raise

            affected2 = cursor.rowcount

            connection.commit()

            return jsonify({
                'success': True,
                'message': f'Actualizadas {affected1} filas (consulta1), {affected2} filas (consulta2)',
                'used_source': used_source,
                'schema': target_schema
            })

        except Exception as e:
            try:
                connection.rollback()
            except Exception:
                pass
            return jsonify({'success': False, 'error': 'Error al ejecutar asignación de datos', 'details': str(e), 'used_source': used_source}), 500

        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                connection.close()
            except Exception:
                pass

    except Exception as e:
        return jsonify({'success': False, 'error': 'Error de conexión a la base de datos', 'details': str(e), 'used_source': used_source}), 500


@erp_audisoft_bp.route('/api/asignacion-pagos', methods=['POST'])
@csrf.exempt
def api_asignacion_pagos_root():
    """Endpoint global para ejecutar la asignación de pagos (compatibilidad UI)."""
    if os.getenv('ENABLE_ASIGNACION_PAGOS', 'true').lower() != 'true':
        return jsonify({'success': False, 'error': 'Endpoint deshabilitado por configuración'}), 404

    target_schema = os.getenv('ASIGNACION_PAGOS_DB', os.getenv('DB_NAME_Vicat', os.getenv('DB_NAME', 'd76893540')))

    required_tables = [
        'documentosventas',
        'co_tr_det_ctacte',
        'co_tr_det_vouchers',
        'co_tmcuentas'
    ]

    try:
        # Preferir conexión a Vicat si está configurada; si no, usar conexión local
        from aplicacion.modelos.base_datos import obtener_conexion_local

        conn = None
        used_source = 'none'
        try:
            conn = obtener_conexion_vicat(target_schema)
            used_source = 'vicat'
        except Exception:
            conn = None

        if conn is None:
            conn = obtener_conexion_local(target_schema)
            used_source = 'local'

        print(f"[ERP_AUDISOFT] asignacion-pagos -> usando conexión: {used_source}, schema: {target_schema}")
        cur = conn.cursor()

        missing = []
        for t in required_tables:
            cur.execute(
                "SELECT COUNT(*) as cnt FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
                (target_schema, t)
            )
            r = cur.fetchone()
            cnt = None
            if isinstance(r, dict):
                cnt = r.get('cnt', 0)
            elif isinstance(r, (list, tuple)) and len(r) > 0:
                cnt = r[0]
            else:
                cnt = 0

            if not cnt:
                missing.append(t)

        if missing:
            try:
                conn.close()
            except Exception:
                pass
            
            error_msg = f"Módulo ERP Audisoft (Pagos) no disponible para la base de datos '{target_schema}'. "
            error_msg += f"Tablas faltantes: {', '.join(missing)}. "
            error_msg += "Este módulo solo funciona con bases de datos que tengan el esquema ERP Audisoft instalado."
            
            print(f"ADVERTENCIA: {error_msg}")
            
            return jsonify({
                'success': False,
                'error': error_msg,
                'missing_tables': missing,
                'schema': target_schema,
                'used_source': used_source,
                'help': 'Verifique que esté accediendo al tenant correcto o configure ASIGNACION_PAGOS_DB en las variables de entorno'
            }), 400

        try:
            conn.begin()

            sql1 = f"""
            UPDATE {target_schema}.documentosventas a
            SET a.observacion = ''
            WHERE a.periodocontable_documentosventas > %s
            """
            cur.execute(sql1, (202500,))
            affected1 = cur.rowcount

            sql2 = f"""
            UPDATE {target_schema}.documentosventas AS dv
                            LEFT JOIN (
                                SELECT
                                    a.codigo_documentosventas,
                                    a.numero_documentosventas,
                                    a.proveedor_documentosventas,
                                    CONCAT(d.nombre, ' ', c.fecha) AS glosa
                                FROM {target_schema}.documentosventas a
                                LEFT JOIN {target_schema}.co_tr_det_ctacte b ON a.codigo_documentosventas = b.tipo_docto
                                                        AND a.numero_documentosventas = b.num_docto
                                                        AND a.proveedor_documentosventas = b.rut_cliente
                                LEFT JOIN {target_schema}.co_tr_det_vouchers c ON b.tipo_voucher = c.tipo
                                                            AND b.numero_voucher = c.numero
                                LEFT JOIN {target_schema}.co_tmcuentas d ON d.codigo = c.cuenta
                                WHERE a.periodocontable_documentosventas > 202500
                                AND c.cuenta NOT IN (101201, 101203, 302001,406004,407005)
                                AND c.tipo <> 15
                            ) AS subquery ON dv.codigo_documentosventas = subquery.codigo_documentosventas
                                        AND dv.numero_documentosventas = subquery.numero_documentosventas
                                        AND dv.proveedor_documentosventas = subquery.proveedor_documentosventas
                            SET dv.observacion = subquery.glosa
                            WHERE dv.periodocontable_documentosventas > 202500
            """
            cur.execute(sql2)
            affected2 = cur.rowcount

            sql3 = f"""
                UPDATE {target_schema}.documentosventas AS dv
                LEFT JOIN (
                    SELECT
                        a.cod_docume_ref,
                        a.num_docume_ref,
                        CONCAT('NC ', a.num_docume) AS glosa
                    FROM {target_schema}.dte_info_referencia a
                    WHERE a.cod_docume = 61
                ) AS subquery ON dv.codigo_documentosventas = subquery.cod_docume_ref AND dv.numero_documentosventas = subquery.num_docume_ref
                SET dv.observacion = subquery.glosa
                WHERE dv.observacion IS NULL;

            """
            cur.execute(sql3)
            affected3 = cur.rowcount

            conn.commit()

            return jsonify({
                'success': True,
                'message': f'Consulta1: {affected1} filas afectadas, Consulta2: {affected2} filas afectadas, Consulta3: {affected3} filas afectadas',
                'used_source': used_source,
                'schema': target_schema
            })

        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            return jsonify({'success': False, 'error': 'Error al ejecutar asignacion-pagos', 'details': str(e), 'used_source': used_source}), 500

        finally:
            try:
                cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

    except Exception as e:
        return jsonify({'success': False, 'error': 'Error de conexión a la base de datos', 'details': str(e), 'used_source': used_source}), 500
