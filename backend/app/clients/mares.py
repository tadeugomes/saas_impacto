"""
Cliente para dados de marés da Marinha do Brasil.

Fornece previsões de maré para portos brasileiros,
janelas de navegação por calado e correlação com operações portuárias.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient, PublicApiError
from app.config import get_settings

logger = logging.getLogger(__name__)

# Mapeamento de instalações portuárias para estações de maré
# Fonte: Diretoria de Hidrografia e Navegação (DHN) da Marinha do Brasil
INSTALACAO_TO_ESTACAO_MARE = {
    "Santos": {"id": "23190", "nome": "Porto de Santos"},
    "Paranaguá": {"id": "23228", "nome": "Paranaguá"},
    "Rio Grande": {"id": "23340", "nome": "Rio Grande"},
    "Itajaí": {"id": "23270", "nome": "Itajaí"},
    "São Francisco do Sul": {"id": "23260", "nome": "São Francisco do Sul"},
    "Vitória": {"id": "23126", "nome": "Vitória"},
    "Tubarão": {"id": "23126", "nome": "Vitória"},
    "Rio de Janeiro": {"id": "23100", "nome": "Ilha Fiscal - RJ"},
    "Itaguaí": {"id": "23095", "nome": "Sepetiba"},
    "Sepetiba": {"id": "23095", "nome": "Sepetiba"},
    "Salvador": {"id": "22970", "nome": "Salvador"},
    "Aratu": {"id": "22970", "nome": "Salvador"},
    "Suape": {"id": "22920", "nome": "Suape"},
    "Recife": {"id": "22910", "nome": "Recife"},
    "Fortaleza": {"id": "22720", "nome": "Fortaleza"},
    "Mucuripe": {"id": "22720", "nome": "Fortaleza"},
    "Pecém": {"id": "22710", "nome": "Pecém"},
    "São Luís": {"id": "22580", "nome": "São Luís"},
    "Itaqui": {"id": "22580", "nome": "São Luís"},
    "Belém": {"id": "22430", "nome": "Belém"},
    "Vila do Conde": {"id": "22420", "nome": "Vila do Conde"},
    "Manaus": {"id": "22250", "nome": "Manaus"},
    "Santarém": {"id": "22350", "nome": "Santarém"},
    "Imbituba": {"id": "23290", "nome": "Imbituba"},
    "Angra dos Reis": {"id": "23110", "nome": "Angra dos Reis"},
    "Cabedelo": {"id": "22880", "nome": "Cabedelo"},
    "Natal": {"id": "22860", "nome": "Natal"},
    "Maceió": {"id": "22940", "nome": "Maceió"},
}


class MaresClient(BasePublicApiClient):
    """Cliente assíncrono para dados de marés."""

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.mares_api_base_url,
            api_name="mares",
            timeout=settings.public_api_timeout_seconds,
        )
        self._cache_ttl = settings.cache_ttl_mares

    def _make_cache_key(self, estacao: str, inicio: str, fim: str) -> str:
        payload = json.dumps(
            {"estacao": estacao, "inicio": inicio, "fim": fim}, sort_keys=True
        )
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:mares:{estacao}:{digest}"

    async def previsao_mares(
        self,
        estacao_id: str,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Previsão de marés para uma estação.

        Args:
            estacao_id: ID da estação de maré
            data_inicio: Data início (YYYY-MM-DD)
            data_fim: Data fim (YYYY-MM-DD)

        Returns:
            Lista de {"datetime": "...", "altura_metros": 1.23, "tipo": "PM"|"BM"}
        """
        if not data_inicio:
            data_inicio = date.today().isoformat()
        if not data_fim:
            data_fim = (date.today() + timedelta(days=7)).isoformat()

        cache_key = self._make_cache_key(estacao_id, data_inicio, data_fim)

        async def _fetch():
            params = {
                "estacao": estacao_id,
                "inicio": data_inicio,
                "fim": data_fim,
                "formato": "json",
            }
            try:
                return await self.get("/previsao", params=params)
            except PublicApiError:
                logger.warning(
                    "mares_api_unavailable",
                    estacao=estacao_id,
                    fallback="simulated",
                )
                return self._generate_simulated_tides(data_inicio, data_fim)

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    def get_estacao_for_instalacao(self, id_instalacao: str) -> Optional[Dict[str, str]]:
        """Mapeia instalação portuária para estação de maré."""
        return INSTALACAO_TO_ESTACAO_MARE.get(id_instalacao)

    @staticmethod
    def _generate_simulated_tides(
        data_inicio: str, data_fim: str
    ) -> List[Dict[str, Any]]:
        """
        Gera dados simulados de maré (padrão semidiurno) como fallback.
        Usado quando a API de marés está indisponível.
        """
        from datetime import datetime

        result = []
        try:
            d_start = datetime.fromisoformat(data_inicio)
            d_end = datetime.fromisoformat(data_fim)
        except ValueError:
            return result

        current = d_start
        hour_offset = 0
        while current <= d_end:
            for h, tipo, alt in [
                (0 + hour_offset, "BM", 0.3),
                (6 + hour_offset, "PM", 1.4),
                (12 + hour_offset, "BM", 0.4),
                (18 + hour_offset, "PM", 1.2),
            ]:
                t = current.replace(hour=int(h) % 24, minute=int((h % 1) * 60))
                result.append({
                    "datetime": t.isoformat(),
                    "altura_metros": alt,
                    "tipo": tipo,
                    "simulado": True,
                })
            current += timedelta(days=1)
            hour_offset = (hour_offset + 0.8) % 6

        return result

    async def janelas_navegacao(
        self,
        estacao_id: str,
        calado_minimo: float,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calcula janelas de navegação baseado em calado mínimo.

        Returns:
            Dict com horas_navegaveis_por_dia, percentual_janela, periodos
        """
        previsao = await self.previsao_mares(estacao_id, data_inicio, data_fim)

        if not previsao:
            return {"horas_navegaveis_por_dia": None, "percentual_janela": None}

        total_pontos = len(previsao)
        pontos_acima = sum(
            1 for p in previsao
            if (p.get("altura_metros") or 0) >= calado_minimo
        )

        pct = round(pontos_acima / total_pontos * 100, 1) if total_pontos > 0 else 0
        horas_dia = round(pct / 100 * 24, 1)

        return {
            "estacao_id": estacao_id,
            "calado_minimo_metros": calado_minimo,
            "horas_navegaveis_por_dia": horas_dia,
            "percentual_janela": pct,
            "total_observacoes": total_pontos,
        }


# Singleton
_mares_client: Optional[MaresClient] = None


def get_mares_client() -> MaresClient:
    global _mares_client
    if _mares_client is None:
        _mares_client = MaresClient()
    return _mares_client
