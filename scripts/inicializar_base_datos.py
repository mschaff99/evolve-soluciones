"""
Script de Inicialización de Base de Datos - Evolve Soluciones
=============================================================

Este script crea un usuario administrador por defecto en PostgreSQL
para permitir el primer acceso al sistema.

Uso:
    python scripts/inicializar_base_datos.py
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from werkzeug.security import generate_password_hash
from aplicacion.modelos.base_datos import ejecutar_consulta_postgres, ejecutar_insercion_postgres
from datetime import datetime
import getpass


def verificar_conexion():
    """Verifica que la conexión a PostgreSQL funcione"""
    try:
        # Prueba simple de conexión sin decodificar caracteres especiales
        resultado = ejecutar_consulta_postgres("SELECT 1 as test", obtener_uno=True)
        
        if resultado and resultado.get('test') == 1:
            print("Conexion exitosa a PostgreSQL")
            
            # Intentar obtener versión (puede fallar por codificación)
            try:
                version = ejecutar_consulta_postgres(
                    "SELECT current_setting('server_version') as version", 
                    obtener_uno=True
                )
                if version:
                    print(f"Version: PostgreSQL {version['version']}")
            except:
                print("Version: PostgreSQL (version no disponible)")
            
            return True
        return False
    except Exception as e:
        print(f"Error conectando a PostgreSQL: {e}")
        print("\nVerifica:")
        print("1. PostgreSQL esta instalado y ejecutandose")
        print("2. Las credenciales en .env o configuracion.py son correctas")
        print("3. La base de datos 'evolve_auth' existe")
        print("\nPara crear la base de datos, ejecuta:")
        print("  psql -U postgres -f scripts/crear_base_datos.sql")
        return False


def verificar_tablas():
    """Verifica que las tablas necesarias existan"""
    try:
        consulta = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'auth' 
            AND table_name IN ('usuarios', 'sesiones_usuario', 'intentos_login')
        """
        tablas = ejecutar_consulta_postgres(consulta)
        
        tablas_necesarias = {'usuarios', 'sesiones_usuario', 'intentos_login'}
        tablas_existentes = {tabla['table_name'] for tabla in tablas}
        
        if tablas_existentes == tablas_necesarias:
            print("Todas las tablas necesarias existen")
            return True
        else:
            faltantes = tablas_necesarias - tablas_existentes
            print(f"Faltan las siguientes tablas: {', '.join(faltantes)}")
            print("\nEjecuta primero el script de migracion:")
            print("psql -U postgres -d evolve_auth -f migraciones/001_crear_tablas_autenticacion_postgres.sql")
            return False
    except Exception as e:
        print(f"Error verificando tablas: {e}")
        return False


def usuario_admin_existe():
    """Verifica si ya existe un usuario administrador"""
    try:
        consulta = """
            SELECT COUNT(*) as total 
            FROM auth.usuarios 
            WHERE rol = 'administrador' AND activo = TRUE
        """
        resultado = ejecutar_consulta_postgres(consulta, obtener_uno=True)
        return resultado['total'] > 0
    except Exception as e:
        print(f"Error verificando usuario admin: {e}")
        return False


def crear_usuario_admin(nombre_usuario=None, email=None, contraseña=None):
    """
    Crea un usuario administrador
    
    Args:
        nombre_usuario (str): Nombre de usuario (opcional, se pedirá si no se proporciona)
        email (str): Email (opcional, se pedirá si no se proporciona)
        contraseña (str): Contraseña (opcional, se pedirá si no se proporciona)
    """
    try:
        # Solicitar datos si no se proporcionaron
        if not nombre_usuario:
            nombre_usuario = input("Nombre de usuario para admin [admin]: ").strip() or "admin"
        
        if not email:
            email = input("Email para admin [admin@evolve.cl]: ").strip() or "admin@evolve.cl"
        
        if not contraseña:
            contraseña = getpass.getpass("Contraseña para admin: ")
            confirmar = getpass.getpass("Confirmar contraseña: ")
            
            if contraseña != confirmar:
                print("Las contraseñas no coinciden")
                return False
            
            if len(contraseña) < 8:
                print("La contraseña debe tener al menos 8 caracteres")
                return False
        
        # Verificar que no exista el usuario
        verificar_usuario = """
            SELECT id FROM auth.usuarios 
            WHERE nombre_usuario = %s OR email = %s
        """
        usuario_existente = ejecutar_consulta_postgres(
            verificar_usuario, 
            (nombre_usuario, email), 
            obtener_uno=True
        )
        
        if usuario_existente:
            print(f"Ya existe un usuario con ese nombre o email")
            return False
        
        # Crear hash de contraseña
        hash_contraseña = generate_password_hash(contraseña)
        
        # Insertar usuario
        consulta = """
            INSERT INTO auth.usuarios 
            (nombre_usuario, email, hash_contraseña, rol, activo, fecha_creacion) 
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        id_usuario = ejecutar_insercion_postgres(
            consulta,
            (nombre_usuario, email, hash_contraseña, 'admin-stratex', True, datetime.now())
        )
        
        if id_usuario:
            print(f"\nUsuario administrador creado exitosamente")
            print(f"ID: {id_usuario}")
            print(f"Usuario: {nombre_usuario}")
            print(f"Email: {email}")
            print(f"Rol: administrador")
            return True
        else:
            print("Error al crear usuario administrador")
            return False
            
    except Exception as e:
        print(f"Error creando usuario administrador: {e}")
        return False


def main():
    """Función principal"""
    print("=" * 60)
    print("INICIALIZACION DE BASE DE DATOS - EVOLVE SOLUCIONES")
    print("=" * 60)
    print()
    
    # Paso 1: Verificar conexión
    print("1. Verificando conexion a PostgreSQL...")
    if not verificar_conexion():
        return
    print()
    
    # Paso 2: Verificar tablas
    print("2. Verificando tablas...")
    if not verificar_tablas():
        return
    print()
    
    # Paso 3: Verificar si ya existe admin
    print("3. Verificando usuario administrador...")
    if usuario_admin_existe():
        print("Ya existe un usuario administrador en el sistema")
        respuesta = input("\n¿Deseas crear otro usuario administrador? (s/N): ").strip().lower()
        if respuesta != 's':
            print("Cancelado")
            return
    print()
    
    # Paso 4: Crear usuario admin
    print("4. Creando usuario administrador...")
    print("-" * 60)
    
    if crear_usuario_admin():
        print("-" * 60)
        print("\nInicializacion completada exitosamente")
        print("\nPuedes iniciar sesion en:")
        print("  http://localhost:5000/auth/iniciar-sesion")
    else:
        print("Error en la inicializacion")


if __name__ == "__main__":
    main()
