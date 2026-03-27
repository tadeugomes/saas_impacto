"""
Serviço de deflação IPCA e conversão cambial.

Transversal a todos os módulos — permite que qualquer série monetária
seja convertida para valores reais (deflacionados) ou para USD.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.clients.bacen import BacenClient, SERIES_CAMBIO_PTAX, get_bacen_client

logger = logging.getLogger(__name__)


class DeflationService:
    """Deflação IPCA e conversão cambial para análise em termos reais."""

    def __init__(self, bacen: Optional[BacenClient] = None):
        self.bacen = bacen or get_bacen_client()

    async def deflacionar_serie(
        self,
        valores: List[Dict[str, Any]],
        campo_valor: str,
        campo_ano: str,
        ano_base: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Deflaciona uma série monetária usando IPCA.

        Adiciona campo '{campo_valor}_real' a cada registro.

        Args:
            valores: Lista de dicts com os dados
            campo_valor: Nome do campo com valor nominal (ex: "receita")
            campo_ano: Nome do campo com o ano (ex: "ano")
            ano_base: Ano base para deflação (default: ano mais recente)

        Returns:
            Lista original com campo adicional de valor real
        """
        if not valores:
            return valores

        # Determina range de anos
        anos = []
        for v in valores:
            try:
                anos.append(int(v.get(campo_ano, 0)))
            except (ValueError, TypeError):
                continue

        if not anos:
            return valores

        ano_min, ano_max = min(anos), max(anos)
        if ano_base is None:
            ano_base = ano_max

        # Obtém deflator
        deflator = await self.bacen.get_deflator_ipca(
            ano_base=ano_base,
            ano_inicio=ano_min,
            ano_fim=ano_max,
        )

        # Aplica deflação
        campo_real = f"{campo_valor}_real"
        resultado = []
        for v in valores:
            registro = dict(v)
            try:
                ano = int(v.get(campo_ano, 0))
                valor_nominal = float(v.get(campo_valor, 0))
                fator = deflator.get(ano, 1.0)
                registro[campo_real] = round(valor_nominal * fator, 2)
                registro["deflator_ipca"] = fator
                registro["ano_base_deflacao"] = ano_base
            except (ValueError, TypeError):
                registro[campo_real] = None
                registro["deflator_ipca"] = None
                registro["ano_base_deflacao"] = ano_base
            resultado.append(registro)

        return resultado

    async def converter_para_usd(
        self,
        valores: List[Dict[str, Any]],
        campo_valor_brl: str,
        campo_ano: str,
    ) -> List[Dict[str, Any]]:
        """
        Converte valores BRL para USD usando PTAX média anual.

        Adiciona campo '{campo_valor_brl}_usd' a cada registro.
        """
        if not valores:
            return valores

        # Obtém câmbio PTAX para os anos necessários
        anos = set()
        for v in valores:
            try:
                anos.add(int(v.get(campo_ano, 0)))
            except (ValueError, TypeError):
                continue

        if not anos:
            return valores

        ptax_por_ano: Dict[int, float] = {}
        for ano in sorted(anos):
            inicio = f"01/01/{ano}"
            fim = f"31/12/{ano}"
            try:
                data = await self.bacen.consultar_serie(
                    SERIES_CAMBIO_PTAX, inicio, fim
                )
                if data:
                    total = sum(float(d["valor"]) for d in data)
                    ptax_por_ano[ano] = total / len(data)
            except Exception:
                continue

        # Aplica conversão
        campo_usd = f"{campo_valor_brl}_usd"
        resultado = []
        for v in valores:
            registro = dict(v)
            try:
                ano = int(v.get(campo_ano, 0))
                valor_brl = float(v.get(campo_valor_brl, 0))
                ptax = ptax_por_ano.get(ano)
                if ptax and ptax > 0:
                    registro[campo_usd] = round(valor_brl / ptax, 2)
                    registro["ptax_media_ano"] = round(ptax, 4)
                else:
                    registro[campo_usd] = None
                    registro["ptax_media_ano"] = None
            except (ValueError, TypeError):
                registro[campo_usd] = None
                registro["ptax_media_ano"] = None
            resultado.append(registro)

        return resultado


# Singleton
_deflation_service: Optional[DeflationService] = None


def get_deflation_service() -> DeflationService:
    global _deflation_service
    if _deflation_service is None:
        _deflation_service = DeflationService()
    return _deflation_service
