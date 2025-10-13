"""
Script de Verificación de Multi-Base de Datos
==============================================

Verifica que el sistema funcione correctamente con múltiples bases de datos MySQL.
Prueba que las consultas se ejecuten en la base de datos correcta según el usuario.

Autor: Evolve Soluciones
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aplicacion.servicios.servicio_consulta_integral import ServicioConsultaIntegral


def verificar_servicio_con_base_datos(nombre_bd):
    """
    Prueba el servicio con una base de datos específica

    Args:
        nombre_bd (str): Nombre de la base de datos a probar

    Returns:
        bool: True si la prueba fue exitosa
    """
    print(f"\n{'='*60}")
    print(f"Probando con base de datos: {nombre_bd}")
    print(f"{'='*60}")

    try:
        # Crear instancia del servicio con la base de datos específica
        servicio = ServicioConsultaIntegral(nombre_bd)
        print(f"✓ Servicio inicializado con base_datos='{servicio.base_datos}'")

        # Intentar obtener conexión
        conexion = servicio.obtener_conexion_evolve()
        print(f"✓ Conexión a MySQL obtenida exitosamente")

        # Verificar que la conexión esté activa
        if conexion and conexion.open:
            print(f"✓ Conexión está abierta y activa")

            # Mostrar información de la conexión
            with conexion.cursor() as cursor:
                cursor.execute("SELECT DATABASE() as db_actual")
                resultado = cursor.fetchone()
                db_actual = resultado[0] if resultado else "desconocida"  # type: ignore
                print(f"✓ Base de datos actual en MySQL: {db_actual}")

                # Verificar que existe la tabla consulta_integral en la BD especificada
                cursor.execute(f"SHOW TABLES FROM {nombre_bd} LIKE 'consulta_integral'")
                tabla_existe = cursor.fetchone()

                if tabla_existe:
                    print(f"✓ Tabla '{nombre_bd}.consulta_integral' existe")

                    # Contar registros
                    cursor.execute(f"SELECT COUNT(*) as total FROM {nombre_bd}.consulta_integral")
                    resultado_count = cursor.fetchone()
                    total = resultado_count[0] if resultado_count else 0  # type: ignore
                    print(f"✓ Total de registros en '{nombre_bd}.consulta_integral': {total}")
                else:
                    print(f"⚠ Tabla '{nombre_bd}.consulta_integral' NO existe")

            conexion.close()
            print(f"✓ Conexión cerrada correctamente")
            return True
        else:
            print(f"✗ Error: Conexión no está activa")
            return False

    except Exception as e:
        print(f"✗ Error durante la prueba: {e}")
        return False


def main():
    """Función principal"""
    print("\n" + "="*60)
    print("VERIFICACIÓN DE SISTEMA MULTI-BASE DE DATOS")
    print("="*60)

    # Bases de datos a probar (ajustar según tu configuración)
    bases_datos_disponibles = ['stratex', 'evolve']

    print(f"\nSe probarán las siguientes bases de datos:")
    for bd in bases_datos_disponibles:
        print(f"  - {bd}")

    # Ejecutar pruebas
    resultados = {}
    for bd in bases_datos_disponibles:
        resultados[bd] = verificar_servicio_con_base_datos(bd)

    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN DE RESULTADOS")
    print("="*60)

    total_exitosas = sum(1 for exito in resultados.values() if exito)
    total_pruebas = len(resultados)

    for bd, exito in resultados.items():
        estado = "✓ EXITOSO" if exito else "✗ FALLIDO"
        print(f"{bd:20} : {estado}")

    print(f"\nTotal: {total_exitosas}/{total_pruebas} pruebas exitosas")

    # Verificar f-strings en consultas
    print("\n" + "="*60)
    print("VERIFICACIÓN DE CONSULTAS DINÁMICAS")
    print("="*60)

    print("\nVerificando que NO existan referencias hardcodeadas a 'stratex.'...")

    import re
    from pathlib import Path

    archivo_servicio = Path(__file__).parent.parent / 'aplicacion' / 'servicios' / 'servicio_consulta_integral.py'

    with open(archivo_servicio, 'r', encoding='utf-8') as f:
        contenido = f.read()

    # Buscar patrones de stratex. en consultas SQL
    patron = r'(FROM|JOIN)\s+stratex\.'
    coincidencias = re.findall(patron, contenido, re.IGNORECASE)

    if coincidencias:
        print(f"✗ Se encontraron {len(coincidencias)} referencias hardcodeadas a 'stratex.'")
        print("  Esto puede causar problemas con multi-tenancy.")
    else:
        print("✓ No se encontraron referencias hardcodeadas a 'stratex.'")
        print("  Todas las consultas usan f-strings dinámicos correctamente.")

    print("\n" + "="*60)
    print("FIN DE VERIFICACIÓN")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
