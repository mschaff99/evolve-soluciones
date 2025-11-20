import pymysql
from configuracion.configuracion import ConfiguracionBase as Config
from datetime import datetime, timedelta
import traceback
import json
from decimal import Decimal
from aplicacion.queries.balance_queries import balance_queries
from aplicacion.prompts.balance_prompts import balance_prompts


class BalanceService:
    """Servicio para generar balances contables"""

    # Cache en memoria para información de empresas (válido por 1 hora)
    _empresa_cache = {}
    _cache_timeout = 3600  # 1 hora en segundos

    @staticmethod
    def _get_empresa_info_cached(empresa_rut, base_datos_usuario=None):
        """
        Obtiene información de empresa con cache en memoria

        Args:
            empresa_rut: RUT de la empresa a buscar
            base_datos_usuario: Base de datos del usuario actual (si no se proporciona, usa Config.DB_NAME)
        """
        cache_key = f"empresa_{empresa_rut}_{base_datos_usuario or Config.DB_NAME}"
        now = datetime.now()

        # Verificar si existe en cache y no ha expirado
        if cache_key in BalanceService._empresa_cache:
            cached_data, cached_time = BalanceService._empresa_cache[cache_key]
            if (now - cached_time).total_seconds() < BalanceService._cache_timeout:
                print(f"[CACHE] Usando info de empresa desde cache: {empresa_rut}")
                return cached_data

        # No está en cache o expiró, obtener de BD
        connection = None
        try:
            # Usar la base de datos del usuario actual o la configurada por defecto
            db_name = base_datos_usuario or Config.DB_NAME
            # Conectar a BD para obtener info de empresa (incluyendo base_datos)
            print(f"[DEBUG] Conectando a {Config.REMOTE_DB_HOST}:{Config.REMOTE_DB_PORT}/{db_name} con usuario {Config.REMOTE_DB_USER}")
            connection = pymysql.connect(
                host=Config.REMOTE_DB_HOST,
                user=Config.REMOTE_DB_USER,
                password=Config.REMOTE_DB_PASSWORD,
                database=db_name,
                port=Config.REMOTE_DB_PORT,
                charset='utf8',
                connect_timeout=5,
                read_timeout=10,
                autocommit=True
            )

            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                consulta_sql = """
                    SELECT empresa, base_datos, correo, grupo, auditor as quien_registra
                    FROM empresas
                    WHERE run_rut = %s LIMIT 1
                """
                print(f"[DEBUG] Ejecutando consulta para RUT: {empresa_rut} en BD: {db_name}")

                # Intentar con el RUT tal cual viene
                cursor.execute(consulta_sql, (empresa_rut,))
                empresa_info = cursor.fetchone()
                print(f"[DEBUG] Resultado de consulta con RUT original: {empresa_info}")

                # Si no encuentra, intentar sin guión
                if not empresa_info and '-' in empresa_rut:
                    rut_sin_guion = empresa_rut.replace('-', '')
                    print(f"[DEBUG] Intentando con RUT sin guión: {rut_sin_guion}")
                    cursor.execute(consulta_sql, (rut_sin_guion,))
                    empresa_info = cursor.fetchone()
                    print(f"[DEBUG] Resultado con RUT sin guión: {empresa_info}")

                # Si aún no encuentra, intentar con guión si no lo tenía
                if not empresa_info and '-' not in empresa_rut and len(empresa_rut) > 1:
                    rut_con_guion = f"{empresa_rut[:-1]}-{empresa_rut[-1]}"
                    print(f"[DEBUG] Intentando con RUT con guión: {rut_con_guion}")
                    cursor.execute(consulta_sql, (rut_con_guion,))
                    empresa_info = cursor.fetchone()
                    print(f"[DEBUG] Resultado con RUT con guión: {empresa_info}")

                if not empresa_info:
                    # Si no encuentra, buscar similares para debug
                    print(f"[DEBUG] No se encontró empresa con ningún formato de RUT. Buscando empresas similares...")
                    cursor.execute("SELECT run_rut, empresa, base_datos FROM empresas WHERE run_rut LIKE %s OR run_rut LIKE %s LIMIT 10",
                                   (f"%{empresa_rut.replace('-', '')}%", f"%{empresa_rut}%"))
                    similares = cursor.fetchall()
                    print(f"[DEBUG] Empresas similares encontradas: {similares}")

                    # Listar todas las empresas si no hay muchas
                    cursor.execute("SELECT COUNT(*) as total FROM empresas")
                    total = cursor.fetchone()
                    print(f"[DEBUG] Total de empresas en BD {db_name}: {total}")

                    if total and total['total'] <= 20:
                        cursor.execute("SELECT run_rut, empresa, base_datos FROM empresas LIMIT 20")
                        todas = cursor.fetchall()
                        print(f"[DEBUG] Todas las empresas en BD:")
                        for emp in todas:
                            print(f"  - RUT: {emp['run_rut']}, Empresa: {emp['empresa']}, BD: {emp.get('base_datos')}")

                if empresa_info:
                    # Guardar en cache SOLO si base_datos tiene valor válido
                    if empresa_info.get('base_datos'):
                        BalanceService._empresa_cache[cache_key] = (empresa_info, now)
                        print(f"Info de empresa cacheada: {empresa_rut} -> BD: {empresa_info['base_datos']}")
                    else:
                        print(f"No se cachea empresa {empresa_rut} porque base_datos es NULL")

                return empresa_info

        except Exception as e:
            print(f"Error obteniendo info empresa: {e}")
            # Invalidar cache en caso de error
            if cache_key in BalanceService._empresa_cache:
                del BalanceService._empresa_cache[cache_key]
                print(f"Cache invalidado para {empresa_rut} debido a error")
            return None
        finally:
            if connection:
                connection.close()

    @staticmethod
    def decimal_to_float(obj):
        """Convierte objetos Decimal a float para serialización JSON, maneja NULL correctamente"""
        if obj is None:
            return 0  # Convertir NULL a 0 en lugar de None
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {key: BalanceService.decimal_to_float(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [BalanceService.decimal_to_float(item) for item in obj]
        else:
            return obj

    @staticmethod
    def detectar_contra_cuenta(nombre_cuenta, tipo_cuenta):
        """
        Detecta si una cuenta es contra-activo o contra-pasivo según su nombre

        Args:
            nombre_cuenta (str): Nombre de la cuenta
            tipo_cuenta (str): Tipo de cuenta (Activo, Pasivo, etc.)

        Returns:
            dict: {'es_contra_cuenta': bool, 'rol_presentacion': str}
        """
        import re

        nombre_lower = nombre_cuenta.lower()

        # Patrones para contra-activo (según el prompt)
        patron_contra_activo = r"(deprec|amort|deterior|desval|provisi[oó]n.*incobrable|obsolescencia)"

        # Patrones para contra-pasivo (según el prompt)
        patron_contra_pasivo = r"(descuento.*(pagar|bono)|costo.*emisi[oó]n.*deuda|prima.*bono.*(deudor))"

        if re.search(patron_contra_activo, nombre_lower):
            return {
                'es_contra_cuenta': True,
                'rol_presentacion': 'contra_activo'
            }
        elif re.search(patron_contra_pasivo, nombre_lower):
            return {
                'es_contra_cuenta': True,
                'rol_presentacion': 'contra_pasivo'
            }
        else:
            # No es contra-cuenta, usar el tipo normal
            tipo_mapping = {
                'Activo': 'activo',
                'Pasivo': 'pasivo',
                'Patrimonio': 'patrimonio',
                'Ingreso': 'ingreso',
                'Gasto': 'gasto'
            }
            return {
                'es_contra_cuenta': False,
                'rol_presentacion': tipo_mapping.get(tipo_cuenta, tipo_cuenta.lower())
            }

    @staticmethod
    def limpiar_datos_balance_para_ia(balance_data):
        """Limpia y valida los datos del balance antes de enviarlos a la IA"""
        try:
            print(f"[LIMPIEZA] Input type: {type(balance_data)}, keys: {list(balance_data.keys()) if isinstance(balance_data, dict) else 'No es dict'}")
            balance_limpio = {
                'cuentas_detalle': [],
                'sumas': None,
                'resultado_ejercicio': None,
                'sumas_iguales': None
            }

            # Procesar cuentas detalle
            for i, cuenta in enumerate(balance_data.get('cuentas_detalle', [])):
                nombre_cuenta = str(cuenta.get('nombre', '')).strip()
                tipo_cuenta = str(cuenta.get('tipo_cuenta', '')).strip()

                # Detectar si es contra-cuenta
                info_contra = BalanceService.detectar_contra_cuenta(nombre_cuenta, tipo_cuenta)

                cuenta_limpia = {
                    'cuenta': str(cuenta.get('cuenta', '')).strip(),
                    'nombre': nombre_cuenta,
                    'tipo_cuenta': tipo_cuenta,

                    # Campos nuevos para contra-cuentas
                    'es_contra_cuenta': info_contra['es_contra_cuenta'],
                    'rol_presentacion': info_contra['rol_presentacion'],

                    # Asegurar que los valores numéricos estén correctos
                    'saldos_iniciales_deudor': float(cuenta.get('saldos_iniciales_deudor') or 0),
                    'saldos_iniciales_acreedor': float(cuenta.get('saldos_iniciales_acreedor') or 0),
                    'debitos': float(cuenta.get('debitos') or 0),
                    'creditos': float(cuenta.get('creditos') or 0),
                    'activos': float(cuenta.get('activos') or 0),
                    'pasivos': float(cuenta.get('pasivos') or 0),
                    'perdida': float(cuenta.get('perdida') or 0),
                    'ganancia': float(cuenta.get('ganancia') or 0)
                }

                # DEBUG: Mostrar la primera cuenta limpia
                if i == 0:
                    print(f" PRIMERA CUENTA DESPUÉS DE LIMPIAR:")
                    print(f"  Cuenta: {cuenta_limpia.get('cuenta')}")
                    print(f"  Valores originales - Débitos: {cuenta.get('debitos')}, Créditos: {cuenta.get('creditos')}")
                    print(f"  Valores limpios - Débitos: {cuenta_limpia.get('debitos')}, Créditos: {cuenta_limpia.get('creditos')}")

                # DEBUG: Mostrar cuentas detectadas como contra-cuentas
                if info_contra['es_contra_cuenta']:
                    print(f"[CONTRA-CUENTA] {nombre_cuenta} -> {info_contra['rol_presentacion']}")

                balance_limpio['cuentas_detalle'].append(cuenta_limpia)

            # Procesar filas de resumen
            for clave in ['sumas', 'resultado_ejercicio', 'sumas_iguales']:
                if balance_data.get(clave):
                    fila = balance_data[clave]
                    balance_limpio[clave] = {
                        'cuenta': str(fila.get('cuenta', '')).strip(),
                        'saldos_iniciales_deudor': float(fila.get('saldos_iniciales_deudor') or 0),
                        'saldos_iniciales_acreedor': float(fila.get('saldos_iniciales_acreedor') or 0),
                        'debitos': float(fila.get('debitos') or 0),
                        'creditos': float(fila.get('creditos') or 0),
                        'activos': float(fila.get('activos') or 0),
                        'pasivos': float(fila.get('pasivos') or 0),
                        'perdida': float(fila.get('perdida') or 0),
                        'ganancia': float(fila.get('ganancia') or 0)
                    }

            print(f"[LIMPIEZA] Output type: {type(balance_limpio)}, cuentas: {len(balance_limpio.get('cuentas_detalle', []))}")
            return balance_limpio

        except Exception as e:
            print(f"Error limpiando datos para IA: {e}")
            print(f"[LIMPIEZA] Devolviendo datos originales por error")
            return balance_data  # Devolver datos originales si hay error

    @staticmethod
    def generar_balance_8_columnas(empresa_rut, periodo_inicio, periodo_fin, base_datos_usuario=None):
        """
        Genera un balance de 8 columnas para una empresa en un período específico

        Args:
            empresa_rut (str): RUT de la empresa
            periodo_inicio (int): Período inicio en formato YYYYMM (ej: 202501)
            periodo_fin (int): Período fin en formato YYYYMM (ej: 202508)
            base_datos_usuario (str): Base de datos del usuario actual (opcional)

        Returns:
            dict: Resultado con success, data y metadatos
        """
        connection = None
        try:
            start_time = datetime.now()
            print(f"[BALANCE] Generando balance para {empresa_rut}: {periodo_inicio} - {periodo_fin}")
            print(f"[BD] Base de datos usuario: {base_datos_usuario or 'No especificada (usará Config.DB_NAME)'}")

            # OPTIMIZACIÓN: Obtener información de empresa con cache
            empresa_info = BalanceService._get_empresa_info_cached(empresa_rut, base_datos_usuario)

            if not empresa_info:
                return {
                    'success': False,
                    'error': f'No se encontró empresa con RUT {empresa_rut}',
                    'traceback': 'Empresa no existe en la base de datos principal'
                }

            info_empresa_time = datetime.now()
            print(f"[TIEMPO] Tiempo para obtener info de empresa: {(info_empresa_time - start_time).total_seconds()}s")
            print(f" DEBUG empresa_info completo: {empresa_info}")

            # Conectar a la base de datos específica de la empresa
            base_datos_empresa = empresa_info.get('base_datos')
            print(f"[DB] Conectando a base de datos específica: {base_datos_empresa}")
            print(f"[DEBUG] Keys disponibles en empresa_info: {list(empresa_info.keys())}")

            if not base_datos_empresa:
                return {
                    'success': False,
                    'error': f'La empresa {empresa_rut} no tiene base de datos específica configurada',
                    'traceback': 'Campo base_datos vacío en tabla empresas'
                }

            connection = pymysql.connect(
                host=Config.REMOTE_DB_HOST,  # Servidor remoto
                user=Config.REMOTE_DB_USER,
                password=Config.REMOTE_DB_PASSWORD,
                database=base_datos_empresa,  # Base de datos específica de la empresa (ej: d77316565)
                port=Config.REMOTE_DB_PORT,
                charset='utf8',
                connect_timeout=30,
                read_timeout=120  # Timeout más largo para consultas complejas
            )

            print(f"[DB] Conectado a base de datos remota: {Config.REMOTE_DB_HOST}/{base_datos_empresa}")

            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # Obtener consulta SQL desde archivo separado
                query = balance_queries.get_balance_8_columnas_query()

                # Construir parámetros usando método optimizado
                params = balance_queries.build_balance_parameters(periodo_inicio, periodo_fin)

                print(f"[BALANCE] Ejecutando consulta de balance con {len(params)} parámetros")
                print(f" DEBUG PARÁMETROS:")
                print(f"  periodo_inicio: {periodo_inicio}")
                print(f"  periodo_fin: {periodo_fin}")
                print(f"  Parámetros completos: {params}")

                query_start_time = datetime.now()
                cursor.execute(query, params)
                resultados = cursor.fetchall()
                query_end_time = datetime.now()
                print(f"[TIEMPO] Tiempo de ejecución de la consulta de balance: {(query_end_time - query_start_time).total_seconds()}s")

                print(f"[OK] Balance generado: {len(resultados)} filas")

                # DEBUG: Mostrar los datos RAW de la primera cuenta con TODOS los campos
                if resultados:
                    primera_fila = resultados[0]
                    print(f" DATOS RAW PRIMERA CUENTA - TODOS LOS CAMPOS:")
                    for key, value in primera_fila.items():
                        print(f"  {key}: {value}")
                    print(f" DATOS RAW PRIMERA CUENTA - RESUMEN:")
                    print(f"  Cuenta: {primera_fila.get('cuenta')}")
                    print(f"  Nombre: {primera_fila.get('nombre')}")
                    print(f"  Saldos iniciales - Deudor: {primera_fila.get('saldos_iniciales_deudor')} | Acreedor: {primera_fila.get('saldos_iniciales_acreedor')}")
                    print(f"  Movimientos - Débitos: {primera_fila.get('debitos')} | Créditos: {primera_fila.get('creditos')}")
                    print(f"  Balance final - Activos: {primera_fila.get('activos')} | Pasivos: {primera_fila.get('pasivos')}")

                    # DEBUG: Buscar la cuenta CAJA específicamente
                    for fila in resultados:
                        if fila.get('cuenta') == '000000111001':
                            print(f" CUENTA CAJA ENCONTRADA - TODOS LOS CAMPOS:")
                            for key, value in fila.items():
                                print(f"  {key}: {value}")
                            break

                # Procesar y estructurar los resultados de la CONSULTA SIMPLIFICADA
                balance_data = {
                    'cuentas_detalle': [],
                    'sumas': None,
                    'resultado_ejercicio': None,
                    'sumas_iguales': None
                }

                processing_start_time = datetime.now()
                for fila in resultados:
                    # Procesar cada fila para asegurar datos correctos
                    fila_procesada = {}
                    for key, value in fila.items():
                        if value is None:
                            fila_procesada[key] = 0
                        elif isinstance(value, Decimal):
                            fila_procesada[key] = float(value)
                        else:
                            fila_procesada[key] = value

                    # DEBUG: Mostrar la primera cuenta procesada
                    if len(balance_data['cuentas_detalle']) == 0:
                        print(f" PRIMERA CUENTA PROCESADA (NUEVA CONSULTA):")
                        print(f"  Cuenta: {fila_procesada.get('cuenta')}")
                        print(f"  Saldos iniciales - Deudor: {fila_procesada.get('saldos_iniciales_deudor')} | Acreedor: {fila_procesada.get('saldos_iniciales_acreedor')}")
                        print(f"  Movimientos - Débitos: {fila_procesada.get('debitos')} | Créditos: {fila_procesada.get('creditos')}")

                    # Con la consulta simplificada, todos los resultados son cuentas detalle
                    balance_data['cuentas_detalle'].append(fila_procesada)

                processing_end_time = datetime.now()
                print(f"[TIEMPO] Tiempo de procesamiento de resultados: {(processing_end_time - processing_start_time).total_seconds()}s")

                # SOLO GENERAR EL BALANCE - Sin análisis automático del mayor
                respuesta = {
                    'success': True,
                    'data': balance_data,
                    'metadata': {
                        'empresa_rut': empresa_rut,
                        'nombre_empresa': empresa_info['empresa'],
                        'base_datos': base_datos_empresa,
                        'servidor_remoto': f"{Config.REMOTE_DB_HOST}:{Config.REMOTE_DB_PORT}",
                        'grupo': empresa_info.get('grupo', ''),
                        'quien_registra': empresa_info.get('quien_registra', ''),
                        'periodo_inicio': periodo_inicio,
                        'periodo_fin': periodo_fin,
                        'total_cuentas': len(balance_data['cuentas_detalle']),
                        'fecha_generacion': datetime.now().isoformat(),
                        'conexion_bd': 'remota_completa'
                    }
                }

                print(" Balance generado SIN análisis automático del mayor - para mejor rendimiento")

                total_end_time = datetime.now()
                print(f"[TIEMPO] Tiempo total de generación de balance: {(total_end_time - start_time).total_seconds()}s")
                return respuesta

        except Exception as e:
            error_completo = traceback.format_exc()
            print(f"Error generando balance: {e}")
            print(f"Traceback completo:\n{error_completo}")

            return {
                'success': False,
                'error': str(e),
                'traceback': error_completo,
                'data': None
            }

        finally:
            if connection:
                connection.close()
                print("🔐 Conexión a BD cerrada")

    @staticmethod
    def formatear_periodo(anio, mes):
        """
        Convierte año y mes a formato YYYYMM

        Args:
            anio (int): Año (ej: 2025)
            mes (int): Mes (1-12)

        Returns:
            int: Período en formato YYYYMM
        """
        return anio * 100 + mes

    @staticmethod
    def obtener_nombre_empresa(empresa_rut, base_datos_usuario=None):
        """
        Obtiene el nombre de la empresa por su RUT desde la base de datos remota
        OPTIMIZADO: Usa el cache de empresa en lugar de hacer consulta separada

        Args:
            empresa_rut (str): RUT de la empresa
            base_datos_usuario (str): Base de datos del usuario actual (opcional)

        Returns:
            str: Nombre de la empresa o RUT si no se encuentra
        """
        try:
            # OPTIMIZACIÓN: Usar el cache en lugar de conexión separada
            empresa_info = BalanceService._get_empresa_info_cached(empresa_rut, base_datos_usuario)

            if empresa_info and empresa_info.get('empresa'):
                return empresa_info['empresa']
            else:
                print(f"[ADVERTENCIA] No se encontró info para empresa: {empresa_rut}")
                return empresa_rut

        except Exception as e:
            print(f"[ADVERTENCIA] Error obteniendo nombre empresa: {e}")
            return empresa_rut

    @staticmethod
    def generar_analisis_mayor_para_ia(empresa_rut, periodo_inicio, periodo_fin, balance_data):
        """
        Genera análisis del mayor SOLO cuando se va a usar con IA.
        Esto se ejecuta por separado para no afectar el rendimiento del balance básico.
        """
        try:
            print(" Generando análisis del mayor para IA...")

            # Obtener info de empresa (puede usar cache)
            empresa_info = BalanceService._get_empresa_info_cached(empresa_rut)
            if not empresa_info:
                return {
                    'anomalias_balance': [],
                    'investigacion_mayor': [],
                    'hallazgos_reglas': []
                }

            base_datos_empresa = empresa_info['base_datos']

            # 1. Detectar anomalías
            anomalias_balance = BalanceService.detectar_anomalias_en_balance(balance_data)

            # 2. Investigar mayor si hay anomalías
            investigacion = BalanceService._analizar_mayor_si_anomalias(
                empresa_base_datos=base_datos_empresa,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                balance_data=balance_data,
                limite_cuentas=3
            )

            # 3. Aplicar reglas contables
            hallazgos_reglas = BalanceService.aplicar_reglas_contables_especificas(investigacion)

            # 4. Investigar cuentas críticas si es necesario
            tiene_anomalias = len(anomalias_balance) > 0
            cuentas_significativas = sum(1 for cuenta in balance_data.get('cuentas_detalle', [])
                                       if (abs(float(cuenta.get('debitos', 0) or 0)) +
                                           abs(float(cuenta.get('creditos', 0) or 0))) > 100000)

            if tiene_anomalias or cuentas_significativas > 10:
                investigacion_criticas = BalanceService._analizar_mayor_cuentas_criticas(
                    empresa_base_datos=base_datos_empresa,
                    periodo_inicio=periodo_inicio,
                    periodo_fin=periodo_fin,
                    balance_data=balance_data,
                    limite_cuentas=3 if not tiene_anomalias else 5
                )
                if investigacion_criticas:
                    investigacion = (investigacion or []) + investigacion_criticas
                    hallazgos_reglas = BalanceService.aplicar_reglas_contables_especificas(investigacion)

            return {
                'anomalias_balance': anomalias_balance,
                'investigacion_mayor': investigacion,
                'hallazgos_reglas': hallazgos_reglas
            }

        except Exception as e:
            print(f"Error generando análisis del mayor: {e}")
            return {
                'anomalias_balance': [],
                'investigacion_mayor': [],
                'hallazgos_reglas': []
            }

    @staticmethod
    def analizar_balance_con_ia(balance_data, metadata, anomalias=None, investigacion_mayor=None, hallazgos_reglas=None):
        """
        Analiza un balance de 8 columnas usando Gemini AI

        Args:
            balance_data (dict): Datos del balance estructurado
            metadata (dict): Metadatos del balance (empresa, período, etc.)
            anomalias (list): Anomalías detectadas opcionales
            investigacion_mayor (list): Investigaciones de mayor opcionales

        Returns:
            dict: Resultado del análisis con la IA
        """
        try:
            print(f"🧠 Iniciando análisis de balance con IA para {metadata.get('nombre_empresa', 'N/A')}")

            # Validar datos de entrada
            if balance_data is None:
                return {
                    'success': False,
                    'error': 'Los datos del balance son nulos',
                    'detalles': 'No se pudieron obtener los datos del balance para el análisis'
                }

            if not isinstance(balance_data, dict):
                return {
                    'success': False,
                    'error': 'Formato de datos de balance inválido',
                    'detalles': f'Se esperaba dict, se recibió {type(balance_data)}'
                }

            # Verificar que hay cuentas para analizar
            cuentas_detalle = balance_data.get('cuentas_detalle', [])
            if not cuentas_detalle:
                return {
                    'success': False,
                    'error': 'No hay cuentas para analizar',
                    'detalles': 'El balance no contiene cuentas detalle'
                }

            print(f"[BALANCE] Balance válido: {len(cuentas_detalle)} cuentas para analizar")

            # LIMPIAR Y VALIDAR DATOS ANTES DE ENVIAR A LA IA
            print(f" DEBUG - balance_data antes de limpiar: {type(balance_data)}, cuentas: {len(balance_data.get('cuentas_detalle', []) if balance_data else [])}")
            balance_data_limpio = BalanceService.limpiar_datos_balance_para_ia(balance_data)
            print(f" DEBUG - balance_data_limpio después de limpiar: {type(balance_data_limpio)}, cuentas: {len(balance_data_limpio.get('cuentas_detalle', []) if balance_data_limpio else [])}")
            print("🧹 Datos del balance limpiados y validados para IA")

            cuentas_limpias = balance_data_limpio.get('cuentas_detalle', [])
            # Analizar TODAS las cuentas, manteniendo el orden del balance
            print(f"🧮 Analizando TODAS las cuentas del balance en orden: {len(cuentas_limpias)} cuentas")

            # Importar el servicio de Gemini
            from aplicacion.servicios.servicio_gemini import gemini_service

            # Preparar el prompt especializado para análisis contable (desde archivo separado)
            prompt_analisis = balance_prompts.get_analisis_contable_prompt()

            # INTEGRAR MEMORIA HISTÓRICA
            try:
                from aplicacion.servicios.servicio_ia_memoria import IAMemoriaService
            except ImportError as import_error:
                print(f"[ADVERTENCIA] Error importando IAMemoriaService: {import_error}")
                IAMemoriaService = None
            contexto_historico = ""
            if IAMemoriaService:
                try:
                    contexto_historico = IAMemoriaService.generar_contexto_historico_para_ia(
                        metadata.get('empresa_rut'),
                        int(str(metadata.get('periodo_fin', 0))[:6])  # Convertir a formato YYYYMM
                    )
                except Exception as memoria_error:
                    print(f"[ADVERTENCIA] Error obteniendo contexto histórico: {memoria_error}")
                    contexto_historico = ""

            if contexto_historico:
                prompt_analisis += f"\n\n---\n\n{contexto_historico}"

            # Mejoras: indicar cuentas típicas a priorizar y verificación cruzada
            prompt_analisis += "\n\n---\n\n" \
                               "🔎 Prioriza revisión de cuentas transitorias y críticas: IVA, Impuestos por Pagar, Remuneraciones por Pagar, Honorarios por Pagar, Leyes Sociales, Provisiones. " \
                               "Verifica que los saldos queden razonablemente en cero al cierre mensual o explica su residuo. Cruza provisiones F29 con sus pagos (PAGO F29)."

            # Instrucciones para análisis de anticipos (si están presentes)
            prompt_analisis += "\n\n---\n\n" \
                               "🔗 **ANÁLISIS DE ANTICIPOS DE PROVEEDORES Y HONORARIOS:**\n\n" \
                               "Si el JSON incluye una sección 'analisis_anticipos_proveedores', úsala como evidencia PRIORITARIA para:\n" \
                               "1. **Validar relaciones entre anticipos y cuentas por pagar** por RUT y monto\n" \
                               "2. **Identificar anticipos no aplicados** o mal aplicados\n" \
                               "3. **Detectar inconsistencias** en la aplicación de anticipos\n" \
                               "4. **Cuadrar saldos** entre cuentas de anticipo (116xxx) y cuentas por pagar (210xxx)\n\n" \
                               "**Para cada cuenta con análisis de anticipos:**\n" \
                               "- Revisa las 'estadisticas' para entender el panorama general\n" \
                               "- Analiza 'saldos_pendientes' para identificar documentos sin relación\n" \
                               "- Usa 'relaciones_encontradas' para validar aplicaciones correctas\n" \
                               "- Integra el 'analisis_ia_resumido' en tu evaluación de la cuenta\n\n" \
                               "**Incluye en tu análisis:**\n" \
                               "- Sección específica 'ANÁLISIS DE ANTICIPOS Y RELACIONES' después del análisis cuenta por cuenta\n" \
                               "- Identifica anticipos rezagados, sobregirados o mal aplicados\n" \
                               "- Propón acciones específicas para regularizar inconsistencias detectadas\n" \
                               "- Evalúa el impacto en la presentación del balance y flujo de caja"
            # Anexo de reglas para uso del Mayor
            prompt_analisis += "\n\n" + balance_prompts.get_anexo_reglas_mayor_prompt()

            # Si hay anomalías, agregar instrucción para priorizarlas
            hay_contexto_extra = bool(anomalias) or bool(investigacion_mayor)
            if hay_contexto_extra:
                prompt_analisis += "\n\n---\n\n" \
                                   "🔸 Nota: Se detectaron anomalías automáticas y se adjuntan muestras del mayor. " \
                                   "Identifica provisiones no pagadas, movimientos fuera de período y contrapartes inusuales. Propón reclasificaciones/ajustes."

            # VALIDACIÓN PREVIA: Asegurar que balance_data_limpio esté disponible para toda la función
            if balance_data_limpio is None:
                print("[CRITICO] balance_data_limpio es None antes de continuar. Reintentando limpieza...")
                balance_data_limpio = BalanceService.limpiar_datos_balance_para_ia(balance_data)
                if balance_data_limpio is None:
                    print("[CRITICO] Limpieza falló dos veces. Usando datos originales.")
                    balance_data_limpio = balance_data or {}

            # Importar el servicio de Gemini
            from aplicacion.servicios.servicio_gemini import gemini_service

            # Preparar los datos del balance para la IA (USANDO DATOS LIMPIOS)
            # Calcular validaciones computadas para ayudar a la IA
            try:
                cuentas_l = balance_data_limpio.get('cuentas_detalle', []) or []
                total_activos_final = sum(c.get('activos', 0) for c in cuentas_l if str(c.get('tipo_cuenta','')).lower() == 'activo')
                # NOTA: En balance de 8 columnas, 'pasivos' incluye Pasivos + Patrimonio (ambos acreedor)
                # Por eso NO sumamos patrimonio por separado
                total_pasivos_patrimonio = sum(c.get('pasivos', 0) for c in cuentas_l if str(c.get('tipo_cuenta','')).lower() in ('pasivo', 'patrimonio'))
                # Resultado calculado desde cuentas (ganancia - pérdida)
                total_ganancia = sum(c.get('ganancia', 0) for c in cuentas_l)
                total_perdida = sum(c.get('perdida', 0) for c in cuentas_l)
                resultado_calculado = float(total_ganancia) - float(total_perdida)
                resultado_row = balance_data_limpio.get('resultado_ejercicio') or {}
                resultado_ejercicio = float(resultado_row.get('pasivos') or resultado_row.get('ganancia') or resultado_row.get('perdida') or 0)
                # Preferir resultado desde fila si viene; si no, usar el calculado
                resultado_para_identidad = resultado_ejercicio if abs(resultado_ejercicio) > 0 else resultado_calculado
                suma_pasivo_patrimonio_resultado = total_pasivos_patrimonio + resultado_para_identidad
                diferencia_identidad = float(total_activos_final) - float(suma_pasivo_patrimonio_resultado)
                sumas_iguales = balance_data_limpio.get('sumas_iguales') or {}
                activos_sumas_iguales = float(sumas_iguales.get('activos') or 0)
                pasivos_sumas_iguales = float(sumas_iguales.get('pasivos') or 0)
                cuadra_activo_pasivo = abs(activos_sumas_iguales - pasivos_sumas_iguales) < 1.0
                # Totales de movimientos y saldos iniciales
                total_debitos = sum(c.get('debitos', 0) for c in cuentas_l)
                total_creditos = sum(c.get('creditos', 0) for c in cuentas_l)
                si_total_deudor = sum(c.get('saldos_iniciales_deudor', 0) for c in cuentas_l)
                si_total_acreedor = sum(c.get('saldos_iniciales_acreedor', 0) for c in cuentas_l)
                delta_mov = float(total_debitos) - float(total_creditos)
                # Dos variantes según convención que use la fuente
                delta_si_deb_menos_cred = float(si_total_deudor) - float(si_total_acreedor)
                delta_si_cred_menos_deb = float(si_total_acreedor) - float(si_total_deudor)
                coincide_mov_con_saldos_iniciales = (
                    abs(delta_mov - delta_si_deb_menos_cred) < 1.0 or
                    abs(delta_mov - delta_si_cred_menos_deb) < 1.0
                )
                validaciones_computadas = {
                    'activo_final_computado': total_activos_final,
                    'pasivo_patrimonio_resultado_computado': suma_pasivo_patrimonio_resultado,
                    'diferencia_identidad': diferencia_identidad,
                    'sumas_iguales_activo': activos_sumas_iguales,
                    'sumas_iguales_pasivo': pasivos_sumas_iguales,
                    'sumas_iguales_cuadra': cuadra_activo_pasivo,
                    'total_debitos': total_debitos,
                    'total_creditos': total_creditos,
                    'delta_movimientos': delta_mov,
                    'si_total_deudor': si_total_deudor,
                    'si_total_acreedor': si_total_acreedor,
                    'delta_si_deb_menos_cred': delta_si_deb_menos_cred,
                    'delta_si_cred_menos_deb': delta_si_cred_menos_deb,
                    'coincide_mov_con_saldos_iniciales': coincide_mov_con_saldos_iniciales,
                    'resultado_calculado': resultado_calculado,
                    'resultado_reportado': resultado_ejercicio,
                    'resultado_usado_identidad': resultado_para_identidad
                }
            except Exception as _:
                validaciones_computadas = {}

            balance_json = {
                "empresa": {
                    "rut": metadata.get('empresa_rut'),
                    "nombre": metadata.get('nombre_empresa'),
                    "grupo": metadata.get('grupo'),
                    "periodo": {
                        "inicio": metadata.get('periodo_inicio'),
                        "fin": metadata.get('periodo_fin')
                    }
                },
                "balance": {
                    "cuentas_detalle": balance_data_limpio.get('cuentas_detalle', []),
                    # Evitar confusiones: no enviar 'sumas' a la IA
                    "sumas": None,
                    "resultado_ejercicio": balance_data_limpio.get('resultado_ejercicio'),
                    "sumas_iguales": balance_data_limpio.get('sumas_iguales')
                },
                "validaciones_computadas": validaciones_computadas,
                "metadatos": {
                    "total_cuentas": len(balance_data_limpio.get('cuentas_detalle', [])),
                    "fecha_generacion": metadata.get('fecha_generacion'),
                    "conexion_bd": metadata.get('conexion_bd')
                }
            }

            # Adjuntar contexto de anomalías e investigación del mayor (con límites para no saturar)
            if anomalias:
                balance_json["anomalias"] = anomalias

            if investigacion_mayor:
                muestras = []
                for inv in investigacion_mayor:
                    movimientos = inv.get('movimientos', [])
                    muestras.append({
                        'cuenta': inv.get('cuenta'),
                        'nombre': inv.get('nombre'),
                        'motivos': inv.get('motivos', []),
                        'rango': inv.get('rango', {}),
                        # limitar a 20 líneas por cuenta para prompt
                        'muestra_movimientos': movimientos[:20]
                    })
                balance_json["investigacion_mayor"] = muestras

            # ========== ANÁLISIS AUTOMÁTICO DE ANTICIPOS DE PROVEEDORES/HONORARIOS ==========
            print(" Detectando cuentas de proveedores/honorarios para análisis de relaciones...")

            # Detectar cuentas relevantes en el balance
            cuentas_proveedores_honorarios = []
            cuentas_anticipos = []

            for cuenta in balance_data_limpio.get('cuentas_detalle', []):
                codigo_cuenta = str(cuenta.get('cuenta', ''))
                nombre_cuenta = str(cuenta.get('nombre', '')).upper()

                # Detectar cuentas de proveedores y honorarios por pagar
                if (codigo_cuenta.startswith('000000210') or
                    'PROVEEDOR' in nombre_cuenta or
                    'HONORARIO' in nombre_cuenta or
                    'SERVICIO' in nombre_cuenta):
                    cuentas_proveedores_honorarios.append({
                        'cuenta': codigo_cuenta,
                        'nombre': cuenta.get('nombre'),
                        'saldo': abs(float(cuenta.get('activos', 0)) + float(cuenta.get('pasivos', 0)))
                    })

                # Detectar cuentas de anticipos
                elif (codigo_cuenta.startswith('000000116') or
                      'ANTICIPO' in nombre_cuenta or
                      'ADELANTO' in nombre_cuenta):
                    cuentas_anticipos.append({
                        'cuenta': codigo_cuenta,
                        'nombre': cuenta.get('nombre'),
                        'saldo': abs(float(cuenta.get('activos', 0)) + float(cuenta.get('pasivos', 0)))
                    })

            print(f" Detectadas {len(cuentas_proveedores_honorarios)} cuentas de proveedores/honorarios")
            print(f" Detectadas {len(cuentas_anticipos)} cuentas de anticipos")

            # NOTA: ANÁLISIS DE ANTICIPOS/PROVEEDORES COMENTADO (DESHABILITADO POR AHORA)
            # Si hay cuentas relevantes con saldos significativos, ejecutar análisis de relaciones
            """
            analisis_anticipos = {}
            if cuentas_proveedores_honorarios or cuentas_anticipos:
                cuentas_significativas = [c for c in (cuentas_proveedores_honorarios + cuentas_anticipos)
                                        if c['saldo'] > 50000]  # Solo cuentas > $50,000

                if cuentas_significativas:
                    print(f" Ejecutando análisis de relaciones para {len(cuentas_significativas)} cuentas significativas...")

                    try:
                        from aplicacion.servicios.servicio_proveedores import proveedores_service

                        # Obtener período hasta (YYYYMM)
                        periodo_hasta = str(metadata.get('periodo_fin', ''))[:6]
                        empresa_rut = metadata.get('empresa_rut', '')

                        # Analizar cada cuenta significativa
                        for cuenta_info in cuentas_significativas[:3]:  # Limitar a 3 cuentas para no saturar
                            codigo_cuenta = cuenta_info['cuenta']
                            print(f"[ANALISIS] Analizando relaciones en cuenta: {codigo_cuenta}")

                            resultado_cuenta = proveedores_service.analizar_proveedores_honorarios(
                                empresa_rut=empresa_rut,
                                periodo_hasta=periodo_hasta,
                                cuenta=codigo_cuenta,
                                incluir_mayor=True
                            )

                            if resultado_cuenta.get('success'):
                                # Extraer análisis IA de forma segura
                                analisis_ia_data = resultado_cuenta.get('analisis_ia', {})
                                if isinstance(analisis_ia_data, dict):
                                    analisis_resumido = str(analisis_ia_data.get('analisis_completo', ''))[:1000]
                                else:
                                    analisis_resumido = str(analisis_ia_data)[:1000] if analisis_ia_data else 'Sin análisis IA disponible'

                                analisis_anticipos[codigo_cuenta] = {
                                    'nombre_cuenta': cuenta_info['nombre'],
                                    'estadisticas': resultado_cuenta.get('estadisticas', {}),
                                    'saldos_pendientes': resultado_cuenta.get('saldos_pendientes', [])[:10],  # Limitar datos
                                    'relaciones_encontradas': resultado_cuenta.get('relaciones_encontradas', [])[:10],
                                    'analisis_ia_resumido': analisis_resumido
                                }
                                print(f" Análisis completado para cuenta {codigo_cuenta}")
                            else:
                                print(f"[ADVERTENCIA] Error en análisis de cuenta {codigo_cuenta}: {resultado_cuenta.get('error')}")

                    except Exception as e:
                        print(f"[ADVERTENCIA] Error en análisis de anticipos: {e}")
                        analisis_anticipos = {'error': f'Error en análisis: {str(e)}'}

            # Agregar análisis de anticipos al JSON principal
            if analisis_anticipos:
                balance_json["analisis_anticipos_proveedores"] = analisis_anticipos
                print(f"📋 Análisis de anticipos agregado al balance: {len(analisis_anticipos)} cuentas analizadas")
            """

            # NOTA: ANÁLISIS DE ANTICIPOS/PROVEEDORES DESHABILITADO
            analisis_anticipos = {}
            print(f"[SKIP] Análisis de anticipos/proveedores deshabilitado por ahora")

            # Convertir todos los Decimals a float para serialización JSON
            balance_json_clean = BalanceService.decimal_to_float(balance_json)

            # Convertir a JSON legible
            balance_json_str = json.dumps(balance_json_clean, indent=2, ensure_ascii=False)

            # DEBUG: Mostrar una muestra de los datos que se envían a la IA
            print(" MUESTRA DE DATOS ENVIADOS A LA IA:")
            if balance_json_clean.get('balance', {}).get('cuentas_detalle'):
                primera_cuenta = balance_json_clean['balance']['cuentas_detalle'][0]
                print(f"Primera cuenta: {primera_cuenta.get('cuenta', 'N/A')} - {primera_cuenta.get('nombre', 'N/A')}")
                print(f"  - Saldos Iniciales: Deudor={primera_cuenta.get('saldos_iniciales_deudor', 0)}, Acreedor={primera_cuenta.get('saldos_iniciales_acreedor', 0)}")
                print(f"  - Movimientos: Débitos={primera_cuenta.get('debitos', 0)}, Créditos={primera_cuenta.get('creditos', 0)}")
                print(f"  - Saldos Finales: Activos={primera_cuenta.get('activos', 0)}, Pasivos={primera_cuenta.get('pasivos', 0)}")

            # Combinar prompt con datos
            prompt_completo = f"{prompt_analisis}\n\n```json\n{balance_json_str}\n```"

            print(f"📄 Enviando balance a IA: {len(balance_data.get('cuentas_detalle', []))} cuentas")
            print(f" PERÍODO ENVIADO A IA - Inicio: {metadata.get('periodo_inicio')}, Fin: {metadata.get('periodo_fin')}")
            print(f" EMPRESA ENVIADA A IA: {metadata.get('nombre_empresa')}")

            # Usar el servicio de Gemini para análisis
            resultado_ia = gemini_service._generate_content(prompt_completo)

            if resultado_ia.get('success'):
                print(" Análisis de IA completado exitosamente")

                # GUARDAR ANÁLISIS EN MEMORIA HISTÓRICA
                analisis_content = resultado_ia.get('content')
                tiempo_procesamiento = getattr(resultado_ia, 'tiempo_procesamiento', 0)

                # GUARDAR EN MEMORIA HISTÓRICA (VERSIÓN SIMPLIFICADA Y ROBUSTA)
                memoria_resultado = {'success': False, 'error': 'Servicio no disponible'}
                if IAMemoriaService:
                    try:
                        # Usar balance_data original si balance_data_limpio no está disponible
                        balance_para_metadata = balance_data

                        # Extraer metadatos de forma segura
                        total_cuentas = 0
                        if isinstance(balance_para_metadata, dict) and 'cuentas_detalle' in balance_para_metadata:
                            total_cuentas = len(balance_para_metadata['cuentas_detalle'])

                        balance_metadata_simple = {
                            'total_cuentas_analizadas': total_cuentas,
                            'sumas_activos': 0,  # Valores por defecto para evitar errores
                            'sumas_pasivos': 0,
                            'resultado_ejercicio': 0
                        }

                        memoria_resultado = IAMemoriaService.guardar_analisis_ia(
                            empresa_rut=metadata.get('empresa_rut', ''),
                            empresa_nombre=metadata.get('nombre_empresa', 'Sin nombre'),
                            periodo_inicio=int(str(metadata.get('periodo_inicio', 202501))[:6]),
                            periodo_fin=int(str(metadata.get('periodo_fin', 202501))[:6]),
                            analisis_completo=analisis_content,
                            balance_metadata=balance_metadata_simple,
                            tiempo_procesamiento=tiempo_procesamiento
                        )
                    except Exception as memoria_error:
                        print(f"[ADVERTENCIA] Error guardando en memoria (no crítico): {memoria_error}")
                        import traceback
                        print(f"[ADVERTENCIA] Traceback memoria: {traceback.format_exc()}")
                        memoria_resultado = {'success': False, 'error': str(memoria_error)}
                else:
                    print("[ADVERTENCIA] IAMemoriaService no disponible, saltando guardado en memoria")

                if memoria_resultado.get('success'):
                    print(f"[GUARDADO] Análisis guardado en memoria - ID: {memoria_resultado.get('analisis_id')}")

                return {
                    'success': True,
                    'analisis': analisis_content,
                    'empresa_info': {
                        'rut': metadata.get('empresa_rut'),
                        'nombre': metadata.get('nombre_empresa'),
                        'periodo': f"{metadata.get('periodo_inicio')} - {metadata.get('periodo_fin')}"
                    },
                    'estadisticas': {
                        'total_cuentas_analizadas': len(balance_data_limpio.get('cuentas_detalle', [])),
                        'fecha_analisis': datetime.now().isoformat(),
                        'analisis_id': memoria_resultado.get('analisis_id') if memoria_resultado.get('success') else None
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"Error en IA: {resultado_ia.get('error', 'Error desconocido')}",
                    'detalles': 'El servicio de IA no pudo procesar el balance'
                }

        except Exception as e:
            error_completo = traceback.format_exc()
            print(f"Error analizando balance con IA: {e}")
            print(f"Traceback: {error_completo}")

            return {
                'success': False,
                'error': f'Error interno en análisis IA: {str(e)}',
                'traceback': error_completo
            }

    @staticmethod
    def detectar_anomalias_en_balance(balance_data):
        """
        Detecta anomalías simples en el balance a nivel de cuenta.
        Heurísticas iniciales (conservadoras):
        - Cuenta con simultáneo saldo en columnas opuestas (activos y pasivos) o (pérdida y ganancia).
        - Cuentas con nombres típicamente transitorios (IVA, REMUN, HONOR, RETENC, LEYES, PROVIS) con residuo != 0.
        """
        try:
            cuentas = balance_data.get('cuentas_detalle', []) or []
            anomalias_encontradas = []

            palabras_transitorias = ['IVA', 'REMUN', 'HONOR', 'RETENC', 'LEYES', 'PROVIS', 'SUELD', 'ARREND', 'IMPUEST', 'TRIBUT', 'F29']

            for cuenta in cuentas:
                cuenta_id = str(cuenta.get('cuenta', '') or '')
                nombre = str(cuenta.get('nombre', '') or '')
                tipo_cuenta = str(cuenta.get('tipo_cuenta', '') or '')

                activos = float(cuenta.get('activos', 0) or 0)
                pasivos = float(cuenta.get('pasivos', 0) or 0)
                perdida = float(cuenta.get('perdida', 0) or 0)
                ganancia = float(cuenta.get('ganancia', 0) or 0)
                debitos = float(cuenta.get('debitos', 0) or 0)
                creditos = float(cuenta.get('creditos', 0) or 0)

                motivos = []

                # 1) Simultáneo en columnas opuestas
                if activos > 0 and pasivos > 0:
                    motivos.append('Saldo simultáneo en Activos y Pasivos')
                if perdida > 0 and ganancia > 0:
                    motivos.append('Saldo simultáneo en Pérdida y Ganancia')

                # 2) Heurística de cuentas transitorias con residuo
                nombre_upper = nombre.upper()
                if any(p in nombre_upper for p in palabras_transitorias):
                    residuo = activos + pasivos + ganancia + perdida
                    if abs(residuo) > 0.001:
                        motivos.append('Cuenta transitoria con saldo residual')

                # 3) Movimientos importantes
                if (debitos + creditos) > 0 and (activos == 0 and pasivos == 0 and perdida == 0 and ganancia == 0):
                    motivos.append('Movimientos sin saldo final aparente (revisar)')

                if motivos:
                    anomalias_encontradas.append({
                        'cuenta': cuenta_id,
                        'nombre': nombre,
                        'tipo_cuenta': tipo_cuenta,
                        'motivos': motivos
                    })

            return anomalias_encontradas
        except Exception as e:
            print(f"[ADVERTENCIA] Error detectando anomalías: {e}")
            return []

    @staticmethod
    def _analizar_mayor_si_anomalias(empresa_base_datos, periodo_inicio, periodo_fin, balance_data, limite_cuentas=3):
        """
        Si se encuentran anomalías, consulta el mayor para un máximo de `limite_cuentas`.
        Retorna lista con {cuenta, nombre, rango, movimientos}.
        """
        try:
            # Conexión directa a la BD específica de la empresa
            connection = pymysql.connect(
                host=Config.REMOTE_DB_HOST,
                user=Config.REMOTE_DB_USER,
                password=Config.REMOTE_DB_PASSWORD,
                database=empresa_base_datos,
                port=Config.REMOTE_DB_PORT,
                charset='utf8',
                connect_timeout=20,
                read_timeout=60
            )

            anomalias = BalanceService.detectar_anomalias_en_balance(balance_data)
            if not anomalias:
                return []

            investigaciones = []
            cuentas_a_revisar = anomalias[:limite_cuentas]

            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                for item in cuentas_a_revisar:
                    cuenta_id = item.get('cuenta')
                    nombre = item.get('nombre')

                    # Autodetectar rango si hace falta
                    inicio, fin = BalanceService._obtener_rango_mayor(cursor, cuenta_id, periodo_inicio, periodo_fin)
                    if inicio is None or fin is None:
                        # No hay movimientos, saltar
                        continue

                    saldo_inicial = BalanceService._obtener_saldo_inicial(cursor, cuenta_id, inicio)
                    movimientos = BalanceService._obtener_movimientos_mayor(cursor, cuenta_id, inicio, fin)

                    # Calcular saldo corrido en Python para evitar variables SQL
                    saldo = float(saldo_inicial or 0)
                    filas = []
                    for idx, mov in enumerate(movimientos):
                        debe = float(mov.get('debe', 0) or 0)
                        haber = float(mov.get('haber', 0) or 0)
                        saldo += (debe - haber)
                        filas.append({
                            'Tipo': mov.get('Tipo'),
                            'Numero': mov.get('Numero'),
                            'Fecha': mov.get('Fecha'),
                            'periodo': mov.get('periodo'),
                            'Glosa': mov.get('Glosa'),
                            'debe': debe,
                            'haber': haber,
                            'saldo_acumulado': saldo,
                            'marca_inicio': 'SI' if idx == 0 else '',
                            'saldo_inicial': float(saldo_inicial or 0)
                        })

                    investigaciones.append({
                        'cuenta': cuenta_id,
                        'nombre': nombre,
                        'rango': {
                            'inicio': inicio,
                            'fin': fin
                        },
                        'motivos': item.get('motivos', []),
                        'movimientos': filas
                    })

            connection.close()
            return investigaciones
        except Exception as e:
            print(f"[ADVERTENCIA] Error analizando mayor por anomalías: {e}")
            try:
                connection.close()
            except:
                pass
            return []

    @staticmethod
    def aplicar_reglas_contables_especificas(investigacion_mayor):
        """
        Aplica reglas específicas sobre el mayor para generar hallazgos detallados.
        Ejemplo: Provisiones F29 no pagadas (Impuestos por Pagar).
        """
        hallazgos = []
        try:
            if not investigacion_mayor:
                return hallazgos

            for inv in investigacion_mayor:
                cuenta = inv.get('cuenta', '')
                nombre = (inv.get('nombre') or '').upper()
                movs = inv.get('movimientos', [])

                # Regla: detectar provisión F29 y pagos asociados
                # Heurística: Glosa contiene 'PROVISION F29' y 'PAGO F29'
                provisiones = [m for m in movs if isinstance(m.get('Glosa'), str) and 'PROVISION F29' in m.get('Glosa').upper()]
                pagos = [m for m in movs if isinstance(m.get('Glosa'), str) and 'PAGO F29' in m.get('Glosa').upper()]

                if provisiones:
                    total_provision = sum(float(m.get('haber', 0) or 0) for m in provisiones)  # Haber en pasivo
                    total_pago = sum(float(m.get('debe', 0) or 0) for m in pagos)              # Debe cancela pasivo
                    diferencia = round(total_provision - total_pago, 2)

                    if diferencia > 0.01:
                        hallazgos.append({
                            'cuenta': cuenta,
                            'nombre': inv.get('nombre'),
                            'tipo': 'PROVISION_F29_NO_PAGADA',
                            'detalle': {
                                'total_provisionado': total_provision,
                                'total_pagado': total_pago,
                                'saldo_pendiente': diferencia,
                                'observacion': 'Existen provisiones F29 no pagadas que explican el saldo acreedor.'
                            }
                        })
        except Exception as e:
            print(f"[ADVERTENCIA] Error aplicando reglas contables: {e}")
        return hallazgos

    @staticmethod
    def _obtener_rango_mayor(cursor, cuenta_id, periodo_inicio, periodo_fin):
        """Obtiene (inicio, fin) para la cuenta. Si vienen provistos, usa esos; si no, autodetecta."""
        try:
            if periodo_inicio and periodo_fin:
                return int(periodo_inicio), int(periodo_fin)

            cursor.execute(
                """
                SELECT MIN(periodo) AS min_p, MAX(periodo) AS max_p
                FROM co_tdvouchers
                WHERE ind_estado='V' AND Cuenta=%s
                """,
                (cuenta_id,)
            )
            row = cursor.fetchone()
            if not row or row.get('min_p') is None or row.get('max_p') is None:
                return None, None
            return int(row['min_p']), int(row['max_p'])
        except Exception as e:
            print(f"[ADVERTENCIA] Error obteniendo rango del mayor: {e}")
            return None, None

    @staticmethod
    def _obtener_saldo_inicial(cursor, cuenta_id, periodo_inicio):
        """Saldo inicial antes del período de inicio."""
        try:
            cursor.execute(
                """
                SELECT COALESCE(SUM(COALESCE(debe,0) - COALESCE(haber,0)), 0) AS saldo_ini
                FROM co_tdvouchers
                WHERE ind_estado='V' AND Cuenta=%s AND periodo < %s
                """,
                (cuenta_id, int(periodo_inicio))
            )
            row = cursor.fetchone()
            return float(row.get('saldo_ini', 0) if row else 0)
        except Exception as e:
            print(f"[ADVERTENCIA] Error obteniendo saldo inicial: {e}")
            return 0.0

    @staticmethod
    def _obtener_movimientos_mayor(cursor, cuenta_id, inicio, fin):
        """Obtiene movimientos del mayor entre inicio y fin, con glosa del comprobante."""
        try:
            cursor.execute(
                """
                SELECT
                  a.Tipo,
                  a.Numero,
                  a.Fecha,
                  a.periodo,
                  b.Glosa,
                  COALESCE(a.debe,  0) AS debe,
                  COALESCE(a.haber, 0) AS haber
                FROM co_tdvouchers a
                LEFT JOIN co_tcvouchers b
                  ON a.Tipo=b.Tipo AND a.Numero=b.Numero
                WHERE a.ind_estado='V'
                  AND a.Cuenta = %s
                  AND a.periodo BETWEEN %s AND %s
                ORDER BY a.periodo, a.Fecha, a.Tipo, a.Numero
                """,
                (cuenta_id, int(inicio), int(fin))
            )
            return list(cursor.fetchall() or [])
        except Exception as e:
            print(f"[ADVERTENCIA] Error obteniendo movimientos del mayor: {e}")
            return []

    @staticmethod
    def _analizar_mayor_cuentas_criticas(empresa_base_datos, periodo_inicio, periodo_fin, balance_data, limite_cuentas=5):
        """
        Siempre investiga mayores para cuentas críticas (por nombre/keyword),
        aunque no existan anomalías previas.
        """
        try:
            connection = pymysql.connect(
                host=Config.REMOTE_DB_HOST,
                user=Config.REMOTE_DB_USER,
                password=Config.REMOTE_DB_PASSWORD,
                database=empresa_base_datos,
                port=Config.REMOTE_DB_PORT,
                charset='utf8',
                connect_timeout=20,
                read_timeout=60
            )

            cuentas = balance_data.get('cuentas_detalle', []) or []
            keywords = ['IVA', 'IMPUEST', 'TRIBUT', 'REMUN', 'HONOR', 'LEYES', 'PROVIS']

            def importancia(c):
                return abs(float(c.get('debitos', 0) or 0)) + abs(float(c.get('creditos', 0) or 0))

            candidatas = [c for c in cuentas if any(k in str(c.get('nombre','')).upper() for k in keywords)]
            candidatas.sort(key=importancia, reverse=True)
            candidatas = candidatas[:limite_cuentas]

            investigaciones = []
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                for cta in candidatas:
                    cuenta_id = str(cta.get('cuenta',''))
                    nombre = str(cta.get('nombre',''))
                    inicio, fin = BalanceService._obtener_rango_mayor(cursor, cuenta_id, periodo_inicio, periodo_fin)
                    if inicio is None or fin is None:
                        continue
                    saldo_inicial = BalanceService._obtener_saldo_inicial(cursor, cuenta_id, inicio)
                    movimientos = BalanceService._obtener_movimientos_mayor(cursor, cuenta_id, inicio, fin)
                    saldo = float(saldo_inicial or 0)
                    filas = []
                    for idx, mov in enumerate(movimientos):
                        debe = float(mov.get('debe', 0) or 0)
                        haber = float(mov.get('haber', 0) or 0)
                        saldo += (debe - haber)
                        filas.append({
                            'Tipo': mov.get('Tipo'),
                            'Numero': mov.get('Numero'),
                            'Fecha': mov.get('Fecha'),
                            'periodo': mov.get('periodo'),
                            'Glosa': mov.get('Glosa'),
                            'debe': debe,
                            'haber': haber,
                            'saldo_acumulado': saldo,
                            'marca_inicio': 'SI' if idx == 0 else '',
                            'saldo_inicial': float(saldo_inicial or 0)
                        })
                    investigaciones.append({
                        'cuenta': cuenta_id,
                        'nombre': nombre,
                        'rango': {'inicio': inicio, 'fin': fin},
                        'motivos': ['Cuenta crítica por naturaleza'],
                        'movimientos': filas
                    })

            connection.close()
            return investigaciones
        except Exception as e:
            print(f"[ADVERTENCIA] Error analizando mayor (críticas): {e}")
            try:
                connection.close()
            except:
                pass
            return []

    @staticmethod
    def preparar_balance_para_ia(balance_data, metadata):
        """
        Prepara los datos del balance en un formato optimizado para la IA

        Args:
            balance_data (dict): Datos del balance
            metadata (dict): Metadatos del balance

        Returns:
            dict: Balance formateado para análisis IA
        """
        try:
            # Formatear cuentas detalle con información más legible
            cuentas_formateadas = []
            for cuenta in balance_data.get('cuentas_detalle', []):
                cuenta_formateada = {
                    "codigo": cuenta.get('cuenta', ''),
                    "nombre": cuenta.get('nombre', 'Sin nombre'),
                    "tipo_cuenta": cuenta.get('tipo_cuenta', ''),
                    "saldos_iniciales": {
                        "deudor": float(cuenta.get('saldos_iniciales_deudor', 0) or 0),
                        "acreedor": float(cuenta.get('saldos_iniciales_acreedor', 0) or 0)
                    },
                    "movimientos": {
                        "debitos": float(cuenta.get('debitos', 0) or 0),
                        "creditos": float(cuenta.get('creditos', 0) or 0)
                    },
                    "saldos_finales": {
                        "activos": float(cuenta.get('activos', 0) or 0),
                        "pasivos": float(cuenta.get('pasivos', 0) or 0),
                        "perdida": float(cuenta.get('perdida', 0) or 0),
                        "ganancia": float(cuenta.get('ganancia', 0) or 0)
                    }
                }
                cuentas_formateadas.append(cuenta_formateada)

            # Formatear resumen
            balance_formateado = {
                "empresa": {
                    "rut": metadata.get('empresa_rut'),
                    "nombre": metadata.get('nombre_empresa'),
                    "grupo": metadata.get('grupo', ''),
                    "periodo": {
                        "inicio": metadata.get('periodo_inicio'),
                        "fin": metadata.get('periodo_fin'),
                        "inicio_legible": f"{str(metadata.get('periodo_inicio', ''))[:4]}/{str(metadata.get('periodo_inicio', ''))[-2:]}",
                        "fin_legible": f"{str(metadata.get('periodo_fin', ''))[:4]}/{str(metadata.get('periodo_fin', ''))[-2:]}"
                    }
                },
                "cuentas": cuentas_formateadas,
                "resumen": {
                    "total_cuentas": len(cuentas_formateadas),
                    "fecha_generacion": metadata.get('fecha_generacion'),
                    "servidor": metadata.get('servidor_remoto', 'No especificado')
                }
            }

            return balance_formateado

        except Exception as e:
            print(f"Error preparando balance para IA: {e}")
            return None


    @staticmethod
    def _extraer_analisis_por_cuenta(analisis_texto):
        """
        Extrae el análisis de cada cuenta del texto completo de IA

        Args:
            analisis_texto (str): Texto completo del análisis de IA

        Returns:
            dict: Diccionario con código_cuenta como clave y texto de análisis como valor
        """
        try:
            import re
            analisis_dict = {}

            print(" DEBUG - Primeros 500 caracteres del análisis:")
            print(analisis_texto[:500] if len(analisis_texto) > 500 else analisis_texto)

            # Buscar secciones de análisis de cada cuenta con varios patrones posibles
            # Patrón 1: ### Cuenta: [NOMBRE]
            # Patrón 2: ### [NOMBRE DE CUENTA]
            # Patrón 3: **Cuenta:** o - **Cuenta:**

            patron_cuenta = r'###\s+(?:Cuenta:\s+)?([^\n]+)'

            partes = re.split(patron_cuenta, analisis_texto)

            print(f" DEBUG - Partes encontradas: {len(partes)}")

            # Las partes impares son nombres de cuenta, las pares son su análisis
            for i in range(1, len(partes), 2):
                if i+1 < len(partes):
                    nombre_cuenta = partes[i].strip()
                    contenido_analisis = partes[i+1].strip()

                    print(f" DEBUG - Procesando: {nombre_cuenta[:100]}")

                    # Extraer código de cuenta (buscar secuencia de 12 dígitos)
                    match_codigo = re.search(r'(\d{12})', nombre_cuenta)
                    if not match_codigo:
                        # Buscar cualquier secuencia de dígitos al inicio
                        match_codigo = re.search(r'^(\d+)', nombre_cuenta.strip())

                    if match_codigo:
                        codigo = match_codigo.group(1)
                        # Limpiar el código de ceros a la izquierda excepto los necesarios
                        codigo_limpio = codigo.lstrip('0') or '0'

                        # Guardar con ambas versiones del código
                        analisis_dict[codigo] = f"### Cuenta: {nombre_cuenta}\n\n{contenido_analisis}"
                        analisis_dict[codigo_limpio] = f"### Cuenta: {nombre_cuenta}\n\n{contenido_analisis}"

                        print(f" Cuenta extraída: {codigo} / {codigo_limpio}")

            print(f" Extraídos análisis de {len(analisis_dict)} cuentas")
            if len(analisis_dict) == 0:
                print("[ADVERTENCIA] No se encontraron análisis de cuentas. Guardando análisis completo como respaldo.")

                # DEBUG: Guardar el análisis completo en un archivo temporal
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
                        f.write(analisis_texto)
                        print(f"[GUARDADO] Análisis completo guardado en: {f.name}")
                except:
                    pass

                # Si no se pudo extraer, usar el análisis completo para todas las cuentas
                return {'__completo__': analisis_texto}

            return analisis_dict

        except Exception as e:
            import traceback
            print(f"[ADVERTENCIA] Error extrayendo análisis por cuenta: {e}")
            print(traceback.format_exc())
            return {}

    @staticmethod
    def obtener_mayor_cuenta(empresa_base_datos, cuenta, periodo_inicio, periodo_fin):
        """
        Obtiene el mayor de una cuenta específica para el período dado

        Args:
            empresa_base_datos (str): Base de datos de la empresa
            cuenta (str): Código de la cuenta
            periodo_inicio (int): Período inicial YYYYMM
            periodo_fin (int): Período final YYYYMM

        Returns:
            list: Movimientos del mayor de la cuenta
        """
        connection = None
        try:
            connection = pymysql.connect(
                host=Config.REMOTE_DB_HOST,
                user=Config.REMOTE_DB_USER,
                password=Config.REMOTE_DB_PASSWORD,
                database=empresa_base_datos,
                port=Config.REMOTE_DB_PORT,
                charset='utf8',
                connect_timeout=Config.REMOTE_DB_CONNECT_TIMEOUT,
                read_timeout=Config.REMOTE_DB_READ_TIMEOUT
            )

            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # Setear parámetros
                cursor.execute("SET @p_cuenta = %s", (cuenta,))
                cursor.execute("SET @p_inicio = %s", (periodo_inicio,))
                cursor.execute("SET @p_fin = %s", (periodo_fin,))

                # Obtener saldo inicial
                cursor.execute("""
                    SELECT COALESCE(SUM(COALESCE(debe,0) - COALESCE(haber,0)), 0) AS saldo_inicial
                    FROM co_tdvouchers
                    WHERE ind_estado='V'
                      AND Cuenta = @p_cuenta
                      AND periodo < @p_inicio
                """)
                saldo_inicial = cursor.fetchone()['saldo_inicial']

                # Setear saldo inicial y acumuladores
                cursor.execute("SET @saldo_ini = %s", (saldo_inicial,))
                cursor.execute("SET @saldo = @saldo_ini")
                cursor.execute("SET @row = 0")

                # Query del mayor
                mayor_query = """
                SELECT
                  t.Tipo,
                  t.Numero,
                  t.Fecha,
                  t.periodo,
                  t.Glosa,
                  t.debe,
                  t.haber,
                  t.RutTesoreria,
                  (@saldo := @saldo + (t.debe - t.haber)) AS saldo_acumulado,
                  CASE WHEN (@row := @row + 1) = 1 THEN 'SI' ELSE '' END AS marca_inicio,
                  @saldo_ini AS saldo_inicial
                FROM (
                  SELECT
                    a.Tipo,
                    a.Numero,
                    a.Fecha,
                    a.periodo,
                    b.Glosa,
                    a.RutTesoreria,
                    COALESCE(a.debe,  0) AS debe,
                    COALESCE(a.haber, 0) AS haber,
                    STR_TO_DATE(CAST(a.Fecha AS CHAR), '%Y%m%d') AS fecha_ord
                  FROM co_tdvouchers a
                  LEFT JOIN co_tcvouchers b
                    ON a.Tipo=b.Tipo AND a.Numero=b.Numero
                  WHERE a.ind_estado='V'
                    AND a.Cuenta = @p_cuenta
                    AND a.periodo BETWEEN @p_inicio AND @p_fin
                ) AS t
                ORDER BY t.fecha_ord, t.Tipo, t.Numero
                """

                cursor.execute(mayor_query)
                movimientos = cursor.fetchall()

                # Convertir Decimals a float
                movimientos_clean = []
                for mov in movimientos:
                    mov_clean = {}
                    for k, v in mov.items():
                        if isinstance(v, Decimal):
                            mov_clean[k] = float(v)
                        else:
                            mov_clean[k] = v
                    movimientos_clean.append(mov_clean)

                return movimientos_clean

        except Exception as e:
            print(f"Error obteniendo mayor de cuenta {cuenta}: {e}")
            return []
        finally:
            if connection:
                connection.close()

    @staticmethod
    def generar_excel_balance_mayores(empresa_rut, periodo_inicio, periodo_fin, incluir_analisis_ia=True):
        """
        Genera un archivo Excel con:
        - Hoja 1: Balance de 8 columnas
        - Hojas siguientes: Mayor de cada cuenta (título = código de cuenta)
        - Si incluir_analisis_ia=True, también incluye el análisis de IA

        Args:
            empresa_rut (str): RUT de la empresa
            periodo_inicio (int): Período inicial YYYYMM
            periodo_fin (int): Período final YYYYMM
            incluir_analisis_ia (bool): Si incluir análisis de IA

        Returns:
            dict: Resultado con el archivo Excel o error
        """
        try:
            import pandas as pd
            import io
            from openpyxl import Workbook
            from openpyxl.utils.dataframe import dataframe_to_rows
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

            print(f"[EXCEL] Generando Excel completo para {empresa_rut}")

            # 1. Generar el balance
            resultado_balance = BalanceService.generar_balance_8_columnas(
                empresa_rut=empresa_rut,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin
            )

            if not resultado_balance.get('success'):
                return {
                    'success': False,
                    'error': f"Error generando balance: {resultado_balance.get('error')}"
                }

            balance_data = resultado_balance['data']
            metadata = resultado_balance['metadata']
            # La base de datos está en metadata
            empresa_base_datos = metadata.get('base_datos')

            # 2. Obtener análisis de IA si se solicita
            analisis_ia_texto = None
            analisis_por_cuenta = {}  # Diccionario para guardar análisis por cuenta

            if incluir_analisis_ia:
                print("🤖 Obteniendo análisis de IA...")
                resultado_ia = BalanceService.analizar_balance_con_ia(
                    balance_data=balance_data,
                    metadata=metadata
                )
                if resultado_ia.get('success'):
                    analisis_ia_texto = resultado_ia.get('analisis')

                    # Extraer análisis por cuenta del texto completo
                    if analisis_ia_texto:
                        print("[ANALISIS] Extrayendo análisis por cuenta...")
                        analisis_por_cuenta = BalanceService._extraer_analisis_por_cuenta(analisis_ia_texto)

            # 3. Crear archivo Excel
            wb = Workbook()

            # === HOJA 1: BALANCE ===
            ws_balance = wb.active
            ws_balance.title = "Balance 8 Columnas"

            # Encabezado del balance
            ws_balance['A1'] = f"BALANCE DE 8 COLUMNAS"
            ws_balance['A2'] = f"Empresa: {metadata.get('nombre_empresa', '')} - RUT: {empresa_rut}"
            ws_balance['A3'] = f"Período: {periodo_inicio} - {periodo_fin}"

            # Aplicar estilos al encabezado
            for row in range(1, 4):
                ws_balance[f'A{row}'].font = Font(bold=True, size=12)

            # Agregar datos del balance
            fila_actual = 5

            # Headers del balance
            headers = ['Cuenta', 'Nombre', 'Tipo', 'Saldo Inicial Deudor', 'Saldo Inicial Acreedor',
                      'Débitos', 'Créditos', 'Activos', 'Pasivos', 'Pérdida', 'Ganancia']

            for col, header in enumerate(headers, 1):
                cell = ws_balance.cell(row=fila_actual, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                cell.font = Font(bold=True, color="FFFFFF")

            fila_actual += 1

            # Datos del balance
            cuentas_detalle = balance_data.get('cuentas_detalle', [])
            for cuenta in cuentas_detalle:
                ws_balance.cell(row=fila_actual, column=1, value=cuenta.get('cuenta'))
                ws_balance.cell(row=fila_actual, column=2, value=cuenta.get('nombre'))
                ws_balance.cell(row=fila_actual, column=3, value=cuenta.get('tipo_cuenta'))

                # Aplicar formato de número con separador de miles
                for col in range(4, 12):
                    cell = ws_balance.cell(row=fila_actual, column=col)
                    if col == 4:
                        cell.value = float(cuenta.get('saldos_iniciales_deudor', 0))
                    elif col == 5:
                        cell.value = float(cuenta.get('saldos_iniciales_acreedor', 0))
                    elif col == 6:
                        cell.value = float(cuenta.get('debitos', 0))
                    elif col == 7:
                        cell.value = float(cuenta.get('creditos', 0))
                    elif col == 8:
                        cell.value = float(cuenta.get('activos', 0))
                    elif col == 9:
                        cell.value = float(cuenta.get('pasivos', 0))
                    elif col == 10:
                        cell.value = float(cuenta.get('perdida', 0))
                    elif col == 11:
                        cell.value = float(cuenta.get('ganancia', 0))

                    # Formato de número con separador de miles
                    cell.number_format = '#,##0'

                fila_actual += 1

            # Totales
            sumas_iguales = balance_data.get('sumas_iguales') or {}
            if sumas_iguales:
                fila_actual += 1
                ws_balance.cell(row=fila_actual, column=2, value="SUMAS IGUALES").font = Font(bold=True)

                # Aplicar formato de número con separador de miles a los totales
                for col in range(4, 12):
                    cell = ws_balance.cell(row=fila_actual, column=col)
                    if col == 4:
                        cell.value = float(sumas_iguales.get('saldos_iniciales_deudor', 0))
                    elif col == 5:
                        cell.value = float(sumas_iguales.get('saldos_iniciales_acreedor', 0))
                    elif col == 6:
                        cell.value = float(sumas_iguales.get('debitos', 0))
                    elif col == 7:
                        cell.value = float(sumas_iguales.get('creditos', 0))
                    elif col == 8:
                        cell.value = float(sumas_iguales.get('activos', 0))
                    elif col == 9:
                        cell.value = float(sumas_iguales.get('pasivos', 0))
                    elif col == 10:
                        cell.value = float(sumas_iguales.get('perdida', 0))
                    elif col == 11:
                        cell.value = float(sumas_iguales.get('ganancia', 0))

                    cell.number_format = '#,##0'
                    cell.font = Font(bold=True)

            # Ajustar anchos de columna
            ws_balance.column_dimensions['A'].width = 15
            ws_balance.column_dimensions['B'].width = 40
            ws_balance.column_dimensions['C'].width = 12
            for col in 'DEFGHIJK':
                ws_balance.column_dimensions[col].width = 15

            # === HOJA 2: ANÁLISIS IA (si está disponible) ===
            if analisis_ia_texto:
                ws_analisis = wb.create_sheet("Análisis IA")
                ws_analisis['A1'] = "ANÁLISIS DE INTELIGENCIA ARTIFICIAL"
                ws_analisis['A1'].font = Font(bold=True, size=14)

                # Dividir el análisis en líneas y agregar
                lineas = analisis_ia_texto.split('\n')
                fila = 3
                for linea in lineas:
                    ws_analisis.cell(row=fila, column=1, value=linea)
                    fila += 1

                ws_analisis.column_dimensions['A'].width = 120

            # === HOJAS DE MAYORES ===
            print(f"📋 Generando mayores para {len(cuentas_detalle)} cuentas...")

            # GENERAR TODAS LAS CUENTAS CON MOVIMIENTOS (sin límite)
            # EXCLUIR cuentas de Ganancia y Pérdida (resultado)
            cuentas_con_movimiento = [c for c in cuentas_detalle
                                    if (float(c.get('debitos', 0)) > 0 or float(c.get('creditos', 0)) > 0)
                                    and (float(c.get('ganancia', 0)) == 0 and float(c.get('perdida', 0)) == 0)]

            print(f"📋 Total de cuentas con movimiento (excluyendo Ganancia/Pérdida): {len(cuentas_con_movimiento)}")

            for cuenta in cuentas_con_movimiento:
                codigo_cuenta = cuenta.get('cuenta', '')
                nombre_cuenta = cuenta.get('nombre', '')

                if not codigo_cuenta:
                    continue

                # Obtener mayor de la cuenta
                movimientos = BalanceService.obtener_mayor_cuenta(
                    empresa_base_datos=empresa_base_datos,
                    cuenta=codigo_cuenta,
                    periodo_inicio=periodo_inicio,
                    periodo_fin=periodo_fin
                )

                if not movimientos:
                    continue

                # Crear hoja para el mayor (usar código como título)
                # Excel tiene límite de 31 caracteres para nombres de hojas
                sheet_name = str(codigo_cuenta)[:31]
                ws_mayor = wb.create_sheet(sheet_name)

                # Encabezado
                ws_mayor['A1'] = f"MAYOR DE CUENTA: {codigo_cuenta} - {nombre_cuenta}"
                ws_mayor['A2'] = f"Período: {periodo_inicio} - {periodo_fin}"
                ws_mayor['A1'].font = Font(bold=True, size=12)
                ws_mayor['A2'].font = Font(bold=True, size=10)

                # Headers del mayor
                headers_mayor = ['Tipo', 'Número', 'Fecha', 'Período', 'Glosa', 'Debe', 'Haber',
                               'RUT', 'Saldo Acumulado']

                fila = 4
                for col, header in enumerate(headers_mayor, 1):
                    cell = ws_mayor.cell(row=fila, column=col, value=header)
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                    cell.font = Font(bold=True, color="FFFFFF")

                # Datos del mayor
                fila = 5
                for mov in movimientos:
                    ws_mayor.cell(row=fila, column=1, value=mov.get('Tipo'))
                    ws_mayor.cell(row=fila, column=2, value=mov.get('Numero'))

                    # Formatear fecha a dd-mm-aaaa
                    fecha_raw = mov.get('Fecha', '')

                    # Convertir a string y limpiar .0 si existe
                    if isinstance(fecha_raw, (int, float)):
                        fecha_str = str(int(fecha_raw))  # Convertir 20250206.0 -> 20250206
                    else:
                        fecha_str = str(fecha_raw)

                    # Formatear a dd-mm-aaaa
                    if fecha_str and len(fecha_str) >= 8:  # YYYYMMDD
                        try:
                            fecha_formateada = f"{fecha_str[6:8]}-{fecha_str[4:6]}-{fecha_str[0:4]}"
                            ws_mayor.cell(row=fila, column=3, value=fecha_formateada)
                        except:
                            ws_mayor.cell(row=fila, column=3, value=fecha_str)
                    else:
                        ws_mayor.cell(row=fila, column=3, value=fecha_str)

                    ws_mayor.cell(row=fila, column=4, value=mov.get('periodo'))
                    ws_mayor.cell(row=fila, column=5, value=mov.get('Glosa'))

                    # Aplicar formato de número con separador de miles
                    cell_debe = ws_mayor.cell(row=fila, column=6, value=mov.get('debe', 0))
                    cell_debe.number_format = '#,##0'

                    cell_haber = ws_mayor.cell(row=fila, column=7, value=mov.get('haber', 0))
                    cell_haber.number_format = '#,##0'

                    ws_mayor.cell(row=fila, column=8, value=mov.get('RutTesoreria'))

                    cell_saldo = ws_mayor.cell(row=fila, column=9, value=mov.get('saldo_acumulado', 0))
                    cell_saldo.number_format = '#,##0'

                    fila += 1

                # === AGREGAR ANÁLISIS DE IA PARA ESTA CUENTA ===
                # Buscar el análisis con diferentes variantes del código
                analisis_cuenta = None
                codigo_limpio = codigo_cuenta.lstrip('0') or '0'

                if codigo_cuenta in analisis_por_cuenta:
                    analisis_cuenta = analisis_por_cuenta[codigo_cuenta]
                    print(f" Análisis encontrado directo para {codigo_cuenta}")
                elif codigo_limpio in analisis_por_cuenta:
                    analisis_cuenta = analisis_por_cuenta[codigo_limpio]
                    print(f" Análisis encontrado limpio para {codigo_limpio}")
                elif '__completo__' in analisis_por_cuenta:
                    # Buscar en el análisis completo con múltiples patrones
                    analisis_completo = analisis_por_cuenta['__completo__']
                    import re

                    # Probar múltiples patrones de búsqueda
                    patrones = [
                        # Patrón 1: ### Cuenta: NOMBRE (con código)
                        rf'###\s+Cuenta:\s+[^\n]*?{codigo_cuenta}[^\n]*?\n(.*?)(?=###\s+Cuenta:|$)',
                        rf'###\s+Cuenta:\s+[^\n]*?{codigo_limpio}[^\n]*?\n(.*?)(?=###\s+Cuenta:|$)',
                        # Patrón 2: ### NOMBRE (con código)
                        rf'###\s+[^\n]*?{codigo_cuenta}[^\n]*?\n(.*?)(?=###|$)',
                        rf'###\s+[^\n]*?{codigo_limpio}[^\n]*?\n(.*?)(?=###|$)',
                        # Patrón 3: Buscar por nombre de cuenta
                        rf'###\s+[^\n]*?{re.escape(nombre_cuenta[:30])}[^\n]*?\n(.*?)(?=###|$)',
                    ]

                    for i, patron in enumerate(patrones):
                        try:
                            match = re.search(patron, analisis_completo, re.DOTALL | re.IGNORECASE)
                            if match:
                                contenido = match.group(1).strip()
                                if len(contenido) > 50:  # Validar que tenga contenido real
                                    analisis_cuenta = f"Código: {codigo_cuenta} | Tipo: {cuenta.get('tipo_cuenta', 'N/A')}\n\n{contenido}"
                                    print(f" Análisis encontrado con patrón {i+1} para {codigo_cuenta}")
                                    break
                        except Exception as e:
                            print(f"[ADVERTENCIA] Error en patrón {i+1}: {e}")
                            continue

                if analisis_cuenta:
                    fila += 2  # Espacio

                    # Separador visual
                    ws_mayor.cell(row=fila, column=1, value="═" * 100)
                    ws_mayor.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=9)
                    fila += 1

                    # Encabezado del análisis con formato destacado
                    cell_titulo = ws_mayor.cell(row=fila, column=1, value="ANÁLISIS DE IA")
                    cell_titulo.font = Font(bold=True, size=14, color="0066CC")
                    cell_titulo.fill = PatternFill(start_color="E8F4F8", end_color="E8F4F8", fill_type="solid")
                    ws_mayor.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=9)
                    fila += 1

                    # Contenido del análisis formateado
                    lineas_analisis = analisis_cuenta.split('\n')

                    for linea in lineas_analisis[:100]:  # Límite de 100 líneas
                        linea_limpia = linea.strip()
                        if linea_limpia and not linea_limpia.startswith('###'):  # Skip títulos ### duplicados
                            cell_analisis = ws_mayor.cell(row=fila, column=1, value=linea_limpia)

                            # Aplicar estilos según el contenido
                            if linea_limpia.startswith('**') or linea_limpia.startswith('- **'):
                                # Bullets y campos importantes en negrita
                                cell_analisis.font = Font(bold=True, size=10)
                            elif linea_limpia.startswith('-') and ':' in linea_limpia:
                                # Etiquetas con bullets
                                cell_analisis.font = Font(bold=True, size=10)
                            else:
                                # Texto normal
                                cell_analisis.font = Font(size=10)

                            # Aplicar wrap text para líneas largas
                            cell_analisis.alignment = Alignment(wrap_text=True, vertical='top')

                            # Merge cells para que el texto tenga más espacio
                            ws_mayor.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=9)

                            # Ajustar altura de fila para líneas largas
                            if len(linea_limpia) > 100:
                                ws_mayor.row_dimensions[fila].height = 30

                            fila += 1
                else:
                    print(f"[ADVERTENCIA] No se encontró análisis para cuenta {codigo_cuenta} ({codigo_limpio})")

                # Ajustar anchos
                ws_mayor.column_dimensions['A'].width = 10
                ws_mayor.column_dimensions['B'].width = 12
                ws_mayor.column_dimensions['C'].width = 12
                ws_mayor.column_dimensions['D'].width = 10
                ws_mayor.column_dimensions['E'].width = 50
                ws_mayor.column_dimensions['F'].width = 15
                ws_mayor.column_dimensions['G'].width = 15
                ws_mayor.column_dimensions['H'].width = 15
                ws_mayor.column_dimensions['I'].width = 15

            # Guardar en buffer
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)

            return {
                'success': True,
                'excel_buffer': output,
                'filename': f"Balance_Mayores_{empresa_rut}_{periodo_inicio}_{periodo_fin}.xlsx",
                'metadata': {
                    'empresa_rut': empresa_rut,
                    'empresa_nombre': metadata.get('nombre_empresa'),
                    'periodo_inicio': periodo_inicio,
                    'periodo_fin': periodo_fin,
                    'total_cuentas': len(cuentas_detalle),
                    'cuentas_con_mayor': len(cuentas_con_movimiento),
                    'incluye_analisis_ia': bool(analisis_ia_texto)
                }
            }

        except Exception as e:
            import traceback
            error_completo = traceback.format_exc()
            print(f"Error generando Excel completo: {e}")
            print(f"Traceback: {error_completo}")

            return {
                'success': False,
                'error': f'Error generando Excel: {str(e)}',
                'traceback': error_completo
            }


# Instancia global del servicio
balance_service = BalanceService()
