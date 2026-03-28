"""
Serviço de indicadores macroeconômicos para contexto de investimento.

Combina dados do BACEN (Selic, IPCA, câmbio, IBC-Br) com dados do
IBGE (PIB municipal, população) para fornecer contexto macro ao investidor.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.clients.bacen import (
    BacenClient,
    SERIES_SELIC_META,
    SERIES_IPCA_MENSAL,
    SERIES_CAMBIO_PTAX,
    SERIES_IBC_BR,
    get_bacen_client,
)
from app.clients.ibge import IbgeClient, get_ibge_client

logger = logging.getLogger(__name__)


class MacroEconomicoService:
    """Indicadores macroeconômicos para contexto de investimento."""

    def __init__(
        self,
        bacen: Optional[BacenClient] = None,
        ibge: Optional[IbgeClient] = None,
    ):
        self.bacen = bacen or get_bacen_client()
        self.ibge = ibge or get_ibge_client()

    async def indicadores_atuais(self) -> Dict[str, Any]:
        """Snapshot atual: Selic, IPCA, câmbio, IBC-Br."""
        return await self.bacen.indicadores_atuais()

    async def serie_historica(
        self,
        codigo_sgs: int,
        anos: int = 5,
    ) -> List[Dict[str, Any]]:
        """Série temporal de um indicador BACEN."""
        inicio = (date.today() - timedelta(days=365 * anos)).strftime("%d/%m/%Y")
        fim = date.today().strftime("%d/%m/%Y")
        return await self.bacen.consultar_serie(codigo_sgs, inicio, fim)

    async def contexto_municipal(
        self,
        cod_ibge: str,
        ano: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        PIB, população e dados socioeconômicos de um município.

        Returns:
            Dict com pib, populacao, pib_per_capita do município
        """
        pop_data = await self.ibge.populacao_municipio(cod_ibge, ano)
        pib_data = await self.ibge.pib_municipio(cod_ibge, ano)

        populacao = pop_data.get("valor") if pop_data else None
        pib_mil = pib_data.get("pib_mil_reais") if pib_data else None

        pib_per_capita = None
        if populacao and pib_mil and populacao > 0:
            pib_per_capita = round((pib_mil * 1000) / populacao, 2)

        return {
            "cod_ibge": cod_ibge,
            "nome_municipio": (pop_data or pib_data or {}).get("nome_municipio", ""),
            "ano": (pop_data or pib_data or {}).get("ano"),
            "populacao": int(populacao) if populacao else None,
            "pib_mil_reais": pib_mil,
            "pib_per_capita_reais": pib_per_capita,
        }


# Singleton
_macro_service: Optional[MacroEconomicoService] = None


def get_macro_service() -> MacroEconomicoService:
    global _macro_service
    if _macro_service is None:
        _macro_service = MacroEconomicoService()
    return _macro_service
