"""
Conexiones y operaciones de base de datos para Evolve Soluciones
================================================================

Este módulo maneja todas las conexiones a bases de datos y operaciones
básicas de acceso a datos.

ARQUITECTURA DE BASES DE DATOS:
- PostgreSQL: Sistema de autenticación (usuarios y sesiones)
- MySQL: Gestión empresarial (empresas, F29, consolidados, etc.)
- MongoDB: Almacenamiento de archivos (opcional)
"""

import psycopg2
import psycopg2.extras
import pymysql
from pymongo import MongoClient
from configuracion.configuracion import obtener_configuracion

# Obtener configuración actual
config = obtener_configuracion()


# ==========================================
# CONEXIONES POSTGRESQL (AUTENTICACIÓN)
# ==========================================

def obtener_conexion_postgres():
    """
    Obtiene una conexión a la base de datos PostgreSQL (autenticación)
    
    Returns:
        psycopg2.Connection: Conexión a PostgreSQL
    """
    try:
        # Conectar con configuración UTF-8 explícita
        conexion = psycopg2.connect(
            host=config.POSTGRES_HOST,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            database=config.POSTGRES_DB,
            port=config.POSTGRES_PORT,
            connect_timeout=30,
            options='-c client_encoding=UTF8'
        )
        
        # Configurar encoding después de conectar
        conexion.set_client_encoding('UTF8')
        
        return conexion
    except Exception as e:
        print(f"Error conectando a PostgreSQL: {e}")
        raise


def ejecutar_consulta_postgres(consulta_sql, parametros=None, obtener_uno=False):
    """
    Ejecuta una consulta SQL en PostgreSQL
    
    Args:
        consulta_sql (str): Consulta SQL a ejecutar
        parametros (tuple): Parámetros para la consulta
        obtener_uno (bool): Si obtener solo un resultado
        
    Returns:
        list|dict: Resultados de la consulta
    """
    conexion = None
    try:
        conexion = obtener_conexion_postgres()
        
        with conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            if parametros:
                cursor.execute(consulta_sql, parametros)
            else:
                cursor.execute(consulta_sql)
            
            if obtener_uno:
                resultado = cursor.fetchone()
                return dict(resultado) if resultado else None
            else:
                resultados = cursor.fetchall()
                return [dict(row) for row in resultados]
                
    except Exception as e:
        print(f"Error ejecutando consulta en PostgreSQL: {e}")
        raise
    finally:
        if conexion:
            conexion.close()


def ejecutar_insercion_postgres(consulta_sql, parametros=None):
    """
    Ejecuta una inserción en PostgreSQL
    
    Args:
        consulta_sql (str): Consulta SQL de inserción
        parametros (tuple): Parámetros para la consulta
        
    Returns:
        int: ID del registro insertado
    """
    conexion = None
    try:
        conexion = obtener_conexion_postgres()
        
        with conexion.cursor() as cursor:
            if parametros:
                cursor.execute(consulta_sql, parametros)
            else:
                cursor.execute(consulta_sql)
            
            # PostgreSQL usa RETURNING para obtener el ID
            if 'RETURNING' in consulta_sql.upper():
                resultado = cursor.fetchone()
                id_insertado = resultado[0] if resultado else None
            else:
                id_insertado = cursor.lastrowid if hasattr(cursor, 'lastrowid') else None
            
            conexion.commit()
            return id_insertado
            
    except Exception as e:
        if conexion:
            conexion.rollback()
        print(f"Error ejecutando inserción en PostgreSQL: {e}")
        raise
    finally:
        if conexion:
            conexion.close()


def ejecutar_actualizacion_postgres(consulta_sql, parametros=None):
    """
    Ejecuta una actualización en PostgreSQL
    
    Args:
        consulta_sql (str): Consulta SQL de actualización
        parametros (tuple): Parámetros para la consulta
        
    Returns:
        int: Número de filas afectadas
    """
    conexion = None
    try:
        conexion = obtener_conexion_postgres()
        
        with conexion.cursor() as cursor:
            if parametros:
                filas_afectadas = cursor.execute(consulta_sql, parametros)
            else:
                filas_afectadas = cursor.execute(consulta_sql)
            
            conexion.commit()
            return cursor.rowcount
            
    except Exception as e:
        if conexion:
            conexion.rollback()
        print(f"Error ejecutando actualización en PostgreSQL: {e}")
        raise
    finally:
        if conexion:
            conexion.close()


# ==========================================
# CONEXIONES MYSQL (GESTIÓN EMPRESARIAL)
# ==========================================

