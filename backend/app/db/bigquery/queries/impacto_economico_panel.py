"""Queries BigQuery para montagem do painel causal municipal.

Gera SQL que constrói uma tabela "long" com todas as variáveis de outcome,
controle e log-transformações que o engine causal (DiD/IV/Panel IV) espera:

  id_municipio, ano,
  n_vinculos, pib, receitas_total, despesas_total, remuneracao_media, ipca_media,
  toneladas_antaq, vista_rs, vista_usd,
  *_log, pib_lag1, n_vinculos_lag1    (features opcionais para augmented SCM)

Fontes base mapeadas em config/sources.yaml:
  - basedosdados.br_ibge_pib.municipio                  (PIB)
  - basedosdados.br_ibge_populacao.municipio             (Pop)
  - basedosdados.br_me_rais.microdados_vinculos          (RAIS)
  - basedosdados.br_me_siconfi.municipio_receitas_*      (SICONFI)
  - basedosdados.br_ibge_ipca.mes_brasil                 (IPCA)
  - antaqdados.br_antaq_estatistico_aquaviario           (ANTAQ)
  - marts_impacto.dims.dim_municipio_antaq               (crosswalk)
  - marts_impacto.impacto_economico.mart_impacto_economico (mart pré-calculado)

As queries preferem o mart quando disponível (mais eficiente e consistente)
e fazem fallback para as fontes brutas apenas para colunas não contempladas.
"""
from __future__ import annotations

from app.db.bigquery.marts.module5 import (
    MART_IMPACTO_ECONOMICO_FQTN,
    DIM_MUNICIPIO_ANTAQ_FQTN,
    BD_DADOS_PIB,
    BD_DADOS_RAIS,
    VIEW_CARGA_METODOLOGIA_OFICIAL,
    CNAES_PORTUARIOS,
)

# ── Fontes adicionais (SICONFI e IPCA) ───────────────────────────────────────
BD_SICONFI_RECEITAS = "basedosdados.br_me_siconfi.municipio_receitas_orcamentarias"
BD_SICONFI_DESPESAS = "basedosdados.br_me_siconfi.municipio_despesas_orcamentarias"
BD_IPCA = "basedosdados.br_ibge_ipca.mes_brasil"

# ── Tabela de commodities (carregada via ingest_worldbank_commodities.py) ─────
COMMODITIES_TABLE = "`marts_impacto.external.worldbank_commodities`"


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _municipio_filter(ids: list[str]) -> str:
    """Gera cláusula IN para filtrar municípios."""
    quoted = ", ".join(f"'{m}'" for m in ids)
    return f"id_municipio IN ({quoted})"


def _year_filter(col: str, ano_inicio: int, ano_fim: int) -> str:
    return f"{col} BETWEEN {ano_inicio} AND {ano_fim}"


# ---------------------------------------------------------------------------
# Query 1: painel via mart (caminho preferencial)
# ---------------------------------------------------------------------------

