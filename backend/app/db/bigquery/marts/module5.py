"""Definições de SQL para os marts do Módulo 5 (Impacto Econômico)."""

from datetime import datetime

from app.config import get_settings

# Estrutura padrão: projeto padrão da conta + dataset do projeto de marts + schema lógico
_SETTINGS = get_settings()

MARTS_PROJECT = _SETTINGS.gcp_project_id
MARTS_DATASET = "marts_impacto"
MART_IMPACTO_TABLE = "mart_impacto_economico"
MART_M5_METADATA_TABLE_NAME = "m5_metadata"
DIM_MUNICIPIO_ANTAQ_TABLE = "dim_municipio_antaq"

MART_IMPACTO_ECONOMICO = f"{MARTS_PROJECT}.{MARTS_DATASET}.{MART_IMPACTO_TABLE}"
MART_M5_METADATA_TABLE = f"{MARTS_PROJECT}.{MARTS_DATASET}.{MART_M5_METADATA_TABLE_NAME}"
DIM_MUNICIPIO_ANTAQ = f"{MARTS_PROJECT}.{MARTS_DATASET}.{DIM_MUNICIPIO_ANTAQ_TABLE}"

MART_IMPACTO_ECONOMICO_FQTN = f"`{MART_IMPACTO_ECONOMICO}`"
MART_M5_METADATA_TABLE_FQTN = f"`{MART_M5_METADATA_TABLE}`"
DIM_MUNICIPIO_ANTAQ_FQTN = f"`{DIM_MUNICIPIO_ANTAQ}`"

MART_IMPACTO_ECONOMICO_COLUMNS = [
    "id_municipio",
    "ano",
    "pib",
    "populacao",
    "va_servicos",
    "va_industria",
    "id_microrregiao",
    "sigla_uf",
    "tonelagem_antaq_oficial",
    "exportacao_dolar",
    "importacao_dolar",
    "comercio_total_dolar",
    "empregos_portuarios",
    "empregos_totais",
    "massa_salarial_portuaria",
    "massa_salarial_total",
    "data_atualizacao",
    "versao_pipeline",
]

# Fontes base utilizadas no mart
BD_DADOS_PIB = "basedosdados.br_ibge_pib.municipio"
BD_DADOS_POPULACAO = "basedosdados.br_ibge_populacao.municipio"
BD_DADOS_RAIS = "basedosdados.br_me_rais.microdados_vinculos"
ANTAQ_DATASET = "antaqdados.br_antaq_estatistico_aquaviario"
VIEW_CARGA_METODOLOGIA_OFICIAL = f"{ANTAQ_DATASET}.v_carga_metodologia_oficial"
COMEX_EXPORT = "basedosdados.br_me_comex_stat.municipio_exportacao"
COMEX_IMPORT = "basedosdados.br_me_comex_stat.municipio_importacao"
BD_DADOS_DIRETORIO_MUNICIPIO = "basedosdados.br_bd_diretorios_brasil.municipio"

CNAES_PORTUARIOS = [
    "5231101",
    "5231102",
    "5231103",
    "5011401",
    "5011402",
    "5012201",
    "5012202",
    "5021101",
    "5021102",
    "5022001",
    "5022002",
    "5030101",
    "5030102",
    "5030103",
    "5091201",
    "5091202",
    "5099801",
    "5099899",
    "5232000",
    "5239701",
    "5239799",
    "5250801",
    "5250802",
    "5250804",
]


def _normalize_name_expr(field: str) -> str:
    """
    Normaliza string para matching entre nomes de município.

    Remove acentuação (mapeamento Unicode/ASCII compatível com BigQuery Standard SQL)
    e excesso de espaço.
    """
    return (
        "LOWER(TRIM(REGEXP_REPLACE("
        f"TRANSLATE("
        f"LOWER(TRIM({field})),"
        "'àáâãäèéêëìíîïòóôõöùúûüç',"
        "'aaaaaeeeiiiiooooouuuuc'),"
        " '[^a-z0-9 ]', '')))"
    )


