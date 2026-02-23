"""
Queries BigQuery para o Módulo 3 - Recursos Humanos.

Este módulo contém as queries SQL para cálculo dos 12 indicadores
do Módulo 3 de recursos humanos, baseados em dados da RAIS.

NOTA: IND-3.07 (Produtividade) usa view oficial ANTAQ v_carga_metodologia_oficial.
"""

from typing import Optional
from app.db.bigquery.sector_codes import CNAES_PORTUARIOS


# ============================================================================
# Constants
# ============================================================================

# Dataset Base dos Dados
BD_DADOS_RAIS = "basedosdados.br_me_rais.microdados_vinculos"
BD_DADOS_PIB = "basedosdados.br_ibge_pib.municipio"
BD_DADOS_DIRETORIO_MUNICIPIO = "basedosdados.br_bd_diretorios_brasil.municipio"

# Dataset ANTAQ no BigQuery (para IND-3.07)
ANTAQ_DATASET = "antaqdados.br_antaq_estatistico_aquaviario"
VIEW_CARGA_METODOLOGIA_OFICIAL = f"{ANTAQ_DATASET}.v_carga_metodologia_oficial"

CNAES_CLAUSE = f"({', '.join(repr(c) for c in CNAES_PORTUARIOS)})"

def _as_string(field: str) -> str:
    return f"CAST({field} AS STRING)"


def _as_int(field: str) -> str:
    return f"SAFE_CAST({field} AS INT64)"


def _where_id_municipio(alias: str, id_municipio: str) -> str:
    return f"{_as_string(f'{alias}.id_municipio')} = '{id_municipio}'"


def _where_ano(alias: str, ano: int) -> str:
    return f"{alias}.ano = {ano}"


def _where_ano_range(alias: str, ano_inicio: int, ano_fim: int) -> str:
    return f"{alias}.ano BETWEEN {ano_inicio} AND {ano_fim}"


def _where_cnae_portuario(alias: str) -> str:
    return f"{_as_string(f'{alias}.cnae_2_subclasse')} IN {CNAES_CLAUSE}"


def _where_vinculo_ativo(alias: str) -> str:
    return f"{_as_int(f'{alias}.vinculo_ativo_3112')} = 1"


def _where_sexo_feminino(alias: str) -> str:
    return f"{_as_int(f'{alias}.sexo')} = 2"


# ============================================================================
# Módulo 3: Queries SQL Templates
# ============================================================================

