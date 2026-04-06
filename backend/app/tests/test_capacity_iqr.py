"""Testes unitários para filtro IQR e indicadores operacionais de capacidade."""
from __future__ import annotations

import pytest

from app.services.capacity.iqr_filter import (
    iqr_bounds,
    iqr_filter_stats,
    iqr_filtered_mean,
)
from app.services.capacity.operational_indicators import compute_group_indicators


# ---------------------------------------------------------------------------
# Filtro IQR
# ---------------------------------------------------------------------------


class TestIqrBounds:
    def test_basic_bounds(self):
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        lb, ub = iqr_bounds(values)
        assert lb < 1
        assert ub > 12

    def test_with_outliers(self):
        values = [2, 3, 3, 4, 4, 4, 5, 5, 6, 100]
        lb, ub = iqr_bounds(values)
        assert 100 > ub  # outlier should be outside bounds

    def test_few_values_returns_min_max(self):
        values = [5.0, 10.0, 15.0]
        lb, ub = iqr_bounds(values)
        assert lb == 5.0
        assert ub == 15.0

    def test_empty_returns_zeros(self):
        lb, ub = iqr_bounds([])
        assert lb == 0.0
        assert ub == 0.0

    def test_identical_values(self):
        values = [5.0, 5.0, 5.0, 5.0, 5.0]
        lb, ub = iqr_bounds(values)
        assert lb == 5.0
        assert ub == 5.0


class TestIqrFilteredMean:
    def test_removes_outliers(self):
        # Normal values 1-10, plus one extreme outlier
        values = list(range(1, 11)) + [1000]
        mean = iqr_filtered_mean(values)
        assert mean is not None
        assert mean < 15  # outlier (1000) should be excluded

    def test_empty_returns_none(self):
        assert iqr_filtered_mean([]) is None

    def test_all_same(self):
        assert iqr_filtered_mean([7.0, 7.0, 7.0, 7.0]) == 7.0

    def test_no_outliers(self):
        values = [10, 11, 12, 13, 14, 15]
        mean = iqr_filtered_mean(values)
        assert mean == pytest.approx(12.5, abs=0.1)


class TestIqrFilterStats:
    def test_returns_all_fields(self):
        stats = iqr_filter_stats([1, 2, 3, 4, 5, 100])
        assert "n_total" in stats
        assert "n_retained" in stats
        assert "n_removed" in stats
        assert "lower_bound" in stats
        assert "upper_bound" in stats
        assert "mean_filtered" in stats

    def test_counts_removed(self):
        stats = iqr_filter_stats([1, 2, 3, 4, 5, 100])
        assert stats["n_total"] == 6
        assert stats["n_removed"] >= 1  # at least the outlier
        assert stats["n_retained"] + stats["n_removed"] == stats["n_total"]

    def test_empty(self):
        stats = iqr_filter_stats([])
        assert stats["n_total"] == 0
        assert stats["mean_filtered"] is None


# ---------------------------------------------------------------------------
# Indicadores operacionais agregados
# ---------------------------------------------------------------------------


def _make_record(
    ano=2023,
    id_instalacao="BRSSZ",
    berco="B01",
    perfil_carga="Granel Sólido",
    sentido="Exportação",
    inop_pre_h=1.0,
    t_op_h=12.0,
    inop_pos_h=0.5,
    ta_h=13.5,
    lm_tons=50000.0,
    produtividade_t_h=4166.67,
):
    return {
        "ano": ano,
        "id_instalacao": id_instalacao,
        "berco": berco,
        "perfil_carga": perfil_carga,
        "sentido": sentido,
        "inop_pre_h": inop_pre_h,
        "t_op_h": t_op_h,
        "inop_pos_h": inop_pos_h,
        "ta_h": ta_h,
        "lm_tons": lm_tons,
        "produtividade_t_h": produtividade_t_h,
    }


class TestComputeGroupIndicators:
    def test_single_group(self):
        records = [_make_record() for _ in range(10)]
        results = compute_group_indicators(records, clearance_h=3.0)
        assert len(results) == 1

        r = results[0]
        assert r["ano"] == 2023
        assert r["id_instalacao"] == "BRSSZ"
        assert r["n_atracacoes"] == 10
        assert r["mean_ta_h"] is not None
        assert r["ta_plus_a"] is not None
        assert r["ta_plus_a"] == pytest.approx(r["mean_ta_h"] + 3.0, abs=0.01)

    def test_multiple_groups(self):
        records = [
            _make_record(berco="B01"),
            _make_record(berco="B01"),
            _make_record(berco="B02"),
        ]
        results = compute_group_indicators(records)
        assert len(results) == 2

    def test_container_mode(self):
        records = [
            {
                "ano": 2023,
                "id_instalacao": "BRSSZ",
                "berco": "B01",
                "perfil_carga": "Carga Conteinerizada",
                "sentido": "Exportação",
                "inop_pre_h": 0.8,
                "t_op_h": 10.0,
                "inop_pos_h": 0.3,
                "ta_h": 11.1,
                "lm_teu": 2500,
                "produtividade_teu_h": 250.0,
            }
            for _ in range(5)
        ]
        results = compute_group_indicators(records, is_container=True)
        assert len(results) == 1
        assert results[0]["is_container"] is True
        assert results[0]["mean_lm"] == pytest.approx(2500, abs=1)

    def test_outlier_removal(self):
        # 9 normal records + 1 outlier
        records = [_make_record(produtividade_t_h=4000) for _ in range(9)]
        records.append(_make_record(produtividade_t_h=99999))
        results = compute_group_indicators(records)
        r = results[0]
        # Média da produtividade deve ser próxima de 4000 (outlier removido)
        assert r["mean_produtividade"] is not None
        assert r["mean_produtividade"] < 10000

    def test_iqr_stats_included(self):
        records = [_make_record() for _ in range(6)]
        results = compute_group_indicators(records)
        r = results[0]
        assert "iqr_inop_pre" in r
        assert "iqr_produtividade" in r
        assert r["iqr_inop_pre"]["n_total"] == 6

    def test_empty_records(self):
        results = compute_group_indicators([])
        assert results == []
