"""Testes funcionais do Épico 5 (E2) - query e semântica de retorno."""

import re

from app.db.bigquery.marts.module5 import MART_IMPACTO_ECONOMICO_FQTN
from app.db.bigquery.queries import get_query


def test_module5_e2_queries_use_expected_outputs_and_aliases():
    """Valida os campos esperados nas projeções dos indicadores do Módulo 5."""
    expected_aliases = {
        "IND-5.12": "crescimento_empregos_pct",
        "IND-5.13": "crescimento_comercio_pct",
        "IND-5.14": "correlacao",
        "IND-5.15": "correlacao",
        "IND-5.16": "correlacao",
        "IND-5.17": "elasticidade",
        "IND-5.19": "crescimento_relativo_uf_pp",
        "IND-5.20": "razao_emprego_total_portuario",
        "IND-5.21": "indice_concentracao_portuaria",
    }

    for code, alias in expected_aliases.items():
        params = {"id_municipio": "3304557"}
        sql = get_query(code)(**params)
        assert alias in sql
        assert "LIMIT 20" in sql

    for code in ("IND-5.14", "IND-5.15", "IND-5.16", "IND-5.17"):
        sql = get_query(code)(id_municipio="3304557")
        assert "n_observacoes" in sql


def test_module5_e2_0506_0511_e_021_depend_on_mart_and_not_name_join():
    """Verifica se indicadores da base portuária usam o mart e evitam join por nome."""
    query06 = get_query("IND-5.06")()
    query11 = get_query("IND-5.11")()

    assert MART_IMPACTO_ECONOMICO_FQTN in query06
    assert MART_IMPACTO_ECONOMICO_FQTN in query11
    assert "municipio = dir.nome" not in query06
    assert "municipio = dir.nome" not in query11


def test_module5_e2_indicator_0507_uses_dollar_and_pib_denominator():
    """Valida a nomenclatura de IND-5.07 como razão de comércio/PIB."""
    sql = get_query("IND-5.07")()
    assert "exportacao_dolar" in sql
    assert "importacao_dolar" in sql
    assert "m.pib" in sql


def test_module5_e2_ordering_prefers_time_series_for_municipio_filter():
    """Com id_municipio, os indicadores temporais ordenam por ano."""
    ranking_checks = {
        "IND-5.01": "p\\.ano",
        "IND-5.02": "p\\.ano",
        "IND-5.03": "p\\.ano",
        "IND-5.04": "p\\.ano",
        "IND-5.05": "p\\.ano",
        "IND-5.06": "m\\.ano",
        "IND-5.07": "m\\.ano",
        "IND-5.08": "p\\.ano",
        "IND-5.09": "p\\.ano",
        "IND-5.10": "a\\.ano",
        "IND-5.11": "a\\.ano",
        "IND-5.12": "a\\.ano",
        "IND-5.13": "a\\.ano",
        "IND-5.18": "m\\.ano",
        "IND-5.19": "m\\.ano",
        "IND-5.20": "p\\.ano",
        "IND-5.21": "n\\.ano",
    }

    for code, pattern in ranking_checks.items():
        sql = get_query(code)(id_municipio="3304557")
        assert re.search(rf"ORDER BY\s+{pattern} DESC", sql), f"Ordenação temporal ausente para {code}"
