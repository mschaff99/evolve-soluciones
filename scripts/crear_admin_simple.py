"""
Script Simple para Crear Usuario Administrador
==============================================

Crea un usuario administrador con credenciales predefinidas.

Uso:
    python scripts/crear_admin_simple.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from werkzeug.security import generate_password_hash
from aplicacion.modelos.base_datos import ejecutar_consulta_postgres, ejecutar_insercion_postgres
from datetime import datetime


def crear_admin():
    """Crea un usuario administrador con credenciales predefinidas"""

    # Credenciales por defecto
    nombre_usuario = "armin-stratex"
    email = "armin@evolve.cl"
    contraseña = "Armin123"  # CAMBIAR DESPUÉS DEL PRIMER LOGIN
    rol = "usuario"

    print("=" * 60)
    print("CREANDO USUARIO ADMINISTRADOR")
    print("=" * 60)
    print()
    print(f"Usuario: {nombre_usuario}")
    print(f"Email: {email}")
    print(f"Contraseña: {contraseña}")
    print(f"Rol: {rol}")
    print()
    print("NOTA: Este usuario podrá ver TODAS las empresas")
    print("Los usuarios normales solo verán empresas donde auditor = su nombre_usuario")
    print()
    print("IMPORTANTE: Cambia la contraseña después del primer login")
    print("=" * 60)
    print()

    try:
        # Verificar si ya existe
        print("Verificando si el usuario ya existe...")
        verificar = """
            SELECT id, nombre_usuario FROM auth.usuarios
            WHERE nombre_usuario = %s
        """
        existe = ejecutar_consulta_postgres(verificar, (nombre_usuario,), obtener_uno=True)

        if existe:
            print(f"ERROR: Ya existe un usuario con el nombre '{nombre_usuario}'")
            print(f"ID: {existe['id']}")
            print()
            print("Para resetear la contraseña, ejecuta en PostgreSQL:")
            print(f"  UPDATE auth.usuarios SET hash_contraseña = '{generate_password_hash(contraseña)}' WHERE nombre_usuario = '{nombre_usuario}';")
            return False

        # Crear hash de contraseña
        print("Generando hash de contraseña...")
        hash_contraseña = generate_password_hash(contraseña)

        # Insertar usuario
        print("Insertando usuario en la base de datos...")
        consulta = """
            INSERT INTO auth.usuarios
            (nombre_usuario, email, hash_contraseña, rol, activo, fecha_creacion)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        id_usuario = ejecutar_insercion_postgres(
            consulta,
            (nombre_usuario, email, hash_contraseña, rol, True, datetime.now())
        )

        if id_usuario:
            print()
            print("=" * 60)
            print("USUARIO CREADO EXITOSAMENTE")
            print("=" * 60)
            print(f"ID: {id_usuario}")
            print(f"Usuario: {nombre_usuario}")
            print(f"Email: {email}")
            print(f"Contraseña: {contraseña}")
            print(f"Rol: {rol}")
            print()
            print("Puedes iniciar sesión en:")
            print("  http://localhost:5000/auth/iniciar-sesion")
            print()
            print("RECUERDA: Cambia la contraseña después del primer login")
            print("=" * 60)
            return True
        else:
            print("ERROR: No se pudo crear el usuario")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False


if __name__ == "__main__":
    import os

    # Verificar que existe el archivo .env
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        print("ADVERTENCIA: No se encontró el archivo .env")
        print("Copiando env.ejemplo a .env...")

        ejemplo_path = Path(__file__).parent.parent / 'env.ejemplo'
        if ejemplo_path.exists():
            import shutil
            shutil.copy(ejemplo_path, env_path)
            print("Archivo .env creado. EDITA las credenciales de PostgreSQL antes de continuar.")
            print()
            input("Presiona ENTER cuando hayas configurado el archivo .env...")
        else:
            print("ERROR: No se encontró env.ejemplo")
            sys.exit(1)

    # Crear admin
    if crear_admin():
        print()
        print("Proceso completado exitosamente")
    else:
        print()
        print("Proceso completado con errores")
        sys.exit(1)