def build_dim_municipio_antaq_sql() -> str:
    """Retorna SQL de criação do crosswalk ANTAQ -> id_municipio IBGE."""
    return f"""
    CREATE OR REPLACE TABLE {DIM_MUNICIPIO_ANTAQ_FQTN}
    PARTITION BY data_execucao
    AS
    WITH municipios_antaq AS (
        SELECT DISTINCT
            TRIM(c.municipio) AS municipio_antaq_original
        FROM {VIEW_CARGA_METODOLOGIA_OFICIAL} c
        WHERE c.municipio IS NOT NULL
    ),
    municipios_normalizados AS (
        SELECT
            m.municipio_antaq_original,
            {_normalize_name_expr("m.municipio_antaq_original")} AS municipio_normalizado
        FROM municipios_antaq m
    ),
    correspondencia_exact AS (
        SELECT
            n.municipio_antaq_original,
            ARRAY_AGG(DISTINCT d.id_municipio IGNORE NULLS ORDER BY d.id_municipio) AS ids
        FROM municipios_normalizados n
        LEFT JOIN {BD_DADOS_DIRETORIO_MUNICIPIO} d
            ON n.municipio_antaq_original = d.nome
        GROUP BY n.municipio_antaq_original
    ),
    correspondencia_normalizada AS (
        SELECT
            n.municipio_antaq_original,
            n.municipio_normalizado,
            ARRAY_AGG(DISTINCT d.id_municipio IGNORE NULLS ORDER BY d.id_municipio) AS ids
        FROM municipios_normalizados n
        LEFT JOIN {BD_DADOS_DIRETORIO_MUNICIPIO} d
            ON n.municipio_normalizado = {_normalize_name_expr("d.nome")}
        GROUP BY
            n.municipio_antaq_original,
            n.municipio_normalizado
    )
    SELECT
        n.municipio_antaq_original,
        n.municipio_normalizado,
        CASE
            WHEN COALESCE(ARRAY_LENGTH(c.ids), 0) = 1 THEN c.ids[OFFSET(0)]
            WHEN COALESCE(ARRAY_LENGTH(c.ids), 0) = 0
                 AND COALESCE(ARRAY_LENGTH(cn.ids), 0) = 1 THEN cn.ids[OFFSET(0)]
            ELSE NULL
        END AS id_municipio,
        CASE
            WHEN COALESCE(ARRAY_LENGTH(c.ids), 0) = 1 THEN 'exact'
            WHEN COALESCE(ARRAY_LENGTH(c.ids), 0) = 0 AND COALESCE(ARRAY_LENGTH(cn.ids), 0) = 1 THEN 'normalized'
            WHEN COALESCE(ARRAY_LENGTH(c.ids), 0) > 1 OR COALESCE(ARRAY_LENGTH(cn.ids), 0) > 1 THEN 'fuzzy'
            ELSE 'manual'
        END AS match_type,
        CASE
            WHEN COALESCE(ARRAY_LENGTH(c.ids), 0) = 1 OR COALESCE(ARRAY_LENGTH(cn.ids), 0) = 1 THEN 'matched'
            WHEN COALESCE(ARRAY_LENGTH(c.ids), 0) > 1 OR COALESCE(ARRAY_LENGTH(cn.ids), 0) > 1 THEN 'ambiguous'
            ELSE 'unmatched'
        END AS status,
        CURRENT_DATE() AS data_execucao
    FROM municipios_normalizados n
    LEFT JOIN correspondencia_exact c USING (municipio_antaq_original)
    LEFT JOIN correspondencia_normalizada cn USING (municipio_antaq_original)
    """


def build_crosswalk_coverage_query() -> str:
    """Retorna SQL de cobertura do crosswalk para controle de qualidade."""
    return f"""
    SELECT
        COUNT(*) AS total_municipios_antaq,
        COUNTIF(status = 'matched') AS total_matched,
        COUNTIF(status = 'unmatched') AS total_unmatched,
        COUNTIF(status = 'ambiguous') AS total_ambiguous,
        SAFE_DIVIDE(COUNTIF(status = 'matched'), COUNT(*)) AS taxa_matched
    FROM {DIM_MUNICIPIO_ANTAQ_FQTN}
    """