def obtener_conexion_local(nombre_base_datos=None):
    """
    Obtiene una conexión a la base de datos MySQL local (empresas)
    
    Args:
        nombre_base_datos (str): Nombre de la base de datos. Si no se especifica, usa la configurada por defecto
    
    Returns:
        pymysql.Connection: Conexión a la base de datos local
    """
    try:
        # Usar la base de datos especificada o la por defecto
        database = nombre_base_datos if nombre_base_datos else config.DB_NAME
        
        conexion = pymysql.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=database,
            port=config.DB_PORT,
            charset='utf8',
            connect_timeout=30,
            read_timeout=30,
            write_timeout=30,
            autocommit=False
        )
        return conexion
    except Exception as e:
        print(f"Error conectando a base de datos MySQL local ({database}): {e}")
        raise


def obtener_conexion_usuario(usuario):
    """
    Obtiene una conexión MySQL usando la base de datos asignada al usuario
    
    Args:
        usuario: Instancia de Usuario con base_datos_mysql configurada
        
    Returns:
        pymysql.Connection: Conexión a la base de datos del usuario
    """
    base_datos = usuario.base_datos_mysql if hasattr(usuario, 'base_datos_mysql') and usuario.base_datos_mysql else config.DB_NAME
    return obtener_conexion_local(base_datos)


def obtener_conexion_remota():
    """
    Obtiene una conexión a la base de datos MySQL remota (para consolidados)
    
    Returns:
        pymysql.Connection: Conexión a la base de datos remota
    """
    try:
        conexion = pymysql.connect(
            host=config.REMOTE_DB_HOST,
            user=config.REMOTE_DB_USER,
            password=config.REMOTE_DB_PASSWORD,
            database=config.REMOTE_DB_NAME,
            port=config.REMOTE_DB_PORT,
            charset='utf8',
            connect_timeout=60,
            read_timeout=600,  # 10 minutos para consultas pesadas
            write_timeout=60,
            autocommit=True
        )
        return conexion
    except Exception as e:
        print(f"Error conectando a base de datos MySQL remota: {e}")
        raise


def ejecutar_procedimiento_almacenado(nombre_procedimiento, parametros=None, usar_remota=True):
    """
    Ejecuta un procedimiento almacenado en la base de datos MySQL
    
    Args:
        nombre_procedimiento (str): Nombre del procedimiento a ejecutar
        parametros (list): Lista de parámetros para el procedimiento
        usar_remota (bool): Si usar la base de datos remota o local
        
    Returns:
        list: Resultados del procedimiento almacenado
    """
    conexion = None
    try:
        # Seleccionar tipo de conexión
        if usar_remota:
            conexion = obtener_conexion_remota()
        else:
            conexion = obtener_conexion_local()
        
        with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
            if parametros:
                cursor.callproc(nombre_procedimiento, parametros)
            else:
                cursor.callproc(nombre_procedimiento)
            
            resultados = cursor.fetchall()
            return resultados
            
    except Exception as e:
        print(f"Error ejecutando procedimiento {nombre_procedimiento}: {e}")
        raise
    finally:
        if conexion:
            conexion.close()


def ejecutar_consulta(consulta_sql, parametros=None, usar_remota=False, obtener_uno=False):
    """
    Ejecuta una consulta SQL en la base de datos MySQL
    
    Args:
        consulta_sql (str): Consulta SQL a ejecutar
        parametros (tuple): Parámetros para la consulta
        usar_remota (bool): Si usar la base de datos remota o local
        obtener_uno (bool): Si obtener solo un resultado
        
    Returns:
        list|dict: Resultados de la consulta
    """
    conexion = None
    try:
        # Seleccionar tipo de conexión
        if usar_remota:
            conexion = obtener_conexion_remota()
        else:
            conexion = obtener_conexion_local()
        
        with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
            if parametros:
                cursor.execute(consulta_sql, parametros)
            else:
                cursor.execute(consulta_sql)
            
            if obtener_uno:
                return cursor.fetchone()
            else:
                return cursor.fetchall()
                
    except Exception as e:
        print(f"Error ejecutando consulta en MySQL: {e}")
        raise
    finally:
        if conexion:
            conexion.close()


def ejecutar_insercion(consulta_sql, parametros=None, usar_remota=False):
    """
    Ejecuta una inserción en la base de datos MySQL
    
    Args:
        consulta_sql (str): Consulta SQL de inserción
        parametros (tuple): Parámetros para la consulta
        usar_remota (bool): Si usar la base de datos remota o local
        
    Returns:
        int: ID del registro insertado
    """
    conexion = None
    try:
        # Seleccionar tipo de conexión
        if usar_remota:
            conexion = obtener_conexion_remota()
        else:
            conexion = obtener_conexion_local()
        
        with conexion.cursor() as cursor:
            if parametros:
                cursor.execute(consulta_sql, parametros)
            else:
                cursor.execute(consulta_sql)
            
            conexion.commit()
            return cursor.lastrowid
            
    except Exception as e:
        if conexion:
            conexion.rollback()
        print(f"Error ejecutando inserción en MySQL: {e}")
        raise
    finally:
        if conexion:
            conexion.close()