def query_causal_panel_from_mart(
    id_municipios: list[str],
    ano_inicio: int = 2010,
    ano_fim: int = 2023,
    include_lags: bool = True,
) -> str:
    """Monta painel causal a partir do mart pré-calculado (melhor performance).

    Requer que ``build_impacto_economico_mart_sql()`` tenha sido rodado antes.

    Parameters
    ----------
    id_municipios:
        Lista de códigos IBGE de municípios a incluir no painel.
    ano_inicio / ano_fim:
        Intervalo de anos (inclusive).
    include_lags:
        Se True, inclui ``pib_lag1`` e ``n_vinculos_portuarios_lag1``
        (úteis para augmented SCM).

    Returns
    -------
    str — SQL Standard para execução no BigQuery.
    """
    mun_filter = _municipio_filter(id_municipios)
    year_filter = _year_filter("m.ano", ano_inicio, ano_fim)

    lag_cols = ""
    if include_lags:
        lag_cols = """
        LAG(m.pib) OVER (PARTITION BY m.id_municipio ORDER BY m.ano)           AS pib_lag1,
        LAG(m.empregos_portuarios) OVER (
            PARTITION BY m.id_municipio ORDER BY m.ano)                         AS empregos_portuarios_lag1,"""

    return f"""
-- painel_causal_from_mart
-- Monta painel causal a partir do mart Módulo 5 pré-calculado.
WITH mart AS (
    SELECT
        m.id_municipio,
        m.ano,
        -- outcomes principais
        m.pib,
        m.empregos_portuarios                                                   AS n_vinculos,
        m.empregos_totais,
        m.tonelagem_antaq_oficial                                               AS toneladas_antaq,
        m.comercio_total_dolar                                                  AS comercio_dolar,
        m.exportacao_dolar,
        m.importacao_dolar,
        m.massa_salarial_portuaria,
        m.massa_salarial_total,
        -- populacao / PIB per capita
        m.populacao,
        SAFE_DIVIDE(m.pib, m.populacao)                                         AS pib_per_capita,
        -- VAB setorial
        m.vab_servicos,
        m.vab_industria,
        -- metadados geográficos
        m.sigla_uf                                                               AS uf,{lag_cols}
        -- marcador de qualidade
        CURRENT_TIMESTAMP()                                                      AS _query_ts
    FROM {MART_IMPACTO_ECONOMICO_FQTN} m
    WHERE {mun_filter}
      AND {year_filter}
),
-- IPCA médio anual (deflator)
ipca_anual AS (
    SELECT
        EXTRACT(YEAR FROM PARSE_DATE('%Y%m', CAST(mes AS STRING)))              AS ano,
        AVG(CAST(numero_indice AS FLOAT64))                                     AS ipca_media
    FROM {BD_IPCA}
    WHERE SAFE_CAST(numero_indice AS FLOAT64) IS NOT NULL
    GROUP BY 1
),
painel AS (
    SELECT
        m.*,
        i.ipca_media,
        -- log-transformações (SAFE_LOG retorna NULL se valor <= 0 ou NULL)
        LN(NULLIF(m.pib,                     0))                                AS pib_log,
        LN(NULLIF(m.n_vinculos,              0))                                AS n_vinculos_log,
        LN(NULLIF(m.empregos_totais,         0))                                AS empregos_totais_log,
        LN(NULLIF(m.toneladas_antaq,         0))                                AS toneladas_antaq_log,
        LN(NULLIF(m.comercio_dolar,          0))                                AS comercio_dolar_log,
        LN(NULLIF(m.exportacao_dolar,        0))                                AS exportacao_dolar_log,
        LN(NULLIF(m.importacao_dolar,        0))                                AS importacao_dolar_log,
        LN(NULLIF(m.massa_salarial_portuaria,0))                                AS massa_salarial_portuaria_log,
        LN(NULLIF(m.massa_salarial_total,    0))                                AS massa_salarial_total_log,
        LN(NULLIF(m.pib_per_capita,          0))                                AS pib_per_capita_log,
        LN(NULLIF(m.populacao,               0))                                AS populacao_log
    FROM mart m
    LEFT JOIN ipca_anual i USING (ano)
)
SELECT
    p.*
FROM painel p
ORDER BY p.id_municipio, p.ano
"""


# ---------------------------------------------------------------------------
# Query 2: painel via fontes brutas (fallback / mais detalhado)
# ---------------------------------------------------------------------------

