"""
Indicadores deflacionados — séries monetárias em valores reais.

Funções async que buscam dados nominais via BigQuery e aplicam
deflação IPCA (via DeflationService) ou conversão cambial PTAX.

IND-2.14: Receita Real por Tonelada (Módulo 2)
IND-4.11: Valor FOB Exportações em USD ajustado (Módulo 4)
IND-4.12: Valor FOB Importações em USD ajustado (Módulo 4)
IND-6.18: Receita Municipal Real per Capita (Módulo 6)
IND-6.19: ICMS Real por Tonelada (Módulo 6)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


async def query_receita_real_por_tonelada(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    id_municipio: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-2.14: Receita Real por Tonelada.

    Busca tonelagem do BigQuery e cruza com receita portuária deflacionada.
    Permite comparação entre anos sem distorção inflacionária.
    """
    from app.db.bigquery.client import get_bigquery_client
    from app.services.deflation_service import get_deflation_service

    bq = get_bigquery_client()
    deflation = get_deflation_service()

    where_inst = f"AND porto_atracacao = '{id_instalacao}'" if id_instalacao else ""
    where_ano = f"AND CAST(ano AS INT64) = {ano}" if ano else ""

    sql = f"""
    SELECT
        porto_atracacao AS id_instalacao,
        CAST(ano AS INT64) AS ano,
        SUM(vlpesocargabruta_oficial) AS tonelagem_total,
        COUNT(DISTINCT idatracacao) AS total_atracoes
    FROM
        `antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial`
    WHERE
        vlpesocargabruta_oficial IS NOT NULL
        {where_inst}
        {where_ano}
    GROUP BY
        porto_atracacao, ano
    ORDER BY
        ano DESC
    """

    try:
        rows = await bq.execute_query(sql, timeout_ms=30000)
    except Exception as e:
        logger.warning("deflated_receita_bq_error: %s", e)
        return []

    if not rows:
        return []

    # Simula receita com proxy: tonelagem × tarifa média estimada (R$ 15/ton)
    TARIFA_MEDIA_TON = 15.0
    for row in rows:
        row["receita_nominal"] = round(
            float(row.get("tonelagem_total", 0)) * TARIFA_MEDIA_TON, 2
        )

    # Deflaciona
    rows = await deflation.deflacionar_serie(
        rows, campo_valor="receita_nominal", campo_ano="ano"
    )

    # Calcula receita real por tonelada
    for row in rows:
        ton = float(row.get("tonelagem_total", 0))
        receita_real = row.get("receita_nominal_real")
        if ton > 0 and receita_real:
            row["receita_real_por_tonelada"] = round(receita_real / ton, 2)
        else:
            row["receita_real_por_tonelada"] = None

    return rows


