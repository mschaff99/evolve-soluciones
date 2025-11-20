"""
Servicio para gestionar la memoria histórica de análisis IA
Permite guardar, consultar y aprender de análisis anteriores
"""

import pymysql
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from configuracion.configuracion import ConfiguracionBase as Config


class IAMemoriaService:
    """Servicio para gestionar memoria histórica de análisis IA"""

    @staticmethod
    def guardar_analisis_ia(
        empresa_rut: str,
        empresa_nombre: str,
        periodo_inicio: int,
        periodo_fin: int,
        analisis_completo: str,
        balance_metadata: Dict,
        tiempo_procesamiento: int = 0,
        tokens_utilizados: int = 0,
        contador_responsable: str = None,
        prompt_utilizado: str = None
    ) -> Dict[str, Any]:
        """
        Guarda un análisis de IA completo en la base de datos
        """
        try:
            connection = pymysql.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                charset='utf8mb4'
            )

            with connection.cursor() as cursor:
                # Extraer hallazgos estructurados del análisis
                hallazgos = IAMemoriaService._extraer_hallazgos_del_analisis(analisis_completo)
                cuentas_problematicas = IAMemoriaService._extraer_cuentas_problematicas(analisis_completo)
                recomendaciones = IAMemoriaService._extraer_recomendaciones(analisis_completo)

                sql = """
                INSERT INTO ia_analisis_historico (
                    empresa_rut, empresa_nombre, periodo_inicio, periodo_fin,
                    analisis_completo, prompt_utilizado, total_cuentas_analizadas,
                    sumas_balance_activos, sumas_balance_pasivos, resultado_ejercicio,
                    hallazgos_detectados, cuentas_problematicas, recomendaciones,
                    tiempo_procesamiento_segundos, tokens_utilizados, contador_responsable
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """

                cursor.execute(sql, (
                    empresa_rut,
                    empresa_nombre,
                    periodo_inicio,
                    periodo_fin,
                    analisis_completo,
                    prompt_utilizado,
                    balance_metadata.get('total_cuentas_analizadas', 0),
                    float(balance_metadata.get('sumas_activos', 0)),
                    float(balance_metadata.get('sumas_pasivos', 0)),
                    float(balance_metadata.get('resultado_ejercicio', 0)),
                    json.dumps(hallazgos, ensure_ascii=False),
                    json.dumps(cuentas_problematicas, ensure_ascii=False),
                    json.dumps(recomendaciones, ensure_ascii=False),
                    tiempo_procesamiento,
                    tokens_utilizados,
                    contador_responsable
                ))

                analisis_id = cursor.lastrowid
                connection.commit()

                print(f" Análisis IA guardado - ID: {analisis_id}")

                # Intentar aprender patrones del nuevo análisis
                IAMemoriaService._aprender_patrones_del_analisis(
                    empresa_rut, analisis_completo, hallazgos
                )

                return {
                    'success': True,
                    'analisis_id': analisis_id,
                    'hallazgos_detectados': len(hallazgos),
                    'message': 'Análisis guardado exitosamente'
                }

        except Exception as e:
            print(f"Error guardando análisis IA: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            try:
                connection.close()
            except:
                pass

    @staticmethod
    def obtener_analisis_anteriores(
        empresa_rut: str,
        ultimos_n_analisis: int = 3,
        incluir_contenido_completo: bool = False
    ) -> List[Dict]:
        """
        Obtiene análisis anteriores para contexto histórico
        """
        try:
            connection = pymysql.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                charset='utf8mb4'
            )

            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                if incluir_contenido_completo:
                    campos = """
                        id, empresa_nombre, periodo_inicio, periodo_fin,
                        analisis_completo, hallazgos_detectados, cuentas_problematicas,
                        recomendaciones, estado_seguimiento, fecha_analisis
                    """
                else:
                    campos = """
                        id, empresa_nombre, periodo_inicio, periodo_fin,
                        hallazgos_detectados, cuentas_problematicas, recomendaciones,
                        estado_seguimiento, fecha_analisis
                    """

                sql = f"""
                SELECT {campos}
                FROM ia_analisis_historico
                WHERE empresa_rut = %s
                ORDER BY fecha_analisis DESC
                LIMIT %s
                """

                cursor.execute(sql, (empresa_rut, ultimos_n_analisis))
                resultados = cursor.fetchall()

                # Convertir JSON strings de vuelta a objetos
                for resultado in resultados:
                    if resultado.get('hallazgos_detectados'):
                        resultado['hallazgos_detectados'] = json.loads(resultado['hallazgos_detectados'])
                    if resultado.get('cuentas_problematicas'):
                        resultado['cuentas_problematicas'] = json.loads(resultado['cuentas_problematicas'])
                    if resultado.get('recomendaciones'):
                        resultado['recomendaciones'] = json.loads(resultado['recomendaciones'])

                return resultados

        except Exception as e:
            print(f"Error obteniendo análisis anteriores: {e}")
            return []
        finally:
            try:
                connection.close()
            except:
                pass

    @staticmethod
    def buscar_patrones_aplicables(empresa_rut: str, contexto_actual: Dict) -> List[Dict]:
        """
        Busca patrones aprendidos que puedan aplicarse al contexto actual
        """
        try:
            connection = pymysql.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                charset='utf8mb4'
            )

            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT
                    patron_nombre, patron_descripcion, tipo_problema,
                    solucion_recomendada, condiciones_activacion,
                    efectividad_porcentaje, veces_aplicado
                FROM ia_patrones_aprendidos
                WHERE activo = TRUE
                AND (empresa_rut = %s OR empresa_rut IS NULL)
                AND efectividad_porcentaje >= 70
                ORDER BY efectividad_porcentaje DESC, veces_aplicado DESC
                """

                cursor.execute(sql, (empresa_rut,))
                patrones = cursor.fetchall()

                # Filtrar patrones que apliquen al contexto actual
                patrones_aplicables = []
                for patron in patrones:
                    condiciones = json.loads(patron['condiciones_activacion'])
                    if IAMemoriaService._evaluar_condiciones_patron(condiciones, contexto_actual):
                        patrones_aplicables.append(patron)

                return patrones_aplicables

        except Exception as e:
            print(f"Error buscando patrones aplicables: {e}")
            return []
        finally:
            try:
                connection.close()
            except:
                pass

    @staticmethod
    def generar_contexto_historico_para_ia(empresa_rut: str, periodo_actual: int) -> str:
        """
        Genera un resumen del contexto histórico para incluir en el prompt de la IA
        """
        try:
            # Obtener análisis anteriores
            analisis_anteriores = IAMemoriaService.obtener_analisis_anteriores(
                empresa_rut, ultimos_n_analisis=2, incluir_contenido_completo=False
            )

            # Obtener patrones aplicables
            patrones = IAMemoriaService.buscar_patrones_aplicables(empresa_rut, {})

            contexto = "MEMORIA HISTÓRICA DE ANÁLISIS:\n\n"

            if analisis_anteriores:
                contexto += "ANÁLISIS ANTERIORES:\n"
                for i, analisis in enumerate(analisis_anteriores, 1):
                    periodo = f"{analisis['periodo_inicio']}-{analisis['periodo_fin']}"
                    contexto += f"{i}. Período {periodo} (Estado: {analisis['estado_seguimiento']}):\n"

                    if analisis.get('hallazgos_detectados'):
                        contexto += "   Hallazgos: " + "; ".join([
                            h.get('descripcion', h) if isinstance(h, dict) else str(h)
                            for h in analisis['hallazgos_detectados'][:3]
                        ]) + "\n"

                    if analisis.get('cuentas_problematicas'):
                        cuentas = [
                            c.get('cuenta', c) if isinstance(c, dict) else str(c)
                            for c in analisis['cuentas_problematicas'][:3]
                        ]
                        contexto += f"   Cuentas problemáticas: {', '.join(cuentas)}\n"

                    contexto += "\n"

            if patrones:
                contexto += "PATRONES APRENDIDOS APLICABLES:\n"
                for patron in patrones[:3]:  # Solo los 3 más efectivos
                    contexto += f"- {patron['patron_nombre']}: {patron['solucion_recomendada']}\n"
                    contexto += f"  (Efectividad: {patron['efectividad_porcentaje']}%)\n"

            contexto += "\nINSTRUCCIONES DE SEGUIMIENTO:\n"
            contexto += "- Compara el estado actual con análisis anteriores\n"
            contexto += "- Indica si problemas previos se RESOLVIERON, PERSISTEN o EMPEORARON\n"
            contexto += "- Aplica patrones aprendidos cuando corresponda\n"
            contexto += "- Prioriza cuentas que han sido problemáticas históricamente\n"
            contexto += f"- IMPORTANTE: El período actual es {periodo_actual}, NO uses períodos de análisis anteriores\n\n"

            return contexto

        except Exception as e:
            print(f"Error generando contexto histórico: {e}")
            return ""

    @staticmethod
    def _extraer_hallazgos_del_analisis(analisis_texto: str) -> List[Dict]:
        """
        Extrae hallazgos estructurados del texto del análisis
        """
        hallazgos = []

        # Buscar palabras clave que indican problemas
        palabras_problema = [
            'CRÍTICO', 'ALERTA', 'PROBLEMA', 'INCONSISTENTE',
            'ANOMALÍA', 'ERROR', 'PENDIENTE', 'VENCIDO'
        ]

        lineas = analisis_texto.split('\n')
        for linea in lineas:
            linea_upper = linea.upper()
            for palabra in palabras_problema:
                if palabra in linea_upper:
                    hallazgos.append({
                        'descripcion': linea.strip(),
                        'severidad': 'alta' if palabra in ['CRÍTICO', 'ERROR'] else 'media',
                        'tipo': 'automatico'
                    })
                    break

        return hallazgos[:10]  # Máximo 10 hallazgos más importantes

    @staticmethod
    def _extraer_cuentas_problematicas(analisis_texto: str) -> List[Dict]:
        """
        Extrae códigos de cuentas que aparecen en contextos problemáticos
        """
        import re

        cuentas = []

        # Buscar códigos de cuenta (formato 000000XXXXXX)
        patron_cuenta = r'000000\d{6}'
        matches = re.findall(patron_cuenta, analisis_texto)

        for match in set(matches):  # Eliminar duplicados
            # Buscar el contexto alrededor del código
            inicio = analisis_texto.find(match)
            if inicio != -1:
                contexto = analisis_texto[max(0, inicio-100):inicio+200]
                cuentas.append({
                    'cuenta': match,
                    'contexto': contexto.strip()
                })

        return cuentas

    @staticmethod
    def _extraer_recomendaciones(analisis_texto: str) -> List[str]:
        """
        Extrae recomendaciones del análisis
        """
        recomendaciones = []

        # Buscar líneas que contengan palabras de recomendación
        palabras_recomendacion = [
            'RECOMENDACIÓN', 'SUGERENCIA', 'DEBE', 'REVISAR',
            'VERIFICAR', 'GESTIONAR', 'CORREGIR'
        ]

        lineas = analisis_texto.split('\n')
        for linea in lineas:
            linea_upper = linea.upper()
            if any(palabra in linea_upper for palabra in palabras_recomendacion):
                if len(linea.strip()) > 20:  # Evitar líneas muy cortas
                    recomendaciones.append(linea.strip())

        return recomendaciones[:10]  # Máximo 10 recomendaciones

    @staticmethod
    def _aprender_patrones_del_analisis(empresa_rut: str, analisis_texto: str, hallazgos: List[Dict]):
        """
        Intenta aprender nuevos patrones del análisis actual
        """
        try:
            # Esta función se puede expandir para detectar patrones automáticamente
            # Por ahora, solo registra que se ejecutó
            print(f"🧠 Analizando patrones para aprendizaje automático - Empresa: {empresa_rut}")

        except Exception as e:
            print(f"[ADVERTENCIA] Error en aprendizaje de patrones: {e}")

    @staticmethod
    def _evaluar_condiciones_patron(condiciones: Dict, contexto_actual: Dict) -> bool:
        """
        Evalúa si las condiciones de un patrón se cumplen en el contexto actual
        """
        try:
            # Implementar lógica de evaluación de condiciones
            # Por ejemplo: si el patrón requiere una cuenta específica con saldo deudor
            if 'cuenta' in condiciones and 'cuenta' in contexto_actual:
                return condiciones['cuenta'] == contexto_actual['cuenta']

            # Por defecto, considerar aplicable (se puede refinar)
            return True

        except Exception as e:
            print(f"[ADVERTENCIA] Error evaluando condiciones de patrón: {e}")
            return False
