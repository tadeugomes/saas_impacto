"""Testes de robustez para o Épico 5 (E3) - contrato de execução/qualidade estática."""
from __future__ import annotations

import inspect
import re
import pytest

from app.db.bigquery.marts.module5 import MART_IMPACTO_ECONOMICO_FQTN
from app.db.bigquery.queries import get_query
from app.schemas.indicators import GenericIndicatorRequest
from app.services.generic_indicator_service import GenericIndicatorService
from app.db.bigquery.queries.module5_economic_impact import (
    BD_DADOS_PIB,
    BD_DADOS_POPULACAO,
    BD_DADOS_RAIS,
    VIEW_CARGA_METODOLOGIA_OFICIAL,
)


MODULE5_CODES = [f"IND-5.{i:02d}" for i in range(1, 22)]


def _generate_query(sql_code: str, params: dict) -> str:
    """Gera SQL para um indicador com parâmetros mínimos de teste."""
    query_fn = get_query(sql_code)
    sig = inspect.signature(query_fn)

    if "id_municipio" in sig.parameters:
        params["id_municipio"] = params.get("id_municipio", "3304557")
    if "ano" in sig.parameters and "ano" not in params:
        params["ano"] = 2023
    elif "ano_inicio" in sig.parameters:
        params["ano_inicio"] = 2020
    if "ano_fim" in sig.parameters and "ano_fim" not in params:
        params["ano_fim"] = 2023

    return query_fn(**params)


def test_module5_e3_queries_are_callable_and_filterable():
    """Valida assinatura + uso de filtros por parâmetro por código de indicador."""
    for code in MODULE5_CODES:
        query_fn = get_query(code)
        signature = inspect.signature(query_fn)
        params = {}
        sql = _generate_query(code, params)

        assert isinstance(sql, str)
        assert sql.strip()

        if "id_municipio" in signature.parameters:
            assert "3304557" in sql

        if "ano" in signature.parameters:
            assert (
                " <= 2023" in sql
                or " = 2023" in sql
                or "BETWEEN 2020 AND 2023" in sql
            ), f"{code} sem filtro de ano aplicado corretamente"

        if "ano_inicio" in signature.parameters and "ano" not in signature.parameters:
            assert "2020" in sql
        if "ano_fim" in signature.parameters and "ano" not in signature.parameters:
            assert "2023" in sql


def test_module5_e3_expected_sources_for_queries():
    """Garante que cada query usa as fontes esperadas para o indicador."""
    expected_sources = {
        "IND-5.01": {BD_DADOS_PIB},
        "IND-5.02": {BD_DADOS_PIB, BD_DADOS_POPULACAO},
        "IND-5.03": {BD_DADOS_POPULACAO},
        "IND-5.04": {BD_DADOS_PIB},
        "IND-5.05": {BD_DADOS_PIB},
        "IND-5.06": {MART_IMPACTO_ECONOMICO_FQTN},
        "IND-5.07": {MART_IMPACTO_ECONOMICO_FQTN},
        "IND-5.08": {BD_DADOS_RAIS},
        "IND-5.09": {BD_DADOS_RAIS},
        "IND-5.10": {BD_DADOS_PIB},
        "IND-5.11": {MART_IMPACTO_ECONOMICO_FQTN},
        "IND-5.12": {BD_DADOS_RAIS},
        "IND-5.13": {
            "basedosdados.br_me_comex_stat.municipio_exportacao",
            "basedosdados.br_me_comex_stat.municipio_importacao",
        },
        "IND-5.14": {MART_IMPACTO_ECONOMICO_FQTN},
        "IND-5.15": {BD_DADOS_RAIS, MART_IMPACTO_ECONOMICO_FQTN},
        "IND-5.16": {
            "basedosdados.br_me_comex_stat.municipio_exportacao",
            "basedosdados.br_me_comex_stat.municipio_importacao",
            BD_DADOS_PIB,
        },
        "IND-5.17": {MART_IMPACTO_ECONOMICO_FQTN},
        "IND-5.18": {BD_DADOS_PIB},
        "IND-5.19": {BD_DADOS_PIB},
        "IND-5.20": {BD_DADOS_RAIS},
        "IND-5.21": {MART_IMPACTO_ECONOMICO_FQTN, BD_DADOS_RAIS, BD_DADOS_PIB},
    }

    for code in MODULE5_CODES:
        sql = _generate_query(code, {})
        for source in expected_sources[code]:
            assert source in sql, f"{code}: fonte esperada ausente: {source}"


def test_module5_e3_no_name_join_for_mart_based_port_indicators():
    """Garante que indicadores acoplados ao mart não fazem join por nome de município."""
    mart_codes = {"IND-5.06", "IND-5.07", "IND-5.11", "IND-5.21", "IND-5.14", "IND-5.15", "IND-5.17"}
    for code in mart_codes:
        sql = get_query(code)(id_municipio="3304557")
        assert "c.municipio = dir.nome" not in sql
        assert "municipio = c.municipio" not in sql
        if code in {"IND-5.06", "IND-5.07", "IND-5.11", "IND-5.21"}:
            assert MART_IMPACTO_ECONOMICO_FQTN in sql
        if code in {"IND-5.06", "IND-5.07", "IND-5.11", "IND-5.21"}:
            assert VIEW_CARGA_METODOLOGIA_OFICIAL not in sql


