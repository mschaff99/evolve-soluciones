"""
Script de Verificación de Conexiones - Evolve Soluciones
========================================================

Verifica que todas las conexiones a bases de datos funcionen correctamente.

Uso:
    python scripts/verificar_conexiones.py
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aplicacion.modelos.base_datos import (
    obtener_conexion_postgres,
    obtener_conexion_local,
    obtener_conexion_remota,
    obtener_conexion_mongo,
    ejecutar_consulta_postgres,
    ejecutar_consulta
)


def verificar_postgres():
    """Verifica conexión a PostgreSQL"""
    print("1. POSTGRESQL (Autenticación)")
    print("-" * 60)
    
    try:
        conexion = obtener_conexion_postgres()
        print("  Conexion: OK")
        
        # Verificar versión
        resultado = ejecutar_consulta_postgres("SELECT version()", obtener_uno=True)
        version = resultado['version'].split(',')[0] if resultado else "Desconocida"
        print(f"  Version: {version}")
        
        # Verificar esquema auth
        esquema = ejecutar_consulta_postgres(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'auth'",
            obtener_uno=True
        )
        
        if esquema:
            print("  Esquema 'auth': Existe")
            
            # Verificar tablas
            tablas = ejecutar_consulta_postgres("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'auth'
                ORDER BY table_name
            """)
            
            if tablas:
                print("  Tablas encontradas:")
                for tabla in tablas:
                    # Contar registros
                    count_query = f"SELECT COUNT(*) as total FROM auth.{tabla['table_name']}"
                    count = ejecutar_consulta_postgres(count_query, obtener_uno=True)
                    print(f"    - {tabla['table_name']}: {count['total']} registros")
        else:
            print("  Esquema 'auth': NO EXISTE")
            print("  Ejecuta: psql -U postgres -d evolve_auth -f migraciones/001_crear_tablas_autenticacion_postgres.sql")
        
        conexion.close()
        print("  Estado: CORRECTO\n")
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        print("  Estado: ERROR\n")
        return False


def verificar_mysql_local():
    """Verifica conexión a MySQL local"""
    print("2. MYSQL LOCAL (Gestión Empresarial)")
    print("-" * 60)
    
    try:
        conexion = obtener_conexion_local()
        print("  Conexion: OK")
        
        # Verificar versión
        resultado = ejecutar_consulta("SELECT VERSION() as version", obtener_uno=True)
        print(f"  Version: MySQL {resultado['version']}")
        
        # Verificar base de datos
        db_info = ejecutar_consulta("SELECT DATABASE() as db_name", obtener_uno=True)
        print(f"  Base de datos: {db_info['db_name']}")
        
        # Listar tablas
        tablas = ejecutar_consulta("SHOW TABLES")
        print(f"  Tablas encontradas: {len(tablas)}")
        
        conexion.close()
        print("  Estado: CORRECTO\n")
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        print("  Estado: ERROR (Opcional - Solo para gestión empresarial)\n")
        return False


def verificar_mysql_remota():
    """Verifica conexión a MySQL remota"""
    print("3. MYSQL REMOTA (Consolidados)")
    print("-" * 60)
    
    try:
        conexion = obtener_conexion_remota()
        print("  Conexion: OK")
        
        # Verificar versión
        resultado = ejecutar_consulta("SELECT VERSION() as version", usar_remota=True, obtener_uno=True)
        print(f"  Version: MySQL {resultado['version']}")
        
        # Verificar base de datos
        db_info = ejecutar_consulta("SELECT DATABASE() as db_name", usar_remota=True, obtener_uno=True)
        print(f"  Base de datos: {db_info['db_name']}")
        
        conexion.close()
        print("  Estado: CORRECTO\n")
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        print("  Estado: ERROR (Opcional - Solo para consolidados)\n")
        return False


def verificar_mongodb():
    """Verifica conexión a MongoDB"""
    print("4. MONGODB (Almacenamiento de Archivos)")
    print("-" * 60)
    
    try:
        db = obtener_conexion_mongo()
        print("  Conexion: OK")
        
        # Verificar colecciones
        colecciones = db.list_collection_names()
        print(f"  Colecciones encontradas: {len(colecciones)}")
        
        if colecciones:
            for col in colecciones[:5]:  # Mostrar primeras 5
                count = db[col].count_documents({})
                print(f"    - {col}: {count} documentos")
        
        print("  Estado: CORRECTO\n")
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        print("  Estado: ERROR (Opcional - Solo para archivos)\n")
        return False


def verificar_usuario_admin():
    """Verifica si existe un usuario administrador"""
    print("5. USUARIO ADMINISTRADOR")
    print("-" * 60)
    
    try:
        resultado = ejecutar_consulta_postgres("""
            SELECT id, nombre_usuario, email, rol, activo 
            FROM auth.usuarios 
            WHERE rol = 'administrador' AND activo = TRUE
            LIMIT 1
        """, obtener_uno=True)
        
        if resultado:
            print("  Usuario admin encontrado:")
            print(f"    ID: {resultado['id']}")
            print(f"    Usuario: {resultado['nombre_usuario']}")
            print(f"    Email: {resultado['email']}")
            print("  Estado: CORRECTO\n")
            return True
        else:
            print("  No se encontró usuario administrador")
            print("  Ejecuta: python scripts/inicializar_base_datos.py")
            print("  Estado: FALTA CONFIGURAR\n")
            return False
            
    except Exception as e:
        print(f"  Error: {e}")
        print("  Estado: ERROR\n")
        return False


def main():
    """Función principal"""
    print("=" * 60)
    print("VERIFICACION DE CONEXIONES - EVOLVE SOLUCIONES")
    print("=" * 60)
    print()
    
    resultados = {
        'postgres': verificar_postgres(),
        'mysql_local': verificar_mysql_local(),
        'mysql_remota': verificar_mysql_remota(),
        'mongodb': verificar_mongodb(),
        'admin': verificar_usuario_admin()
    }
    
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    # Requeridos
    print("\nREQUERIDOS:")
    print(f"  PostgreSQL (Auth):     {'OK' if resultados['postgres'] else 'ERROR'}")
    print(f"  Usuario Admin:         {'OK' if resultados['admin'] else 'FALTA'}")
    
    # Opcionales
    print("\nOPCIONALES:")
    print(f"  MySQL Local:           {'OK' if resultados['mysql_local'] else 'ERROR'}")
    print(f"  MySQL Remota:          {'OK' if resultados['mysql_remota'] else 'ERROR'}")
    print(f"  MongoDB:               {'OK' if resultados['mongodb'] else 'ERROR'}")
    
    print()
    
    # Determinar si el sistema está listo
    listo = resultados['postgres'] and resultados['admin']
    
    if listo:
        print("ESTADO GENERAL: SISTEMA LISTO PARA USAR")
        print("\nPuedes iniciar la aplicacion con:")
        print("  python aplicacion.py")
        print("\nAccede en:")
        print("  http://localhost:5000/auth/iniciar-sesion")
    else:
        print("ESTADO GENERAL: REQUIERE CONFIGURACION")
        
        if not resultados['postgres']:
            print("\n1. Configura PostgreSQL:")
            print("   - Instala PostgreSQL")
            print("   - Crea la base de datos: CREATE DATABASE evolve_auth;")
            print("   - Ejecuta migracion: psql -U postgres -d evolve_auth -f migraciones/001_crear_tablas_autenticacion_postgres.sql")
        
        if not resultados['admin']:
            print("\n2. Crea usuario administrador:")
            print("   python scripts/inicializar_base_datos.py")
    
    print()


if __name__ == "__main__":
    main()
