# Script de Verificación - Integración Módulo IA
# Ejecutar: python scripts/verificar_integracion_ia.py

import os
import sys

def verificar_archivo(ruta, descripcion):
    """Verifica que un archivo exista"""
    existe = os.path.exists(ruta)
    estado = "✅" if existe else "❌"
    print(f"{estado} {descripcion}: {ruta}")
    return existe

def verificar_directorio(ruta, descripcion):
    """Verifica que un directorio exista"""
    existe = os.path.isdir(ruta)
    estado = "✅" if existe else "❌"
    print(f"{estado} {descripcion}: {ruta}")
    return existe

def verificar_contenido_archivo(ruta, texto, descripcion):
    """Verifica que un archivo contenga cierto texto"""
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
            contiene = texto in contenido
            estado = "✅" if contiene else "❌"
            print(f"{estado} {descripcion}")
            return contiene
    except:
        print(f"Error leyendo {ruta}")
        return False

def main():
    print("=" * 70)
    print("VERIFICACIÓN DE INTEGRACIÓN - MÓDULO IA")
    print("=" * 70)
    print()

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resultados = []

    # Verificar directorios
    print("📁 VERIFICANDO DIRECTORIOS...")
    print("-" * 70)
    resultados.append(verificar_directorio(
        os.path.join(base_path, "aplicacion", "queries"),
        "Directorio queries"
    ))
    resultados.append(verificar_directorio(
        os.path.join(base_path, "aplicacion", "prompts"),
        "Directorio prompts"
    ))
    print()

    # Verificar servicios
    print("🔧 VERIFICANDO SERVICIOS...")
    print("-" * 70)
    resultados.append(verificar_archivo(
        os.path.join(base_path, "aplicacion", "servicios", "servicio_balance_ia.py"),
        "Servicio Balance IA"
    ))
    resultados.append(verificar_archivo(
        os.path.join(base_path, "aplicacion", "servicios", "servicio_gemini.py"),
        "Servicio Gemini"
    ))
    resultados.append(verificar_archivo(
        os.path.join(base_path, "aplicacion", "servicios", "servicio_ia_memoria.py"),
        "Servicio IA Memoria"
    ))
    print()

    # Verificar queries
    print("📊 VERIFICANDO QUERIES...")
    print("-" * 70)
    resultados.append(verificar_archivo(
        os.path.join(base_path, "aplicacion", "queries", "balance_queries.py"),
        "Balance Queries"
    ))
    resultados.append(verificar_archivo(
        os.path.join(base_path, "aplicacion", "queries", "proveedores_queries.py"),
        "Proveedores Queries"
    ))
    resultados.append(verificar_archivo(
        os.path.join(base_path, "aplicacion", "queries", "__init__.py"),
        "Queries __init__"
    ))
    print()

    # Verificar prompts
    print("💬 VERIFICANDO PROMPTS...")
    print("-" * 70)
    resultados.append(verificar_archivo(
        os.path.join(base_path, "aplicacion", "prompts", "balance_prompts.py"),
        "Balance Prompts"
    ))
    resultados.append(verificar_archivo(
        os.path.join(base_path, "aplicacion", "prompts", "proveedores_prompts.py"),
        "Proveedores Prompts"
    ))
    resultados.append(verificar_archivo(
        os.path.join(base_path, "aplicacion", "prompts", "__init__.py"),
        "Prompts __init__"
    ))
    print()

    # Verificar controlador
    print("🎮 VERIFICANDO CONTROLADOR...")
    print("-" * 70)
    resultados.append(verificar_archivo(
        os.path.join(base_path, "aplicacion", "controladores", "ia.py"),
        "Controlador IA"
    ))
    print()

    # Verificar template
    print("🎨 VERIFICANDO TEMPLATE...")
    print("-" * 70)
    resultados.append(verificar_archivo(
        os.path.join(base_path, "aplicacion", "plantillas", "ia_dashboard.html"),
        "Dashboard IA"
    ))
    print()

    # Verificar migración
    print("🗄️ VERIFICANDO MIGRACIÓN...")
    print("-" * 70)
    resultados.append(verificar_archivo(
        os.path.join(base_path, "migraciones", "007_modulo_ia_memoria.sql"),
        "Migración SQL"
    ))
    print()

    # Verificar documentación
    print("📚 VERIFICANDO DOCUMENTACIÓN...")
    print("-" * 70)
    resultados.append(verificar_archivo(
        os.path.join(base_path, "documentacion", "MODULO_IA.md"),
        "Documentación Módulo IA"
    ))
    resultados.append(verificar_archivo(
        os.path.join(base_path, "INTEGRACION_IA_RESUMEN.md"),
        "Resumen de Integración"
    ))
    print()

    # Verificar registro del blueprint
    print("🔗 VERIFICANDO REGISTRO DE BLUEPRINT...")
    print("-" * 70)
    resultados.append(verificar_contenido_archivo(
        os.path.join(base_path, "aplicacion.py"),
        "from aplicacion.controladores.ia import ia_bp",
        "Import del blueprint IA en aplicacion.py"
    ))
    resultados.append(verificar_contenido_archivo(
        os.path.join(base_path, "aplicacion.py"),
        "aplicacion.register_blueprint(ia_bp)",
        "Registro del blueprint IA en aplicacion.py"
    ))
    print()

    # Verificar dependencias
    print("📦 VERIFICANDO DEPENDENCIAS...")
    print("-" * 70)
    resultados.append(verificar_contenido_archivo(
        os.path.join(base_path, "requirements.txt"),
        "Flask-Compress",
        "Flask-Compress en requirements.txt"
    ))
    resultados.append(verificar_contenido_archivo(
        os.path.join(base_path, "requirements.txt"),
        "openpyxl",
        "openpyxl en requirements.txt"
    ))
    resultados.append(verificar_contenido_archivo(
        os.path.join(base_path, "requirements.txt"),
        "requests",
        "requests en requirements.txt"
    ))
    print()

    # Resumen final
    print("=" * 70)
    print("RESUMEN DE VERIFICACIÓN")
    print("=" * 70)
    total = len(resultados)
    exitosos = sum(resultados)
    fallidos = total - exitosos
    porcentaje = (exitosos / total * 100) if total > 0 else 0

    print(f"Total de verificaciones: {total}")
    print(f"✅ Exitosas: {exitosos}")
    print(f"Fallidas: {fallidos}")
    print(f"📊 Porcentaje de éxito: {porcentaje:.1f}%")
    print()

    if fallidos == 0:
        print("🎉 ¡INTEGRACIÓN COMPLETADA EXITOSAMENTE!")
        print()
        print("Próximos pasos:")
        print("1. Aplicar migración SQL: psql -U postgres -d evolve -f migraciones/007_modulo_ia_memoria.sql")
        print("2. Configurar GEMINI_API_KEY en archivo .env")
        print("3. Instalar dependencias: pip install -r requirements.txt")
        print("4. Iniciar aplicación: python aplicacion.py")
        print("5. Acceder a: http://localhost:5000/ia/dashboard")
        return 0
    else:
        print("⚠️ HAY ELEMENTOS FALTANTES O CON ERRORES")
        print()
        print("Revisa los elementos marcados con arriba.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
