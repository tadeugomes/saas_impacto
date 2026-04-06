"""Testes unitários para projeção de saturação e tendência de capacidade."""
from __future__ import annotations

import pytest

from app.services.capacity.saturation_projection import (
    compute_capacity_trend,
    identify_bottleneck,
    project_saturation_year,
)


class TestProjectSaturationYear:
    def test_growing_demand_finds_saturation(self):
        """Demanda crescente deve encontrar ano de saturação."""
        historical = [
            {"ano": 2020, "mov_realizada": 100_000},
            {"ano": 2021, "mov_realizada": 120_000},
            {"ano": 2022, "mov_realizada": 140_000},
            {"ano": 2023, "mov_realizada": 160_000},
            {"ano": 2024, "mov_realizada": 180_000},
        ]
        result = project_saturation_year(historical, capacity=300_000)
        assert result["ano_saturacao"] is not None
        assert result["anos_ate_saturacao"] > 0
        assert result["taxa_crescimento_anual"] > 0
        assert len(result["projecao"]) > 0

    def test_stable_demand_no_saturation(self):
        """Demanda estável abaixo da capacidade → sem saturação."""
        historical = [
            {"ano": 2020, "mov_realizada": 50_000},
            {"ano": 2021, "mov_realizada": 50_500},
            {"ano": 2022, "mov_realizada": 49_800},
            {"ano": 2023, "mov_realizada": 50_200},
        ]
        result = project_saturation_year(historical, capacity=1_000_000, max_horizon=2060)
        # Taxa de crescimento é ~0, capacity é muito alta → no saturation in horizon
        assert result["demanda_atual"] < result["capacidade"]

    def test_already_saturated(self):
        """Demanda já acima da capacidade → saturação imediata."""
        historical = [
            {"ano": 2020, "mov_realizada": 500_000},
            {"ano": 2021, "mov_realizada": 600_000},
            {"ano": 2022, "mov_realizada": 700_000},
        ]
        result = project_saturation_year(historical, capacity=300_000)
        assert result["ano_saturacao"] is not None
        assert result["anos_ate_saturacao"] is not None

    def test_empty_historical(self):
        result = project_saturation_year([], capacity=100_000)
        assert result["ano_saturacao"] is None
        assert result["projecao"] == []

    def test_single_year(self):
        result = project_saturation_year(
            [{"ano": 2024, "mov_realizada": 50_000}],
            capacity=100_000,
        )
        assert result["demanda_atual"] == 50_000

    def test_projecao_limited_to_30_years(self):
        historical = [
            {"ano": 2020, "mov_realizada": 100},
            {"ano": 2021, "mov_realizada": 110},
        ]
        result = project_saturation_year(historical, capacity=999_999_999)
        assert len(result["projecao"]) <= 30


class TestComputeCapacityTrend:
    def test_trend_with_variation(self):
        results = [
            {"ano": 2022, "c_cais_bruta": 100_000, "bor_obs_pct": 40, "bur_obs_pct": 50, "bor_adm": 0.50, "saturado": False},
            {"ano": 2023, "c_cais_bruta": 110_000, "bor_obs_pct": 45, "bur_obs_pct": 55, "bor_adm": 0.50, "saturado": False},
        ]
        trend = compute_capacity_trend(results)
        assert len(trend) == 2
        assert trend[0]["variacao_c_cais_pct"] is None  # primeiro ano
        assert trend[1]["variacao_c_cais_pct"] == pytest.approx(10.0, abs=0.1)
        assert trend[1]["variacao_bor_pp"] == pytest.approx(5.0, abs=0.1)

    def test_empty(self):
        assert compute_capacity_trend([]) == []


class TestIdentifyBottleneck:
    def test_cais_only(self):
        result = identify_bottleneck(c_cais=100_000)
        assert result["gargalo"] == "cais"
        assert result["c_sistema"] == 100_000

    def test_armazenagem_bottleneck(self):
        result = identify_bottleneck(c_cais=100_000, c_armazenagem=50_000)
        assert result["gargalo"] == "armazenagem"
        assert result["c_sistema"] == 50_000

    def test_hinterland_bottleneck(self):
        result = identify_bottleneck(c_cais=100_000, c_armazenagem=200_000, c_hinterland=80_000)
        assert result["gargalo"] == "hinterland"
        assert result["c_sistema"] == 80_000

    def test_all_none(self):
        # c_cais=0 but not None
        result = identify_bottleneck(c_cais=0)
        assert result["gargalo"] == "cais"
