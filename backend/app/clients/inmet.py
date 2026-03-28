"""
Cliente para a API do INMET (Instituto Nacional de Meteorologia).

API: https://apitempo.inmet.gov.br/
Autenticação: Nenhuma (API pública).

Fornece dados de precipitação, temperatura e umidade por estação
meteorológica — usados como variável exógena no forecast de carga.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient, PublicApiError
from app.config import get_settings

logger = logging.getLogger(__name__)

# Estações meteorológicas próximas a corredores logísticos de portos
# Mapeamento: porto → estação INMET no corredor de acesso
PORTO_ESTACOES_INMET = {
    "Santos": [
        {"codigo": "A701", "nome": "São Paulo - Mirante", "tipo": "corredor_logistico"},
        {"codigo": "A711", "nome": "Campinas", "tipo": "regiao_produtora"},
    ],
    "Paranaguá": [
        {"codigo": "A807", "nome": "Curitiba", "tipo": "corredor_logistico"},
        {"codigo": "A836", "nome": "Londrina", "tipo": "regiao_produtora"},
    ],
    "Rio Grande": [
        {"codigo": "A801", "nome": "Porto Alegre", "tipo": "corredor_logistico"},
    ],
    "Itaqui": [
        {"codigo": "A203", "nome": "São Luís", "tipo": "corredor_logistico"},
    ],
    "São Luís": [
        {"codigo": "A203", "nome": "São Luís", "tipo": "corredor_logistico"},
    ],
    "Tubarão": [
        {"codigo": "A612", "nome": "Vitória", "tipo": "porto"},
    ],
    "Vitória": [
        {"codigo": "A612", "nome": "Vitória", "tipo": "porto"},
    ],
    "Manaus": [
        {"codigo": "A101", "nome": "Manaus", "tipo": "porto"},
    ],
}

# Estações em regiões produtoras-chave (para forecast de safra)
REGIOES_PRODUTORAS = {
    "MT_soja": {"codigo": "A901", "nome": "Cuiabá", "desc": "Centro-Oeste soja"},
    "GO_soja": {"codigo": "A002", "nome": "Goiânia", "desc": "Goiás soja/milho"},
    "PR_grao": {"codigo": "A836", "nome": "Londrina", "desc": "Norte PR grãos"},
    "RS_grao": {"codigo": "A801", "nome": "Porto Alegre", "desc": "RS grãos"},
    "SP_cana": {"codigo": "A711", "nome": "Campinas", "desc": "SP cana-de-açúcar"},
    "MG_cafe": {"codigo": "A510", "nome": "Belo Horizonte", "desc": "MG café/minério"},
}


class InmetClient(BasePublicApiClient):
    """Cliente assíncrono para a API do INMET."""

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.inmet_api_base_url,
            api_name="inmet",
            timeout=settings.public_api_timeout_seconds,
        )
        self._cache_ttl = settings.cache_ttl_ambiental  # 1h

    def _make_cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps({"ep": endpoint, **params}, sort_keys=True)
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:inmet:{endpoint}:{digest}"

    async def dados_estacao(
        self,
        codigo_estacao: str,
        data_inicio: str,
        data_fim: str,
    ) -> List[Dict[str, Any]]:
        """
        Busca dados meteorológicos de uma estação.

        Args:
            codigo_estacao: Código da estação INMET
            data_inicio: YYYY-MM-DD
            data_fim: YYYY-MM-DD

        Returns:
            Lista de {data, precipitacao_mm, temp_max, temp_min, umidade_pct}
        """
        cache_key = self._make_cache_key(
            "estacao", {"est": codigo_estacao, "ini": data_inicio, "fim": data_fim}
        )

        async def _fetch():
            path = f"/estacao/{data_inicio}/{data_fim}/{codigo_estacao}"
            try:
                data = await self.get(path)
                if not isinstance(data, list):
                    return []
                return [
                    {
                        "data": item.get("DT_MEDICAO", item.get("data", "")),
                        "precipitacao_mm": _safe_float(item.get("CHUVA", item.get("precipitacao"))),
                        "temp_max": _safe_float(item.get("TEMP_MAX", item.get("temp_max"))),
                        "temp_min": _safe_float(item.get("TEMP_MIN", item.get("temp_min"))),
                        "umidade_pct": _safe_float(item.get("UMID_MED", item.get("umidade"))),
                    }
                    for item in data
                ]
            except PublicApiError as e:
                logger.warning("inmet_estacao_error est=%s: %s", codigo_estacao, e)
                return []

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    async def precipitacao_acumulada_mensal(
        self,
        codigo_estacao: str,
        ano: int,
    ) -> List[Dict[str, Any]]:
        """
        Precipitação acumulada por mês para uma estação.

        Returns:
            Lista de {ano, mes, precipitacao_acumulada_mm}
        """
        data_inicio = f"{ano}-01-01"
        data_fim = f"{ano}-12-31"
        dados = await self.dados_estacao(codigo_estacao, data_inicio, data_fim)

        from collections import defaultdict
        by_month: Dict[int, float] = defaultdict(float)
        for d in dados:
            try:
                mes = int(str(d.get("data", ""))[:7].split("-")[1])
                precip = d.get("precipitacao_mm") or 0
                by_month[mes] += precip
            except (ValueError, IndexError):
                continue

        return [
            {"ano": ano, "mes": mes, "precipitacao_acumulada_mm": round(val, 1)}
            for mes, val in sorted(by_month.items())
        ]

    def get_estacoes_porto(self, id_instalacao: str) -> List[Dict[str, str]]:
        """Retorna estações meteorológicas relevantes para um porto."""
        return PORTO_ESTACOES_INMET.get(id_instalacao, [])


def _safe_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


# Singleton
_inmet_client: Optional[InmetClient] = None


def get_inmet_client() -> InmetClient:
    global _inmet_client
    if _inmet_client is None:
        _inmet_client = InmetClient()
    return _inmet_client