def test_module5_e3_divisao_usa_protecao_zero_no_divisao():
    """Checa segurança básica de divisão para indicadores de razão em SQL."""
    # Indicadores de razão/crescimento devem proteger o divisor.
    assertive_codes = {
        "IND-5.02",
        "IND-5.04",
        "IND-5.05",
        "IND-5.06",
        "IND-5.07",
        "IND-5.08",
        "IND-5.09",
        "IND-5.10",
        "IND-5.11",
        "IND-5.12",
        "IND-5.13",
        "IND-5.20",
        "IND-5.21",
    }
    for code in assertive_codes:
        sql = get_query(code)(id_municipio="3304557")
        if "NULLIF" in sql and "ROUND(" in sql:
            continue
        # Crescimentos e proporções podem não ter divisão explícita (ex.: correlação/elasticidade com log).
        if code in {"IND-5.14", "IND-5.15", "IND-5.16", "IND-5.17"}:
            continue
        assert "NULLIF(" in sql, f"{code}: divisor deveria usar proteção contra zero"


class _CapturingBigQueryClient:
    """Cliente BigQuery falso para validar query gerada sem depender de conectividade real."""

    def __init__(self):
        self.last_query: str | None = None

    async def execute_query(self, query: str, *_, **__) -> list:
        self.last_query = query
        return []


def _build_request(code: str) -> GenericIndicatorRequest:
    """Cria request mínima para forçar parâmetros configuráveis por código."""
    query_fn = get_query(code)
    signature = inspect.signature(query_fn)
    params = {}

    if "id_municipio" in signature.parameters:
        params["id_municipio"] = "3304557"
    if "ano" in signature.parameters:
        params["ano"] = 2023
    else:
        if "ano_inicio" in signature.parameters:
            params["ano_inicio"] = 2020
        if "ano_fim" in signature.parameters:
            params["ano_fim"] = 2023

    return GenericIndicatorRequest(codigo_indicador=code, **params)


@pytest.mark.asyncio
async def test_module5_e3_execution_contract_applies_filters_and_returns_data():
    """US-030: executa todos os indicadores com cliente mock e valida contrato/filters."""
    for code in MODULE5_CODES:
        client = _CapturingBigQueryClient()
        service = GenericIndicatorService(bq_client=client)

        query_fn = get_query(code)
        signature = inspect.signature(query_fn)
        request = _build_request(code)

        response = await service.execute_indicator(request)

        assert response.codigo_indicador == code
        assert response.data == []
        assert response.warnings == []

        query = client.last_query
        assert query is not None
        assert "SELECT" in query.upper()
        assert "FROM" in query.upper()

        if "id_municipio" in signature.parameters:
            assert "3304557" in query

        if "ano" in signature.parameters:
            assert ("= 2023" in query) or ("<= 2023" in query)
        else:
            if "ano_inicio" in signature.parameters:
                assert "2020" in query
            if "ano_fim" in signature.parameters:
                assert "2023" in query


@pytest.mark.asyncio
async def test_module5_e3_time_series_and_ranking_semantics():
    """US-032: verifica ordenação por série temporal e ranking conforme semântica."""
    structural_codes = (
        "IND-5.01",
        "IND-5.02",
        "IND-5.03",
        "IND-5.04",
        "IND-5.05",
        "IND-5.06",
        "IND-5.07",
        "IND-5.08",
        "IND-5.09",
        "IND-5.10",
        "IND-5.11",
        "IND-5.12",
        "IND-5.13",
        "IND-5.18",
        "IND-5.19",
        "IND-5.20",
        "IND-5.21",
    )

    for code in structural_codes:
        query_by_municipio = get_query(code)(id_municipio="3304557")
        query_ranking = get_query(code)()

        assert re.search(r"ORDER BY\s+[a-zA-Z_][a-zA-Z0-9_]*\.ano", query_by_municipio), (
            f"{code} deve ordenar por ano quando filtrado por id_municipio"
        )
        assert "LIMIT 20" in query_ranking
        # No ranking global, o critério principal não deve ser ano
        assert "ORDER BY" in query_ranking


@pytest.mark.asyncio
async def test_module5_e3_correlational_semantics():
    """US-032: valida formato de retorno esperado para indicadores correlacionais."""
    for code in ("IND-5.14", "IND-5.15", "IND-5.16", "IND-5.17"):
        query_by_municipio = get_query(code)(id_municipio="3304557")
        query_ranking = get_query(code)()

        assert (
            re.search(r"ORDER BY\s+correlacao", query_ranking) is not None
            or re.search(r"ORDER BY\s+elasticidade", query_ranking) is not None
        )
        assert "id_municipio = '3304557'" in query_by_municipio
        assert "HAVING" in query_by_municipio and "COUNT" in query_by_municipio
