"""Validações de contrato para o Módulo 5 (Impacto Econômico Regional)."""

import inspect
import re
import pytest

import json
from app.db.bigquery.queries import ALL_QUERIES, get_query
from app.services.generic_indicator_service import (
    INDICATORS_METADATA,
    GenericIndicatorService,
)
from app.api.v1.indicators import generic as indicators_api


MODULE5_INDICATORS = [f"IND-5.{i:02d}" for i in range(1, 22)]


def test_module5_metadata_and_queries_are_consistent():
    """Valida que o catálogo do Módulo 5 está completo e alinhado com as queries."""
    missing_metadata = sorted(set(MODULE5_INDICATORS) - set(INDICATORS_METADATA.keys()))
    missing_queries = sorted(set(MODULE5_INDICATORS) - set(ALL_QUERIES.keys()))

    assert not missing_metadata, f"Códigos sem metadados: {missing_metadata}"
    assert not missing_queries, f"Códigos sem query: {missing_queries}"

    for code in MODULE5_INDICATORS:
        query_fn = get_query(code)
        assert callable(query_fn)
        params = {"id_municipio": "3304557"}
        signature = inspect.signature(query_fn)
        if "ano" in signature.parameters:
            params["ano"] = 2023
        if "ano_inicio" in signature.parameters:
            params["ano_inicio"] = 2020
        if "ano_fim" in signature.parameters:
            params["ano_fim"] = 2023

        sql = query_fn(**params)
        assert isinstance(sql, str)
        assert sql.strip(), f"Query vazia para {code}"


def test_module5_indicator_metadata_is_accessible():
    """Valida metadados por indicador via serviço público."""
    service = GenericIndicatorService()

    for code in MODULE5_INDICATORS:
        metadata = service.get_indicator_metadata(code)
        assert metadata.codigo == code
        assert metadata.modulo == 5
        assert metadata.implementation_status in {"implemented", "technical_debt"}
        assert metadata.granularidade
        assert metadata.fonte_dados


def test_module5_correlation_metadata_mentions_no_causality():
    """Valida metadados metodológicos dos indicadores de associação."""
    for code in ("IND-5.14", "IND-5.15", "IND-5.16", "IND-5.17"):
        descricao = INDICATORS_METADATA[code]["descricao"].lower()
        assert re.search(r"corr|elastic", descricao), f"Sem semântica associativa em {code}"
        assert "não implica causalidade" in descricao or "nao implica causalidade" in descricao


def test_module5_metadata_has_interpretation_and_sources():
    """Valida granularidade e fonte por indicador do Módulo 5."""
    required = ("descricao", "granularidade", "fonte_dados")

    for code in MODULE5_INDICATORS:
        meta = INDICATORS_METADATA.get(code, {})
        for field in required:
            assert meta.get(field), f"{code} sem campo obrigatório: {field}"

        fonte = meta["fonte_dados"].lower()
        assert any(token in fonte for token in ("ibge", "rais", "antaq", "comex")), (
            f"{code} sem fonte explícita: {meta['fonte_dados']}"
        )

        descricao = meta["descricao"].lower()
        if code in {"IND-5.14", "IND-5.15", "IND-5.16", "IND-5.17"}:
            assert "associação" in descricao, f"{code} sem limitação metodológica de associação"
            assert "não implica causalidade" in descricao or "nao implica causalidade" in descricao


@pytest.mark.asyncio
async def test_modules_overview_reports_21_indicators_in_module5():
    """Valida o overview geral: Módulo 5 deve expor 21 indicadores."""
    response = await indicators_api.get_modules_overview()
    payload = json.loads(response.body)

    module5 = next(item for item in payload["modulos"] if item["modulo"] == 5)
    assert module5["total_indicadores"] == 21
