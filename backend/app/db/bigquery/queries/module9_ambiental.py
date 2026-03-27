"""
Queries do Módulo 9 — Risco Ambiental.

Funções async que consultam ANA e INPE. IND-9.03 retorna
bloco `composicao` com transparência total sobre os dados.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.clients.ana import get_ana_client
from app.clients.inpe import get_inpe_client
from app.services.ambiental_service import get_ambiental_service


async def query_risco_hidrico(
    id_instalacao: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-9.01: Índice de Risco Hídrico (portos fluviais)."""
    if not id_instalacao:
        return []

    ana = get_ana_client()
    estacao = ana.get_estacao_for_porto(id_instalacao)
    if not estacao:
        return [{
            "id_instalacao": id_instalacao,
            "tipo_porto": "maritimo",
            "risco_hidrico": None,
            "nota": "Porto marítimo — risco hídrico não aplicável",
        }]

    resultado = await ana.calcular_risco_hidrico(estacao["codigo"], calado_minimo_metros=12.0)
    return [{
        "id_instalacao": id_instalacao,
        "tipo_porto": "fluvial",
        "estacao_ana": estacao["codigo"],
        "rio": estacao.get("rio", ""),
        **resultado,
    }]


async def query_risco_incendio(
    id_instalacao: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-9.02: Focos de Incêndio Próximos ao Porto."""
    if not id_instalacao:
        return []

    inpe = get_inpe_client()
    resultado = await inpe.calcular_risco_incendio(id_instalacao, raio_km=50, dias=7)
    return [resultado]


async def query_indice_risco_ambiental(
    id_instalacao: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-9.03: Índice de Risco Ambiental Composto.

    Retorna valor normalizado (0-1) + bloco `composicao` com
    fórmula, pesos, fontes, períodos e nota metodológica.
    """
    if not id_instalacao:
        return []

    service = get_ambiental_service()
    resultado = await service.indice_risco_ambiental(id_instalacao)
    return [resultado]


QUERIES_MODULE_9 = {
    "IND-9.01": query_risco_hidrico,
    "IND-9.02": query_risco_incendio,
    "IND-9.03": query_indice_risco_ambiental,
}
