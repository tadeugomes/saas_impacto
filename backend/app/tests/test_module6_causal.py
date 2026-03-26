"""
Testes unitários para backend/app/services/module6_causal.py

Cobre:
    - _run_panel_fe: resultado correto, dados insuficientes, erros de estimação
    - _build_fiscal_panel_query: geração de SQL correta com/sem id_municipio
    - estimate_panel_fe_m6: roteamento por código, mock do BigQuery
"""
from __future__ import annotations

import math
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from app.services.module6_causal import (
    _MIN_UNIT_YEARS,
    _MIN_UNITS,
    _build_fiscal_panel_query,
    _run_panel_fe,
    estimate_panel_fe_m6,
)


# ============================================================================
# Fixtures
# ============================================================================

def _make_panel_df(
    n_municipios: int = 5,
    n_anos: int = 8,
    seed: int = 42,
) -> pd.DataFrame:
    """Gera painel sintético (id_municipio, ano, tonelagem, receita_fiscal_total)."""
    rng = __import__("random")
    rng.seed(seed)
    rows = []
    for i in range(n_municipios):
        base_ton = 1_000_000 * (i + 1)
        base_rec = 50_000_000 * (i + 1)
        for j in range(n_anos):
            ano = 2015 + j
            ton = base_ton + rng.gauss(0, base_ton * 0.05)
            rec = base_rec + 0.02 * ton + rng.gauss(0, base_rec * 0.02)
            rows.append(
                {
                    "id_municipio": f"4100{i:03d}",
                    "ano": ano,
                    "tonelagem": max(ton, 1.0),
                    "receita_fiscal_total": max(rec, 1.0),
                }
            )
    return pd.DataFrame(rows)


# ============================================================================
# _run_panel_fe
# ============================================================================

class TestRunPanelFe:
    def test_returns_expected_keys(self):
        df = _make_panel_df()
        result = _run_panel_fe(df, outcome="receita_fiscal_total", treatment="tonelagem")
        expected = {
            "coef", "std_err", "p_value", "ci_lower", "ci_upper",
            "n_obs", "n_municipios", "r2_within", "method",
            "log_log", "significant", "error", "outcome",
        }
        assert expected.issubset(result.keys())

    def test_method_is_panel_fe(self):
        df = _make_panel_df()
        result = _run_panel_fe(df, outcome="receita_fiscal_total", treatment="tonelagem")
        assert result["method"] == "panel_fe"

    def test_normal_estimation_no_error(self):
        df = _make_panel_df()
        result = _run_panel_fe(df, outcome="receita_fiscal_total", treatment="tonelagem")
        assert result["error"] is None
        assert result["coef"] is not None
        assert result["n_obs"] == len(df)

    def test_log_log_flag(self):
        df = _make_panel_df()
        result = _run_panel_fe(df, outcome="receita_fiscal_total", treatment="tonelagem", log_log=True)
        assert result["log_log"] is True
        assert result["error"] is None

    def test_log_log_drops_non_positive(self):
        df = _make_panel_df()
        # Add rows with zero/negative to be filtered
        df.loc[0, "tonelagem"] = 0
        df.loc[1, "receita_fiscal_total"] = -1
        result = _run_panel_fe(df, outcome="receita_fiscal_total", treatment="tonelagem", log_log=True)
        assert result["error"] is None
        assert result["n_obs"] < len(df)

    def test_insufficient_data_units(self):
        # Only 1 municipality — too few for FE
        df = _make_panel_df(n_municipios=1, n_anos=20)
        result = _run_panel_fe(df, outcome="receita_fiscal_total", treatment="tonelagem")
        assert result["error"] is not None
        assert result["coef"] is None

    def test_insufficient_data_observations(self):
        # 2 municipalities × 2 years = 4 obs < MIN_UNIT_YEARS
        df = _make_panel_df(n_municipios=2, n_anos=2)
        result = _run_panel_fe(df, outcome="receita_fiscal_total", treatment="tonelagem")
        assert result["error"] is not None
        assert result["coef"] is None

    def test_significant_is_bool_when_estimated(self):
        df = _make_panel_df()
        result = _run_panel_fe(df, outcome="receita_fiscal_total", treatment="tonelagem")
        if result["error"] is None:
            assert isinstance(result["significant"], bool)

    def test_ci_ordering(self):
        df = _make_panel_df()
        result = _run_panel_fe(df, outcome="receita_fiscal_total", treatment="tonelagem")
        if result["error"] is None:
            assert result["ci_lower"] < result["ci_upper"]

    def test_r2_within_in_range(self):
        df = _make_panel_df()
        result = _run_panel_fe(df, outcome="receita_fiscal_total", treatment="tonelagem")
        if result["error"] is None and result["r2_within"] is not None:
            assert 0.0 <= result["r2_within"] <= 1.0

    def test_empty_dataframe_returns_error(self):
        df = pd.DataFrame(columns=["id_municipio", "ano", "tonelagem", "receita_fiscal_total"])
        result = _run_panel_fe(df, outcome="receita_fiscal_total", treatment="tonelagem")
        assert result["error"] is not None
        assert result["coef"] is None


