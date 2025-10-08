"""
Script para Insertar Credenciales SII desde Archivo
===================================================

Lee credenciales desde un archivo de texto y las inserta en la base de datos.

Formato del archivo (credenciales_sii.txt):
    76244083-0,120f67risesdsdr
    76553200-0,120455sofrisusdfsdfr
    12345678-9,mi_clave_secreta

También acepta formato con paréntesis y comillas:
    ("76244083-0","120f67risesdsdr"),
    ("76553200-0","120455sofrisusdfsdfr"),

Uso:
    python scripts/insertar_credenciales_desde_archivo.py [archivo]

Ejemplos:
    python scripts/insertar_credenciales_desde_archivo.py
    python scripts/insertar_credenciales_desde_archivo.py credenciales_sii.txt

Autor: Evolve Soluciones
Fecha: 2025-10-03
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from werkzeug.security import generate_password_hash
from aplicacion.modelos.base_datos import ejecutar_insercion, ejecutar_consulta, obtener_conexion_local
from datetime import datetime
import pymysql


def verificar_tabla_existe():
    """Verifica si existe la tabla credenciales_sii"""
    conexion = None
    try:
        conexion = obtener_conexion_local()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT COUNT(*) as existe
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = 'credenciales_sii'
        """)

        resultado = cursor.fetchone()

        if resultado[0] == 0:  # type: ignore
            print("La tabla 'credenciales_sii' no existe.")
            return False

        print(" Tabla 'credenciales_sii' encontrada\n")
        return True

    except pymysql.Error as e:
        print(f"Error verificando tabla: {e}")
        return False
    finally:
        if conexion:
            conexion.close()


def limpiar_linea(linea):
    """
    Limpia una línea del archivo removiendo caracteres especiales

    Args:
        linea (str): Línea del archivo

    Returns:
        str: Línea limpia
    """
    # Remover espacios, comillas, paréntesis, saltos de línea
    limpia = linea.strip()
    limpia = limpia.replace('(', '').replace(')', '')
    limpia = limpia.replace('"', '').replace("'", '')
    limpia = limpia.replace(';', '')
    return limpia


def parsear_linea(linea):
    """
    Parsea una línea del archivo y extrae RUT y clave

    Args:
        linea (str): Línea del archivo

    Returns:
        tuple: (rut, clave) o None si no se pudo parsear
    """
    try:
        # Limpiar línea
        limpia = limpiar_linea(linea)

        # Saltar líneas vacías o comentarios
        if not limpia or limpia.startswith('#') or limpia.startswith('//'):
            return None

        # Separar por coma
        partes = limpia.split(',')

        if len(partes) < 2:
            return None

        rut = partes[0].strip().replace('.', '')
        clave = partes[1].strip()

        # Validar formato básico
        if not rut or not clave:
            return None

        if '-' not in rut:
            return None

        return (rut, clave)

    except Exception as e:
        print(f"  Error parseando línea '{linea[:50]}...': {e}")
        return None


def leer_credenciales_desde_archivo(archivo_path):
    """
    Lee credenciales desde un archivo de texto

    Args:
        archivo_path (str): Ruta al archivo

    Returns:
        list: Lista de tuplas (rut, clave)
    """
    credenciales = []

    try:
        with open(archivo_path, 'r', encoding='utf-8') as f:
            for num_linea, linea in enumerate(f, 1):
                resultado = parsear_linea(linea)

                if resultado:
                    credenciales.append(resultado)

        return credenciales

    except FileNotFoundError:
        print(f"Archivo no encontrado: {archivo_path}")
        return []
    except Exception as e:
        print(f"Error leyendo archivo: {e}")
        return []


def insertar_credencial_individual(rut, clave, actualizar_existente=False):
    """Inserta una credencial individual (con hash bcrypt)"""
    try:
        # Verificar si ya existe
        verificar = "SELECT id FROM credenciales_sii WHERE rut = %s"
        existe = ejecutar_consulta(verificar, (rut,), obtener_uno=True)

        if existe:
            if actualizar_existente:
                # Hashear la clave con bcrypt
                hash_clave = generate_password_hash(clave)

                consulta_update = """
                    UPDATE credenciales_sii
                    SET clave = %s,
                        fecha_actualizacion = %s
                    WHERE rut = %s
                """

                conexion = obtener_conexion_local()
                cursor = conexion.cursor()
                cursor.execute(consulta_update, (hash_clave, datetime.now(), rut))
                conexion.commit()
                conexion.close()

                return (True, "Actualizado", existe['id'])  # type: ignore
            else:
                return (False, "Ya existe", existe['id'])  # type: ignore

        # Insertar nueva credencial
        # Hashear la clave con bcrypt
        hash_clave = generate_password_hash(clave)

        consulta_insert = """
            INSERT INTO credenciales_sii
            (rut, clave, fecha_creacion)
            VALUES (%s, %s, %s)
        """

        id_insertado = ejecutar_insercion(
            consulta_insert,
            (rut, hash_clave, datetime.now())
        )

        if id_insertado:
            return (True, "Insertado", id_insertado)
        else:
            return (False, "Error al insertar", None)

    except Exception as e:
        return (False, f"Error: {str(e)}", None)


