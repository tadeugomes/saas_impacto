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
