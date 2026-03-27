"""
Indicadores externos para o Módulo 6 — Finanças Públicas.

Funções async que consultam TCEs e Portal da Transparência
para complementar os dados FINBRA existentes via BigQuery.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.clients.tce import get_tce_client, get_uf_for_porto, TCE_REGISTRY
from app.clients.transparencia import get_transparencia_client


async def query_autonomia_fiscal(
    id_municipio: Optional[str] = None,
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-6.06: Autonomia Fiscal — Receita própria / Receita total."""
    uf = get_uf_for_porto(id_instalacao) if id_instalacao else None
    if not uf or uf not in TCE_REGISTRY:
        return [{
            "id_municipio": id_municipio,
            "autonomia_fiscal": None,
            "nota": f"TCE não disponível para UF" + (f" ({uf})" if uf else ""),
        }]

    if not id_municipio or not ano:
        return []

    tce = get_tce_client(uf)
    resultado = await tce.calcular_autonomia_fiscal(id_municipio, ano)
    resultado["id_instalacao"] = id_instalacao
    return [resultado]


async def query_investimento_per_capita(
    id_municipio: Optional[str] = None,
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-6.07: Investimento per capita — Despesas de capital / População."""
    uf = get_uf_for_porto(id_instalacao) if id_instalacao else None
    if not uf or uf not in TCE_REGISTRY:
        return [{
            "id_municipio": id_municipio,
            "investimento_per_capita": None,
            "nota": "TCE não disponível para esta UF",
        }]

    if not id_municipio or not ano:
        return []

    tce = get_tce_client(uf)
    despesas = await tce.consultar_despesas(id_municipio, ano)

    despesas_capital = sum(
        float(d.get("valor_pago", d.get("empenhado", 0)) or 0)
        for d in despesas
        if str(d.get("categoria", d.get("grupo", ""))).lower() in (
            "investimentos", "inversões financeiras", "capital",
        )
    )

    # Busca população via IBGE
    from app.clients.ibge import get_ibge_client
    ibge = get_ibge_client()
    pop_data = await ibge.populacao_municipio(id_municipio, ano)
    populacao = int(pop_data.get("valor", 0)) if pop_data and pop_data.get("valor") else None

    per_capita = round(despesas_capital / populacao, 2) if populacao and populacao > 0 else None

    return [{
        "id_municipio": id_municipio,
        "id_instalacao": id_instalacao,
        "ano": ano,
        "despesas_capital": despesas_capital,
        "populacao": populacao,
        "investimento_per_capita": per_capita,
    }]


async def query_execucao_orcamentaria(
    id_municipio: Optional[str] = None,
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-6.08: Eficiência na Execução Orçamentária — Executado / Autorizado."""
    uf = get_uf_for_porto(id_instalacao) if id_instalacao else None
    if not uf or uf not in TCE_REGISTRY:
        return [{
            "id_municipio": id_municipio,
            "eficiencia_execucao": None,
            "nota": "TCE não disponível para esta UF",
        }]

    if not id_municipio or not ano:
        return []

    tce = get_tce_client(uf)
    resultado = await tce.calcular_execucao_orcamentaria(id_municipio, ano)
    resultado["id_instalacao"] = id_instalacao
    return [resultado]


async def query_investimento_federal(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-6.09: Investimento Federal no Município Portuário."""
    if not id_municipio or not ano:
        return []

    transp = get_transparencia_client()

    # Busca população para calcular per capita
    from app.clients.ibge import get_ibge_client
    ibge = get_ibge_client()
    pop_data = await ibge.populacao_municipio(id_municipio, ano)
    populacao = int(pop_data.get("valor", 0)) if pop_data and pop_data.get("valor") else None

    resultado = await transp.calcular_investimento_federal(
        id_municipio, ano, populacao
    )
    return [resultado]


async def query_emendas_parlamentares(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-6.10: Emendas Parlamentares no município."""
    if not id_municipio or not ano:
        return []

    transp = get_transparencia_client()
    emendas = await transp.buscar_emendas_municipio(id_municipio, ano)

    valor_total = sum(
        float(e.get("valor", e.get("valorEmpenhado", 0)) or 0) for e in emendas
    )

    return [{
        "cod_municipio": id_municipio,
        "ano": ano,
        "qtd_emendas": len(emendas),
        "valor_total_emendas": valor_total,
    }]


async def query_servidores_federais(
    id_municipio: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """IND-6.11: Servidores Federais no município (proxy presença federal)."""
    if not id_municipio:
        return []

    transp = get_transparencia_client()
    resultado = await transp.buscar_servidores_municipio(id_municipio)
    return [resultado]


QUERIES_MODULE_6_EXTERNAL = {
    "IND-6.12": query_autonomia_fiscal,
    "IND-6.13": query_investimento_per_capita,
    "IND-6.14": query_execucao_orcamentaria,
    "IND-6.15": query_investimento_federal,
    "IND-6.16": query_emendas_parlamentares,
    "IND-6.17": query_servidores_federais,
}
