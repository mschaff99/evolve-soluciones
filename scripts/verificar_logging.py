"""
Script de Verificación del Sistema de Logging Detallado

Verifica que todos los componentes del sistema de logging estén funcionando correctamente.
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verificar_archivos():
    """Verifica que todos los archivos necesarios existan"""
    print("=" * 80)
    print("1. VERIFICANDO ARCHIVOS")
    print("=" * 80)

    archivos_requeridos = [
        'aplicacion/utilidades/logging_detallado.py',
        'aplicacion/plantillas/paginas/ayuda_navegador.html',
        'documentacion/PROBLEMA_CHROME_COOKIES.md',
        'RESUMEN_IMPLEMENTACION.md'
    ]

    todos_ok = True
    for archivo in archivos_requeridos:
        ruta_completa = os.path.join(os.path.dirname(os.path.dirname(__file__)), archivo)
        existe = os.path.exists(ruta_completa)
        simbolo = "✅" if existe else "❌"
        print(f"{simbolo} {archivo}")
        if not existe:
            todos_ok = False

    return todos_ok


def verificar_imports():
    """Verifica que los imports funcionen correctamente"""
    print("\n" + "=" * 80)
    print("2. VERIFICANDO IMPORTS")
    print("=" * 80)

    imports_exitosos = []
    imports_fallidos = []

    # Test 1: logging_detallado
    try:
        from aplicacion.utilidades.logging_detallado import (
            configurar_logging_detallado,
            log_intento_login,
            log_error_csrf_detallado,
            detectar_problema_cookies_chrome,
            log_diagnostico_cookies
        )
        imports_exitosos.append("logging_detallado (5 funciones)")
        print("✅ aplicacion.utilidades.logging_detallado")
    except Exception as e:
        imports_fallidos.append(f"logging_detallado: {e}")
        print(f"aplicacion.utilidades.logging_detallado: {e}")

    # Test 2: aplicacion principal
    try:
        # Importar el módulo raíz aplicacion.py (no el paquete aplicacion/)
        import importlib.util

        app_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "aplicacion.py")
        spec = importlib.util.spec_from_file_location("aplicacion_main", app_path)

        if spec is None or spec.loader is None:
            raise ImportError("No se pudo cargar el módulo aplicacion.py")

        aplicacion_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(aplicacion_main)

        app = aplicacion_main.crear_aplicacion('desarrollo')
        imports_exitosos.append("aplicacion.crear_aplicacion")
        print("✅ aplicacion.crear_aplicacion")

        # Verificar que el logging fue configurado
        if os.path.exists('logs'):
            print("✅ Carpeta logs/ creada")
        else:
            print("⚠️  Carpeta logs/ no creada aún (se creará al ejecutar la app)")
    except Exception as e:
        imports_fallidos.append(f"aplicacion: {e}")
        print(f"aplicacion.crear_aplicacion: {e}")

    return len(imports_fallidos) == 0


def verificar_funciones():
    """Verifica que las funciones clave funcionen"""
    print("\n" + "=" * 80)
    print("3. VERIFICANDO FUNCIONES")
    print("=" * 80)

    try:
        from aplicacion.utilidades.logging_detallado import detectar_problema_cookies_chrome
        from flask import Flask
        from flask.testing import FlaskClient

        # Crear app de prueba
        app = Flask(__name__)
        app.config['TESTING'] = True

        with app.test_request_context(
            '/',
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) Chrome/118.0.0.0'}
        ):
            resultado = detectar_problema_cookies_chrome()
            print(f"✅ detectar_problema_cookies_chrome() ejecutada")
            print(f"   - Problema detectado: {resultado['problema_detectado']}")
            print(f"   - Es Chrome: {resultado['es_chrome']}")
            print(f"   - Navegador: {resultado['navegador']}")

        return True
    except Exception as e:
        print(f"Error en verificación de funciones: {e}")
        return False


def verificar_rutas():
    """Verifica que las rutas estén registradas"""
    print("\n" + "=" * 80)
    print("4. VERIFICANDO RUTAS")
    print("=" * 80)

    try:
        # Importar el módulo raíz aplicacion.py (no el paquete aplicacion/)
        import sys
        import importlib.util

        # Cargar aplicacion.py directamente
        app_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "aplicacion.py")
        spec = importlib.util.spec_from_file_location("aplicacion_main", app_path)

        if spec is None or spec.loader is None:
            raise ImportError("No se pudo cargar el módulo aplicacion.py")

        aplicacion_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(aplicacion_main)

        app = aplicacion_main.crear_aplicacion('desarrollo')

        rutas_esperadas = [
            '/auth/iniciar-sesion',
            '/auth/cerrar-sesion',
            '/auth/limpiar-sesion',
            '/auth/ayuda-navegador'
        ]

        # Obtener todas las rutas registradas
        rutas_registradas = [rule.rule for rule in app.url_map.iter_rules()]

        todas_ok = True
        for ruta in rutas_esperadas:
            existe = ruta in rutas_registradas
            simbolo = "✅" if existe else "❌"
            print(f"{simbolo} {ruta}")
            if not existe:
                todas_ok = False

        return todas_ok
    except Exception as e:
        print(f"Error verificando rutas: {e}")
        return False


def verificar_templates():
    """Verifica que los templates existan"""
    print("\n" + "=" * 80)
    print("5. VERIFICANDO TEMPLATES")
    print("=" * 80)

    templates_requeridos = [
        'aplicacion/plantillas/paginas/ayuda_navegador.html',
        'aplicacion/plantillas/paginas/iniciar_sesion.html'
    ]

    todas_ok = True
    for template in templates_requeridos:
        ruta_completa = os.path.join(os.path.dirname(os.path.dirname(__file__)), template)
        existe = os.path.exists(ruta_completa)
        simbolo = "✅" if existe else "❌"
        print(f"{simbolo} {template}")
        if not existe:
            todas_ok = False

    return todas_ok


def main():
    """Función principal"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "VERIFICACIÓN DEL SISTEMA DE LOGGING DETALLADO" + " " * 18 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    resultados = {
        'archivos': verificar_archivos(),
        'imports': verificar_imports(),
        'funciones': verificar_funciones(),
        'rutas': verificar_rutas(),
        'templates': verificar_templates()
    }

    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN FINAL")
    print("=" * 80)

    total_checks = len(resultados)
    checks_exitosos = sum(1 for v in resultados.values() if v)

    for nombre, resultado in resultados.items():
        simbolo = "✅" if resultado else "❌"
        print(f"{simbolo} {nombre.capitalize()}: {'OK' if resultado else 'FALLÓ'}")

    print(f"\nTotal: {checks_exitosos}/{total_checks} verificaciones exitosas")

    if all(resultados.values()):
        print("\n🎉 ¡TODAS LAS VERIFICACIONES PASARON!")
        print("\n📋 Próximos pasos:")
        print("   1. Ejecutar: python aplicacion.py")
        print("   2. Abrir navegador: http://localhost:5000/auth/iniciar-sesion")
        print("   3. Verificar: http://localhost:5000/auth/ayuda-navegador")
        print("   4. Monitorear logs: Get-Content logs\\autenticacion.log -Wait")
        return 0
    else:
        print("\n⚠️  ALGUNAS VERIFICACIONES FALLARON")
        print("Por favor revisa los errores arriba y corrige antes de ejecutar.")
        return 1


if __name__ == '__main__':
    exit(main())
