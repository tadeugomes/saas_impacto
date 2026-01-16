"""
Queries BigQuery para o Módulo 7 - Índices Sintéticos.

Este módulo contém as queries SQL para cálculo dos 7 indicadores
do Módulo 7 de índices sintéticos compostos.

NOTA: Usa view oficial ANTAQ v_carga_metodologia_oficial para dados de carga.
"""

from typing import Optional


# ============================================================================
# Constants
# ============================================================================

# Dataset ANTAQ no BigQuery
ANTAQ_DATASET = "antaqdados.br_antaq_estatistico_aquaviario"

# View oficial metodológica ANTAQ (OBRIGATÓRIO)
VIEW_CARGA_METODOLOGIA_OFICIAL = f"{ANTAQ_DATASET}.v_carga_metodologia_oficial"

# View de atracação (para alguns indicadores)
VIEW_ATRACAO_VALIDADA = f"{ANTAQ_DATASET}.v_atracacao_validada"


# ============================================================================
# Módulo 7: Queries SQL Templates
# ============================================================================

def query_indice_eficiencia_operacional(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-7.01: Índice de Eficiência Operacional.

    Componentes:
    - Tonelagem movimentada
    - Número de atracações

    Unidade: Índice (0-100)
    Granularidade: Instalação/Ano
    """
    where_clause = f"AND porto_atracacao = '{id_instalacao}'" if id_instalacao else ""
    where_ano = f"AND ano = {ano}" if ano else ""

    return f"""
    WITH metricas AS (
        SELECT
            porto_atracacao AS id_instalacao,
            CAST(ano AS INT64) AS ano,
            SUM(vlpesocargabruta_oficial) AS tonelagem,
            COUNT(DISTINCT idatracacao) AS atracoes
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
        WHERE
            vlpesocargabruta_oficial IS NOT NULL
            {where_clause}
            {where_ano}
        GROUP BY
            porto_atracacao,
            ano
    ),
    normalizacao AS (
        SELECT
            id_instalacao,
            ano,
            (tonelagem - MIN(tonelagem) OVER()) / NULLIF(MAX(tonelagem) OVER() - MIN(tonelagem) OVER(), 0) * 100 AS norm_ton,
            (atracoes - MIN(atracoes) OVER()) / NULLIF(MAX(atracoes) OVER() - MIN(atracoes) OVER(), 0) * 100 AS norm_attr
        FROM
            metricas
    )
    SELECT
        id_instalacao,
        ano,
        ROUND((norm_ton + norm_attr) / 2, 2) AS indice_eficiencia
    FROM
        normalizacao
    ORDER BY
        ano DESC,
        indice_eficiencia DESC
    """


def query_indice_relevancia(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-7.02: Índice de Relevância Portuária.

    Componentes:
    - Tonelagem movimentada
    - Número de atracações

    Unidade: Índice (0-100)
    Granularidade: Instalação/Ano
    """
    where_clause = f"WHERE porto_atracacao = '{id_instalacao}'" if id_instalacao else ""
    where_ano = f"AND ano = {ano}" if ano else ""

    return f"""
    WITH metricas AS (
        SELECT
            porto_atracacao AS id_instalacao,
            CAST(ano AS INT64) AS ano,
            SUM(vlpesocargabruta_oficial) AS tonelagem,
            COUNT(DISTINCT idatracacao) AS atracoes
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
        WHERE
            vlpesocargabruta_oficial IS NOT NULL
            {where_clause}
            {where_ano}
        GROUP BY
            porto_atracacao,
            ano
    ),
    normalizacao AS (
        SELECT
            id_instalacao,
            ano,
            (tonelagem - MIN(tonelagem) OVER()) / NULLIF(MAX(tonelagem) OVER() - MIN(tonelagem) OVER(), 0) * 100 AS norm_ton,
            (atracoes - MIN(atracoes) OVER()) / NULLIF(MAX(atracoes) OVER() - MIN(atracoes) OVER(), 0) * 100 AS norm_attr
        FROM
            metricas
    )
    SELECT
        id_instalacao,
        ano,
        ROUND((norm_ton + norm_attr) / 2, 2) AS indice_relevancia
    FROM
        normalizacao
    ORDER BY
        ano DESC,
        indice_relevancia DESC
    """


def query_indice_integracao(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-7.03: Índice de Integração Multimodal.

    Componentes:
    - Modais utilizados (baseado em tipo de navegação)
    - Diversificação de tipos de carga

    Unidade: Índice (0-100)
    Granularidade: Instalação/Ano
    """
    where_clause = f"WHERE porto_atracacao = '{id_instalacao}'" if id_instalacao else ""
    where_ano = f"AND ano = {ano}" if ano else ""

    return f"""
    WITH modais AS (
        SELECT
            porto_atracacao AS id_instalacao,
            CAST(ano AS INT64) AS ano,
            COUNT(DISTINCT tipo_de_navegacao_da_atracacao) AS modais_distintos
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
        WHERE
            tipo_de_navegacao_da_atracacao IS NOT NULL
            {where_clause}
            {where_ano}
        GROUP BY
            porto_atracacao,
            ano
    ),
    tipos_carga AS (
        SELECT
            porto_atracacao AS id_instalacao,
            CAST(ano AS INT64) AS ano,
            COUNT(DISTINCT sentido) AS tipos_carga_distintos
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
        WHERE
            sentido IS NOT NULL
            {where_clause}
            {where_ano}
        GROUP BY
            porto_atracacao,
            ano
    ),
    maximos AS (
        SELECT
            MAX(modais_distintos) AS max_modais,
            MAX(tipos_carga_distintos) AS max_tipos
        FROM
            modais,
            tipos_carga
    )
    SELECT
        COALESCE(m.id_instalacao, t.id_instalacao) AS id_instalacao,
        COALESCE(m.ano, t.ano) AS ano,
        ROUND(
            (COALESCE(m.modais_distintos, 0) * 100.0 / mx.max_modais +
             COALESCE(t.tipos_carga_distintos, 0) * 100.0 / mx.max_tipos) / 2,
            2
        ) AS indice_integracao
    FROM
        modais m
    FULL OUTER JOIN
        tipos_carga t USING (id_instalacao, ano)
    CROSS JOIN
        maximos mx
    ORDER BY
        ano DESC,
        indice_integracao DESC
    """


def query_indice_concentracao_portuaria(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-7.04: Índice de Concentração Portuária.

    Score baseado em participação na tonelagem nacional.

    Unidade: Índice (0-100)
    Granularidade: Instalação/Ano
    """
    where_ano = f"WHERE ano = {ano}" if ano else ""

    return f"""
    WITH totais AS (
        SELECT
            ano,
            SUM(vlpesocargabruta_oficial) AS total_nacional
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
        {where_ano}
        GROUP BY
            ano
    ),
    portos AS (
        SELECT
            porto_atracacao AS id_instalacao,
            CAST(ano AS INT64) AS ano,
            SUM(vlpesocargabruta_oficial) AS tonelagem
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
        WHERE
            vlpesocargabruta_oficial IS NOT NULL
        GROUP BY
            porto_atracacao,
            ano
    )
    SELECT
        p.id_instalacao,
        p.ano,
        ROUND(p.tonelagem * 100.0 / t.total_nacional, 4) AS indice_concentracao
    FROM
        portos p
    INNER JOIN
        totais t ON p.ano = t.ano
    ORDER BY
        p.ano DESC,
        indice_concentracao DESC
    """


def query_ranking_portuarios(
    ano: Optional[int] = None,
    limit: int = 50,
) -> str:
    """
    IND-7.05: Ranking de Portos por Eficiência.

    Unidade: Posição no ranking
    Granularidade: Instalação/Ano
    """
    where_ano = f"WHERE ano = {ano}" if ano else ""

    return f"""
    WITH metricas AS (
        SELECT
            porto_atracacao AS id_instalacao,
            CAST(ano AS INT64) AS ano,
            SUM(vlpesocargabruta_oficial) AS tonelagem,
            COUNT(DISTINCT idatracacao) AS atracoes,
            ROUND(SUM(vlpesocargabruta_oficial) / NULLIF(COUNT(DISTINCT idatracacao), 0), 2) AS carga_por_atracacao
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
        WHERE
            vlpesocargabruta_oficial IS NOT NULL
            {where_ano}
        GROUP BY
            porto_atracacao,
            ano
    ),
    pontuacao AS (
        SELECT
            id_instalacao,
            ano,
            tonelagem,
            atracoes,
            carga_por_atracacao,
            RANK() OVER (ORDER BY tonelagem DESC) AS rank_ton,
            RANK() OVER (ORDER BY atracoes DESC) AS rank_attr,
            RANK() OVER (ORDER BY carga_por_atracacao DESC) AS rank_prod
        FROM
            metricas
    )
    SELECT
        id_instalacao,
        ano,
        tonelagem,
        atracoes,
        carga_por_atracacao,
        rank_ton,
        rank_attr,
        rank_prod,
        ROW_NUMBER() OVER (ORDER BY (rank_ton + rank_attr + rank_prod) ASC) AS ranking_geral
    FROM
        pontuacao
    ORDER BY
        ranking_geral
    LIMIT {limit * 2}
    """


def query_indice_benchmark(
    id_instalacao: str,
    ano: Optional[int] = None,
) -> str:
    """
    IND-7.06: Índice de Benchmark (posição relativa).

    Compara a instalação com a média dos top 10.

    Unidade: Índice (0-200, onde 100 = média do top 10)
    Granularidade: Instalação/Ano
    """
    where_ano = f"AND ano = {ano}" if ano else ""

    return f"""
    WITH metricas AS (
        SELECT
            porto_atracacao AS id_instalacao,
            CAST(ano AS INT64) AS ano,
            SUM(vlpesocargabruta_oficial) AS tonelagem,
            COUNT(DISTINCT idatracacao) AS atracoes
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
        WHERE
            vlpesocargabruta_oficial IS NOT NULL
        GROUP BY
            porto_atracacao,
            ano
    ),
    top10 AS (
        SELECT
            ano,
            AVG(tonelagem) AS avg_tonelagem_top10,
            AVG(atracoes) AS avg_atracacoes_top10
        FROM (
            SELECT
                id_instalacao,
                ano,
                tonelagem,
                atracoes,
                RANK() OVER (PARTITION BY ano ORDER BY tonelagem DESC) AS ranking
            FROM
                metricas
        ) ranked
        WHERE
            ranking <= 10
            {where_ano}
        GROUP BY
            ano
    ),
    instalacao_alvo AS (
        SELECT
            id_instalacao,
            ano,
            tonelagem,
            atracoes
        FROM
            metricas
        WHERE
            id_instalacao = '{id_instalacao}'
            {where_ano}
    )
    SELECT
        i.id_instalacao,
        i.ano,
        i.tonelagem,
        i.atracoes,
        t.avg_tonelagem_top10,
        t.avg_atracacoes_top10,
        ROUND(
            (i.tonelagem * 50.0 / NULLIF(t.avg_tonelagem_top10, 0) +
             i.atracoes * 50.0 / NULLIF(t.avg_atracacoes_top10, 0)),
            2
        ) AS indice_benchmark
    FROM
        instalacao_alvo i
    CROSS JOIN
        top10 t
    ORDER BY
        i.ano DESC
    """


def query_indice_variacao_anual(
    id_instalacao: Optional[str] = None,
    anos: int = 3,
) -> str:
    """
    IND-7.07: Índice de Variação Anual Consolidado.

    Média da variação percentual dos últimos N anos.

    Unidade: Percentual
    Granularidade: Instalação
    """
    where_clause = f"WHERE porto_atracacao = '{id_instalacao}'" if id_instalacao else ""

    return f"""
    WITH tonelagem_anual AS (
        SELECT
            porto_atracacao AS id_instalacao,
            CAST(ano AS INT64) AS ano,
            SUM(vlpesocargabruta_oficial) AS tonelagem
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
        WHERE
            vlpesocargabruta_oficial IS NOT NULL
            {where_clause}
        GROUP BY
            porto_atracacao,
            ano
        ORDER BY
            ano DESC
        LIMIT {anos * 2}
    ),
    variacao_anual AS (
        SELECT
            a.id_instalacao,
            a.ano,
            (a.tonelagem - b.tonelagem) * 100.0 / NULLIF(b.tonelagem, 0) AS variacao_pct
        FROM
            tonelagem_anual a
        INNER JOIN
            tonelagem_anual b ON a.id_instalacao = b.id_instalacao AND a.ano = b.ano + 1
    )
    SELECT
        id_instalacao,
        ROUND(AVG(variacao_pct), 2) AS variacao_media_anual_pct,
        COUNT(*) AS anos_analisados
    FROM
        variacao_anual
    GROUP BY
        id_instalacao
    ORDER BY
        variacao_media_anual_pct DESC
    """


# ============================================================================
# Dicionário de Queries
# ============================================================================

QUERIES_MODULE_7 = {
    "IND-7.01": query_indice_eficiencia_operacional,
    "IND-7.02": query_indice_relevancia,
    "IND-7.03": query_indice_integracao,
    "IND-7.04": query_indice_concentracao_portuaria,
    "IND-7.05": query_ranking_portuarios,
    "IND-7.06": query_indice_benchmark,
    "IND-7.07": query_indice_variacao_anual,
}


def get_query_module7(indicator_code: str) -> callable:
    """Retorna a função de query para um indicador do Módulo 7."""
    if indicator_code not in QUERIES_MODULE_7:
        raise ValueError(f"Indicador {indicator_code} não encontrado no Módulo 7")
    return QUERIES_MODULE_7[indicator_code]
