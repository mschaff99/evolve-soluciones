"""
Script para Insertar Credenciales SII de Forma Masiva
=====================================================

Permite insertar múltiples credenciales del SII desde una lista en el código
o desde un archivo.

Uso:
    python scripts/insertar_credenciales_masivo.py

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
    """
    Verifica si existe la tabla credenciales_sii

    Returns:
        bool: True si la tabla existe
    """
    conexion = None
    try:
        conexion = obtener_conexion_local()
        cursor = conexion.cursor()

        # Verificar si la tabla existe
        cursor.execute("""
            SELECT COUNT(*) as existe
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = 'credenciales_sii'
        """)

        resultado = cursor.fetchone()

        if resultado[0] == 0:  # type: ignore
            print("❌ La tabla 'credenciales_sii' no existe.")
            print("\nLa tabla debe existir con la siguiente estructura:")
            print("""
CREATE TABLE `credenciales_sii` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `rut` VARCHAR(20) NOT NULL,
    `clave` VARCHAR(255) NOT NULL,
    `fecha_creacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` DATETIME NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE INDEX `rut` (`rut`),
    INDEX `idx_rut` (`rut`),
    INDEX `idx_fecha_creacion` (`fecha_creacion`)
) ENGINE=InnoDB COLLATE='utf8_unicode_ci';
            """)
            return False

        print(" Tabla 'credenciales_sii' encontrada\n")
        return True

    except pymysql.Error as e:
        print(f"❌ Error verificando tabla: {e}")
        return False
    finally:
        if conexion:
            conexion.close()


def limpiar_rut(rut):
    """Limpia el RUT removiendo puntos pero manteniendo el guión"""
    return rut.replace(".", "").replace('"', '').replace("'", '').strip()


def insertar_credencial_individual(rut, clave, actualizar_existente=False):
    """
    Inserta una credencial individual

    Args:
        rut (str): RUT del contribuyente
        clave (str): Clave en texto plano (se hasheará con bcrypt)
        actualizar_existente (bool): Si True, actualiza si ya existe

    Returns:
        tuple: (exito: bool, mensaje: str, id: int|None)
    """
    try:
        rut_limpio = limpiar_rut(rut)

        # Verificar si ya existe
        verificar = "SELECT id FROM credenciales_sii WHERE rut = %s"
        existe = ejecutar_consulta(verificar, (rut_limpio,), obtener_uno=True)

        if existe:
            if actualizar_existente:
                # Actualizar credencial existente
                # IMPORTANTE: Hashear la clave con bcrypt
                hash_clave = generate_password_hash(clave)

                consulta_update = """
                    UPDATE credenciales_sii
                    SET clave = %s,
                        fecha_actualizacion = %s
                    WHERE rut = %s
                """

                conexion = obtener_conexion_local()
                cursor = conexion.cursor()
                cursor.execute(consulta_update, (hash_clave, datetime.now(), rut_limpio))
                conexion.commit()
                conexion.close()

                return (True, "Actualizado", existe['id'])  # type: ignore
            else:
                return (False, "Ya existe", existe['id'])  # type: ignore

        # Insertar nueva credencial
        # IMPORTANTE: Hashear la clave con bcrypt
        hash_clave = generate_password_hash(clave)

        consulta_insert = """
            INSERT INTO credenciales_sii
            (rut, clave, fecha_creacion)
            VALUES (%s, %s, %s)
        """

        id_insertado = ejecutar_insercion(
            consulta_insert,
            (rut_limpio, hash_clave, datetime.now())
        )

        if id_insertado:
            return (True, "Insertado", id_insertado)
        else:
            return (False, "Error al insertar", None)

    except Exception as e:
        return (False, f"Error: {str(e)}", None)


def insertar_credenciales_masivo(credenciales, actualizar_existentes=False):
    """
    Inserta múltiples credenciales de forma masiva

    Args:
        credenciales (list): Lista de tuplas (rut, clave)
        actualizar_existentes (bool): Si True, actualiza las que ya existen

    Returns:
        dict: Estadísticas del proceso
    """
    print("\n" + "=" * 80)
    print("INSERCIÓN MASIVA DE CREDENCIALES SII")
    print("=" * 80 + "\n")

    total = len(credenciales)
    insertados = 0
    actualizados = 0
    existentes = 0
    errores = 0

    print(f"📊 Total de credenciales a procesar: {total}\n")
    print("-" * 80)

    for idx, (rut, clave) in enumerate(credenciales, 1):
        rut_limpio = limpiar_rut(rut)

        # Mostrar progreso
        print(f"[{idx}/{total}] Procesando {rut_limpio}...", end=" ")

        exito, mensaje, id_registro = insertar_credencial_individual(
            rut_limpio,
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
                print(f"⚠️  Ya existe (ID: {id_registro})")
                existentes += 1
            else:
                print(f"❌ Error: {mensaje}")
                errores += 1

    print("-" * 80)
    print("\n" + "=" * 80)
    print("RESUMEN DE INSERCIÓN MASIVA")
    print("=" * 80)
    print(f"Total procesados:    {total}")
    print(f" Insertados:       {insertados}")
    print(f"🔄 Actualizados:     {actualizados}")
    print(f"⚠️  Ya existían:      {existentes}")
    print(f"❌ Errores:          {errores}")
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
    print("INSERCIÓN MASIVA DE CREDENCIALES SII - Evolve Soluciones")
    print("=" * 80 + "\n")

    # Verificar que exista la tabla
    if not verificar_tabla_existe():
        print("❌ No se pudo verificar la tabla. Verifica la conexión a la base de datos.")
        print("   O asegúrate de que la tabla 'credenciales_sii' exista.")
        return

    # AQUÍ COLOCA TUS CREDENCIALES
    # Formato: (RUT, CLAVE)
    # El RUT puede estar con o sin puntos, se limpiarán automáticamente
    credenciales = [
            ("17357778-8","Lwj189482"),
("17659618-K","0196.sqd"),
("6268748-7","871h"),
("7052246-2","Riorahue2"),
("7052257-8","Algifol257"),
("76022072-8","Ele07276"),
("76024782-0","Gru78276"),
("76073162-5","Sae16276"),
("76073164-1","Fro16476"),
("76186388-6","Sag38876"),
("76389448-7","Tol44876"),
("76410374-2","Nor37476"),
("76429813-6","Ltc81376"),
("76440111-5","Cen11176"),
("76519747-3","Satt74776"),
("76870327-2","76870bfspa"),
("77122643-4","Sta64377"),
("77227557-9","Ges55777"),
("77227565-K","Inn56577"),
("77282311-8","eneltra18"),
("77312201-6","Sts20177"),
("77611649-1","Mtr64977"),
("77657831-2","Global77"),
("77679045-1","77679contw"),
("77708654-5","Sag65477"),
("77729726-0","sta72677"),
("78660990-9","9909algspa"),
("88272600-2","Ede60088"),
("96531500-4","Luz50096"),
("99528750-1","Gen75099"),
("77896991-2","Aurora1980")

    ]

    if not credenciales:
        print("⚠️  No hay credenciales definidas en el script.")
        print("\nPara usar este script:")
        print("1. Abre el archivo: scripts/insertar_credenciales_masivo.py")
        print("2. Busca la lista 'credenciales' en la función main()")
        print("3. Agrega tus credenciales en el formato:")
        print('   ("RUT", "CLAVE"),')
        print("\nEjemplo:")
        print('   credenciales = [')
        print('       ("76244083-0", "mi_clave_secreta"),')
        print('       ("76553200-0", "otra_clave"),')
        print('   ]')
        return

    print(f"📋 Se encontraron {len(credenciales)} credenciales para insertar.\n")

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
        print("⚠️  Hubo algunos errores durante el proceso.")
        print("   Revisa los mensajes anteriores para más detalles.")
    elif resultado['insertados'] > 0 or resultado['actualizados'] > 0:
        print(" Proceso completado exitosamente!")
    else:
        print("ℹ️  No se insertaron credenciales nuevas.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
