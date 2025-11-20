#!/usr/bin/env python3
"""
Script SIMPLE para insertar/actualizar UNA credencial con encriptación reversible
==================================================================================
PARA EL PROYECTO: evolve-soluciones

Modo interactivo que solicita RUT y contraseña, la encripta con Fernet
y la guarda en la base de datos usando ServicioEmpresas.

 Encriptación reversible (Fernet/AES) - Compatible con automatización
 Verifica la credencial después de guardarla
 Muestra si se insertó o actualizó

Uso:
    python scripts/insertar_credencial_simple.py
    python scripts/insertar_credencial_simple.py --rut 77235170-4 --password miPassword123
    python scripts/insertar_credencial_simple.py --base-datos evolve
"""

import sys
import os
import argparse
import getpass

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aplicacion.servicios.servicio_empresas import ServicioEmpresas


def insertar_credencial_interactiva(base_datos: str = 'stratex'):
    """Modo interactivo para insertar una credencial"""
    print()
    print("=" * 80)
    print("🔐 INSERTAR CREDENCIAL SII - Modo Interactivo")
    print("=" * 80)
    print(f"🗄️  Base de datos: {base_datos}")
    print()

    # Solicitar RUT
    rut = input("📋 Ingrese el RUT (formato: XX.XXX.XXX-X o XXXXXXXX-X): ").strip()
    if not rut:
        print("RUT requerido")
        return False

    print()

    # Inicializar servicio
    try:
        servicio = ServicioEmpresas(base_datos=base_datos)
        print(f" Conectado a base de datos: {base_datos}")
    except Exception as e:
        print(f"Error conectando a base de datos: {e}")
        return False

    print()

    # Verificar si ya existe
    try:
        credencial_existente = servicio.verificar_credencial_existe(rut)
        if credencial_existente:
            print(f"⚠️  Ya existe una credencial para {rut}")
            print(f"   📅 Fecha creación: {credencial_existente.get('fecha_creacion', 'N/A')}")
            print(f"   📅 Última actualización: {credencial_existente.get('fecha_actualizacion', 'N/A')}")
            print()

            respuesta = input("¿Deseas ACTUALIZAR la contraseña? (s/n): ").strip().lower()
            if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
                print("Operación cancelada")
                return False
            print()
    except Exception as e:
        # Si no existe el método, continuar sin verificar
        pass

    # Solicitar contraseña
    password = getpass.getpass("🔑 Ingrese la contraseña del SII: ").strip()
    if not password:
        print("Contraseña requerida")
        return False

    password2 = getpass.getpass("🔑 Confirme la contraseña: ").strip()
    if password != password2:
        print("Las contraseñas no coinciden")
        return False

    print()
    print(f"💾 Guardando credencial para {rut} con encriptación reversible (Fernet)...")

    # Guardar con encriptación reversible
    try:
        if servicio.guardar_credencial_sii(rut, password):
            print(" Credencial guardada exitosamente")
            print()

            # Verificar que se puede desencriptar
            print(" Verificando que se puede desencriptar...")
            password_recuperada = servicio.obtener_credencial_sii_desencriptada(rut)

            if password_recuperada:
                if password_recuperada == password:
                    print(" Verificación exitosa - La contraseña se puede recuperar correctamente")
                    print()
                    print("=" * 80)
                    print("🎉 ¡TODO LISTO!")
                    print("=" * 80)
                    print(f" El RUT {rut} ahora tiene login 100% automático")
                    print(f" La contraseña está encriptada con Fernet (reversible)")
                    print(f" Los scripts pueden leer la contraseña automáticamente")
                    print("=" * 80)
                    return True
                else:
                    print("⚠️  ADVERTENCIA: La contraseña recuperada NO coincide")
                    print(f"   Original: {password[:3]}{'*' * max(0, len(password) - 3)}")
                    print(f"   Recuperada: {password_recuperada[:3]}{'*' * max(0, len(password_recuperada) - 3)}")
                    return False
            else:
                print("⚠️  ADVERTENCIA: No se pudo recuperar la contraseña")
                print("💡 Posible causa: La contraseña está con bcrypt (no reversible)")
                return False
        else:
            print("Error guardando credencial")
            return False

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def insertar_credencial_argumentos(rut: str, password: str, base_datos: str = 'stratex'):
    """Insertar credencial desde argumentos de línea de comandos"""
    print()
    print("=" * 80)
    print("🔐 INSERTAR CREDENCIAL SII")
    print("=" * 80)
    print(f"🗄️  Base de datos: {base_datos}")
    print(f"📋 RUT: {rut}")
    print(f"🔑 Password: {'*' * len(password)}")
    print()

    try:
        servicio = ServicioEmpresas(base_datos=base_datos)
        print(f" Conectado a base de datos: {base_datos}")
    except Exception as e:
        print(f"Error conectando a base de datos: {e}")
        return False

    print()

    # Verificar si ya existe
    try:
        credencial_existente = servicio.verificar_credencial_existe(rut)
        if credencial_existente:
            print(f"⚠️  Ya existe credencial para {rut} - Se actualizará")
            print()
    except:
        pass

    print(f"💾 Guardando credencial...")

    try:
        if servicio.guardar_credencial_sii(rut, password):
            print(" Credencial guardada exitosamente")
            print()

            # Verificar
            print(" Verificando...")
            password_recuperada = servicio.obtener_credencial_sii_desencriptada(rut)

            if password_recuperada and password_recuperada == password:
                print(" Verificación exitosa")
                print()
                print("=" * 80)
                print("🎉 ¡TODO LISTO!")
                print("=" * 80)
                return True
            else:
                print("⚠️  Verificación falló")
                return False
        else:
            print("Error guardando credencial")
            return False

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Insertar una credencial SII con encriptación reversible (Fernet)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s                                      # Modo interactivo
  %(prog)s --rut 77235170-4 --password abc123   # Desde argumentos
  %(prog)s --base-datos evolve                  # Usar BD evolve
        """
    )

    parser.add_argument(
        '--rut', '-r',
        type=str,
        help='RUT de la empresa'
    )
    parser.add_argument(
        '--password', '-p',
        type=str,
        help='Contraseña del SII (⚠️  visible en historial de comandos)'
    )
    parser.add_argument(
        '--base-datos', '-b',
        type=str,
        default='stratex',
        help='Base de datos MySQL a usar (default: stratex)'
    )

    args = parser.parse_args()

    # Si hay argumentos, usarlos
    if args.rut and args.password:
        return 0 if insertar_credencial_argumentos(args.rut, args.password, args.base_datos) else 1

    # Si falta alguno, ir a modo interactivo
    if args.rut or args.password:
        print("⚠️  Si usas --rut también necesitas --password (o viceversa)")
        print("💡 Ejecuta sin argumentos para modo interactivo")
        return 1

    # Modo interactivo
    return 0 if insertar_credencial_interactiva(args.base_datos) else 1


if __name__ == '__main__':
    sys.exit(main())
