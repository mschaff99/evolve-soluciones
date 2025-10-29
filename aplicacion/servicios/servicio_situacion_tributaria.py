"""
Servicio de Situación Tributaria
================================

Consolida, para una empresa (RUT) y una base de datos dada, la información
clave desde Consulta Integral F29 y DJ Integral, para ser mostrada en una
pantalla unificada de "Situación Tributaria".
"""

from typing import Dict, Any, List, Optional
import pymysql

from aplicacion.servicios.servicio_consulta_integral import ServicioConsultaIntegral
from aplicacion.servicios.servicio_dj_integral import ServicioDJIntegral


class ServicioSituacionTributaria:
    """Servicio para consolidar F29 y DJ de una empresa específica"""

    def __init__(self, base_datos: str = 'stratex') -> None:
        self.base_datos = base_datos
        self.servicio_f29 = ServicioConsultaIntegral(base_datos)
        self.servicio_dj = ServicioDJIntegral(base_datos)

    def obtener_situacion_por_rut(self, rut: str) -> Dict[str, Any]:
        """
        Obtiene la situación tributaria consolidada (F29 + DJ) para un RUT.

        Args:
            rut: RUT de la empresa (con o sin formato)

        Returns:
            Dict con resumen de empresa, F29 y DJ.
        """
        resultado: Dict[str, Any] = {
            'rut': rut,
            'empresa': None,
            'f29': {
                'periodos': [],
                'total_observaciones': 0,
                'ultima_fecha_proceso': None,
            },
            'dj': {
                'resumen_anual': {},
                'total_observadas': 0,
                'ultima_fecha_consulta': None,
            }
        }

        # 1) Datos de empresa y F29 (consulta_integral)
        try:
            detalles = self.servicio_f29.obtener_detalles_empresa_por_rut(rut)
            if detalles:
                resultado['empresa'] = detalles

            # Traer todos los períodos de F29 para este RUT
            conexion = self.servicio_f29.obtener_conexion_evolve()
            with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = f"""
                    SELECT id, periodo, tabla_resultados, estado, fechaproceso
                    FROM {self.base_datos}.consulta_integral
                    WHERE rut = %s
                    ORDER BY periodo DESC
                """
                cursor.execute(sql, (rut,))
                periodos = cursor.fetchall()

                # Contar observaciones por periodo
                for p in periodos:
                    p_id = p['id']
                    sql_obs = f"SELECT COUNT(*) as total FROM {self.base_datos}.observaciones WHERE consulta_id = %s"
                    cursor.execute(sql_obs, (p_id,))
                    total_obs = cursor.fetchone()['total'] if cursor.rowcount is not None else 0
                    resultado['f29']['periodos'].append({
                        'periodo': p['periodo'],
                        'resultado': p.get('tabla_resultados') or '',
                        'estado': p.get('estado') or '',
                        'observaciones': total_obs,
                        'fechaproceso': p.get('fechaproceso').isoformat() if p.get('fechaproceso') else None
                    })
                    resultado['f29']['total_observaciones'] += total_obs

                if periodos:
                    resultado['f29']['ultima_fecha_proceso'] = (
                        periodos[0].get('fechaproceso').isoformat() if periodos[0].get('fechaproceso') else None
                    )
        except Exception as e:
            print(f"ERROR: Situación Tributaria - obteniendo F29: {e}")
        finally:
            try:
                if 'conexion' in locals() and conexion:
                    conexion.close()
            except Exception:
                pass

        # 2) Resumen DJ por año
        try:
            djs = self.servicio_dj.obtener_dj_por_rut(rut)
            total_observadas = 0
            resumen_anual: Dict[str, List[Dict[str, Any]]] = {}

            for dj in djs:
                for anio in ['2025', '2024', '2023', '2022', '2021', '2020']:
                    estado_campo = f"estado_{anio}"
                    estado = dj.get(estado_campo)
                    if not estado:
                        continue
                    if anio not in resumen_anual:
                        resumen_anual[anio] = []
                    resumen_anual[anio].append({
                        'dj_numero': dj['dj_numero'],
                        'titulo': dj['titulo'],
                        'estado': estado,
                        'dj_id': dj['dj_id']
                    })
                    if estado == 'Observada':
                        total_observadas += 1

            resultado['dj']['resumen_anual'] = resumen_anual
            resultado['dj']['total_observadas'] = total_observadas

            # Última fecha de consulta DJ (si está disponible via obtener_datos_empresas_con_dj)
            datos_empresas = self.servicio_dj.obtener_datos_empresas_con_dj({'rut_filtro': rut})
            ultima = None
            if datos_empresas and rut in datos_empresas.get('empresas', {}):
                ultima = datos_empresas['empresas'][rut].get('ultima_fecha_consulta')
            resultado['dj']['ultima_fecha_consulta'] = (
                ultima.isoformat() if hasattr(ultima, 'isoformat') and ultima else ultima
            )
        except Exception as e:
            print(f"ERROR: Situación Tributaria - obteniendo DJ: {e}")

        return resultado


