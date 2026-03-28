"""
Cliente para a API DataJud/CNJ (processos judiciais).

API: https://datajud-wiki.cnj.jus.br/api-publica/
Autenticação: DATAJUD_API_KEY (registro gratuito).

Busca processos judiciais relacionados ao setor portuário.
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

# CNAEs portuários para filtrar partes de processos
CNAES_PORTUARIOS = {
    "5211-2/01", "5211-2/99", "5212-5/00",
    "5231-1/01", "5231-1/02", "5232-0/00", "5239-7/00",
    "5011-4/01", "5011-4/02", "5012-2/01",
    "5021-1/01", "5030-1/01", "5030-1/02",
}

# Assuntos judiciais portuários (códigos CNJ)
ASSUNTOS_PORTUARIOS = [
    "portuário", "marítimo", "aquaviário",
    "operador portuário", "trabalhador avulso",
    "praticagem", "ANTAQ",
]


class DatajudClient(BasePublicApiClient):
    """Cliente assíncrono para a API DataJud/CNJ."""

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.datajud_api_base_url,
            api_name="datajud",
            timeout=settings.public_api_timeout_seconds,
        )
        self._api_key = settings.datajud_api_key
        self._cache_ttl = settings.cache_ttl_compliance

    def _make_cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps({"ep": endpoint, **params}, sort_keys=True)
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:datajud:{endpoint}:{digest}"

    def _auth_headers(self) -> Optional[Dict[str, str]]:
        if self._api_key:
            return {"Authorization": f"APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="}
        return None

    async def buscar_processos_portuarios(
        self,
        nome_instalacao: str,
        ano: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca processos judiciais relacionados ao porto.

        Busca por termos portuários + nome da instalação nos assuntos
        e partes dos processos.
        """
        query_terms = f"{nome_instalacao} porto portuário"

        cache_key = self._make_cache_key(
            "processos_port", {"q": query_terms, "ano": ano}
        )

        async def _fetch():
            # DataJud usa Elasticsearch-like query
            body = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"assuntos.descricao": query_terms}},
                        ],
                    }
                },
                "size": 50,
                "sort": [{"dataAjuizamento": {"order": "desc"}}],
            }

            if ano:
                body["query"]["bool"]["filter"] = [
                    {"range": {"dataAjuizamento": {
                        "gte": f"{ano}-01-01",
                        "lte": f"{ano}-12-31",
                    }}}
                ]

            headers = self._auth_headers()
            try:
                # DataJud usa POST para busca
                data = await self._request(
                    "POST", "/processos/_search",
                    params=None, headers=headers, json_body=body,
                )
                hits = data.get("hits", {}).get("hits", []) if isinstance(data, dict) else []
                # Filtra por relevância portuária
                results = []
                for hit in hits:
                    source = hit.get("_source", {})
                    text = json.dumps(source, ensure_ascii=False)
                    if _is_port_related(text):
                        results.append({
                            "numero_processo": source.get("numeroProcesso", ""),
                            "tribunal": source.get("tribunal", ""),
                            "classe": source.get("classe", {}).get("nome", ""),
                            "assuntos": [
                                a.get("nome", a.get("descricao", ""))
                                for a in source.get("assuntos", [])
                            ],
                            "data_ajuizamento": source.get("dataAjuizamento", ""),
                            "grau": source.get("grau", ""),
                        })
                return results
            except (PublicApiError, Exception) as e:
                logger.warning("datajud_processos_error: %s", e)
                return []

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)


# Singleton
_datajud_client: Optional[DatajudClient] = None


def get_datajud_client() -> DatajudClient:
    global _datajud_client
    if _datajud_client is None:
        _datajud_client = DatajudClient()
    return _datajud_client
