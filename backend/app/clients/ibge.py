"""
Cliente para as APIs do IBGE (Instituto Brasileiro de Geografia e Estatística).

APIs utilizadas:
- Localidades: municípios, estados, regiões
- Agregados: PIB municipal, população estimada, IPCA regional
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient
from app.config import get_settings

logger = logging.getLogger(__name__)

# Agregados prioritários
AGREGADO_PIB_MUNICIPAL = 5938
AGREGADO_POPULACAO_ESTIMADA = 6579


class IbgeClient(BasePublicApiClient):
    """Cliente assíncrono para as APIs do IBGE."""

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.ibge_api_base_url,
            api_name="ibge",
            timeout=settings.public_api_timeout_seconds,
        )
        self._cache_ttl = settings.cache_ttl_ibge

    def _make_cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps(
            {"endpoint": endpoint, **params}, sort_keys=True
        )
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:ibge:{endpoint}:{digest}"

    async def buscar_municipios(self, uf: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista municípios, opcionalmente filtrados por UF.

        Args:
            uf: Sigla da UF (ex: "SP", "RJ") ou None para todos

        Returns:
            Lista de {"id": 3550308, "nome": "São Paulo", ...}
        """
        if uf:
            path = f"/localidades/estados/{uf}/municipios"
        else:
            path = "/localidades/municipios"

        # Usa base v1 para localidades
        cache_key = self._make_cache_key("municipios", {"uf": uf or "todos"})

        async def _fetch():
            # API de localidades usa v1, não v3
            from app.clients.base import BasePublicApiClient
            settings = get_settings()
            localidades_url = settings.ibge_api_base_url.replace("/v3", "/v1")
            client = await self._get_client()
            resp = await client.get(
                localidades_url.rstrip("/") + path
            )
            resp.raise_for_status()
            return resp.json()

        return await self.get_cached(cache_key, _fetch, ttl=86400)

    async def consultar_agregado(
        self,
        agregado_id: int,
        variavel_id: int,
        localidade: str,
        periodo: str = "last",
    ) -> List[Dict[str, Any]]:
        """
        Consulta um agregado estatístico do IBGE.

        Args:
            agregado_id: ID do agregado (ex: 5938 para PIB)
            variavel_id: ID da variável
            localidade: Código da localidade (ex: "N6[3550308]" para município)
            periodo: Período (ex: "last", "2020", "2015-2023")

        Returns:
            Lista de resultados com {classificacao, serie, ...}
        """
        path = f"/agregados/{agregado_id}/periodos/{periodo}/variaveis/{variavel_id}"
        params = {"localidades": localidade}

        cache_key = self._make_cache_key(
            f"agregado_{agregado_id}",
            {"variavel": variavel_id, "localidade": localidade, "periodo": periodo},
        )

        async def _fetch():
            return await self.get(path, params=params)

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    async def populacao_municipio(
        self, cod_ibge: str, ano: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retorna a população estimada de um município.

        Args:
            cod_ibge: Código IBGE de 7 dígitos
            ano: Ano de referência (None = mais recente)

        Returns:
            {"cod_ibge": "...", "ano": 2024, "populacao": 12345678}
        """
        periodo = str(ano) if ano else "last"
        localidade = f"N6[{cod_ibge}]"

        try:
            data = await self.consultar_agregado(
                agregado_id=AGREGADO_POPULACAO_ESTIMADA,
                variavel_id=9324,  # População residente estimada
                localidade=localidade,
                periodo=periodo,
            )
            return self._extract_valor(data, cod_ibge)
        except Exception as e:
            logger.warning(
                "ibge_populacao_error",
                cod_ibge=cod_ibge,
                ano=ano,
                error=str(e),
            )
            return None

    async def pib_municipio(
        self, cod_ibge: str, ano: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retorna o PIB municipal.

        Args:
            cod_ibge: Código IBGE de 7 dígitos
            ano: Ano de referência

        Returns:
            {"cod_ibge": "...", "ano": 2021, "pib_mil_reais": 123456.78}
        """
        periodo = str(ano) if ano else "last"
        localidade = f"N6[{cod_ibge}]"

        try:
            data = await self.consultar_agregado(
                agregado_id=AGREGADO_PIB_MUNICIPAL,
                variavel_id=37,  # PIB a preços correntes (R$ 1.000)
                localidade=localidade,
                periodo=periodo,
            )
            result = self._extract_valor(data, cod_ibge)
            if result and result.get("valor") is not None:
                result["pib_mil_reais"] = result.pop("valor")
            return result
        except Exception as e:
            logger.warning(
                "ibge_pib_error",
                cod_ibge=cod_ibge,
                ano=ano,
                error=str(e),
            )
            return None

    @staticmethod
    def _extract_valor(
        data: Any, cod_ibge: str
    ) -> Optional[Dict[str, Any]]:
        """Extrai valor numérico da resposta de agregados do IBGE."""
        if not data or not isinstance(data, list):
            return None

        for item in data:
            resultados = item.get("resultados", [])
            for resultado in resultados:
                series = resultado.get("series", [])
                for serie in series:
                    localidade = serie.get("localidade", {})
                    loc_id = str(localidade.get("id", ""))
                    if loc_id == str(cod_ibge):
                        serie_data = serie.get("serie", {})
                        for ano_str, valor_str in serie_data.items():
                            try:
                                return {
                                    "cod_ibge": cod_ibge,
                                    "nome_municipio": localidade.get("nome", ""),
                                    "ano": int(ano_str),
                                    "valor": float(valor_str) if valor_str and valor_str != "..." else None,
                                }
                            except (ValueError, TypeError):
                                continue
        return None


# Singleton
_ibge_client: Optional[IbgeClient] = None


def get_ibge_client() -> IbgeClient:
    global _ibge_client
    if _ibge_client is None:
        _ibge_client = IbgeClient()
    return _ibge_client