def insertar_credenciales_masivo(credenciales, actualizar_existentes=False):
    """Inserta múltiples credenciales"""
    print("\n" + "=" * 80)
    print("INSERCIÓN MASIVA DE CREDENCIALES SII")
    print("=" * 80 + "\n")

    total = len(credenciales)
    insertados = 0
    actualizados = 0
    existentes = 0
    errores = 0

    print(f" Total de credenciales a procesar: {total}\n")
    print("-" * 80)

    for idx, (rut, clave) in enumerate(credenciales, 1):
        print(f"[{idx}/{total}] Procesando {rut}...", end=" ")

        exito, mensaje, id_registro = insertar_credencial_individual(
            rut,
            clave,
            actualizar_existentes
        )

        if exito:
            if mensaje == "Insertado":
                print(f" Insertado (ID: {id_registro})")
                insertados += 1
            elif mensaje == "Actualizado":
                print(f"🔄 Actualizado (ID: {id_registro})")
                actualizados += 1
        else:
            if "Ya existe" in mensaje:
                print(f"  Ya existe (ID: {id_registro})")
                existentes += 1
            else:
                print(f"Error: {mensaje}")
                errores += 1

    print("-" * 80)
    print("\n" + "=" * 80)
    print("RESUMEN DE INSERCIÓN MASIVA")
    print("=" * 80)
    print(f"Total procesados:    {total}")
    print(f" Insertados:       {insertados}")
    print(f" Actualizados:     {actualizados}")
    print(f"  Ya existían:      {existentes}")
    print(f"Errores:          {errores}")
    print("=" * 80 + "\n")

    return {
        'total': total,
        'insertados': insertados,
        'actualizados': actualizados,
        'existentes': existentes,
        'errores': errores
    }


def main():
    """Función principal"""

    print("\n" + "=" * 80)
    print("INSERCIÓN MASIVA DE CREDENCIALES SII DESDE ARCHIVO")
    print("Evolve Soluciones")
    print("=" * 80 + "\n")

    # Verificar tabla
    if not verificar_tabla_existe():
        print("No se pudo verificar la tabla.")
        return

    # Determinar archivo a usar
    if len(sys.argv) > 1:
        archivo = sys.argv[1]
    else:
        archivo = "scripts/credenciales_sii.txt"

        # Si no existe, informar
        if not Path(archivo).exists():
            print(f"  No se encontró el archivo: {archivo}\n")
            print("Para usar este script:")
            print(f"1. Crea un archivo de texto (ej: {archivo})")
            print("2. Agrega tus credenciales en el formato:")
            print("   RUT,CLAVE")
            print("   o")
            print('   ("RUT","CLAVE"),')
            print("\nEjemplo:")
            print("  76244083-0,mi_clave_secreta")
            print('  ("76.553.200-0","otra_clave"),')
            return

    print(f"Leyendo archivo: {archivo}\n")

    # Leer credenciales
    credenciales = leer_credenciales_desde_archivo(archivo)

    if not credenciales:
        print("No se encontraron credenciales válidas en el archivo.")
        print("\nVerifica que el formato sea correcto:")
        print("  RUT,CLAVE")
        print("\nEjemplo:")
        print("  76244083-0,mi_clave_secreta")
        print("  76.553.200-0,otra_clave")
        return

    print(f" Se leyeron {len(credenciales)} credenciales del archivo.\n")

    # Mostrar preview
    print("Vista previa de las primeras 5 credenciales:")
    print("-" * 40)
    for idx, (rut, clave) in enumerate(credenciales[:5], 1):
        print(f"{idx}. {rut} -> {'*' * len(clave)}")
    if len(credenciales) > 5:
        print(f"... y {len(credenciales) - 5} más")
    print("-" * 40 + "\n")

    # Preguntar si actualizar existentes
    respuesta = input("¿Actualizar credenciales que ya existan? (s/n) [n]: ").lower().strip()
    actualizar = (respuesta == 's')

    if actualizar:
        print("🔄 Modo: Actualizar credenciales existentes")
    else:
        print("➕ Modo: Solo insertar nuevas (omitir existentes)")

    print()
    input("Presiona ENTER para continuar o CTRL+C para cancelar...")

    # Insertar credenciales
    resultado = insertar_credenciales_masivo(credenciales, actualizar)

    if resultado['errores'] > 0:
        print("  Hubo algunos errores durante el proceso.")
    elif resultado['insertados'] > 0 or resultado['actualizados'] > 0:
        print(" Proceso completado exitosamente!")
    else:
        print("ℹ️  No se insertaron credenciales nuevas.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Operación cancelada por el usuario")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        import traceback
        traceback.print_exc()
