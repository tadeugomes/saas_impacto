"""
Queries BigQuery para o Módulo 12 — Capacidade Portuária.

Implementa as queries de extração da base depurada (Passo 1 da metodologia
LabPortos/UFMA), calculando tempos operacionais por atracação a partir das
5 timestamps ANTAQ.

As queries retornam dados por atracação individual (não agregados) para que
o filtro IQR e a agregação sejam feitos em Python.

Referências:
- arquivos_capacidades/Memoria_Calculo_Capacidade_Sem_Conteineres.ipynb
- arquivos_capacidades/Memoria_Calculo_Capacidade_Conteineres.ipynb
- arquivos_capacidades/roteiro_capacidades_portuarias_v12.md (Passos 1-2)
"""
from __future__ import annotations

from typing import Optional


# ============================================================================
# Constants
# ============================================================================

ANTAQ_DATASET = "antaqdados.br_antaq_estatistico_aquaviario"
VIEW_ATRACACAO = f"{ANTAQ_DATASET}.v_atracacao_validada"
VIEW_CARGA = f"{ANTAQ_DATASET}.v_carga_metodologia_oficial"
TABLE_MERCADORIA = f"{ANTAQ_DATASET}.mercadoria_carga"


# ============================================================================
# Helpers
# ============================================================================

def _pdt(col: str) -> str:
    """COALESCE de SAFE.PARSE_DATETIME para formatos mistos ANTAQ (YYYY-MM-DD / DD/MM/YYYY)."""
    return (
        f"COALESCE(SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', {col}), "
        f"SAFE.PARSE_DATETIME('%d/%m/%Y %H:%M:%S', {col}))"
    )

def _build_where(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
    extra: Optional[list] = None,
) -> str:
    """Constrói cláusula WHERE para queries de capacidade."""
    clauses = list(extra) if extra else []
    if id_instalacao:
        clauses.append(f"a.porto_atracacao = '{id_instalacao}'")
    if ano:
        clauses.append(f"CAST(a.ano AS INT64) = {ano}")
    elif ano_inicio and ano_fim:
        clauses.append(
            f"CAST(a.ano AS INT64) BETWEEN {ano_inicio} AND {ano_fim}"
        )
    return " AND ".join(clauses) if clauses else "1=1"


# ============================================================================
# Passo 1 — Base Depurada Não-Conteinerizada
# ============================================================================

