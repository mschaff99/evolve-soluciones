"""
Servicio de integración con Gestion-Consulta-Integral (GCI)
===========================================================

Dispara en segundo plano (background) las opciones individuales 1 y 3 de
Gestion-Consulta-Integral para un RUT específico, utilizando la credencial SII
almacenada en este sistema (desencriptada mediante Fernet).

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

    Returns:
        Tuple[str, str]: (ruta_directorio_gci, ruta_main_py)
    """
    dir_gci = r"c:\\Users\\mscha\\Desktop\\Gestion-Consulta-Integral"
    ruta_main = os.path.join(dir_gci, "main.py")
    return dir_gci, ruta_main


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

    python_exe = obtener_python_actual()
    dir_gci, ruta_main = obtener_ruta_gci()

    # El script es interactivo, no acepta argumentos en línea de comandos
    cmd = [python_exe, ruta_main]

    with open(log_path, "w", encoding="utf-8") as logf:
        logf.write(f"[{ahora}] Ejecutando opcion {opcion} para {rut} en {base_datos}\n")
        logf.write(f"Logs dir: {logs_dir}\n")
        logf.write(f"Python: {python_exe}\n")
        logf.write(f"Directorio GCI: {dir_gci}\n")
        logf.write(f"Script: {ruta_main} (existe={os.path.isfile(ruta_main)})\n")
        logf.write(f"Comando: {python_exe} {os.path.basename(ruta_main)}\n")
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
            proceso = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=logf,
                stderr=logf,
                cwd=dir_gci,
                env=env,
                text=True,
                bufsize=1  # Line buffered
            )

            # Enviar respuestas al proceso interactivo:
            # 1. Primero esperar un poco para que muestre el menú
            time.sleep(1)
            # 2. Enviar la opción (1 o 3) seguida de Enter
            proceso.stdin.write(f"{opcion}\n")
            proceso.stdin.flush()
            logf.write(f"\n[Auto] Enviado: {opcion}\n")

            # 3. Esperar un poco antes de enviar el RUT
            time.sleep(1)
            # 4. Enviar el RUT cuando lo pida
            proceso.stdin.write(f"{rut}\n")
            proceso.stdin.flush()
            logf.write(f"[Auto] Enviado RUT: {rut}\n")

            # 5. Enviar la contraseña del SII si el script la solicita
            #    (se envía en todo caso; el script la ignorará si no la necesita)
            time.sleep(1)
            try:
                proceso.stdin.write("\n")  # asegurar línea si quedó input pendiente
                proceso.stdin.flush()
            except Exception:
                pass
            proceso.stdin.write("\n")  # salto de línea por si el prompt requiere enter previo
            proceso.stdin.flush()
            # Enviar password (no registrar en logs)
            proceso.stdin.write(f"{password}\n")
            proceso.stdin.flush()
            logf.write("[Auto] Enviada contraseña (oculta en log)\n")

            # 6. Dar tiempo a que el proceso arranque la tarea y vuelva al menú
            time.sleep(2)
            # 7. Enviar '5' para salir del menú y evitar EOF en el próximo input
            proceso.stdin.write("5\n")
            proceso.stdin.flush()
            logf.write("[Auto] Enviado: 5 (Salir)\n")

            # 8. Cerrar stdin para indicar fin de entradas
            proceso.stdin.close()

            # 9. Esperar a que termine el subproceso para ejecutar secuencialmente
            rc = proceso.wait()
            logf.write(f"[Auto] Proceso finalizado. returncode={rc}\n")

            print(f"GCI opcion {opcion} lanzada para {rut}. Log: {log_path}")
        except Exception as e:
            logf.write(f"ERROR: {e}\n")
            import traceback
            logf.write(traceback.format_exc())
            print(f"ERROR lanzando GCI opcion {opcion} para {rut}: {e}")


def ejecutar_automatico_opciones_1_y_3(rut: str, base_datos: str) -> bool:
    """Dispara en background las opciones 1 y 3 de GCI para un RUT de forma secuencial."""
    servicio_empresas = ServicioEmpresas(base_datos)
    password: Optional[str] = servicio_empresas.obtener_credencial_sii_desencriptada(rut)

    if not password:
        return False

    def _ejecutar_secuencial():
        try:
            print(f"Integración GCI: iniciando ejecución secuencial para {rut}")
            _ejecutar_gci_opcion(1, rut, password, base_datos)
            _ejecutar_gci_opcion(3, rut, password, base_datos)
            print(f"Integración GCI: ejecución secuencial finalizada para {rut}")
        except Exception as e:
            print(f"Integración GCI: error en ejecución secuencial para {rut}: {e}")

    hilo = threading.Thread(target=_ejecutar_secuencial, daemon=True)
    hilo.start()
    print(f"Integración GCI: hilo lanzado (secuencial 1→3) para {rut} | logs en ./logs")
    return True


