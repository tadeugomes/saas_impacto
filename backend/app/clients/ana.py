"""
Cliente para a API da ANA (Agência Nacional de Águas).

Fornece dados hidrológicos (nível de rios, vazão, chuva) relevantes
para portos fluviais (Manaus, Porto Velho, Santarém, Belém etc.).
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient
from app.config import get_settings

logger = logging.getLogger(__name__)

# Estações hidrológicas próximas a portos fluviais
PORTO_TO_ESTACAO_HIDRO = {
    "Manaus": {"codigo": "14990000", "rio": "Rio Negro", "nome": "Manaus"},
    "Porto Velho": {"codigo": "15400000", "rio": "Rio Madeira", "nome": "Porto Velho"},
    "Santarém": {"codigo": "17900000", "rio": "Rio Tapajós", "nome": "Santarém"},
    "Belém": {"codigo": "31490000", "rio": "Rio Guamá", "nome": "Belém"},
    "Itacoatiara": {"codigo": "16030000", "rio": "Rio Amazonas", "nome": "Itacoatiara"},
    "Vila do Conde": {"codigo": "31480000", "rio": "Rio Pará", "nome": "Vila do Conde"},
}


class AnaClient(BasePublicApiClient):
    """Cliente assíncrono para a API da ANA."""

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.ana_api_base_url,
            api_name="ana",
            timeout=settings.public_api_timeout_seconds,
        )
        self._cache_ttl = settings.cache_ttl_ambiental

    def _make_cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps({"ep": endpoint, **params}, sort_keys=True)
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:ana:{endpoint}:{digest}"

    async def consultar_nivel_rio(
        self,
        codigo_estacao: str,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Consulta nível do rio em uma estação hidrológica.

        Args:
            codigo_estacao: Código da estação ANA
            data_inicio: Data início (YYYY-MM-DD)
            data_fim: Data fim (YYYY-MM-DD)

        Returns:
            Lista de {"data": "...", "nivel_metros": 12.3, "vazao_m3s": 456.7}
        """
        cache_key = self._make_cache_key(
            "nivel", {"est": codigo_estacao, "ini": data_inicio, "fim": data_fim}
        )

        async def _fetch():
            params = {"codEstacao": codigo_estacao, "formato": "json"}
            if data_inicio:
                params["dataInicio"] = data_inicio
            if data_fim:
                params["dataFim"] = data_fim
            try:
                data = await self.get("/HidroSerieHistorica", params=params)
                return self._parse_nivel_response(data)
            except Exception as e:
                logger.warning(
                    "ana_api_error", estacao=codigo_estacao, error=str(e)
                )
                return []

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    async def calcular_risco_hidrico(
        self,
        codigo_estacao: str,
        calado_minimo_metros: float,
    ) -> Dict[str, Any]:
        """
        Calcula índice de risco hídrico: nível do rio vs. calado mínimo.

        Returns:
            Dict com nivel_atual, calado_minimo, risco_normalizado (0-1)
        """
        dados = await self.consultar_nivel_rio(codigo_estacao)

        if not dados:
            return {
                "codigo_estacao": codigo_estacao,
                "nivel_atual_metros": None,
                "calado_minimo_metros": calado_minimo_metros,
                "risco_normalizado": None,
                "classificacao": "sem_dados",
            }

        nivel_atual = dados[-1].get("nivel_metros")
        if nivel_atual is None:
            return {
                "codigo_estacao": codigo_estacao,
                "nivel_atual_metros": None,
                "calado_minimo_metros": calado_minimo_metros,
                "risco_normalizado": None,
                "classificacao": "sem_dados",
            }

        # Normaliza: risco 0 quando nível >> calado, risco 1 quando nível <= calado
        margem = nivel_atual - calado_minimo_metros
        if margem <= 0:
            risco = 1.0
        elif margem >= calado_minimo_metros:
            risco = 0.0
        else:
            risco = round(1 - (margem / calado_minimo_metros), 3)

        classificacao = "baixo" if risco < 0.3 else "moderado" if risco < 0.7 else "alto"

        return {
            "codigo_estacao": codigo_estacao,
            "nivel_atual_metros": nivel_atual,
            "calado_minimo_metros": calado_minimo_metros,
            "margem_metros": round(margem, 2),
            "risco_normalizado": risco,
            "classificacao": classificacao,
        }

    def get_estacao_for_porto(self, id_instalacao: str) -> Optional[Dict[str, str]]:
        """Mapeia instalação portuária para estação hidrológica."""
        return PORTO_TO_ESTACAO_HIDRO.get(id_instalacao)

    @staticmethod
    def _parse_nivel_response(data: Any) -> List[Dict[str, Any]]:
        """Parse da resposta XML/JSON da ANA para formato padronizado."""
        if isinstance(data, list):
            result = []
            for item in data:
                try:
                    result.append({
                        "data": str(item.get("Data", item.get("data", ""))),
                        "nivel_metros": float(item.get("Nivel", item.get("nivel", 0))),
                        "vazao_m3s": float(item.get("Vazao", item.get("vazao", 0))) if item.get("Vazao") or item.get("vazao") else None,
                    })
                except (ValueError, TypeError):
                    continue
            return result
        return []


# Singleton
_ana_client: Optional[AnaClient] = None


def get_ana_client() -> AnaClient:
    global _ana_client
    if _ana_client is None:
        _ana_client = AnaClient()
    return _ana_client
