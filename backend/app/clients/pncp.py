"""
Cliente para o Portal Nacional de Contratações Públicas (PNCP).

API: https://pncp.gov.br/api/consulta/v1/
Autenticação: Nenhuma (API pública, Lei 14.133/2021).

Foco: licitações e contratos relacionados ao setor portuário,
filtrados por termos e órgãos portuários.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient, PublicApiError
from app.config import get_settings

logger = logging.getLogger(__name__)

# Termos para filtrar licitações/contratos portuários
TERMOS_PORTUARIOS = [
    "porto", "portuário", "terminal", "atracação", "berço",
    "cais", "píer", "retroárea", "armazém portuário",
    "operador portuário", "antaq", "praticagem", "rebocador",
    "contêiner", "granel", "alfândega", "zona primária",
    "dragagem", "sinalização náutica", "canal de acesso",
]

# Órgãos portuários federais (filtro por código UASG ou nome)
ORGAOS_PORTUARIOS = [
    "companhia docas",
    "autoridade portuária",
    "antaq",
    "secretaria de portos",
    "ministério de portos",
    "codesp", "cdrj", "codeba", "codern", "codomar",
    "emap", "suprg",
]


def _is_port_related(text: str) -> bool:
    """Verifica se um texto é relacionado ao setor portuário."""
    text_lower = text.lower()
    return any(t in text_lower for t in TERMOS_PORTUARIOS + ORGAOS_PORTUARIOS)


class PncpClient(BasePublicApiClient):
    """Cliente assíncrono para a API do PNCP."""

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.pncp_api_base_url,
            api_name="pncp",
            timeout=settings.public_api_timeout_seconds,
        )
        self._cache_ttl = settings.cache_ttl_compliance

    def _make_cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps({"ep": endpoint, **params}, sort_keys=True)
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:pncp:{endpoint}:{digest}"

    async def buscar_contratacoes_portuarias(
        self,
        cod_municipio_ibge: str,
        ano: int,
    ) -> List[Dict[str, Any]]:
        """
        Busca licitações/contratos portuários no município.

        Filtra por termos portuários no objeto da contratação
        e por órgãos portuários conhecidos.
        """
        cache_key = self._make_cache_key(
            "contratacoes_port", {"mun": cod_municipio_ibge, "ano": ano}
        )

        async def _fetch():
            params = {
                "codigoMunicipio": cod_municipio_ibge,
                "dataInicial": f"{ano}-01-01",
                "dataFinal": f"{ano}-12-31",
                "pagina": 1,
                "tamanhoPagina": 100,
            }
            try:
                data = await self.get("/contratacoes", params=params)
                items = data if isinstance(data, list) else data.get("data", []) if isinstance(data, dict) else []
                # Filtra apenas contratações portuárias
                return [
                    item for item in items
                    if _is_port_related(
                        str(item.get("objetoCompra", ""))
                        + " " + str(item.get("orgaoEntidade", {}).get("razaoSocial", ""))
                    )
                ]
            except PublicApiError as e:
                logger.warning("pncp_contratacoes_error: %s", e)
                return []

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    async def calcular_regularidade_licitatoria(
        self,
        cod_municipio_ibge: str,
        ano: int,
    ) -> Dict[str, Any]:
        """
        IND-10.06: Regularidade Licitatória.

        Razão entre contratos com publicação regular (no PNCP) vs. total.
        """
        contratacoes = await self.buscar_contratacoes_portuarias(cod_municipio_ibge, ano)

        total = len(contratacoes)
        if total == 0:
            return {
                "cod_municipio": cod_municipio_ibge,
                "ano": ano,
                "total_contratacoes": 0,
                "com_publicacao_regular": 0,
                "regularidade": None,
            }

        regulares = sum(
            1 for c in contratacoes
            if c.get("dataPublicacaoPncp") and c.get("modalidadeId")
        )

        return {
            "cod_municipio": cod_municipio_ibge,
            "ano": ano,
            "total_contratacoes": total,
            "com_publicacao_regular": regulares,
            "regularidade": round(regulares / total, 4) if total > 0 else None,
        }


# Singleton
_pncp_client: Optional[PncpClient] = None


def get_pncp_client() -> PncpClient:
    global _pncp_client
    if _pncp_client is None:
        _pncp_client = PncpClient()
    return _pncp_client
