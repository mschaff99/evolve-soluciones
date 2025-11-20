"""
Script para verificar en qué base de datos se guardaron los datos del GCI
=========================================================================

Uso:
    python scripts/verificar_datos_guardados.py 76281385-8

Verifica en todas las bases de datos configuradas dónde están los datos.
"""

import sys
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

def verificar_en_base_datos(nombre_db, rut):
    """Verifica si existen datos para el RUT en una base de datos específica"""

    try:
        conexion = pymysql.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "audytax"),
            password=os.getenv("DB_PASSWORD", "2904"),
            database=nombre_db,
            port=int(os.getenv("DB_PORT", 3306)),
            charset='utf8mb4'
        )

        with conexion.cursor() as cursor:
            # Verificar F29 (consulta_integral)
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM consulta_integral
                WHERE rut = %s
            """, (rut,))
            total_f29 = cursor.fetchone()[0]

            # Verificar observaciones F29
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM observaciones o
                JOIN consulta_integral ci ON o.consulta_id = ci.id
                WHERE ci.rut = %s
            """, (rut,))
            total_obs_f29 = cursor.fetchone()[0]

            # Verificar DJ
            try:
                cursor.execute("""
                    SELECT COUNT(*) as total
                    FROM dj_integral
                    WHERE rut = %s
                """, (rut,))
                total_dj = cursor.fetchone()[0]

                # Verificar observaciones DJ
                cursor.execute("""
                    SELECT COUNT(*) as total
                    FROM dj_integral_observaciones
                    WHERE rut = %s
                """, (rut,))
                total_obs_dj = cursor.fetchone()[0]
            except pymysql.err.ProgrammingError:
                # Tabla no existe
                total_dj = 0
                total_obs_dj = 0

            # Obtener última fecha de proceso
            cursor.execute("""
                SELECT MAX(fecha_proceso) as ultima_fecha
                FROM consulta_integral
                WHERE rut = %s
            """, (rut,))
            ultima_fecha = cursor.fetchone()[0]

        conexion.close()

        return {
            'conectado': True,
            'total_f29': total_f29,
            'total_obs_f29': total_obs_f29,
            'total_dj': total_dj,
            'total_obs_dj': total_obs_dj,
            'ultima_fecha': ultima_fecha
        }

    except pymysql.err.OperationalError as e:
        if e.args[0] == 1049:  # Base de datos no existe
            return {'conectado': False, 'error': 'Base de datos no existe'}
        else:
            return {'conectado': False, 'error': str(e)}
    except Exception as e:
        return {'conectado': False, 'error': str(e)}


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/verificar_datos_guardados.py <RUT>")
        print("Ejemplo: python scripts/verificar_datos_guardados.py 76281385-8")
        sys.exit(1)

    rut = sys.argv[1]

    print("\n" + "="*70)
    print(f" VERIFICACIÓN: Dónde están los datos de {rut}")
    print("="*70 + "\n")

    # Bases de datos a verificar
    bases_datos = [
        'stratex',
        'gestion_consulta',
        'evolve',
        'vicat'
    ]

    resultados = {}

    for nombre_db in bases_datos:
        print(f"📊 Verificando en base de datos: {nombre_db}")
        resultado = verificar_en_base_datos(nombre_db, rut)
        resultados[nombre_db] = resultado

        if resultado['conectado']:
            print(f"    Conectado exitosamente")
            print(f"   📄 Registros F29: {resultado['total_f29']}")
            print(f"   ⚠️  Observaciones F29: {resultado['total_obs_f29']}")
            print(f"    Registros DJ: {resultado['total_dj']}")
            print(f"   🔴 Observaciones DJ: {resultado['total_obs_dj']}")
            if resultado['ultima_fecha']:
                print(f"   📅 Última actualización: {resultado['ultima_fecha']}")
            else:
                print(f"   📅 Sin datos")
        else:
            print(f"   {resultado['error']}")

        print()

    # Resumen
    print("="*70)
    print("📊 RESUMEN")
    print("="*70 + "\n")

    bases_con_datos = []
    for nombre_db, resultado in resultados.items():
        if resultado.get('conectado') and (resultado.get('total_f29', 0) > 0 or resultado.get('total_dj', 0) > 0):
            bases_con_datos.append(nombre_db)

    if not bases_con_datos:
        print("NO se encontraron datos en ninguna base de datos")
        print(f"\nPosibles causas:")
        print(f"1. El proceso GCI no se ejecutó correctamente")
        print(f"2. El RUT {rut} no tiene datos")
        print(f"3. Los datos se guardaron en otra base de datos no verificada")
    elif len(bases_con_datos) == 1:
        db_correcta = 'stratex'
        db_actual = bases_con_datos[0]

        if db_actual == db_correcta:
            print(f" Los datos están en la base de datos CORRECTA: {db_actual}")
        else:
            print(f"⚠️  Los datos están en la base de datos INCORRECTA")
            print(f"\n   Base de datos esperada: {db_correcta}")
            print(f"   Base de datos actual: {db_actual}")
            print(f"\n🔧 SOLUCIÓN:")
            print(f"   1. Verificar que config/settings.py use: DB_NAME = os.getenv('DB_NAME', 'gestion_consulta')")
            print(f"   2. Revisar el log del GCI en logs/ para confirmar qué DB_NAME recibió")
            print(f"   3. Ejecutar: python scripts/diagnosticar_gci_db.py")
    else:
        print(f"⚠️  Los datos están DUPLICADOS en múltiples bases de datos:")
        for db in bases_con_datos:
            print(f"   - {db}")

    print("\n" + "="*70)
    print("💡 PRÓXIMOS PASOS")
    print("="*70 + "\n")

    if bases_con_datos and bases_con_datos[0] != 'stratex':
        print("1. Revisar el último log del GCI:")
        print("   - Buscar la sección '🔧 CONFIGURACIÓN DE BASE DE DATOS'")
        print("   - Confirmar qué valor tiene DB_NAME\n")

        print("2. Verificar que el script GCI lee la variable de entorno:")
        print("   - Archivo: Gestion-Consulta-Integral/config/settings.py")
        print("   - Debe tener: DB_NAME = os.getenv('DB_NAME', 'gestion_consulta')\n")

        print("3. Ejecutar diagnóstico completo:")
        print("   python scripts/diagnosticar_gci_db.py\n")

        print("4. Si es necesario migrar los datos:")
        print(f"   - De: {bases_con_datos[0]}")
        print(f"   - A: stratex")
        print("   - Usar script de migración (pendiente crear)\n")

    print()


if __name__ == '__main__':
    main()
