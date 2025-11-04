"""
Servicio de integración con Gestion-Consulta-Integral (GCI)
===========================================================

Dispara en segundo plano (background) la opción 5 (Salir)
de Gestion-Consulta-Integral para un RUT específico.

Seguridad:
- Nunca se escribe la contraseña en los logs.
- Se valida disponibilidad de contraseña antes de ejecutar.
"""

import os
import sys
import time
import threading
import subprocess
from datetime import datetime
from typing import Optional, Tuple

from aplicacion.servicios.servicio_empresas import ServicioEmpresas


def obtener_python_actual() -> str:
    """Devuelve el ejecutable de Python del proceso actual (mejor que adivinar venv).

    Returns:
        str: Ruta absoluta del ejecutable de Python en uso.
    """
    return sys.executable or "python"


def obtener_ruta_gci() -> Tuple[str, str]:
    """Obtiene la ruta del directorio y del main.py del proyecto GCI.

    Busca en múltiples ubicaciones posibles:
    1. C:\\Users\\Administrator\\Desktop\\Gestion-Consulta-Integral (prioritario)
    2. c:\\Users\\mscha\\Desktop\\Gestion-Consulta-Integral (fallback)
    3. Variable de entorno GCI_PATH si está definida

    Returns:
        Tuple[str, str]: (ruta_directorio_gci, ruta_main_py)

    Raises:
        FileNotFoundError: Si no encuentra el directorio GCI en ninguna ruta.
    """
    # Rutas posibles en orden de prioridad
    rutas_posibles = [
        r"C:\Users\Administrator\Desktop\Gestion-Consulta-Integral",
        r"c:\Users\mscha\Desktop\Gestion-Consulta-Integral",
        os.environ.get("GCI_PATH", ""),  # Variable de entorno como fallback
    ]

    # Filtrar rutas vacías
    rutas_posibles = [r for r in rutas_posibles if r]

    # Buscar la primera ruta que exista
    for dir_gci in rutas_posibles:
        if os.path.isdir(dir_gci):
            ruta_main = os.path.join(dir_gci, "main.py")
            if os.path.isfile(ruta_main):
                print(f"DEBUG: GCI encontrado en: {dir_gci}")
                return dir_gci, ruta_main

    # Si no encuentra en ninguna ruta, mostrar error informativo
    print(f"ERROR: No se encontró Gestion-Consulta-Integral en ninguna de estas rutas:")
    for ruta in rutas_posibles:
        print(f"  - {ruta}")
    print(f"Considera definir la variable de entorno GCI_PATH con la ruta correcta.")

    raise FileNotFoundError(
        f"No se encontró el directorio GCI. Rutas buscadas: {', '.join(rutas_posibles)}"
    )


def obtener_python_gci(dir_gci: str) -> str:
    """Obtiene el ejecutable de Python del entorno virtual de GCI.

    Args:
        dir_gci: Ruta del directorio GCI

    Returns:
        str: Ruta del python.exe del venv de GCI o python por defecto
    """
    # Posibles ubicaciones del venv en GCI
    venv_paths = [
        os.path.join(dir_gci, ".venv", "Scripts", "python.exe"),
        os.path.join(dir_gci, "venv", "Scripts", "python.exe"),
        os.path.join(dir_gci, ".venv", "bin", "python"),
        os.path.join(dir_gci, "venv", "bin", "python"),
    ]

    # Usar el primer venv que exista
    for venv_python in venv_paths:
        if os.path.isfile(venv_python):
            print(f"DEBUG: Usando Python de GCI: {venv_python}")
            return venv_python

    # Fallback: usar python del sistema
    print(f"WARNING: No se encontró venv de GCI, usando python del sistema")
    return "python"


