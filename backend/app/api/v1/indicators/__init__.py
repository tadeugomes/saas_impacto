"""
Routers de Indicadores da API v1.

Este módulo exporta todos os routers de indicadores organizados por módulo.
"""

from app.api.v1.indicators.module1 import router as module1_router
from app.api.v1.indicators.generic import router as generic_router

__all__ = [
    "module1_router",
    "generic_router",
]
