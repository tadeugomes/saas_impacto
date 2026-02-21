"""
Queries BigQuery para indicadores.

Este módulo exporta todas as queries organizadas por módulo.
"""

# Module 1 - Ship Operations
from app.db.bigquery.queries.module1_ship_operations import (
    query_tempo_medio_espera,
    query_tempo_medio_porto,
    query_tempo_bruto_atracacao,
    query_tempo_liquido_operacao,
    query_taxa_ocupacao_bercos,
    query_tempo_ocioso_turno,
    query_arqueacao_bruta_media,
    query_comprimento_medio_navios,
    query_calado_maximo_operacional,
    query_distribuicao_tipo_navio,
    query_numero_atracacoes,
    query_indice_paralisacao,
    query_resumo_operacoes_navios,
    QUERIES_MODULE_1,
)

# Module 2 - Cargo Operations
from app.db.bigquery.queries.module2_cargo_operations import (
    query_carga_total_movimentada,
    query_teus_movimentados,
    query_passageiros_ferry,
    query_passageiros_cruzeiro,
    query_carga_media_atracacao,
    query_produtividade_bruta,
    query_produtividade_granel_solido,
    query_produtividade_granel_liquido,
    query_movimentos_hora_conteiner,
    query_toneladas_por_hectare,
    query_toneladas_por_metro_cais,
    query_mix_carga,
    query_sazonalidade_mensal,
    QUERIES_MODULE_2,
)

# Module 3 - Human Resources
from app.db.bigquery.queries.module3_human_resources import (
    query_empregos_diretos_portuarios,
    query_paridade_genero_geral,
    query_paridade_categoria_profissional,
    query_taxa_emprego_temporario,
    query_salario_medio_setor_portuario,
    query_massa_salarial_portuaria,
    query_produtividade_ton_empregado,
    query_receita_por_empregado,
    query_distribuicao_escolaridade,
    query_idade_media,
    query_variacao_anual_empregos,
    query_participacao_emprego_local,
    QUERIES_MODULE_3,
)

# Module 4 - Foreign Trade
from app.db.bigquery.queries.module4_foreign_trade import (
    query_valor_fob_exportacoes,
    query_valor_fob_importacoes,
    query_balanca_comercial,
    query_peso_liquido_exportacoes,
    query_peso_liquido_importacoes,
    query_valor_medio_kg_exportacao,
    query_concentracao_por_pais,
    query_concentracao_por_ncm,
    query_variacao_anual_comercio,
    query_market_share_porto,
    QUERIES_MODULE_4,
)

# Module 5 - Economic Impact
from app.db.bigquery.queries.module5_economic_impact import (
    query_pib_municipal,
    query_pib_per_capita,
    query_populacao_municipal,
    query_pib_setorial_servicos,
    query_pib_setorial_industria,
    query_intensidade_portuaria,
    query_intensidade_comercial,
    query_concentracao_emprego_portuario,
    query_concentracao_salarial_portuaria,
    query_crescimento_pib_municipal,
    query_crescimento_tonelagem,
    query_crescimento_empregos,
    query_crescimento_comercio_exterior,
    query_correlacao_tonelagem_pib,
    query_correlacao_tonelagem_empregos,
    query_correlacao_comercio_pib,
    query_elasticidade_tonelagem_pib,
    query_participacao_pib_regional,
    query_crescimento_relativo_uf,
    query_razao_emprego_total_portuario,
    query_indice_concentracao_portuaria_m5,
    QUERIES_MODULE_5,
)

# Module 6 - Public Finance
from app.db.bigquery.queries.module6_public_finance import (
    query_arrecadacao_icms,
    query_arrecadacao_iss,
    query_receita_total_municipal,
    query_receita_per_capita,
    query_crescimento_receita,
    query_receita_fiscal_total,
    query_receita_fiscal_per_capita,
    query_receita_fiscal_por_tonelada,
    query_icms_por_tonelada,
    query_correlacao_tonelagem_receita_fiscal,
    query_elasticidade_tonelagem_receita_fiscal,
    QUERIES_MODULE_6,
)

# Module 7 - Synthetic Indices
from app.db.bigquery.queries.module7_synthetic_indices import (
    query_indice_eficiencia_operacional,
    query_indice_relevancia,
    query_indice_integracao,
    query_indice_concentracao_portuaria,
    query_ranking_portuarios,
    query_indice_benchmark,
    query_indice_variacao_anual,
    QUERIES_MODULE_7,
)

# Dicionário consolidado de todos os módulos
ALL_QUERIES = {
    **QUERIES_MODULE_1,
    **QUERIES_MODULE_2,
    **QUERIES_MODULE_3,
    **QUERIES_MODULE_4,
    **QUERIES_MODULE_5,
    **QUERIES_MODULE_6,
    **QUERIES_MODULE_7,
}

