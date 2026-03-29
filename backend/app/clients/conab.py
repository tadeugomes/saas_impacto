"""
Cliente para dados de safra/produção agrícola.

Fonte primária: API SIDRA/IBGE (Produção Agrícola Municipal - PAM).
A CONAB não disponibiliza API JSON pública. Em vez de scraping do site
da CONAB, usa-se a tabela 1612 do SIDRA (IBGE), que contém produção
anual por produto e UF com cobertura 1974-presente.
Classificação c81 (lista de produtos da lavoura temporária).

Os dados de safra são o principal driver de tonelagem em portos
graneleiros (Santos, Paranaguá, Rio Grande, São Luís).
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient, PublicApiError
from app.config import get_settings

logger = logging.getLogger(__name__)

# Mapeamento de produtos para portos
PRODUTO_PORTO = {
    "soja": ["Santos", "Paranaguá", "Rio Grande", "São Luís", "Itaqui", "Santarém", "Barcarena"],
    "milho": ["Santos", "Paranaguá", "Rio Grande", "São Luís", "Itaqui"],
    "açúcar": ["Santos", "Paranaguá", "Maceió", "Recife", "Suape"],
    "café": ["Santos", "Vitória", "Rio de Janeiro"],
    "algodão": ["Santos", "Salvador", "Vitória"],
}

# Códigos SIDRA para produtos agrícolas.
# Estratégia: tenta tabela 1612/c81 primeiro; fallback para 5457/c782.
SIDRA_TABELAS = [
    # (tabela, classificação, códigos de produto)
    # Códigos descobertos via discover_sidra_codes.py (2026-03-28)
    ("1612", "c81", {
        # c81 = lavoura temporária (café não consta, é permanente)
        "soja": "2713",
        "milho": "2711",
        "açúcar": "2696",    # Cana-de-açúcar
        "algodão": "2689",   # Algodão herbáceo (em caroço)
    }),
    ("5457", "c782", {
        # c782 = lavoura temporária + permanente (inclui café)
        "soja": "40124",
        "milho": "40122",
        "açúcar": "40106",   # Cana-de-açúcar
        "café": "40139",     # Café (em grão) Total
        "algodão": "40099",  # Algodão herbáceo (em caroço)
    }),
]

# Atalho: primeiro mapeamento (usado em estimativa_safra que não precisa de fallback)
SIDRA_PRODUTO_CODIGO = SIDRA_TABELAS[0][2]

# UFs produtoras por produto
PRODUTO_UF_PRODUTORA = {
    "soja": ["MT", "PR", "RS", "GO", "MS", "BA", "MA", "TO", "PI"],
    "milho": ["MT", "PR", "GO", "MS", "MG", "RS"],
    "açúcar": ["SP", "GO", "MG", "MS", "PR", "AL", "PE"],
    "café": ["MG", "ES", "SP", "PR", "BA", "RO"],
}

# Código IBGE das UFs
UF_IBGE = {
    "RO": "11", "AC": "12", "AM": "13", "RR": "14", "PA": "15",
    "AP": "16", "TO": "17", "MA": "21", "PI": "22", "CE": "23",
    "RN": "24", "PB": "25", "PE": "26", "AL": "27", "SE": "28",
    "BA": "29", "MG": "31", "ES": "32", "RJ": "33", "SP": "35",
    "PR": "41", "SC": "42", "RS": "43", "MS": "50", "MT": "51",
    "GO": "52", "DF": "53",
}


class ConabClient(BasePublicApiClient):
    """Cliente para dados de produção agrícola via SIDRA/IBGE."""

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url="https://apisidra.ibge.gov.br",
            api_name="conab_sidra",
            timeout=settings.public_api_timeout_seconds,
        )
        self._cache_ttl = 86400  # 24h (dados anuais, baixa frequência)

    def _make_cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps({"ep": endpoint, **params}, sort_keys=True)
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:conab:{endpoint}:{digest}"

    async def estimativa_safra(
        self,
        produto: str,
        safra: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Produção agrícola por UF via SIDRA/IBGE (tabela 1612 - PAM).

        Tabela 1612: Produção agrícola municipal (lavoura temporária)
        Variável 214: Quantidade produzida (toneladas)

        Args:
            produto: Nome do produto (soja, milho, açúcar, café)
            safra: Não usado (SIDRA retorna último ano disponível)

        Returns:
            Lista de {uf, producao_mil_ton}
        """
        codigo_produto = SIDRA_PRODUTO_CODIGO.get(produto)
        if not codigo_produto:
            logger.warning("conab: produto '%s' sem código SIDRA", produto)
            return []

        cache_key = self._make_cache_key("sidra_pam", {"prod": produto})

        async def _fetch():
            # SIDRA API: tabela 1612, variável 214 (qtd produzida),
            # nível territorial 3 (UF), último período disponível
            path = (
                f"/values"
                f"/t/1612"             # Tabela PAM lavoura temporária
                f"/n3/all"             # Todas UFs
                f"/v/214"              # Variável: quantidade produzida
                f"/p/last%201"         # Último período
                f"/c81/{codigo_produto}"   # Produto (classif. c81)
            )
            try:
                data = await self.get(path)
                if not isinstance(data, list) or len(data) < 2:
                    return []
                # Primeira linha é header, demais são dados
                results = []
                for row in data[1:]:
                    uf_nome = row.get("D1N", "")
                    valor_str = row.get("V", "0")
                    if valor_str == "-" or valor_str == "..." or not valor_str:
                        continue
                    try:
                        producao_ton = float(valor_str)
                        results.append({
                            "uf": uf_nome[:2].upper() if len(uf_nome) >= 2 else uf_nome,
                            "uf_nome": uf_nome,
                            "producao_mil_ton": round(producao_ton / 1000, 1),
                        })
                    except (ValueError, TypeError):
                        continue
                return results
            except PublicApiError as e:
                logger.warning("conab_sidra_error produto=%s: %s", produto, e)
                return []

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    async def producao_por_uf(
        self,
        produto: str,
        uf: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Produção por UF em mil toneladas (último ano disponível).
        """
        dados = await self.estimativa_safra(produto)

        result = {}
        for item in dados:
            item_uf = str(item.get("uf", "")).upper()
            if uf and item_uf != uf.upper():
                continue
            try:
                prod = float(item.get("producao_mil_ton", 0) or 0)
                result[item_uf] = result.get(item_uf, 0) + prod
            except (ValueError, TypeError):
                continue

        return result

    async def serie_producao_anual(
        self,
        produto: str,
        n_anos: int = 15,
    ) -> List[Dict[str, Any]]:
        """
        Série temporal de produção total (Brasil) por ano, últimos n_anos.

        Busca no nível n3 (UF) e agrega para total nacional, porque
        o nível n1 (Brasil) retorna V="..." (dados suprimidos) em
        várias combinações tabela/classificação do SIDRA.

        Tenta múltiplas tabelas/classificações em sequência (fallback).

        Returns:
            Lista de {ano, producao_mil_ton}
        """
        cache_key = self._make_cache_key("sidra_pam_serie_n3v2", {"prod": produto, "n": n_anos})

        async def _fetch():
            for tabela, classif, codigos in SIDRA_TABELAS:
                codigo_produto = codigos.get(produto)
                if not codigo_produto:
                    continue

                path = (
                    f"/values"
                    f"/t/{tabela}"
                    f"/n3/all"                    # Todas UFs (nível 3)
                    f"/v/214"                     # Quantidade produzida
                    f"/p/last%20{n_anos}"         # Últimos N períodos
                    f"/{classif}/{codigo_produto}"
                )
                try:
                    data = await self.get(path)
                except PublicApiError as e:
                    logger.warning(
                        "conab_sidra_serie: %s t/%s/%s/%s falhou: %s",
                        produto, tabela, classif, codigo_produto, e,
                    )
                    continue

                if not isinstance(data, list) or len(data) < 2:
                    logger.warning(
                        "conab_sidra_serie: %s t/%s resposta vazia",
                        produto, tabela,
                    )
                    continue

                logger.info(
                    "conab_sidra_serie: %s t/%s/%s n3 => %d linhas brutas",
                    produto, tabela, classif, len(data) - 1,
                )

                # Log da primeira linha de dados para debug
                if len(data) > 1:
                    first = data[1]
                    logger.info(
                        "conab_sidra_serie: primeira linha: D1N=%s D2N=%s D3N=%s D4N=%s V=%s",
                        first.get("D1N"), first.get("D2N"), first.get("D3N"),
                        first.get("D4N"), first.get("V"),
                    )

                # Agrega produção por ano (soma de todas as UFs)
                producao_por_ano: Dict[int, float] = {}
                linhas_validas = 0
                for row in data[1:]:
                    ano_str = ""
                    for key in ("D2N", "D3N", "D4N", "D1N"):
                        val = str(row.get(key, "")).strip()
                        if val and val[:4].isdigit() and len(val[:4]) == 4:
                            ano_str = val[:4]
                            break
                    if not ano_str:
                        for key in ("D2C", "D3C", "D4C"):
                            val = str(row.get(key, "")).strip()
                            if val and val.isdigit() and len(val) == 4:
                                ano_str = val
                                break

                    valor_str = str(row.get("V", "0")).strip()
                    if valor_str in ("-", "...", "X", "") or not valor_str:
                        continue
                    try:
                        ano = int(ano_str)
                        producao_ton = float(valor_str)
                        producao_por_ano[ano] = producao_por_ano.get(ano, 0.0) + producao_ton
                        linhas_validas += 1
                    except (ValueError, TypeError):
                        continue

                if producao_por_ano:
                    results = [
                        {"ano": ano, "producao_mil_ton": round(total / 1000, 1)}
                        for ano, total in sorted(producao_por_ano.items())
                    ]
                    logger.info(
                        "conab_sidra_serie: %s t/%s => %d anos (%d linhas UF válidas)",
                        produto, tabela, len(results), linhas_validas,
                    )
                    return results

                logger.warning(
                    "conab_sidra_serie: %s t/%s/%s 0 registros válidos, tentando fallback",
                    produto, tabela, classif,
                )

            logger.warning("conab_sidra_serie: %s => todas as tabelas falharam", produto)
            return []

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    def get_produtos_porto(self, id_instalacao: str) -> List[str]:
        """Produtos agrícolas relevantes para um porto."""
        return [
            prod for prod, portos in PRODUTO_PORTO.items()
            if id_instalacao in portos
        ]


# Singleton
_conab_client: Optional[ConabClient] = None


def get_conab_client() -> ConabClient:
    global _conab_client
    if _conab_client is None:
        _conab_client = ConabClient()
    return _conab_client
