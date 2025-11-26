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
        Obtiene la situación tributaria consolidada (F29 + DJ + Renta) para un RUT.

        Args:
            rut: RUT de la empresa (con o sin formato)

        Returns:
            Dict con resumen de empresa, F29, DJ y Renta.
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
            },
            'renta': {
                'glosas': [],  # Situación Renta Actual
                'eventos': []  # Historial
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
                    SELECT id, periodo, tabla_resultados, estado, fechaproceso, total_observaciones
                    FROM {self.base_datos}.consulta_integral
                    WHERE rut = %s
                    AND estado = 'V'
                    ORDER BY periodo DESC
                """
                cursor.execute(sql, (rut,))
                periodos = cursor.fetchall()

                # Usar total_observaciones de la tabla consulta_integral directamente
                # Si no existe, hacer fallback a contar desde tabla observaciones
                consulta_ids = [p['id'] for p in periodos if p.get('id')]
                conteos_por_consulta = {}

                # Primero intentar usar el campo total_observaciones de consulta_integral
                usa_campo_directo = any(p.get('total_observaciones') is not None for p in periodos)

                if not usa_campo_directo and consulta_ids:
                    # Fallback: contar desde tabla observaciones
                    placeholders = ','.join(['%s'] * len(consulta_ids))
                    sql_obs_agg = f"SELECT consulta_id, COUNT(*) as total FROM {self.base_datos}.observaciones WHERE consulta_id IN ({placeholders}) GROUP BY consulta_id"
                    cursor.execute(sql_obs_agg, tuple(consulta_ids))
                    filas_conteo = cursor.fetchall()
                    for fila_c in filas_conteo:
                        conteos_por_consulta[fila_c['consulta_id']] = fila_c.get('total', 0)

                for p in periodos:
                    p_id = p.get('id')
                    # Priorizar total_observaciones de la tabla, si no usar el conteo
                    total_obs = p.get('total_observaciones') or conteos_por_consulta.get(p_id, 0) or 0
                    resultado['f29']['periodos'].append({
                        'periodo': p.get('periodo'),
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

            # Obtener última fecha de consulta directamente desde dj_integral
            try:
                conexion_dj = self.servicio_dj.obtener_conexion()
                with conexion_dj.cursor(pymysql.cursors.DictCursor) as cursor:
                    # Consulta simplificada - dj_integral NO tiene campo auditor
                    consulta_fecha = f"""
                        SELECT
                            MAX(fecha_consulta) as ultima_fecha
                        FROM {self.base_datos}.dj_integral
                        WHERE rut = %s AND estado = 'T'
                    """
                    print(f"DEBUG: Consultando fecha para RUT: {rut}")
                    cursor.execute(consulta_fecha, (rut,))
                    resultado_fecha = cursor.fetchone()
                    print(f"DEBUG: Resultado consulta fecha: {resultado_fecha}")

                    if resultado_fecha and resultado_fecha.get('ultima_fecha'):
                        ultima_fecha = resultado_fecha.get('ultima_fecha')

                        # Formatear fecha para mostrar solo la fecha (sin hora)
                        if hasattr(ultima_fecha, 'date'):
                            fecha_formateada = ultima_fecha.date().isoformat()
                        elif hasattr(ultima_fecha, 'isoformat'):
                            fecha_formateada = ultima_fecha.isoformat()
                        else:
                            fecha_formateada = str(ultima_fecha)

                        resultado['dj']['ultima_fecha_consulta'] = fecha_formateada
                        # Usuario viene de la tabla empresas, no de dj_integral
                        resultado['dj']['usuario'] = None  # No disponible en dj_integral

                        print(f"DEBUG: Fecha guardada: {fecha_formateada}")
                    else:
                        print(f"WARNING: No se encontró fecha de consulta para RUT {rut}")

            except Exception as e_fecha:
                print(f"ERROR obteniendo fecha de consulta DJ: {e_fecha}")
                import traceback
                traceback.print_exc()
            finally:
                try:
                    if 'conexion_dj' in locals() and conexion_dj:
                        conexion_dj.close()
                except Exception:
                    pass

        except Exception as e:
            print(f"ERROR: Situación Tributaria - obteniendo DJ: {e}")

        # 3) Datos de Renta (glosas y eventos) para años 2023-2025
        try:
            from datetime import datetime
            anio_actual = datetime.now().year
            periodos_renta = [anio_actual, anio_actual - 1, anio_actual - 2]  # 2025, 2024, 2023

            print(f"DEBUG RENTA: Buscando datos para RUT={rut}, periodos={periodos_renta}")

            conexion_renta = self.servicio_f29.obtener_conexion_evolve()
            with conexion_renta.cursor(pymysql.cursors.DictCursor) as cursor:
                # Obtener glosas (Situación Renta Actual)
                placeholders = ','.join(['%s'] * len(periodos_renta))
                sql_glosas = f"""
                    SELECT periodo, descripcion
                    FROM {self.base_datos}.renta_glosas
                    WHERE rut = %s AND periodo IN ({placeholders})
                    AND estado='T'
                    ORDER BY periodo DESC
                """
                print(f"DEBUG RENTA: Ejecutando SQL glosas: {sql_glosas}")
                print(f"DEBUG RENTA: Parámetros glosas: {(rut, *periodos_renta)}")
                cursor.execute(sql_glosas, (rut, *periodos_renta))
                glosas = cursor.fetchall()
                print(f"DEBUG RENTA: Glosas encontradas: {len(glosas)}")
                resultado['renta']['glosas'] = [
                    {
                        'periodo': g['periodo'],
                        'descripcion': g['descripcion']
                    }
                    for g in glosas
                ]

                # Obtener eventos (Historial) - ordenados por fecha descendente
                sql_eventos = f"""
                    SELECT periodo, folio, nombre, fecha_evento
                    FROM {self.base_datos}.renta_eventos
                    WHERE rut = %s AND periodo IN ({placeholders})
                    AND estado='T'
                    ORDER BY periodo DESC,
                             STR_TO_DATE(fecha_evento, '%%d/%%m/%%Y') DESC
                """
                print(f"DEBUG RENTA: Ejecutando SQL eventos: {sql_eventos}")
                print(f"DEBUG RENTA: Parámetros eventos: {(rut, *periodos_renta)}")
                cursor.execute(sql_eventos, (rut, *periodos_renta))
                eventos = cursor.fetchall()
                print(f"DEBUG RENTA: Eventos encontrados: {len(eventos)}")
                for i, e in enumerate(eventos[:3]):
                    print(f"DEBUG RENTA: Evento {i+1}: periodo={e.get('periodo')}, folio={e.get('folio')}, nombre={e.get('nombre', '')[:50]}")
                resultado['renta']['eventos'] = [
                    {
                        'periodo': e['periodo'],
                        'folio': e['folio'],
                        'nombre': e['nombre'],
                        'fecha_evento': e['fecha_evento']
                    }
                    for e in eventos
                ]
                print(f"DEBUG RENTA: Total eventos en resultado: {len(resultado['renta']['eventos'])}")
        except Exception as e:
            print(f"ERROR: Situación Tributaria - obteniendo Renta: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                if 'conexion_renta' in locals() and conexion_renta:
                    conexion_renta.close()
            except Exception:
                pass

        return resultado


