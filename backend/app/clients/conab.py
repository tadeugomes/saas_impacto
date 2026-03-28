"""
Cliente para dados de safra da CONAB (Companhia Nacional de Abastecimento).

Fornece estimativas de safra (soja, milho, açúcar, café etc.)
que são o principal driver de tonelagem em portos graneleiros.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient, PublicApiError
from app.config import get_settings

logger = logging.getLogger(__name__)

# Mapeamento de produtos CONAB para portos
PRODUTO_PORTO = {
    "soja": ["Santos", "Paranaguá", "Rio Grande", "São Luís", "Itaqui", "Santarém", "Barcarena"],
    "milho": ["Santos", "Paranaguá", "Rio Grande", "São Luís", "Itaqui"],
    "a��úcar": ["Santos", "Paranaguá", "Maceió", "Recife", "Suape"],
    "café": ["Santos", "Vitória", "Rio de Janeiro"],
    "algodão": ["Santos", "Salvador", "Vitória"],
    "minério": ["Tubarão", "Itaguaí", "São Luís", "Itaqui"],
}

# UFs produtoras relevantes por produto
PRODUTO_UF_PRODUTORA = {
    "soja": ["MT", "PR", "RS", "GO", "MS", "BA", "MA", "TO", "PI"],
    "milho": ["MT", "PR", "GO", "MS", "MG", "RS"],
    "açúcar": ["SP", "GO", "MG", "MS", "PR", "AL", "PE"],
    "café": ["MG", "ES", "SP", "PR", "BA", "RO"],
}


class ConabClient(BasePublicApiClient):
    """Cliente assíncrono para dados de safra da CONAB."""

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.conab_api_base_url,
            api_name="conab",
            timeout=settings.public_api_timeout_seconds,
        )
        self._cache_ttl = settings.cache_ttl_ibge  # Dados de safra = mensal

    def _make_cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps({"ep": endpoint, **params}, sort_keys=True)
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:conab:{endpoint}:{digest}"

    async def estimativa_safra(
        self,
        produto: str,
        safra: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca estimativa de safra da CONAB.

        Args:
            produto: Nome do produto (soja, milho, açúcar, café)
            safra: Ano-safra (ex: "2024/25"). Default: safra atual.

        Returns:
            Lista de {uf, produto, area_plantada_ha, producao_mil_ton, produtividade_kg_ha}
        """
        cache_key = self._make_cache_key(
            "safra", {"prod": produto, "safra": safra or "atual"}
        )

        async def _fetch():
            params = {"produto": produto}
            if safra:
                params["safra"] = safra
            try:
                data = await self.get("/safras/serie-historica", params=params)
                if isinstance(data, dict):
                    return data.get("data", data.get("items", []))
                return data if isinstance(data, list) else []
            except PublicApiError as e:
                logger.warning("conab_safra_error produto=%s: %s", produto, e)
                return []

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    async def producao_por_uf(
        self,
        produto: str,
        uf: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Retorna produção estimada por UF (mil toneladas).

        Útil para associar safra regional ao porto mais próximo.
        """
        dados = await self.estimativa_safra(produto)

        result = {}
        for item in dados:
            item_uf = str(item.get("uf", item.get("estado", ""))).upper()
            if uf and item_uf != uf.upper():
                continue
            try:
                prod = float(item.get("producao", item.get("producao_mil_ton", 0)) or 0)
                result[item_uf] = result.get(item_uf, 0) + prod
            except (ValueError, TypeError):
                continue

        return result

    def get_produtos_porto(self, id_instalacao: str) -> List[str]:
        """Retorna produtos agrícolas relevantes para um porto."""
        return [
            prod for prod, portos in PRODUTO_PORTO.items()
            if id_instalacao in portos
        ]


# Singleton
_conab_client: Optional[ConabClient] = None


def get_conab_client() -> ConabClient:
    global _conab_client
    if _conab_client is None:
        _conab_client = ConabClient()
    return _conab_client