def query_causal_panel_municipal(
    id_municipios: list[str],
    ano_inicio: int = 2010,
    ano_fim: int = 2023,
    include_siconfi: bool = True,
    include_antaq: bool = True,
    include_lags: bool = True,
) -> str:
    """Constrói painel causal diretamente das fontes brutas no BigQuery.

    Use quando o mart ainda não foi calculado ou quando precisa de colunas
    extras (SICONFI detalhado, etc.).

    Parameters
    ----------
    id_municipios:
        Códigos IBGE dos municípios do painel.
    ano_inicio / ano_fim:
        Período do painel (inclusive).
    include_siconfi:
        Incluir receitas e despesas municipais (SICONFI).
    include_antaq:
        Incluir movimentação de carga ANTAQ.
    include_lags:
        Incluir variáveis defasadas (pib_lag1, n_vinculos_lag1).

    Returns
    -------
    str — SQL Standard para execução no BigQuery.
    """
    mun_filter_pib = _municipio_filter(id_municipios)
    cnae_list = ", ".join(f"'{c}'" for c in CNAES_PORTUARIOS)

    siconfi_cte = ""
    siconfi_join = ""
    siconfi_cols = ""
    if include_siconfi:
        siconfi_cte = f"""
receitas AS (
    SELECT
        CAST(r.id_municipio AS STRING) AS id_municipio,
        r.ano,
        SUM(r.valor) AS receitas_total
    FROM {BD_SICONFI_RECEITAS} r
    WHERE CAST(r.id_municipio AS STRING) IN ({', '.join(f"'{m}'" for m in id_municipios)})
      AND r.ano BETWEEN {ano_inicio} AND {ano_fim}
      AND r.valor IS NOT NULL
    GROUP BY r.id_municipio, r.ano
),
despesas AS (
    SELECT
        CAST(d.id_municipio AS STRING) AS id_municipio,
        d.ano,
        SUM(d.valor) AS despesas_total
    FROM {BD_SICONFI_DESPESAS} d
    WHERE CAST(d.id_municipio AS STRING) IN ({', '.join(f"'{m}'" for m in id_municipios)})
      AND d.ano BETWEEN {ano_inicio} AND {ano_fim}
      AND d.valor IS NOT NULL
    GROUP BY d.id_municipio, d.ano
),"""
        siconfi_join = """
    LEFT JOIN receitas   rec USING (id_municipio, ano)
    LEFT JOIN despesas   dep USING (id_municipio, ano)"""
        siconfi_cols = """
        rec.receitas_total,
        dep.despesas_total,
        LN(NULLIF(rec.receitas_total, 0))                           AS receitas_total_log,
        LN(NULLIF(dep.despesas_total, 0))                           AS despesas_total_log,"""

    antaq_cte = ""
    antaq_join = ""
    antaq_cols = ""
    if include_antaq:
        antaq_cte = f"""
antaq_agg AS (
    SELECT
        cm.id_municipio,
        CAST(CAST(a.ano AS INT64) AS INT64) AS ano,
        SUM(a.vlpesocargabruta_oficial) AS toneladas_antaq
    FROM {VIEW_CARGA_METODOLOGIA_OFICIAL} a
    INNER JOIN {DIM_MUNICIPIO_ANTAQ_FQTN} cm
        ON a.municipio = cm.municipio_antaq_original
    WHERE cm.status = 'matched'
      AND cm.id_municipio IN ({', '.join(f"'{m}'" for m in id_municipios)})
      AND CAST(CAST(a.ano AS INT64) AS INT64) BETWEEN {ano_inicio} AND {ano_fim}
    GROUP BY cm.id_municipio, CAST(CAST(a.ano AS INT64) AS INT64)
),"""
        antaq_join = "\n    LEFT JOIN antaq_agg  ant USING (id_municipio, ano)"
        antaq_cols = """
        ant.toneladas_antaq,
        LN(NULLIF(ant.toneladas_antaq, 0))                          AS toneladas_antaq_log,"""

    lag_cols = ""
    if include_lags:
        lag_cols = """
        LAG(p.pib) OVER (PARTITION BY p.id_municipio ORDER BY p.ano)
            AS pib_lag1,
        LAG(rais_portuario.n_vinculos) OVER (PARTITION BY p.id_municipio ORDER BY p.ano)
            AS n_vinculos_lag1,"""

    return f"""
-- query_causal_panel_municipal
-- Painel causal construído a partir das fontes brutas.
WITH
pib_pop AS (
    SELECT
        CAST(p.id_municipio AS STRING) AS id_municipio,
        CAST(p.ano AS INT64)           AS ano,
        p.pib,
        CAST(p.populacao AS INT64)     AS populacao,
        SAFE_DIVIDE(p.pib, p.populacao) AS pib_per_capita
    FROM {BD_DADOS_PIB} p
    WHERE CAST(p.id_municipio AS STRING) IN ({', '.join(f"'{m}'" for m in id_municipios)})
      AND p.ano BETWEEN {ano_inicio} AND {ano_fim}
      AND p.pib IS NOT NULL
),
rais_portuario AS (
    SELECT
        CAST(r.id_municipio AS STRING) AS id_municipio,
        r.ano,
        COUNT(*)                       AS n_vinculos,
        AVG(r.valor_remuneracao_media) AS remuneracao_media
    FROM {BD_DADOS_RAIS} r
    WHERE CAST(r.id_municipio AS STRING) IN ({', '.join(f"'{m}'" for m in id_municipios)})
      AND r.cnae_2_subclasse IN ({cnae_list})
      AND r.vinculo_ativo_3112 = '1'
      AND r.ano BETWEEN {ano_inicio} AND {ano_fim}
      AND r.id_municipio IS NOT NULL
    GROUP BY r.id_municipio, r.ano
),
ipca_anual AS (
    SELECT
        EXTRACT(YEAR FROM PARSE_DATE('%Y%m', CAST(mes AS STRING))) AS ano,
        AVG(CAST(numero_indice AS FLOAT64))                         AS ipca_media
    FROM {BD_IPCA}
    WHERE SAFE_CAST(numero_indice AS FLOAT64) IS NOT NULL
    GROUP BY 1
),
{siconfi_cte}
{antaq_cte}
painel AS (
    SELECT
        p.id_municipio,
        p.ano,
        p.pib,
        p.populacao,
        p.pib_per_capita,
        rais_portuario.n_vinculos,
        rais_portuario.remuneracao_media,
        i.ipca_media,{siconfi_cols}{antaq_cols}
        -- log-transformações
        LN(NULLIF(p.pib,                        0))  AS pib_log,
        LN(NULLIF(rais_portuario.n_vinculos,    0))  AS n_vinculos_log,
        LN(NULLIF(rais_portuario.remuneracao_media, 0)) AS remuneracao_media_log,
        LN(NULLIF(p.pib_per_capita,             0))  AS pib_per_capita_log,
        LN(NULLIF(p.populacao,                  0))  AS populacao_log,{lag_cols}
        CURRENT_TIMESTAMP()                           AS _query_ts
    FROM pib_pop p
    LEFT JOIN rais_portuario USING (id_municipio, ano)
    LEFT JOIN ipca_anual i   USING (ano){siconfi_join}{antaq_join}
)
SELECT p.*
FROM painel p
ORDER BY p.id_municipio, p.ano
"""


