"""
Cliente para a API da ANA (Agência Nacional de Águas).

A API retorna XML (Microsoft diffgram). Dados de cotas (nível) usam
tipoDados=1 com campos Cota01-Cota31; vazão usa tipoDados=3 com Vazao01-Vazao31.

Relevante para portos fluviais (Manaus, Porto Velho, Santarém, Belém etc.).
"""

from __future__ import annotations

import hashlib
import json
import logging
import xml.etree.ElementTree as ET
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
    """Cliente assíncrono para a API da ANA (resposta XML)."""

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

    async def _request_xml(self, path: str, params: dict) -> Optional[ET.Element]:
        """Faz GET e parseia resposta XML (a ANA não retorna JSON)."""
        import httpx

        client = await self._get_client()
        for attempt in range(self.MAX_RETRIES):
            try:
                resp = await client.get(path, params=params)
                resp.raise_for_status()
                return ET.fromstring(resp.text)
            except (httpx.HTTPStatusError, httpx.TransportError, ET.ParseError) as e:
                logger.warning("ana_xml_request_error path=%s attempt=%s err=%s", path, attempt + 1, e)
                if attempt < self.MAX_RETRIES - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
        return None

    async def consultar_nivel_rio(
        self,
        codigo_estacao: str,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Consulta nível do rio (cotas) em uma estação hidrológica.

        A API retorna XML com registros mensais contendo Cota01-Cota31.
        Extraímos o último valor disponível como nível atual.

        Returns:
            Lista de {"data": "...", "nivel_metros": 12.3, "vazao_m3s": 456.7}
        """
        cache_key = self._make_cache_key(
            "nivel", {"est": codigo_estacao, "ini": data_inicio, "fim": data_fim}
        )

        async def _fetch():
            params = {
                "codEstacao": codigo_estacao,
                "tipoDados": "1",  # 1=cotas (nível), 3=vazão
                "nivelConsistencia": "1",
            }
            if data_inicio:
                params["dataInicio"] = data_inicio
            if data_fim:
                params["dataFim"] = data_fim

            try:
                root = await self._request_xml("/HidroSerieHistorica", params)
                if root is None:
                    return []
                return self._parse_xml_cotas(root)
            except Exception as e:
                logger.warning("ana_api_error estacao=%s err=%s", codigo_estacao, e)
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
    def _parse_xml_cotas(root: ET.Element) -> List[Dict[str, Any]]:
        """
        Parseia XML diffgram da ANA para lista padronizada.

        O XML contém SerieHistorica com DataHora (mês/ano) e Cota01-Cota31
        (valores diários de nível em cm). Converte para metros.
        """
        result = []
        # Busca em todos os namespaces
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag != "SerieHistorica":
                continue

            # Extrai data do registro (mensal)
            data_hora = None
            cotas = {}
            vazoes = {}

            for child in elem:
                child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                text = (child.text or "").strip()

                if child_tag == "DataHora" and text:
                    data_hora = text[:10]  # YYYY-MM-DD
                elif child_tag.startswith("Cota") and not child_tag.endswith("Status"):
                    try:
                        dia = int(child_tag.replace("Cota", ""))
                        if text:
                            cotas[dia] = float(text)
                    except (ValueError, TypeError):
                        pass
                elif child_tag.startswith("Vazao") and not child_tag.endswith("Status"):
                    try:
                        dia = int(child_tag.replace("Vazao", ""))
                        if text:
                            vazoes[dia] = float(text)
                    except (ValueError, TypeError):
                        pass

            if not data_hora:
                continue

            # Para cada dia com dados, gera um registro
            for dia in sorted(set(list(cotas.keys()) + list(vazoes.keys()))):
                cota_cm = cotas.get(dia)
                vazao = vazoes.get(dia)
                result.append({
                    "data": f"{data_hora[:8]}{dia:02d}",
                    "nivel_metros": round(cota_cm / 100, 2) if cota_cm is not None else None,
                    "vazao_m3s": vazao,
                })

        return result

    @staticmethod
    def _parse_nivel_response(data: Any) -> List[Dict[str, Any]]:
        """Parse de resposta JSON (fallback para quando dados vêm como JSON)."""
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
