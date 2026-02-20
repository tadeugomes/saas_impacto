"""
Queries BigQuery para o Módulo 5 - Impacto Econômico Regional.

Este módulo contém as queries SQL para cálculo dos 21 indicadores
do Módulo 5 de impacto econômico regional.

NOTA: Usa view oficial ANTAQ v_carga_metodologia_oficial para dados de carga.
"""

from typing import Optional

from app.db.bigquery.marts.module5 import (
    MART_IMPACTO_ECONOMICO_FQTN,
    BD_DADOS_DIRETORIO_MUNICIPIO,
)


# ============================================================================
# Constants
# ============================================================================

# Datasets Base dos Dados
BD_DADOS_PIB = "basedosdados.br_ibge_pib.municipio"
BD_DADOS_POPULACAO = "basedosdados.br_ibge_populacao.municipio"
BD_DADOS_RAIS = "basedosdados.br_me_rais.microdados_vinculos"

# Dataset ANTAQ no BigQuery (view oficial)
ANTAQ_DATASET = "antaqdados.br_antaq_estatistico_aquaviario"
VIEW_CARGA_METODOLOGIA_OFICIAL = f"{ANTAQ_DATASET}.v_carga_metodologia_oficial"

# Diretórios para mapeamento Name -> ID
BD_DADOS_DIRETORIO_MUNICIPIO = "basedosdados.br_bd_diretorios_brasil.municipio"

# CNAEs do Setor Portuário
CNAES_PORTUARIOS = [
    '5231101', '5231102', '5231103', '5011401', '5011402',
    '5012201', '5012202', '5021101', '5021102', '5022001',
    '5022002', '5030101', '5030102', '5030103', '5091201',
    '5091202', '5099801', '5099899', '5232000', '5239701',
    '5239799', '5250801', '5250802', '5250804'
]

CNAES_CLAUSE = f"({', '.join(repr(c) for c in CNAES_PORTUARIOS)})"


# ============================================================================
# Módulo 5: Queries SQL Templates
# ============================================================================