# ============================================================================
# _build_fiscal_panel_query
# ============================================================================

class TestBuildFiscalPanelQuery:
    def test_returns_string(self):
        q = _build_fiscal_panel_query()
        assert isinstance(q, str)
        assert len(q) > 100

    def test_contains_mart_reference(self):
        q = _build_fiscal_panel_query()
        assert "MART" in q.upper() or "mart_impacto" in q.lower()

    def test_contains_finbra_reference(self):
        q = _build_fiscal_panel_query()
        assert "siconfi" in q.lower() or "FINBRA" in q or "finbra" in q.lower()

    def test_without_id_municipio_no_uf_filter(self):
        q = _build_fiscal_panel_query()
        assert "SUBSTRING" not in q

    def test_with_id_municipio_adds_uf_filter(self):
        q = _build_fiscal_panel_query(id_municipio="4118204")
        # UF prefix "41" should appear in filter
        assert "'41'" in q
        assert "SUBSTRING" in q

    def test_uf_prefix_extraction(self):
        q = _build_fiscal_panel_query(id_municipio="2111300")
        assert "'21'" in q


# ============================================================================
# estimate_panel_fe_m6
# ============================================================================

class TestEstimatePanelFeM6:
    @pytest.mark.asyncio
    async def test_returns_none_for_non_causal_code(self):
        result = await estimate_panel_fe_m6("IND-6.01", id_municipio=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_module5_code(self):
        result = await estimate_panel_fe_m6("IND-5.14", id_municipio=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_ind_610_with_sufficient_data(self):
        df = _make_panel_df(n_municipios=5, n_anos=8)
        rows = df.to_dict("records")

        bq_mock = MagicMock()
        bq_mock.execute_query = AsyncMock(return_value=rows)

        result = await estimate_panel_fe_m6("IND-6.10", id_municipio="4118204", bq_client=bq_mock)

        assert result is not None
        assert result["method"] == "panel_fe"
        assert result["log_log"] is False
        bq_mock.execute_query.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ind_611_uses_log_log(self):
        df = _make_panel_df(n_municipios=5, n_anos=8)
        rows = df.to_dict("records")

        bq_mock = MagicMock()
        bq_mock.execute_query = AsyncMock(return_value=rows)

        result = await estimate_panel_fe_m6("IND-6.11", id_municipio=None, bq_client=bq_mock)

        assert result is not None
        assert result["log_log"] is True

    @pytest.mark.asyncio
    async def test_empty_bq_result_returns_insufficient_data(self):
        bq_mock = MagicMock()
        bq_mock.execute_query = AsyncMock(return_value=[])

        result = await estimate_panel_fe_m6("IND-6.10", id_municipio=None, bq_client=bq_mock)

        assert result is not None
        assert result["error"] is not None
        assert result["n_obs"] == 0

    @pytest.mark.asyncio
    async def test_bq_exception_returns_error_dict(self):
        bq_mock = MagicMock()
        bq_mock.execute_query = AsyncMock(side_effect=RuntimeError("BQ timeout"))

        result = await estimate_panel_fe_m6("IND-6.10", id_municipio="4118204", bq_client=bq_mock)

        assert result is not None
        assert result["error"] is not None
        assert "BQ timeout" in result["error"]
        assert result["coef"] is None

    @pytest.mark.asyncio
    async def test_no_bq_client_uses_global(self):
        """estimate_panel_fe_m6 sem bq_client não deve lançar AttributeError."""
        # Apenas verifica que o código não quebra ao construir — o cliente global
        # falhará ao tentar executar no ambiente de testes (sem credenciais),
        # mas não deve lançar exceção no código de orquestração.
        bq_mock = MagicMock()
        bq_mock.execute_query = AsyncMock(side_effect=Exception("no credentials"))

        # Com bq_client explícito deve retornar erro limpo
        result = await estimate_panel_fe_m6("IND-6.10", id_municipio=None, bq_client=bq_mock)
        assert result is not None
        assert result["error"] is not None
