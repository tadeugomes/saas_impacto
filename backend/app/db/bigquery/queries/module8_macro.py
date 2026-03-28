"""
Queries do Módulo 8 — Contexto Macroeconômico.

Diferente dos módulos 1-7 (BigQuery SQL), o Módulo 8 usa funções async
que consultam APIs externas (BACEN, IBGE). Essas funções são detectadas
pelo GenericIndicatorService via inspect.iscoroutinefunction().
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.clients.bacen import (
    SERIES_CAMBIO_PTAX,
    SERIES_IBC_BR,
    SERIES_IPCA_MENSAL,
    SERIES_SELIC_META,
    get_bacen_client,
)
from app.clients.ibge import get_ibge_client


async def query_selic_meta(
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-8.01: Taxa Selic Meta (% a.a.) — série histórica."""
    bacen = get_bacen_client()
    inicio, fim = _resolve_periodo(ano, ano_inicio, ano_fim)
    data = await bacen.consultar_serie(SERIES_SELIC_META, inicio, fim)
    return _normalize_serie(data, "selic_meta_aa")


async def query_ipca_acumulado(
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-8.02: IPCA acumulado 12 meses (%)."""
    bacen = get_bacen_client()
    # Buscar 13 meses extras para calcular acumulado 12m desde o início
    inicio, fim = _resolve_periodo(ano, ano_inicio, ano_fim, extra_meses=13)
    data = await bacen.consultar_serie(SERIES_IPCA_MENSAL, inicio, fim)

    if len(data) < 12:
        return _normalize_serie(data, "ipca_mensal")

    # Calcula acumulado 12m em janela deslizante
    resultado = []
    for i in range(12, len(data)):
        janela = data[i - 11 : i + 1]
        acum = 1.0
        for item in janela:
            try:
                acum *= 1 + float(item["valor"]) / 100
            except (ValueError, TypeError):
                continue
        acum_pct = round((acum - 1) * 100, 2)

        ponto = data[i]
        resultado.append({
            "data": ponto.get("data", ""),
            "ano": _extract_ano(ponto.get("data", "")),
            "mes": _extract_mes(ponto.get("data", "")),
            "ipca_acumulado_12m": acum_pct,
        })

    return resultado


async def query_cambio_ptax(
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-8.03: Câmbio USD/BRL (PTAX venda) — série diária."""
    bacen = get_bacen_client()
    inicio, fim = _resolve_periodo(ano, ano_inicio, ano_fim)
    data = await bacen.consultar_serie(SERIES_CAMBIO_PTAX, inicio, fim)
    return _normalize_serie(data, "cambio_ptax_venda")


async def query_ibc_br(
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-8.04: IBC-Br dessazonalizado (proxy PIB mensal)."""
    bacen = get_bacen_client()
    inicio, fim = _resolve_periodo(ano, ano_inicio, ano_fim)
    data = await bacen.consultar_serie(SERIES_IBC_BR, inicio, fim)
    return _normalize_serie(data, "ibc_br")


async def query_populacao_municipal(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-8.05: População do município portuário (IBGE atualizada)."""
    if not id_municipio:
        return []
    ibge = get_ibge_client()
    result = await ibge.populacao_municipio(id_municipio, ano)
    if result and result.get("valor") is not None:
        return [{
            "cod_ibge": result["cod_ibge"],
            "nome_municipio": result.get("nome_municipio", ""),
            "ano": result["ano"],
            "populacao": int(result["valor"]),
        }]
    return []


async def query_pib_per_capita_municipal(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-8.06: PIB per capita municipal (IBGE)."""
    if not id_municipio:
        return []

    from app.services.macro_economico_service import get_macro_service

    service = get_macro_service()
    ctx = await service.contexto_municipal(id_municipio, ano)
    if ctx.get("pib_per_capita_reais") is not None:
        return [{
            "cod_ibge": ctx["cod_ibge"],
            "nome_municipio": ctx.get("nome_municipio", ""),
            "ano": ctx.get("ano"),
            "pib_per_capita_reais": ctx["pib_per_capita_reais"],
            "populacao": ctx.get("populacao"),
            "pib_mil_reais": ctx.get("pib_mil_reais"),
        }]
    return []


# ============================================================================
# Helpers
# ============================================================================


def _resolve_periodo(
    ano: Optional[int],
    ano_inicio: Optional[int],
    ano_fim: Optional[int],
    extra_meses: int = 0,
) -> tuple[str, str]:
    """Converte parâmetros de período para formato dd/MM/yyyy do BACEN."""
    today = date.today()

    if ano:
        d_inicio = date(ano, 1, 1) - timedelta(days=30 * extra_meses)
        d_fim = date(ano, 12, 31) if ano < today.year else today
    elif ano_inicio and ano_fim:
        d_inicio = date(ano_inicio, 1, 1) - timedelta(days=30 * extra_meses)
        d_fim = date(ano_fim, 12, 31) if ano_fim < today.year else today
    else:
        d_inicio = today - timedelta(days=365 * 5 + 30 * extra_meses)
        d_fim = today

    return d_inicio.strftime("%d/%m/%Y"), d_fim.strftime("%d/%m/%Y")


def _normalize_serie(
    data: List[Dict[str, Any]], campo_valor: str
) -> List[Dict[str, Any]]:
    """Converte série BACEN {data, valor} para formato padronizado."""
    resultado = []
    for item in data:
        try:
            valor = float(item.get("valor", 0))
        except (ValueError, TypeError):
            valor = None

        resultado.append({
            "data": item.get("data", ""),
            "ano": _extract_ano(item.get("data", "")),
            "mes": _extract_mes(item.get("data", "")),
            campo_valor: valor,
        })
    return resultado


def _extract_ano(data_str: str) -> Optional[int]:
    """Extrai ano de data no formato dd/MM/yyyy."""
    try:
        return int(data_str.split("/")[2])
    except (IndexError, ValueError):
        return None


def _extract_mes(data_str: str) -> Optional[int]:
    """Extrai mês de data no formato dd/MM/yyyy."""
    try:
        return int(data_str.split("/")[1])
    except (IndexError, ValueError):
        return None


# Dicionário de queries do Módulo 8
QUERIES_MODULE_8 = {
    "IND-8.01": query_selic_meta,
    "IND-8.02": query_ipca_acumulado,
    "IND-8.03": query_cambio_ptax,
    "IND-8.04": query_ibc_br,
    "IND-8.05": query_populacao_municipal,
    "IND-8.06": query_pib_per_capita_municipal,
}
