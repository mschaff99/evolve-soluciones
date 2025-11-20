"""
Queries SQL especializadas para el sistema Evolve Soluciones
Contiene consultas optimizadas para diferentes módulos del sistema
"""

from aplicacion.queries.balance_queries import balance_queries, BalanceQueries
from aplicacion.queries.proveedores_queries import proveedores_queries, ProveedoresQueries

__all__ = [
    'balance_queries',
    'BalanceQueries',
    'proveedores_queries',
    'ProveedoresQueries',
]