def build_impacto_economico_mart_sql(versao_pipeline: str = "v1.0.0") -> str:
    """Retorna SQL de criação da versão completa do mart do Módulo 5."""
    return f"""
    CREATE OR REPLACE TABLE {MART_IMPACTO_ECONOMICO_FQTN}
    PARTITION BY RANGE_BUCKET(
        ano,
        GENERATE_ARRAY(1900, 2100, 1)
    )
    CLUSTER BY id_municipio
    AS
    WITH pib_base AS (
        SELECT
            CAST(p.id_municipio AS STRING) AS id_municipio,
            CAST(p.ano AS INT64) AS ano,
            p.pib,
            CAST(pop.populacao AS INT64) AS populacao,
            p.va_servicos,
            p.va_industria,
            d.id_microrregiao,
            d.sigla_uf
        FROM {BD_DADOS_PIB} p
        INNER JOIN {BD_DADOS_POPULACAO} pop
            ON CAST(pop.id_municipio AS STRING) = CAST(p.id_municipio AS STRING)
            AND CAST(pop.ano AS INT64) = CAST(p.ano AS INT64)
        INNER JOIN {BD_DADOS_DIRETORIO_MUNICIPIO} d
            ON p.id_municipio = d.id_municipio
        WHERE p.pib IS NOT NULL
    ),
    antaq_base AS (
        SELECT
            c.municipio AS municipio_antaq_original,
            c.ano,
            SUM(c.vlpesocargabruta_oficial) AS tonelagem_antaq_oficial
        FROM {VIEW_CARGA_METODOLOGIA_OFICIAL} c
        WHERE c.vlpesocargabruta_oficial IS NOT NULL
        GROUP BY c.municipio, c.ano
    ),
    antaq_mapeado AS (
        SELECT
            cm.id_municipio,
            CAST(CAST(a.ano AS INT64) AS INT64) AS ano,
            a.tonelagem_antaq_oficial
        FROM antaq_base a
        INNER JOIN {DIM_MUNICIPIO_ANTAQ_FQTN} cm
            ON a.municipio_antaq_original = cm.municipio_antaq_original
        WHERE cm.status = 'matched'
            AND cm.id_municipio IS NOT NULL
            AND a.tonelagem_antaq_oficial IS NOT NULL
    ),
    exportacao AS (
        SELECT
            CAST(e.id_municipio AS STRING) AS id_municipio,
            e.ano,
            SUM(e.valor_fob_dolar) AS exportacao_dolar
        FROM {COMEX_EXPORT} e
        WHERE e.valor_fob_dolar IS NOT NULL
        GROUP BY e.id_municipio, e.ano
    ),
    importacao AS (
        SELECT
            CAST(i.id_municipio AS STRING) AS id_municipio,
            i.ano,
            SUM(i.valor_fob_dolar) AS importacao_dolar
        FROM {COMEX_IMPORT} i
        WHERE i.valor_fob_dolar IS NOT NULL
        GROUP BY i.id_municipio, i.ano
    ),
    comex AS (
        SELECT
            COALESCE(e.id_municipio, i.id_municipio) AS id_municipio,
            COALESCE(e.ano, i.ano) AS ano,
            COALESCE(e.exportacao_dolar, 0) AS exportacao_dolar,
            COALESCE(i.importacao_dolar, 0) AS importacao_dolar,
            COALESCE(e.exportacao_dolar, 0) + COALESCE(i.importacao_dolar, 0) AS comercio_total_dolar
        FROM exportacao e
        FULL OUTER JOIN importacao i
            ON e.id_municipio = i.id_municipio AND e.ano = i.ano
    ),
    empregos_portuarios AS (
        SELECT
            CAST(r.id_municipio AS STRING) AS id_municipio,
            r.ano,
            COUNT(*) AS empregos_portuarios
        FROM {BD_DADOS_RAIS} r
        WHERE r.cnae_2_subclasse IN ({", ".join(repr(cnae) for cnae in CNAES_PORTUARIOS)})
            AND r.vinculo_ativo_3112 = '1'
            AND r.id_municipio IS NOT NULL
        GROUP BY r.id_municipio, r.ano
    ),
    empregos_totais AS (
        SELECT
            CAST(r.id_municipio AS STRING) AS id_municipio,
            r.ano,
            COUNT(*) AS empregos_totais
        FROM {BD_DADOS_RAIS} r
        WHERE r.vinculo_ativo_3112 = '1'
            AND r.id_municipio IS NOT NULL
        GROUP BY r.id_municipio, r.ano
    ),
    massa_salarial AS (
        SELECT
            CAST(r.id_municipio AS STRING) AS id_municipio,
            r.ano,
            SUM(
                CASE
                    WHEN r.cnae_2_subclasse IN ({", ".join(repr(cnae) for cnae in CNAES_PORTUARIOS)})
                    THEN r.valor_remuneracao_media * 12
                    ELSE 0
                END
            ) AS massa_salarial_portuaria,
            SUM(r.valor_remuneracao_media * 12) AS massa_salarial_total
        FROM {BD_DADOS_RAIS} r
        WHERE r.valor_remuneracao_media IS NOT NULL
            AND r.vinculo_ativo_3112 = '1'
            AND r.id_municipio IS NOT NULL
        GROUP BY r.id_municipio, r.ano
    )
    SELECT
        COALESCE(m.id_municipio, a.id_municipio, c.id_municipio, ep.id_municipio, et.id_municipio, ms.id_municipio) AS id_municipio,
        COALESCE(m.ano, a.ano, c.ano, ep.ano, et.ano, ms.ano) AS ano,
        m.pib,
        m.populacao,
        m.va_servicos,
        m.va_industria,
        m.id_microrregiao,
        m.sigla_uf,
        a.tonelagem_antaq_oficial,
        c.exportacao_dolar,
        c.importacao_dolar,
        c.comercio_total_dolar,
        ep.empregos_portuarios,
        et.empregos_totais,
        ms.massa_salarial_portuaria,
        ms.massa_salarial_total,
        CURRENT_TIMESTAMP() AS data_atualizacao,
        '{versao_pipeline}' AS versao_pipeline
    FROM pib_base m
    FULL OUTER JOIN antaq_mapeado a
        USING (id_municipio, ano)
    FULL OUTER JOIN comex c
        ON c.id_municipio = COALESCE(m.id_municipio, a.id_municipio)
        AND c.ano = COALESCE(m.ano, a.ano)
    FULL OUTER JOIN empregos_portuarios ep
        ON ep.id_municipio = COALESCE(m.id_municipio, a.id_municipio, c.id_municipio)
        AND ep.ano = COALESCE(m.ano, a.ano, c.ano)
    FULL OUTER JOIN empregos_totais et
        ON et.id_municipio = COALESCE(m.id_municipio, a.id_municipio, c.id_municipio, ep.id_municipio)
        AND et.ano = COALESCE(m.ano, a.ano, c.ano, ep.ano)
    FULL OUTER JOIN massa_salarial ms
        ON ms.id_municipio = COALESCE(m.id_municipio, a.id_municipio, c.id_municipio, ep.id_municipio, et.id_municipio)
        AND ms.ano = COALESCE(m.ano, a.ano, c.ano, ep.ano, et.ano)
    WHERE
        COALESCE(m.id_municipio, a.id_municipio, c.id_municipio, ep.id_municipio, et.id_municipio, ms.id_municipio) IS NOT NULL
    """


