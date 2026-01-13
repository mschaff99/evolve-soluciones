"""
API REST v1
===========
Controladores de API REST para el frontend React
"""
from flask import Blueprint

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Importar controladores para registrar rutas
from aplicacion.controladores.api import autenticacion, empresas, f29