def _ejecutar_gci_opcion(opcion: int, rut: str, password: str, base_datos: str) -> None:
    """Ejecuta una opción de GCI en un subproceso interactivo y guarda logs en archivo.

    El script main.py es interactivo: muestra menú, espera opción, luego pide RUT.
    Este método automatiza la interacción enviando las respuestas necesarias.

    Args:
        opcion: Número de opción de GCI (1 o 3).
        rut: RUT a procesar.
        password: Contraseña SII en texto plano (no se usa directamente aquí, el script la obtiene).
        base_datos: Nombre de la base de datos actual (contexto).
    """
    ahora = datetime.now().strftime("%Y%m%d-%H%M%S")
    logs_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, f"gci_opcion{opcion}_{rut}_{ahora}.log")

    dir_gci, ruta_main = obtener_ruta_gci()
    python_gci = obtener_python_gci(dir_gci)

    # El script es interactivo, no acepta argumentos en línea de comandos
    cmd = [python_gci, ruta_main]

    with open(log_path, "w", encoding="utf-8") as logf:
        logf.write(f"[{ahora}] Ejecutando opcion {opcion} para {rut} en {base_datos}\n")
        logf.write(f"Logs dir: {logs_dir}\n")
        logf.write(f"Python GCI: {python_gci}\n")
        logf.write(f"Directorio GCI: {dir_gci}\n")
        logf.write(f"Script: {ruta_main} (existe={os.path.isfile(ruta_main)})\n")
        logf.write(f"Comando: {python_gci} {os.path.basename(ruta_main)}\n")
        logf.write(f"Interacción automática: opción={opcion}, rut={rut}\n\n")
        try:
            if not os.path.isdir(dir_gci):
                logf.write("ERROR: Directorio GCI no existe.\n")
                print("ERROR: Directorio GCI no existe.")
                return
            if not os.path.isfile(ruta_main):
                logf.write("ERROR: main.py de GCI no existe en la ruta indicada.\n")
                print("ERROR: main.py de GCI no existe en la ruta indicada.")
                return

            # Forzar UTF-8 en el proceso hijo
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"

            # Ejecutar con stdin para enviar respuestas interactivas
            try:
                proceso = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=logf,
                    stderr=subprocess.STDOUT,
                    cwd=dir_gci,
                    env=env,
                    text=True,
                    bufsize=1  # Line buffered
                )
                logf.write("[GCI] Proceso iniciado correctamente\n")
            except Exception as e_popen:
                logf.write(f"ERROR al iniciar proceso GCI: {e_popen}\n")
                print(f"ERROR al iniciar GCI: {e_popen}")
                return

            # Enviar respuestas al proceso interactivo
            try:
                # 1. Esperar a que muestre el menú
                time.sleep(1)
                logf.write("[Auto] Enviando opción...\n")

                # 2. Enviar la opción (1 o 3) seguida de Enter
                proceso.stdin.write(f"{opcion}\n")
                proceso.stdin.flush()
                logf.write(f"[Auto] Enviado: {opcion}\n")

                # 3. Esperar antes de enviar el RUT
                time.sleep(1)
                logf.write("[Auto] Enviando RUT...\n")

                # 4. Enviar el RUT
                proceso.stdin.write(f"{rut}\n")
                proceso.stdin.flush()
                logf.write(f"[Auto] Enviado RUT: {rut}\n")

                # 5. Esperar antes de enviar contraseña
                time.sleep(1)
                logf.write("[Auto] Enviando contraseña...\n")

                # Enviar password (no registrar en logs)
                proceso.stdin.write(f"{password}\n")
                proceso.stdin.flush()
                logf.write("[Auto] Enviada contraseña (oculta en log)\n")

                # 6. Dar tiempo a que el proceso arranque la tarea
                time.sleep(2)
                logf.write("[Auto] Enviando salida...\n")

                # 7. Enviar '5' para salir del menú
                proceso.stdin.write("5\n")
                proceso.stdin.flush()
                logf.write("[Auto] Enviado: 5 (Salir)\n")

            except BrokenPipeError as e_pipe:
                logf.write(f"ERROR: Proceso GCI terminó inesperadamente: {e_pipe}\n")
                print(f"GCI terminó inesperadamente: {e_pipe}")
            except OSError as e_os:
                logf.write(f"ERROR: Problema de comunicación con GCI: {e_os}\n")
                print(f"Error de I/O con GCI: {e_os}")
            except Exception as e_stdin:
                logf.write(f"ERROR: Error escribiendo en stdin: {e_stdin}\n")
                print(f"Error comunicando con GCI: {e_stdin}")
            finally:
                # Cerrar stdin para indicar fin de entradas
                try:
                    if proceso.stdin and not proceso.stdin.closed:
                        proceso.stdin.close()
                except Exception:
                    pass

            # 8. Esperar a que termine el subproceso
            try:
                rc = proceso.wait(timeout=600)  # 10 minutos para procesos pesados (F29 + DJ)
                logf.write(f"[Auto] Proceso finalizado. returncode={rc}\n")
                print(f"GCI opcion {opcion} lanzada para {rut}. Log: {log_path}")
            except subprocess.TimeoutExpired:
                logf.write("WARNING: Proceso GCI tardó más de 10 minutos, finalizando...\n")
                proceso.kill()
                print(f"WARNING: GCI tardó demasiado para {rut}")

        except FileNotFoundError as e_notfound:
            logf.write(f"ERROR: {e_notfound}\n")
            print(f"ERROR: GCI no disponible: {e_notfound}")
        except Exception as e:
            logf.write(f"ERROR: {e}\n")
            import traceback
            logf.write(traceback.format_exc())
            print(f"ERROR lanzando GCI opcion {opcion} para {rut}: {e}")


def ejecutar_automatico_opciones_1_y_3(rut: str, base_datos: str) -> bool:
    """Dispara en background la opción 5 (Salir) de GCI para un RUT."""
    servicio_empresas = ServicioEmpresas(base_datos)
    password: Optional[str] = servicio_empresas.obtener_credencial_sii_desencriptada(rut)

    if not password:
        return False

    def _ejecutar_opcion_5():
        try:
            print(f"Integración GCI: iniciando ejecución de opción 5 (Salir) para {rut}")
            _ejecutar_gci_opcion(5, rut, password, base_datos)
            print(f"Integración GCI: ejecución de opción 5 finalizada para {rut}")
        except Exception as e:
            print(f"Integración GCI: error en ejecución de opción 5 para {rut}: {e}")

    hilo = threading.Thread(target=_ejecutar_opcion_5, daemon=True)
    hilo.start()
    print(f"Integración GCI: hilo lanzado (opción 5 - Salir) para {rut} | logs en ./logs")
    return True


