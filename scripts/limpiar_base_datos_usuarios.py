"""
Script para limpiar espacios en blanco del campo base_datos_mysql en la tabla usuarios
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aplicacion.modelos.base_datos import ejecutar_consulta_postgres

def limpiar_base_datos_usuarios():
    """Limpia espacios en blanco del campo base_datos_mysql"""
    try:
        # Actualizar todos los usuarios quitando espacios
        consulta_update = """
            UPDATE usuarios 
            SET base_datos_mysql = TRIM(base_datos_mysql)
            WHERE base_datos_mysql IS NOT NULL
        """
        
        ejecutar_consulta_postgres(consulta_update)
        print("✅ Espacios en blanco eliminados del campo base_datos_mysql")
        
        # Verificar resultados
        consulta_verificar = """
            SELECT id, nombre_usuario, 
                   CONCAT('[', base_datos_mysql, ']') as base_datos_con_corchetes,
                   LENGTH(base_datos_mysql) as longitud
            FROM usuarios
        """
        
        usuarios = ejecutar_consulta_postgres(consulta_verificar)
        
        if usuarios:
            print("\n📋 Usuarios actualizados:")
            for usuario in usuarios:
                print(f"   ID: {usuario['id']}")
                print(f"   Usuario: {usuario['nombre_usuario']}")
                print(f"   Base de datos: {usuario['base_datos_con_corchetes']}")
                print(f"   Longitud: {usuario['longitud']} caracteres")
                print("   " + "-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Error limpiando base de datos: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Limpiador de Espacios en Campo base_datos_mysql")
    print("=" * 60)
    
    if limpiar_base_datos_usuarios():
        print("\n✅ Proceso completado exitosamente")
    else:
        print("\n❌ El proceso falló")
