"""
Cliente para a API do INPE (Instituto Nacional de Pesquisas Espaciais).

Fornece dados de focos de incêndio próximos a instalações portuárias.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient
from app.config import get_settings

logger = logging.getLogger(__name__)

# Coordenadas aproximadas dos principais portos brasileiros
PORTO_COORDENADAS = {
    "Santos": {"lat": -23.9536, "lon": -46.3338},
    "Paranaguá": {"lat": -25.5163, "lon": -48.5225},
    "Rio Grande": {"lat": -32.0517, "lon": -52.0986},
    "Itajaí": {"lat": -26.9087, "lon": -48.6677},
    "Vitória": {"lat": -20.3155, "lon": -40.2922},
    "Tubarão": {"lat": -20.2866, "lon": -40.2405},
    "Rio de Janeiro": {"lat": -22.8912, "lon": -43.1729},
    "Itaguaí": {"lat": -22.9027, "lon": -43.7953},
    "Salvador": {"lat": -12.9744, "lon": -38.5127},
    "Aratu": {"lat": -12.7897, "lon": -38.4970},
    "Suape": {"lat": -8.3936, "lon": -34.9604},
    "Recife": {"lat": -8.0604, "lon": -34.8714},
    "Fortaleza": {"lat": -3.7204, "lon": -38.4826},
    "Mucuripe": {"lat": -3.7189, "lon": -38.4793},
    "Pecém": {"lat": -3.5340, "lon": -38.8114},
    "São Luís": {"lat": -2.5578, "lon": -44.2627},
    "Itaqui": {"lat": -2.5750, "lon": -44.3567},
    "Belém": {"lat": -1.4419, "lon": -48.4927},
    "Vila do Conde": {"lat": -1.5383, "lon": -48.7444},
    "Manaus": {"lat": -3.1340, "lon": -60.0227},
    "Santarém": {"lat": -2.4389, "lon": -54.7050},
    "Porto Velho": {"lat": -8.7619, "lon": -63.9039},
    "Maceió": {"lat": -9.6682, "lon": -35.7390},
    "Natal": {"lat": -5.7752, "lon": -35.2020},
    "Cabedelo": {"lat": -6.9678, "lon": -34.8391},
}


class InpeClient(BasePublicApiClient):
    """Cliente assíncrono para a API de queimadas do INPE."""

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.inpe_api_base_url,
            api_name="inpe",
            timeout=settings.public_api_timeout_seconds,
        )
        self._cache_ttl = settings.cache_ttl_ambiental

    def _make_cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps({"ep": endpoint, **params}, sort_keys=True)
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:inpe:{endpoint}:{digest}"

    async def buscar_focos_incendio(
        self,
        lat: float,
        lon: float,
        raio_km: int = 50,
        dias: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Busca focos de incêndio em um raio ao redor de coordenadas.

        Args:
            lat: Latitude do ponto central
            lon: Longitude do ponto central
            raio_km: Raio de busca em km (default: 50)
            dias: Últimos N dias (default: 7)

        Returns:
            Lista de focos com {lat, lon, data, satelite, municipio, distancia_km}
        """
        cache_key = self._make_cache_key(
            "focos",
            {"lat": round(lat, 2), "lon": round(lon, 2), "raio": raio_km, "dias": dias},
        )

        async def _fetch():
            params = {
                "latitude": lat,
                "longitude": lon,
                "raio": raio_km,
                "dias": dias,
                "formato": "json",
            }
            try:
                data = await self.get("/focos", params=params)
                if isinstance(data, list):
                    # Adiciona distância calculada a cada foco
                    for foco in data:
                        foco_lat = float(foco.get("lat", foco.get("latitude", 0)))
                        foco_lon = float(foco.get("lon", foco.get("longitude", 0)))
                        foco["distancia_km"] = round(
                            self._haversine(lat, lon, foco_lat, foco_lon), 1
                        )
                    return data
                return []
            except Exception as e:
                logger.warning("inpe_api_error", error=str(e))
                return []

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    async def calcular_risco_incendio(
        self,
        id_instalacao: str,
        raio_km: int = 50,
        dias: int = 7,
    ) -> Dict[str, Any]:
        """
        Calcula índice de risco de incêndio para uma instalação portuária.

        Returns:
            Dict com focos_detectados, risco_normalizado (0-1), classificacao
        """
        coords = PORTO_COORDENADAS.get(id_instalacao)
        if not coords:
            return {
                "id_instalacao": id_instalacao,
                "focos_detectados": None,
                "risco_normalizado": None,
                "classificacao": "sem_dados",
            }

        focos = await self.buscar_focos_incendio(
            coords["lat"], coords["lon"], raio_km, dias
        )

        n_focos = len(focos)

        # Normalização: 0 focos = risco 0, 50+ focos = risco 1
        if n_focos == 0:
            risco = 0.0
        elif n_focos >= 50:
            risco = 1.0
        else:
            risco = round(n_focos / 50, 3)

        classificacao = "baixo" if risco < 0.3 else "moderado" if risco < 0.7 else "alto"

        return {
            "id_instalacao": id_instalacao,
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "raio_busca_km": raio_km,
            "periodo_dias": dias,
            "focos_detectados": n_focos,
            "risco_normalizado": risco,
            "classificacao": classificacao,
        }

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distância entre dois pontos geográficos em km."""
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def get_coordenadas_porto(self, id_instalacao: str) -> Optional[Dict[str, float]]:
        """Retorna coordenadas de uma instalação portuária."""
        return PORTO_COORDENADAS.get(id_instalacao)


# Singleton
_inpe_client: Optional[InpeClient] = None


def get_inpe_client() -> InpeClient:
    global _inpe_client
    if _inpe_client is None:
        _inpe_client = InpeClient()
    return _inpe_client
