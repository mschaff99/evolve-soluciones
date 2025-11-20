"""
Servicio de Gestión de Empresas para Evolve Soluciones
========================================================

Maneja la lógica de negocio para empresas y credenciales SII.
"""

from typing import List, Dict, Optional, Any
import pymysql
from aplicacion.modelos.base_datos import obtener_conexion_local


class ServicioEmpresas:
    """Servicio para gestión de empresas y credenciales SII"""

    def __init__(self, base_datos='stratex'):
        """
        Inicializa el servicio con la base de datos a usar

        Args:
            base_datos (str): Nombre de la base de datos MySQL
        """
        self.base_datos = base_datos

    def obtener_conexion(self):
        """
        Obtiene conexión a la base de datos MySQL asignada

        Returns:
            Connection: Conexión PyMySQL
        """
        return obtener_conexion_local(self.base_datos)

    def obtener_todas_empresas_con_credenciales(self, filtros: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todas las empresas con sus credenciales SII

        Args:
            filtros (dict, optional): Filtros a aplicar (usuario, grupo, etc.)

        Returns:
            List[Dict]: Lista de empresas con credenciales
        """
        conexion = None
        try:
            conexion = self.obtener_conexion()

            with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
                # Construir consulta base (solo columnas que existen en la tabla)
                consulta = """
                    SELECT
                        a.run_rut,
                        a.empresa,
                        a.auditor,
                        a.grupo,
                        b.clave as clave_sii,
                        b.fecha_actualizacion as fecha_actualizacion_clave,
                        CASE
                            WHEN b.estado = 'F' THEN 'Sin configurar'
                            WHEN b.clave IS NOT NULL THEN 'Configurada'
                            ELSE 'Sin configurar'
                        END as estado_credencial
                    FROM empresas a
                    LEFT JOIN credenciales_sii b ON a.run_rut = b.rut
                    WHERE 1=1
                """

                parametros = []

                # Aplicar filtros
                if filtros:
                    if filtros.get('usuario_filtro'):
                        consulta += " AND a.auditor = %s"
                        parametros.append(filtros['usuario_filtro'])

                    if filtros.get('grupo_filtro'):
                        consulta += " AND a.grupo = %s"
                        parametros.append(filtros['grupo_filtro'])

                    # Comentado - columna 'activo' no existe en la tabla
                    # if filtros.get('activo') is not None:
                    #     consulta += " AND a.activo = %s"
                    #     parametros.append(filtros['activo'])

                    if filtros.get('buscar'):
                        consulta += " AND (a.empresa LIKE %s OR a.run_rut LIKE %s)"
                        busqueda = f"%{filtros['buscar']}%"
                        parametros.extend([busqueda, busqueda])

                consulta += " ORDER BY a.empresa ASC"

                cursor.execute(consulta, parametros)
                resultados = cursor.fetchall()

                # Convertir a lista para satisfacer el tipo de retorno
                return list(resultados) if resultados else []

        except Exception as e:
            print(f"Error obteniendo empresas con credenciales: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if conexion:
                conexion.close()

    def obtener_empresa_por_rut(self, rut: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de una empresa por RUT

        Args:
            rut (str): RUT de la empresa

        Returns:
            Dict: Datos de la empresa o None
        """
        conexion = None
        try:
            conexion = self.obtener_conexion()

            with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
                consulta = """
                    SELECT
                        a.*,
                        b.clave as clave_sii,
                        b.fecha_actualizacion as fecha_actualizacion_clave
                    FROM empresas a
                    LEFT JOIN credenciales_sii b ON a.run_rut = b.rut
                    WHERE a.run_rut = %s
                """

                cursor.execute(consulta, [rut])
                resultado = cursor.fetchone()

                return resultado

        except Exception as e:
            print(f"Error obteniendo empresa {rut}: {e}")
            return None
        finally:
            if conexion:
                conexion.close()

    def crear_empresa(self, datos: Dict[str, Any], usuario: str) -> bool:
        """
        Crea una nueva empresa

        Args:
            datos (dict): Datos de la empresa
            usuario (str): Usuario que crea el registro

        Returns:
            bool: True si se creó exitosamente
        """
        conexion = None
        try:
            conexion = self.obtener_conexion()

            with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
                # Verificar que no exista ya una empresa con ese RUT
                rut = datos.get('run_rut')
                cursor.execute("SELECT run_rut FROM empresas WHERE run_rut = %s", [rut])
                existe = cursor.fetchone()

                if existe:
                    print(f"ERROR: Ya existe una empresa con RUT {rut}")
                    return False

                # Obtener el próximo valor de orden (máximo + 1)
                cursor.execute("SELECT COALESCE(MAX(orden), 0) + 1 as siguiente_orden FROM empresas")
                resultado = cursor.fetchone()
                siguiente_orden = resultado['siguiente_orden'] if resultado else 1

                # Insertar empresa con todos los campos requeridos
                consulta = """
                    INSERT INTO empresas (
                        orden, run_rut, empresa, auditor, grupo
                    ) VALUES (
                        %s, %s, %s, %s, %s
                    )
                """

                # El auditor será el del formulario o el usuario actual como fallback
                parametros = (
                    siguiente_orden,
                    rut,
                    datos.get('empresa'),
                    datos.get('auditor') or usuario,
                    datos.get('grupo')
                )

                cursor.execute(consulta, parametros)
                filas_insertadas = cursor.rowcount
                conexion.commit()

                print(f"OK: Empresa {rut} creada exitosamente con orden {siguiente_orden} ({filas_insertadas} fila(s) insertada(s))")
                return True

        except pymysql.IntegrityError as e:
            if conexion:
                conexion.rollback()
            print(f"ERROR: Error de integridad creando empresa: {e}")
            print("       Posible RUT duplicado o violación de constraint")
            import traceback
            traceback.print_exc()
            return False
        except Exception as e:
            if conexion:
                conexion.rollback()
            print(f"ERROR: Error creando empresa: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if conexion:
                conexion.close()

    def actualizar_empresa(self, rut: str, datos: Dict[str, Any]) -> bool:
        """
        Actualiza datos de una empresa

        Args:
            rut (str): RUT de la empresa
            datos (dict): Datos a actualizar

        Returns:
            bool: True si se actualizó exitosamente
        """
        conexion = None
        try:
            conexion = self.obtener_conexion()

            with conexion.cursor() as cursor:
                # Verificar que la empresa existe antes de actualizar
                cursor.execute("SELECT run_rut FROM empresas WHERE run_rut = %s", [rut])
                existe = cursor.fetchone()

                if not existe:
                    print(f"ERROR: No se puede actualizar - La empresa con RUT {rut} no existe")
                    return False

                # Actualizar empresa
                consulta = """
                    UPDATE empresas
                    SET empresa = %s,
                        auditor = %s,
                        grupo = %s
                    WHERE run_rut = %s
                """

                parametros = (
                    datos.get('empresa'),
                    datos.get('auditor'),
                    datos.get('grupo'),
                    rut
                )

                cursor.execute(consulta, parametros)
                filas_afectadas = cursor.rowcount

                # Verificar que se actualizó al menos una fila
                if filas_afectadas == 0:
                    print(f"ADVERTENCIA: UPDATE no afectó ninguna fila para RUT {rut}")
                    return False

                conexion.commit()

                print(f"OK: Empresa {rut} actualizada exitosamente ({filas_afectadas} fila(s) afectada(s))")
                return True

        except Exception as e:
            if conexion:
                conexion.rollback()
            print(f"ERROR: Error actualizando empresa {rut}: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if conexion:
                conexion.close()

    def guardar_credencial_sii(self, rut: str, clave: str) -> bool:
        """
        Guarda o actualiza credencial SII de una empresa con encriptación reversible (Fernet)

        Usa el MISMO proceso que insertar_credencial_simple.py:
        1. Encripta la clave con Fernet
        2. Guarda en base de datos
        3. Verifica que se puede desencriptar correctamente
        4. Confirma que la desencriptación devuelve el mismo texto

        Args:
            rut (str): RUT de la empresa
            clave (str): Clave SII en texto plano

        Returns:
            bool: True si se guardó exitosamente Y se verificó la desencriptación
        """
        from aplicacion.servicios.servicio_encriptacion import servicio_encriptacion

        conexion = None
        try:
            conexion = self.obtener_conexion()

            # PASO 1: Encriptar la clave con Fernet (reversible)
            print(f"INFO: Encriptando credencial para {rut} con Fernet...")
            clave_encriptada = servicio_encriptacion.encriptar(clave)

            # Verificar formato Fernet
            if not clave_encriptada.startswith('gAAAAA'):
                print(f"ADVERTENCIA: La encriptacion no parece ser Fernet")
                return False

            with conexion.cursor() as cursor:
                # Verificar si ya existe
                cursor.execute("SELECT rut FROM credenciales_sii WHERE rut = %s", [rut])
                existe = cursor.fetchone()

                if existe:
                    # PASO 2: Actualizar
                    consulta = """
                        UPDATE credenciales_sii
                        SET clave = %s,
                            estado = 'V',
                            fecha_actualizacion = CURRENT_TIMESTAMP
                        WHERE rut = %s
                    """
                    cursor.execute(consulta, [clave_encriptada, rut])
                    print(f"INFO: Credencial SII para {rut} actualizada en base de datos")
                else:
                    # PASO 2: Insertar
                    consulta = """
                        INSERT INTO credenciales_sii (rut, clave, estado)
                        VALUES (%s, %s, 'V')
                    """
                    cursor.execute(consulta, [rut, clave_encriptada])
                    print(f"INFO: Credencial SII para {rut} creada en base de datos")

                conexion.commit()

                # PASO 3: Verificar que se puede desencriptar
                print(f"INFO: Verificando que se puede desencriptar...")
                clave_recuperada = servicio_encriptacion.desencriptar(clave_encriptada)

                # PASO 4: Confirmar que coinciden
                if clave_recuperada == clave:
                    print(f"OK: Verificacion exitosa - La contrasena se puede recuperar correctamente")
                    print(f"OK: Credencial SII para {rut} lista para automatizacion (Fernet reversible)")
                    return True
                else:
                    print(f"ERROR: La contrasena recuperada NO coincide con la original")
                    print(f"   Original: {clave[:3]}{'*' * max(0, len(clave) - 3)}")
                    print(f"   Recuperada: {clave_recuperada[:3]}{'*' * max(0, len(clave_recuperada) - 3)}")
                    # Hacer rollback porque la verificación falló
                    conexion.rollback()
                    return False

        except Exception as e:
            if conexion:
                conexion.rollback()
            print(f"ERROR: Error guardando credencial SII para {rut}: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if conexion:
                conexion.close()

    def obtener_credencial_sii_desencriptada(self, rut: str) -> Optional[str]:
        """
        Obtiene la credencial SII desencriptada (texto plano)

        Este método desencripta la contraseña almacenada con Fernet
        para permitir su uso en scripts externos.

        Args:
            rut (str): RUT de la empresa

        Returns:
            str: Contraseña en texto plano o None si no existe
        """
        from aplicacion.servicios.servicio_encriptacion import servicio_encriptacion

        conexion = None
        try:
            conexion = self.obtener_conexion()

            with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT clave FROM credenciales_sii WHERE rut = %s", [rut])
                resultado = cursor.fetchone()

                if not resultado:
                    return None

                clave_encriptada = resultado['clave']

                # Desencriptar la clave
                try:
                    clave_plana = servicio_encriptacion.desencriptar(clave_encriptada)
                    return clave_plana
                except Exception as e:
                    print(f"[ADVERTENCIA] Error desencriptando credencial para {rut}: {e}")
                    print("    Puede ser que esté en formato bcrypt (no reversible)")
                    return None

        except Exception as e:
            print(f"Error obteniendo credencial SII para {rut}: {e}")
            return None
        finally:
            if conexion:
                conexion.close()

    def verificar_credencial_existe(self, rut: str) -> Optional[dict]:
        """
        Verifica si existe una credencial para un RUT y retorna sus metadatos

        Args:
            rut (str): RUT de la empresa

        Returns:
            dict: Información de la credencial (sin la clave desencriptada) o None
        """
        conexion = None
        try:
            conexion = self.obtener_conexion()

            with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
                consulta = """
                    SELECT rut, fecha_actualizacion
                    FROM credenciales_sii
                    WHERE rut = %s
                """
                cursor.execute(consulta, [rut])
                return cursor.fetchone()

        except Exception as e:
            print(f"Error verificando credencial para {rut}: {e}")
            return None
        finally:
            if conexion:
                conexion.close()

    def eliminar_credencial_sii(self, rut: str) -> bool:
        """
        Elimina la credencial SII de una empresa

        Args:
            rut (str): RUT de la empresa

        Returns:
            bool: True si se eliminó exitosamente
        """
        conexion = None
        try:
            conexion = self.obtener_conexion()

            with conexion.cursor() as cursor:
                consulta = "DELETE FROM credenciales_sii WHERE rut = %s"
                cursor.execute(consulta, [rut])
                conexion.commit()

                print(f"[OK] Credencial SII para {rut} eliminada")
                return True

        except Exception as e:
            if conexion:
                conexion.rollback()
            print(f"Error eliminando credencial SII para {rut}: {e}")
            return False
        finally:
            if conexion:
                conexion.close()

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de empresas

        Returns:
            Dict: Estadísticas
        """
        conexion = None
        try:
            conexion = self.obtener_conexion()

            with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
                # Total empresas (sin filtro por 'activo' ya que la columna no existe)
                cursor.execute("SELECT COUNT(*) as total FROM empresas")
                total_empresas = cursor.fetchone()['total']  # type: ignore

                # Empresas con credenciales
                cursor.execute("""
                    SELECT COUNT(DISTINCT e.run_rut) as total
                    FROM empresas e
                    INNER JOIN credenciales_sii c ON e.run_rut = c.rut
                """)
                con_credenciales = cursor.fetchone()['total']  # type: ignore

                # Empresas sin credenciales
                sin_credenciales = total_empresas - con_credenciales

                # Empresas no configuradas (estado = 'F' o sin credencial)
                cursor.execute("""
                    SELECT COUNT(a.run_rut) as total
                    FROM empresas a
                    LEFT JOIN credenciales_sii b ON a.run_rut = b.rut
                    WHERE b.estado = 'F' OR b.rut IS NULL
                """)
                no_configuradas = cursor.fetchone()['total']  # type: ignore

                # Empresas por auditor
                cursor.execute("""
                    SELECT auditor, COUNT(*) as cantidad
                    FROM empresas
                    GROUP BY auditor
                    ORDER BY cantidad DESC
                """)
                por_auditor = cursor.fetchall()

                return {
                    'total_empresas': total_empresas,
                    'con_credenciales': con_credenciales,
                    'sin_credenciales': sin_credenciales,
                    'no_configuradas': no_configuradas,
                    'por_auditor': por_auditor
                }

        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {
                'total_empresas': 0,
                'con_credenciales': 0,
                'sin_credenciales': 0,
                'no_configuradas': 0,
                'por_auditor': []
            }
        finally:
            if conexion:
                conexion.close()

    def obtener_auditores_activos(self) -> List[str]:
        """
        Obtiene una lista de auditores únicos con estado 'V' (Vigente)
        desde la tabla de usuarios_acceso en la BD MySQL principal.

        Returns:
            List[str]: Lista de nombres de auditores activos.
        """
        conexion = None
        try:
            # La tabla usuarios_acceso está en la BD principal de la app (MySQL)
            conexion = self.obtener_conexion()

            with conexion.cursor() as cursor:
                # Usar la tabla y columna correctas según tu CREATE TABLE
                consulta = """
                    SELECT DISTINCT auditor
                    FROM usuarios_acceso
                    WHERE estado = 'V'
                    ORDER BY auditor ASC
                """
                cursor.execute(consulta)
                resultados = cursor.fetchall()

                # DEBUG: Imprimir cuántos auditores se encontraron
                print(f"DEBUG: Se encontraron {len(resultados)} auditores activos.")

                # Devolver una lista de nombres de auditores
                return [fila[0] for fila in resultados if fila[0]]

        except Exception as e:
            print(f"Error obteniendo auditores activos desde MySQL: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if conexion:
                conexion.close()

    def obtener_resumen_observaciones_por_auditor(self, usuario_actual) -> Dict[str, Any]:
        """
        Obtiene un resumen de observaciones por código, pivotando por auditor.
        - Los administradores ven todos los auditores.
        - Los usuarios no administradores solo ven sus propios datos.

        Args:
            usuario_actual: Objeto del usuario que realiza la solicitud.

        Returns:
            Dict: Un diccionario con 'headers', 'rows' y 'totals'.
        """
        conexion = None
        try:
            conexion = self.obtener_conexion()
            with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
                headers = []
                rows = []
                totals = {}

                if usuario_actual.es_administrador():
                    # Lógica para administradores: pivot dinámico
                    # 1. Obtener lista de auditores para las columnas
                    cursor.execute(f"""
                        SELECT DISTINCT COALESCE(c.auditor, '(Sin Asignar)') as auditor
                        FROM {self.base_datos}.observaciones a
                        LEFT JOIN {self.base_datos}.consulta_integral b ON a.consulta_id = b.id
                        LEFT JOIN {self.base_datos}.empresas c ON b.rut = c.run_rut
                        ORDER BY 1
                    """)
                    auditores = [row['auditor'] for row in cursor.fetchall()]

                    # Validar que hay auditores antes de construir pivot
                    if not auditores:
                        print(f"ADVERTENCIA: No hay auditores con observaciones en {self.base_datos}")
                        return {'headers': ['Código'], 'rows': [], 'totals': {}}

                    headers = ['Código'] + auditores

                    # 2. Construir la parte dinámica de la consulta
                    columnas_pivot = ", ".join([
                        f"SUM(CASE WHEN COALESCE(c.auditor, '(Sin Asignar)') = '{auditor}' THEN 1 ELSE 0 END) AS `{auditor}`"
                        for auditor in auditores
                    ])

                    # 3. Construir y ejecutar la consulta final
                    consulta_final = f"""
                        SELECT
                            a.codigo,
                            {columnas_pivot}
                        FROM {self.base_datos}.observaciones a
                        LEFT JOIN {self.base_datos}.consulta_integral b ON a.consulta_id = b.id
                        LEFT JOIN {self.base_datos}.empresas c ON b.rut = c.run_rut
                        GROUP BY a.codigo
                        ORDER BY a.codigo
                    """
                    cursor.execute(consulta_final)
                    rows = cursor.fetchall()

                else:
                    # Lógica para no administradores: solo sus datos
                    auditor_actual = usuario_actual.nombre_usuario
                    headers = ['Código', auditor_actual]

                    consulta = f"""
                        SELECT
                            a.codigo,
                            COUNT(a.id) as total_auditor
                        FROM {self.base_datos}.observaciones a
                        LEFT JOIN {self.base_datos}.consulta_integral b ON a.consulta_id = b.id
                        LEFT JOIN {self.base_datos}.empresas c ON b.rut = c.run_rut
                        WHERE c.auditor = %s
                        GROUP BY a.codigo
                        ORDER BY a.codigo
                    """
                    cursor.execute(consulta, (auditor_actual,))
                    resultados = cursor.fetchall()
                    # Adaptar el formato para que coincida con la estructura de la plantilla
                    for row in resultados:
                        rows.append({
                            'codigo': row['codigo'],
                            f'`{auditor_actual}`': row['total_auditor']
                        })

                # Calcular la fila de totales
                if rows:
                    totals['Código'] = 'Total'
                    for header in headers:
                        if header != 'Código':
                            col_name_in_dict = header
                            if f'`{header}`' in rows[0]:
                                col_name_in_dict = f'`{header}`'

                            total_col = sum(row.get(col_name_in_dict, 0) for row in rows)
                            totals[header] = total_col

                return {'headers': headers, 'rows': rows, 'totals': totals}

        except pymysql.err.ProgrammingError as e:
            if "doesn't exist" in str(e):
                print(f"ADVERTENCIA: Tabla de observaciones no existe en {self.base_datos}: {e}")
                return {'headers': [], 'rows': [], 'totals': {}}
            else:
                print(f"Error SQL obteniendo resumen de observaciones: {e}")
                import traceback
                traceback.print_exc()
                return {'headers': [], 'rows': [], 'totals': {}}
        except Exception as e:
            print(f"Error obteniendo resumen de observaciones: {e}")
            import traceback
            traceback.print_exc()
            return {'headers': [], 'rows': [], 'totals': {}}
        finally:
            if conexion:
                conexion.close()

    def obtener_resumen_observaciones_dj_por_auditor(self, usuario_actual) -> Dict[str, Any]:
        """
        Obtiene un resumen de observaciones de DJ por código, pivotando por auditor.
        - Los administradores ven todos los auditores.
        - Los usuarios no administradores solo ven sus propios datos.

        Args:
            usuario_actual: Objeto del usuario que realiza la solicitud.

        Returns:
            Dict: Un diccionario con 'headers', 'rows' y 'totals'.
        """
        conexion = None
        try:
            conexion = self.obtener_conexion()
            with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
                headers = []
                rows = []
                totals = {}

                if usuario_actual.es_administrador():
                    # Lógica para administradores: pivot dinámico
                    cursor.execute(f"""
                        SELECT DISTINCT COALESCE(c.auditor, '(Sin Asignar)') as auditor
                        FROM {self.base_datos}.dj_integral_observaciones a
                        LEFT JOIN {self.base_datos}.empresas c ON a.rut = c.run_rut
                        ORDER BY 1
                    """)
                    auditores = [row['auditor'] for row in cursor.fetchall()]

                    # Validar que hay auditores antes de construir pivot
                    if not auditores:
                        print(f"ADVERTENCIA: No hay auditores con observaciones DJ en {self.base_datos}")
                        return {'headers': ['Código'], 'rows': [], 'totals': {}}

                    headers = ['Código'] + auditores

                    columnas_pivot = ", ".join([
                        f"COUNT(CASE WHEN COALESCE(c.auditor, '(Sin Asignar)') = '{auditor}' THEN a.observacion_code END) AS `{auditor}`"
                        for auditor in auditores
                    ])

                    consulta_final = f"""
                        SELECT
                            a.observacion_code as codigo,
                            {columnas_pivot}
                        FROM {self.base_datos}.dj_integral_observaciones a
                        LEFT JOIN {self.base_datos}.empresas c ON a.rut = c.run_rut
                        GROUP BY a.observacion_code
                        ORDER BY a.observacion_code
                    """
                    cursor.execute(consulta_final)
                    rows = cursor.fetchall()

                else:
                    # Lógica para no administradores
                    auditor_actual = usuario_actual.nombre_usuario
                    headers = ['Código', auditor_actual]

                    consulta = f"""
                        SELECT
                            a.observacion_code as codigo,
                            COUNT(a.observacion_code) as total_auditor
                        FROM {self.base_datos}.dj_integral_observaciones a
                        LEFT JOIN {self.base_datos}.empresas c ON a.rut = c.run_rut
                        WHERE c.auditor = %s
                        GROUP BY a.observacion_code
                        ORDER BY a.observacion_code
                    """
                    cursor.execute(consulta, (auditor_actual,))
                    resultados = cursor.fetchall()
                    for row in resultados:
                        rows.append({
                            'codigo': row['codigo'],
                            f'`{auditor_actual}`': row['total_auditor']
                        })

                # Calcular totales
                if rows:
                    totals['Código'] = 'Total'
                    for header in headers:
                        if header != 'Código':
                            col_name_in_dict = f'`{header}`' if f'`{header}`' in rows[0] else header
                            total_col = sum(row.get(col_name_in_dict, 0) for row in rows)
                            totals[header] = total_col

                return {'headers': headers, 'rows': rows, 'totals': totals}

        except pymysql.err.ProgrammingError as e:
            if "doesn't exist" in str(e):
                print(f"ADVERTENCIA: Tabla de observaciones DJ no existe en {self.base_datos}: {e}")
                return {'headers': [], 'rows': [], 'totals': {}}
            else:
                print(f"Error SQL obteniendo resumen de observaciones DJ: {e}")
                import traceback
                traceback.print_exc()
                return {'headers': [], 'rows': [], 'totals': {}}
        except Exception as e:
            print(f"Error obteniendo resumen de observaciones DJ: {e}")
            import traceback
            traceback.print_exc()
            return {'headers': [], 'rows': [], 'totals': {}}
        finally:
            if conexion:
                conexion.close()
