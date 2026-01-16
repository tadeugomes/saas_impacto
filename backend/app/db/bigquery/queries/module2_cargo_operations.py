"""
Queries BigQuery para o Módulo 2 - Operações de Carga.

Este módulo contém as queries SQL para cálculo dos 13 indicadores
do Módulo 2 de operações de carga.

ATALHO: Usa a view oficial v_carga_metodologia_oficial conforme
padrão ANTAQ (planejamento/docs/role_sql_antaq_bigquery/PADRAO_BIGQUERY_ANTAQ.md)
"""

from typing import Optional


# ============================================================================
# Constants
# ============================================================================

# Dataset ANTAQ no BigQuery
ANTAQ_DATASET = "antaqdados.br_antaq_estatistico_aquaviario"

# View oficial metodológica ANTAQ (OBRIGATÓRIO)
VIEW_CARGA_METODOLOGIA_OFICIAL = f"{ANTAQ_DATASET}.v_carga_metodologia_oficial"


# ============================================================================
# Módulo 2: Queries SQL Templates
# ============================================================================

def query_carga_total_movimentada(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-2.01: Total Carga Movimentada [UNCTAD].

    Unidade: Toneladas
    Granularidade: Instalação/Ano
    """
    where_clauses = []
    if id_instalacao:
        where_clauses.append(f"AND porto_atracacao = '{id_instalacao}'")
    if ano:
        where_clauses.append(f"AND ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"AND ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n    ".join(where_clauses) if where_clauses else ""

    return f"""
    SELECT
        porto_atracacao AS id_instalacao,
        CAST(ano AS INT64) AS ano,
        ROUND(SUM(vlpesocargabruta_oficial), 2) AS tonelagem_total
    FROM
        `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
    WHERE
        vlpesocargabruta_oficial IS NOT NULL
        {where_sql}
    GROUP BY
        porto_atracacao,
        ano
    ORDER BY
        ano DESC,
        id_instalacao
    """


def query_teus_movimentados(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-2.02: TEUs Movimentados [UNCTAD].

    Unidade: TEUs
    Granularidade: Instalação/Ano
    """
    where_clauses = ["teu IS NOT NULL", "teu > 0"]
    if id_instalacao:
        where_clauses.append(f"AND porto_atracacao = '{id_instalacao}'")
    if ano:
        where_clauses.append(f"AND ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"AND ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n    ".join(where_clauses)

    return f"""
    SELECT
        porto_atracacao AS id_instalacao,
        CAST(ano AS INT64) AS ano,
        SUM(teu) AS total_teus
    FROM
        `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
    WHERE
        {where_sql}
    GROUP BY
        porto_atracacao,
        ano
    ORDER BY
        ano DESC,
        id_instalacao
    """


def query_passageiros_ferry(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-2.03: Total Passageiros Ferry [NECTAD].

    NOTA: Este indicador não está disponível na view de carga.
    Retorna 0 como placeholder - requer dados específicos de passageiros.

    Unidade: Contagem
    Granularidade: Instalação/Ano
    """
    return f"""
    SELECT
        '{id_instalacao or 'TODOS'}' AS id_instalacao,
        {ano or 2024} AS ano,
        0 AS passageiros_ferry
    """


def query_passageiros_cruzeiro(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-2.04: Total Passageiros Cruzeiro [UNCTAD].

    NOTA: Este indicador não está disponível na view de carga.
    Retorna 0 como placeholder - requer dados específicos de passageiros.

    Unidade: Contagem
    Granularidade: Instalação/Ano
    """
    return f"""
    SELECT
        '{id_instalacao or 'TODOS'}' AS id_instalacao,
        {ano or 2024} AS ano,
        0 AS passageiros_cruzeiro
    """


def query_carga_media_atracacao(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-2.05: Carga Média por Atracação [UNCTAD].

    Unidade: Toneladas/Atracação
    Granularidade: Instalação/Ano
    """
    where_clauses = []
    if id_instalacao:
        where_clauses.append(f"AND porto_atracacao = '{id_instalacao}'")
    if ano:
        where_clauses.append(f"AND ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"AND ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n    ".join(where_clauses) if where_clauses else ""

    return f"""
    SELECT
        porto_atracacao AS id_instalacao,
        CAST(ano AS INT64) AS ano,
        ROUND(SUM(vlpesocargabruta_oficial) / NULLIF(COUNT(DISTINCT idatracacao), 0), 2) AS carga_media_atracacao
    FROM
        `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
    WHERE
        vlpesocargabruta_oficial IS NOT NULL
        {where_sql}
    GROUP BY
        porto_atracacao,
        ano
    ORDER BY
        ano DESC,
        id_instalacao
    """


def query_produtividade_bruta(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-2.06: Produtividade Bruta (ton/h) [UNCTAD].

    Unidade: Toneladas/Hora
    Granularidade: Instalação/Ano

    NOTA: Requer JOIN com tabela de atracação para calcular tempo de operação.
    Como não temos tabela de tempos, calcula uma proxy simples.
    """
    where_clauses = []
    if id_instalacao:
        where_clauses.append(f"AND porto_atracacao = '{id_instalacao}'")
    if ano:
        where_clauses.append(f"AND ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"AND ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n    ".join(where_clauses) if where_clauses else ""

    return f"""
    WITH metricas AS (
        SELECT
            porto_atracacao,
            CAST(ano AS INT64) AS ano,
            SUM(vlpesocargabruta_oficial) AS tonelagem_total,
            COUNT(DISTINCT idatracacao) AS total_atracacoes
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
        WHERE
            vlpesocargabruta_oficial IS NOT NULL
            {where_sql}
        GROUP BY
            porto_atracacao,
            ano
    )
    SELECT
        porto_atracacao AS id_instalacao,
        ano,
        ROUND(tonelagem_total / NULLIF(total_atracacoes * 24, 0), 2) AS produtividade_ton_hora
    FROM
        metricas
    ORDER BY
        ano DESC,
        id_instalacao
    """


def query_produtividade_granel_solido(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-2.07: Produtividade Granel Sólido [UNCTAD].

    Unidade: Toneladas/Hora
    Granularidade: Instalação/Ano

    NOTA: Filtra por mercadorias de granel sólido.
    """
    where_clauses = []
    if id_instalacao:
        where_clauses.append(f"AND porto_atracacao = '{id_instalacao}'")
    if ano:
        where_clauses.append(f"AND ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"AND ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n    ".join(where_clauses) if where_clauses else ""

    return f"""
    WITH mercadorias_granel_solido AS (
        -- Códigos de mercadorias típicas de granel sólido
        SELECT DISTINCT cdmercadoria
        FROM `antaqdados.br_antaq_estatistico_aquaviario.mercadoria_carga`
        WHERE LOWER(grupo_mercadoria) LIKE '%mineral%'
           OR LOWER(grupo_mercadoria) LIKE '%granel%'
           OR LOWER(subgrupo_mercadoria) LIKE '%sólido%'
    ),
    metricas AS (
        SELECT
            c.porto_atracacao,
            CAST(c.ano AS INT64) AS ano,
            SUM(c.vlpesocargabruta_oficial) AS tonelagem_total,
            COUNT(DISTINCT c.idatracacao) AS total_atracacoes
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}` c
        INNER JOIN
            mercadorias_granel_solido m ON c.cdmercadoria = m.cdmercadoria
        WHERE
            c.vlpesocargabruta_oficial IS NOT NULL
            {where_sql}
        GROUP BY
            c.porto_atracacao,
            c.ano
    )
    SELECT
        porto_atracacao AS id_instalacao,
        ano,
        ROUND(tonelagem_total / NULLIF(total_atracacoes * 24, 0), 2) AS produtividade_granel_solido
    FROM
        metricas
    ORDER BY
        ano DESC,
        id_instalacao
    """


def query_produtividade_granel_liquido(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-2.08: Produtividade Granel Líquido [UNCTAD].

    Unidade: Toneladas/Hora
    Granularidade: Instalação/Ano

    NOTA: Filtra por mercadorias de granel líquido.
    """
    where_clauses = []
    if id_instalacao:
        where_clauses.append(f"AND porto_atracacao = '{id_instalacao}'")
    if ano:
        where_clauses.append(f"AND ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"AND ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n    ".join(where_clauses) if where_clauses else ""

    return f"""
    WITH mercadorias_granel_liquido AS (
        -- Códigos de mercadorias típicas de granel líquido
        SELECT DISTINCT cdmercadoria
        FROM `antaqdados.br_antaq_estatistico_aquaviario.mercadoria_carga`
        WHERE LOWER(grupo_mercadoria) LIKE '%líquido%'
           OR LOWER(grupo_mercadoria) LIKE '%petróleo%'
           OR LOWER(subgrupo_mercadoria) LIKE '%líquido%'
    ),
    metricas AS (
        SELECT
            c.porto_atracacao,
            CAST(c.ano AS INT64) AS ano,
            SUM(c.vlpesocargabruta_oficial) AS tonelagem_total,
            COUNT(DISTINCT c.idatracacao) AS total_atracacoes
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}` c
        INNER JOIN
            mercadorias_granel_liquido m ON c.cdmercadoria = m.cdmercadoria
        WHERE
            c.vlpesocargabruta_oficial IS NOT NULL
            {where_sql}
        GROUP BY
            c.porto_atracacao,
            c.ano
    )
    SELECT
        porto_atracacao AS id_instalacao,
        ano,
        ROUND(tonelagem_total / NULLIF(total_atracacoes * 24, 0), 2) AS produtividade_granel_liquido
    FROM
        metricas
    ORDER BY
        ano DESC,
        id_instalacao
    """


def query_movimentos_hora_conteiner(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-2.09: Movimentos/Hora Contêiner (LPSPH) [UNCTAD].

    Unidade: Movimentos/Hora
    Granularidade: Instalação/Ano

    NOTA: Calcula TEUs por atracação como proxy.
    """
    where_clauses = ["teu IS NOT NULL", "teu > 0"]
    if id_instalacao:
        where_clauses.append(f"AND porto_atracacao = '{id_instalacao}'")
    if ano:
        where_clauses.append(f"AND ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"AND ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n    ".join(where_clauses)

    return f"""
    SELECT
        porto_atracacao AS id_instalacao,
        CAST(ano AS INT64) AS ano,
        ROUND(SUM(teu) / NULLIF(COUNT(DISTINCT idatracacao) * 24, 0), 2) AS lifts_per_ship_hour
    FROM
        `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
    WHERE
        {where_sql}
    GROUP BY
        porto_atracacao,
        ano
    ORDER BY
        ano DESC,
        id_instalacao
    """


def query_toneladas_por_hectare(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-2.10: Toneladas por Hectare [UNCTAD].

    Unidade: Toneladas/Hectare
    Granularidade: Instalação/Ano

    NOTA: Requer dados de área física do porto (não disponível na view).
    Retorna tonelagem total como placeholder.
    """
    where_clauses = []
    if id_instalacao:
        where_clauses.append(f"AND porto_atracacao = '{id_instalacao}'")
    if ano:
        where_clauses.append(f"AND ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"AND ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n    ".join(where_clauses) if where_clauses else ""

    return f"""
    SELECT
        porto_atracacao AS id_instalacao,
        CAST(ano AS INT64) AS ano,
        ROUND(SUM(vlpesocargabruta_oficial), 2) AS tonelagem_total
    FROM
        `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
    WHERE
        vlpesocargabruta_oficial IS NOT NULL
        {where_sql}
    GROUP BY
        porto_atracacao,
        ano
    ORDER BY
        ano DESC,
        id_instalacao
    """


def query_toneladas_por_metro_cais(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-2.11: Toneladas por Metro de Cais [UNCTAD].

    Unidade: Toneladas/Metro
    Granularidade: Instalação/Ano

    NOTA: Requer dados de extensão de cais (não disponível na view).
    Retorna tonelagem total como placeholder.
    """
    where_clauses = []
    if id_instalacao:
        where_clauses.append(f"AND porto_atracacao = '{id_instalacao}'")
    if ano:
        where_clauses.append(f"AND ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"AND ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n    ".join(where_clauses) if where_clauses else ""

    return f"""
    SELECT
        porto_atracacao AS id_instalacao,
        CAST(ano AS INT64) AS ano,
        ROUND(SUM(vlpesocargabruta_oficial), 2) AS tonelagem_total
    FROM
        `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
    WHERE
        vlpesocargabruta_oficial IS NOT NULL
        {where_sql}
    GROUP BY
        porto_atracacao,
        ano
    ORDER BY
        ano DESC,
        id_instalacao
    """


def query_mix_carga(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-2.12: Mix de Carga.

    Unidade: Percentual por tipo
    Granularidade: Instalação/Ano/Tipo
    """
    where_clauses = []
    if id_instalacao:
        where_clauses.append(f"AND porto_atracacao = '{id_instalacao}'")
    if ano:
        where_clauses.append(f"AND ano = {ano}")

    where_sql = "\n    ".join(where_clauses) if where_clauses else ""

    return f"""
    WITH tonelagens AS (
        SELECT
            porto_atracacao AS id_instalacao,
            CAST(ano AS INT64) AS ano,
            sentido AS tipo_carga,
            SUM(vlpesocargabruta_oficial) AS tonelagem
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
        WHERE
            vlpesocargabruta_oficial IS NOT NULL
            AND sentido IS NOT NULL
            {where_sql}
        GROUP BY
            porto_atracacao,
            ano,
            sentido
    ),
    totais AS (
        SELECT
            id_instalacao,
            ano,
            SUM(tonelagem) AS total_geral
        FROM
            tonelagens
        GROUP BY
            id_instalacao,
            ano
    )
    SELECT
        t.id_instalacao,
        t.ano,
        t.tipo_carga,
        t.tonelagem,
        ROUND(t.tonelagem * 100.0 / NULLIF(tot.total_geral, 0), 2) AS percentual
    FROM
        tonelagens t
    INNER JOIN
        totais tot ON t.id_instalacao = tot.id_instalacao AND t.ano = tot.ano
    ORDER BY
        t.ano DESC,
        t.id_instalacao,
        percentual DESC
    """


def query_sazonalidade_mensal(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-2.13: Sazonalidade Mensal.

    Unidade: Índice (100 = média)
    Granularidade: Instalação/Ano/Mês
    """
    where_clauses = []
    if id_instalacao:
        where_clauses.append(f"AND porto_atracacao = '{id_instalacao}'")
    if ano:
        where_clauses.append(f"AND ano = {ano}")

    where_sql = "\n    ".join(where_clauses) if where_clauses else ""

    return f"""
    WITH mensal AS (
        SELECT
            porto_atracacao AS id_instalacao,
            CAST(ano AS INT64) AS ano,
            CAST(mes AS INT64) AS mes,
            SUM(vlpesocargabruta_oficial) AS tonelagem_mes
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
        WHERE
            vlpesocargabruta_oficial IS NOT NULL
            {where_sql}
        GROUP BY
            porto_atracacao,
            ano,
            mes
    ),
    media_anual AS (
        SELECT
            id_instalacao,
            ano,
            AVG(tonelagem_mes) AS media_mensal
        FROM
            mensal
        GROUP BY
            id_instalacao,
            ano
    )
    SELECT
        m.id_instalacao,
        m.ano,
        m.mes,
        m.tonelagem_mes,
        ROUND(m.tonelagem_mes / NULLIF(a.media_mensal, 0) * 100, 2) AS indice_sazonalidade
    FROM
        mensal m
    INNER JOIN
        media_anual a ON m.id_instalacao = a.id_instalacao AND m.ano = a.ano
    ORDER BY
        m.ano DESC,
        m.id_instalacao,
        m.mes
    """


# ============================================================================
# Dicionário de Queries
# ============================================================================

QUERIES_MODULE_2 = {
    "IND-2.01": query_carga_total_movimentada,
    "IND-2.02": query_teus_movimentados,
    "IND-2.03": query_passageiros_ferry,
    "IND-2.04": query_passageiros_cruzeiro,
    "IND-2.05": query_carga_media_atracacao,
    "IND-2.06": query_produtividade_bruta,
    "IND-2.07": query_produtividade_granel_solido,
    "IND-2.08": query_produtividade_granel_liquido,
    "IND-2.09": query_movimentos_hora_conteiner,
    "IND-2.10": query_toneladas_por_hectare,
    "IND-2.11": query_toneladas_por_metro_cais,
    "IND-2.12": query_mix_carga,
    "IND-2.13": query_sazonalidade_mensal,
}


def get_query_module2(indicator_code: str) -> callable:
    """Retorna a função de query para um indicador do Módulo 2."""
    if indicator_code not in QUERIES_MODULE_2:
        raise ValueError(f"Indicador {indicator_code} não encontrado no Módulo 2")
    return QUERIES_MODULE_2[indicator_code]
