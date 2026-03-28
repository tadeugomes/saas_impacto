"""
Cliente para a API do Tribunal de Contas da União (TCU).

Busca acórdãos e lista de inidôneos, filtrados por termos portuários.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient, PublicApiError
from app.clients.pncp import TERMOS_PORTUARIOS, _is_port_related
from app.config import get_settings

logger = logging.getLogger(__name__)


class TcuClient(BasePublicApiClient):
    """Cliente assíncrono para a API do TCU."""

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.tcu_api_base_url,
            api_name="tcu",
            timeout=settings.public_api_timeout_seconds,
        )
        self._cache_ttl = settings.cache_ttl_compliance

    def _make_cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps({"ep": endpoint, **params}, sort_keys=True)
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:tcu:{endpoint}:{digest}"

    async def buscar_acordaos_portuarios(
        self,
        termo_busca: str,
        ano: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca acórdãos do TCU relacionados ao setor portuário.

        Args:
            termo_busca: Nome do porto ou instalação
            ano: Ano de referência (opcional)
        """
        # Combina nome do porto com termos portuários genéricos
        query = f"{termo_busca} porto portuário"

        cache_key = self._make_cache_key(
            "acordaos_port", {"q": query, "ano": ano}
        )

        async def _fetch():
            params = {"query": query, "limite": 50}
            if ano:
                params["anoInicial"] = ano
                params["anoFinal"] = ano
            try:
                data = await self.get("/acordaos", params=params)
                items = data if isinstance(data, list) else data.get("items", data.get("data", [])) if isinstance(data, dict) else []
                # Filtro adicional de relevância portuária
                return [
                    item for item in items
                    if _is_port_related(
                        str(item.get("descricao", ""))
                        + " " + str(item.get("ementa", ""))
                        + " " + str(item.get("entidade", ""))
                    )
                ]
            except PublicApiError as e:
                logger.warning("tcu_acordaos_error: %s", e)
                return []

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    async def buscar_inidôneos_portuarios(
        self,
        cod_municipio_ibge: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca empresas inidôneas do setor portuário na lista do TCU.
        """
        cache_key = self._make_cache_key(
            "inidoneos_port", {"mun": cod_municipio_ibge or "all"}
        )

        async def _fetch():
            params = {"limite": 100}
            if cod_municipio_ibge:
                params["municipio"] = cod_municipio_ibge
            try:
                data = await self.get("/licitantes-inidoneos", params=params)
                items = data if isinstance(data, list) else data.get("items", data.get("data", [])) if isinstance(data, dict) else []
                return [
                    item for item in items
                    if _is_port_related(
                        str(item.get("razaoSocial", ""))
                        + " " + str(item.get("cnae", ""))
                        + " " + str(item.get("motivo", ""))
                    )
                ]
            except PublicApiError as e:
                logger.warning("tcu_inidoneos_error: %s", e)
                return []

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)


# Singleton
_tcu_client: Optional[TcuClient] = None


def get_tcu_client() -> TcuClient:
    global _tcu_client
    if _tcu_client is None:
        _tcu_client = TcuClient()
    return _tcu_client