def query_base_depurada_nao_conteiner(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """Base depurada para carga NÃO conteinerizada (tonelagem).

    Retorna uma linha por atracação com:
    - Tempos operacionais: lineup_h, inop_pre_h, t_op_h, inop_pos_h, ta_h
    - Carga: lm_tons (lote por atracação)
    - Perfil de carga derivado de grupo_mercadoria
    - Produtividade: produtividade_t_h

    Equivalente à "Planilha 1" do notebook Sem_Conteineres.
    """
    where = _build_where(
        id_instalacao, ano, ano_inicio, ano_fim,
        extra=[
            "a.data_chegada IS NOT NULL",
            "a.data_chegada != 'nan'",
            "a.data_atracacao IS NOT NULL",
            "a.data_inicio_operacao IS NOT NULL",
            "a.data_termino_operacao IS NOT NULL",
            "a.data_desatracacao IS NOT NULL",
        ],
    )

    return f"""
    WITH carga_por_atracacao AS (
        -- Agregar carga por atracação (pode haver múltiplas linhas de carga)
        SELECT
            c.idatracacao,
            SUM(c.vlpesocargabruta_oficial) AS lm_tons,
            -- Perfil de carga dominante (pela maior tonelagem)
            ARRAY_AGG(
                CASE
                    WHEN LOWER(m.string_field_3) LIKE '%mineral%'
                      OR LOWER(m.string_field_3) LIKE '%granel%'
                      OR LOWER(m.string_field_4) LIKE '%sólido%'
                    THEN 'Granel Sólido'
                    WHEN LOWER(m.string_field_3) LIKE '%líquido%'
                      OR LOWER(m.string_field_3) LIKE '%petróleo%'
                      OR LOWER(m.string_field_4) LIKE '%líquido%'
                    THEN 'Granel Líquido'
                    ELSE 'Carga Geral'
                END
                ORDER BY c.vlpesocargabruta_oficial DESC
                LIMIT 1
            )[OFFSET(0)] AS perfil_carga,
            c.sentido
        FROM `{VIEW_CARGA}` c
        LEFT JOIN `{TABLE_MERCADORIA}` m
            ON c.cdmercadoria = m.string_field_0
        WHERE c.vlpesocargabruta_oficial IS NOT NULL
          AND c.vlpesocargabruta_oficial > 0
          -- Excluir carga conteinerizada (TEU preenchido)
          AND (c.teu IS NULL OR SAFE_CAST(c.teu AS INT64) = 0)
        GROUP BY c.idatracacao, c.sentido
    )
    SELECT
        a.porto_atracacao AS id_instalacao,
        CAST(a.ano AS INT64) AS ano,
        a.idatracacao,
        a.idberco AS berco,
        ca.perfil_carga,
        ca.sentido,
        a.tipo_de_navegacao_da_atracacao AS tipo_navegacao,

        -- Tempos operacionais (horas)
        ROUND(DATETIME_DIFF(
            {_pdt('a.data_atracacao')},
            {_pdt('a.data_chegada')},
            MINUTE
        ) / 60.0, 4) AS lineup_h,

        ROUND(DATETIME_DIFF(
            {_pdt('a.data_inicio_operacao')},
            {_pdt('a.data_atracacao')},
            MINUTE
        ) / 60.0, 4) AS inop_pre_h,

        ROUND(DATETIME_DIFF(
            {_pdt('a.data_termino_operacao')},
            {_pdt('a.data_inicio_operacao')},
            MINUTE
        ) / 60.0, 4) AS t_op_h,

        ROUND(DATETIME_DIFF(
            {_pdt('a.data_desatracacao')},
            {_pdt('a.data_termino_operacao')},
            MINUTE
        ) / 60.0, 4) AS inop_pos_h,

        -- Ta = inop_pre + t_op + inop_pos
        ROUND((
            DATETIME_DIFF(
                {_pdt('a.data_desatracacao')},
                {_pdt('a.data_atracacao')},
                MINUTE
            )
        ) / 60.0, 4) AS ta_h,

        -- Carga e produtividade
        ROUND(ca.lm_tons, 2) AS lm_tons,
        ROUND(ca.lm_tons / NULLIF(
            DATETIME_DIFF(
                {_pdt('a.data_termino_operacao')},
                {_pdt('a.data_inicio_operacao')},
                MINUTE
            ) / 60.0,
            0
        ), 2) AS produtividade_t_h

    FROM `{VIEW_ATRACACAO}` a
    INNER JOIN carga_por_atracacao ca ON a.idatracacao = ca.idatracacao
    WHERE {where}
      -- Filtrar T_op > 0 (atracações com operação efetiva)
      AND DATETIME_DIFF(
            {_pdt('a.data_termino_operacao')},
            {_pdt('a.data_inicio_operacao')},
            MINUTE
          ) > 0
    ORDER BY a.ano, a.porto_atracacao, a.idatracacao
    """


# ============================================================================
# Passo 1 — Base Depurada Conteinerizada
# ============================================================================

def query_base_depurada_conteiner(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """Base depurada para carga CONTEINERIZADA (TEU).

    Diferença vs. não-conteinerizada:
    - ANTAQ pode registrar a mesma atracação múltiplas vezes (uma por
      armador/operador). O notebook resolve isso com GROUP BY (IMO + 5 timestamps)
      somando TEU. Aqui fazemos o equivalente no SQL com GROUP BY idatracacao
      (que já é único por atracação na view validada) + SUM(TEU).
    - Lote medido em TEU, não toneladas.
    - Produtividade em TEU/h.

    Equivalente à "Planilha 1" do notebook Conteineres (com tratamento de réplicas).
    """
    where = _build_where(
        id_instalacao, ano, ano_inicio, ano_fim,
        extra=[
            "a.data_chegada IS NOT NULL",
            "a.data_chegada != 'nan'",
            "a.data_atracacao IS NOT NULL",
            "a.data_inicio_operacao IS NOT NULL",
            "a.data_termino_operacao IS NOT NULL",
            "a.data_desatracacao IS NOT NULL",
        ],
    )

    return f"""
    WITH teu_por_atracacao AS (
        -- Deduplicação de réplicas: SUM(TEU) por atracação
        -- Na base ANTAQ, a mesma atracação pode aparecer N vezes
        -- com TEU parciais. Somamos para obter o total.
        SELECT
            c.idatracacao,
            SUM(SAFE_CAST(c.teu AS INT64)) AS lm_teu,
            c.sentido
        FROM `{VIEW_CARGA}` c
        WHERE c.teu IS NOT NULL
          AND SAFE_CAST(c.teu AS INT64) > 0
        GROUP BY c.idatracacao, c.sentido
    )
    SELECT
        a.porto_atracacao AS id_instalacao,
        CAST(a.ano AS INT64) AS ano,
        a.idatracacao,
        a.idberco AS berco,
        'Carga Conteinerizada' AS perfil_carga,
        ta.sentido,
        a.tipo_de_navegacao_da_atracacao AS tipo_navegacao,

        -- Tempos operacionais (horas)
        ROUND(DATETIME_DIFF(
            {_pdt('a.data_atracacao')},
            {_pdt('a.data_chegada')},
            MINUTE
        ) / 60.0, 4) AS lineup_h,

        ROUND(DATETIME_DIFF(
            {_pdt('a.data_inicio_operacao')},
            {_pdt('a.data_atracacao')},
            MINUTE
        ) / 60.0, 4) AS inop_pre_h,

        ROUND(DATETIME_DIFF(
            {_pdt('a.data_termino_operacao')},
            {_pdt('a.data_inicio_operacao')},
            MINUTE
        ) / 60.0, 4) AS t_op_h,

        ROUND(DATETIME_DIFF(
            {_pdt('a.data_desatracacao')},
            {_pdt('a.data_termino_operacao')},
            MINUTE
        ) / 60.0, 4) AS inop_pos_h,

        ROUND((
            DATETIME_DIFF(
                {_pdt('a.data_desatracacao')},
                {_pdt('a.data_atracacao')},
                MINUTE
            )
        ) / 60.0, 4) AS ta_h,

        -- TEU e produtividade
        ta.lm_teu,
        ROUND(ta.lm_teu / NULLIF(
            DATETIME_DIFF(
                {_pdt('a.data_termino_operacao')},
                {_pdt('a.data_inicio_operacao')},
                MINUTE
            ) / 60.0,
            0
        ), 2) AS produtividade_teu_h

    FROM `{VIEW_ATRACACAO}` a
    INNER JOIN teu_por_atracacao ta ON a.idatracacao = ta.idatracacao
    WHERE {where}
      AND DATETIME_DIFF(
            {_pdt('a.data_termino_operacao')},
            {_pdt('a.data_inicio_operacao')},
            MINUTE
          ) > 0
    ORDER BY a.ano, a.porto_atracacao, a.idatracacao
    """


# ============================================================================
# Query auxiliar: contagem de berços por instalação/ano
# ============================================================================

def query_contagem_bercos(
    id_instalacao: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """Conta berços distintos operacionais por instalação/ano.

    Útil quando o admin não configurou n_bercos no terminal_capacity_configs.
    """
    clauses = []
    if id_instalacao:
        clauses.append(f"porto_atracacao = '{id_instalacao}'")
    if ano:
        clauses.append(f"CAST(ano AS INT64) = {ano}")
    elif ano_inicio and ano_fim:
        clauses.append(f"CAST(ano AS INT64) BETWEEN {ano_inicio} AND {ano_fim}")

    where = " AND ".join(clauses) if clauses else "1=1"

    return f"""
    SELECT
        porto_atracacao AS id_instalacao,
        CAST(ano AS INT64) AS ano,
        COUNT(DISTINCT idberco) AS n_bercos_observados
    FROM `{VIEW_ATRACACAO}`
    WHERE {where}
      AND idberco IS NOT NULL
    GROUP BY porto_atracacao, ano
    ORDER BY ano DESC
    """


# ============================================================================
# Dicionário de queries do Módulo 12
# ============================================================================

QUERIES_MODULE_12 = {
    "IND-12.01": query_base_depurada_nao_conteiner,
    "IND-12.02": query_base_depurada_conteiner,
    "IND-12.03": query_contagem_bercos,
}
