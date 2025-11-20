"""
Prompts especializados para análisis con IA
Contiene templates de prompts para diferentes tipos de análisis contables
"""

from aplicacion.prompts.balance_prompts import balance_prompts, BalancePrompts
from aplicacion.prompts.proveedores_prompts import proveedores_prompts, ProveedoresPrompts

__all__ = [
    'balance_prompts',
    'BalancePrompts',
    'proveedores_prompts',
    'ProveedoresPrompts',
]
