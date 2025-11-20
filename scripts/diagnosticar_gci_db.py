"""
Script de diagnóstico para verificar configuración de base de datos en GCI
===========================================================================

Uso:
    python scripts/diagnosticar_gci_db.py

Verifica:
- Qué base de datos está configurada en .env
- Si el script GCI lee variables de entorno correctamente
- Prueba sobrescribir DB_NAME vía variable de entorno
"""

import os
import sys
import subprocess
from pathlib import Path

def diagnosticar_config_actual():
    """Muestra la configuración actual de .env"""
    print("\n" + "="*60)
    print(" DIAGNÓSTICO: Configuración Actual")
    print("="*60 + "\n")

    # Leer .env del proyecto
    env_file = Path(__file__).parent.parent / '.env'

    if not env_file.exists():
        print(f"No se encontró archivo .env en: {env_file}")
        return

    print(f"✅ Archivo .env encontrado: {env_file}\n")

    # Buscar DB_NAME en .env
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('DB_NAME'):
                print(f"   {line.strip()}")

    print()


def diagnosticar_gci_config():
    """Verifica la configuración del script GCI"""
    print("\n" + "="*60)
    print(" DIAGNÓSTICO: Configuración de GCI")
    print("="*60 + "\n")

    # Rutas posibles del GCI
    rutas_gci = [
        r"C:\Users\Administrator\Desktop\Gestion-Consulta-Integral",
        r"c:\Users\mscha\Desktop\Gestion-Consulta-Integral",
    ]

    dir_gci = None
    for ruta in rutas_gci:
        if os.path.isdir(ruta):
            dir_gci = ruta
            break

    if not dir_gci:
        print("No se encontró el directorio de GCI")
        print(f"   Rutas buscadas: {rutas_gci}")
        return

    print(f"✅ GCI encontrado en: {dir_gci}\n")

    # Verificar .env del GCI
    env_gci = Path(dir_gci) / '.env'
    if env_gci.exists():
        print(f"✅ Archivo .env de GCI encontrado\n")
        print("   Configuración de base de datos:")
        with open(env_gci, 'r', encoding='utf-8') as f:
            for line in f:
                if 'DB_' in line and not line.strip().startswith('#'):
                    print(f"      {line.strip()}")
    else:
        print(f"⚠️  No se encontró .env en GCI: {env_gci}")

    print()

    # Buscar archivos de configuración
    config_files = [
        'config.py',
        'src/config.py',
        'src/database/config.py',
        'database/config.py'
    ]

    print(" Buscando archivos de configuración...\n")
    for config_file in config_files:
        config_path = Path(dir_gci) / config_file
        if config_path.exists():
            print(f"   ✅ Encontrado: {config_file}")

            # Leer y buscar DB_NAME
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'DB_NAME' in content:
                    print(f"      📝 Contiene configuración de DB_NAME")

                    # Buscar líneas relevantes
                    for line in content.split('\n'):
                        if 'DB_NAME' in line and not line.strip().startswith('#'):
                            print(f"         {line.strip()}")
        else:
            print(f"   No encontrado: {config_file}")

    print()


def test_variable_entorno():
    """Prueba sobrescribir DB_NAME vía variable de entorno"""
    print("\n" + "="*60)
    print("🧪 TEST: Sobrescribir DB_NAME vía Variable de Entorno")
    print("="*60 + "\n")

    # Crear script de prueba
    test_script = """
import os
from dotenv import load_dotenv

# Simular lo que hace el script GCI
load_dotenv()

db_name_env = os.getenv("DB_NAME")
print(f"DB_NAME desde variable de entorno: {db_name_env}")

# Si GCI lo hace correctamente, debería mostrar 'test_database'
"""

    test_file = Path(__file__).parent.parent / 'logs' / 'test_env.py'
    test_file.parent.mkdir(exist_ok=True)

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_script)

    print("1️⃣  Test SIN sobrescribir (debería mostrar 'stratex' del .env):")
    result1 = subprocess.run(
        [sys.executable, str(test_file)],
        capture_output=True,
        text=True
    )
    print(f"   {result1.stdout.strip()}\n")

    print("2️⃣  Test CON sobrescritura (debería mostrar 'test_database'):")
    env = dict(os.environ)
    env["DB_NAME"] = "test_database"
    result2 = subprocess.run(
        [sys.executable, str(test_file)],
        capture_output=True,
        text=True,
        env=env
    )
    print(f"   {result2.stdout.strip()}\n")

    # Limpiar
    test_file.unlink()

    if "test_database" in result2.stdout:
        print("✅ La variable de entorno se puede sobrescribir correctamente")
        print("✅ El script GCI DEBERÍA poder leer la base de datos dinámica")
    else:
        print("⚠️  La variable de entorno NO se sobrescribe correctamente")
        print("⚠️  Esto puede indicar un problema con python-dotenv")

    print()


def mostrar_recomendaciones():
    """Muestra recomendaciones finales"""
    print("\n" + "="*60)
    print("💡 RECOMENDACIONES")
    print("="*60 + "\n")

    print("1. Verificar que el script GCI use esta estructura:")
    print("""
   import os
   from dotenv import load_dotenv

   load_dotenv()

   DB_NAME = os.getenv("DB_NAME", "stratex")  # 👈 CRÍTICO
""")

    print("\n2. Agregar logging en GCI para confirmar la base de datos:")
    print("""
   import logging
   logging.info(f"🔧 Base de datos configurada: {DB_NAME}")
""")

    print("\n3. Probar guardando credenciales desde diferentes bases:")
    print("   - http://localhost:5000/stratex/empresas")
    print("   - http://localhost:5000/vicat/empresas (si existe)")

    print("\n4. Verificar en MySQL que los datos se guarden en la BD correcta:")
    print("""
   USE stratex;
   SELECT COUNT(*) FROM consulta_integral;

   USE vicat;
   SELECT COUNT(*) FROM consulta_integral;
""")

    print()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 DIAGNÓSTICO: Configuración Multi-Base de Datos GCI")
    print("="*60)

    diagnosticar_config_actual()
    diagnosticar_gci_config()
    test_variable_entorno()
    mostrar_recomendaciones()

    print("\n" + "="*60)
    print("✅ Diagnóstico completado")
    print("="*60 + "\n")

    print("📖 Para más información, consulta:")
    print("   documentacion/CONFIGURACION_GCI_MULTI_DB.md")
    print()
