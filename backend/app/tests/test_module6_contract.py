"""Validações de contrato para o Módulo 6 (Finanças Públicas)."""
from __future__ import annotations

import inspect
import math
import re

import pytest

from app.db.bigquery.queries import ALL_QUERIES, get_query
from app.schemas.indicators import GenericIndicatorRequest
from app.services.generic_indicator_service import GenericIndicatorService, INDICATORS_METADATA

MODULE6_INDICATORS = [f"IND-6.{i:02d}" for i in range(1, 12)]


class _CapturingBigQueryClient:
    """Cliente BigQuery mínimo para validar SQL gerada sem BigQuery real."""

    def __init__(self):
        self.last_query: str | None = None

    async def execute_query(self, query: str, *_, **__) -> list:
        self.last_query = query
        return []


class _StaticBigQueryClient(_CapturingBigQueryClient):
    """Cliente fake que sempre retorna um conjunto fixo de linhas."""

    def __init__(self, rows: list[dict]):
        super().__init__()
        self.rows = rows

    async def execute_query(self, query: str, *_, **__) -> list:
        self.last_query = query
        return self.rows


@pytest.mark.asyncio
async def test_module6_metadata_and_queries_are_consistent():
    """Valida catálogo e registro de queries para os códigos 6.01–6.11."""
    missing_metadata = sorted(set(MODULE6_INDICATORS) - set(INDICATORS_METADATA.keys()))
    missing_queries = sorted(set(MODULE6_INDICATORS) - set(ALL_QUERIES.keys()))

    assert not missing_metadata, f"Códigos sem metadados: {missing_metadata}"
    assert not missing_queries, f"Códigos sem query: {missing_queries}"

    for code in MODULE6_INDICATORS:
        query_fn = get_query(code)
        signature = inspect.signature(query_fn)

        params = {}
        if "id_municipio" in signature.parameters:
            params["id_municipio"] = "3304557"
        if "ano" in signature.parameters:
            params["ano"] = 2023
        if "ano_inicio" in signature.parameters:
            params["ano_inicio"] = 2020
        if "ano_fim" in signature.parameters:
            params["ano_fim"] = 2023

        sql = query_fn(**params)
        assert isinstance(sql, str)
        assert sql.strip()


@pytest.mark.asyncio
async def test_module6_indicator_metadata_is_accessible_and_interpretable():
    """Valida campos obrigatórios e limitação de causalidade dos indicadores associativos."""
    service = GenericIndicatorService()

    for code in MODULE6_INDICATORS:
        metadata = service.get_indicator_metadata(code)
        assert metadata.codigo == code
        assert metadata.modulo == 6
        assert metadata.granularidade
        assert metadata.fonte_dados
        assert metadata.descricao

    for code in ("IND-6.10", "IND-6.11"):
        descricao = INDICATORS_METADATA[code]["descricao"].lower()
        assert "associação" in descricao, f"Sem semântica associativa em {code}"
        assert (
            "não causalidade" in descricao
            or "nao causalidade" in descricao
            or "sem causalidade" in descricao
        )


@pytest.mark.asyncio
async def test_module6_execution_contract_applies_filters_and_returns_empty_data():
    """Executa consulta de cada código com cliente fake e valida parâmetros mínimos."""
    for code in MODULE6_INDICATORS:
        signature = inspect.signature(get_query(code))

        request_params = {}
        if "id_municipio" in signature.parameters:
            request_params["id_municipio"] = "3304557"
        if "ano" in signature.parameters:
            request_params["ano"] = 2023
        else:
            if "ano_inicio" in signature.parameters:
                request_params["ano_inicio"] = 2020
            if "ano_fim" in signature.parameters:
                request_params["ano_fim"] = 2023

        client = _CapturingBigQueryClient()
        service = GenericIndicatorService(bq_client=client)
        response = await service.execute_indicator(
            GenericIndicatorRequest(codigo_indicador=code, **request_params)
        )

        assert response.codigo_indicador == code
        assert response.data == []

        query = client.last_query
        assert query is not None
        assert "SELECT" in query.upper()
        assert "FROM" in query.upper()

        if "id_municipio" in signature.parameters:
            assert "3304557" in query
        if "ano" in signature.parameters:
            assert "2023" in query


@pytest.mark.asyncio
async def test_module6_quality_warns_correlation_bounds():
    service = GenericIndicatorService(
        bq_client=_StaticBigQueryClient(
            [
                {
                    "id_municipio": "3304557",
                    "nome_municipio": "Vitória",
                    "correlacao": 2.5,
                    "correlacao_tonelagem_receita_fiscal": 2.5,
                }
            ]
        )
    )

    response = await service.execute_indicator(
        GenericIndicatorRequest(codigo_indicador="IND-6.10", id_municipio="3304557")
    )
    assert response.warnings
    assert any(
        w.tipo == "correlacao_fora_intervalo" and w.campo == "correlacao" for w in response.warnings
    )


@pytest.mark.asyncio
async def test_module6_quality_warns_invalid_elasticidade():
    service = GenericIndicatorService(
        bq_client=_StaticBigQueryClient(
            [
                {
                    "id_municipio": "3304557",
                    "nome_municipio": "Vitória",
                    "elasticidade": math.inf,
                    "n_observacoes": 7,
                }
            ]
        )
    )

    response = await service.execute_indicator(
        GenericIndicatorRequest(codigo_indicador="IND-6.11", id_municipio="3304557")
    )
    assert response.warnings
    assert any(
        w.tipo == "elasticidade_invalida" and w.campo == "elasticidade" for w in response.warnings
    )
