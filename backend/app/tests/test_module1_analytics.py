"""
Testes unitários para as features analíticas do Módulo 1.

Cobre:
- Feature 1: Análise de tendência operacional
- Feature 2: Benchmarking contra pares
- Feature 3: Score de eficiência decomposto
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.services.indicator_service import ShipOperationsIndicatorService
from app.schemas.indicators import (
    ClassificacaoTendencia,
    ClassificacaoBenchmark,
    TendenciaOperacionalResponse,
    BenchmarkingResponse,
    ScoreEficienciaResponse,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def service():
    svc = ShipOperationsIndicatorService.__new__(ShipOperationsIndicatorService)
    svc.bq_client = AsyncMock()
    return svc


# ---------------------------------------------------------------------------
# Feature 1: Tendência Operacional
# ---------------------------------------------------------------------------

class TestTendenciaOperacional:
    """Testes da análise de tendência."""

    @pytest.mark.asyncio
    async def test_tendencia_improving(self, service):
        """Queda em tempo de espera → IMPROVING."""
        service.bq_client.execute_query = AsyncMock(return_value=[
            {
                "id_instalacao": "Porto de Santos",
                "ano": 2023,
                "valor_101": 20.0, "prev_101": 30.0, "yoy_101": -33.33, "class_101": "IMPROVING",
                "valor_102": 50.0, "prev_102": 55.0, "yoy_102": -9.09, "class_102": "IMPROVING",
                "valor_103": 40.0, "prev_103": 42.0, "yoy_103": -4.76, "class_103": "STABLE",
                "valor_104": 30.0, "prev_104": 31.0, "yoy_104": -3.23, "class_104": "STABLE",
                "valor_106": 5.0, "prev_106": 8.0, "yoy_106": -37.5, "class_106": "IMPROVING",
                "valor_111": 5000, "prev_111": 4800, "yoy_111": 4.17, "class_111": "STABLE",
                "valor_112": 12.0, "prev_112": 15.0, "yoy_112": -20.0, "class_112": "IMPROVING",
                "cagr3_101": -10.5, "cagr3_103": -2.0, "cagr3_111": 3.5,
            }
        ])

        results = await service.get_tendencia_operacional(id_instalacao="Porto de Santos")
        assert len(results) == 1
        resp = results[0]
        assert isinstance(resp, TendenciaOperacionalResponse)
        assert resp.id_instalacao == "Porto de Santos"
        assert resp.ano == 2023
        assert len(resp.indicadores) == 7

        # IND-1.01: espera caiu 33% → IMPROVING
        ind_101 = resp.indicadores[0]
        assert ind_101.indicador_codigo == "IND-1.01"
        assert ind_101.classificacao == ClassificacaoTendencia.IMPROVING
        assert ind_101.variacao_yoy_pct == -33.33
        assert ind_101.polaridade_inversa is True

    @pytest.mark.asyncio
    async def test_tendencia_deteriorating(self, service):
        """Aumento em tempo de espera → DETERIORATING."""
        service.bq_client.execute_query = AsyncMock(return_value=[
            {
                "id_instalacao": "Porto X",
                "ano": 2023,
                "valor_101": 40.0, "prev_101": 20.0, "yoy_101": 100.0, "class_101": "DETERIORATING",
                "valor_102": 80.0, "prev_102": 55.0, "yoy_102": 45.45, "class_102": "DETERIORATING",
                "valor_103": 60.0, "prev_103": 42.0, "yoy_103": 42.86, "class_103": "DETERIORATING",
                "valor_104": 45.0, "prev_104": 31.0, "yoy_104": 45.16, "class_104": "DETERIORATING",
                "valor_106": 12.0, "prev_106": 8.0, "yoy_106": 50.0, "class_106": "DETERIORATING",
                "valor_111": 3000, "prev_111": 4800, "yoy_111": -37.5, "class_111": "DETERIORATING",
                "valor_112": 25.0, "prev_112": 15.0, "yoy_112": 66.67, "class_112": "DETERIORATING",
                "cagr3_101": None, "cagr3_103": None, "cagr3_111": None,
            }
        ])

        results = await service.get_tendencia_operacional(id_instalacao="Porto X")
        assert len(results) == 1
        ind_101 = results[0].indicadores[0]
        assert ind_101.classificacao == ClassificacaoTendencia.DETERIORATING

        # IND-1.11 (atracações): queda = DETERIORATING (polaridade direta)
        ind_111 = results[0].indicadores[5]
        assert ind_111.classificacao == ClassificacaoTendencia.DETERIORATING
        assert ind_111.polaridade_inversa is False

    @pytest.mark.asyncio
    async def test_tendencia_sem_dados(self, service):
        """Sem resultados → lista vazia."""
        service.bq_client.execute_query = AsyncMock(return_value=[])
        results = await service.get_tendencia_operacional(id_instalacao="Inexistente")
        assert results == []

    @pytest.mark.asyncio
    async def test_tendencia_cagr(self, service):
        """CAGR 3 anos presente quando há dados suficientes."""
        service.bq_client.execute_query = AsyncMock(return_value=[
            {
                "id_instalacao": "Porto Santos",
                "ano": 2023,
                "valor_101": 20.0, "prev_101": 25.0, "yoy_101": -20.0, "class_101": "IMPROVING",
                "valor_102": 50.0, "prev_102": 55.0, "yoy_102": -9.09, "class_102": "IMPROVING",
                "valor_103": 35.0, "prev_103": 40.0, "yoy_103": -12.5, "class_103": "IMPROVING",
                "valor_104": 28.0, "prev_104": 30.0, "yoy_104": -6.67, "class_104": "IMPROVING",
                "valor_106": 5.0, "prev_106": 7.0, "yoy_106": -28.57, "class_106": "IMPROVING",
                "valor_111": 6000, "prev_111": 5500, "yoy_111": 9.09, "class_111": "IMPROVING",
                "valor_112": 10.0, "prev_112": 14.0, "yoy_112": -28.57, "class_112": "IMPROVING",
                "cagr3_101": -8.5, "cagr3_103": -5.2, "cagr3_111": 6.1,
            }
        ])

        results = await service.get_tendencia_operacional(id_instalacao="Porto Santos")
        ind_101 = results[0].indicadores[0]
        assert ind_101.cagr_3y_pct == -8.5


# ---------------------------------------------------------------------------
# Feature 2: Benchmarking
# ---------------------------------------------------------------------------

class TestBenchmarking:
    """Testes do benchmarking contra pares."""

    @pytest.mark.asyncio
    async def test_benchmarking_acima_media(self, service):
        """Porto com tempos baixos → ACIMA_MEDIA em tempos."""
        service.bq_client.execute_query = AsyncMock(return_value=[
            {
                "id_instalacao": "Porto Eficiente",
                "ind_101": 10.0, "prank_101": 15.0, "med_101": 25.0, "p75_101": 35.0,
                "ind_102": None, "prank_102": None,
                "ind_103": 20.0, "prank_103": 20.0, "med_103": 40.0, "p75_103": 55.0,
                "ind_104": 15.0, "prank_104": 10.0, "med_104": 30.0, "p75_104": 45.0,
                "ind_106": 3.0, "prank_106": 5.0, "med_106": 8.0, "p75_106": 12.0,
                "ind_111": 8000, "prank_111": 90.0, "med_111": 3000, "p75_111": 5000,
                "ind_112": 5.0, "prank_112": 10.0, "med_112": 15.0, "p75_112": 22.0,
                "total_portos": 50,
            }
        ])

        result = await service.get_benchmarking(id_instalacao="Porto Eficiente", ano=2023)
        assert isinstance(result, BenchmarkingResponse)
        assert result.total_portos == 50

        # IND-1.01: prank 15 → ACIMA_MEDIA (tempo baixo = bom)
        ind_101 = result.indicadores[0]
        assert ind_101.percentil_rank == 15.0
        assert ind_101.classificacao == ClassificacaoBenchmark.ACIMA_MEDIA
        assert ind_101.mediana_nacional == 25.0

        # IND-1.11: prank 90 → ACIMA_MEDIA (muitas atracações = bom)
        ind_111 = result.indicadores[4]
        assert ind_111.classificacao == ClassificacaoBenchmark.ACIMA_MEDIA

    @pytest.mark.asyncio
    async def test_benchmarking_abaixo_media(self, service):
        """Porto com tempos altos → ABAIXO_MEDIA."""
        service.bq_client.execute_query = AsyncMock(return_value=[
            {
                "id_instalacao": "Porto Lento",
                "ind_101": 60.0, "prank_101": 85.0, "med_101": 25.0, "p75_101": 35.0,
                "ind_103": 80.0, "prank_103": 90.0, "med_103": 40.0, "p75_103": 55.0,
                "ind_104": 60.0, "prank_104": 80.0, "med_104": 30.0, "p75_104": 45.0,
                "ind_106": 20.0, "prank_106": 88.0, "med_106": 8.0, "p75_106": 12.0,
                "ind_111": 500, "prank_111": 10.0, "med_111": 3000, "p75_111": 5000,
                "ind_112": 30.0, "prank_112": 92.0, "med_112": 15.0, "p75_112": 22.0,
                "total_portos": 50,
            }
        ])

        result = await service.get_benchmarking(id_instalacao="Porto Lento", ano=2023)
        # IND-1.01: prank 85 → ABAIXO_MEDIA (muito tempo de espera)
        assert result.indicadores[0].classificacao == ClassificacaoBenchmark.ABAIXO_MEDIA
        # IND-1.11: prank 10 → ABAIXO_MEDIA (poucas atracações)
        assert result.indicadores[4].classificacao == ClassificacaoBenchmark.ABAIXO_MEDIA

    @pytest.mark.asyncio
    async def test_benchmarking_not_found(self, service):
        """Porto não encontrado → None."""
        service.bq_client.execute_query = AsyncMock(return_value=[])
        result = await service.get_benchmarking(id_instalacao="Inexistente", ano=2023)
        assert result is None


# ---------------------------------------------------------------------------
# Feature 3: Score de Eficiência
# ---------------------------------------------------------------------------

class TestScoreEficiencia:
    """Testes do score de eficiência decomposto."""

    @pytest.mark.asyncio
    async def test_score_completo(self, service):
        """Score com decomposição correta por componente."""
        service.bq_client.execute_query = AsyncMock(return_value=[
            {
                "id_instalacao": "Porto Top",
                "ind_101": 10.0, "norm_101": 90.0,
                "ind_103": 20.0, "norm_103": 85.0,
                "ind_104": 15.0, "norm_104": 80.0,
                "ind_106": 3.0, "norm_106": 95.0,
                "ind_111": 8000, "norm_111": 88.0,
                "ind_112": 5.0, "norm_112": 92.0,
                "score_total": 88.9,
                "ranking_posicao": 1,
                "total_portos": 40,
            },
            {
                "id_instalacao": "Porto Medio",
                "ind_101": 30.0, "norm_101": 50.0,
                "ind_103": 40.0, "norm_103": 50.0,
                "ind_104": 30.0, "norm_104": 50.0,
                "ind_106": 8.0, "norm_106": 50.0,
                "ind_111": 3000, "norm_111": 50.0,
                "ind_112": 15.0, "norm_112": 50.0,
                "score_total": 50.0,
                "ranking_posicao": 20,
                "total_portos": 40,
            },
        ])

        results = await service.get_score_eficiencia(ano=2023)
        assert len(results) == 2

        top = results[0]
        assert isinstance(top, ScoreEficienciaResponse)
        assert top.id_instalacao == "Porto Top"
        assert top.score_total == 88.9
        assert top.ranking_posicao == 1
        assert top.total_portos == 40
        assert len(top.componentes) == 6

        # Verificar decomposição: IND-1.01 peso 0.20, norm 90 → contribuição 18.0
        comp_101 = top.componentes[0]
        assert comp_101.indicador_codigo == "IND-1.01"
        assert comp_101.peso == 0.20
        assert comp_101.valor_normalizado == 90.0
        assert comp_101.contribuicao == 18.0  # 90 * 0.20

        # Nota metodológica presente
        assert "min-max" in top.nota_metodologica
        assert "IND-7.01" in top.nota_metodologica

    @pytest.mark.asyncio
    async def test_score_single_port(self, service):
        """Score para um único porto."""
        service.bq_client.execute_query = AsyncMock(return_value=[
            {
                "id_instalacao": "Porto X",
                "ind_101": 25.0, "norm_101": 60.0,
                "ind_103": 35.0, "norm_103": 55.0,
                "ind_104": 25.0, "norm_104": 65.0,
                "ind_106": 6.0, "norm_106": 70.0,
                "ind_111": 4000, "norm_111": 45.0,
                "ind_112": 12.0, "norm_112": 58.0,
                "score_total": 60.45,
                "ranking_posicao": 12,
                "total_portos": 40,
            },
        ])

        results = await service.get_score_eficiencia(ano=2023, id_instalacao="Porto X")
        assert len(results) == 1
        assert results[0].ranking_posicao == 12

    @pytest.mark.asyncio
    async def test_score_sem_dados(self, service):
        """Sem dados → lista vazia."""
        service.bq_client.execute_query = AsyncMock(return_value=[])
        results = await service.get_score_eficiencia(ano=2023)
        assert results == []


# ---------------------------------------------------------------------------
# Testes de integração SQL (verificam que as queries geram SQL válido)
# ---------------------------------------------------------------------------

class TestQueryGeneration:
    """Verifica que as funções de query geram SQL sem erros."""

    def test_tendencia_query_com_instalacao(self):
        from app.db.bigquery.queries.module1_ship_operations import query_tendencia_operacional
        sql = query_tendencia_operacional(id_instalacao="Porto de Santos", ano_inicio=2019, ano_fim=2023)
        assert "Porto de Santos" in sql
        assert "LAG" in sql
        assert "BETWEEN 2019 AND 2023" in sql

    def test_tendencia_query_sem_filtro(self):
        from app.db.bigquery.queries.module1_ship_operations import query_tendencia_operacional
        sql = query_tendencia_operacional(ano_fim=2023)
        assert "BETWEEN 2018 AND 2023" in sql  # default: ano_fim - 5

    def test_benchmarking_query(self):
        from app.db.bigquery.queries.module1_ship_operations import query_benchmarking_operacional
        sql = query_benchmarking_operacional(id_instalacao="Porto de Santos", ano=2023)
        assert "Porto de Santos" in sql
        assert "PERCENT_RANK" in sql
        assert "PERCENTILE_CONT" in sql
        assert "2023" in sql

    def test_score_query_com_instalacao(self):
        from app.db.bigquery.queries.module1_ship_operations import query_score_eficiencia_decomposto
        sql = query_score_eficiencia_decomposto(id_instalacao="Porto de Santos", ano=2023)
        assert "Porto de Santos" in sql
        assert "0.20" in sql  # peso espera
        assert "0.15" in sql  # peso outros

    def test_score_query_ranking_geral(self):
        from app.db.bigquery.queries.module1_ship_operations import query_score_eficiencia_decomposto
        sql = query_score_eficiencia_decomposto(ano=2023)
        assert "porto_atracacao" not in sql or "AND porto_atracacao" not in sql
        assert "ROW_NUMBER" in sql
