"""
Queries BigQuery para o Módulo 6 - Finanças Públicas.

Este módulo contém os indicadores de finanças públicas com base em dados reais da
Base dos Dados (SICONFI e diretório municipal), com apoio de mart/crosswalk para
tonelagem ANTAQ:

- FINBRA/SICONFI: receitas municipais (ICMS, ISS, receitas correntes)
- mart_impacto_*.marts_impacto.impacto_economico: tonelagem por município/ano
"""

from __future__ import annotations

from typing import Optional

from app.db.bigquery.marts.module5 import MART_IMPACTO_ECONOMICO_FQTN


# ============================================================================
# Constants
# ============================================================================

# Dataset Base dos Dados - FINBRA
BD_DADOS_FINBRA = "basedosdados.br_me_siconfi.municipio_receitas_orcamentarias"
BD_DADOS_DIRETORIO_MUNICIPIO = "basedosdados.br_bd_diretorios_brasil.municipio"

# Mart de impacto (já inclui crosswalk ANTAQ -> IBGE e janela de município/ano)
MART_IMPACTO_ECONOMICO_FQTN = MART_IMPACTO_ECONOMICO_FQTN


# ============================================================================
# Helpers
# ============================================================================

def _as_int_filters(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """Monta filtros padrão reutilizáveis para campos id/ano."""
    clauses = []
    if id_municipio:
        clauses.append(f"r.id_municipio = '{id_municipio}'")
    if ano:
        clauses.append(f"r.ano = {ano}")
    elif ano_inicio and ano_fim:
        clauses.append(f"r.ano BETWEEN {ano_inicio} AND {ano_fim}")
    return "\n        AND ".join(clauses) if clauses else ""


def _as_mart_filters(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """Monta filtros padrão para o mart de impacto (tonelagem)."""
    clauses = ["m.tonelagem_antaq_oficial IS NOT NULL"]
    if id_municipio:
        clauses.append(f"m.id_municipio = '{id_municipio}'")
    if ano:
        clauses.append(f"m.ano = {ano}")
    elif ano_inicio and ano_fim:
        clauses.append(f"m.ano BETWEEN {ano_inicio} AND {ano_fim}")
    return "\n        AND ".join(clauses) if clauses else ""


def _safe_order_by_id_ou_ano(
    id_municipio: Optional[str],
    valor_alias: str = "valor",
    tempo_alias: str = "m.ano",
) -> str:
    return f"{tempo_alias} DESC" if id_municipio else f"{valor_alias} DESC"


def _safe_where(sql_where: str) -> str:
    if not sql_where:
        return ""
    return f"WHERE {sql_where}"


def _safe_where_finbra(where_sql: str, alias: str = "r") -> str:
    if not where_sql:
        return ""
    return f"WHERE\n            {alias}.{where_sql.replace('r.', '').replace('m.', '')}"


# ============================================================================
# Módulo 6: Queries SQL Templates
# ============================================================================

def query_arrecadacao_icms(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-6.01: Arrecadação de ICMS (SICONFI).
    """
    where_sql = _as_int_filters(id_municipio, ano, ano_inicio, ano_fim)
    return f"""
    SELECT
        r.id_municipio,
        dir.nome AS nome_municipio,
        r.ano,
        ROUND(SUM(r.valor), 2) AS arrecadacao_icms
    FROM `{BD_DADOS_FINBRA}` r
    LEFT JOIN `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON r.id_municipio = dir.id_municipio
    WHERE
        r.conta_bd = 'Cota-Parte do ICMS'
        AND r.estagio_bd = 'Receitas Brutas Realizadas'
        AND r.valor IS NOT NULL
        {f"AND {where_sql}" if where_sql else ""}
    GROUP BY
        r.id_municipio,
        dir.nome,
        r.ano
    ORDER BY
        { _safe_order_by_id_ou_ano(id_municipio, "arrecadacao_icms") }
    """


def query_arrecadacao_iss(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-6.02: Arrecadação de ISS (SICONFI).
    """
    where_sql = _as_int_filters(id_municipio, ano, ano_inicio, ano_fim)
    return f"""
    SELECT
        r.id_municipio,
        dir.nome AS nome_municipio,
        r.ano,
        ROUND(SUM(r.valor), 2) AS arrecadacao_iss
    FROM `{BD_DADOS_FINBRA}` r
    LEFT JOIN `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON r.id_municipio = dir.id_municipio
    WHERE
        r.conta_bd = 'Imposto sobre Serviços de Qualquer Natureza - ISSQN'
        AND r.estagio_bd = 'Receitas Brutas Realizadas'
        AND r.valor IS NOT NULL
        {f"AND {where_sql}" if where_sql else ""}
    GROUP BY
        r.id_municipio,
        dir.nome,
        r.ano
    ORDER BY
        { _safe_order_by_id_ou_ano(id_municipio, "arrecadacao_iss") }
    """


def query_receita_total_municipal(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-6.03: Receita Total Municipal (SICONFI - receitas correntes).
    """
    where_sql = _as_int_filters(id_municipio, ano, ano_inicio, ano_fim)
    return f"""
    SELECT
        r.id_municipio,
        dir.nome AS nome_municipio,
        r.ano,
        ROUND(SUM(r.valor), 2) AS receita_total
    FROM `{BD_DADOS_FINBRA}` r
    LEFT JOIN `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON r.id_municipio = dir.id_municipio
    WHERE
        r.conta_bd = 'Receitas Correntes'
        AND r.estagio_bd = 'Receitas Brutas Realizadas'
        AND r.valor IS NOT NULL
        {f"AND {where_sql}" if where_sql else ""}
    GROUP BY
        r.id_municipio,
        dir.nome,
        r.ano
    ORDER BY
        { _safe_order_by_id_ou_ano(id_municipio, "receita_total") }
    """


def query_receita_per_capita(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-6.04: Receita per Capita Municipal.
    """
    where_sql = _as_int_filters(id_municipio, ano, ano_inicio, ano_fim)
    return f"""
    WITH receitas AS (
        SELECT
            id_municipio,
            CAST(ano AS INT64) AS ano,
            ROUND(SUM(valor), 2) AS receita_total
        FROM `{BD_DADOS_FINBRA}`
        WHERE
            conta_bd = 'Receitas Correntes'
            AND estagio_bd = 'Receitas Brutas Realizadas'
            AND valor IS NOT NULL
            {f"AND {where_sql}" if where_sql else ""}
        GROUP BY id_municipio, ano
    )
    SELECT
        r.id_municipio,
        dir.nome AS nome_municipio,
        r.ano,
        ROUND(r.receita_total / NULLIF(pop.populacao, 0), 2) AS receita_per_capita
    FROM receitas r
    INNER JOIN `{BD_DADOS_DIRETORIO_MUNICIPIO}` d
        ON r.id_municipio = d.id_municipio
    INNER JOIN `basedosdados.br_ibge_populacao.municipio` pop
        ON r.id_municipio = pop.id_municipio AND r.ano = pop.ano
    LEFT JOIN `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir
        ON r.id_municipio = dir.id_municipio
    WHERE pop.populacao IS NOT NULL
        AND pop.populacao > 0
    ORDER BY
        { _safe_order_by_id_ou_ano(id_municipio, "receita_per_capita") }
    """


def query_crescimento_receita(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-6.05: Crescimento anual da Receita (%).
    """
    where_clause = f"WHERE id_municipio = '{id_municipio}'" if id_municipio else ""
    where_clause_ano = f"AND ano <= {ano}" if ano else ""
    return f"""
    WITH receita_anual AS (
        SELECT
            CAST(id_municipio AS STRING) AS id_municipio,
            CAST(ano AS INT64) AS ano,
            SUM(valor) AS receita_total
        FROM `{BD_DADOS_FINBRA}`
        WHERE
            conta_bd = 'Receitas Correntes'
            AND estagio_bd = 'Receitas Brutas Realizadas'
            AND valor IS NOT NULL
            {where_clause}
            {where_clause_ano}
        GROUP BY id_municipio, ano
    )
    SELECT
        a.id_municipio,
        dir.nome AS nome_municipio,
        a.ano,
        ROUND((a.receita_total - b.receita_total) * 100.0 / NULLIF(b.receita_total, 0), 2) AS crescimento_receita_pct
    FROM receita_anual a
    INNER JOIN receita_anual b
        ON a.id_municipio = b.id_municipio AND a.ano = b.ano + 1
    LEFT JOIN `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir
        ON a.id_municipio = dir.id_municipio
    ORDER BY
        { _safe_order_by_id_ou_ano(id_municipio, "crescimento_receita_pct") }
    """


def _query_finbra_tributos_agregados(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    CTE auxiliar comum para receita fiscal (ICMS + ISS).
    """
    where_sql = _as_int_filters(id_municipio, ano, ano_inicio, ano_fim)
    return f"""
    WITH receitas_tributarias AS (
        SELECT
            CAST(id_municipio AS STRING) AS id_municipio,
            CAST(ano AS INT64) AS ano,
            SUM(CASE WHEN conta_bd = 'Cota-Parte do ICMS'
                     THEN CAST(valor AS FLOAT64) ELSE 0 END) AS arrecadacao_icms,
            SUM(CASE WHEN conta_bd = 'Imposto sobre Serviços de Qualquer Natureza - ISSQN'
                     THEN CAST(valor AS FLOAT64) ELSE 0 END) AS arrecadacao_iss
        FROM `{BD_DADOS_FINBRA}`
        WHERE
            conta_bd IN ('Cota-Parte do ICMS', 'Imposto sobre Serviços de Qualquer Natureza - ISSQN')
            AND estagio_bd = 'Receitas Brutas Realizadas'
            AND valor IS NOT NULL
            {f"AND {where_sql}" if where_sql else ""}
        GROUP BY id_municipio, ano
    )
    """


def query_receita_fiscal_total(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-6.07: Receita Fiscal Total (ICMS + ISS).
    """
    order_by = _safe_order_by_id_ou_ano(id_municipio, "receita_fiscal_total")
    return f"""
    {_query_finbra_tributos_agregados(id_municipio, ano, ano_inicio, ano_fim)}
    SELECT
        r.id_municipio,
        dir.nome AS nome_municipio,
        r.ano,
        ROUND(r.arrecadacao_icms + r.arrecadacao_iss, 2) AS receita_fiscal_total
    FROM receitas_tributarias r
    LEFT JOIN `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON r.id_municipio = dir.id_municipio
    WHERE (r.arrecadacao_icms IS NOT NULL OR r.arrecadacao_iss IS NOT NULL)
    ORDER BY
        {order_by}
    """


def query_receita_fiscal_per_capita(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-6.08: Receita Fiscal per Capita (ICMS + ISS per habitante).
    """
    order_by = _safe_order_by_id_ou_ano(id_municipio, "receita_fiscal_per_capita")
    return f"""
    {_query_finbra_tributos_agregados(id_municipio, ano, ano_inicio, ano_fim)},
    receita_fiscal AS (
        SELECT
            id_municipio,
            ano,
            arrecadacao_icms,
            arrecadacao_iss,
            arrecadacao_icms + arrecadacao_iss AS receita_fiscal_total
        FROM receitas_tributarias
    )
    SELECT
        rf.id_municipio,
        dir.nome AS nome_municipio,
        rf.ano,
        ROUND(rf.receita_fiscal_total / NULLIF(pop.populacao, 0), 2) AS receita_fiscal_per_capita
    FROM receita_fiscal rf
    INNER JOIN `basedosdados.br_ibge_populacao.municipio` pop
        ON rf.id_municipio = pop.id_municipio AND rf.ano = pop.ano
    LEFT JOIN `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir
        ON rf.id_municipio = dir.id_municipio
    WHERE pop.populacao IS NOT NULL
        AND pop.populacao > 0
    ORDER BY
        {order_by}
    """


def query_receita_fiscal_por_tonelada(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-6.09: Receita Fiscal por Tonelada Movimentada (R$/t, ICMS+ISS).
    """
    receita_where = _as_int_filters(id_municipio, ano, ano_inicio, ano_fim)
    tonelagem_where = _as_mart_filters(id_municipio, ano, ano_inicio, ano_fim)
    order_by = _safe_order_by_id_ou_ano(id_municipio, "receita_fiscal_por_tonelada")
    return f"""
    {_query_finbra_tributos_agregados(id_municipio, ano, ano_inicio, ano_fim)},
    receita_fiscal AS (
        SELECT
            id_municipio,
            ano,
            arrecadacao_icms,
            arrecadacao_iss,
            arrecadacao_icms + arrecadacao_iss AS receita_fiscal_total
        FROM receitas_tributarias
    ),
    toneladas AS (
        SELECT
            id_municipio,
            ano,
            tonelagem_antaq_oficial AS tonelagem_total
        FROM {MART_IMPACTO_ECONOMICO_FQTN}
        WHERE {tonelagem_where}
    )
    SELECT
        COALESCE(r.id_municipio, t.id_municipio) AS id_municipio,
        dir.nome AS nome_municipio,
        COALESCE(r.ano, t.ano) AS ano,
        COALESCE(r.arrecadacao_icms, 0) AS arrecadacao_icms,
        COALESCE(r.arrecadacao_iss, 0) AS arrecadacao_iss,
        COALESCE(r.receita_fiscal_total, 0) AS receita_fiscal_total,
        COALESCE(t.tonelagem_total, 0) AS tonelagem_total,
        ROUND(
            COALESCE(r.receita_fiscal_total, 0) / NULLIF(COALESCE(t.tonelagem_total, 0), 0),
            4
        ) AS receita_fiscal_por_tonelada
    FROM receita_fiscal r
    FULL OUTER JOIN toneladas t
        ON r.id_municipio = t.id_municipio AND r.ano = t.ano
    LEFT JOIN `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir
        ON COALESCE(r.id_municipio, t.id_municipio) = dir.id_municipio
    ORDER BY
        {order_by}
    """


def query_icms_por_tonelada(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-6.06: ICMS por Tonelada Movimentada (R$/t).
    """
    receita_where = _as_int_filters(id_municipio, ano, ano_inicio, ano_fim)
    tonelagem_where = _as_mart_filters(id_municipio, ano, ano_inicio, ano_fim)
    order_by = _safe_order_by_id_ou_ano(id_municipio, "icms_por_tonelada")
    return f"""
    WITH icms AS (
        SELECT
            CAST(id_municipio AS STRING) AS id_municipio,
            CAST(ano AS INT64) AS ano,
            SUM(valor) AS icms_total
        FROM `{BD_DADOS_FINBRA}`
        WHERE
            conta_bd = 'Cota-Parte do ICMS'
            AND estagio_bd = 'Receitas Brutas Realizadas'
            AND valor IS NOT NULL
            {f"AND {receita_where}" if receita_where else ""}
        GROUP BY id_municipio, ano
    ),
    toneladas AS (
        SELECT
            id_municipio,
            ano,
            tonelagem_antaq_oficial AS tonelagem_total
        FROM {MART_IMPACTO_ECONOMICO_FQTN}
        WHERE {tonelagem_where}
    )
    SELECT
        COALESCE(i.id_municipio, t.id_municipio) AS id_municipio,
        dir.nome AS nome_municipio,
        COALESCE(i.ano, t.ano) AS ano,
        COALESCE(i.icms_total, 0) AS icms_total,
        COALESCE(t.tonelagem_total, 0) AS tonelagem_total,
        ROUND(COALESCE(i.icms_total, 0) / NULLIF(COALESCE(t.tonelagem_total, 0), 0), 4) AS icms_por_tonelada
    FROM icms i
    FULL OUTER JOIN toneladas t
        ON i.id_municipio = t.id_municipio AND i.ano = t.ano
    LEFT JOIN `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir
        ON COALESCE(i.id_municipio, t.id_municipio) = dir.id_municipio
    ORDER BY
        {order_by}
    """


def query_correlacao_tonelagem_receita_fiscal(
    id_municipio: Optional[str] = None,
    min_anos: int = 5,
) -> str:
    """
    IND-6.10: Correlação entre tonelagem e receita fiscal (ICMS+ISS).
    Unidade: Coeficiente (-1 a +1), não causal.
    """
    where_id = f"AND m.id_municipio = '{id_municipio}'" if id_municipio else ""
    return f"""
    {_query_finbra_tributos_agregados(id_municipio)}
    , receita_fiscal AS (
        SELECT
            id_municipio,
            ano,
            arrecadacao_icms + arrecadacao_iss AS receita_fiscal_total
        FROM receitas_tributarias
    ),
    dados AS (
        SELECT
            m.id_municipio,
            m.ano,
            m.tonelagem_antaq_oficial AS tonelagem,
            r.receita_fiscal_total
        FROM {MART_IMPACTO_ECONOMICO_FQTN} m
        INNER JOIN receita_fiscal r
            ON m.id_municipio = r.id_municipio
            AND m.ano = r.ano
        WHERE
            m.tonelagem_antaq_oficial IS NOT NULL
            AND m.tonelagem_antaq_oficial > 0
            AND r.receita_fiscal_total IS NOT NULL
            AND r.receita_fiscal_total > 0
            {where_id}
    )
    SELECT
        d.id_municipio,
        dir.nome AS nome_municipio,
        ROUND(CORR(d.tonelagem, d.receita_fiscal_total), 4) AS correlacao,
        ROUND(CORR(d.tonelagem, d.receita_fiscal_total), 4) AS correlacao_tonelagem_receita_fiscal,
        COUNT(*) AS n_observacoes,
        COUNT(*) AS anos_analisados
    FROM dados d
    LEFT JOIN `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir
        ON d.id_municipio = dir.id_municipio
    GROUP BY d.id_municipio, dir.nome
    HAVING COUNT(*) >= {min_anos}
    ORDER BY
        correlacao_tonelagem_receita_fiscal DESC
    LIMIT 20
    """


def query_elasticidade_tonelagem_receita_fiscal(
    id_municipio: Optional[str] = None,
    min_anos: int = 5,
) -> str:
    """
    IND-6.11: Elasticidade de Tonelagem em relação à Receita Fiscal (log-log).
    Não é causal; representa sensibilidade histórica associativa.
    """
    where_id = f"AND m.id_municipio = '{id_municipio}'" if id_municipio else ""
    return f"""
    {_query_finbra_tributos_agregados(id_municipio)}
    , receita_fiscal AS (
        SELECT
            id_municipio,
            ano,
            arrecadacao_icms + arrecadacao_iss AS receita_fiscal_total
        FROM receitas_tributarias
    ),
    dados AS (
        SELECT
            m.id_municipio,
            dir.nome AS nome_municipio,
            m.ano,
            LN(NULLIF(m.tonelagem_antaq_oficial, 0)) AS ln_tonelagem,
            LN(NULLIF(rf.receita_fiscal_total, 0)) AS ln_receita_fiscal
        FROM {MART_IMPACTO_ECONOMICO_FQTN} m
        INNER JOIN receita_fiscal rf
            ON m.id_municipio = rf.id_municipio
            AND m.ano = rf.ano
        LEFT JOIN `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir
            ON m.id_municipio = dir.id_municipio
        WHERE
            m.tonelagem_antaq_oficial > 0
            AND rf.receita_fiscal_total > 0
            {where_id}
    ),
    estatisticas AS (
        SELECT
            id_municipio,
            nome_municipio,
            COUNT(*) AS n,
            SUM(ln_tonelagem) AS sum_ln_tonelagem,
            SUM(ln_receita_fiscal) AS sum_ln_receita_fiscal,
            SUM(ln_tonelagem * ln_receita_fiscal) AS sum_ln_tonelagem_receita,
            SUM(ln_tonelagem * ln_tonelagem) AS sum_ln_tonelagem_sq,
            SUM(ln_receita_fiscal * ln_receita_fiscal) AS sum_ln_receita_fiscal_sq
        FROM dados
        GROUP BY id_municipio, nome_municipio
        HAVING COUNT(*) >= {min_anos}
    )
    SELECT
        id_municipio,
        nome_municipio,
        ROUND(
            (n * sum_ln_tonelagem_receita - sum_ln_tonelagem * sum_ln_receita_fiscal) /
            NULLIF(n * sum_ln_receita_fiscal_sq - sum_ln_receita_fiscal * sum_ln_receita_fiscal, 0),
            4
        ) AS elasticidade,
        ROUND(
            (n * sum_ln_tonelagem_receita - sum_ln_tonelagem * sum_ln_receita_fiscal) /
            NULLIF(n * sum_ln_receita_fiscal_sq - sum_ln_receita_fiscal * sum_ln_receita_fiscal, 0),
            4
        ) AS elasticidade_tonelagem_receita_fiscal,
        n AS n_observacoes,
        n AS anos_analisados
    FROM estatisticas
    ORDER BY
        elasticidade_tonelagem_receita_fiscal DESC
    LIMIT 20
    """


# ============================================================================
# Dicionário de Queries
# ============================================================================

QUERIES_MODULE_6 = {
    "IND-6.01": query_arrecadacao_icms,
    "IND-6.02": query_arrecadacao_iss,
    "IND-6.03": query_receita_total_municipal,
    "IND-6.04": query_receita_per_capita,
    "IND-6.05": query_crescimento_receita,
    "IND-6.06": query_icms_por_tonelada,
    "IND-6.07": query_receita_fiscal_total,
    "IND-6.08": query_receita_fiscal_per_capita,
    "IND-6.09": query_receita_fiscal_por_tonelada,
    "IND-6.10": query_correlacao_tonelagem_receita_fiscal,
    "IND-6.11": query_elasticidade_tonelagem_receita_fiscal,
}


def get_query_module6(indicator_code: str) -> callable:
    """Retorna a função de query para um indicador do Módulo 6."""
    if indicator_code not in QUERIES_MODULE_6:
        raise ValueError(f"Indicador {indicator_code} não encontrado no Módulo 6")
    return QUERIES_MODULE_6[indicator_code]