# ---------------------------------------------------------------------------
# Query 3: painel de commodities (instrumento para IV)
# ---------------------------------------------------------------------------

def query_commodities_iv_panel(
    id_municipios: list[str],
    ano_inicio: int = 2010,
    ano_fim: int = 2023,
    commodity_cols: list[str] | None = None,
) -> str:
    """Faz join do painel municipal com preços de commodities para uso como IV.

    Requer que a tabela ``marts_impacto.external.worldbank_commodities``
    tenha sido criada via ``scripts/ingest_worldbank_commodities.py``.

    Parameters
    ----------
    commodity_cols:
        Colunas de commodities a incluir. Se None, inclui todas disponíveis.

    Returns
    -------
    str — SQL que traz o painel municipal + índice de commodities.
    """
    mun_filter = _municipio_filter(id_municipios)
    commodity_select = (
        "c.*"
        if commodity_cols is None
        else ", ".join(f"c.{col}" for col in commodity_cols)
    )

    return f"""
-- query_commodities_iv_panel
-- Painel municipal + precos de commodities para uso como instrumento IV.
SELECT
    m.*,
    {commodity_select}
FROM ({query_causal_panel_from_mart(
    id_municipios=id_municipios,
    ano_inicio=ano_inicio,
    ano_fim=ano_fim,
    include_lags=False,
)}) m
LEFT JOIN {COMMODITIES_TABLE} c
    ON m.ano = c.ano
WHERE {mun_filter.replace('id_municipio', 'm.id_municipio')}
ORDER BY m.id_municipio, m.ano
"""


# ---------------------------------------------------------------------------
# Query 4: UF-ano agregado (para análise SCM/DiD a nível estadual)
# ---------------------------------------------------------------------------

def query_causal_panel_uf_year(
    ufs: list[str],
    ano_inicio: int = 2010,
    ano_fim: int = 2023,
) -> str:
    """Agrega o mart de impacto para nível UF-ano.

    Útil para análises de alto nível (DiD estadual, SCM por UF).

    Parameters
    ----------
    ufs:
        Lista de siglas de UF (ex.: ['MA', 'PA', 'RJ']).

    Returns
    -------
    str — SQL que entrega painel agregado na granularidade UF-ano.
    """
    uf_filter = ", ".join(f"'{u}'" for u in ufs)

    return f"""
-- query_causal_panel_uf_year
-- Painel causal agregado para nível UF-ano.
WITH mart_uf AS (
    SELECT
        m.sigla_uf                                  AS uf,
        m.ano,
        SUM(m.pib)                                  AS pib,
        SUM(m.populacao)                            AS populacao,
        SUM(m.empregos_portuarios)                  AS n_vinculos,
        SUM(m.empregos_totais)                      AS empregos_totais,
        SUM(m.tonelagem_antaq_oficial)              AS toneladas_antaq,
        SUM(m.comercio_total_dolar)                 AS comercio_dolar,
        AVG(m.massa_salarial_portuaria /
            NULLIF(m.empregos_portuarios, 0))       AS remuneracao_media
    FROM {MART_IMPACTO_ECONOMICO_FQTN} m
    WHERE m.sigla_uf IN ({uf_filter})
      AND m.ano BETWEEN {ano_inicio} AND {ano_fim}
    GROUP BY m.sigla_uf, m.ano
),
ipca_anual AS (
    SELECT
        EXTRACT(YEAR FROM PARSE_DATE('%Y%m', CAST(mes AS STRING))) AS ano,
        AVG(CAST(numero_indice AS FLOAT64)) AS ipca_media
    FROM {BD_IPCA}
    WHERE SAFE_CAST(numero_indice AS FLOAT64) IS NOT NULL
    GROUP BY 1
)
SELECT
    m.uf,
    m.ano,
    m.pib,
    m.populacao,
    SAFE_DIVIDE(m.pib, m.populacao)             AS pib_per_capita,
    m.n_vinculos,
    m.empregos_totais,
    m.toneladas_antaq,
    m.comercio_dolar,
    m.remuneracao_media,
    i.ipca_media,
    LN(NULLIF(m.pib,            0))             AS pib_log,
    LN(NULLIF(m.n_vinculos,     0))             AS n_vinculos_log,
    LN(NULLIF(m.toneladas_antaq,0))             AS toneladas_antaq_log,
    LN(NULLIF(m.comercio_dolar, 0))             AS comercio_dolar_log
FROM mart_uf m
LEFT JOIN ipca_anual i USING (ano)
ORDER BY m.uf, m.ano
"""
