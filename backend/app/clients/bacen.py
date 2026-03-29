"""
Cliente para a API do Banco Central do Brasil (SGS).

Séries prioritárias para contexto de investimento:
- 432: IPCA mensal (deflação)
- 11:  Taxa Selic meta (custo de oportunidade)
- 3698: Câmbio PTAX venda (competitividade exportadora)
- 24364: IBC-Br (proxy PIB mensal)
- 13522: Expectativa Focus IPCA 12 meses
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient
from app.config import get_settings

logger = logging.getLogger(__name__)

# Séries SGS mais relevantes para o investidor
SERIES_SELIC_META = 4189  # Selic meta definida pelo Copom (% a.m.) — série mensal
SERIES_IPCA_MENSAL = 433  # IPCA variação mensal (%)
SERIES_CAMBIO_PTAX = 3698  # Dólar PTAX venda
SERIES_IBC_BR = 24364  # IBC-Br dessazonalizado
SERIES_FOCUS_IPCA = 13522  # Expectativa Focus IPCA 12 meses


class BacenClient(BasePublicApiClient):
    """Cliente assíncrono para a API SGS do Banco Central."""

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.bacen_api_base_url,
            api_name="bacen",
            timeout=settings.public_api_timeout_seconds,
        )
        self._cache_ttl = settings.cache_ttl_bacen

    def _make_cache_key(self, serie: int, inicio: str, fim: str) -> str:
        payload = json.dumps(
            {"serie": serie, "inicio": inicio, "fim": fim},
            sort_keys=True,
        )
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:bacen:{serie}:{digest}"

    async def consultar_serie(
        self,
        codigo_serie: int,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Consulta uma série temporal do SGS.

        Args:
            codigo_serie: Código da série no SGS (ex: 432 para IPCA)
            data_inicio: Data início no formato dd/MM/yyyy
            data_fim: Data fim no formato dd/MM/yyyy

        Returns:
            Lista de {"data": "dd/MM/yyyy", "valor": "1.23"}
        """
        if not data_inicio:
            data_inicio = (date.today() - timedelta(days=365 * 5)).strftime(
                "%d/%m/%Y"
            )
        if not data_fim:
            data_fim = date.today().strftime("%d/%m/%Y")

        cache_key = self._make_cache_key(codigo_serie, data_inicio, data_fim)

        async def _fetch():
            path = f"/bcdata.sgs.{codigo_serie}/dados"
            params = {
                "formato": "json",
                "dataInicial": data_inicio,
                "dataFinal": data_fim,
            }
            return await self.get(path, params=params)

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    async def indicadores_atuais(self) -> Dict[str, Any]:
        """
        Retorna snapshot dos indicadores macro atuais.

        Returns:
            Dict com selic, ipca_mensal, ipca_12m, cambio_ptax, ibc_br
        """
        cache_key = f"api:bacen:indicadores_atuais:{date.today().isoformat()}"

        async def _fetch():
            hoje = date.today().strftime("%d/%m/%Y")
            inicio_12m = (date.today() - timedelta(days=400)).strftime("%d/%m/%Y")
            inicio_1m = (date.today() - timedelta(days=60)).strftime("%d/%m/%Y")

            selic_data = await self.consultar_serie(
                SERIES_SELIC_META, inicio_1m, hoje
            )
            ipca_data = await self.consultar_serie(
                SERIES_IPCA_MENSAL, inicio_12m, hoje
            )
            cambio_data = await self.consultar_serie(
                SERIES_CAMBIO_PTAX, inicio_1m, hoje
            )
            ibc_data = await self.consultar_serie(
                SERIES_IBC_BR, inicio_1m, hoje
            )

            def _last_valor(data: list) -> Optional[float]:
                if not data:
                    return None
                try:
                    return float(data[-1]["valor"])
                except (KeyError, ValueError, TypeError):
                    return None

            def _acumulado_12m(data: list) -> Optional[float]:
                if len(data) < 12:
                    return None
                try:
                    ultimos_12 = data[-12:]
                    acum = 1.0
                    for item in ultimos_12:
                        acum *= 1 + float(item["valor"]) / 100
                    return round((acum - 1) * 100, 2)
                except (ValueError, TypeError):
                    return None

            # Série 4189 retorna % a.m.; converter para % a.a.
            selic_mensal = _last_valor(selic_data)
            selic_aa = round(((1 + selic_mensal / 100) ** 12 - 1) * 100, 2) if selic_mensal else None

            return {
                "selic_meta_aa": selic_aa,
                "ipca_mensal": _last_valor(ipca_data),
                "ipca_acumulado_12m": _acumulado_12m(ipca_data),
                "cambio_ptax_venda": _last_valor(cambio_data),
                "ibc_br": _last_valor(ibc_data),
                "data_referencia": date.today().isoformat(),
            }

        return await self.get_cached(cache_key, _fetch, ttl=3600)

    async def get_deflator_ipca(
        self,
        ano_base: int,
        ano_inicio: int,
        ano_fim: int,
    ) -> Dict[int, float]:
        """
        Calcula fatores de deflação IPCA por ano, relativo ao ano_base.

        Retorna dict {ano: fator} onde valor_real = valor_nominal * fator.
        """
        data_inicio = f"01/01/{ano_inicio}"
        data_fim = f"31/12/{ano_fim}"
        ipca_data = await self.consultar_serie(
            SERIES_IPCA_MENSAL, data_inicio, data_fim
        )

        # Agrupa IPCA mensal por ano e calcula acumulado anual
        annual_ipca: Dict[int, float] = {}
        for item in ipca_data:
            try:
                parts = item["data"].split("/")
                ano = int(parts[2])
                valor = float(item["valor"])
                if ano not in annual_ipca:
                    annual_ipca[ano] = 1.0
                annual_ipca[ano] *= 1 + valor / 100
            except (ValueError, TypeError, KeyError, IndexError):
                continue

        # Calcula índice acumulado
        anos_sorted = sorted(annual_ipca.keys())
        indice: Dict[int, float] = {}
        acum = 1.0
        for ano in anos_sorted:
            acum *= annual_ipca.get(ano, 1.0)
            indice[ano] = acum

        # Fator de deflação relativo ao ano_base
        base_indice = indice.get(ano_base, 1.0)
        deflator: Dict[int, float] = {}
        for ano in range(ano_inicio, ano_fim + 1):
            ano_indice = indice.get(ano, base_indice)
            deflator[ano] = round(base_indice / ano_indice, 6) if ano_indice else 1.0

        return deflator


# Singleton
_bacen_client: Optional[BacenClient] = None


def get_bacen_client() -> BacenClient:
    global _bacen_client
    if _bacen_client is None:
        _bacen_client = BacenClient()
    return _bacen_client
