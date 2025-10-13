"""
Modelo de Módulos del Sistema - Evolve Soluciones
==================================================

Define las clases para gestionar módulos y su habilitación por base de datos.
Permite control granular de funcionalidades por cliente/tenant.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from aplicacion.modelos.base_datos import ejecutar_consulta_postgres, ejecutar_actualizacion_postgres


class Modulo:
    """
    Representa un módulo/funcionalidad del sistema
    """

    def __init__(self, id, codigo, nombre, descripcion=None, icono=None,
                 orden_menu=0, url_base=None, requiere_licencia=False, activo=True):
        self.id = id
        self.codigo = codigo
        self.nombre = nombre
        self.descripcion = descripcion
        self.icono = icono
        self.orden_menu = orden_menu
        self.url_base = url_base
        self.requiere_licencia = requiere_licencia
        self.activo = activo

    def to_dict(self) -> Dict:
        """
        Convierte el módulo a diccionario

        Returns:
            Dict con datos del módulo
        """
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'icono': self.icono,
            'orden_menu': self.orden_menu,
            'url_base': self.url_base,
            'requiere_licencia': self.requiere_licencia,
            'activo': self.activo
        }

    @staticmethod
    def obtener_todos() -> List[Dict[str, Any]]:
        """
        Obtiene todos los módulos del sistema

        Returns:
            Lista de módulos activos
        """
        try:
            consulta = """
                SELECT id, codigo, nombre, descripcion, icono,
                       orden_menu, url_base, requiere_licencia, activo
                FROM auth.modulos_sistema
                WHERE activo = TRUE
                ORDER BY orden_menu
            """
            resultado = ejecutar_consulta_postgres(consulta)
            return resultado if isinstance(resultado, list) else []
        except Exception as e:
            print(f"Error obteniendo todos los módulos: {e}")
            return []

    @staticmethod
    def obtener_modulos_habilitados_bd(nombre_base_datos: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los módulos habilitados para una base de datos específica

        Args:
            nombre_base_datos: Nombre de la BD MySQL (ej: 'stratex', 'evolve')

        Returns:
            Lista de módulos habilitados ordenados por orden_menu
        """
        try:
            consulta = """
                SELECT
                    m.id,
                    m.codigo,
                    m.nombre,
                    m.descripcion,
                    m.icono,
                    m.orden_menu,
                    m.url_base,
                    m.requiere_licencia,
                    mh.habilitado,
                    bd.nombre_base_datos,
                    bd.nombre_cliente
                FROM auth.modulos_sistema m
                INNER JOIN auth.modulos_habilitados_bd mh ON m.id = mh.id_modulo
                INNER JOIN auth.bases_datos_mysql bd ON mh.id_base_datos = bd.id
                WHERE bd.nombre_base_datos = %s
                  AND m.activo = TRUE
                  AND mh.habilitado = TRUE
                  AND bd.activo = TRUE
                ORDER BY m.orden_menu
            """
            resultado = ejecutar_consulta_postgres(consulta, (nombre_base_datos,))
            return resultado if isinstance(resultado, list) else []
        except Exception as e:
            print(f"Error obteniendo módulos para BD {nombre_base_datos}: {e}")
            return []

    @staticmethod
    def verificar_modulo_habilitado(nombre_base_datos: str, codigo_modulo: str) -> bool:
        """
        Verifica si un módulo está habilitado para una base de datos

        Args:
            nombre_base_datos: Nombre de la BD MySQL
            codigo_modulo: Código del módulo (ej: 'consulta_f29')

        Returns:
            True si está habilitado, False si no
        """
        try:
            # Usar la función de PostgreSQL para verificación
            consulta = "SELECT auth.modulo_habilitado(%s, %s) as habilitado"
            resultado = ejecutar_consulta_postgres(
                consulta,
                (nombre_base_datos, codigo_modulo),
                obtener_uno=True
            )
            if resultado and isinstance(resultado, dict):
                return bool(resultado.get('habilitado', False))
            return False
        except Exception as e:
            print(f"Error verificando módulo {codigo_modulo} para BD {nombre_base_datos}: {e}")
            return False

    @staticmethod
    def obtener_por_codigo(codigo_modulo: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un módulo por su código

        Args:
            codigo_modulo: Código único del módulo

        Returns:
            Dict con datos del módulo o None
        """
        try:
            consulta = """
                SELECT id, codigo, nombre, descripcion, icono,
                       orden_menu, url_base, requiere_licencia, activo
                FROM auth.modulos_sistema
                WHERE codigo = %s AND activo = TRUE
            """
            resultado = ejecutar_consulta_postgres(consulta, (codigo_modulo,), obtener_uno=True)
            if resultado and isinstance(resultado, dict):
                return resultado
            return None
        except Exception as e:
            print(f"Error obteniendo módulo {codigo_modulo}: {e}")
            return None


class BaseDatosMySQL:
    """
    Representa un registro de base de datos MySQL (tenant/cliente)
    """

    def __init__(self, id, nombre_base_datos, nombre_cliente, rut_cliente=None,
                 estado='activo', plan=None, activo=True):
        self.id = id
        self.nombre_base_datos = nombre_base_datos
        self.nombre_cliente = nombre_cliente
        self.rut_cliente = rut_cliente
        self.estado = estado
        self.plan = plan
        self.activo = activo

    @staticmethod
    def obtener_todas() -> List[Dict[str, Any]]:
        """
        Obtiene todas las bases de datos registradas

        Returns:
            Lista de bases de datos activas
        """
        try:
            consulta = """
                SELECT id, nombre_base_datos, nombre_cliente, rut_cliente,
                       estado, plan, fecha_contratacion, fecha_vencimiento, activo
                FROM auth.bases_datos_mysql
                WHERE activo = TRUE
                ORDER BY nombre_cliente
            """
            resultado = ejecutar_consulta_postgres(consulta)
            return resultado if isinstance(resultado, list) else []
        except Exception as e:
            print(f"Error obteniendo bases de datos: {e}")
            return []

    @staticmethod
    def obtener_por_nombre(nombre_base_datos: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de una base de datos por su nombre

        Args:
            nombre_base_datos: Nombre de la BD MySQL

        Returns:
            Dict con datos de la BD o None
        """
        try:
            consulta = """
                SELECT id, nombre_base_datos, nombre_cliente, rut_cliente,
                       estado, plan, fecha_contratacion, fecha_vencimiento,
                       notas, activo
                FROM auth.bases_datos_mysql
                WHERE nombre_base_datos = %s AND activo = TRUE
            """
            resultado = ejecutar_consulta_postgres(consulta, (nombre_base_datos,), obtener_uno=True)
            if resultado and isinstance(resultado, dict):
                return resultado
            return None
        except Exception as e:
            print(f"Error obteniendo BD {nombre_base_datos}: {e}")
            return None

    @staticmethod
    def validar_existe(nombre_base_datos: str) -> bool:
        """
        Valida que una base de datos esté registrada y activa

        Args:
            nombre_base_datos: Nombre de la BD MySQL

        Returns:
            True si existe y está activa
        """
        try:
            consulta = """
                SELECT COUNT(*) as total
                FROM auth.bases_datos_mysql
                WHERE nombre_base_datos = %s AND activo = TRUE
            """
            resultado = ejecutar_consulta_postgres(
                consulta,
                (nombre_base_datos,),
                obtener_uno=True
            )
            if resultado and isinstance(resultado, dict):
                return bool(resultado.get('total', 0) > 0)
            return False
        except Exception as e:
            print(f"Error validando BD {nombre_base_datos}: {e}")
            return False

    @staticmethod
    def obtener_modulos_habilitados(nombre_base_datos: str) -> List[Dict[str, Any]]:
        """
        Obtiene los módulos habilitados para esta BD

        Args:
            nombre_base_datos: Nombre de la BD MySQL

        Returns:
            Lista de módulos habilitados
        """
        return Modulo.obtener_modulos_habilitados_bd(nombre_base_datos)


class GestorModulos:
    """
    Clase de utilidad para gestión de módulos y permisos
    """

    @staticmethod
    def habilitar_modulo(nombre_base_datos: str, codigo_modulo: str, usuario: Optional[str] = None) -> bool:
        """
        Habilita un módulo para una base de datos

        Args:
            nombre_base_datos: Nombre de la BD MySQL
            codigo_modulo: Código del módulo a habilitar
            usuario: Usuario que realiza la habilitación (opcional)

        Returns:
            True si se habilitó correctamente
        """
        try:
            # Obtener IDs
            bd = BaseDatosMySQL.obtener_por_nombre(nombre_base_datos)
            modulo = Modulo.obtener_por_codigo(codigo_modulo)

            if not bd or not modulo:
                print(f"BD o módulo no encontrado: {nombre_base_datos}, {codigo_modulo}")
                return False

            # Insertar o actualizar
            consulta = """
                INSERT INTO auth.modulos_habilitados_bd
                    (id_base_datos, id_modulo, habilitado, usuario_habilitacion, fecha_habilitacion)
                VALUES (%s, %s, TRUE, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (id_base_datos, id_modulo)
                DO UPDATE SET
                    habilitado = TRUE,
                    fecha_habilitacion = CURRENT_TIMESTAMP,
                    usuario_habilitacion = EXCLUDED.usuario_habilitacion
            """
            ejecutar_actualizacion_postgres(consulta, (bd['id'], modulo['id'], usuario))
            return True
        except Exception as e:
            print(f"Error habilitando módulo {codigo_modulo} para {nombre_base_datos}: {e}")
            return False

    @staticmethod
    def deshabilitar_modulo(nombre_base_datos: str, codigo_modulo: str) -> bool:
        """
        Deshabilita un módulo para una base de datos

        Args:
            nombre_base_datos: Nombre de la BD MySQL
            codigo_modulo: Código del módulo a deshabilitar

        Returns:
            True si se deshabilitó correctamente
        """
        try:
            consulta = """
                UPDATE auth.modulos_habilitados_bd mh
                SET habilitado = FALSE,
                    fecha_deshabilitacion = CURRENT_TIMESTAMP
                FROM auth.bases_datos_mysql bd, auth.modulos_sistema m
                WHERE mh.id_base_datos = bd.id
                  AND mh.id_modulo = m.id
                  AND bd.nombre_base_datos = %s
                  AND m.codigo = %s
            """
            ejecutar_actualizacion_postgres(consulta, (nombre_base_datos, codigo_modulo))
            return True
        except Exception as e:
            print(f"Error deshabilitando módulo {codigo_modulo} para {nombre_base_datos}: {e}")
            return False

    @staticmethod
    def obtener_resumen_modulos_bd(nombre_base_datos: str) -> Dict:
        """
        Obtiene un resumen de módulos disponibles vs habilitados

        Args:
            nombre_base_datos: Nombre de la BD MySQL

        Returns:
            Dict con resumen de módulos
        """
        try:
            todos_modulos = Modulo.obtener_todos()
            modulos_habilitados = Modulo.obtener_modulos_habilitados_bd(nombre_base_datos)

            codigos_habilitados = {m['codigo'] for m in modulos_habilitados}

            return {
                'base_datos': nombre_base_datos,
                'total_modulos_sistema': len(todos_modulos),
                'total_modulos_habilitados': len(modulos_habilitados),
                'modulos_habilitados': modulos_habilitados,
                'modulos_disponibles': [
                    m for m in todos_modulos if m['codigo'] not in codigos_habilitados
                ]
            }
        except Exception as e:
            print(f"Error obteniendo resumen de módulos: {e}")
            return {}