def query_empregos_diretos_portuarios(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-3.01: Empregos Diretos Portuários [UNCTAD].

    Unidade: Contagem
    Granularidade: Município/Ano
    """
    where_clauses = [_where_cnae_portuario("r"), _where_vinculo_ativo("r")]
    if id_municipio:
        where_clauses.append(_where_id_municipio("r", id_municipio))
    if ano:
        where_clauses.append(_where_ano("r", ano))
    elif ano_inicio and ano_fim:
        where_clauses.append(_where_ano_range("r", ano_inicio, ano_fim))

    where_sql = "\n        AND ".join(where_clauses)

    return f"""
    SELECT
        {_as_string("r.id_municipio")} AS id_municipio,
        dir.nome AS nome_municipio,
        r.ano,
        COUNT(*) AS empregos_portuarios
    FROM
        `{BD_DADOS_RAIS}` r
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON {_as_string("r.id_municipio")} = {_as_string("dir.id_municipio")}
    WHERE
        {where_sql}
    GROUP BY
        id_municipio,
        dir.nome,
        r.ano
    ORDER BY
        r.ano DESC,
        dir.nome
    """


def query_paridade_genero_geral(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-3.02: Paridade de Gênero Geral [UNCTAD].

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_clauses = [_where_cnae_portuario("r"), _where_vinculo_ativo("r")]
    if id_municipio:
        where_clauses.append(_where_id_municipio("r", id_municipio))
    if ano:
        where_clauses.append(_where_ano("r", ano))
    elif ano_inicio and ano_fim:
        where_clauses.append(_where_ano_range("r", ano_inicio, ano_fim))

    where_sql = "\n        AND ".join(where_clauses)

    return f"""
    SELECT
        {_as_string("r.id_municipio")} AS id_municipio,
        dir.nome AS nome_municipio,
        r.ano,
        ROUND(SUM(CASE WHEN {_where_sexo_feminino("r")} THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS percentual_feminino
    FROM
        `{BD_DADOS_RAIS}` r
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON {_as_string("r.id_municipio")} = {_as_string("dir.id_municipio")}
    WHERE
        r.sexo IS NOT NULL
        AND {where_sql}
    GROUP BY
        id_municipio,
        dir.nome,
        r.ano
    ORDER BY
        r.ano DESC,
        dir.nome
    """


def query_paridade_categoria_profissional(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-3.03: Paridade por Categoria Profissional [UNCTAD].

    Unidade: Percentual por categoria
    Granularidade: Município/Ano/Categoria
    """
    where_clauses = [_where_cnae_portuario("r"), _where_vinculo_ativo("r")]
    if id_municipio:
        where_clauses.append(_where_id_municipio("r", id_municipio))
    if ano:
        where_clauses.append(_where_ano("r", ano))
    elif ano_inicio and ano_fim:
        where_clauses.append(_where_ano_range("r", ano_inicio, ano_fim))

    where_sql = "\n        AND ".join(where_clauses)

    return f"""
    WITH categorias AS (
        SELECT
            {_as_string("r.id_municipio")} AS id_municipio,
            r.ano,
            CASE
                WHEN SUBSTR(cbo_2002, 1, 1) IN ('1', '2') THEN 'GESTAO_TECNICO'
                WHEN SUBSTR(cbo_2002, 1, 1) IN ('3', '4') THEN 'ADMINISTRATIVO'
                ELSE 'OPERACIONAL'
            END AS categoria,
            COUNT(*) AS total,
            SUM(CASE WHEN {_where_sexo_feminino("r")} THEN 1 ELSE 0 END) AS feminino
        FROM
            `{BD_DADOS_RAIS}` r
        WHERE
            cbo_2002 IS NOT NULL
            AND sexo IS NOT NULL
            AND {where_sql}
        GROUP BY
            id_municipio,
            r.ano,
            categoria
    )
    SELECT
        c.id_municipio,
        dir.nome AS nome_municipio,
        c.ano,
        c.categoria,
        c.total,
        c.feminino,
        ROUND(c.feminino * 100.0 / c.total, 2) AS percentual_feminino
    FROM
        categorias c
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON c.id_municipio = {_as_string("dir.id_municipio")}
    ORDER BY
        c.ano DESC,
        id_municipio,
        c.categoria
    """


def query_taxa_emprego_temporario(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-3.04: Taxa de Emprego Temporário [UNCTAD].

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_clauses = [_where_cnae_portuario("r"), _where_vinculo_ativo("r")]
    if id_municipio:
        where_clauses.append(_where_id_municipio("r", id_municipio))
    if ano:
        where_clauses.append(_where_ano("r", ano))
    elif ano_inicio and ano_fim:
        where_clauses.append(_where_ano_range("r", ano_inicio, ano_fim))

    where_sql = "\n        AND ".join(where_clauses)

    return f"""
    SELECT
        {_as_string("r.id_municipio")} AS id_municipio,
        dir.nome AS nome_municipio,
        r.ano,
        ROUND(SUM(CASE
            WHEN {_as_int("r.tipo_vinculo")} IN (1, 3, 5, 7) THEN 1
            ELSE 0
        END) * 100.0 / COUNT(*), 2) AS taxa_temporario
    FROM
        `{BD_DADOS_RAIS}` r
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON {_as_string("r.id_municipio")} = {_as_string("dir.id_municipio")}
    WHERE
        r.tipo_vinculo IS NOT NULL
        AND {where_sql}
    GROUP BY
        id_municipio,
        dir.nome,
        r.ano
    ORDER BY
        r.ano DESC,
        dir.nome
    """


def query_salario_medio_setor_portuario(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-3.05: Salário Médio Setor Portuário [UNCTAD].

    Unidade: R$ (valores nominais)
    Granularidade: Município/Ano
    """
    where_clauses = [_where_cnae_portuario("r"), _where_vinculo_ativo("r")]
    if id_municipio:
        where_clauses.append(_where_id_municipio("r", id_municipio))
    if ano:
        where_clauses.append(_where_ano("r", ano))
    elif ano_inicio and ano_fim:
        where_clauses.append(_where_ano_range("r", ano_inicio, ano_fim))

    where_sql = "\n        AND ".join(where_clauses)

    return f"""
    SELECT
        {_as_string("r.id_municipio")} AS id_municipio,
        dir.nome AS nome_municipio,
        r.ano,
        ROUND(AVG(r.valor_remuneracao_media), 2) AS salario_medio
    FROM
        `{BD_DADOS_RAIS}` r
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON {_as_string("r.id_municipio")} = {_as_string("dir.id_municipio")}
    WHERE
        r.valor_remuneracao_media IS NOT NULL
        AND r.valor_remuneracao_media > 0
        AND {where_sql}
    GROUP BY
        id_municipio,
        dir.nome,
        r.ano
    ORDER BY
        r.ano DESC,
        dir.nome
    """


def query_massa_salarial_portuaria(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-3.06: Massa Salarial Portuária [UNCTAD].

    Unidade: R$/ano
    Granularidade: Município/Ano
    """
    where_clauses = [_where_cnae_portuario("r"), _where_vinculo_ativo("r")]
    if id_municipio:
        where_clauses.append(_where_id_municipio("r", id_municipio))
    if ano:
        where_clauses.append(_where_ano("r", ano))
    elif ano_inicio and ano_fim:
        where_clauses.append(_where_ano_range("r", ano_inicio, ano_fim))

    where_sql = "\n        AND ".join(where_clauses)

    return f"""
    SELECT
        {_as_string("r.id_municipio")} AS id_municipio,
        dir.nome AS nome_municipio,
        r.ano,
        ROUND(SUM(r.valor_remuneracao_media * 12), 2) AS massa_salarial_anual
    FROM
        `{BD_DADOS_RAIS}` r
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON {_as_string("r.id_municipio")} = {_as_string("dir.id_municipio")}
    WHERE
        r.valor_remuneracao_media IS NOT NULL
        AND {where_sql}
    GROUP BY
        id_municipio,
        dir.nome,
        r.ano
    ORDER BY
        r.ano DESC,
        dir.nome
    """


def query_produtividade_ton_empregado(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-3.07: Produtividade (ton/empregado) [UNCTAD].

    Unidade: Toneladas/Empregado
    Granularidade: Município/Ano

    Requer JOIN com dados ANTAQ (view oficial).
    """
    where_clause_rais = f"AND {_where_id_municipio('r', id_municipio)}" if id_municipio else ""
    where_ano_rais = f"AND {_where_ano('r', ano)}" if ano else ""

    where_clause_carga = f"AND {_as_string('municipio')} = '{id_municipio}'" if id_municipio else ""
    where_ano_carga = f"AND ano = {ano}" if ano else ""

    return f"""
    WITH empregos AS (
        SELECT
            {_as_string("r.id_municipio")} AS id_municipio,
            r.ano,
            COUNT(*) AS empregos_portuarios
        FROM
            `{BD_DADOS_RAIS}` r
        WHERE
            {_where_cnae_portuario("r")}
            AND {_where_vinculo_ativo("r")}
            {where_clause_rais}
            {where_ano_rais}
        GROUP BY
            id_municipio,
            r.ano
    ),
    tonelagem AS (
        SELECT
            {_as_string("municipio")} AS id_municipio,
            CAST(ano AS INT64) AS ano,
            SUM(vlpesocargabruta_oficial) AS tonelagem_total
        FROM
            `{VIEW_CARGA_METODOLOGIA_OFICIAL}`
        WHERE
            vlpesocargabruta_oficial IS NOT NULL
            {where_clause_carga}
            {where_ano_carga}
        GROUP BY
            id_municipio,
            ano
    )
    SELECT
        e.id_municipio,
        dir.nome AS nome_municipio,
        e.ano,
        ROUND(t.tonelagem_total / NULLIF(e.empregos_portuarios, 0), 2) AS ton_por_empregado
    FROM
        empregos e
    LEFT JOIN
        tonelagem t USING (id_municipio, ano)
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON e.id_municipio = {_as_string("dir.id_municipio")}
    ORDER BY
        ano DESC,
        id_municipio
    """


def query_receita_por_empregado(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-3.08: Receita por Empregado (proxy) [UNCTAD].

    Unidade: R$/Empregado
    Granularidade: Município/Ano
    """
    where_clause = f"AND {_where_id_municipio('r', id_municipio)}" if id_municipio else ""
    where_ano = f"AND r.ano = {ano}" if ano else ""

    return f"""
    WITH empregos AS (
        SELECT
            {_as_string("r.id_municipio")} AS id_municipio,
            r.ano,
            COUNT(*) AS empregos_portuarios
        FROM
            `{BD_DADOS_RAIS}` r
        WHERE
            {_where_cnae_portuario("r")}
            AND {_where_vinculo_ativo("r")}
            {where_clause}
            {where_ano}
        GROUP BY
            id_municipio,
            r.ano
    )
    SELECT
        e.id_municipio,
        dir.nome AS nome_municipio,
        e.ano,
        ROUND(p.pib / NULLIF(e.empregos_portuarios, 0), 2) AS pib_por_empregado_portuario
    FROM
        empregos e
    INNER JOIN
        `{BD_DADOS_PIB}` p ON e.id_municipio = {_as_string("p.id_municipio")} AND e.ano = p.ano
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON e.id_municipio = {_as_string("dir.id_municipio")}
    ORDER BY
        e.ano DESC,
        dir.nome
    """


def query_distribuicao_escolaridade(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-3.09: Distribuição por Escolaridade.

    Unidade: Percentual por faixa
    Granularidade: Município/Ano/Escolaridade
    """
    where_clauses = [_where_cnae_portuario("r"), _where_vinculo_ativo("r")]
    if id_municipio:
        where_clauses.append(_where_id_municipio("r", id_municipio))
    if ano:
        where_clauses.append(_where_ano("r", ano))

    where_sql = "\n        AND ".join(where_clauses)

    # A coluna de escolaridade na RAIS varia por versão do dataset.
    # Para evitar "Name ... not found" (erro de compilação), extraímos via JSON.
    grau_instrucao_expr = """
        COALESCE(
            JSON_VALUE(TO_JSON_STRING(r), '$.grau_instrucao'),
            JSON_VALUE(TO_JSON_STRING(r), '$.grau_instrucao_2005'),
            JSON_VALUE(TO_JSON_STRING(r), '$.grau_instrucao_2010'),
            JSON_VALUE(TO_JSON_STRING(r), '$.grau_instrucao_2019')
        )
    """.strip()

    return f"""
    WITH escolaridade AS (
        SELECT
            {_as_string("r.id_municipio")} AS id_municipio,
            r.ano,
            {grau_instrucao_expr} AS grau_instrucao,
            COUNT(*) AS qtd
        FROM
            `{BD_DADOS_RAIS}` r
        WHERE
            {where_sql}
            AND {grau_instrucao_expr} IS NOT NULL
        GROUP BY
            id_municipio,
            r.ano,
            grau_instrucao
    ),
    totais AS (
        SELECT
            id_municipio,
            ano,
            SUM(qtd) AS total
        FROM
            escolaridade
        GROUP BY
            id_municipio,
            ano
    )
    SELECT
        e.id_municipio,
        dir.nome AS nome_municipio,
        e.ano,
        e.grau_instrucao,
        e.qtd,
        ROUND(e.qtd * 100.0 / t.total, 2) AS percentual
    FROM
        escolaridade e
    INNER JOIN
        totais t ON e.id_municipio = t.id_municipio AND e.ano = t.ano
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON e.id_municipio = {_as_string("dir.id_municipio")}
    ORDER BY
        e.ano DESC,
        dir.nome,
        percentual DESC
    """


def query_idade_media(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-3.10: Idade Média.

    Unidade: Anos
    Granularidade: Município/Ano
    """
    where_clauses = [_where_cnae_portuario("r"), _where_vinculo_ativo("r")]
    if id_municipio:
        where_clauses.append(_where_id_municipio("r", id_municipio))
    if ano:
        where_clauses.append(_where_ano("r", ano))
    elif ano_inicio and ano_fim:
        where_clauses.append(_where_ano_range("r", ano_inicio, ano_fim))

    where_sql = "\n        AND ".join(where_clauses)

    return f"""
    SELECT
        {_as_string("r.id_municipio")} AS id_municipio,
        dir.nome AS nome_municipio,
        r.ano,
        ROUND(AVG(r.idade), 1) AS idade_media
    FROM
        `{BD_DADOS_RAIS}` r
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON {_as_string("r.id_municipio")} = {_as_string("dir.id_municipio")}
    WHERE
        r.idade IS NOT NULL
        AND r.idade > 0
        AND {where_sql}
    GROUP BY
        id_municipio,
        dir.nome,
        r.ano
    ORDER BY
        r.ano DESC,
        dir.nome
    """


def query_variacao_anual_empregos(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
) -> str:
    """
    IND-3.11: Variação Anual de Empregos.

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_clause = f"AND {_where_id_municipio('r', id_municipio)}" if id_municipio else ""
    where_ano = ""
    where_final_ano = ""
    if ano:
        where_ano = f"AND r.ano IN ({ano - 1}, {ano})"
        where_final_ano = f"WHERE a.ano = {ano}"

    return f"""
    WITH empregos_ano AS (
        SELECT
            {_as_string("r.id_municipio")} AS id_municipio,
            r.ano,
            COUNT(*) AS empregos
        FROM
            `{BD_DADOS_RAIS}` r
        WHERE
            {_where_cnae_portuario("r")}
            AND {_where_vinculo_ativo("r")}
            {where_clause}
            {where_ano}
        GROUP BY
            id_municipio,
            r.ano
    )
    SELECT
        a.id_municipio,
        dir.nome AS nome_municipio,
        a.ano,
        ROUND((a.empregos - b.empregos) * 100.0 / NULLIF(b.empregos, 0), 2) AS variacao_percentual
    FROM
        empregos_ano a
    INNER JOIN
        empregos_ano b ON a.id_municipio = b.id_municipio AND a.ano = b.ano + 1
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON a.id_municipio = {_as_string("dir.id_municipio")}
    {where_final_ano}
    ORDER BY
        a.ano DESC,
        dir.nome
    """


def query_participacao_emprego_local(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    IND-3.12: Participação no Emprego Local.

    Unidade: Percentual
    Granularidade: Município/Ano
    """
    where_portuarios = [_where_cnae_portuario("r"), _where_vinculo_ativo("r")]
    if id_municipio:
        where_portuarios.append(_where_id_municipio("r", id_municipio))
    if ano:
        where_portuarios.append(_where_ano("r", ano))
    elif ano_inicio and ano_fim:
        where_portuarios.append(_where_ano_range("r", ano_inicio, ano_fim))

    where_portuarios_sql = "\n        AND ".join(where_portuarios)

    where_totais = []
    if id_municipio:
        where_totais.append(_where_id_municipio("r2", id_municipio))
    if ano:
        where_totais.append(_where_ano("r2", ano))
    elif ano_inicio and ano_fim:
        where_totais.append(_where_ano_range("r2", ano_inicio, ano_fim))

    where_totais_sql = "\n        AND ".join(where_totais)
    where_totais_where = f"WHERE\n            {where_totais_sql}" if where_totais_sql else ""

    return f"""
    WITH portuarios AS (
        SELECT
            {_as_string("r.id_municipio")} AS id_municipio,
            r.ano,
            COUNT(*) AS empregos_portuarios
        FROM
            `{BD_DADOS_RAIS}` r
        WHERE
            {where_portuarios_sql}
        GROUP BY
            id_municipio,
            r.ano
    ),
    totais AS (
        SELECT
            {_as_string("r2.id_municipio")} AS id_municipio,
            r2.ano,
            COUNT(*) AS empregos_totais
        FROM
            `{BD_DADOS_RAIS}` r2
        {where_totais_where}
        GROUP BY
            id_municipio,
            r2.ano
    )
    SELECT
        p.id_municipio,
        dir.nome AS nome_municipio,
        p.ano,
        ROUND(p.empregos_portuarios * 100.0 / NULLIF(t.empregos_totais, 0), 2) AS participacao_emprego_local
    FROM
        portuarios p
    INNER JOIN
        totais t USING (id_municipio, ano)
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON p.id_municipio = {_as_string("dir.id_municipio")}
    ORDER BY
        p.ano DESC,
        dir.nome
    """


# ============================================================================
# Dicionário de Queries
# ============================================================================

QUERIES_MODULE_3 = {
    "IND-3.01": query_empregos_diretos_portuarios,
    "IND-3.02": query_paridade_genero_geral,
    "IND-3.03": query_paridade_categoria_profissional,
    "IND-3.04": query_taxa_emprego_temporario,
    "IND-3.05": query_salario_medio_setor_portuario,
    "IND-3.06": query_massa_salarial_portuaria,
    "IND-3.07": query_produtividade_ton_empregado,
    "IND-3.08": query_receita_por_empregado,
    "IND-3.09": query_distribuicao_escolaridade,
    "IND-3.10": query_idade_media,
    "IND-3.11": query_variacao_anual_empregos,
    "IND-3.12": query_participacao_emprego_local,
}


def get_query_module3(indicator_code: str) -> callable:
    """Retorna a função de query para um indicador do Módulo 3."""
    if indicator_code not in QUERIES_MODULE_3:
        raise ValueError(f"Indicador {indicator_code} não encontrado no Módulo 3")
    return QUERIES_MODULE_3[indicator_code]


# ============================================================================
# Queries Auxiliares (fora do dicionário de indicadores)
# ============================================================================

def query_total_municipal_employment(
    id_municipio: Optional[str] = None,
    ano: Optional[int] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> str:
    """
    Emprego total municipal — TODOS os setores (sem filtro CNAE).

    Usada pelo serviço de multiplicadores para calcular empregos
    indiretos via estimativa causal (outcome = emprego_total).

    Unidade: Contagem
    Granularidade: Município/Ano
    """
    where_clauses = [_where_vinculo_ativo("r")]
    if id_municipio:
        where_clauses.append(_where_id_municipio("r", id_municipio))
    if ano:
        where_clauses.append(_where_ano("r", ano))
    elif ano_inicio and ano_fim:
        where_clauses.append(_where_ano_range("r", ano_inicio, ano_fim))

    where_sql = "\n        AND ".join(where_clauses)

    return f"""
    SELECT
        {_as_string("r.id_municipio")} AS id_municipio,
        dir.nome AS nome_municipio,
        r.ano,
        COUNT(*) AS empregos_totais
    FROM
        `{BD_DADOS_RAIS}` r
    LEFT JOIN
        `{BD_DADOS_DIRETORIO_MUNICIPIO}` dir ON {_as_string("r.id_municipio")} = {_as_string("dir.id_municipio")}
    WHERE
        {where_sql}
    GROUP BY
        id_municipio,
        dir.nome,
        r.ano
    ORDER BY
        r.ano DESC,
        dir.nome
    """
