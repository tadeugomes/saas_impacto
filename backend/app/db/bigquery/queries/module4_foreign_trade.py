"""
Queries BigQuery para o Módulo 4 - Comércio Exterior.

Este módulo contém as queries SQL para cálculo dos 10 indicadores
do Módulo 4 de comércio exterior, baseados em dados do Comex Stat.
"""

from typing import Optional


# ============================================================================
# Constants
# ============================================================================

# Dataset Base dos Dados - Comex Stat
BD_DADOS_EXPORTACAO = "basedosdados.br_me_comex_stat.municipio_exportacao"
BD_DADOS_IMPORTACAO = "basedosdados.br_me_comex_stat.municipio_importacao"
BD_DADOS_DIRETORIO_MUNICIPIO = "basedosdados.br_bd_diretorios_brasil.municipio"


# ============================================================================
# Módulo 4: Queries SQL Templates
# ============================================================================

def query_valor_fob_exportacoes(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-4.01: Valor FOB Exportações (US$).

    Unidade: US$
    Granularidade: Município/Ano
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"e.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"e.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"e.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""

    return f"""
    SELECT
        e.id_municipio,
        dir.nome AS nome_municipio,
        e.ano,
        ROUND(SUM(e.valor_fob_dolar), 2) AS valor_exportacoes_usd
    FROM
        `{BD_DADOS_EXPORTACAO}` e
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON e.id_municipio = dir.id_municipio
    WHERE
        e.valor_fob_dolar IS NOT NULL
        {f"AND {where_sql}" if where_sql else ""}
    GROUP BY
        e.id_municipio,
        dir.nome,
        e.ano
    ORDER BY
        e.ano DESC,
        dir.nome
    """


def query_valor_fob_importacoes(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-4.02: Valor FOB Importações (US$).

    Unidade: US$
    Granularidade: Município/Ano
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"i.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"i.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"i.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""

    return f"""
    SELECT
        i.id_municipio,
        dir.nome AS nome_municipio,
        i.ano,
        ROUND(SUM(i.valor_fob_dolar), 2) AS valor_importacoes_usd
    FROM
        `{BD_DADOS_IMPORTACAO}` i
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON i.id_municipio = dir.id_municipio
    WHERE
        i.valor_fob_dolar IS NOT NULL
        {f"AND {where_sql}" if where_sql else ""}
    GROUP BY
        i.id_municipio,
        dir.nome,
        i.ano
    ORDER BY
        i.ano DESC,
        dir.nome
    """


def query_balanca_comercial(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-4.03: Balança Comercial do Porto.

    Unidade: US$
    Granularidade: Município/Ano
    """
    where_exp = []
    where_imp = []
    if id_municipio:
        where_exp.append(f"e.id_municipio = '{id_municipio}'")
        where_imp.append(f"i.id_municipio = '{id_municipio}'")
    if ano:
        where_exp.append(f"e.ano = {ano}")
        where_imp.append(f"i.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_exp.append(f"e.ano BETWEEN {ano_inicio} AND {ano_fim}")
        where_imp.append(f"i.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_exp_sql = "\n        AND ".join(where_exp) if where_exp else ""
    where_imp_sql = "\n        AND ".join(where_imp) if where_imp else ""

    return f"""
    WITH exportacoes AS (
        SELECT
            e.id_municipio,
            e.ano,
            ROUND(SUM(e.valor_fob_dolar), 2) AS valor_exportacoes
        FROM
            `{BD_DADOS_EXPORTACAO}` e
        WHERE
            e.valor_fob_dolar IS NOT NULL
            {f"AND {where_exp_sql}" if where_exp_sql else ""}
        GROUP BY
            e.id_municipio,
            e.ano
    ),
    importacoes AS (
        SELECT
            i.id_municipio,
            i.ano,
            ROUND(SUM(i.valor_fob_dolar), 2) AS valor_importacoes
        FROM
            `{BD_DADOS_IMPORTACAO}` i
        WHERE
            i.valor_fob_dolar IS NOT NULL
            {f"AND {where_imp_sql}" if where_imp_sql else ""}
        GROUP BY
            i.id_municipio,
            i.ano
    )
    SELECT
        COALESCE(e.id_municipio, i.id_municipio) AS id_municipio,
        dir.nome AS nome_municipio,
        COALESCE(e.ano, i.ano) AS ano,
        COALESCE(e.valor_exportacoes, 0) AS valor_exportacoes_usd,
        COALESCE(i.valor_importacoes, 0) AS valor_importacoes_usd,
        ROUND(COALESCE(e.valor_exportacoes, 0) - COALESCE(i.valor_importacoes, 0), 2) AS balanca_comercial_usd,
        ROUND(COALESCE(i.valor_importacoes, 0) * 100.0 / NULLIF(COALESCE(e.valor_exportacoes, 0), 0), 2) AS cobertura_importacoes_pct
    FROM
        exportacoes e
    FULL OUTER JOIN
        importacoes i USING (id_municipio, ano)
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON COALESCE(e.id_municipio, i.id_municipio) = dir.id_municipio
    ORDER BY
        COALESCE(e.ano, i.ano) DESC,
        dir.nome
    """


def query_peso_liquido_exportacoes(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-4.04: Peso Líquido Exportações (kg).

    Unidade: kg
    Granularidade: Município/Ano
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"e.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"e.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"e.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""

    return f"""
    SELECT
        e.id_municipio,
        dir.nome AS nome_municipio,
        e.ano,
        ROUND(SUM(e.kg_liquido), 2) AS peso_liquido_exportacoes_kg
    FROM
        `{BD_DADOS_EXPORTACAO}` e
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON e.id_municipio = dir.id_municipio
    WHERE
        e.kg_liquido IS NOT NULL
        {f"AND {where_sql}" if where_sql else ""}
    GROUP BY
        e.id_municipio,
        dir.nome,
        e.ano
    ORDER BY
        e.ano DESC,
        dir.nome
    """


def query_peso_liquido_importacoes(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-4.05: Peso Líquido Importações (kg).

    Unidade: kg
    Granularidade: Município/Ano
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"i.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"i.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"i.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""

    return f"""
    SELECT
        i.id_municipio,
        dir.nome AS nome_municipio,
        i.ano,
        ROUND(SUM(i.kg_liquido), 2) AS peso_liquido_importacoes_kg
    FROM
        `{BD_DADOS_IMPORTACAO}` i
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON i.id_municipio = dir.id_municipio
    WHERE
        i.kg_liquido IS NOT NULL
        {f"AND {where_sql}" if where_sql else ""}
    GROUP BY
        i.id_municipio,
        dir.nome,
        i.ano
    ORDER BY
        i.ano DESC,
        dir.nome
    """


def query_valor_medio_kg_exportacao(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-4.06: Valor Médio por kg Exportação (US$/kg).

    Unidade: US$/kg
    Granularidade: Município/Ano
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"e.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"e.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"e.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""

    return f"""
    SELECT
        e.id_municipio,
        dir.nome AS nome_municipio,
        e.ano,
        ROUND(SUM(e.valor_fob_dolar) / NULLIF(SUM(e.kg_liquido), 0), 4) AS valor_medio_usd_kg
    FROM
        `{BD_DADOS_EXPORTACAO}` e
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON e.id_municipio = dir.id_municipio
    WHERE
        e.valor_fob_dolar IS NOT NULL
        AND e.kg_liquido IS NOT NULL
        AND e.kg_liquido > 0
        {f"AND {where_sql}" if where_sql else ""}
    GROUP BY
        e.id_municipio,
        dir.nome,
        e.ano
    ORDER BY
        e.ano DESC,
        dir.nome
    """


def query_concentracao_por_pais(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    top_n: int = 10,
) -> str:
    """
    IND-4.07: Concentração por País de Destino/Origem.

    Unidade: Percentual
    Granularidade: Município/Ano/País
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"e.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"e.ano = {ano}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""

    return f"""
    WITH totais AS (
        SELECT
            e.id_municipio,
            e.ano,
            SUM(e.valor_fob_dolar) AS total_valor
        FROM
            `{BD_DADOS_EXPORTACAO}` e
        WHERE
            e.valor_fob_dolar IS NOT NULL
            {f"AND {where_sql}" if where_sql else ""}
        GROUP BY
            e.id_municipio,
            e.ano
    )
    SELECT
        e.id_municipio,
        dir.nome AS nome_municipio,
        e.ano,
        e.pais_destino,
        ROUND(SUM(e.valor_fob_dolar), 2) AS valor_exportacoes_usd,
        ROUND(SUM(e.valor_fob_dolar) * 100.0 / t.total_valor, 2) AS percentual
    FROM
        `{BD_DADOS_EXPORTACAO}` e
    INNER JOIN
        totais t ON e.id_municipio = t.id_municipio AND e.ano = t.ano
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON e.id_municipio = dir.id_municipio
    WHERE
        e.valor_fob_dolar IS NOT NULL
        {f"AND {where_sql}" if where_sql else ""}
    GROUP BY
        e.id_municipio,
        dir.nome,
        e.ano,
        e.pais_destino,
        t.total_valor
    ORDER BY
        e.ano DESC,
        dir.nome,
        percentual DESC
    LIMIT 1000
    """


def query_concentracao_por_ncm(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    top_n: int = 10,
) -> str:
    """
    IND-4.08: Concentração por NCM (Nomenclatura Comum do Mercosul).

    Unidade: Percentual
    Granularidade: Município/Ano/NCM
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"e.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"e.ano = {ano}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""

    return f"""
    WITH totais AS (
        SELECT
            e.id_municipio,
            e.ano,
            SUM(e.valor_fob_dolar) AS total_valor
        FROM
            `{BD_DADOS_EXPORTACAO}` e
        WHERE
            e.valor_fob_dolar IS NOT NULL
            {f"AND {where_sql}" if where_sql else ""}
        GROUP BY
            e.id_municipio,
            e.ano
    )
    SELECT
        e.id_municipio,
        dir.nome AS nome_municipio,
        e.ano,
        SUBSTR(e.ncm, 1, 4) AS ncm_capitulo,
        ROUND(SUM(e.valor_fob_dolar), 2) AS valor_exportacoes_usd,
        ROUND(SUM(e.valor_fob_dolar) * 100.0 / t.total_valor, 2) AS percentual
    FROM
        `{BD_DADOS_EXPORTACAO}` e
    INNER JOIN
        totais t ON e.id_municipio = t.id_municipio AND e.ano = t.ano
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON e.id_municipio = dir.id_municipio
    WHERE
        e.valor_fob_dolar IS NOT NULL
        AND e.ncm IS NOT NULL
        {f"AND {where_sql}" if where_sql else ""}
    GROUP BY
        e.id_municipio,
        dir.nome,
        e.ano,
        ncm_capitulo,
        t.total_valor
    ORDER BY
        e.ano DESC,
        dir.nome,
        percentual DESC
    """


def query_variacao_anual_comercio(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-4.09: Variação Anual do Comércio Exterior.

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_clause = f"AND e.id_municipio = '{id_municipio}'" if id_municipio else ""
    where_ano = f"AND e.ano <= {ano}" if ano else ""

    return f"""
    WITH comercio_anual AS (
        SELECT
            e.id_municipio,
            e.ano,
            SUM(e.valor_fob_dolar) AS valor_total
        FROM
            `{BD_DADOS_EXPORTACAO}` e
        WHERE
            e.valor_fob_dolar IS NOT NULL
            {where_clause}
            {where_ano}
        GROUP BY
            e.id_municipio,
            e.ano
    )
    SELECT
        a.id_municipio,
        dir.nome AS nome_municipio,
        a.ano,
        a.valor_total AS valor_comercio_usd,
        ROUND((a.valor_total - b.valor_total) * 100.0 / NULLIF(b.valor_total, 0), 2) AS variacao_percentual
    FROM
        comercio_anual a
    INNER JOIN
        comercio_anual b ON a.id_municipio = b.id_municipio AND a.ano = b.ano + 1
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON a.id_municipio = dir.id_municipio
    ORDER BY
        a.ano DESC,
        dir.nome
    """


def query_market_share_porto(
    ano: Optional[int] = None,
) -> str:
    """
    IND-4.10: Market Share entre Portos.

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_ano = f"WHERE e.ano = {ano}" if ano else ""

    return f"""
    WITH totais AS (
        SELECT
            e.ano,
            SUM(e.valor_fob_dolar) AS total_nacional
        FROM
            `{BD_DADOS_EXPORTACAO}` e
        {where_ano}
        GROUP BY
            e.ano
    ),
    portos AS (
        SELECT
            e.id_municipio,
            e.ano,
            SUM(e.valor_fob_dolar) AS valor_porto
        FROM
            `{BD_DADOS_EXPORTACAO}` e
        {where_ano}
        GROUP BY
            e.id_municipio,
            e.ano
    )
    SELECT
        p.id_municipio,
        dir.nome AS nome_municipio,
        p.ano,
        p.valor_porto,
        ROUND(p.valor_porto * 100.0 / t.total_nacional, 4) AS market_share_pct
    FROM
        portos p
    CROSS JOIN
        totais t
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON p.id_municipio = dir.id_municipio
    WHERE
        p.ano = t.ano
    ORDER BY
        p.ano DESC,
        market_share_pct DESC
    """


# ============================================================================
# Dicionário de Queries
# ============================================================================

QUERIES_MODULE_4 = {
    "IND-4.01": query_valor_fob_exportacoes,
    "IND-4.02": query_valor_fob_importacoes,
    "IND-4.03": query_balanca_comercial,
    "IND-4.04": query_peso_liquido_exportacoes,
    "IND-4.05": query_peso_liquido_importacoes,
    "IND-4.06": query_valor_medio_kg_exportacao,
    "IND-4.07": query_concentracao_por_pais,
    "IND-4.08": query_concentracao_por_ncm,
    "IND-4.09": query_variacao_anual_comercio,
    "IND-4.10": query_market_share_porto,
}


def get_query_module4(indicator_code: str) -> callable:
    """Retorna a função de query para um indicador do Módulo 4."""
    if indicator_code not in QUERIES_MODULE_4:
        raise ValueError(f"Indicador {indicator_code} não encontrado no Módulo 4")
    return QUERIES_MODULE_4[indicator_code]