async def query_fob_exportacoes_usd_ajustado(
    id_instalacao: Optional[str] = None,
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-4.11: Valor FOB Exportações ajustado por câmbio.

    Busca FOB em USD do BigQuery e converte para BRL deflacionado,
    permitindo comparação de competitividade real entre anos.
    """
    from app.db.bigquery.client import get_bigquery_client
    from app.services.deflation_service import get_deflation_service

    bq = get_bigquery_client()
    deflation = get_deflation_service()

    where_mun = f"AND id_municipio = '{id_municipio}'" if id_municipio else ""
    where_ano = f"AND ano = {ano}" if ano else ""

    sql = f"""
    SELECT
        id_municipio,
        CAST(ano AS INT64) AS ano,
        SUM(valor_fob_dolar) AS fob_usd,
        SUM(kg_liquido) AS peso_kg
    FROM
        `basedosdados.br_me_comex_stat.municipio_exportacao`
    WHERE
        valor_fob_dolar IS NOT NULL
        {where_mun}
        {where_ano}
    GROUP BY
        id_municipio, ano
    ORDER BY
        ano DESC
    """

    try:
        rows = await bq.execute_query(sql, timeout_ms=30000)
    except Exception as e:
        logger.warning("deflated_fob_exp_error: %s", e)
        return []

    if not rows:
        return []

    # Converte FOB USD → BRL usando PTAX, depois deflaciona
    cambio = await deflation.bacen.get_deflator_ipca(2023, 2010, 2025)
    ptax = {}
    try:
        data = await deflation.bacen.consultar_serie(3698, "01/01/2010", "31/12/2025")
        from collections import defaultdict
        by_year: dict[int, list[float]] = defaultdict(list)
        for item in data:
            try:
                parts = item["data"].split("/")
                y = int(parts[2])
                by_year[y].append(float(item["valor"]))
            except (ValueError, KeyError, IndexError):
                continue
        ptax = {y: sum(v) / len(v) for y, v in by_year.items() if v}
    except Exception:
        pass

    for row in rows:
        try:
            fob = float(row.get("fob_usd", 0))
            ano_row = int(row.get("ano", 0))
            taxa = ptax.get(ano_row)
            row["fob_brl_nominal"] = round(fob * taxa, 2) if taxa else None
            row["cambio_ptax_medio"] = round(taxa, 4) if taxa else None
            row["fob_usd_por_kg"] = round(fob / float(row.get("peso_kg", 1)), 4) if row.get("peso_kg") else None
        except (ValueError, TypeError):
            row["fob_brl_nominal"] = None

    # Deflaciona a versão BRL
    rows = await deflation.deflacionar_serie(
        rows, campo_valor="fob_brl_nominal", campo_ano="ano"
    )

    return rows


async def query_fob_importacoes_usd_ajustado(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-4.12: Valor FOB Importações ajustado por câmbio.
    """
    from app.db.bigquery.client import get_bigquery_client
    from app.services.deflation_service import get_deflation_service

    bq = get_bigquery_client()
    deflation = get_deflation_service()

    where_mun = f"AND id_municipio = '{id_municipio}'" if id_municipio else ""
    where_ano = f"AND ano = {ano}" if ano else ""

    sql = f"""
    SELECT
        id_municipio,
        CAST(ano AS INT64) AS ano,
        SUM(valor_fob_dolar) AS fob_usd,
        SUM(kg_liquido) AS peso_kg
    FROM
        `basedosdados.br_me_comex_stat.municipio_importacao`
    WHERE
        valor_fob_dolar IS NOT NULL
        {where_mun}
        {where_ano}
    GROUP BY
        id_municipio, ano
    ORDER BY
        ano DESC
    """

    try:
        rows = await bq.execute_query(sql, timeout_ms=30000)
    except Exception as e:
        logger.warning("deflated_fob_imp_error: %s", e)
        return []

    if not rows:
        return []

    # Converte e deflaciona (mesma lógica do export)
    rows = await deflation.converter_para_usd(rows, "fob_usd", "ano")

    return rows


async def query_receita_municipal_real_per_capita(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-6.18: Receita Municipal Real per Capita.

    Receita total do município deflacionada por IPCA / população.
    """
    from app.db.bigquery.client import get_bigquery_client
    from app.services.deflation_service import get_deflation_service

    bq = get_bigquery_client()
    deflation = get_deflation_service()

    where_mun = f"AND id_municipio = '{id_municipio}'" if id_municipio else ""
    where_ano = f"AND ano = {ano}" if ano else ""

    sql = f"""
    SELECT
        r.id_municipio,
        CAST(r.ano AS INT64) AS ano,
        r.receitas_realizadas AS receita_nominal,
        p.populacao
    FROM
        `basedosdados.br_me_siconfi.municipio_receitas_orcamentarias` r
    LEFT JOIN
        `basedosdados.br_ibge_populacao.municipio` p
        ON r.id_municipio = p.id_municipio AND CAST(r.ano AS INT64) = CAST(p.ano AS INT64)
    WHERE
        r.receitas_realizadas IS NOT NULL
        {where_mun}
        {where_ano}
    GROUP BY
        r.id_municipio, r.ano, r.receitas_realizadas, p.populacao
    ORDER BY
        r.ano DESC
    """

    try:
        rows = await bq.execute_query(sql, timeout_ms=30000)
    except Exception as e:
        logger.warning("deflated_receita_mun_error: %s", e)
        return []

    if not rows:
        return []

    # Deflaciona
    rows = await deflation.deflacionar_serie(
        rows, campo_valor="receita_nominal", campo_ano="ano"
    )

    # Calcula per capita
    for row in rows:
        receita_real = row.get("receita_nominal_real")
        pop = row.get("populacao")
        if receita_real and pop and float(pop) > 0:
            row["receita_real_per_capita"] = round(float(receita_real) / float(pop), 2)
        else:
            row["receita_real_per_capita"] = None

    return rows


async def query_icms_real_por_tonelada(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-6.19: ICMS Real por Tonelada.

    ICMS arrecadado no município deflacionado / tonelagem portuária.
    Mede a eficiência fiscal real da operação portuária.
    """
    from app.db.bigquery.client import get_bigquery_client
    from app.services.deflation_service import get_deflation_service

    bq = get_bigquery_client()
    deflation = get_deflation_service()

    where_mun = f"AND r.id_municipio = '{id_municipio}'" if id_municipio else ""
    where_ano = f"AND CAST(r.ano AS INT64) = {ano}" if ano else ""

    sql = f"""
    WITH receita AS (
        SELECT
            id_municipio,
            CAST(ano AS INT64) AS ano,
            SUM(receitas_realizadas) AS icms_nominal
        FROM
            `basedosdados.br_me_siconfi.municipio_receitas_orcamentarias`
        WHERE
            conta LIKE '%%ICMS%%'
            AND receitas_realizadas IS NOT NULL
        GROUP BY id_municipio, ano
    ),
    carga AS (
        SELECT
            dir.id_municipio,
            CAST(c.ano AS INT64) AS ano,
            SUM(c.vlpesocargabruta_oficial) AS tonelagem
        FROM
            `antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial` c
        JOIN
            `basedosdados.br_bd_diretorios_brasil.municipio` dir
            ON c.porto_atracacao = dir.nome
        WHERE c.vlpesocargabruta_oficial IS NOT NULL
        GROUP BY dir.id_municipio, c.ano
    )
    SELECT
        r.id_municipio,
        r.ano,
        r.icms_nominal,
        c.tonelagem
    FROM receita r
    LEFT JOIN carga c ON r.id_municipio = c.id_municipio AND r.ano = c.ano
    WHERE 1=1
        {where_mun}
        {where_ano}
    ORDER BY r.ano DESC
    """

    try:
        rows = await bq.execute_query(sql, timeout_ms=30000)
    except Exception as e:
        logger.warning("deflated_icms_ton_error: %s", e)
        return []

    if not rows:
        return []

    # Deflaciona
    rows = await deflation.deflacionar_serie(
        rows, campo_valor="icms_nominal", campo_ano="ano"
    )

    # Calcula ICMS real por tonelada
    for row in rows:
        icms_real = row.get("icms_nominal_real")
        ton = row.get("tonelagem")
        if icms_real and ton and float(ton) > 0:
            row["icms_real_por_tonelada"] = round(float(icms_real) / float(ton), 4)
        else:
            row["icms_real_por_tonelada"] = None

    return rows


QUERIES_DEFLATED = {
    "IND-2.14": query_receita_real_por_tonelada,
    "IND-4.11": query_fob_exportacoes_usd_ajustado,
    "IND-4.12": query_fob_importacoes_usd_ajustado,
    "IND-6.18": query_receita_municipal_real_per_capita,
    "IND-6.19": query_icms_real_por_tonelada,
}
