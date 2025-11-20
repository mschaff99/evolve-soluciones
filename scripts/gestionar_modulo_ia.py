#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para gestionar permisos del Módulo IA
Permite habilitar/deshabilitar el módulo IA para bases de datos específicas
"""

import sys
from aplicacion import crear_aplicacion
from aplicacion.modelos.modulo import Modulo, GestorModulos

def listar_bases_datos_con_ia():
    """Lista todas las bases de datos que tienen el módulo IA habilitado"""
    app = crear_aplicacion()

    with app.app_context():
        print("=" * 60)
        print("BASES DE DATOS CON MÓDULO IA HABILITADO")
        print("=" * 60)

        try:
            # Consulta directa a la vista
            from aplicacion.modelos.base_datos import ejecutar_consulta_postgres

            consulta = """
                SELECT
                    bd.nombre_base_datos,
                    bd.nombre_cliente,
                    bd.plan,
                    bd.estado,
                    mh.habilitado,
                    mh.fecha_habilitacion::DATE as fecha_habilitacion
                FROM auth.bases_datos_mysql bd
                LEFT JOIN auth.modulos_habilitados_bd mh ON bd.id = mh.id_base_datos
                LEFT JOIN auth.modulos_sistema m ON mh.id_modulo = m.id AND m.codigo = 'ia'
                WHERE bd.activo = TRUE
                ORDER BY bd.nombre_base_datos
            """

            resultados = ejecutar_consulta_postgres(consulta)

            if not resultados:
                print("\nNo hay bases de datos registradas.")
                return

            for row in resultados:
                estado_ia = " HABILITADO" if row['habilitado'] else "❌ NO HABILITADO"
                print(f"\n📊 {row['nombre_base_datos']}")
                print(f"   Cliente: {row['nombre_cliente']}")
                print(f"   Plan: {row['plan'] or 'N/A'}")
                print(f"   Estado BD: {row['estado']}")
                print(f"   Módulo IA: {estado_ia}")
                if row['habilitado'] and row['fecha_habilitacion']:
                    print(f"   Fecha habilitación: {row['fecha_habilitacion']}")

            print("\n" + "=" * 60)

        except Exception as e:
            print(f"❌ Error al consultar bases de datos: {e}")
            import traceback
            traceback.print_exc()


def habilitar_ia_para_bd(nombre_bd):
    """Habilita el módulo IA para una base de datos específica"""
    app = crear_aplicacion()

    with app.app_context():
        try:
            print(f"\n🔧 Habilitando módulo IA para: {nombre_bd}")

            resultado = GestorModulos.habilitar_modulo(
                nombre_base_datos=nombre_bd,
                codigo_modulo='ia',
                usuario='admin_script'
            )

            if resultado['success']:
                print(f" {resultado['mensaje']}")

                # Verificar
                tiene_ia = Modulo.verificar_modulo_habilitado(nombre_bd, 'ia')
                if tiene_ia:
                    print(f" Verificado: La BD '{nombre_bd}' ahora tiene acceso al módulo IA")
                else:
                    print(f"⚠️ Advertencia: La habilitación no se pudo verificar")
            else:
                print(f"❌ Error: {resultado.get('mensaje', 'Error desconocido')}")

        except Exception as e:
            print(f"❌ Error al habilitar módulo IA: {e}")
            import traceback
            traceback.print_exc()


def deshabilitar_ia_para_bd(nombre_bd):
    """Deshabilita el módulo IA para una base de datos específica"""
    app = crear_aplicacion()

    with app.app_context():
        try:
            print(f"\n🔧 Deshabilitando módulo IA para: {nombre_bd}")

            resultado = GestorModulos.deshabilitar_modulo(
                nombre_base_datos=nombre_bd,
                codigo_modulo='ia'
            )

            if resultado['success']:
                print(f" {resultado['mensaje']}")

                # Verificar
                tiene_ia = Modulo.verificar_modulo_habilitado(nombre_bd, 'ia')
                if not tiene_ia:
                    print(f" Verificado: La BD '{nombre_bd}' ya no tiene acceso al módulo IA")
                else:
                    print(f"⚠️ Advertencia: La deshabilitación no se pudo verificar")
            else:
                print(f"❌ Error: {resultado.get('mensaje', 'Error desconocido')}")

        except Exception as e:
            print(f"❌ Error al deshabilitar módulo IA: {e}")
            import traceback
            traceback.print_exc()


def mostrar_ayuda():
    """Muestra la ayuda del script"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║          GESTIÓN DE PERMISOS - MÓDULO IA                     ║
╚══════════════════════════════════════════════════════════════╝

USO:
    python scripts/gestionar_modulo_ia.py [comando] [argumentos]

COMANDOS:

    listar
        Lista todas las bases de datos y su estado del módulo IA
        Ejemplo: python scripts/gestionar_modulo_ia.py listar

    habilitar <nombre_bd>
        Habilita el módulo IA para una base de datos específica
        Ejemplo: python scripts/gestionar_modulo_ia.py habilitar evolve

    deshabilitar <nombre_bd>
        Deshabilita el módulo IA para una base de datos específica
        Ejemplo: python scripts/gestionar_modulo_ia.py deshabilitar evolve

    ayuda
        Muestra esta ayuda

EJEMPLOS:

    # Ver qué bases de datos tienen IA
    python scripts/gestionar_modulo_ia.py listar

    # Habilitar IA para una empresa
    python scripts/gestionar_modulo_ia.py habilitar mi_empresa

    # Deshabilitar IA
    python scripts/gestionar_modulo_ia.py deshabilitar mi_empresa

NOTAS:
    - Requiere que la migración 008_habilitar_modulo_ia.sql esté ejecutada
    - Solo administradores deberían ejecutar este script
    - Los cambios son inmediatos (no requiere reiniciar la app)

""")


def main():
    """Función principal del script"""
    if len(sys.argv) < 2:
        mostrar_ayuda()
        sys.exit(1)

    comando = sys.argv[1].lower()

    if comando == 'listar':
        listar_bases_datos_con_ia()

    elif comando == 'habilitar':
        if len(sys.argv) < 3:
            print("❌ Error: Debes especificar el nombre de la base de datos")
            print("Uso: python scripts/gestionar_modulo_ia.py habilitar <nombre_bd>")
            sys.exit(1)
        nombre_bd = sys.argv[2]
        habilitar_ia_para_bd(nombre_bd)

    elif comando == 'deshabilitar':
        if len(sys.argv) < 3:
            print("❌ Error: Debes especificar el nombre de la base de datos")
            print("Uso: python scripts/gestionar_modulo_ia.py deshabilitar <nombre_bd>")
            sys.exit(1)
        nombre_bd = sys.argv[2]
        deshabilitar_ia_para_bd(nombre_bd)

    elif comando in ['ayuda', 'help', '-h', '--help']:
        mostrar_ayuda()

    else:
        print(f"❌ Comando desconocido: {comando}")
        print("\nComandos válidos: listar, habilitar, deshabilitar, ayuda")
        mostrar_ayuda()
        sys.exit(1)


if __name__ == '__main__':
    main()
