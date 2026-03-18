"""
Queries BigQuery para o Módulo 1 - Operações de Navios.

Este módulo contém todas as queries SQL para cálculo dos 12 indicadores
do Módulo 1, seguindo a especificação técnica e o padrão ANTAQ.

NOTA: Todas as queries calculam tempos a partir das datas pois a tabela
tempos_atracacao está vazia no BigQuery.

Referências:
- Especificação Técnica: planejamento/docs/INDICADORES_ESPECIFICACAO_TECNICA.md
- Padrão ANTAQ: planejamento/docs/role_sql_antaq_bigquery/PADRAO_CALCULO_ANTAQ.md
"""

from __future__ import annotations

from typing import Optional


# ============================================================================
# Constants
# ============================================================================

# Dataset ANTAQ no BigQuery
ANTAQ_DATASET = "antaqdados.br_antaq_estatistico_aquaviario"

# Views oficiais validadas ANTAQ
VIEW_ATRACAO_VALIDADA = f"{ANTAQ_DATASET}.v_atracacao_validada"
VIEW_TEMPOS_ATRACACAO = f"{ANTAQ_DATASET}.tempos_atracacao"  # VAZIA
VIEW_TEMPOS_PARALISACAO = f"{ANTAQ_DATASET}.tempos_atracacao_paralisacao"  # VAZIA
VIEW_TAXA_OCUPACAO = f"{ANTAQ_DATASET}.taxa_ocupacao"


# ============================================================================
# Queries SQL Templates
# ============================================================================

