"""Difference-in-Differences — estimação e diagnósticos.

Portado de new_impacto/src/causal/did.py.
Alterações de adaptação:
  - import circular `from src.causal.did import run_event_study` corrigido
    (a função já está no escopo local, chamada diretamente).
  - Nenhuma mudança funcional nos algoritmos.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats  # noqa: F401  (disponível para uso futuro pelos callers)


# ---------------------------------------------------------------------------
# Diagnóstico: tendências paralelas
# ---------------------------------------------------------------------------

def test_parallel_trends(
    df: pd.DataFrame,
    outcome: str,
    unit_col: str = "id_municipio",
    time_col: str = "ano",
    treat_col: str = "treated",
    treatment_year: int = 2015,
    controls: Iterable[str] | None = None,
    cluster_col: str | None = None,
) -> dict:
    """Testa a hipótese de tendências paralelas via interações tratamento × ano pré.

    H₀: Todos os coeficientes de interação tratamento × ano = 0.
    Se p < 0,05, rejeita-se a hipótese de tendências paralelas.

    Returns
    -------
    dict com chaves:
        f_stat, f_pvalue, coefficients (list[dict]), n_obs,
        null_hypothesis, interpretation
    """
    controls = list(controls or [])
    pre_data = df[df[time_col] < treatment_year].copy()

    if len(pre_data) == 0:
        return {
            "f_stat": float("nan"),
            "f_pvalue": float("nan"),
            "coefficients": [],
            "n_obs": 0,
            "null_hypothesis": "All treatment × year interactions = 0",
            "interpretation": "ERROR: No pre-treatment data available",
        }

    years = sorted(pre_data[time_col].unique())
    years_to_interact = years[1:]  # omite o primeiro como referência

    for year in years_to_interact:
        pre_data[f"year_{year}"] = (pre_data[time_col] == year).astype(int)
        pre_data[f"treat_x_year_{year}"] = (
            pre_data[treat_col] * pre_data[f"year_{year}"]
        )

    interaction_terms = [f"treat_x_year_{year}" for year in years_to_interact]
    formula_parts = (
        [treat_col]
        + [f"year_{year}" for year in years_to_interact]
        + interaction_terms
    )
    if controls:
        formula_parts.extend(controls)

    formula = f"{outcome} ~ " + " + ".join(formula_parts) + f" + C({unit_col})"

    cols_to_check = [outcome, unit_col, time_col, treat_col] + controls
    data = pre_data.dropna(subset=cols_to_check).copy()
    cluster = cluster_col or unit_col

    try:
        model = smf.ols(formula, data=data).fit(
            cov_type="cluster", cov_kwds={"groups": data[cluster]}
        )
    except Exception as exc:
        return {
            "f_stat": float("nan"),
            "f_pvalue": float("nan"),
            "coefficients": [],
            "n_obs": len(data),
            "null_hypothesis": "All treatment × year interactions = 0",
            "interpretation": f"ERROR: Regression failed — {exc}",
        }

    coef_data = []
    for year in years_to_interact:
        term = f"treat_x_year_{year}"
        if term in model.params:
            coef_data.append(
                {
                    "year": int(year),
                    "coef": float(model.params[term]),
                    "se": float(model.bse[term]),
                    "t_stat": float(model.tvalues[term]),
                    "pvalue": float(model.pvalues[term]),
                }
            )

    # F-test conjunto
    present = [t for t in interaction_terms if t in model.params]
    f_stat = f_pvalue = float("nan")
    if present:
        hypotheses = " = ".join(present)
        try:
            f_test = model.f_test(hypotheses + " = 0")
            f_val = f_test.fvalue
            f_stat = float(f_val[0][0] if hasattr(f_val, "__getitem__") else f_val)
            f_pvalue = float(f_test.pvalue)
        except Exception:
            R = np.zeros((len(present), len(model.params)))
            for i, p in enumerate(present):
                R[i, model.params.index.get_loc(p)] = 1
            try:
                wald = model.wald_test(R)
                fv = getattr(wald, "fvalue", None) or getattr(wald, "statistic", None)
                if fv is not None:
                    f_stat = float(fv[0][0] if hasattr(fv, "__getitem__") else fv)
                    f_pvalue = float(wald.pvalue)
            except Exception:
                pass

    if np.isnan(f_pvalue):
        interpretation = "Unable to compute F-test"
    elif f_pvalue < 0.05:
        interpretation = (
            "REJECT parallel trends (p<0.05): Pre-treatment trends differ significantly"
        )
    elif f_pvalue < 0.10:
        interpretation = (
            "WEAK parallel trends (0.05≤p<0.10): Some evidence of differential pre-trends"
        )
    else:
        interpretation = (
            "PASS parallel trends (p≥0.10): No significant evidence of differential pre-trends"
        )

    return {
        "f_stat": f_stat,
        "f_pvalue": f_pvalue,
        "coefficients": coef_data,
        "n_obs": int(model.nobs),
        "null_hypothesis": "All treatment × year interactions = 0",
        "interpretation": interpretation,
    }


# ---------------------------------------------------------------------------
# Event study
# ---------------------------------------------------------------------------

def run_event_study(
    df: pd.DataFrame,
    outcome: str,
    unit_col: str = "id_municipio",
    time_col: str = "ano",
    treat_col: str = "treated",
    treatment_year: int = 2015,
    controls: Iterable[str] | None = None,
    pre_window: int = 5,
    post_window: int = 5,
    cluster_col: str | None = None,
) -> dict:
    """Event study: coeficientes por período relativo ao tratamento.

    Período t=-1 é omitido como referência.

    Returns
    -------
    dict com chaves:
        coefficients (list[dict] com rel_time/coef/se/t_stat/pvalue/ci_lower/ci_upper),
        n_obs, formula, reference_period
    """
    controls = list(controls or [])
    data = df.copy()
    data["rel_time"] = data[time_col] - treatment_year
    data = data[
        (data["rel_time"] >= -pre_window) & (data["rel_time"] <= post_window)
    ].copy()

    if len(data) == 0:
        return {
            "coefficients": [],
            "n_obs": 0,
            "formula": "",
            "reference_period": -1,
        }

    rel_times = sorted(data["rel_time"].unique())
    rel_times_to_include = [t for t in rel_times if t != -1]

    for t in rel_times_to_include:
        data[f"rel_time_{t}"] = (data["rel_time"] == t).astype(int)
        data[f"treat_x_rel_time_{t}"] = data[treat_col] * data[f"rel_time_{t}"]

    interaction_terms = [f"treat_x_rel_time_{t}" for t in rel_times_to_include]
    time_dummies = [f"rel_time_{t}" for t in rel_times_to_include]
    formula_parts = [treat_col] + time_dummies + interaction_terms
    if controls:
        formula_parts.extend(controls)

    formula = f"{outcome} ~ " + " + ".join(formula_parts) + f" + C({unit_col})"
    cols_to_check = [outcome, unit_col, time_col, treat_col] + controls
    data = data.dropna(subset=cols_to_check).copy()
    cluster = cluster_col or unit_col

    try:
        model = smf.ols(formula, data=data).fit(
            cov_type="cluster", cov_kwds={"groups": data[cluster]}
        )
    except Exception as exc:
        return {
            "coefficients": [],
            "n_obs": len(data),
            "formula": formula,
            "reference_period": -1,
            "error": str(exc),
        }

    # referência t=-1
    coef_data: list[dict] = [
        {
            "rel_time": -1,
            "coef": 0.0,
            "se": 0.0,
            "t_stat": 0.0,
            "pvalue": 1.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
        }
    ]

    for t in rel_times_to_include:
        term = f"treat_x_rel_time_{t}"
        if term in model.params:
            coef = float(model.params[term])
            se = float(model.bse[term])
            coef_data.append(
                {
                    "rel_time": int(t),
                    "coef": coef,
                    "se": se,
                    "t_stat": float(model.tvalues[term]),
                    "pvalue": float(model.pvalues[term]),
                    "ci_lower": coef - 1.96 * se,
                    "ci_upper": coef + 1.96 * se,
                }
            )

    coef_data.sort(key=lambda r: r["rel_time"])

    return {
        "coefficients": coef_data,
        "n_obs": int(model.nobs),
        "formula": formula,
        "reference_period": -1,
    }


# ---------------------------------------------------------------------------
# DiD principal
# ---------------------------------------------------------------------------

def run_did(
    df: pd.DataFrame,
    outcome: str,
    unit_col: str = "id_municipio",
    time_col: str = "ano",
    treat_col: str = "treated",
    post_col: str = "post",
    controls: Iterable[str] | None = None,
    cluster_col: str | None = None,
) -> dict:
    """Two-way fixed-effects DiD com erros-padrão clusterizados.

    Returns
    -------
    dict com chaves: outcome, coef, std_err, p_value, n_obs, r2, formula
    """
    controls = list(controls or [])
    formula_parts = [f"{treat_col}*{post_col}"]
    if controls:
        formula_parts.extend(controls)
    formula = (
        f"{outcome} ~ "
        + " + ".join(formula_parts)
        + f" + C({unit_col}) + C({time_col})"
    )

    cols_to_check = [outcome, unit_col, time_col, treat_col, post_col] + controls
    data = df.dropna(subset=cols_to_check).copy()
    cluster = cluster_col or unit_col
    model = smf.ols(formula, data=data).fit(
        cov_type="cluster", cov_kwds={"groups": data[cluster]}
    )

    term = f"{treat_col}:{post_col}"
    if term not in model.params:
        term = f"{post_col}:{treat_col}"

    return {
        "outcome": outcome,
        "coef": float(model.params.get(term, float("nan"))),
        "std_err": float(model.bse.get(term, float("nan"))),
        "p_value": float(model.pvalues.get(term, float("nan"))),
        "n_obs": int(model.nobs),
        "r2": float(model.rsquared),
        "formula": formula,
    }


# ---------------------------------------------------------------------------
# Placebo tests
# ---------------------------------------------------------------------------

def run_placebo_tests(
    df: pd.DataFrame,
    outcome: str,
    placebo_years: Iterable[int],
    actual_treatment_year: int,
    unit_col: str = "id_municipio",
    time_col: str = "ano",
    treat_col: str = "treated",
    post_col: str = "post",
    controls: Iterable[str] | None = None,
    cluster_col: str | None = None,
) -> dict:
    """Placebos DiD com datas de tratamento fictícias pré-tratamento real.

    Returns
    -------
    dict com chaves:
        placebo_results (list[dict]), actual_treatment_year,
        n_placebos_tested, n_significant, interpretation
    """
    placebo_years_list = list(placebo_years)
    placebo_results = []
    pre_actual_data = df[df[time_col] < actual_treatment_year].copy()

    for placebo_year in placebo_years_list:
        df_copy = pre_actual_data.copy()
        df_copy["post_placebo"] = (df_copy[time_col] >= placebo_year).astype(int)
        try:
            res = run_did(
                df=df_copy,
                outcome=outcome,
                unit_col=unit_col,
                time_col=time_col,
                treat_col=treat_col,
                post_col="post_placebo",
                controls=controls,
                cluster_col=cluster_col,
            )
            res["placebo_year"] = int(placebo_year)
            placebo_results.append(res)
        except Exception as exc:
            placebo_results.append(
                {
                    "placebo_year": int(placebo_year),
                    "outcome": outcome,
                    "coef": float("nan"),
                    "std_err": float("nan"),
                    "p_value": float("nan"),
                    "error": str(exc),
                }
            )

    n_significant = sum(
        1 for r in placebo_results if r.get("p_value", 1) < 0.10
    )
    n_total = len(placebo_results)

    if n_significant == 0:
        interpretation = (
            f"PASS: No significant placebo effects (0/{n_total}). Parallel trends likely hold."
        )
    elif n_significant <= n_total / 2:
        interpretation = (
            f"WEAK: Some placebo effects significant ({n_significant}/{n_total}). Check pre-trends."
        )
    else:
        interpretation = (
            f"FAIL: Multiple placebo effects significant ({n_significant}/{n_total}). "
            "Parallel trends violated."
        )

    return {
        "placebo_results": placebo_results,
        "actual_treatment_year": actual_treatment_year,
        "n_placebos_tested": n_total,
        "n_significant": n_significant,
        "interpretation": interpretation,
    }


# ---------------------------------------------------------------------------
# Jackknife (donor sensitivity)
# ---------------------------------------------------------------------------

def donor_sensitivity_analysis(
    df: pd.DataFrame,
    outcome: str,
    unit_col: str = "id_municipio",
    time_col: str = "ano",
    treat_col: str = "treated",
    post_col: str = "post",
    controls: Iterable[str] | None = None,
    cluster_col: str | None = None,
) -> dict:
    """Jackknife: re-estima DiD removendo cada unidade de controle.

    Returns
    -------
    dict com chaves:
        baseline_coef, jackknife_coefs (list[dict]),
        mean_coef, std_dev, min_coef, max_coef,
        n_control_units, interpretation
    """
    baseline = run_did(
        df=df,
        outcome=outcome,
        unit_col=unit_col,
        time_col=time_col,
        treat_col=treat_col,
        post_col=post_col,
        controls=controls,
        cluster_col=cluster_col,
    )
    baseline_coef = baseline["coef"]
    control_units = df[df[treat_col] == 0][unit_col].unique()
    jackknife_results: list[dict] = []

    for excluded in control_units:
        df_sub = df[df[unit_col] != excluded].copy()
        try:
            res = run_did(
                df=df_sub,
                outcome=outcome,
                unit_col=unit_col,
                time_col=time_col,
                treat_col=treat_col,
                post_col=post_col,
                controls=controls,
                cluster_col=cluster_col,
            )
            jackknife_results.append(
                {
                    "excluded_unit": str(excluded),
                    "coef": res["coef"],
                    "std_err": res["std_err"],
                    "p_value": res["p_value"],
                }
            )
        except Exception as exc:
            jackknife_results.append(
                {"excluded_unit": str(excluded), "coef": float("nan"), "error": str(exc)}
            )

    valid_coefs = [r["coef"] for r in jackknife_results if not np.isnan(r["coef"])]

    if valid_coefs:
        mean_coef = float(np.mean(valid_coefs))
        std_dev = float(np.std(valid_coefs))
        min_coef = float(np.min(valid_coefs))
        max_coef = float(np.max(valid_coefs))
        relative_std = abs(std_dev / baseline_coef) if baseline_coef != 0 else float("inf")

        if relative_std < 0.10:
            interpretation = f"ROBUST: Low variation (std/baseline={relative_std:.1%})"
        elif relative_std < 0.25:
            interpretation = f"MODERATE: Some variation (std/baseline={relative_std:.1%})"
        else:
            interpretation = (
                f"SENSITIVE: High variation (std/baseline={relative_std:.1%}). "
                "Results may be driven by specific donors."
            )
    else:
        mean_coef = std_dev = min_coef = max_coef = float("nan")
        interpretation = "Unable to compute jackknife statistics"

    return {
        "baseline_coef": baseline_coef,
        "jackknife_coefs": jackknife_results,
        "mean_coef": mean_coef,
        "std_dev": std_dev,
        "min_coef": min_coef,
        "max_coef": max_coef,
        "n_control_units": int(len(control_units)),
        "interpretation": interpretation,
    }


# ---------------------------------------------------------------------------
# Especificações alternativas
# ---------------------------------------------------------------------------

def run_did_specifications(
    df: pd.DataFrame,
    outcome: str,
    unit_col: str = "id_municipio",
    time_col: str = "ano",
    treat_col: str = "treated",
    post_col: str = "post",
    controls: Iterable[str] | None = None,
    cluster_col: str | None = None,
) -> list[dict]:
    """DiD em 4 especificações alternativas para teste de robustez.

    Returns
    -------
    list[dict] — cada dict tem as chaves:
        specification, coef, std_err, p_value, n_obs, r2  (ou ``error``)
    """
    specs: list[dict] = []

    def _try(spec_name: str, **kwargs) -> dict:
        try:
            r = run_did(df=df, outcome=outcome, **kwargs)
            return {
                "specification": spec_name,
                "coef": r["coef"],
                "std_err": r["std_err"],
                "p_value": r["p_value"],
                "n_obs": r["n_obs"],
                "r2": r["r2"],
            }
        except Exception as exc:
            return {"specification": spec_name, "error": str(exc)}

    specs.append(
        _try(
            "1. Baseline (FE + controls + clustering)",
            unit_col=unit_col, time_col=time_col,
            treat_col=treat_col, post_col=post_col,
            controls=controls, cluster_col=cluster_col,
        )
    )
    specs.append(
        _try(
            "2. No controls (FE only)",
            unit_col=unit_col, time_col=time_col,
            treat_col=treat_col, post_col=post_col,
            controls=None, cluster_col=cluster_col,
        )
    )

    # Sem clustering (cada obs é seu próprio cluster)
    df_temp = df.copy()
    df_temp["_row_id"] = range(len(df_temp))
    specs.append(
        _try(
            "3. No clustering (FE + controls)",
            unit_col=unit_col, time_col=time_col,
            treat_col=treat_col, post_col=post_col,
            controls=controls, cluster_col="_row_id",
        )
    )

    if cluster_col != time_col:
        specs.append(
            _try(
                "4. Cluster by time (FE + controls)",
                unit_col=unit_col, time_col=time_col,
                treat_col=treat_col, post_col=post_col,
                controls=controls, cluster_col=time_col,
            )
        )

    return specs


# ---------------------------------------------------------------------------
# Wrapper completo com todos os diagnósticos
# ---------------------------------------------------------------------------

def run_did_with_diagnostics(
    df: pd.DataFrame,
    outcome: str,
    treatment_year: int = 2015,
    unit_col: str = "id_municipio",
    time_col: str = "ano",
    treat_col: str = "treated",
    post_col: str = "post",
    controls: Iterable[str] | None = None,
    cluster_col: str | None = None,
    run_parallel_trends: bool = True,
    run_event_study_flag: bool = True,
    run_placebo: bool = True,
    placebo_years: Iterable[int] | None = None,
    run_sensitivity: bool = True,
    run_specifications: bool = True,
    pre_window: int = 5,
    post_window: int = 5,
) -> dict:
    """DiD completo com todos os diagnósticos e checks de robustez.

    Executa estimação principal + tendências paralelas + event study +
    placebos + jackknife + especificações alternativas.

    Returns
    -------
    dict com chaves:
        main_result, parallel_trends, event_study, placebo,
        sensitivity, specifications, warnings
    """
    warnings_list: list[str] = []

    main_result = run_did(
        df=df,
        outcome=outcome,
        unit_col=unit_col,
        time_col=time_col,
        treat_col=treat_col,
        post_col=post_col,
        controls=controls,
        cluster_col=cluster_col,
    )

    result: dict = {"main_result": main_result, "warnings": warnings_list}

    if run_parallel_trends:
        try:
            pt = test_parallel_trends(
                df=df,
                outcome=outcome,
                unit_col=unit_col,
                time_col=time_col,
                treat_col=treat_col,
                treatment_year=treatment_year,
                controls=controls,
                cluster_col=cluster_col,
            )
            result["parallel_trends"] = pt
            if pt.get("f_pvalue", 1) < 0.05:
                warnings_list.append(
                    "Parallel trends test REJECTED (p<0.05). DiD estimates may be biased."
                )
        except Exception as exc:
            result["parallel_trends"] = {"error": str(exc)}
            warnings_list.append(f"Parallel trends test failed: {exc}")

    if run_event_study_flag:
        try:
            es = run_event_study(
                df=df,
                outcome=outcome,
                unit_col=unit_col,
                time_col=time_col,
                treat_col=treat_col,
                treatment_year=treatment_year,
                controls=controls,
                pre_window=pre_window,
                post_window=post_window,
                cluster_col=cluster_col,
            )
            result["event_study"] = es
            pre_coefs = [c for c in es.get("coefficients", []) if c["rel_time"] < 0]
            if pre_coefs:
                n_sig = sum(1 for c in pre_coefs if c["pvalue"] < 0.10)
                if n_sig > len(pre_coefs) / 2:
                    warnings_list.append(
                        f"Event study: {n_sig}/{len(pre_coefs)} significant pre-treatment "
                        "coefficients. Parallel trends questionable."
                    )
        except Exception as exc:
            result["event_study"] = {"error": str(exc)}
            warnings_list.append(f"Event study failed: {exc}")

    if run_placebo:
        try:
            py = list(placebo_years or [treatment_year - 3, treatment_year - 2])
            placebo = run_placebo_tests(
                df=df,
                outcome=outcome,
                placebo_years=py,
                actual_treatment_year=treatment_year,
                unit_col=unit_col,
                time_col=time_col,
                treat_col=treat_col,
                post_col=post_col,
                controls=controls,
                cluster_col=cluster_col,
            )
            result["placebo"] = placebo
            if placebo.get("n_significant", 0) > 0:
                warnings_list.append(
                    f"Placebo tests: {placebo['n_significant']}/{placebo['n_placebos_tested']} "
                    "significant. Parallel trends may not hold."
                )
        except Exception as exc:
            result["placebo"] = {"error": str(exc)}
            warnings_list.append(f"Placebo tests failed: {exc}")

    if run_sensitivity:
        try:
            sens = donor_sensitivity_analysis(
                df=df,
                outcome=outcome,
                unit_col=unit_col,
                time_col=time_col,
                treat_col=treat_col,
                post_col=post_col,
                controls=controls,
                cluster_col=cluster_col,
            )
            result["sensitivity"] = sens
            if "SENSITIVE" in sens.get("interpretation", ""):
                warnings_list.append(
                    "Results sensitive to specific control units. Consider expanding donor pool."
                )
        except Exception as exc:
            result["sensitivity"] = {"error": str(exc)}
            warnings_list.append(f"Sensitivity analysis failed: {exc}")

    if run_specifications:
        try:
            specs = run_did_specifications(
                df=df,
                outcome=outcome,
                unit_col=unit_col,
                time_col=time_col,
                treat_col=treat_col,
                post_col=post_col,
                controls=controls,
                cluster_col=cluster_col,
            )
            result["specifications"] = specs
            valid_coefs = [
                s["coef"] for s in specs if "coef" in s and not np.isnan(s["coef"])
            ]
            if len(valid_coefs) > 1:
                cv = abs(np.std(valid_coefs) / np.mean(valid_coefs)) if np.mean(valid_coefs) != 0 else float("inf")
                if cv > 0.3:
                    warnings_list.append(
                        f"High variation across specifications (CV={cv:.1%}). "
                        "Results may be sensitive to modeling choices."
                    )
        except Exception as exc:
            result["specifications"] = []
            warnings_list.append(f"Specification tests failed: {exc}")

    if not warnings_list:
        warnings_list.append("All diagnostic tests passed. DiD estimates appear robust.")

    result["warnings"] = warnings_list
    return result