def ejecutar_actualizacion(consulta_sql, parametros=None, usar_remota=False):
    """
    Ejecuta una actualización en la base de datos MySQL
    
    Args:
        consulta_sql (str): Consulta SQL de actualización
        parametros (tuple): Parámetros para la consulta
        usar_remota (bool): Si usar la base de datos remota o local
        
    Returns:
        int: Número de filas afectadas
    """
    conexion = None
    try:
        # Seleccionar tipo de conexión
        if usar_remota:
            conexion = obtener_conexion_remota()
        else:
            conexion = obtener_conexion_local()
        
        with conexion.cursor() as cursor:
            if parametros:
                filas_afectadas = cursor.execute(consulta_sql, parametros)
            else:
                filas_afectadas = cursor.execute(consulta_sql)
            
            conexion.commit()
            return filas_afectadas
            
    except Exception as e:
        if conexion:
            conexion.rollback()
        print(f"Error ejecutando actualización en MySQL: {e}")
        raise
    finally:
        if conexion:
            conexion.close()


# ==========================================
# MONGODB (ALMACENAMIENTO DE ARCHIVOS)
# ==========================================

def obtener_conexion_mongo():
    """
    Obtiene una conexión a MongoDB
    
    Returns:
        pymongo.database.Database: Conexión a la base de datos MongoDB
    """
    try:
        cliente = MongoClient(config.MONGO_URI)
        base_datos = cliente[config.MONGO_DB_NAME]
        return base_datos
    except Exception as e:
        print(f"Error conectando a MongoDB: {e}")
        raise


# ==========================================
# MANEJADORES CONTEXTUALES
# ==========================================

class ManejadorBaseDatos:
    """Clase para manejar operaciones de base de datos MySQL de forma contextual"""
    
    def __init__(self, usar_remota=False):
        self.usar_remota = usar_remota
        self.conexion = None
    
    def __enter__(self):
        """Abre conexión al entrar al contexto"""
        if self.usar_remota:
            self.conexion = obtener_conexion_remota()
        else:
            self.conexion = obtener_conexion_local()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cierra conexión al salir del contexto"""
        if self.conexion:
            if exc_type is not None:
                self.conexion.rollback()
            else:
                self.conexion.commit()
            self.conexion.close()
    
    def ejecutar_consulta(self, consulta_sql, parametros=None, obtener_uno=False):
        """Ejecuta una consulta usando la conexión del contexto"""
        with self.conexion.cursor(pymysql.cursors.DictCursor) as cursor:
            if parametros:
                cursor.execute(consulta_sql, parametros)
            else:
                cursor.execute(consulta_sql)
            
            if obtener_uno:
                return cursor.fetchone()
            else:
                return cursor.fetchall()
    
    def ejecutar_insercion(self, consulta_sql, parametros=None):
        """Ejecuta una inserción usando la conexión del contexto"""
        with self.conexion.cursor() as cursor:
            if parametros:
                cursor.execute(consulta_sql, parametros)
            else:
                cursor.execute(consulta_sql)
            return cursor.lastrowid


class ManejadorPostgreSQL:
    """Clase para manejar operaciones de PostgreSQL de forma contextual"""
    
    def __init__(self):
        self.conexion = None
    
    def __enter__(self):
        """Abre conexión al entrar al contexto"""
        self.conexion = obtener_conexion_postgres()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cierra conexión al salir del contexto"""
        if self.conexion:
            if exc_type is not None:
                self.conexion.rollback()
            else:
                self.conexion.commit()
            self.conexion.close()
    
    def ejecutar_consulta(self, consulta_sql, parametros=None, obtener_uno=False):
        """Ejecuta una consulta usando la conexión del contexto"""
        with self.conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            if parametros:
                cursor.execute(consulta_sql, parametros)
            else:
                cursor.execute(consulta_sql)
            
            if obtener_uno:
                resultado = cursor.fetchone()
                return dict(resultado) if resultado else None
            else:
                resultados = cursor.fetchall()
                return [dict(row) for row in resultados]
    
    def ejecutar_insercion(self, consulta_sql, parametros=None):
        """Ejecuta una inserción usando la conexión del contexto"""
        with self.conexion.cursor() as cursor:
            if parametros:
                cursor.execute(consulta_sql, parametros)
            else:
                cursor.execute(consulta_sql)
            
            if 'RETURNING' in consulta_sql.upper():
                resultado = cursor.fetchone()
                return resultado[0] if resultado else None
            return None