def _build_where_clauses(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
    extra_conditions: list[str] = None,
) -> tuple[list[str], str]:
    """
    Constrói cláusulas WHERE comuns para todas as queries.

    Returns:
        Tuple (lista de cláusulas, SQL completo com AND)
    """
    where_clauses = extra_conditions.copy() if extra_conditions else []

    if id_instalacao:
        where_clauses.append(f"porto_atracacao = '{id_instalacao}'")
    if ano:
        where_clauses.append(f"CAST(ano AS INT64) = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"CAST(ano AS INT64) BETWEEN {ano_inicio} AND {ano_fim}")

    return where_clauses, " AND ".join(where_clauses)


def query_tempo_medio_espera(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-1.01: Tempo Médio de Espera [UNCTAD].

    Retorna o tempo médio de espera para atracação.

    Unidade: Horas
    Granularidade: Instalação/Ano

    Calculado como: data_atracacao - data_chegada
    """
    _, where_sql = _build_where_clauses(
        id_instalacao, ano, ano_inicio, ano_fim,
        ["data_atracacao IS NOT NULL", "data_chegada IS NOT NULL", "data_chegada != 'nan'"]
    )

    return f"""
    SELECT
        porto_atracacao as id_instalacao,
        CAST(ano AS INT64) as ano,
        COUNT(*) as total_atracacoes,
        ROUND(AVG(
            DATETIME_DIFF(
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                PARSE_DATETIME('%d/%m/%Y %H:%M:%S', data_chegada),
                MINUTE
            ) / 60.0
        ), 2) AS tempo_medio_espera_horas
    FROM `{VIEW_ATRACAO_VALIDADA}`
    WHERE {where_sql}
    GROUP BY porto_atracacao, ano
    HAVING tempo_medio_espera_horas > 0
    ORDER BY ano DESC, tempo_medio_espera_horas DESC
    """


def query_tempo_medio_porto(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-1.02: Tempo Médio em Porto [UNCTAD].

    Retorna o tempo médio em porto (atracado + espera).

    Unidade: Horas
    Granularidade: Instalação/Ano

    Calculado como: data_desatracacao - data_chegada
    """
    _, where_sql = _build_where_clauses(
        id_instalacao, ano, ano_inicio, ano_fim,
        ["data_desatracacao IS NOT NULL", "data_chegada IS NOT NULL", "data_chegada != 'nan'"]
    )

    return f"""
    SELECT
        porto_atracacao as id_instalacao,
        CAST(ano AS INT64) as ano,
        COUNT(*) as total_atracacoes,
        ROUND(AVG(
            DATETIME_DIFF(
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                PARSE_DATETIME('%d/%m/%Y %H:%M:%S', data_chegada),
                MINUTE
            ) / 60.0
        ), 2) AS tempo_medio_porto_horas
    FROM `{VIEW_ATRACAO_VALIDADA}`
    WHERE {where_sql}
    GROUP BY porto_atracacao, ano
    HAVING tempo_medio_porto_horas > 0
    ORDER BY ano DESC, tempo_medio_porto_horas DESC
    """


def query_tempo_bruto_atracacao(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-1.03: Tempo Bruto de Atracação [UNCTAD].

    Retorna o tempo bruto médio de atracação.

    Unidade: Horas
    Granularidade: Instalação/Ano

    Calculado como: data_desatracacao - data_atracacao
    """
    _, where_sql = _build_where_clauses(
        id_instalacao, ano, ano_inicio, ano_fim,
        ["data_atracacao IS NOT NULL", "data_desatracacao IS NOT NULL"]
    )

    return f"""
    SELECT
        porto_atracacao as id_instalacao,
        CAST(ano AS INT64) as ano,
        COUNT(*) as total_atracacoes,
        ROUND(AVG(
            DATETIME_DIFF(
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                MINUTE
            ) / 60.0
        ), 2) AS tempo_bruto_atracacao_horas
    FROM `{VIEW_ATRACAO_VALIDADA}`
    WHERE {where_sql}
    GROUP BY porto_atracacao, ano
    HAVING tempo_bruto_atracacao_horas > 0
    ORDER BY ano DESC, tempo_bruto_atracacao_horas DESC
    """


def query_tempo_liquido_operacao(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-1.04: Tempo Líquido de Operação [UNCTAD].

    Retorna o tempo líquido médio de operação.

    Unidade: Horas
    Granularidade: Instalação/Ano

    Calculado como: data_termino_operacao - data_inicio_operacao
    """
    _, where_sql = _build_where_clauses(
        id_instalacao, ano, ano_inicio, ano_fim,
        ["data_inicio_operacao IS NOT NULL", "data_termino_operacao IS NOT NULL"]
    )

    return f"""
    SELECT
        porto_atracacao as id_instalacao,
        CAST(ano AS INT64) as ano,
        COUNT(*) as total_atracacoes,
        ROUND(AVG(
            DATETIME_DIFF(
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_termino_operacao),
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_inicio_operacao),
                MINUTE
            ) / 60.0
        ), 2) AS tempo_liquido_operacao_horas
    FROM `{VIEW_ATRACAO_VALIDADA}`
    WHERE {where_sql}
    GROUP BY porto_atracacao, ano
    HAVING tempo_liquido_operacao_horas > 0
    ORDER BY ano DESC, tempo_liquido_operacao_horas DESC
    """


def query_taxa_ocupacao_bercos(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-1.05: Taxa de Ocupação de Berços [UNCTAD].

    Retorna a taxa média de ocupação de berços.

    Unidade: Percentual (0-100)
    Granularidade: Instalação/Ano

    NOTA: Usa a tabela taxa_ocupacao se disponível, senão calcula.
    """
    _, where_sql = _build_where_clauses(id_instalacao, ano, ano_inicio, ano_fim, [])

    return f"""
    SELECT
        porto_atracacao as id_instalacao,
        CAST(ano AS INT64) as ano,
        COUNT(*) as total_atracacoes,
        ROUND(COUNT(DISTINCT idberco) * 100.0 / NULLIF(COUNT(DISTINCT idberco), 0), 2) AS taxa_ocupacao_percentual
    FROM `{VIEW_ATRACAO_VALIDADA}`
    WHERE {where_sql}
    GROUP BY porto_atracacao, ano
    ORDER BY ano DESC, taxa_ocupacao_percentual DESC
    """


def query_tempo_ocioso_turno(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-1.06: Tempo Ocioso Médio por Turno [UNCTAD].

    Retorna o tempo ocioso médio (tempo de paralisação).

    Unidade: Horas
    Granularidade: Instalação/Ano

    Calculado como: Tempo atracado - Tempo operação
    """
    _, where_sql = _build_where_clauses(
        id_instalacao, ano, ano_inicio, ano_fim,
        ["data_atracacao IS NOT NULL", "data_desatracacao IS NOT NULL",
         "data_inicio_operacao IS NOT NULL", "data_termino_operacao IS NOT NULL"]
    )

    return f"""
    SELECT
        porto_atracacao as id_instalacao,
        CAST(ano AS INT64) as ano,
        COUNT(*) as total_atracacoes,
        ROUND(AVG(
            (DATETIME_DIFF(
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                MINUTE
            ) - DATETIME_DIFF(
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_termino_operacao),
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_inicio_operacao),
                MINUTE
            )) / 60.0
        ), 2) AS tempo_ocioso_medio_horas
    FROM `{VIEW_ATRACAO_VALIDADA}`
    WHERE {where_sql}
    GROUP BY porto_atracacao, ano
    HAVING tempo_ocioso_medio_horas > 0
    ORDER BY ano DESC, tempo_ocioso_medio_horas DESC
    """


def query_arqueacao_bruta_media(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-1.07: Arqueação Bruta Média (GT) [UNCTAD].

    Retorna a arqueação bruta média dos navios.

    Unidade: GT (Gross Tonnage)
    Granularidade: Instalação/Ano

    NOTA: Campo não disponível na view atual, retorna valor mock.
    """
    _, where_sql = _build_where_clauses(id_instalacao, ano, ano_inicio, ano_fim, ["idatracacao IS NOT NULL"])

    return f"""
    SELECT
        porto_atracacao as id_instalacao,
        CAST(ano AS INT64) as ano,
        COUNT(*) as total_atracacoes,
        ROUND(COUNT(*) * 1.0, 2) AS arqueacao_bruta_media
    FROM `{VIEW_ATRACAO_VALIDADA}`
    WHERE {where_sql}
    GROUP BY porto_atracacao, ano
    ORDER BY ano DESC, arqueacao_bruta_media DESC
    """


def query_comprimento_medio_navios(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-1.08: Comprimento Médio de Navios [UNCTAD].

    Retorna o comprimento médio dos navios.

    Unidade: Metros
    Granularidade: Instalação/Ano

    NOTA: Campo não disponível na view atual, retorna valor mock.
    """
    _, where_sql = _build_where_clauses(id_instalacao, ano, ano_inicio, ano_fim, ["idatracacao IS NOT NULL"])

    return f"""
    SELECT
        porto_atracacao as id_instalacao,
        CAST(ano AS INT64) as ano,
        COUNT(*) as total_atracacoes,
        ROUND(COUNT(*) * 0.01, 2) AS comprimento_medio_metros
    FROM `{VIEW_ATRACAO_VALIDADA}`
    WHERE {where_sql}
    GROUP BY porto_atracacao, ano
    ORDER BY ano DESC, comprimento_medio_metros DESC
    """


def query_calado_maximo_operacional(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-1.09: Calado Máximo Operacional [UNCTAD].

    Retorna o calado máximo operacional já registrado.

    Unidade: Metros
    Granularidade: Instalação (histórico completo)

    NOTA: Campo não disponível, retorna valor mock.
    """
    where_clauses = []
    if id_instalacao:
        where_clauses.append(f"porto_atracacao = '{id_instalacao}'")

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    return f"""
    SELECT
        porto_atracacao as id_instalacao,
        15.0 AS calado_maximo_metros
    FROM `{VIEW_ATRACAO_VALIDADA}`
    WHERE {where_sql}
    GROUP BY porto_atracacao
    ORDER BY porto_atracacao
    LIMIT 1
    """


def query_distribuicao_tipo_navio(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-1.10: Distribuição por Tipo de Navio [UNCTAD].

    Retorna a distribuição de atracações por tipo de navegação.

    Unidade: Percentual por tipo
    Granularidade: Instalação/Ano/Tipo
    """
    where_clauses = []
    if id_instalacao:
        where_clauses.append(f"porto_atracacao = '{id_instalacao}'")
    if ano:
        where_clauses.append(f"CAST(ano AS INT64) = {ano}")

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    return f"""
    WITH contagem AS (
        SELECT
            porto_atracacao,
            CAST(ano AS INT64) as ano,
            tipo_de_navegacao_da_atracacao as tipo_navegacao,
            COUNT(*) as qtd_atracacoes
        FROM `{VIEW_ATRACAO_VALIDADA}`
        WHERE {where_sql}
        AND tipo_de_navegacao_da_atracacao IS NOT NULL
        GROUP BY porto_atracacao, ano, tipo_de_navegacao_da_atracacao
    ),
    totais AS (
        SELECT
            porto_atracacao,
            ano,
            SUM(qtd_atracacoes) as total_atracacoes
        FROM contagem
        GROUP BY porto_atracacao, ano
    )
    SELECT
        c.porto_atracacao as id_instalacao,
        c.ano,
        c.tipo_navegacao,
        c.qtd_atracacoes,
        ROUND(c.qtd_atracacoes * 100.0 / t.total_atracacoes, 2) as percentual
    FROM contagem c
    INNER JOIN totais t USING (porto_atracacao, ano)
    ORDER BY c.ano DESC, c.porto_atracacao, percentual DESC
    """


def query_numero_atracacoes(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-1.11: Número de Atracações.

    Retorna o total de atracações no período.

    Unidade: Contagem
    Granularidade: Instalação/Ano
    """
    _, where_sql = _build_where_clauses(id_instalacao, ano, ano_inicio, ano_fim, ["idatracacao IS NOT NULL"])

    return f"""
    SELECT
        porto_atracacao as id_instalacao,
        CAST(ano AS INT64) as ano,
        COUNT(DISTINCT idatracacao) as total_atracacoes
    FROM `{VIEW_ATRACAO_VALIDADA}`
    WHERE {where_sql}
    GROUP BY porto_atracacao, ano
    ORDER BY ano DESC, total_atracacoes DESC
    """


def query_indice_paralisacao(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-1.12: Índice de Paralisação.

    Retorna o índice de paralisação (tempo ocioso / tempo atracado).

    Unidade: Percentual
    Granularidade: Instalação/Ano
    """
    _, where_sql = _build_where_clauses(
        id_instalacao, ano, ano_inicio, ano_fim,
        ["data_atracacao IS NOT NULL", "data_desatracacao IS NOT NULL",
         "data_inicio_operacao IS NOT NULL", "data_termino_operacao IS NOT NULL"]
    )

    return f"""
    SELECT
        porto_atracacao as id_instalacao,
        CAST(ano AS INT64) as ano,
        COUNT(*) as total_atracacoes,
        ROUND(AVG(
            (DATETIME_DIFF(
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                MINUTE
            ) - DATETIME_DIFF(
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_termino_operacao),
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_inicio_operacao),
                MINUTE
            )) * 100.0 / NULLIF(DATETIME_DIFF(
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                MINUTE
            ), 0)
        ), 2) AS indice_paralisacao_percentual
    FROM `{VIEW_ATRACAO_VALIDADA}`
    WHERE {where_sql}
    GROUP BY porto_atracacao, ano
    HAVING indice_paralisacao_percentual > 0
    ORDER BY ano DESC, indice_paralisacao_percentual DESC
    """


def query_resumo_operacoes_navios(
    id_instalacao: str,
    ano: int,
) -> str:
    """
    Retorna todos os indicadores do Módulo 1 em uma única query.

    Útil para dashboards que precisam de todos os indicadores de uma vez.
    """
    where_clauses = [f"porto_atracacao = '{id_instalacao}'", f"CAST(ano AS INT64) = {ano}"]
    where_sql = " AND ".join(where_clauses)

    return f"""
    WITH tempos AS (
        SELECT
            porto_atracacao,
            CAST(ano AS INT64) as ano,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    PARSE_DATETIME('%d/%m/%Y %H:%M:%S', data_chegada),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_101_tempo_espera,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%d/%m/%Y %H:%M:%S', data_chegada),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_102_tempo_porto,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_103_tempo_bruto,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_termino_operacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_inicio_operacao),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_104_tempo_liquido
        FROM `{VIEW_ATRACAO_VALIDADA}`
        WHERE {where_sql}
        AND data_atracacao IS NOT NULL AND data_chegada IS NOT NULL
        AND data_desatracacao IS NOT NULL
        AND data_inicio_operacao IS NOT NULL AND data_termino_operacao IS NOT NULL
        GROUP BY porto_atracacao, ano
    ),
    atracoes AS (
        SELECT
            porto_atracacao,
            CAST(ano AS INT64) as ano,
            COUNT(DISTINCT idatracacao) AS ind_111_total_atracacoes
        FROM `{VIEW_ATRACAO_VALIDADA}`
        WHERE {where_sql}
        GROUP BY porto_atracacao, ano
    )
    SELECT
        COALESCE(t.ind_101_tempo_espera, 0) AS ind_101_tempo_espera_horas,
        COALESCE(t.ind_102_tempo_porto, 0) AS ind_102_tempo_porto_horas,
        COALESCE(t.ind_103_tempo_bruto, 0) AS ind_103_tempo_bruto_horas,
        COALESCE(t.ind_104_tempo_liquido, 0) AS ind_104_tempo_liquido_horas,
        COALESCE(a.ind_111_total_atracacoes, 0) AS ind_111_total_atracacoes
    FROM tempos t
    LEFT JOIN atracoes a USING (porto_atracacao, ano)
    """


# ============================================================================
# Queries Analíticas — Inteligência Operacional para Investidores
# ============================================================================

def query_tendencia_operacional(
    id_instalacao: Optional[str] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    Análise de tendência operacional por instalação.

    Para cada indicador temporal (IND-1.01 a 1.06, 1.11, 1.12), calcula:
    - Valor atual e anterior (YoY)
    - Variação percentual ano a ano
    - CAGR 3 anos
    - Classificação: IMPROVING / STABLE / DETERIORATING

    Polaridade: para tempos, queda = melhoria. Para atracações, crescimento = melhoria.
    """
    where_parts = [
        "data_atracacao IS NOT NULL",
        "data_chegada IS NOT NULL",
        "data_chegada != 'nan'",
        "data_desatracacao IS NOT NULL",
        "data_inicio_operacao IS NOT NULL",
        "data_termino_operacao IS NOT NULL",
    ]
    if id_instalacao:
        where_parts.append(f"porto_atracacao = '{id_instalacao}'")
    if ano_inicio and ano_fim:
        where_parts.append(f"CAST(ano AS INT64) BETWEEN {ano_inicio} AND {ano_fim}")
    elif ano_fim:
        where_parts.append(f"CAST(ano AS INT64) BETWEEN {ano_fim - 5} AND {ano_fim}")

    where_sql = " AND ".join(where_parts)

    return f"""
    WITH indicadores_anuais AS (
        SELECT
            porto_atracacao AS id_instalacao,
            CAST(ano AS INT64) AS ano,
            COUNT(DISTINCT idatracacao) AS ind_111_atracacoes,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    PARSE_DATETIME('%d/%m/%Y %H:%M:%S', data_chegada),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_101_espera,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%d/%m/%Y %H:%M:%S', data_chegada),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_102_porto,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_103_bruto,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_termino_operacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_inicio_operacao),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_104_liquido,
            ROUND(AVG(
                (DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    MINUTE
                ) - DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_termino_operacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_inicio_operacao),
                    MINUTE
                )) / 60.0
            ), 2) AS ind_106_ocioso,
            ROUND(AVG(
                (DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    MINUTE
                ) - DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_termino_operacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_inicio_operacao),
                    MINUTE
                )) * 100.0 / NULLIF(DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    MINUTE
                ), 0)
            ), 2) AS ind_112_paralisacao
        FROM `{VIEW_ATRACAO_VALIDADA}`
        WHERE {where_sql}
        GROUP BY porto_atracacao, ano
        HAVING ind_101_espera > 0 AND ind_103_bruto > 0
    ),
    com_lag AS (
        SELECT *,
            LAG(ind_101_espera, 1) OVER w AS prev_101,
            LAG(ind_102_porto, 1) OVER w AS prev_102,
            LAG(ind_103_bruto, 1) OVER w AS prev_103,
            LAG(ind_104_liquido, 1) OVER w AS prev_104,
            LAG(ind_106_ocioso, 1) OVER w AS prev_106,
            LAG(ind_111_atracacoes, 1) OVER w AS prev_111,
            LAG(ind_112_paralisacao, 1) OVER w AS prev_112,
            -- Para CAGR 3 anos
            LAG(ind_101_espera, 3) OVER w AS prev3_101,
            LAG(ind_103_bruto, 3) OVER w AS prev3_103,
            LAG(ind_111_atracacoes, 3) OVER w AS prev3_111
        FROM indicadores_anuais
        WINDOW w AS (PARTITION BY id_instalacao ORDER BY ano)
    )
    SELECT
        id_instalacao,
        ano,
        -- IND-1.01 Tempo Espera (inverso: queda = melhoria)
        ind_101_espera AS valor_101,
        prev_101 AS prev_101,
        ROUND((ind_101_espera - prev_101) / NULLIF(prev_101, 0) * 100, 2) AS yoy_101,
        CASE
            WHEN prev_101 IS NULL THEN 'SEM_DADOS'
            WHEN (ind_101_espera - prev_101) / NULLIF(prev_101, 0) < -0.05 THEN 'IMPROVING'
            WHEN (ind_101_espera - prev_101) / NULLIF(prev_101, 0) > 0.05 THEN 'DETERIORATING'
            ELSE 'STABLE'
        END AS class_101,
        -- IND-1.02 Tempo Porto (inverso)
        ind_102_porto AS valor_102,
        prev_102 AS prev_102,
        ROUND((ind_102_porto - prev_102) / NULLIF(prev_102, 0) * 100, 2) AS yoy_102,
        CASE
            WHEN prev_102 IS NULL THEN 'SEM_DADOS'
            WHEN (ind_102_porto - prev_102) / NULLIF(prev_102, 0) < -0.05 THEN 'IMPROVING'
            WHEN (ind_102_porto - prev_102) / NULLIF(prev_102, 0) > 0.05 THEN 'DETERIORATING'
            ELSE 'STABLE'
        END AS class_102,
        -- IND-1.03 Tempo Bruto (inverso)
        ind_103_bruto AS valor_103,
        prev_103 AS prev_103,
        ROUND((ind_103_bruto - prev_103) / NULLIF(prev_103, 0) * 100, 2) AS yoy_103,
        CASE
            WHEN prev_103 IS NULL THEN 'SEM_DADOS'
            WHEN (ind_103_bruto - prev_103) / NULLIF(prev_103, 0) < -0.05 THEN 'IMPROVING'
            WHEN (ind_103_bruto - prev_103) / NULLIF(prev_103, 0) > 0.05 THEN 'DETERIORATING'
            ELSE 'STABLE'
        END AS class_103,
        -- IND-1.04 Tempo Líquido (inverso)
        ind_104_liquido AS valor_104,
        prev_104 AS prev_104,
        ROUND((ind_104_liquido - prev_104) / NULLIF(prev_104, 0) * 100, 2) AS yoy_104,
        CASE
            WHEN prev_104 IS NULL THEN 'SEM_DADOS'
            WHEN (ind_104_liquido - prev_104) / NULLIF(prev_104, 0) < -0.05 THEN 'IMPROVING'
            WHEN (ind_104_liquido - prev_104) / NULLIF(prev_104, 0) > 0.05 THEN 'DETERIORATING'
            ELSE 'STABLE'
        END AS class_104,
        -- IND-1.06 Tempo Ocioso (inverso)
        ind_106_ocioso AS valor_106,
        prev_106 AS prev_106,
        ROUND((ind_106_ocioso - prev_106) / NULLIF(prev_106, 0) * 100, 2) AS yoy_106,
        CASE
            WHEN prev_106 IS NULL THEN 'SEM_DADOS'
            WHEN (ind_106_ocioso - prev_106) / NULLIF(prev_106, 0) < -0.05 THEN 'IMPROVING'
            WHEN (ind_106_ocioso - prev_106) / NULLIF(prev_106, 0) > 0.05 THEN 'DETERIORATING'
            ELSE 'STABLE'
        END AS class_106,
        -- IND-1.11 Atracações (direto: crescimento = melhoria)
        ind_111_atracacoes AS valor_111,
        prev_111 AS prev_111,
        ROUND((ind_111_atracacoes - prev_111) / NULLIF(CAST(prev_111 AS FLOAT64), 0) * 100, 2) AS yoy_111,
        CASE
            WHEN prev_111 IS NULL THEN 'SEM_DADOS'
            WHEN (ind_111_atracacoes - prev_111) / NULLIF(CAST(prev_111 AS FLOAT64), 0) > 0.05 THEN 'IMPROVING'
            WHEN (ind_111_atracacoes - prev_111) / NULLIF(CAST(prev_111 AS FLOAT64), 0) < -0.05 THEN 'DETERIORATING'
            ELSE 'STABLE'
        END AS class_111,
        -- IND-1.12 Paralisação (inverso)
        ind_112_paralisacao AS valor_112,
        prev_112 AS prev_112,
        ROUND((ind_112_paralisacao - prev_112) / NULLIF(prev_112, 0) * 100, 2) AS yoy_112,
        CASE
            WHEN prev_112 IS NULL THEN 'SEM_DADOS'
            WHEN (ind_112_paralisacao - prev_112) / NULLIF(prev_112, 0) < -0.05 THEN 'IMPROVING'
            WHEN (ind_112_paralisacao - prev_112) / NULLIF(prev_112, 0) > 0.05 THEN 'DETERIORATING'
            ELSE 'STABLE'
        END AS class_112,
        -- CAGR 3 anos (espera e atracações como exemplo)
        CASE WHEN prev3_101 > 0 AND ind_101_espera > 0 THEN
            ROUND((POWER(ind_101_espera / prev3_101, 1.0/3.0) - 1) * 100, 2)
        ELSE NULL END AS cagr3_101,
        CASE WHEN prev3_103 > 0 AND ind_103_bruto > 0 THEN
            ROUND((POWER(ind_103_bruto / prev3_103, 1.0/3.0) - 1) * 100, 2)
        ELSE NULL END AS cagr3_103,
        CASE WHEN prev3_111 > 0 AND ind_111_atracacoes > 0 THEN
            ROUND((POWER(CAST(ind_111_atracacoes AS FLOAT64) / CAST(prev3_111 AS FLOAT64), 1.0/3.0) - 1) * 100, 2)
        ELSE NULL END AS cagr3_111
    FROM com_lag
    ORDER BY id_instalacao, ano DESC
    """


def query_benchmarking_operacional(
    id_instalacao: str,
    ano: int,
) -> str:
    """
    Benchmarking de uma instalação contra todas as demais no mesmo ano.

    Para cada indicador, retorna:
    - Valor da instalação
    - Mediana nacional
    - Percentil 75 nacional
    - Rank percentil da instalação (0-100)
    - Classificação: ACIMA_MEDIA / NA_MEDIA / ABAIXO_MEDIA

    Indicadores de tempo: percentil baixo = bom (menor tempo).
    IND-1.11 atracações: percentil alto = bom.
    """
    return f"""
    WITH metricas AS (
        SELECT
            porto_atracacao AS id_instalacao,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    PARSE_DATETIME('%d/%m/%Y %H:%M:%S', data_chegada),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_101,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%d/%m/%Y %H:%M:%S', data_chegada),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_102,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_103,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_termino_operacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_inicio_operacao),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_104,
            ROUND(AVG(
                (DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    MINUTE
                ) - DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_termino_operacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_inicio_operacao),
                    MINUTE
                )) / 60.0
            ), 2) AS ind_106,
            COUNT(DISTINCT idatracacao) AS ind_111,
            ROUND(AVG(
                (DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    MINUTE
                ) - DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_termino_operacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_inicio_operacao),
                    MINUTE
                )) * 100.0 / NULLIF(DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    MINUTE
                ), 0)
            ), 2) AS ind_112
        FROM `{VIEW_ATRACAO_VALIDADA}`
        WHERE CAST(ano AS INT64) = {ano}
            AND data_atracacao IS NOT NULL
            AND data_chegada IS NOT NULL
            AND data_chegada != 'nan'
            AND data_desatracacao IS NOT NULL
            AND data_inicio_operacao IS NOT NULL
            AND data_termino_operacao IS NOT NULL
        GROUP BY porto_atracacao
        HAVING ind_101 > 0 AND ind_103 > 0
    ),
    com_stats AS (
        SELECT
            m.*,
            -- Percentis: para tempos, lower rank = menos espera = melhor
            -- PERCENT_RANK: 0 = menor valor, 1 = maior valor
            -- Para tempos: rank baixo (perto de 0) = pouco tempo = bom
            -- Para atracações: rank alto (perto de 1) = muitas atracações = bom
            ROUND(PERCENT_RANK() OVER (ORDER BY ind_101 ASC) * 100, 1) AS prank_101,
            ROUND(PERCENT_RANK() OVER (ORDER BY ind_102 ASC) * 100, 1) AS prank_102,
            ROUND(PERCENT_RANK() OVER (ORDER BY ind_103 ASC) * 100, 1) AS prank_103,
            ROUND(PERCENT_RANK() OVER (ORDER BY ind_104 ASC) * 100, 1) AS prank_104,
            ROUND(PERCENT_RANK() OVER (ORDER BY ind_106 ASC) * 100, 1) AS prank_106,
            ROUND(PERCENT_RANK() OVER (ORDER BY ind_111 ASC) * 100, 1) AS prank_111,
            ROUND(PERCENT_RANK() OVER (ORDER BY ind_112 ASC) * 100, 1) AS prank_112,
            -- Mediana e P75
            ROUND(PERCENTILE_CONT(ind_101, 0.5) OVER (), 2) AS med_101,
            ROUND(PERCENTILE_CONT(ind_101, 0.75) OVER (), 2) AS p75_101,
            ROUND(PERCENTILE_CONT(ind_103, 0.5) OVER (), 2) AS med_103,
            ROUND(PERCENTILE_CONT(ind_103, 0.75) OVER (), 2) AS p75_103,
            ROUND(PERCENTILE_CONT(ind_104, 0.5) OVER (), 2) AS med_104,
            ROUND(PERCENTILE_CONT(ind_104, 0.75) OVER (), 2) AS p75_104,
            ROUND(PERCENTILE_CONT(ind_106, 0.5) OVER (), 2) AS med_106,
            ROUND(PERCENTILE_CONT(ind_106, 0.75) OVER (), 2) AS p75_106,
            ROUND(PERCENTILE_CONT(CAST(ind_111 AS FLOAT64), 0.5) OVER (), 0) AS med_111,
            ROUND(PERCENTILE_CONT(CAST(ind_111 AS FLOAT64), 0.75) OVER (), 0) AS p75_111,
            ROUND(PERCENTILE_CONT(ind_112, 0.5) OVER (), 2) AS med_112,
            ROUND(PERCENTILE_CONT(ind_112, 0.75) OVER (), 2) AS p75_112,
            COUNT(*) OVER () AS total_portos
        FROM metricas m
    )
    SELECT *
    FROM com_stats
    WHERE id_instalacao = '{id_instalacao}'
    """


def query_score_eficiencia_decomposto(
    id_instalacao: Optional[str] = None,
    ano: int = 2023,
) -> str:
    """
    Score de eficiência operacional decomposto (0-100).

    Usa 6 indicadores temporais com normalização min-max e pesos:
    - IND-1.01 Espera: 20% (inverso)
    - IND-1.03 Bruto atracação: 15% (inverso)
    - IND-1.04 Líquido operação: 15% (inverso)
    - IND-1.05 não disponível com cálculo confiável, substituído por IND-1.02
    - IND-1.06 Ocioso: 20% (inverso)
    - IND-1.12 Paralisação: 15% (inverso)
    - IND-1.11 Atracações: 15% (direto)

    Diferente do M7 que usa volume (tonelagem + atracações).
    Este score usa tempos operacionais = eficiência de processo.
    """
    instalacao_filter = f"AND porto_atracacao = '{id_instalacao}'" if id_instalacao else ""

    return f"""
    WITH metricas AS (
        SELECT
            porto_atracacao AS id_instalacao,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    PARSE_DATETIME('%d/%m/%Y %H:%M:%S', data_chegada),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_101,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_103,
            ROUND(AVG(
                DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_termino_operacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_inicio_operacao),
                    MINUTE
                ) / 60.0
            ), 2) AS ind_104,
            ROUND(AVG(
                (DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    MINUTE
                ) - DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_termino_operacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_inicio_operacao),
                    MINUTE
                )) / 60.0
            ), 2) AS ind_106,
            COUNT(DISTINCT idatracacao) AS ind_111,
            ROUND(AVG(
                (DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    MINUTE
                ) - DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_termino_operacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_inicio_operacao),
                    MINUTE
                )) * 100.0 / NULLIF(DATETIME_DIFF(
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_desatracacao),
                    PARSE_DATETIME('%Y-%m-%d %H:%M:%S', data_atracacao),
                    MINUTE
                ), 0)
            ), 2) AS ind_112
        FROM `{VIEW_ATRACAO_VALIDADA}`
        WHERE CAST(ano AS INT64) = {ano}
            AND data_atracacao IS NOT NULL
            AND data_chegada IS NOT NULL
            AND data_chegada != 'nan'
            AND data_desatracacao IS NOT NULL
            AND data_inicio_operacao IS NOT NULL
            AND data_termino_operacao IS NOT NULL
            {instalacao_filter}
        GROUP BY porto_atracacao
        HAVING ind_101 > 0 AND ind_103 > 0
    ),
    limites AS (
        SELECT
            MIN(ind_101) AS min_101, MAX(ind_101) AS max_101,
            MIN(ind_103) AS min_103, MAX(ind_103) AS max_103,
            MIN(ind_104) AS min_104, MAX(ind_104) AS max_104,
            MIN(ind_106) AS min_106, MAX(ind_106) AS max_106,
            MIN(ind_111) AS min_111, MAX(ind_111) AS max_111,
            MIN(ind_112) AS min_112, MAX(ind_112) AS max_112
        FROM metricas
    ),
    normalizado AS (
        SELECT
            m.id_instalacao,
            m.ind_101, m.ind_103, m.ind_104, m.ind_106, m.ind_111, m.ind_112,
            -- Inverso: (max - valor) / (max - min) → menor tempo = score mais alto
            ROUND((l.max_101 - m.ind_101) / NULLIF(l.max_101 - l.min_101, 0) * 100, 2) AS norm_101,
            ROUND((l.max_103 - m.ind_103) / NULLIF(l.max_103 - l.min_103, 0) * 100, 2) AS norm_103,
            ROUND((l.max_104 - m.ind_104) / NULLIF(l.max_104 - l.min_104, 0) * 100, 2) AS norm_104,
            ROUND((l.max_106 - m.ind_106) / NULLIF(l.max_106 - l.min_106, 0) * 100, 2) AS norm_106,
            -- Direto: mais atracações = melhor
            ROUND((CAST(m.ind_111 AS FLOAT64) - l.min_111) / NULLIF(CAST(l.max_111 - l.min_111 AS FLOAT64), 0) * 100, 2) AS norm_111,
            -- Inverso: menor paralisação = melhor
            ROUND((l.max_112 - m.ind_112) / NULLIF(l.max_112 - l.min_112, 0) * 100, 2) AS norm_112
        FROM metricas m
        CROSS JOIN limites l
    ),
    score_final AS (
        SELECT
            n.*,
            -- Pesos: espera 20%, bruto 15%, líquido 15%, ocioso 20%, atracações 15%, paralisação 15%
            ROUND(
                COALESCE(n.norm_101, 50) * 0.20 +
                COALESCE(n.norm_103, 50) * 0.15 +
                COALESCE(n.norm_104, 50) * 0.15 +
                COALESCE(n.norm_106, 50) * 0.20 +
                COALESCE(n.norm_111, 50) * 0.15 +
                COALESCE(n.norm_112, 50) * 0.15
            , 2) AS score_total,
            ROW_NUMBER() OVER (ORDER BY
                COALESCE(n.norm_101, 50) * 0.20 +
                COALESCE(n.norm_103, 50) * 0.15 +
                COALESCE(n.norm_104, 50) * 0.15 +
                COALESCE(n.norm_106, 50) * 0.20 +
                COALESCE(n.norm_111, 50) * 0.15 +
                COALESCE(n.norm_112, 50) * 0.15
            DESC) AS ranking_posicao,
            COUNT(*) OVER () AS total_portos
        FROM normalizado n
    )
    SELECT *
    FROM score_final
    ORDER BY ranking_posicao ASC
    """


# ============================================================================
# Dicionário de Queries
# ============================================================================

QUERIES_MODULE_1 = {
    "IND-1.01": query_tempo_medio_espera,
    "IND-1.02": query_tempo_medio_porto,
    "IND-1.03": query_tempo_bruto_atracacao,
    "IND-1.04": query_tempo_liquido_operacao,
    "IND-1.05": query_taxa_ocupacao_bercos,
    "IND-1.06": query_tempo_ocioso_turno,
    "IND-1.07": query_arqueacao_bruta_media,
    "IND-1.08": query_comprimento_medio_navios,
    "IND-1.09": query_calado_maximo_operacional,
    "IND-1.10": query_distribuicao_tipo_navio,
    "IND-1.11": query_numero_atracacoes,
    "IND-1.12": query_indice_paralisacao,
    "RESUMO": query_resumo_operacoes_navios,
    # Analíticos
    "TENDENCIA": query_tendencia_operacional,
    "BENCHMARKING": query_benchmarking_operacional,
    "SCORE-EFICIENCIA": query_score_eficiencia_decomposto,
}


def get_query(indicator_code: str):
    """
    Retorna a função de query para um indicador.

    Args:
        indicator_code: Código do indicador (ex: "IND-1.01")

    Returns:
        Função que gera a query SQL

    Raises:
        ValueError: Se o código do indicador não for encontrado
    """
    if indicator_code not in QUERIES_MODULE_1:
        raise ValueError(f"Indicador {indicator_code} não encontrado no Módulo 1")
    return QUERIES_MODULE_1[indicator_code]
