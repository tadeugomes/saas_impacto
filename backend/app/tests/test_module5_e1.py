"""Testes do E1 - mart e crosswalk do Módulo 5."""

from app.db.bigquery.marts import module5 as marts_module5
from app.db.bigquery.marts.module5 import (
    MART_IMPACTO_ECONOMICO_FQTN,
    DIM_MUNICIPIO_ANTAQ_FQTN,
    build_dim_municipio_antaq_sql,
    build_impacto_economico_mart_sql,
)
from app.db.bigquery.queries.module5_economic_impact import (
    query_intensidade_portuaria,
    query_crescimento_tonelagem,
)


def test_module5_e1_mart_queries_reference_crosswalk_and_mart():
    """Valida se os templates SQL de E1 estão alinhados com nomes esperados."""
    dim_sql = build_dim_municipio_antaq_sql()
    mart_sql = build_impacto_economico_mart_sql()

    assert "dim_municipio_antaq" in dim_sql
    assert "match_type" in dim_sql
    assert "status" in dim_sql
    assert marts_module5.DIM_MUNICIPIO_ANTAQ_FQTN == DIM_MUNICIPIO_ANTAQ_FQTN
    assert "marts_impacto" in mart_sql
    assert "PARTITION BY ano" in mart_sql or "PARTITION BY RANGE_BUCKET" in mart_sql
    assert "CLUSTER BY id_municipio" in mart_sql
    assert "tonelagem_antaq_oficial" in mart_sql


def test_module5_e1_0606_and_0511_use_mart_tables():
    """Garantia de que IND-5.06 e IND-5.11 não usam join por nome de município."""
    sql_06 = query_intensidade_portuaria()
    sql_11 = query_crescimento_tonelagem()

    assert MART_IMPACTO_ECONOMICO_FQTN in sql_06
    assert MART_IMPACTO_ECONOMICO_FQTN in sql_11
    assert "c.municipio = dir.nome" not in sql_06
    assert "c.municipio = dir.nome" not in sql_11
    assert "v_carga_metodologia_oficial" not in sql_11
