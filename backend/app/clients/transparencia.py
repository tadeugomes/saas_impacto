"""
Cliente para o Portal da Transparência do Governo Federal.

API: https://api.portaldatransparencia.gov.br/api-de-dados/
Requer TRANSPARENCIA_API_KEY (registro gratuito).
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient, PublicApiError
from app.config import get_settings

logger = logging.getLogger(__name__)


class TransparenciaClient(BasePublicApiClient):
    """Cliente assíncrono para o Portal da Transparência."""

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.transparencia_api_base_url,
            api_name="transparencia",
            timeout=settings.public_api_timeout_seconds,
        )
        self._api_key = settings.transparencia_api_key
        self._cache_ttl = 43200  # 12h

    def _make_cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps({"ep": endpoint, **params}, sort_keys=True)
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:transparencia:{endpoint}:{digest}"

    def _auth_headers(self) -> Optional[Dict[str, str]]:
        if self._api_key:
            return {"chave-api-dados": self._api_key}
        return None

    async def _get_with_auth(self, path: str, params: dict) -> Any:
        """GET com header de autenticação."""
        headers = self._auth_headers()
        return await self._request("GET", path, params=params, headers=headers)

    async def buscar_contratos_municipio(
        self,
        cod_municipio_ibge: str,
        ano: int,
    ) -> List[Dict[str, Any]]:
        """Busca contratos federais em um município."""
        cache_key = self._make_cache_key(
            "contratos", {"mun": cod_municipio_ibge, "ano": ano}
        )

        async def _fetch():
            params = {
                "codigoMunicipio": cod_municipio_ibge,
                "dataInicial": f"01/01/{ano}",
                "dataFinal": f"31/12/{ano}",
                "pagina": 1,
            }
            try:
                return await self._get_with_auth("/contratos", params)
            except PublicApiError as e:
                if e.status_code == 401:
                    logger.warning("transparencia_api_key_invalida")
                else:
                    logger.warning("transparencia_contratos_error", error=str(e))
                return []

        result = await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)
        return result if isinstance(result, list) else []

    async def buscar_emendas_municipio(
        self,
        cod_municipio_ibge: str,
        ano: int,
    ) -> List[Dict[str, Any]]:
        """Busca emendas parlamentares direcionadas ao município."""
        cache_key = self._make_cache_key(
            "emendas", {"mun": cod_municipio_ibge, "ano": ano}
        )

        async def _fetch():
            params = {
                "codigoMunicipio": cod_municipio_ibge,
                "anoEmenda": ano,
                "pagina": 1,
            }
            try:
                return await self._get_with_auth("/emendas", params)
            except PublicApiError:
                return []

        result = await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)
        return result if isinstance(result, list) else []

    async def buscar_servidores_municipio(
        self,
        cod_municipio_ibge: str,
    ) -> Dict[str, Any]:
        """Conta servidores federais no município (proxy presença federal)."""
        cache_key = self._make_cache_key(
            "servidores", {"mun": cod_municipio_ibge}
        )

        async def _fetch():
            params = {"codigoMunicipio": cod_municipio_ibge, "pagina": 1}
            try:
                data = await self._get_with_auth("/servidores", params)
                total = len(data) if isinstance(data, list) else 0
                return {"cod_municipio": cod_municipio_ibge, "total_servidores": total}
            except PublicApiError:
                return {"cod_municipio": cod_municipio_ibge, "total_servidores": None}

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    async def calcular_investimento_federal(
        self,
        cod_municipio_ibge: str,
        ano: int,
        populacao: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        IND-6.09: Investimento Federal no Município Portuário.
        IND-6.10: Emendas Parlamentares no município.
        """
        contratos = await self.buscar_contratos_municipio(cod_municipio_ibge, ano)
        emendas = await self.buscar_emendas_municipio(cod_municipio_ibge, ano)

        valor_contratos = sum(
            float(c.get("valorInicial", c.get("valor", 0)) or 0) for c in contratos
        )
        valor_emendas = sum(
            float(e.get("valor", e.get("valorEmpenhado", 0)) or 0) for e in emendas
        )

        per_capita = None
        if populacao and populacao > 0:
            per_capita = round((valor_contratos + valor_emendas) / populacao, 2)

        return {
            "cod_municipio": cod_municipio_ibge,
            "ano": ano,
            "valor_contratos_federais": valor_contratos,
            "qtd_contratos": len(contratos),
            "valor_emendas": valor_emendas,
            "qtd_emendas": len(emendas),
            "investimento_federal_total": valor_contratos + valor_emendas,
            "investimento_per_capita": per_capita,
        }


# Singleton
_transparencia_client: Optional[TransparenciaClient] = None


def get_transparencia_client() -> TransparenciaClient:
    global _transparencia_client
    if _transparencia_client is None:
        _transparencia_client = TransparenciaClient()
    return _transparencia_client