def query_pib_municipal(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-5.01: PIB Municipal.

    Unidade: R$ (preços correntes)
    Granularidade: Município/Ano
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"p.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"p.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"p.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""
    order_by = "p.ano DESC" if id_municipio else "p.pib DESC"

    return f"""
    SELECT
        p.id_municipio,
        dir.nome AS nome_municipio,
        p.ano,
        ROUND(p.pib, 2) AS pib_municipal
    FROM
        `{BD_DADOS_PIB}` p
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON p.id_municipio = dir.id_municipio
    WHERE
        p.pib IS NOT NULL
        {f"AND {where_sql}" if where_sql else ""}
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_pib_per_capita(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-5.02: PIB per Capita.

    Unidade: R$/habitante
    Granularidade: Município/Ano
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"p.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"p.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"p.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""
    order_by = "p.ano DESC" if id_municipio else "pib_per_capita DESC"

    return f"""
    SELECT
        p.id_municipio,
        dir.nome AS nome_municipio,
        p.ano,
        ROUND(p.pib / NULLIF(pop.populacao, 0), 2) AS pib_per_capita
    FROM
        `{BD_DADOS_PIB}` p
    INNER JOIN
        `{BD_DADOS_POPULACAO}` pop ON p.id_municipio = pop.id_municipio AND p.ano = pop.ano
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON p.id_municipio = dir.id_municipio
    WHERE
        p.pib IS NOT NULL
        AND pop.populacao IS NOT NULL
        AND pop.populacao > 0
        {f"AND {where_sql}" if where_sql else ""}
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_populacao_municipal(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-5.03: População Municipal.

    Unidade: Habitantes
    Granularidade: Município/Ano
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"p.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"p.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"p.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""
    order_by = "p.ano DESC" if id_municipio else "p.populacao DESC"

    return f"""
    SELECT
        p.id_municipio,
        dir.nome AS nome_municipio,
        p.ano,
        p.populacao
    FROM
        `{BD_DADOS_POPULACAO}` p
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON p.id_municipio = dir.id_municipio
    WHERE
        p.populacao IS NOT NULL
        {f"AND {where_sql}" if where_sql else ""}
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_pib_setorial_servicos(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-5.04: PIB Setorial - Serviços (%).

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"p.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"p.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"p.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""
    order_by = "p.ano DESC" if id_municipio else "pib_servicos_percentual DESC"

    return f"""
    SELECT
        p.id_municipio,
        dir.nome AS nome_municipio,
        p.ano,
        ROUND(p.va_servicos * 100.0 / NULLIF(p.pib, 0), 2) AS pib_servicos_percentual
    FROM
        `{BD_DADOS_PIB}` p
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON p.id_municipio = dir.id_municipio
    WHERE
        p.va_servicos IS NOT NULL
        AND p.pib IS NOT NULL
        AND p.pib > 0
        {f"AND {where_sql}" if where_sql else ""}
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_pib_setorial_industria(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-5.05: PIB Setorial - Indústria (%).

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"p.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"p.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"p.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""
    order_by = "p.ano DESC" if id_municipio else "pib_industria_percentual DESC"

    return f"""
    SELECT
        p.id_municipio,
        dir.nome AS nome_municipio,
        p.ano,
        ROUND(p.va_industria * 100.0 / NULLIF(p.pib, 0), 2) AS pib_industria_percentual
    FROM
        `{BD_DADOS_PIB}` p
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON p.id_municipio = dir.id_municipio
    WHERE
        p.va_industria IS NOT NULL
        AND p.pib IS NOT NULL
        AND p.pib > 0
        {f"AND {where_sql}" if where_sql else ""}
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_intensidade_portuaria(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-5.06: Intensidade Portuária (ton/PIB).

    Unidade: Toneladas/R$
    Granularidade: Município/Ano
    """
    where_subquery = []
    if id_municipio:
        where_subquery.append(f"m.id_municipio = '{id_municipio}'")
    if ano:
        where_subquery.append(f"m.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_subquery.append(f"m.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_subquery_sql = "\n            AND ".join(where_subquery) if where_subquery else ""

    order_by = "m.ano DESC" if id_municipio else "intensidade_portuaria DESC"

    return f"""
    SELECT
        m.id_municipio,
        municipio_dir.nome AS nome_municipio,
        m.ano,
        ROUND(m.tonelagem_antaq_oficial / NULLIF(m.pib, 0), 4) AS intensidade_portuaria
    FROM {MART_IMPACTO_ECONOMICO_FQTN} m
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` municipio_dir ON m.id_municipio = municipio_dir.id_municipio
    WHERE
        m.pib IS NOT NULL
        AND m.pib > 0
        {f"AND {where_subquery_sql}" if where_subquery_sql else ""}
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_intensidade_comercial(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-5.07: Intensidade Comercial.

    Unidade: Razão (US$/R$)
    Granularidade: Município/Ano
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"m.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"m.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_clauses.append(f"m.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""
    order_by = "m.ano DESC" if id_municipio else "intensidade_comercial DESC"

    return f"""
    SELECT
        m.id_municipio,
        dir.nome AS nome_municipio,
        m.ano,
        ROUND(
            (COALESCE(m.exportacao_dolar, 0) + COALESCE(m.importacao_dolar, 0)) /
            NULLIF(m.pib, 0),
            4
        ) AS intensidade_comercial
    FROM {MART_IMPACTO_ECONOMICO_FQTN} m
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON m.id_municipio = dir.id_municipio
    WHERE
        m.pib IS NOT NULL
        AND m.pib > 0
        {f"AND {where_sql}" if where_sql else ""}
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_concentracao_emprego_portuario(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-5.08: Concentração de Emprego Portuário.

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_portuarios = [f"cnae_2_subclasse IN {CNAES_CLAUSE}", "vinculo_ativo_3112 = '1'"]
    if id_municipio:
        where_portuarios.append(f"r.id_municipio = '{id_municipio}'")
    if ano:
        where_portuarios.append(f"r.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_portuarios.append(f"r.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_portuarios_sql = "\n        AND ".join(where_portuarios)

    where_totais = []
    if id_municipio:
        where_totais.append(f"r2.id_municipio = '{id_municipio}'")
    if ano:
        where_totais.append(f"r2.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_totais.append(f"r2.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_totais_sql = "\n        AND ".join(where_totais)
    order_by = "p.ano DESC" if id_municipio else "concentracao_emprego_pct DESC"

    return f"""
    WITH portuarios AS (
        SELECT
            r.id_municipio,
            r.ano,
            COUNT(*) AS empregos_portuarios
        FROM
            `{BD_DADOS_RAIS}` r
        WHERE
            {where_portuarios_sql}
        GROUP BY
            r.id_municipio,
            r.ano
    ),
    totais AS (
        SELECT
            r2.id_municipio,
            r2.ano,
            COUNT(*) AS empregos_totais
        FROM
            `{BD_DADOS_RAIS}` r2
        WHERE
            r2.vinculo_ativo_3112 = '1'
            {f"AND {where_totais_sql}" if where_totais_sql else ""}
        GROUP BY
            r2.id_municipio,
            r2.ano
    )
    SELECT
        p.id_municipio,
        dir.nome AS nome_municipio,
        p.ano,
        ROUND(p.empregos_portuarios * 100.0 / NULLIF(t.empregos_totais, 0), 2) AS concentracao_emprego_pct
    FROM
        portuarios p
    INNER JOIN
        totais t USING (id_municipio, ano)
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON p.id_municipio = dir.id_municipio
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_concentracao_salarial_portuaria(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-5.09: Concentração Salarial Portuária.

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_portuarios = [f"cnae_2_subclasse IN {CNAES_CLAUSE}", "vinculo_ativo_3112 = '1'"]
    if id_municipio:
        where_portuarios.append(f"r.id_municipio = '{id_municipio}'")
    if ano:
        where_portuarios.append(f"r.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_portuarios.append(f"r.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_totais = []
    if id_municipio:
        where_totais.append(f"r2.id_municipio = '{id_municipio}'")
    if ano:
        where_totais.append(f"r2.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_totais.append(f"r2.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_portuarios_sql = "\n        AND ".join(where_portuarios)
    where_totais_sql = "\n        AND ".join(where_totais)
    order_by = "p.ano DESC" if id_municipio else "concentracao_salarial_pct DESC"

    return f"""
    WITH portuarios AS (
        SELECT
            r.id_municipio,
            r.ano,
            SUM(r.valor_remuneracao_media * 12) AS massa_salarial_port
        FROM
            `{BD_DADOS_RAIS}` r
        WHERE
            r.valor_remuneracao_media IS NOT NULL
            AND {where_portuarios_sql}
        GROUP BY
            r.id_municipio,
            r.ano
    ),
    totais AS (
        SELECT
            r2.id_municipio,
            r2.ano,
            SUM(r2.valor_remuneracao_media * 12) AS massa_salarial_total
        FROM
            `{BD_DADOS_RAIS}` r2
        WHERE
            r2.valor_remuneracao_media IS NOT NULL
            AND r2.vinculo_ativo_3112 = '1'
            {f"AND {where_totais_sql}" if where_totais_sql else ""}
        GROUP BY
            r2.id_municipio,
            r2.ano
    )
    SELECT
        p.id_municipio,
        dir.nome AS nome_municipio,
        p.ano,
        ROUND(p.massa_salarial_port * 100.0 / NULLIF(t.massa_salarial_total, 0), 2) AS concentracao_salarial_pct
    FROM
        portuarios p
    INNER JOIN
        totais t USING (id_municipio, ano)
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON p.id_municipio = dir.id_municipio
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_crescimento_pib_municipal(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-5.10: Crescimento PIB Municipal (%).

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"p.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"p.ano <= {ano}")

    where_sql = "\n        AND ".join(where_clauses) if where_clauses else ""
    order_by = "a.ano DESC" if id_municipio else "crescimento_pib_percentual DESC"

    return f"""
    WITH pib_ano AS (
        SELECT
            p.id_municipio,
            p.ano,
            p.pib
        FROM
            `{BD_DADOS_PIB}` p
        WHERE
            p.pib IS NOT NULL
            {f"AND {where_sql}" if where_sql else ""}
    )
    SELECT
        a.id_municipio,
        dir.nome AS nome_municipio,
        a.ano,
        ROUND((a.pib - b.pib) * 100.0 / NULLIF(b.pib, 0), 2) AS crescimento_pib_percentual
    FROM
        pib_ano a
    INNER JOIN
        pib_ano b ON a.id_municipio = b.id_municipio AND a.ano = b.ano + 1
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON a.id_municipio = dir.id_municipio
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_crescimento_tonelagem(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-5.11: Crescimento de Tonelagem (%).

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_clauses = []
    if id_municipio:
        where_clauses.append(f"m.id_municipio = '{id_municipio}'")
    if ano:
        where_clauses.append(f"m.ano <= {ano}")

    where_sql = "\n            AND ".join(where_clauses) if where_clauses else ""

    return f"""
    WITH tonelagem_ano AS (
        SELECT
            m.id_municipio,
            municipio_dir.nome,
            m.ano,
            m.tonelagem_antaq_oficial AS tonelagem
        FROM {MART_IMPACTO_ECONOMICO_FQTN} m
        LEFT JOIN
            `{BD_DADOS_DIRETORIO_MUNICIPIO}` municipio_dir
            ON m.id_municipio = municipio_dir.id_municipio
        WHERE
            m.tonelagem_antaq_oficial IS NOT NULL
            {f"AND {where_sql}" if where_sql else ""}
    )
    SELECT
        a.id_municipio,
        a.nome AS nome_municipio,
        a.ano,
        ROUND((a.tonelagem - b.tonelagem) * 100.0 / NULLIF(b.tonelagem, 0), 2) AS crescimento_tonelagem_pct
    FROM
        tonelagem_ano a
    INNER JOIN
        tonelagem_ano b ON a.id_municipio = b.id_municipio AND a.ano = b.ano + 1
    ORDER BY
        {"a.ano DESC, crescimento_tonelagem_pct DESC" if id_municipio else "crescimento_tonelagem_pct DESC"}
    LIMIT 20
    """


def query_crescimento_empregos(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-5.12: Crescimento de Empregos (%).

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_portuarios = [f"cnae_2_subclasse IN {CNAES_CLAUSE}", "vinculo_ativo_3112 = '1'"]
    if id_municipio:
        where_portuarios.append(f"r.id_municipio = '{id_municipio}'")
    where_ano = f"AND r.ano <= {ano}" if ano else ""

    where_portuarios_sql = "\n        AND ".join(where_portuarios)
    order_by = "a.ano DESC" if id_municipio else "crescimento_empregos_pct DESC"

    return f"""
    WITH empregos_ano AS (
        SELECT
            r.id_municipio,
            r.ano,
            COUNT(*) AS empregos
        FROM
            `{BD_DADOS_RAIS}` r
        WHERE
            {where_portuarios_sql}
            {where_ano}
        GROUP BY
            r.id_municipio,
            r.ano
    )
    SELECT
        a.id_municipio,
        dir.nome AS nome_municipio,
        a.ano,
        ROUND((a.empregos - b.empregos) * 100.0 / NULLIF(b.empregos, 0), 2) AS crescimento_empregos_pct
    FROM
        empregos_ano a
    INNER JOIN
        empregos_ano b ON a.id_municipio = b.id_municipio AND a.ano = b.ano + 1
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON a.id_municipio = dir.id_municipio
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_crescimento_comercio_exterior(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-5.13: Crescimento de Comércio Exterior (%).

    Calcula o crescimento do valor total (exportações + importações).

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_exp = []
    where_imp = []
    if id_municipio:
        where_exp.append(f"e.id_municipio = '{id_municipio}'")
        where_imp.append(f"i.id_municipio = '{id_municipio}'")
    where_ano_exp = f"AND e.ano <= {ano}" if ano else ""
    where_ano_imp = f"AND i.ano <= {ano}" if ano else ""

    where_exp_sql = "\n        AND ".join(where_exp) if where_exp else ""
    where_imp_sql = "\n        AND ".join(where_imp) if where_imp else ""
    order_by = "a.ano DESC" if id_municipio else "crescimento_comercio_pct DESC"

    return f"""
    WITH exportacoes_anual AS (
        SELECT
            e.id_municipio,
            e.ano,
            SUM(e.valor_fob_dolar) AS valor_exportacoes
        FROM
            `basedosdados.br_me_comex_stat.municipio_exportacao` e
        WHERE
            e.valor_fob_dolar IS NOT NULL
            {f"AND {where_exp_sql}" if where_exp_sql else ""}
            {where_ano_exp}
        GROUP BY
            e.id_municipio,
            e.ano
    ),
    importacoes_anual AS (
        SELECT
            i.id_municipio,
            i.ano,
            SUM(i.valor_fob_dolar) AS valor_importacoes
        FROM
            `basedosdados.br_me_comex_stat.municipio_importacao` i
        WHERE
            i.valor_fob_dolar IS NOT NULL
            {f"AND {where_imp_sql}" if where_imp_sql else ""}
            {where_ano_imp}
        GROUP BY
            i.id_municipio,
            i.ano
    ),
    comercio_anual AS (
        SELECT
            COALESCE(e.id_municipio, i.id_municipio) AS id_municipio,
            COALESCE(e.ano, i.ano) AS ano,
            COALESCE(e.valor_exportacoes, 0) + COALESCE(i.valor_importacoes, 0) AS comercio_total
        FROM
            exportacoes_anual e
        FULL OUTER JOIN
            importacoes_anual i USING (id_municipio, ano)
    )
    SELECT
        a.id_municipio,
        dir.nome AS nome_municipio,
        a.ano,
        ROUND((a.comercio_total - b.comercio_total) * 100.0 / NULLIF(b.comercio_total, 0), 2) AS crescimento_comercio_pct
    FROM
        comercio_anual a
    INNER JOIN
        comercio_anual b ON a.id_municipio = b.id_municipio AND a.ano = b.ano + 1
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON a.id_municipio = dir.id_municipio
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_correlacao_tonelagem_pib(
    id_municipio: Optional[str] = None,
    min_anos: int = 5,
) -> str:
    """
    IND-5.14: Correlação Tonelagem × PIB.

    Unidade: Coeficiente (-1 a +1)
    Granularidade: Município
    """
    where_clause = f"AND m.id_municipio = '{id_municipio}'" if id_municipio else ""

    return f"""
    WITH dados_completos AS (
        SELECT
            m.id_municipio,
            m.ano,
            m.tonelagem_antaq_oficial AS tonelagem,
            m.pib
        FROM
            {MART_IMPACTO_ECONOMICO_FQTN} m
        WHERE
            m.tonelagem_antaq_oficial IS NOT NULL
            AND m.pib IS NOT NULL
            {where_clause}
    )
    SELECT
        dc.id_municipio,
        dir.nome AS nome_municipio,
        ROUND(CORR(dc.tonelagem, dc.pib), 4) AS correlacao,
        ROUND(CORR(dc.tonelagem, dc.pib), 4) AS correlacao_tonelagem_pib,
        COUNT(*) AS n_observacoes,
        COUNT(*) AS anos_analisados
    FROM
        dados_completos dc
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON dc.id_municipio = dir.id_municipio
    GROUP BY
        dc.id_municipio, dir.nome
    HAVING
        COUNT(*) >= {min_anos}
    ORDER BY
        correlacao_tonelagem_pib DESC
    LIMIT 20
    """


def query_participacao_pib_regional(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-5.18: Participação no PIB Regional.

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_clause = f"AND m.id_municipio = '{id_municipio}'" if id_municipio else ""
    where_ano = f"AND p.ano = {ano}" if ano else ""
    order_by = "m.ano DESC" if id_municipio else "participacao_pib_regional_pct DESC"

    return f"""
    WITH pib_municipios AS (
        SELECT
            d.id_microrregiao,
            p.ano,
            SUM(p.pib) AS pib_regiao
        FROM
            `{BD_DADOS_PIB}` p
        INNER JOIN
            `{BD_DADOS_DIRETORIO_MUNICIPIO}` d USING (id_municipio)
        WHERE
            d.id_microrregiao IS NOT NULL
            {where_ano}
        GROUP BY
            d.id_microrregiao,
            p.ano
    )
    SELECT
        m.id_municipio,
        dir.nome AS nome_municipio,
        m.ano,
        ROUND(m.pib * 100.0 / NULLIF(r.pib_regiao, 0), 4) AS participacao_pib_regional_pct
    FROM
        `{BD_DADOS_PIB}` m
    INNER JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` d USING (id_municipio)
    INNER JOIN
        pib_municipios r ON d.id_microrregiao = r.id_microrregiao AND m.ano = r.ano
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON m.id_municipio = dir.id_municipio
    WHERE
        m.pib IS NOT NULL
        {where_clause}
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_correlacao_tonelagem_empregos(
    id_municipio: Optional[str] = None,
    min_anos: int = 5,
) -> str:
    """
    IND-5.15: Correlação Tonelagem × Empregos.

    Unidade: Coeficiente (-1 a +1)
    Granularidade: Município
    """
    where_clause = f"AND m.id_municipio = '{id_municipio}'" if id_municipio else ""
    where_clause_r = f"AND r.id_municipio = '{id_municipio}'" if id_municipio else ""

    return f"""
    WITH dados_completos AS (
        SELECT
            m.id_municipio,
            m.ano,
            e.empregos_portuarios AS empregos,
            m.tonelagem_antaq_oficial AS tonelagem
        FROM
            {MART_IMPACTO_ECONOMICO_FQTN} m
        INNER JOIN (
            SELECT
                r.id_municipio,
                r.ano,
                COUNT(*) AS empregos_portuarios
            FROM {BD_DADOS_RAIS} r
            WHERE
                cnae_2_subclasse IN {CNAES_CLAUSE}
                AND vinculo_ativo_3112 = '1'
                {where_clause_r}
            GROUP BY
                id_municipio,
                ano
        ) e
            ON m.id_municipio = e.id_municipio AND m.ano = e.ano
        WHERE
            m.tonelagem_antaq_oficial IS NOT NULL
            AND m.tonelagem_antaq_oficial > 0
            AND m.pib IS NOT NULL
            AND e.empregos_portuarios IS NOT NULL
    )
    SELECT
        dc.id_municipio,
        dir.nome AS nome_municipio,
        ROUND(CORR(dc.tonelagem, dc.empregos), 4) AS correlacao,
        ROUND(CORR(dc.tonelagem, dc.empregos), 4) AS correlacao_tonelagem_empregos,
        COUNT(*) AS n_observacoes,
        COUNT(*) AS anos_analisados
    FROM
        dados_completos dc
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON dc.id_municipio = dir.id_municipio
    GROUP BY
        dc.id_municipio, dir.nome
    HAVING
        COUNT(*) >= {min_anos}
    ORDER BY
        correlacao_tonelagem_empregos DESC
    LIMIT 20
    """


def query_correlacao_comercio_pib(
    id_municipio: Optional[str] = None,
    min_anos: int = 5,
) -> str:
    """
    IND-5.16: Correlação Comércio × PIB.

    Unidade: Coeficiente (-1 a +1)
    Granularidade: Município
    """
    where_clause_exp = f"AND e.id_municipio = '{id_municipio}'" if id_municipio else ""
    where_clause_imp = f"AND i.id_municipio = '{id_municipio}'" if id_municipio else ""

    return f"""
    WITH exportacoes AS (
        SELECT
            e.id_municipio,
            e.ano,
            SUM(e.valor_fob_dolar) AS valor_exportacoes
        FROM
            `basedosdados.br_me_comex_stat.municipio_exportacao` e
        WHERE
            e.valor_fob_dolar IS NOT NULL
            {where_clause_exp}
        GROUP BY
            e.id_municipio,
            e.ano
    ),
    importacoes AS (
        SELECT
            i.id_municipio,
            i.ano,
            SUM(i.valor_fob_dolar) AS valor_importacoes
        FROM
            `basedosdados.br_me_comex_stat.municipio_importacao` i
        WHERE
            i.valor_fob_dolar IS NOT NULL
            {where_clause_imp}
        GROUP BY
            i.id_municipio,
            i.ano
    ),
    comercio_total AS (
        SELECT
            COALESCE(e.id_municipio, i.id_municipio) AS id_municipio,
            COALESCE(e.ano, i.ano) AS ano,
            COALESCE(e.valor_exportacoes, 0) + COALESCE(i.valor_importacoes, 0) AS comercio
        FROM
            exportacoes e
        FULL OUTER JOIN
            importacoes i USING (id_municipio, ano)
    ),
    dados_completos AS (
        SELECT
            c.id_municipio,
            c.ano,
            c.comercio,
            p.pib
        FROM
            comercio_total c
        INNER JOIN
            `{BD_DADOS_PIB}` p ON c.id_municipio = p.id_municipio AND c.ano = p.ano
        WHERE
            p.pib IS NOT NULL
            AND c.comercio > 0
    )
    SELECT
        dc.id_municipio,
        dir.nome AS nome_municipio,
        ROUND(CORR(dc.comercio, dc.pib), 4) AS correlacao,
        ROUND(CORR(dc.comercio, dc.pib), 4) AS correlacao_comercio_pib,
        COUNT(*) AS n_observacoes,
        COUNT(*) AS anos_analisados
    FROM
        dados_completos dc
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON dc.id_municipio = dir.id_municipio
    GROUP BY
        dc.id_municipio, dir.nome
    HAVING
        COUNT(*) >= {min_anos}
    ORDER BY
        correlacao_comercio_pib DESC
    LIMIT 20
    """


def query_elasticidade_tonelagem_pib(
    id_municipio: Optional[str] = None,
    min_anos: int = 5,
) -> str:
    """
    IND-5.17: Elasticidade Tonelagem/PIB.

    Regressão log-log simples: ln(tonelagem) = α + β·ln(PIB)
    β é a elasticidade.

    Unidade: Elasticidade
    Granularidade: Município

    Interpretação: Variação % na tonelagem para cada 1% de variação no PIB
    """
    where_clause = f"AND m.id_municipio = '{id_municipio}'" if id_municipio else ""

    return f"""
    WITH dados_log AS (
        SELECT
            m.id_municipio,
            dir.nome,
            m.ano,
            LN(m.tonelagem_antaq_oficial) AS ln_tonelagem,
            LN(m.pib) AS ln_pib
        FROM
            {MART_IMPACTO_ECONOMICO_FQTN} m
        LEFT JOIN
            `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON m.id_municipio = dir.id_municipio
        WHERE
            m.tonelagem_antaq_oficial > 0
            AND m.pib > 0
            {where_clause}
    ),
    estatisticas AS (
        SELECT
            id_municipio,
            nome,
            COUNT(*) AS n,
            SUM(ln_tonelagem) AS sum_ln_ton,
            SUM(ln_pib) AS sum_ln_pib,
            SUM(ln_tonelagem * ln_pib) AS sum_ln_ton_pib,
            SUM(ln_tonelagem * ln_tonelagem) AS sum_ln_ton_sq,
            SUM(ln_pib * ln_pib) AS sum_ln_pib_sq
        FROM
            dados_log
        GROUP BY
            id_municipio, nome
        HAVING
            COUNT(*) >= {min_anos}
    )
    SELECT
        id_municipio,
        nome AS nome_municipio,
        ROUND(
            (n * sum_ln_ton_pib - sum_ln_ton * sum_ln_pib) /
            NULLIF(n * sum_ln_pib_sq - sum_ln_pib * sum_ln_pib, 0),
            4
        ) AS elasticidade,
        ROUND(
            (n * sum_ln_ton_pib - sum_ln_ton * sum_ln_pib) /
            NULLIF(n * sum_ln_pib_sq - sum_ln_pib * sum_ln_pib, 0),
            4
        ) AS elasticidade_tonelagem_pib,
        n AS n_observacoes,
        n AS anos_analisados
    FROM
        estatisticas
    ORDER BY
        elasticidade_tonelagem_pib DESC
    LIMIT 20
    """


def query_crescimento_relativo_uf(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-5.19: Crescimento Relativo ao Estado.

    Compara o crescimento do PIB municipal com o crescimento médio do PIB estadual.

    Unidade: Pontos percentuais
    Granularidade: Município/Ano
    """
    where_mun = f"AND p.id_municipio = '{id_municipio}'" if id_municipio else ""
    where_ano = f"AND p.ano <= {ano}" if ano else ""
    order_by = "m.ano DESC" if id_municipio else "crescimento_relativo_uf_pp DESC"

    return f"""
    WITH pib_municipal AS (
        SELECT
            p.id_municipio,
            d.sigla_uf,
            p.ano,
            p.pib
        FROM
            `{BD_DADOS_PIB}` p
        INNER JOIN
            `{BD_DADOS_DIRETORIO_MUNICIPIO}` d USING (id_municipio)
        WHERE
            p.pib IS NOT NULL
            {where_mun}
            {where_ano}
    ),
    cresc_municipal AS (
        SELECT
            a.id_municipio,
            a.sigla_uf,
            a.ano,
            (a.pib - b.pib) * 100.0 / NULLIF(b.pib, 0) AS crescimento_municipal_pct
        FROM
            pib_municipal a
        INNER JOIN
            pib_municipal b ON a.id_municipio = b.id_municipio AND a.ano = b.ano + 1
    ),
    pib_estadual AS (
        SELECT
            sigla_uf,
            ano,
            SUM(pib) AS pib_estadual
        FROM
            pib_municipal
        GROUP BY
            sigla_uf,
            ano
    ),
    cresc_estadual AS (
        SELECT
            a.sigla_uf,
            a.ano,
            (a.pib_estadual - b.pib_estadual) * 100.0 / NULLIF(b.pib_estadual, 0) AS crescimento_estadual_pct
        FROM
            pib_estadual a
        INNER JOIN
            pib_estadual b ON a.sigla_uf = b.sigla_uf AND a.ano = b.ano + 1
    )
    SELECT
        m.id_municipio,
        dir.nome AS nome_municipio,
        m.ano,
        ROUND(m.crescimento_municipal_pct, 2) AS crescimento_municipal_pct,
        ROUND(u.crescimento_estadual_pct, 2) AS crescimento_estadual_pct,
        ROUND(m.crescimento_municipal_pct - u.crescimento_estadual_pct, 2) AS crescimento_relativo_uf_pp,
        ROUND(m.crescimento_municipal_pct - u.crescimento_estadual_pct, 2) AS crescimento_relativo_uf_pct
    FROM
        cresc_municipal m
    INNER JOIN
        cresc_estadual u ON m.sigla_uf = u.sigla_uf AND m.ano = u.ano
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON m.id_municipio = dir.id_municipio
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_razao_emprego_total_portuario(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-5.20: Razão Emprego Total/Portuário.

    Quantos empregos totais existem para cada emprego portuário.

    Unidade: Razão
    Granularidade: Município/Ano
    """
    where_portuarios = [f"cnae_2_subclasse IN {CNAES_CLAUSE}", "vinculo_ativo_3112 = '1'"]
    if id_municipio:
        where_portuarios.append(f"r.id_municipio = '{id_municipio}'")
    if ano:
        where_portuarios.append(f"r.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_portuarios.append(f"r.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_portuarios_sql = "\n        AND ".join(where_portuarios)

    where_totais = []
    if id_municipio:
        where_totais.append(f"r2.id_municipio = '{id_municipio}'")
    if ano:
        where_totais.append(f"r2.ano = {ano}")
    elif ano_inicio and ano_fim:
        where_totais.append(f"r2.ano BETWEEN {ano_inicio} AND {ano_fim}")

    where_totais_sql = "\n        AND ".join(where_totais)
    order_by = "p.ano DESC" if id_municipio else "razao_emprego_total_portuario DESC"

    return f"""
    WITH portuarios AS (
        SELECT
            r.id_municipio,
            r.ano,
            COUNT(*) AS empregos_portuarios
        FROM
            `{BD_DADOS_RAIS}` r
        WHERE
            {where_portuarios_sql}
        GROUP BY
            r.id_municipio,
            r.ano
    ),
    totais AS (
        SELECT
            r2.id_municipio,
            r2.ano,
            COUNT(*) AS empregos_totais
        FROM
            `{BD_DADOS_RAIS}` r2
        WHERE
            r2.vinculo_ativo_3112 = '1'
            {f"AND {where_totais_sql}" if where_totais_sql else ""}
        GROUP BY
            r2.id_municipio,
            r2.ano
    )
    SELECT
        p.id_municipio,
        dir.nome AS nome_municipio,
        p.ano,
        p.empregos_portuarios,
        t.empregos_totais,
        ROUND(t.empregos_totais / NULLIF(p.empregos_portuarios, 0), 2) AS razao_emprego_total_portuario
    FROM
        portuarios p
    INNER JOIN
        totais t USING (id_municipio, ano)
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON p.id_municipio = dir.id_municipio
    ORDER BY
        {order_by}
    LIMIT 20
    """


def query_indice_concentracao_portuaria_m5(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-5.21: Índice de Concentração Portuária.

    Score composto normalizado (0-100) baseado em:
    - Participação no emprego local
    - Intensidade portuária
    - Participação no PIB regional

    Unidade: Índice (0-100)
    Granularidade: Município/Ano
    """
    where_clause = f"AND m.id_municipio = '{id_municipio}'" if id_municipio else ""
    where_ano = f"AND m.ano = {ano}" if ano else ""
    order_by = "n.ano DESC" if id_municipio else "indice_concentracao_portuaria DESC"

    return f"""
    WITH pib_base AS (
        SELECT
            p.id_municipio,
            p.ano,
            p.pib,
            d.id_microrregiao
        FROM `{BD_DADOS_PIB}` p
        INNER JOIN `{BD_DADOS_DIRETORIO_MUNICIPIO}` d USING (id_municipio)
    ),
    emprego_concentracao AS (
        SELECT
            p.id_municipio,
            p.ano,
            p.empregos_portuarios * 100.0 / NULLIF(t.empregos_totais, 0) AS participacao_emprego
    FROM (
            SELECT r.id_municipio, r.ano, COUNT(*) AS empregos_portuarios
            FROM `{BD_DADOS_RAIS}` r
            WHERE r.cnae_2_subclasse IN {CNAES_CLAUSE}
                AND r.vinculo_ativo_3112 = '1'
                {f"AND r.id_municipio = '{id_municipio}'" if id_municipio else ""}
                {f"AND r.ano = {ano}" if ano else ""}
            GROUP BY r.id_municipio, r.ano
        ) p
        JOIN (
            SELECT r2.id_municipio, r2.ano, COUNT(*) AS empregos_totais
            FROM `{BD_DADOS_RAIS}` r2
            WHERE r2.vinculo_ativo_3112 = '1'
                {f"AND r2.id_municipio = '{id_municipio}'" if id_municipio else ""}
                {f"AND r2.ano = {ano}" if ano else ""}
            GROUP BY r2.id_municipio, r2.ano
        ) t USING (id_municipio, ano)
    ),
    intensidade_portuaria AS (
        SELECT
            m.id_municipio,
            m.ano,
            m.tonelagem_antaq_oficial / NULLIF(m.pib, 0) AS intensidade_portuaria
        FROM {MART_IMPACTO_ECONOMICO_FQTN} m
        WHERE 1=1
            {where_ano}
            {where_clause}
            AND m.pib IS NOT NULL
            AND m.tonelagem_antaq_oficial IS NOT NULL
    ),
    participacao_pib_regional AS (
        SELECT
            m.id_municipio,
            m.ano,
            m.pib * 100.0 / NULLIF(r.pib_regiao, 0) AS participacao_pib_regional
        FROM pib_base m
        JOIN (
            SELECT id_microrregiao, ano, SUM(pib) AS pib_regiao
            FROM pib_base
            WHERE id_microrregiao IS NOT NULL {f"AND ano = {ano}" if ano else ""}
            GROUP BY id_microrregiao, ano
        ) r ON m.id_microrregiao = r.id_microrregiao AND m.ano = r.ano
        WHERE m.pib IS NOT NULL {where_clause}
    ),
    indicadores_juntos AS (
        SELECT
            COALESCE(e.id_municipio, i.id_municipio, p.id_municipio) AS id_municipio,
            COALESCE(e.ano, i.ano, p.ano) AS ano,
            e.participacao_emprego,
            i.intensidade_portuaria,
            p.participacao_pib_regional
        FROM emprego_concentracao e
        FULL OUTER JOIN intensidade_portuaria i USING (id_municipio, ano)
        FULL OUTER JOIN participacao_pib_regional p USING (id_municipio, ano)
    ),
    minmax AS (
        SELECT
            MIN(participacao_emprego) AS min_emprego,
            MAX(participacao_emprego) AS max_emprego,
            MIN(intensidade_portuaria) AS min_intensidade,
            MAX(intensidade_portuaria) AS max_intensidade,
            MIN(participacao_pib_regional) AS min_pib_reg,
            MAX(participacao_pib_regional) AS max_pib_reg
        FROM indicadores_juntos
    ),
    normalizado AS (
        SELECT
            i.id_municipio,
            i.ano,
            (i.participacao_emprego - m.min_emprego) /
                NULLIF(m.max_emprego - m.min_emprego, 0) * 100 AS norm_emprego,
            (i.intensidade_portuaria - m.min_intensidade) /
                NULLIF(m.max_intensidade - m.min_intensidade, 0) * 100 AS norm_intensidade,
            (i.participacao_pib_regional - m.min_pib_reg) /
                NULLIF(m.max_pib_reg - m.min_pib_reg, 0) * 100 AS norm_pib_reg
        FROM indicadores_juntos i
        CROSS JOIN minmax m
    )
    SELECT
        n.id_municipio,
        dir.nome AS nome_municipio,
        n.ano,
        ROUND(
            (COALESCE(n.norm_emprego, 0) + COALESCE(n.norm_intensidade, 0) + COALESCE(n.norm_pib_reg, 0)) / 3,
            2
        ) AS indice_concentracao_portuaria
    FROM
        normalizado n
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON n.id_municipio = dir.id_municipio
    ORDER BY
        {order_by}
    LIMIT 20
    """


# ============================================================================
# Dicionário de Queries
# ============================================================================

QUERIES_MODULE_5 = {
    "IND-5.01": query_pib_municipal,
    "IND-5.02": query_pib_per_capita,
    "IND-5.03": query_populacao_municipal,
    "IND-5.04": query_pib_setorial_servicos,
    "IND-5.05": query_pib_setorial_industria,
    "IND-5.06": query_intensidade_portuaria,
    "IND-5.07": query_intensidade_comercial,
    "IND-5.08": query_concentracao_emprego_portuario,
    "IND-5.09": query_concentracao_salarial_portuaria,
    "IND-5.10": query_crescimento_pib_municipal,
    "IND-5.11": query_crescimento_tonelagem,
    "IND-5.12": query_crescimento_empregos,
    "IND-5.13": query_crescimento_comercio_exterior,
    "IND-5.14": query_correlacao_tonelagem_pib,
    "IND-5.15": query_correlacao_tonelagem_empregos,
    "IND-5.16": query_correlacao_comercio_pib,
    "IND-5.17": query_elasticidade_tonelagem_pib,
    "IND-5.18": query_participacao_pib_regional,
    "IND-5.19": query_crescimento_relativo_uf,
    "IND-5.20": query_razao_emprego_total_portuario,
    "IND-5.21": query_indice_concentracao_portuaria_m5,
}


def get_query_module5(indicator_code: str) -> callable:
    """Retorna a função de query para um indicador do Módulo 5."""
    if indicator_code not in QUERIES_MODULE_5:
        raise ValueError(f"Indicador {indicator_code} não encontrado no Módulo 5")
    return QUERIES_MODULE_5[indicator_code]
