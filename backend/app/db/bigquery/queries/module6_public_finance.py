"""
Queries BigQuery para o Módulo 6 - Finanças Públicas.

Este módulo contém as queries SQL para cálculo dos 6 indicadores
do Módulo 6 de finanças públicas, baseados em dados FINBRA/STN.

NOTA: IND-6.06 (ICMS por Tonelada) usa view oficial ANTAQ v_carga_metodologia_oficial.
"""

from typing import Optional


# ============================================================================
# Constants
# ============================================================================

# Dataset Base dos Dados - SICONFI
BD_DADOS_FINBRA = "basedosdados.br_me_siconfi.municipio_receitas_orcamentarias"
BD_DADOS_DIRETORIO_MUNICIPIO = "basedosdados.br_bd_diretorios_brasil.municipio"

# Dataset ANTAQ no BigQuery (view oficial)
ANTAQ_DATASET = "antaqdados.br_antaq_estatistico_aquaviario"
VIEW_CARGA_METODOLOGIA_OFICIAL = f"{ANTAQ_DATASET}.v_carga_metodologia_oficial"


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
    IND-6.01: Arrecadação de ICMS.

    Unidade: R$
    Granularidade: Município/Ano
    """
    where_clauses = [
        "f.conta_bd = 'Cota-Parte do ICMS'",
        "f.estagio_bd = 'Receitas Brutas Realizadas'"
    ]
    if id_municipio:
        where_clauses.append(f"f.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"f.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"f.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""

    return f"""
    SELECT
        f.id_municipio,
        dir.nome AS nome_municipio,
        f.ano,
        ROUND(SUM(f.valor), 2) AS arrecadacao_icms
    FROM
        `{BD_DADOS_FINBRA}` f
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON f.id_municipio = dir.id_municipio
    WHERE
        f.valor IS NOT NULL
        {f"AND {where_sql}" if where_sql else ""}
    GROUP BY
        f.id_municipio,
        dir.nome,
        f.ano
    ORDER BY
        f.ano DESC,
        dir.nome
    """


def query_arrecadacao_iss(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-6.02: Arrecadação de ISS.

    Unidade: R$
    Granularidade: Município/Ano
    """
    where_clauses = [
        "f.conta_bd = 'Imposto sobre Serviços de Qualquer Natureza - ISSQN'",
        "f.estagio_bd = 'Receitas Brutas Realizadas'"
    ]
    if id_municipio:
        where_clauses.append(f"f.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"f.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"f.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""

    return f"""
    SELECT
        f.id_municipio,
        dir.nome AS nome_municipio,
        f.ano,
        ROUND(SUM(f.valor), 2) AS arrecadacao_iss
    FROM
        `{BD_DADOS_FINBRA}` f
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON f.id_municipio = dir.id_municipio
    WHERE
        f.valor IS NOT NULL
        {f"AND {where_sql}" if where_sql else ""}
    GROUP BY
        f.id_municipio,
        dir.nome,
        f.ano
    ORDER BY
        f.ano DESC,
        dir.nome
    """


def query_receita_total_municipal(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-6.03: Receita Total Municipal.

    Unidade: R$
    Granularidade: Município/Ano
    """
    where_clauses = [
        "f.conta_bd = 'Receitas Correntes'",
        "f.estagio_bd = 'Receitas Brutas Realizadas'"
    ]
    if id_municipio:
        where_clauses.append(f"f.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"f.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"f.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""

    return f"""
    SELECT
        f.id_municipio,
        dir.nome AS nome_municipio,
        f.ano,
        ROUND(SUM(f.valor), 2) AS receita_total
    FROM
        `{BD_DADOS_FINBRA}` f
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON f.id_municipio = dir.id_municipio
    WHERE
        f.valor IS NOT NULL
        {f"AND {where_sql}" if where_sql else ""}
    GROUP BY
        f.id_municipio,
        dir.nome,
        f.ano
    ORDER BY
        f.ano DESC,
        dir.nome
    """


def query_receita_per_capita(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-6.04: Receita per Capita.

    Unidade: R$/habitante
    Granularidade: Município/Ano
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"f.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"f.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"f.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""

    return f"""
    WITH receitas AS (
        SELECT
            id_municipio,
            ano,
            ROUND(SUM(valor), 2) AS receita_total
        FROM
            `{BD_DADOS_FINBRA}`
        WHERE
            conta_bd = 'Receitas Correntes'
            AND estagio_bd = 'Receitas Brutas Realizadas'
            AND valor IS NOT NULL
            {f"AND {where_sql.replace('f.', '')}" if where_sql else ""}
        GROUP BY
            id_municipio,
            ano
    )
    SELECT
        r.id_municipio,
        dir.nome AS nome_municipio,
        r.ano,
        ROUND(r.receita_total / NULLIF(pop.populacao, 0), 2) AS receita_per_capita
    FROM
        receitas r
    INNER JOIN
        `basedosdados.br_ibge_populacao.municipio` pop
        ON r.id_municipio = pop.id_municipio AND r.ano = pop.ano
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON r.id_municipio = dir.id_municipio
    WHERE
        pop.populacao IS NOT NULL
        AND pop.populacao > 0
    ORDER BY
        r.ano DESC,
        dir.nome
    """


def query_crescimento_receita(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-6.05: Crescimento da Receita (%).

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_clause = f"WHERE id_municipio = '{id_municipio}'" if id_municipio else ""
    where_ano = f"AND ano <= {ano}" if ano else ""

    return f"""
    WITH receita_anual AS (
        SELECT
            id_municipio,
            ano,
            SUM(valor) AS receita_total
        FROM
            `{BD_DADOS_FINBRA}`
        WHERE
            conta_bd = 'Receitas Correntes'
            AND estagio_bd = 'Receitas Brutas Realizadas'
            AND valor IS NOT NULL
            {where_clause}
            {where_ano}
        GROUP BY
            id_municipio,
            ano
    )
    SELECT
        a.id_municipio,
        dir.nome AS nome_municipio,
        a.ano,
        ROUND((a.receita_total - b.receita_total) * 100.0 / NULLIF(b.receita_total, 0), 2) AS crescimento_receita_pct
    FROM
        receita_anual a
    INNER JOIN
        receita_anual b ON a.id_municipio = b.id_municipio AND a.ano = b.ano + 1
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON a.id_municipio = dir.id_municipio
    ORDER BY
        a.ano DESC,
        dir.nome
    """


def query_icms_por_tonelada(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-6.06: ICMS por Tonelada Movimentada.

    Unidade: R$/ton
    Granularidade: Município/Ano
    """
    where_finbra = []
    where_carga = []

    if id_municipio:
        where_finbra.append(f"id_municipio = '{id_municipio}'")
        where_carga.append(f"municipio = '{id_municipio}'")
    if ano:
        where_finbra.append(f"ano = {ano}")
        where_carga.append(f"ano = {ano}")
    elif ano_inicio and ano_fim:
        where_finbra.append(f"ano BETWEEN {ano_inicio} AND {ano_fim}")
        where_carga.append(f"ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_finbra_sql = "\n        AND ".join(where_finbra) if where_finbra else ""
    where_carga_sql = "\n        AND ".join(where_carga) if where_carga else ""

    return f"""
    WITH icms AS (
        SELECT
            id_municipio,
            ano,
            SUM(valor) AS icms_total
        FROM
            `{BD_DADOS_FINBRA}`
        WHERE
            conta_bd = 'Cota-Parte do ICMS'
            AND estagio_bd = 'Receitas Brutas Realizadas'
            AND valor IS NOT NULL
            {f"AND {where_finbra_sql}" if where_finbra_sql else ""}
        GROUP BY
            id_municipio,
            ano
    ),
    tonelagem AS (
        SELECT
            municipio AS id_municipio,
            CAST(ano AS INT64) AS ano,
            SUM(vlpesocargabruta_oficial) AS tonelagem_total
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
        WHERE
            vlpesocargabruta_oficial IS NOT NULL
            {f"AND {where_carga_sql}" if where_carga_sql else ""}
        GROUP BY
            municipio,
            ano
    )
    SELECT
        COALESCE(i.id_municipio, t.id_municipio) AS id_municipio,
        dir.nome AS nome_municipio,
        COALESCE(i.ano, t.ano) AS ano,
        COALESCE(i.icms_total, 0) AS icms_total,
        COALESCE(t.tonelagem_total, 0) AS tonelagem_total,
        ROUND(COALESCE(i.icms_total, 0) / NULLIF(COALESCE(t.tonelagem_total, 0), 0), 4) AS icms_por_tonelada
    FROM
        icms i
    FULL OUTER JOIN
        tonelagem t USING (id_municipio, ano)
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON COALESCE(i.id_municipio, t.id_municipio) = dir.id_municipio
    ORDER BY
        COALESCE(i.ano, t.ano) DESC,
        dir.nome
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
}


def get_query_module6(indicator_code: str) -> callable:
    """Retorna a função de query para um indicador do Módulo 6."""
    if indicator_code not in QUERIES_MODULE_6:
        raise ValueError(f"Indicador {indicator_code} não encontrado no Módulo 6")
    return QUERIES_MODULE_6[indicator_code]
