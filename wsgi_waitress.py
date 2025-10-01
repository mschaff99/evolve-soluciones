import os
import importlib.util

# Carga explícita del archivo aplicacion.py (evita conflicto con el paquete aplicacion/)
BASE_DIR = os.path.dirname(__file__)
APLICACION_PY = os.path.join(BASE_DIR, 'aplicacion.py')

spec = importlib.util.spec_from_file_location('aplicacion_root', APLICACION_PY)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(module)

# Objeto WSGI para Waitress
app = module.app


