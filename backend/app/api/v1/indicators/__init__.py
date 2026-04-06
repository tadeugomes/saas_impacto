"""
Routers de Indicadores da API v1.

Este módulo exporta todos os routers de indicadores organizados por módulo.
"""

from app.api.v1.indicators.module1 import router as module1_router
from app.api.v1.indicators.generic import router as generic_router
from app.api.v1.indicators.forecasting import router as forecasting_router
from app.api.v1.indicators.module6_fiscal import router as module6_fiscal_router
from app.api.v1.indicators.module12_capacity import router as module12_capacity_router

__all__ = [
    "module1_router",
    "generic_router",
    "forecasting_router",
    "module6_fiscal_router",
    "module12_capacity_router",
]
