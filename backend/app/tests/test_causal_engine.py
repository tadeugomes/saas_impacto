"""Testes unitários do engine causal — PR-02.

Não requerem BigQuery nem banco de dados: toda a lógica é testada
com painéis sintéticos gerados em memória.

Critérios de aceite do PR-02:
  ✅ DiD retorna chaves esperadas e não explode em painel sintético
  ✅ test_parallel_trends funciona com cluster por id_municipio
  ✅ run_iv_2sls retorna coef / SE / pvalue
  ✅ run_panel_iv retorna main_result + first_stage
  ✅ serialize_causal_result: nenhum DataFrame cru na saída
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
import pytest

# ─── imports do engine ────────────────────────────────────────────────────────
from app.services.impacto_economico.causal.prep import (
    add_uf_from_municipio,
    build_did_panel,
    aggregate_panel_by_uf_year,
)
from app.services.impacto_economico.causal.did import (
    run_did,
    test_parallel_trends as check_parallel_trends,  # alias: evita coleta acidental pelo pytest
    run_event_study,
    run_did_with_diagnostics,
)
from app.services.impacto_economico.causal.iv import (
    run_iv_2sls,
    first_stage_diagnostics,
    run_iv_with_diagnostics,
)
from app.services.impacto_economico.causal.iv_panel import (
    run_panel_iv,
    run_panel_iv_with_diagnostics,
)
from app.services.impacto_economico.causal.comparison import compare_method_results
from app.services.impacto_economico.causal.serialize import (
    serialize_causal_result,
    dataframe_to_records,
    sanitize_scalars,
)


# ─── Fixtures sintéticas ──────────────────────────────────────────────────────

TREATED_IDS = ["3304557", "3550308"]   # Rio de Janeiro, São Paulo (fictício)
CONTROL_IDS = ["3106200", "2927408", "1501402", "4314902", "5103403"]
ALL_IDS = TREATED_IDS + CONTROL_IDS
YEARS = list(range(2010, 2022))
TREATMENT_YEAR = 2015
POST_YEAR = TREATMENT_YEAR


def _make_synthetic_panel(
    rng: np.random.Generator,
    treatment_effect: float = 0.15,
) -> pd.DataFrame:
    """Cria painel municipal sintético com efeito de tratamento conhecido."""
    rows = []
    for mun in ALL_IDS:
        is_treated = mun in TREATED_IDS
        for year in YEARS:
            post = year >= POST_YEAR
            # outcome = tendência + FE_municipio + FE_ano + ATT + ruído
            pib = (
                10.0
                + 0.05 * (year - 2010)
                + (0.5 if is_treated else 0.0)
                + (treatment_effect if (is_treated and post) else 0.0)
                + rng.normal(0, 0.05)
            )
            rows.append(
                {
                    "id_municipio": mun,
                    "ano": year,
                    "pib_log": pib,
                    "toneladas_log": pib * 0.8 + rng.normal(0, 0.1),
                    "empregos_log": pib * 0.6 + rng.normal(0, 0.08),
                    "ipca": rng.uniform(3.0, 8.0),
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture(scope="module")
def synthetic_panel() -> pd.DataFrame:
    rng = np.random.default_rng(seed=42)
    raw = _make_synthetic_panel(rng)
    panel = build_did_panel(raw, treated_ids=TREATED_IDS, post_year=POST_YEAR, scope="all")
    return panel


@pytest.fixture(scope="module")
def synthetic_iv_df() -> pd.DataFrame:
    """Painel simples para testes de IV."""
    rng = np.random.default_rng(seed=7)
    n = 200
    z = rng.normal(0, 1, n)           # instrumento
    x = 0.8 * z + rng.normal(0, 0.5, n)  # endógena (correlacionada com z)
    y = 1.5 * x + rng.normal(0, 0.3, n)  # outcome
    return pd.DataFrame({"outcome": y, "endog": x, "instrument": z})


# ─── prep ─────────────────────────────────────────────────────────────────────


class TestPrep:
    def test_add_uf_adds_column(self):
        df = pd.DataFrame({"id_municipio": ["3304557", "2927408", "1501402"]})
        out = add_uf_from_municipio(df)
        assert "uf" in out.columns
        assert list(out["uf"]) == ["RJ", "BA", "PA"]

    def test_build_did_panel_columns(self):
        rng = np.random.default_rng(0)
        raw = _make_synthetic_panel(rng)
        panel = build_did_panel(raw, treated_ids=TREATED_IDS, post_year=POST_YEAR, scope="all")
        assert {"treated", "post", "did", "uf"}.issubset(panel.columns)
        assert panel["treated"].isin([0, 1]).all()
        assert panel["did"].isin([0, 1]).all()

    def test_scope_state_filters_to_treated_ufs(self):
        rng = np.random.default_rng(1)
        raw = _make_synthetic_panel(rng)
        panel = build_did_panel(raw, treated_ids=TREATED_IDS, post_year=POST_YEAR, scope="state")
        treated_ufs = panel.loc[panel["treated"] == 1, "uf"].unique()
        remaining_ufs = panel["uf"].unique()
        assert all(uf in remaining_ufs for uf in treated_ufs)

    def test_aggregate_panel_by_uf_year(self):
        rng = np.random.default_rng(2)
        raw = _make_synthetic_panel(rng)
        raw["n_vinculos"] = rng.integers(100, 5000, len(raw))
        raw["receitas_total"] = rng.uniform(1e6, 1e9, len(raw))
        raw["despesas_total"] = rng.uniform(1e6, 1e9, len(raw))
        raw["pib"] = rng.uniform(1e8, 1e12, len(raw))
        raw["remuneracao_media"] = rng.uniform(1500, 8000, len(raw))
        raw["ipca_media"] = rng.uniform(3, 10, len(raw))
        raw = add_uf_from_municipio(raw)
        agg = aggregate_panel_by_uf_year(raw)
        assert "n_vinculos_log" in agg.columns
        assert agg["uf"].nunique() > 0


# ─── did ──────────────────────────────────────────────────────────────────────


class TestDiD:
    def test_run_did_keys(self, synthetic_panel):
        result = run_did(
            df=synthetic_panel,
            outcome="pib_log",
            unit_col="id_municipio",
            time_col="ano",
            treat_col="treated",
            post_col="post",
            cluster_col="id_municipio",
        )
        expected = {"outcome", "coef", "std_err", "p_value", "n_obs", "r2", "formula"}
        assert expected.issubset(result.keys())

    def test_run_did_coef_finite(self, synthetic_panel):
        result = run_did(
            df=synthetic_panel,
            outcome="pib_log",
            cluster_col="id_municipio",
        )
        assert math.isfinite(result["coef"])
        assert 0 <= result["r2"] <= 1
        assert result["n_obs"] > 0

    def test_run_did_detects_treatment_effect(self, synthetic_panel):
        """DiD deve recuperar efeito ≈ 0.15 com 12 anos × 7 municípios."""
        result = run_did(df=synthetic_panel, outcome="pib_log", cluster_col="id_municipio")
        # tolerância ampla por causa do tamanho de amostra
        assert abs(result["coef"] - 0.15) < 0.20

    def test_parallel_trends_cluster_by_municipio(self, synthetic_panel):
        result = check_parallel_trends(
            df=synthetic_panel,
            outcome="pib_log",
            treatment_year=TREATMENT_YEAR,
            cluster_col="id_municipio",
        )
        expected_keys = {
            "f_stat", "f_pvalue", "coefficients", "n_obs",
            "null_hypothesis", "interpretation",
        }
        assert expected_keys.issubset(result.keys())
        # coefficients é list[dict] (não DataFrame)
        assert isinstance(result["coefficients"], list)
        # dados sintéticos com tendência paralela → deve passar ou ser nan
        assert isinstance(result["f_stat"], (float, int))

    def test_run_event_study_returns_list(self, synthetic_panel):
        result = run_event_study(
            df=synthetic_panel,
            outcome="pib_log",
            treatment_year=TREATMENT_YEAR,
            pre_window=4,
            post_window=4,
        )
        assert isinstance(result["coefficients"], list)
        assert "C(id_municipio)" in result["formula"]
        assert "C(ano)" in result["formula"]
        if result["coefficients"]:
            ref = next(c for c in result["coefficients"] if c["rel_time"] == -1)
            assert ref["coef"] == 0.0

    def test_run_event_study_marks_pre_post_periods(self, synthetic_panel):
        result = run_event_study(
            df=synthetic_panel,
            outcome="pib_log",
            treatment_year=TREATMENT_YEAR,
            pre_window=3,
            post_window=3,
        )
        coeffs = result["coefficients"]
        assert any(c["period"] == "pre" for c in coeffs if c["rel_time"] < 0)
        assert any(c["period"] == "post" for c in coeffs if c["rel_time"] >= 0)

    def test_run_did_with_diagnostics_structure(self, synthetic_panel):
        result = run_did_with_diagnostics(
            df=synthetic_panel,
            outcome="pib_log",
            treatment_year=TREATMENT_YEAR,
            run_sensitivity=False,   # acelera o teste (jackknife é lento)
            run_specifications=False,
        )
        assert "main_result" in result
        assert "warnings" in result
        assert isinstance(result["warnings"], list)

    def test_did_no_dataframe_in_output(self, synthetic_panel):
        """Nenhum DataFrame cru deve aparecer na saída do DiD."""
        result = run_did_with_diagnostics(
            df=synthetic_panel,
            outcome="pib_log",
            treatment_year=TREATMENT_YEAR,
            run_sensitivity=False,
            run_specifications=False,
        )

        def _assert_no_df(obj, path="root"):
            if isinstance(obj, pd.DataFrame):
                raise AssertionError(f"DataFrame encontrado em {path}")
            if isinstance(obj, dict):
                for k, v in obj.items():
                    _assert_no_df(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    _assert_no_df(v, f"{path}[{i}]")

        _assert_no_df(result)


# ─── iv ───────────────────────────────────────────────────────────────────────


class TestIV:
    def test_run_iv_2sls_keys(self, synthetic_iv_df):
        result = run_iv_2sls(
            df=synthetic_iv_df,
            outcome="outcome",
            endog="endog",
            instrument="instrument",
        )
        expected = {"outcome", "endog", "instrument", "coef", "std_err", "p_value",
                    "ci_lower", "ci_upper", "n_obs"}
        assert expected.issubset(result.keys())

    def test_run_iv_2sls_coef_finite(self, synthetic_iv_df):
        result = run_iv_2sls(
            df=synthetic_iv_df,
            outcome="outcome",
            endog="endog",
            instrument="instrument",
        )
        assert math.isfinite(result["coef"])
        assert math.isfinite(result["std_err"])
        assert math.isfinite(result["p_value"])
        assert result["n_obs"] > 0

    def test_run_iv_recovers_known_coef(self, synthetic_iv_df):
        """IV deve recuperar coeficiente ≈ 1.5 do DGP sintético."""
        result = run_iv_2sls(
            df=synthetic_iv_df,
            outcome="outcome",
            endog="endog",
            instrument="instrument",
        )
        assert abs(result["coef"] - 1.5) < 0.5

    def test_first_stage_diagnostics_keys(self, synthetic_iv_df):
        result = first_stage_diagnostics(
            df=synthetic_iv_df,
            endog="endog",
            instrument="instrument",
        )
        expected = {"f_stat", "f_pvalue", "r2", "coef", "se", "t_stat",
                    "pvalue", "n_obs", "interpretation"}
        assert expected.issubset(result.keys())

    def test_first_stage_strong_instrument(self, synthetic_iv_df):
        """Instrumento sintético com ρ=0.8 deve ter F >> 10."""
        result = first_stage_diagnostics(
            df=synthetic_iv_df, endog="endog", instrument="instrument",
        )
        assert result["f_stat"] > 10
        assert "STRONG" in result["interpretation"] or "ADEQUATE" in result["interpretation"]

    def test_run_iv_with_diagnostics_has_first_stage(self, synthetic_iv_df):
        result = run_iv_with_diagnostics(
            df=synthetic_iv_df,
            outcome="outcome",
            endog="endog",
            instrument="instrument",
        )
        assert "main_result" in result
        assert "first_stage" in result
        assert "reduced_form" in result
        assert "warnings" in result


# ─── iv_panel ─────────────────────────────────────────────────────────────────


class TestPanelIV:
    @pytest.fixture(scope="class")
    def panel_iv_df(self):
        """Painel municipal sintético para testes de Panel IV."""
        rng = np.random.default_rng(seed=99)
        rows = []
        for mun in ALL_IDS:
            for year in YEARS:
                z = rng.normal(0, 1)
                x = 0.7 * z + rng.normal(0, 0.4)
                y = 1.2 * x + rng.normal(0, 0.3)
                rows.append({
                    "id_municipio": mun,
                    "ano": year,
                    "outcome": y,
                    "endog": x,
                    "instrument": z,
                })
        return pd.DataFrame(rows)

    def test_run_panel_iv_main_result_keys(self, panel_iv_df):
        result = run_panel_iv(
            df=panel_iv_df,
            outcome="outcome",
            endog="endog",
            instrument="instrument",
        )
        assert "main_result" in result
        assert "first_stage" in result
        mr = result["main_result"]
        expected = {"coef", "std_err", "t_stat", "p_value",
                    "ci_lower", "ci_upper", "n_obs", "n_entities", "n_time_periods"}
        assert expected.issubset(mr.keys())

    def test_run_panel_iv_first_stage_keys(self, panel_iv_df):
        result = run_panel_iv(
            df=panel_iv_df,
            outcome="outcome",
            endog="endog",
            instrument="instrument",
        )
        fs = result["first_stage"]
        assert {"f_stat", "f_pvalue", "r2", "interpretation"}.issubset(fs.keys())

    def test_run_panel_iv_coef_finite(self, panel_iv_df):
        result = run_panel_iv(
            df=panel_iv_df,
            outcome="outcome",
            endog="endog",
            instrument="instrument",
        )
        mr = result["main_result"]
        assert math.isfinite(mr["coef"])
        assert math.isfinite(mr["std_err"])
        assert mr["n_obs"] > 0

    def test_run_panel_iv_with_diagnostics_specs(self, panel_iv_df):
        result = run_panel_iv_with_diagnostics(
            df=panel_iv_df,
            outcome="outcome",
            endog="endog",
            instrument="instrument",
            alternative_specifications=True,
        )
        assert "main_result" in result
        assert "specifications" in result
        assert len(result["specifications"]) == 4  # two-way + entity + time + pooled


# ─── comparison ───────────────────────────────────────────────────────────────


class TestComparison:
    def test_compare_single_method(self):
        did_mock = {"coef": 0.10, "std_err": 0.03, "p_value": 0.001}
        result = compare_method_results(did_result=did_mock, outcome="pib_log")
        assert "DiD" in result["methods_available"]
        assert len(result["comparison_table"]) == 1

    def test_compare_did_iv(self):
        did_mock = {"coef": 0.10, "std_err": 0.03, "p_value": 0.001}
        iv_mock = {"coef": 0.12, "std_err": 0.05, "p_value": 0.020}
        result = compare_method_results(
            did_result=did_mock, iv_result=iv_mock, outcome="empregos_log"
        )
        assert set(result["methods_available"]) == {"DiD", "IV"}
        assert len(result["comparison_table"]) == 2
        assert isinstance(result["consistency_assessment"], str)

    def test_comparison_table_json_serializable(self):
        did_mock = {"coef": 0.10, "std_err": 0.03, "p_value": 0.001}
        iv_mock = {"coef": float("nan"), "std_err": 0.05, "p_value": 0.020}
        result = compare_method_results(
            did_result=did_mock, iv_result=iv_mock, outcome="pib"
        )
        json.dumps(result["comparison_table"])  # não deve lançar exceção


# ─── serialize ────────────────────────────────────────────────────────────────


class TestSerialize:
    def test_sanitize_nan_to_none(self):
        assert sanitize_scalars(float("nan")) is None
        assert sanitize_scalars(float("inf")) is None
        assert sanitize_scalars(float("-inf")) is None

    def test_sanitize_numpy_types(self):
        assert isinstance(sanitize_scalars(np.float64(3.14)), float)
        assert isinstance(sanitize_scalars(np.int32(7)), int)
        assert isinstance(sanitize_scalars(np.bool_(True)), bool)

    def test_dataframe_to_records_basic(self):
        df = pd.DataFrame({"a": [1.0, 2.0, float("nan")], "b": ["x", "y", "z"]})
        records = dataframe_to_records(df)
        assert len(records) == 3
        assert records[2]["a"] is None  # NaN → None
        assert records[0]["b"] == "x"

    def test_serialize_nested_dict_with_df(self):
        df = pd.DataFrame({"coef": [0.1, 0.2], "pvalue": [0.01, 0.05]})
        payload = {"main_result": {"coef": np.float64(0.15)}, "coefficients": df}
        result = serialize_causal_result(payload)
        assert isinstance(result["main_result"]["coef"], float)
        assert isinstance(result["coefficients"], list)
        json.dumps(result)  # não deve lançar

    def test_serialize_full_did_result_json_safe(self, synthetic_panel):
        """Resultado completo do DiD deve ser 100% serializável em JSON."""
        raw = run_did_with_diagnostics(
            df=synthetic_panel,
            outcome="pib_log",
            treatment_year=TREATMENT_YEAR,
            run_sensitivity=False,
            run_specifications=False,
        )
        payload = serialize_causal_result(raw)
        json_str = json.dumps(payload)
        assert len(json_str) > 10

    def test_no_dataframe_in_serialized_output(self, synthetic_panel):
        """Garantia de contrato: nenhum DataFrame deve aparecer após serialize."""
        raw = run_did_with_diagnostics(
            df=synthetic_panel,
            outcome="pib_log",
            treatment_year=TREATMENT_YEAR,
            run_sensitivity=False,
            run_specifications=False,
        )
        payload = serialize_causal_result(raw)

        def _check(obj, path="root"):
            if isinstance(obj, pd.DataFrame):
                raise AssertionError(f"DataFrame encontrado em '{path}'")
            if isinstance(obj, dict):
                for k, v in obj.items():
                    _check(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    _check(v, f"{path}[{i}]")

        _check(payload)
