#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Instalador de Playwright para GCI
==================================
Ejecutar como Administrator
Instala los navegadores de Playwright en el contexto del usuario actual
"""

import os
import sys
import subprocess
from pathlib import Path


def encontrar_gci():
    """Encuentra el directorio de GCI"""
    rutas_posibles = [
        Path(r"C:\Users\Administrator\Desktop\Gestion-Consulta-Integral"),
        Path(r"c:\Users\mscha\Desktop\Gestion-Consulta-Integral"),
    ]

    # Si está definida GCI_PATH, agregarla
    if "GCI_PATH" in os.environ:
        rutas_posibles.insert(0, Path(os.environ["GCI_PATH"]))

    for ruta in rutas_posibles:
        if ruta.is_dir():
            print(f" GCI encontrado en: {ruta}")
            return ruta

    print("ERROR: No se encontró GCI en ninguna ruta:")
    for ruta in rutas_posibles:
        print(f"   - {ruta}")
    print("\nDefine la variable de entorno GCI_PATH si está en otra ubicación")
    sys.exit(1)


def encontrar_python_gci(dir_gci):
    """Encuentra el ejecutable de Python de GCI"""
    venv_paths = [
        dir_gci / ".venv" / "Scripts" / "python.exe",
        dir_gci / "venv" / "Scripts" / "python.exe",
    ]

    for venv_py in venv_paths:
        if venv_py.is_file():
            print(f" Python de GCI encontrado: {venv_py}")
            return str(venv_py)

    print("ERROR: No se encontró venv de GCI en:")
    for venv_py in venv_paths:
        print(f"   - {venv_py}")
    print("\nAsegúrate de que GCI tiene un entorno virtual activado")
    sys.exit(1)


def main():
    print("=" * 50)
    print("Instalador de Playwright para GCI")
    print("=" * 50)
    print()

    # Encontrar GCI
    dir_gci = encontrar_gci()

    # Encontrar Python de GCI
    python_gci = encontrar_python_gci(dir_gci)

    print()
    print("🚀 Instalando Playwright...")
    print(f"Directorio de trabajo: {dir_gci}")
    print(f"Python a usar: {python_gci}")
    print()

    # Cambiar al directorio de GCI
    os.chdir(dir_gci)

    try:
        # Ejecutar playwright install
        print("⏳ Descargando navegadores (puede tomar varios minutos)...")
        result = subprocess.run(
            [python_gci, "-m", "playwright", "install"],
            check=False
        )

        if result.returncode == 0:
            print()
            print(" Playwright instalado exitosamente")
            print()
            print("Instalando dependencias del sistema...")
            subprocess.run(
                [python_gci, "-m", "playwright", "install-deps"],
                check=False
            )
            print()
            print("=" * 50)
            print(" Instalación completada")
            print("=" * 50)
            return 0
        else:
            print()
            print(f"Error durante la instalación de Playwright")
            print(f"Exit code: {result.returncode}")
            return 1

    except Exception as e:
        print(f"Excepción: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
