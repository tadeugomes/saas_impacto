"""Testes de qualidade de dados (US-031) para o Módulo 5."""

import math
import pytest

from app.schemas.indicators import GenericIndicatorRequest
from app.services.generic_indicator_service import GenericIndicatorService


class _DummyBigQueryClient:
    """Client mínimo para retornar resultados controlados nos testes."""

    def __init__(self, rows):
        self.rows = rows
        self.last_query = None

    async def execute_query(self, query, *_, **__):
        self.last_query = query
        return self.rows


@pytest.mark.asyncio
async def test_module5_quality_warns_when_correlation_exceeds_bounds():
    """Correlação fora do intervalo [-1,1] gera warning e mantém HTTP 200."""
    service = GenericIndicatorService(
        bq_client=_DummyBigQueryClient([
            {
                "id_municipio": "3550308",
                "nome_municipio": "São Paulo",
                "correlacao": 1.23,
                "correlacao_tonelagem_pib": 1.23,
                "n_observacoes": 10,
            },
        ])
    )

    response = await service.execute_indicator(
        GenericIndicatorRequest(codigo_indicador="IND-5.14", id_municipio="3550308")
    )

    assert response.warnings, "Correlação inválida deveria gerar warning"
    assert any(
        w.tipo == "correlacao_fora_intervalo" and w.campo == "correlacao"
        for w in response.warnings
    )


@pytest.mark.asyncio
async def test_module5_quality_warns_when_elasticidade_is_invalid():
    """Elasticidade inválida (NaN/Inf) gera warning e não quebra a consulta."""
    service = GenericIndicatorService(
        bq_client=_DummyBigQueryClient([
            {
                "id_municipio": "3550308",
                "nome_municipio": "São Paulo",
                "elasticidade": math.inf,
                "n_observacoes": 6,
            },
        ])
    )

    response = await service.execute_indicator(
        GenericIndicatorRequest(codigo_indicador="IND-5.17", id_municipio="3550308")
    )

    assert response.warnings
    assert any(
        w.tipo == "elasticidade_invalida" and w.campo == "elasticidade"
        for w in response.warnings
    )


@pytest.mark.asyncio
async def test_module5_quality_warns_percentual_out_of_range():
    """Participações/pct fora do intervalo 0..100 geram warning."""
    service = GenericIndicatorService(
        bq_client=_DummyBigQueryClient([
            {
                "id_municipio": "3550308",
                "nome_municipio": "São Paulo",
                "pib_servicos_percentual": 123.4,
                "ano": 2023,
            },
        ])
    )

    response = await service.execute_indicator(
        GenericIndicatorRequest(codigo_indicador="IND-5.04", id_municipio="3550308")
    )

    assert response.warnings
    assert any(
        w.tipo == "percentual_fora_intervalo" and w.campo == "pib_servicos_percentual"
        for w in response.warnings
    )


@pytest.mark.asyncio
async def test_module5_quality_warns_negative_population():
    """PIB/população/totais com negativo geram warning em vez de falha."""
    service = GenericIndicatorService(
        bq_client=_DummyBigQueryClient([
            {
                "id_municipio": "3304557",
                "nome_municipio": "Vitória",
                "populacao": -100,
                "ano": 2022,
            },
        ])
    )

    response = await service.execute_indicator(
        GenericIndicatorRequest(codigo_indicador="IND-5.03", id_municipio="3304557")
    )

    assert response.warnings
    assert any(
        w.tipo == "valor_negativo" and w.campo == "populacao" for w in response.warnings
    )


@pytest.mark.asyncio
async def test_module5_quality_returns_empty_warnings_for_valid_data():
    """Resultados válidos não devem retornar warnings."""
    service = GenericIndicatorService(
        bq_client=_DummyBigQueryClient([
            {
                "id_municipio": "3304557",
                "nome_municipio": "Vitória",
                "pib_municipal": 12000000,
                "ano": 2022,
            },
        ])
    )

    response = await service.execute_indicator(
        GenericIndicatorRequest(codigo_indicador="IND-5.01", id_municipio="3304557")
    )

    assert response.warnings == []
