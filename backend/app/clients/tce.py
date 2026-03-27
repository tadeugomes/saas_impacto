"""
Cliente para APIs dos Tribunais de Contas Estaduais (TCEs).

Cada TCE tem uma API diferente. Este cliente unifica o acesso
com um registry de endpoints por estado.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient, PublicApiError
from app.config import get_settings

logger = logging.getLogger(__name__)

# Registry de APIs por TCE
TCE_REGISTRY = {
    "SP": {
        "base_url": "https://transparencia.tce.sp.gov.br/api",
        "endpoints": {
            "receitas": "/receitas",
            "despesas": "/despesas",
        },
    },
    "RJ": {
        "base_url": "https://api-dados-abertos.tce.rj.gov.br",
        "endpoints": {
            "receitas": "/receitas",
            "despesas": "/despesas",
            "licitacoes": "/licitacoes",
            "contratos": "/contratos",
        },
    },
    "RS": {
        "base_url": "https://dados.tce.rs.gov.br/api",
        "endpoints": {
            "receitas": "/receitas",
            "despesas": "/despesas",
        },
    },
}

# Mapeamento de portos para UF
PORTO_TO_UF = {
    "Santos": "SP", "São Sebastião": "SP",
    "Rio de Janeiro": "RJ", "Itaguaí": "RJ", "Sepetiba": "RJ",
    "Angra dos Reis": "RJ", "Niterói": "RJ",
    "Rio Grande": "RS", "Porto Alegre": "RS",
    "Vitória": "ES", "Tubarão": "ES",
    "Salvador": "BA", "Aratu": "BA", "Ilhéus": "BA",
    "Suape": "PE", "Recife": "PE",
    "Fortaleza": "CE", "Mucuripe": "CE", "Pecém": "CE",
    "São Luís": "MA", "Itaqui": "MA",
    "Paranaguá": "PR",
    "Itajaí": "SC", "São Francisco do Sul": "SC", "Imbituba": "SC",
}


class TceClient(BasePublicApiClient):
    """Cliente unificado para APIs dos TCEs."""

    def __init__(self, uf: str):
        if uf not in TCE_REGISTRY:
            raise ValueError(f"TCE {uf} não suportado. Disponíveis: {list(TCE_REGISTRY.keys())}")

        self.uf = uf
        config = TCE_REGISTRY[uf]
        settings = get_settings()
        super().__init__(
            base_url=config["base_url"],
            api_name=f"tce_{uf.lower()}",
            timeout=settings.public_api_timeout_seconds,
        )
        self._endpoints = config["endpoints"]
        self._cache_ttl = settings.cache_ttl_ibge  # Dados fiscais mudam lentamente

    def _make_cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps(
            {"uf": self.uf, "ep": endpoint, **params}, sort_keys=True
        )
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:tce_{self.uf.lower()}:{endpoint}:{digest}"

    async def consultar_receitas(
        self,
        cod_municipio: str,
        ano: int,
    ) -> List[Dict[str, Any]]:
        """Consulta receitas municipais no TCE."""
        endpoint = self._endpoints.get("receitas")
        if not endpoint:
            return []

        cache_key = self._make_cache_key("receitas", {"mun": cod_municipio, "ano": ano})

        async def _fetch():
            params = {"municipio": cod_municipio, "ano": ano, "formato": "json"}
            try:
                return await self.get(endpoint, params=params)
            except PublicApiError as e:
                logger.warning("tce_receitas_error", uf=self.uf, error=str(e))
                return []

        result = await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)
        return result if isinstance(result, list) else []

    async def consultar_despesas(
        self,
        cod_municipio: str,
        ano: int,
    ) -> List[Dict[str, Any]]:
        """Consulta despesas municipais no TCE."""
        endpoint = self._endpoints.get("despesas")
        if not endpoint:
            return []

        cache_key = self._make_cache_key("despesas", {"mun": cod_municipio, "ano": ano})

        async def _fetch():
            params = {"municipio": cod_municipio, "ano": ano, "formato": "json"}
            try:
                return await self.get(endpoint, params=params)
            except PublicApiError as e:
                logger.warning("tce_despesas_error", uf=self.uf, error=str(e))
                return []

        result = await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)
        return result if isinstance(result, list) else []

    async def calcular_autonomia_fiscal(
        self,
        cod_municipio: str,
        ano: int,
    ) -> Dict[str, Any]:
        """
        IND-6.06: Autonomia Fiscal = Receita própria / Receita total.

        Mede a capacidade do município de gerar receita própria.
        """
        receitas = await self.consultar_receitas(cod_municipio, ano)

        if not receitas:
            return {
                "cod_municipio": cod_municipio,
                "ano": ano,
                "receita_propria": None,
                "receita_total": None,
                "autonomia_fiscal": None,
            }

        receita_total = sum(
            float(r.get("valor", r.get("receita_realizada", 0)) or 0) for r in receitas
        )
        receita_propria = sum(
            float(r.get("valor", r.get("receita_realizada", 0)) or 0)
            for r in receitas
            if str(r.get("categoria", r.get("tipo", ""))).lower() in (
                "receita tributária", "tributaria", "receita patrimonial",
                "receita de serviços", "propria",
            )
        )

        autonomia = round(receita_propria / receita_total, 4) if receita_total > 0 else None

        return {
            "cod_municipio": cod_municipio,
            "ano": ano,
            "receita_propria": receita_propria,
            "receita_total": receita_total,
            "autonomia_fiscal": autonomia,
        }

    async def calcular_execucao_orcamentaria(
        self,
        cod_municipio: str,
        ano: int,
    ) -> Dict[str, Any]:
        """
        IND-6.08: Eficiência na Execução Orçamentária = Executado / Autorizado.
        """
        despesas = await self.consultar_despesas(cod_municipio, ano)

        if not despesas:
            return {
                "cod_municipio": cod_municipio,
                "ano": ano,
                "despesa_executada": None,
                "despesa_autorizada": None,
                "eficiencia_execucao": None,
            }

        executada = sum(
            float(d.get("valor_pago", d.get("empenhado", 0)) or 0) for d in despesas
        )
        autorizada = sum(
            float(d.get("valor_autorizado", d.get("dotacao_atualizada", executada)) or 0)
            for d in despesas
        )

        eficiencia = round(executada / autorizada, 4) if autorizada > 0 else None

        return {
            "cod_municipio": cod_municipio,
            "ano": ano,
            "despesa_executada": executada,
            "despesa_autorizada": autorizada,
            "eficiencia_execucao": eficiencia,
        }


def get_tce_client(uf: str) -> TceClient:
    """Factory para TceClient por UF."""
    return TceClient(uf)


def get_uf_for_porto(id_instalacao: str) -> Optional[str]:
    """Retorna a UF de uma instalação portuária."""
    return PORTO_TO_UF.get(id_instalacao)
