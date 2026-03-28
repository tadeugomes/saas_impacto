"""
Cliente para o índice ONI (Oceanic Niño Index) da NOAA.

1 valor por mês. El Niño (ONI > +0.5) ou La Niña (ONI < -0.5).
Impacto forte na safra brasileira com lag de 3-6 meses.

Fonte: https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient, PublicApiError
from app.config import get_settings

logger = logging.getLogger(__name__)

# Mapeamento de trimestres ONI para meses
TRIMESTRE_MAP = {
    "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4,
    "AMJ": 5, "MJJ": 6, "JJA": 7, "JAS": 8,
    "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
}


def _classify_enso(oni: float) -> str:
    """Classifica fase ENSO pelo índice ONI."""
    if oni >= 1.5:
        return "el_nino_forte"
    elif oni >= 0.5:
        return "el_nino"
    elif oni <= -1.5:
        return "la_nina_forte"
    elif oni <= -0.5:
        return "la_nina"
    return "neutro"


class NoaaEnsoClient(BasePublicApiClient):
    """Cliente assíncrono para o índice ONI da NOAA."""

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.noaa_oni_base_url,
            api_name="noaa_enso",
            timeout=settings.public_api_timeout_seconds,
        )
        self._cache_ttl = 86400  # 24h — atualiza mensalmente

    async def get_oni_series(self) -> List[Dict[str, Any]]:
        """
        Busca série histórica completa do ONI.

        Returns:
            Lista de {ano, mes, oni, fase_enso}
        """
        cache_key = "api:noaa:oni:full_series"

        async def _fetch():
            try:
                # ONI é um arquivo texto simples
                client = await self._get_client()
                resp = await client.get("/oni.ascii.txt")
                resp.raise_for_status()
                return self._parse_oni_text(resp.text)
            except Exception as e:
                logger.warning("noaa_oni_error: %s", e)
                return []

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    async def get_oni_atual(self) -> Dict[str, Any]:
        """Retorna o ONI mais recente."""
        serie = await self.get_oni_series()
        if not serie:
            return {"oni": None, "fase_enso": "sem_dados"}
        return serie[-1]

    async def get_oni_por_periodo(
        self,
        ano_inicio: int,
        ano_fim: int,
    ) -> List[Dict[str, Any]]:
        """Filtra série ONI por período."""
        serie = await self.get_oni_series()
        return [
            item for item in serie
            if ano_inicio <= item.get("ano", 0) <= ano_fim
        ]

    @staticmethod
    def _parse_oni_text(text: str) -> List[Dict[str, Any]]:
        """
        Parseia o arquivo oni.ascii.txt da NOAA.

        Formato:
          YEAR   DJF   JFM   FMA   MAM   AMJ   MJJ   JJA   JAS   ASO   SON   OND   NDJ
          1950   -1.5  -1.3  ...
        """
        result = []
        lines = text.strip().split("\n")

        for line in lines:
            parts = line.split()
            if len(parts) < 13:
                continue
            try:
                ano = int(parts[0])
            except ValueError:
                continue

            for i, trimestre in enumerate(
                ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
            ):
                try:
                    oni = float(parts[i + 1])
                    mes = TRIMESTRE_MAP[trimestre]
                    result.append({
                        "ano": ano,
                        "mes": mes,
                        "trimestre": trimestre,
                        "oni": oni,
                        "fase_enso": _classify_enso(oni),
                    })
                except (ValueError, IndexError):
                    continue

        return result


# Singleton
_noaa_client: Optional[NoaaEnsoClient] = None


def get_noaa_enso_client() -> NoaaEnsoClient:
    global _noaa_client
    if _noaa_client is None:
        _noaa_client = NoaaEnsoClient()
    return _noaa_client
