import os
import importlib.util
from werkzeug.middleware.proxy_fix import ProxyFix

# Carga explícita del archivo aplicacion.py (evita conflicto con el paquete aplicacion/)
BASE_DIR = os.path.dirname(__file__)
APLICACION_PY = os.path.join(BASE_DIR, 'aplicacion.py')

spec = importlib.util.spec_from_file_location('aplicacion_root', APLICACION_PY)
if spec is None or spec.loader is None:
    raise RuntimeError(f"No se pudo cargar el módulo desde {APLICACION_PY}")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Objeto WSGI para Waitress
app = module.app

# Middleware para manejar headers de proxy (IIS, Nginx, etc.)
# Esto permite obtener la IP real del cliente detrás de un reverse proxy
# x_for=1: Confía en el header X-Forwarded-For (número de proxies)
# x_proto=1: Confía en el header X-Forwarded-Proto (HTTP/HTTPS)
# x_host=1: Confía en el header X-Forwarded-Host
# x_prefix=1: Confía en el header X-Forwarded-Prefix
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
    x_prefix=1
)