def build_indicator_metadata_sql() -> str:
    """Retorna SQL de metadados de indicadores processados no mart."""
    # Metadados-fonte da camada de API (fonte única da verdade de catálogo).
    # Evita manter este contrato em duplicidade.
    from app.services.generic_indicator_service import INDICATORS_METADATA

    module5_rows = [
        meta
        for code, meta in INDICATORS_METADATA.items()
        if str(code).startswith("IND-5.")
    ]

    if not module5_rows:
        # fallback defensivo para não quebrar a pipeline caso haja regressão no import
        module5_rows = []

    def _sql_val(v: object) -> str:
        if v is None:
            return "NULL"
        s = str(v)
        s = s.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{s}'"

    rows_sql = ",\n        ".join(
            (
                "STRUCT("
                + ", ".join(
                    [
                        f"{_sql_val(meta.get('codigo'))} AS codigo_indicador",
                        f"{_sql_val(meta.get('nome'))} AS nome",
                        f"{_sql_val(meta.get('unidade'))} AS unidade",
                        f"{_sql_val(meta.get('fonte_dados'))} AS fonte_dados",
                        f"{_sql_val(meta.get('granularidade'))} AS granularidade",
                        f"{_sql_val(meta.get('descricao'))} AS descricao",
                    ]
                )
                + f", '{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}' AS versao_pipeline, CURRENT_TIMESTAMP() AS data_atualizacao)"
                for meta in sorted(module5_rows, key=lambda m: m.get("codigo", ""))
            )
        )

    if not rows_sql:
        rows_sql = (
            "STRUCT('IND-5.01' AS codigo_indicador, 'PIB Municipal' AS nome, 'R$' AS unidade, "
            "'IBGE - PIB municipal' AS fonte_dados, 'Município/Ano' AS granularidade, "
            "'Indicador 5.01 - nível de fallback.' AS descricao, "
            f"'{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}' AS versao_pipeline, CURRENT_TIMESTAMP() AS data_atualizacao)"
        )

    return f"""
    CREATE OR REPLACE TABLE {MART_M5_METADATA_TABLE_FQTN}
    AS
    SELECT *
    FROM UNNEST([
        {rows_sql}
    ])
    """
