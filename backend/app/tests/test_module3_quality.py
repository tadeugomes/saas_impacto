"""Testes de diagnóstico de dados do Módulo 3."""

import pytest

from app.schemas.indicators import GenericIndicatorRequest
from app.services.generic_indicator_service import GenericIndicatorService


class _DummyBigQueryClient:
    """Cliente minimalista para simular consultas de indicador e cobertura."""

    def __init__(self, indicator_rows, coverage_rows):
        self.indicator_rows = list(indicator_rows)
        self.coverage_rows = list(coverage_rows)
        self.calls = []

    async def execute_query(self, query, *_, **__):
        self.calls.append(query)
        if "linhas_ano_solicitado" in query:
            return self.coverage_rows
        return self.indicator_rows

    async def get_dry_run_results(self, query):
        return {"total_bytes_processed": 0}


@pytest.mark.asyncio
async def test_module3_year_without_data_returns_warning():
    """Ano fora da cobertura do município retorna warning de sem_dados_ano."""
    service = GenericIndicatorService(
        bq_client=_DummyBigQueryClient(
            indicator_rows=[],
            coverage_rows=[
                {
                    "ano_min": 2019,
                    "ano_max": 2021,
                    "anos_disponiveis": 3,
                    "linhas_ano_solicitado": 0,
                    "linhas_ano_anterior": 0,
                },
            ],
        )
    )

    response = await service.execute_indicator(
        GenericIndicatorRequest(codigo_indicador="IND-3.10", id_municipio="1234567", ano=2022)
    )

    assert response.data == []
    assert response.warnings
    assert any(
        warning.tipo in {"sem_dados_ano", "ano_apos_cobertura", "ano_antes_cobertura"}
        for warning in response.warnings
    )


@pytest.mark.asyncio
async def test_module3_variation_indicator_with_missing_previous_year_warns_historical_insufficient():
    """Variação anual sem ano anterior retorna warning de histórico insuficiente."""
    service = GenericIndicatorService(
        bq_client=_DummyBigQueryClient(
            indicator_rows=[],
            coverage_rows=[
                {
                    "ano_min": 2021,
                    "ano_max": 2022,
                    "anos_disponiveis": 2,
                    "linhas_ano_solicitado": 100,
                    "linhas_ano_anterior": 0,
                },
            ],
        )
    )

    response = await service.execute_indicator(
        GenericIndicatorRequest(codigo_indicador="IND-3.11", id_municipio="1234567", ano=2022)
    )

    assert response.data == []
    assert any(
        warning.tipo == "historico_insuficiente" and "2021" in warning.mensagem
        for warning in response.warnings
    )
