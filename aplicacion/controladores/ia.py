"""
Rutas para integración con IA (Inteligencia Artificial)
Endpoints para análisis de balances y datos contables usando Gemini AI
"""

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from datetime import datetime
from aplicacion.utilidades.decoradores import solo_administradores, requiere_modulo
import traceback

# Crear blueprint para rutas de IA
ia_bp = Blueprint('ia', __name__, url_prefix='/ia')


@ia_bp.route('/test-gemini', methods=['GET'])
@login_required
@requiere_modulo('ia')
@solo_administradores
def probar_conexion_gemini():
    """Probar conexión con Gemini AI"""
    try:
        from aplicacion.servicios.servicio_gemini import gemini_service

        print(f"[TEST] Usuario {current_user.nombre_usuario} probando conexión con Gemini")

        resultado = gemini_service.test_connection()

        if resultado.get('success'):
            print(f" Conexión exitosa con Gemini AI")
            return jsonify({
                'estado': 'exitoso',
                'mensaje': 'Conexión exitosa con Gemini AI',
                'respuesta': resultado.get('response', ''),
                'timestamp': datetime.now().isoformat()
            })
        else:
            print(f"Error en conexión: {resultado.get('error')}")
            return jsonify({
                'estado': 'error',
                'mensaje': resultado.get('error', 'Error desconocido'),
                'timestamp': datetime.now().isoformat()
            }), 500

    except Exception as e:
        error_completo = traceback.format_exc()
        print(f"Error probando Gemini: {e}")
        print(f"Traceback completo:\n{error_completo}")

        return jsonify({
            'estado': 'error',
            'mensaje': f'Error al probar Gemini: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@ia_bp.route('/generar-balance', methods=['POST'])
@login_required
@requiere_modulo('ia')
def generar_balance_empresa():
    """Generar balance de 8 columnas para una empresa específica - Accesible para todos los usuarios"""
    import sys
    import logging
    logger = logging.getLogger('aplicacion_root')

    try:
        logger.info("[INICIO] Endpoint /ia/generar-balance llamado")
        print("[INICIO] Endpoint /ia/generar-balance llamado", file=sys.stderr, flush=True)

        datos = request.get_json()
        logger.info(f"[DATOS] Datos recibidos: {datos}")
        print(f"[DATOS] Datos recibidos: {datos}", file=sys.stderr, flush=True)

        if not datos:
            logger.error("[ERROR] No se proporcionaron datos")
            return jsonify({
                'estado': 'error',
                'mensaje': 'No se proporcionaron datos'
            }), 400

        empresa_rut = datos.get('empresa_rut')
        anio_inicio = datos.get('anio_inicio', 2025)
        mes_inicio = datos.get('mes_inicio', 1)
        anio_fin = datos.get('anio_fin', 2025)
        mes_fin = datos.get('mes_fin', 8)

        if not empresa_rut:
            logger.error("[ERROR] empresa_rut no proporcionado")
            return jsonify({
                'estado': 'error',
                'mensaje': 'empresa_rut es requerido'
            }), 400

        logger.info(f"[BALANCE] Generando balance: RUT={empresa_rut}, Periodo={anio_inicio}/{mes_inicio} - {anio_fin}/{mes_fin}")
        print(f"[BALANCE] Generando balance: RUT={empresa_rut}, Periodo={anio_inicio}/{mes_inicio} - {anio_fin}/{mes_fin}", file=sys.stderr, flush=True)

        # Importar el servicio de balance
        logger.info("[IMPORT] Importando servicio de balance")
        print("[IMPORT] Importando servicio de balance", file=sys.stderr, flush=True)
        from aplicacion.servicios.servicio_balance_ia import balance_service

        # Formatear períodos a YYYYMM
        logger.info(f"[FORMATO] Formateando periodos: {anio_inicio}/{mes_inicio} - {anio_fin}/{mes_fin}")
        print(f"[FORMATO] Formateando periodos: {anio_inicio}/{mes_inicio} - {anio_fin}/{mes_fin}", file=sys.stderr, flush=True)
        periodo_inicio = balance_service.formatear_periodo(anio_inicio, mes_inicio)
        periodo_fin = balance_service.formatear_periodo(anio_fin, mes_fin)
        logger.info(f"[FORMATO] Periodos formateados: {periodo_inicio} - {periodo_fin}")

        # Obtener nombre de la empresa
        logger.info(f"[EMPRESA] Obteniendo nombre para RUT: {empresa_rut}")
        print(f"[EMPRESA] Obteniendo nombre para RUT: {empresa_rut}", file=sys.stderr, flush=True)
        nombre_empresa = balance_service.obtener_nombre_empresa(empresa_rut)
        logger.info(f"[EMPRESA] Nombre obtenido: {nombre_empresa}")

        # Generar el balance
        logger.info(f"[GENERANDO] Llamando a generar_balance_8_columnas")
        print(f"[GENERANDO] Llamando a generar_balance_8_columnas", file=sys.stderr, flush=True)
        resultado = balance_service.generar_balance_8_columnas(
            empresa_rut=empresa_rut,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin
        )
        logger.info(f"[RESULTADO] Balance generado, success={resultado.get('success')}")
        print(f"[RESULTADO] Balance generado, success={resultado.get('success')}", file=sys.stderr, flush=True)

        if resultado.get('success'):
            # Agregar información adicional
            resultado['metadata']['nombre_empresa'] = nombre_empresa

            return jsonify({
                'estado': 'exitoso',
                'balance': resultado['data'],
                'metadata': resultado['metadata'],
                'empresa': {
                    'rut': empresa_rut,
                    'nombre': nombre_empresa
                },
                'periodo': {
                    'inicio': f"{anio_inicio}/{mes_inicio:02d}",
                    'fin': f"{anio_fin}/{mes_fin:02d}",
                    'formato_bd': f"{periodo_inicio} - {periodo_fin}"
                },
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'estado': 'error',
                'mensaje': resultado.get('error', 'Error generando balance'),
                'detalles': resultado.get('traceback'),
                'timestamp': datetime.now().isoformat()
            }), 500

    except Exception as e:
        import sys
        import logging
        logger = logging.getLogger('aplicacion_root')

        error_completo = traceback.format_exc()
        logger.error(f"[ERROR CRITICO] Error en generar_balance_empresa: {e}")
        logger.error(f"[TRACEBACK] {error_completo}")
        print(f"[ERROR CRITICO] Error en generar_balance_empresa: {e}", file=sys.stderr, flush=True)
        print(f"[TRACEBACK] {error_completo}", file=sys.stderr, flush=True)

        return jsonify({
            'estado': 'error',
            'mensaje': f'Error interno: {str(e)}',
            'detalles': error_completo,
            'timestamp': datetime.now().isoformat()
        }), 500


@ia_bp.route('/analizar-balance', methods=['POST'])
@login_required
@requiere_modulo('ia')
def analizar_balance_con_ia():
    """Analizar balance usando Gemini AI - Accesible para todos los usuarios"""
    try:
        datos = request.get_json()

        if not datos:
            return jsonify({
                'estado': 'error',
                'mensaje': 'No se proporcionaron datos'
            }), 400

        empresa_rut = datos.get('empresa_rut')
        periodo = datos.get('periodo')
        tipo_analisis = datos.get('tipo_analisis', 'completo')

        if not empresa_rut or not periodo:
            return jsonify({
                'estado': 'error',
                'mensaje': 'empresa_rut y periodo son requeridos'
            }), 400

        print(f" Analizando balance: RUT={empresa_rut}, Período={periodo}, Tipo={tipo_analisis}")

        # TODO: Aquí implementaremos la consulta SQL para obtener datos del balance
        # Por ahora simulamos datos para probar la integración
        datos_balance_simulados = {
            'empresa_info': {
                'rut': empresa_rut,
                'nombre': 'Empresa de Prueba'
            },
            'periodo': periodo,
            'cuentas': [
                {
                    'codigo': '1101',
                    'nombre': 'Caja',
                    'debe': 1500000,
                    'haber': 0
                },
                {
                    'codigo': '1102',
                    'nombre': 'Banco',
                    'debe': 5000000,
                    'haber': 200000
                }
            ]
        }

        # Usar Gemini para análisis
        from aplicacion.servicios.servicio_gemini import gemini_service

        resultado_analisis = gemini_service.analyze_balance(
            balance_data=datos_balance_simulados,
            analysis_type=tipo_analisis
        )

        if resultado_analisis.get('success'):
            return jsonify({
                'estado': 'exitoso',
                'analisis': resultado_analisis.get('analysis'),
                'empresa_rut': empresa_rut,
                'periodo': periodo,
                'tipo_analisis': tipo_analisis,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'estado': 'error',
                'mensaje': resultado_analisis.get('error', 'Error en análisis'),
                'timestamp': datetime.now().isoformat()
            }), 500

    except Exception as e:
        error_completo = traceback.format_exc()
        print(f"Error analizando balance: {e}")
        print(f"Traceback completo:\n{error_completo}")

        return jsonify({
            'estado': 'error',
            'mensaje': f'Error al analizar balance: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@ia_bp.route('/estado-gemini', methods=['GET'])
@login_required
@requiere_modulo('ia')
def obtener_estado_gemini():
    """Obtener estado de la configuración de Gemini"""
    try:
        from config import Config

        # Verificar configuración (sin exponer la API key)
        tiene_api_key = bool(Config.GEMINI_API_KEY)
        modelo_configurado = Config.GEMINI_MODEL
        url_api = Config.GEMINI_API_URL

        return jsonify({
            'estado': 'exitoso',
            'configuracion': {
                'api_key_configurada': tiene_api_key,
                'modelo': modelo_configurado,
                'url_api': url_api,
                'usuario_actual': current_user.nombre_usuario,
                'permisos': {
                    'puede_probar': current_user.is_admin(),
                    'puede_analizar': current_user.is_supervisor()
                }
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'estado': 'error',
            'mensaje': f'Error obteniendo estado: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@ia_bp.route('/dashboard')
@login_required
@requiere_modulo('ia')
def dashboard_ia():
    """
    Dashboard de Inteligencia Artificial - ACCESIBLE PARA TODOS LOS USUARIOS
    Todos los usuarios (normales, supervisores y administradores) ven el mismo dashboard completo
    sin restricciones de funcionalidad
    """
    print(f"[IA] Usuario {current_user.nombre_usuario} (Rol: {current_user.rol}) accediendo al Dashboard IA")

    # TODOS los usuarios ven el mismo dashboard completo con todas las funcionalidades
    return render_template('ia_dashboard.html',
                         titulo='Dashboard de Inteligencia Artificial',
                         usuario=current_user)


@ia_bp.route('/api/empresas-lista', methods=['GET'])
@login_required
def obtener_empresas_para_ia():
    """
    Obtener lista de empresas para análisis IA
    TODOS LOS USUARIOS ven todas las empresas disponibles sin restricciones
    """
    try:
        from aplicacion.servicios.servicio_empresas import ServicioEmpresas
        from flask_login import current_user

        anio = request.args.get('anio', type=int)
        mes = request.args.get('mes', type=int)

        print(f"[IA] Obteniendo empresas para IA: anio={anio}, mes={mes}")
        print(f"[USER] Usuario: {current_user.nombre_usuario}, Rol: {current_user.rol}")

        # Obtener base de datos del usuario actual
        base_datos = getattr(current_user, 'base_datos_mysql', 'stratex')

        # Validación: Asegurarse de que base_datos no sea un valor inválido
        if not base_datos or base_datos in ['favicon.ico', 'static', 'None', '']:
            print(f"[WARNING] Base de datos inválida detectada: '{base_datos}', usando 'stratex' por defecto")
            base_datos = 'stratex'

        print(f"[DB] Usando base de datos: {base_datos}")

        # TODOS los usuarios pueden ver TODAS las empresas (sin restricciones)
        servicio = ServicioEmpresas(base_datos)
        empresas = servicio.obtener_todas_empresas_con_credenciales()

        # Formatear datos para el dashboard de IA con los campos disponibles
        empresas_ia = []
        for empresa in empresas:
            empresa_formateada = {
                'rut': empresa.get('run_rut', ''),
                'empresa': empresa.get('empresa', ''),
                'usuario': empresa.get('auditor', 'Sin asignar'),
                'grupo': empresa.get('grupo', 'General'),
            }
            empresas_ia.append(empresa_formateada)

        print(f" {len(empresas_ia)} empresas obtenidas para IA (acceso completo)")
        print(f"[RESPONSE] Enviando respuesta: success=True, total={len(empresas_ia)}")

        return jsonify({
            'success': True,
            'empresas': empresas_ia,
            'total': len(empresas_ia)
            }), 500

    except Exception as e:
        error_completo = traceback.format_exc()
        print(f"Error obteniendo empresas para IA: {e}")
        print(f"Traceback completo:\n{error_completo}")

        return jsonify({
            'success': False,
            'error': f'Error interno: {str(e)}',
            'empresas': []
        }), 500


@ia_bp.route('/generar-balance', methods=['POST'])
@login_required
@requiere_modulo('ia')
def generar_balance_empresas():
    """Generar balance de 8 columnas para una empresa específica"""
    try:
        datos = request.get_json()

        print(f" Datos recibidos: {datos}")

        if not datos:
            return jsonify({
                'estado': 'error',
                'mensaje': 'No se proporcionaron datos JSON'
            }), 400

        empresa_rut = datos.get('empresa_rut')
        anio_inicio = datos.get('anio_inicio')
        mes_inicio = datos.get('mes_inicio')
        anio_fin = datos.get('anio_fin')
        mes_fin = datos.get('mes_fin')

        print(f" Valores extraídos: RUT={empresa_rut}, inicio={anio_inicio}/{mes_inicio}, fin={anio_fin}/{mes_fin}")

        # Validar que todos los campos estén presentes y no sean None
        campos_faltantes = []
        if not empresa_rut:
            campos_faltantes.append('empresa_rut')
        if anio_inicio is None:
            campos_faltantes.append('anio_inicio')
        if mes_inicio is None:
            campos_faltantes.append('mes_inicio')
        if anio_fin is None:
            campos_faltantes.append('anio_fin')
        if mes_fin is None:
            campos_faltantes.append('mes_fin')

        if campos_faltantes:
            return jsonify({
                'estado': 'error',
                'mensaje': f'Campos faltantes o nulos: {", ".join(campos_faltantes)}',
                'datos_recibidos': datos
            }), 400

        # Validar tipos de datos
        try:
            anio_inicio = int(anio_inicio)
            mes_inicio = int(mes_inicio)
            anio_fin = int(anio_fin)
            mes_fin = int(mes_fin)
        except (ValueError, TypeError) as e:
            return jsonify({
                'estado': 'error',
                'mensaje': f'Error de conversión de tipos: {str(e)}',
                'datos_recibidos': datos
            }), 400

        print(f"[BALANCE] Generando balance para {empresa_rut}: {anio_inicio}/{mes_inicio} - {anio_fin}/{mes_fin}")

        # Importar el servicio de balance
        from aplicacion.servicios.servicio_balance_ia import BalanceService

        # Generar balance
        resultado = BalanceService.generar_balance_8_columnas(
            empresa_rut=empresa_rut,
            periodo_inicio=int(f"{anio_inicio}{mes_inicio:02d}"),
            periodo_fin=int(f"{anio_fin}{mes_fin:02d}")
        )

        if resultado.get('success'):
            # Usar estructura consistente con 'data' en lugar de 'balance'
            return jsonify({
                'estado': 'exitoso',
                'balance': resultado.get('data'),  # Los datos del balance están en 'data'
                'metadata': resultado.get('metadata'),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'estado': 'error',
                'mensaje': resultado.get('error', 'Error desconocido al generar balance'),
                'detalles': resultado.get('traceback'),
                'timestamp': datetime.now().isoformat()
            }), 500

    except Exception as e:
        error_completo = traceback.format_exc()
        print(f"Error generando balance: {e}")
        print(f"Traceback completo:\n{error_completo}")

        return jsonify({
            'estado': 'error',
            'mensaje': f'Error interno al generar balance: {str(e)}',
            'detalles': 'Error en el servidor. Verifique la conexión a la base de datos.',
            'timestamp': datetime.now().isoformat()
        }), 500


@ia_bp.route('/analizar-balance-completo', methods=['POST'])
@login_required
@requiere_modulo('ia')
def analizar_balance_completo():
    """Generar y analizar balance con IA en un solo endpoint"""
    try:
        datos = request.get_json()

        if not datos:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400

        empresa_rut = datos.get('empresa_rut')
        anio_inicio = datos.get('anio_inicio')
        mes_inicio = datos.get('mes_inicio')
        anio_fin = datos.get('anio_fin')
        mes_fin = datos.get('mes_fin')

        # Validar que TODOS los parámetros estén presentes
        if not empresa_rut:
            return jsonify({
                'success': False,
                'error': 'empresa_rut es requerido'
            }), 400

        if anio_inicio is None or mes_inicio is None or anio_fin is None or mes_fin is None:
            return jsonify({
                'success': False,
                'error': 'Todos los parámetros de período son requeridos: anio_inicio, mes_inicio, anio_fin, mes_fin',
                'datos_recibidos': datos
            }), 400

        print(f" Análisis completo para RUT {empresa_rut}: {anio_inicio}/{mes_inicio} - {anio_fin}/{mes_fin}")

        # Importar servicios necesarios
        from aplicacion.servicios.servicio_balance_ia import BalanceService

        # Paso 1: Generar balance
        periodo_inicio = int(f"{anio_inicio}{mes_inicio:02d}")
        periodo_fin = int(f"{anio_fin}{mes_fin:02d}")

        resultado_balance = BalanceService.generar_balance_8_columnas(
            empresa_rut=empresa_rut,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin
        )

        print(f" Resultado balance: {resultado_balance.keys() if resultado_balance else 'None'}")

        if not resultado_balance.get('success'):
            return jsonify({
                'success': False,
                'error': f'Error generando balance: {resultado_balance.get("error")}',
                'detalles': resultado_balance.get('detalles'),
                'fase': 'generacion_balance'
            }), 400

        # Paso 2: Obtener datos del balance correctamente
        # El servicio devuelve 'data' no 'balance'
        balance_data = resultado_balance.get('data') or resultado_balance.get('balance')
        metadata = resultado_balance.get('metadata')

        print(f" Balance data type: {type(balance_data)}")
        print(f" Metadata: {metadata}")

        # Validar que tenemos datos válidos
        if balance_data is None:
            return jsonify({
                'success': False,
                'error': 'No se pudieron obtener los datos del balance',
                'detalles': 'El servicio de balance no retornó datos válidos',
                'fase': 'validacion_balance',
                'debug': {
                    'resultado_keys': list(resultado_balance.keys()),
                    'data_presente': 'data' in resultado_balance,
                    'balance_presente': 'balance' in resultado_balance
                }
            }), 400

        # Paso 2.5: Generar análisis del mayor SOLO para IA (separado del balance básico)
        print(" Generando análisis del mayor para IA...")
        analisis_mayor = BalanceService.generar_analisis_mayor_para_ia(
            empresa_rut=empresa_rut,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            balance_data=balance_data
        )

        # Paso 3: Analizar con IA usando el balance + análisis del mayor
        resultado_analisis = BalanceService.analizar_balance_con_ia(
            balance_data,
            metadata,
            anomalias=analisis_mayor.get('anomalias_balance', []),
            investigacion_mayor=analisis_mayor.get('investigacion_mayor', []),
            hallazgos_reglas=analisis_mayor.get('hallazgos_reglas', [])
        )

        if resultado_analisis.get('success'):
            return jsonify({
                'success': True,
                'analisis': resultado_analisis.get('analisis'),
                'empresa_info': resultado_analisis.get('empresa_info'),
                'estadisticas': resultado_analisis.get('estadisticas'),
                'balance_original': balance_data,
                'metadata_balance': metadata,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': resultado_analisis.get('error'),
                'detalles': resultado_analisis.get('detalles'),
                'fase': 'analisis_ia',
                'balance_generado': balance_data  # Incluir balance para debug
            }), 400

    except Exception as e:
        error_completo = traceback.format_exc()
        print(f"Error en análisis completo: {e}")
        print(f"Traceback: {error_completo}")

        return jsonify({
            'success': False,
            'error': f'Error interno: {str(e)}',
            'traceback': error_completo,
            'fase': 'error_interno'
        }), 500


# =====================================================
# RUTAS PARA MEMORIA HISTÓRICA DE ANÁLISIS IA
# =====================================================

@ia_bp.route('/historial-analisis/<empresa_rut>', methods=['GET'])
@login_required
@requiere_modulo('ia')
def obtener_historial_analisis(empresa_rut):
    """
    Obtiene el historial de análisis IA para una empresa
    """
    try:
        from aplicacion.servicios.servicio_ia_memoria import IAMemoriaService

        # Parámetros opcionales
        limite = request.args.get('limite', 5, type=int)
        incluir_completo = request.args.get('incluir_completo', 'false').lower() == 'true'

        historial = IAMemoriaService.obtener_analisis_anteriores(
            empresa_rut=empresa_rut,
            ultimos_n_analisis=limite,
            incluir_contenido_completo=incluir_completo
        )

        return jsonify({
            'success': True,
            'historial': historial,
            'total_analisis': len(historial)
        })

    except Exception as e:
        print(f"Error obteniendo historial: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ia_bp.route('/patrones-aprendidos', methods=['GET'])
@login_required
@requiere_modulo('ia')
def obtener_patrones_aprendidos():
    """
    Obtiene patrones aprendidos por la IA
    """
    try:
        from aplicacion.servicios.servicio_ia_memoria import IAMemoriaService

        empresa_rut = request.args.get('empresa_rut')

        patrones = IAMemoriaService.buscar_patrones_aplicables(
            empresa_rut=empresa_rut or '',
            contexto_actual={}
        )

        return jsonify({
            'success': True,
            'patrones': patrones,
            'total_patrones': len(patrones)
        })

    except Exception as e:
        print(f"Error obteniendo patrones: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ia_bp.route('/estadisticas-memoria', methods=['GET'])
@login_required
@requiere_modulo('ia')
def obtener_estadisticas_memoria():
    """
    Obtiene estadísticas generales de la memoria de análisis
    """
    try:
        import pymysql
        from config import Config

        connection = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4'
        )

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Total de análisis realizados
            cursor.execute("SELECT COUNT(*) as total FROM ia_analisis_historico")
            total_analisis = cursor.fetchone()['total']

            # Análisis por estado
            cursor.execute("""
                SELECT estado_seguimiento, COUNT(*) as cantidad
                FROM ia_analisis_historico
                GROUP BY estado_seguimiento
            """)
            por_estado = cursor.fetchall()

            # Empresas con más análisis
            cursor.execute("""
                SELECT empresa_rut, empresa_nombre, COUNT(*) as total_analisis
                FROM ia_analisis_historico
                GROUP BY empresa_rut, empresa_nombre
                ORDER BY total_analisis DESC
                LIMIT 10
            """)
            empresas_activas = cursor.fetchall()

            # Análisis recientes (últimos 7 días)
            cursor.execute("""
                SELECT COUNT(*) as recientes
                FROM ia_analisis_historico
                WHERE fecha_analisis >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """)
            analisis_recientes = cursor.fetchone()['recientes']

        connection.close()

        return jsonify({
            'success': True,
            'estadisticas': {
                'total_analisis': total_analisis,
                'analisis_recientes_7_dias': analisis_recientes,
                'distribucion_por_estado': por_estado,
                'empresas_mas_activas': empresas_activas
            }
        })

    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ia_bp.route('/exportar-balance-completo', methods=['POST'])
@login_required
@requiere_modulo('ia')
def exportar_balance_completo():
    """Exportar balance con mayores y análisis IA a Excel"""
    try:
        from flask import send_file
        from aplicacion.servicios.servicio_balance_ia import BalanceService

        datos = request.get_json()

        if not datos:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron datos'
            }), 400

        empresa_rut = datos.get('empresa_rut')
        anio_inicio = datos.get('anio_inicio')
        mes_inicio = datos.get('mes_inicio')
        anio_fin = datos.get('anio_fin')
        mes_fin = datos.get('mes_fin')
        incluir_ia = datos.get('incluir_ia', True)

        # Validar parámetros
        if not all([empresa_rut, anio_inicio, mes_inicio, anio_fin, mes_fin]):
            return jsonify({
                'success': False,
                'error': 'Todos los parámetros son requeridos'
            }), 400

        # Formatear períodos
        periodo_inicio = int(f"{anio_inicio}{mes_inicio:02d}")
        periodo_fin = int(f"{anio_fin}{mes_fin:02d}")

        print(f"[EXPORT] Exportando balance completo: {empresa_rut} | {periodo_inicio}-{periodo_fin} | IA={incluir_ia}")

        # Generar Excel
        resultado = BalanceService.generar_excel_balance_mayores(
            empresa_rut=empresa_rut,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            incluir_analisis_ia=incluir_ia
        )

        if resultado['success']:
            # Enviar archivo
            return send_file(
                resultado['excel_buffer'],
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=resultado['filename']
            )
        else:
            return jsonify({
                'success': False,
                'error': resultado.get('error', 'Error generando Excel')
            }), 500

    except Exception as e:
        import traceback
        error_completo = traceback.format_exc()
        print(f"Error exportando balance completo: {e}")
        print(error_completo)

        return jsonify({
            'success': False,
            'error': f'Error al exportar: {str(e)}'
        }), 500
