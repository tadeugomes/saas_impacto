"""
Cliente para dados meteorológicos históricos via Open-Meteo.

API: https://archive-api.open-meteo.com/v1/archive
Autenticação: Nenhuma (API pública, gratuita para uso não-comercial).
Documentação: https://open-meteo.com/en/docs/historical-weather-api

Substitui o antigo cliente INMET (apitempo.inmet.gov.br), que está
fora do ar desde 2025. A interface pública é idêntica: os mesmos
métodos e mapeamentos de porto são mantidos para compatibilidade
com o feature_builder.

Variáveis diárias usadas:
  - precipitation_sum: precipitação total do dia (mm)
  - temperature_2m_max: temperatura máxima (°C)
  - temperature_2m_min: temperatura mínima (°C)
  - relative_humidity_2m_mean: umidade relativa média (%)
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient, PublicApiError
from app.config import get_settings

logger = logging.getLogger(__name__)

# Coordenadas dos pontos de referência para cada porto.
# Cada porto tem um ponto principal (corredor logístico ou cidade-porto)
# e opcionalmente um ponto em região produtora.
PORTO_PONTOS_METEO = {
    "Santos": [
        {"lat": -23.96, "lon": -46.33, "nome": "Santos", "tipo": "porto"},
        {"lat": -22.91, "lon": -47.06, "nome": "Campinas", "tipo": "regiao_produtora"},
    ],
    "Paranaguá": [
        {"lat": -25.52, "lon": -48.51, "nome": "Paranaguá", "tipo": "porto"},
        {"lat": -23.31, "lon": -51.16, "nome": "Londrina", "tipo": "regiao_produtora"},
    ],
    "Rio Grande": [
        {"lat": -32.03, "lon": -52.10, "nome": "Rio Grande", "tipo": "porto"},
    ],
    "Itaqui": [
        {"lat": -2.55, "lon": -44.28, "nome": "São Luís", "tipo": "porto"},
    ],
    "São Luís": [
        {"lat": -2.55, "lon": -44.28, "nome": "São Luís", "tipo": "porto"},
    ],
    "Tubarão": [
        {"lat": -20.32, "lon": -40.34, "nome": "Vitória", "tipo": "porto"},
    ],
    "Vitória": [
        {"lat": -20.32, "lon": -40.34, "nome": "Vitória", "tipo": "porto"},
    ],
    "Manaus": [
        {"lat": -3.12, "lon": -60.02, "nome": "Manaus", "tipo": "porto"},
    ],
}

# Mapeamento de compatibilidade: código INMET antigo → coordenadas
# Mantido para eventual código legado que referencie estações por código.
_ESTACAO_COORDS = {
    "A701": {"lat": -23.50, "lon": -46.62},   # SP Mirante
    "A711": {"lat": -22.91, "lon": -47.06},   # Campinas
    "A807": {"lat": -25.43, "lon": -49.27},   # Curitiba
    "A836": {"lat": -23.31, "lon": -51.16},   # Londrina
    "A801": {"lat": -30.05, "lon": -51.17},   # Porto Alegre
    "A203": {"lat": -2.55,  "lon": -44.28},   # São Luís
    "A612": {"lat": -20.32, "lon": -40.34},   # Vitória
    "A101": {"lat": -3.12,  "lon": -60.02},   # Manaus
    "A901": {"lat": -15.60, "lon": -56.10},   # Cuiabá
    "A002": {"lat": -16.67, "lon": -49.25},   # Goiânia
    "A510": {"lat": -19.93, "lon": -43.94},   # Belo Horizonte
}

# Compatibilidade: mapeamento antigo porto → estações (para get_estacoes_porto)
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


class InmetClient(BasePublicApiClient):
    """
    Cliente de dados meteorológicos históricos via Open-Meteo.

    Mantém o nome InmetClient e a interface pública original para
    compatibilidade com feature_builder e main.py.
    """

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url="https://archive-api.open-meteo.com",
            api_name="open_meteo",
            timeout=settings.public_api_timeout_seconds,
        )
        self._cache_ttl = settings.cache_ttl_ambiental  # 1h

    def _make_cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps({"ep": endpoint, **params}, sort_keys=True)
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:open_meteo:{endpoint}:{digest}"

    async def dados_estacao(
        self,
        codigo_estacao: str,
        data_inicio: str,
        data_fim: str,
    ) -> List[Dict[str, Any]]:
        """
        Busca dados meteorológicos diários via Open-Meteo.

        Aceita código de estação INMET (convertido para lat/lon)
        para compatibilidade.

        Args:
            codigo_estacao: Código INMET (ex: A701) ou "lat,lon"
            data_inicio: YYYY-MM-DD
            data_fim: YYYY-MM-DD

        Returns:
            Lista de {data, precipitacao_mm, temp_max, temp_min, umidade_pct}
        """
        coords = self._resolve_coords(codigo_estacao)
        if not coords:
            logger.warning("open_meteo: estação '%s' sem coordenadas", codigo_estacao)
            return []

        cache_key = self._make_cache_key(
            "archive",
            {"lat": coords["lat"], "lon": coords["lon"], "ini": data_inicio, "fim": data_fim},
        )

        async def _fetch():
            params = (
                f"?latitude={coords['lat']}"
                f"&longitude={coords['lon']}"
                f"&start_date={data_inicio}"
                f"&end_date={data_fim}"
                f"&daily=precipitation_sum,temperature_2m_max,temperature_2m_min"
                f"&timezone=America%2FSao_Paulo"
            )
            path = f"/v1/archive{params}"
            try:
                data = await self.get(path)
                if not isinstance(data, dict) or "daily" not in data:
                    logger.warning("open_meteo: resposta sem 'daily' para %s", codigo_estacao)
                    return []

                daily = data["daily"]
                dates = daily.get("time", [])
                precip = daily.get("precipitation_sum", [])
                tmax = daily.get("temperature_2m_max", [])
                tmin = daily.get("temperature_2m_min", [])

                results = []
                for i, dt in enumerate(dates):
                    results.append({
                        "data": dt,
                        "precipitacao_mm": _safe_float(precip[i] if i < len(precip) else None),
                        "temp_max": _safe_float(tmax[i] if i < len(tmax) else None),
                        "temp_min": _safe_float(tmin[i] if i < len(tmin) else None),
                        "umidade_pct": None,  # Open-Meteo archive não tem umidade no plano gratuito
                    })
                logger.info(
                    "open_meteo: %s %s..%s => %d dias",
                    codigo_estacao, data_inicio, data_fim, len(results),
                )
                return results
            except PublicApiError as e:
                logger.warning("open_meteo_error est=%s: %s", codigo_estacao, e)
                return []

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    async def precipitacao_acumulada_mensal(
        self,
        codigo_estacao: str,
        ano: int,
    ) -> List[Dict[str, Any]]:
        """
        Precipitação acumulada por mês.

        Returns:
            Lista de {ano, mes, precipitacao_acumulada_mm}
        """
        from datetime import date

        data_inicio = f"{ano}-01-01"
        # Open-Meteo Historical API só aceita datas até ontem.
        # Para o ano corrente, limita ao dia anterior.
        hoje = date.today()
        if ano >= hoje.year:
            ontem = hoje.replace(day=max(1, hoje.day - 1))
            data_fim = ontem.isoformat()
        else:
            data_fim = f"{ano}-12-31"
        dados = await self.dados_estacao(codigo_estacao, data_inicio, data_fim)

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

    def _resolve_coords(self, codigo_estacao: str) -> Optional[Dict[str, float]]:
        """Converte código de estação INMET em coordenadas."""
        if codigo_estacao in _ESTACAO_COORDS:
            return _ESTACAO_COORDS[codigo_estacao]
        # Tenta formato "lat,lon"
        if "," in codigo_estacao:
            parts = codigo_estacao.split(",")
            try:
                return {"lat": float(parts[0]), "lon": float(parts[1])}
            except (ValueError, IndexError):
                pass
        return None


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