__all__ = [
    # Module 1 - Ship Operations
    "query_tempo_medio_espera",
    "query_tempo_medio_porto",
    "query_tempo_bruto_atracacao",
    "query_tempo_liquido_operacao",
    "query_taxa_ocupacao_bercos",
    "query_tempo_ocioso_turno",
    "query_arqueacao_bruta_media",
    "query_comprimento_medio_navios",
    "query_calado_maximo_operacional",
    "query_distribuicao_tipo_navio",
    "query_numero_atracacoes",
    "query_indice_paralisacao",
    "query_resumo_operacoes_navios",
    "QUERIES_MODULE_1",
    # Module 2 - Cargo Operations
    "query_carga_total_movimentada",
    "query_teus_movimentados",
    "query_passageiros_ferry",
    "query_passageiros_cruzeiro",
    "query_carga_media_atracacao",
    "query_produtividade_bruta",
    "query_produtividade_granel_solido",
    "query_produtividade_granel_liquido",
    "query_movimentos_hora_conteiner",
    "query_toneladas_por_hectare",
    "query_toneladas_por_metro_cais",
    "query_mix_carga",
    "query_sazonalidade_mensal",
    "QUERIES_MODULE_2",
    # Module 3 - Human Resources
    "query_empregos_diretos_portuarios",
    "query_paridade_genero_geral",
    "query_paridade_categoria_profissional",
    "query_taxa_emprego_temporario",
    "query_salario_medio_setor_portuario",
    "query_massa_salarial_portuaria",
    "query_produtividade_ton_empregado",
    "query_receita_por_empregado",
    "query_distribuicao_escolaridade",
    "query_idade_media",
    "query_variacao_anual_empregos",
    "query_participacao_emprego_local",
    "QUERIES_MODULE_3",
    # Module 4 - Foreign Trade
    "query_valor_fob_exportacoes",
    "query_valor_fob_importacoes",
    "query_balanca_comercial",
    "query_peso_liquido_exportacoes",
    "query_peso_liquido_importacoes",
    "query_valor_medio_kg_exportacao",
    "query_concentracao_por_pais",
    "query_concentracao_por_ncm",
    "query_variacao_anual_comercio",
    "query_market_share_porto",
    "QUERIES_MODULE_4",
    # Module 5 - Economic Impact
    "query_pib_municipal",
    "query_pib_per_capita",
    "query_populacao_municipal",
    "query_pib_setorial_servicos",
    "query_pib_setorial_industria",
    "query_intensidade_portuaria",
    "query_intensidade_comercial",
    "query_concentracao_emprego_portuario",
    "query_concentracao_salarial_portuaria",
    "query_crescimento_pib_municipal",
    "query_crescimento_tonelagem",
    "query_crescimento_empregos",
    "query_crescimento_comercio_exterior",
    "query_correlacao_tonelagem_pib",
    "query_correlacao_tonelagem_empregos",
    "query_correlacao_comercio_pib",
    "query_elasticidade_tonelagem_pib",
    "query_participacao_pib_regional",
    "query_crescimento_relativo_uf",
    "query_razao_emprego_total_portuario",
    "query_indice_concentracao_portuaria_m5",
    "QUERIES_MODULE_5",
    # Module 6 - Public Finance
    "query_arrecadacao_icms",
    "query_arrecadacao_iss",
    "query_receita_total_municipal",
    "query_receita_per_capita",
    "query_crescimento_receita",
    "query_receita_fiscal_total",
    "query_receita_fiscal_per_capita",
    "query_receita_fiscal_por_tonelada",
    "query_icms_por_tonelada",
    "query_correlacao_tonelagem_receita_fiscal",
    "query_elasticidade_tonelagem_receita_fiscal",
    "QUERIES_MODULE_6",
    # Module 7 - Synthetic Indices
    "query_indice_eficiencia_operacional",
    "query_indice_relevancia",
    "query_indice_integracao",
    "query_indice_concentracao_portuaria",
    "query_ranking_portuarios",
    "query_indice_benchmark",
    "query_indice_variacao_anual",
    "QUERIES_MODULE_7",
    # Consolidated
    "ALL_QUERIES",
]


def get_query(indicator_code: str) -> callable:
    """
    Retorna a função de query para qualquer indicador.

    Args:
        indicator_code: Código do indicador (ex: "IND-1.01")

    Returns:
        Função que gera a query SQL

    Raises:
        ValueError: Se o código do indicador não for encontrado
    """
    if indicator_code not in ALL_QUERIES:
        raise ValueError(f"Indicador {indicator_code} não encontrado")
    return ALL_QUERIES[indicator_code]
