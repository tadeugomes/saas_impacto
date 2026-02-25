"""Variáveis Instrumentais — 2SLS e diagnósticos.

Portado de new_impacto/src/causal/iv.py sem alterações funcionais.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.sandbox.regression.gmm import IV2SLS


def run_iv_2sls(
    df: pd.DataFrame,
    outcome: str,
    endog: str,
    instrument: str,
    controls: Iterable[str] | None = None,
) -> dict:
    """2SLS simples com um regressor endógeno e um instrumento.

    Returns
    -------
    dict com chaves:
        outcome, endog, instrument, coef, std_err, p_value,
        ci_lower, ci_upper, n_obs
    """
    controls = list(controls or [])
    data = df.dropna(subset=[outcome, endog, instrument] + controls).copy()

    y = data[outcome].astype(float).to_numpy()
    endog_x = data[endog].astype(float).to_numpy()
    instr_z = data[instrument].astype(float).to_numpy()

    if controls:
        controls_x = data[controls].astype(float).to_numpy()
        exog = np.column_stack([endog_x, controls_x])
        instruments = np.column_stack([instr_z, controls_x])
    else:
        exog = endog_x[:, None]
        instruments = instr_z[:, None]

    exog = sm.add_constant(exog)
    instruments = sm.add_constant(instruments)

    model = IV2SLS(y, exog, instruments).fit()
    coef = float(model.params[1])
    se = float(model.bse[1])

    return {
        "outcome": outcome,
        "endog": endog,
        "instrument": instrument,
        "coef": coef,
        "std_err": se,
        "p_value": float(model.pvalues[1]),
        "ci_lower": coef - 1.96 * se,
        "ci_upper": coef + 1.96 * se,
        "n_obs": int(model.nobs),
    }


def first_stage_diagnostics(
    df: pd.DataFrame,
    endog: str,
    instrument: str,
    controls: Iterable[str] | None = None,
) -> dict:
    """Diagnóstico do primeiro estágio: relevância do instrumento.

    Regra de bolso (Stock & Yogo 2005):
    - F > 10  : instrumento forte pelo critério básico
    - F > 16.38 : valor crítico para 10% de viés maximal (1 instr., 1 endog.)

    Returns
    -------
    dict com chaves:
        f_stat, f_pvalue, r2, coef, se, t_stat, pvalue, n_obs,
        warning (str | None), interpretation
    """
    controls = list(controls or [])
    data = df.dropna(subset=[endog, instrument] + controls).copy()

    y_first = data[endog].astype(float).to_numpy()
    z = data[instrument].astype(float).to_numpy()

    if controls:
        X_ctrl = data[controls].astype(float).to_numpy()
        X_first = np.column_stack([z, X_ctrl])
    else:
        X_first = z[:, None]

    X_first = sm.add_constant(X_first)

    try:
        fs = sm.OLS(y_first, X_first).fit()
    except Exception as exc:
        return {
            "error": f"First-stage regression failed: {exc}",
            "f_stat": float("nan"),
            "f_pvalue": float("nan"),
        }

    coef = float(fs.params[1])
    se = float(fs.bse[1])
    t_stat = float(fs.tvalues[1])
    pvalue = float(fs.pvalues[1])
    r2 = float(fs.rsquared)
    f_stat = t_stat**2  # F = t² para instrumento único
    f_pvalue = pvalue

    if f_stat < 10:
        warning = f"WEAK INSTRUMENT (F={f_stat:.2f} < 10). 2SLS estimates may be biased."
        interpretation = "WEAK: Instrument fails rule-of-thumb test (F<10)"
    elif f_stat < 16.38:
        warning = (
            f"MARGINAL INSTRUMENT (10 ≤ F={f_stat:.2f} < 16.38). "
            "Consider weak-instrument-robust inference."
        )
        interpretation = "MARGINAL: Passes rule-of-thumb but below Stock-Yogo critical value"
    else:
        warning = None
        interpretation = f"STRONG: Instrument passes both tests (F={f_stat:.2f} ≥ 16.38)"

    return {
        "f_stat": f_stat,
        "f_pvalue": f_pvalue,
        "r2": r2,
        "coef": coef,
        "se": se,
        "t_stat": t_stat,
        "pvalue": pvalue,
        "n_obs": int(fs.nobs),
        "warning": warning,
        "interpretation": interpretation,
    }


def run_reduced_form(
    df: pd.DataFrame,
    outcome: str,
    instrument: str,
    controls: Iterable[str] | None = None,
) -> dict:
    """Forma reduzida: outcome ~ instrument + controls.

    Útil para diagnosticar se um resultado nulo no IV é por instrumento
    fraco ou ausência real de efeito.

    Returns
    -------
    dict com chaves: coef, se, t_stat, pvalue, r2, n_obs, interpretation
    """
    controls = list(controls or [])
    data = df.dropna(subset=[outcome, instrument] + controls).copy()

    y = data[outcome].astype(float).to_numpy()
    z = data[instrument].astype(float).to_numpy()

    if controls:
        X_rf = np.column_stack([z, data[controls].astype(float).to_numpy()])
    else:
        X_rf = z[:, None]

    X_rf = sm.add_constant(X_rf)

    try:
        rf = sm.OLS(y, X_rf).fit()
    except Exception as exc:
        return {
            "error": f"Reduced form regression failed: {exc}",
            "coef": float("nan"),
            "pvalue": float("nan"),
        }

    coef = float(rf.params[1])
    se = float(rf.bse[1])
    t_stat = float(rf.tvalues[1])
    pvalue = float(rf.pvalues[1])

    if pvalue < 0.05:
        interpretation = f"SIGNIFICANT (p={pvalue:.3f}): instrument directly affects outcome"
    elif pvalue < 0.10:
        interpretation = f"MARGINALLY SIGNIFICANT (p={pvalue:.3f})"
    else:
        interpretation = f"NOT SIGNIFICANT (p={pvalue:.3f}): no direct effect of instrument"

    return {
        "coef": coef,
        "se": se,
        "t_stat": t_stat,
        "pvalue": pvalue,
        "r2": float(rf.rsquared),
        "n_obs": int(rf.nobs),
        "interpretation": interpretation,
    }


def test_alternative_instruments(
    df: pd.DataFrame,
    outcome: str,
    endog: str,
    instruments: dict[str, str],
    controls: Iterable[str] | None = None,
) -> list[dict]:
    """Testa robustez com múltiplos instrumentos alternativos.

    Parameters
    ----------
    instruments:
        Mapeamento nome_legível → coluna_no_df.

    Returns
    -------
    list[dict] com chaves por instrumento:
        instrument, coef, se, pvalue, first_stage_f, first_stage_r2, n_obs
    """
    results: list[dict] = []
    for inst_name, inst_col in instruments.items():
        try:
            iv_res = run_iv_2sls(
                df=df, outcome=outcome, endog=endog,
                instrument=inst_col, controls=controls,
            )
            fs = first_stage_diagnostics(
                df=df, endog=endog, instrument=inst_col, controls=controls,
            )
            results.append(
                {
                    "instrument": inst_name,
                    "coef": iv_res["coef"],
                    "se": iv_res["std_err"],
                    "pvalue": iv_res["p_value"],
                    "first_stage_f": fs.get("f_stat", float("nan")),
                    "first_stage_r2": fs.get("r2", float("nan")),
                    "n_obs": iv_res["n_obs"],
                }
            )
        except Exception as exc:
            results.append({"instrument": inst_name, "error": str(exc)})
    return results


def run_iv_with_diagnostics(
    df: pd.DataFrame,
    outcome: str,
    endog: str,
    instrument: str,
    controls: Iterable[str] | None = None,
    alternative_instruments: dict[str, str] | None = None,
) -> dict:
    """IV completo com primeiro estágio, forma reduzida e instrumentos alternativos.

    Returns
    -------
    dict com chaves:
        main_result, first_stage, reduced_form,
        alternative_instruments (list[dict] | None), warnings
    """
    warnings_list: list[str] = []

    main_result = run_iv_2sls(
        df=df, outcome=outcome, endog=endog,
        instrument=instrument, controls=controls,
    )
    result: dict = {"main_result": main_result, "warnings": warnings_list}

    # Primeiro estágio
    try:
        fs = first_stage_diagnostics(
            df=df, endog=endog, instrument=instrument, controls=controls,
        )
        result["first_stage"] = fs
        if fs.get("warning"):
            warnings_list.append(f"First-stage: {fs['warning']}")
    except Exception as exc:
        result["first_stage"] = {"error": str(exc)}
        warnings_list.append(f"First-stage diagnostics failed: {exc}")

    # Forma reduzida
    try:
        rf = run_reduced_form(
            df=df, outcome=outcome, instrument=instrument, controls=controls,
        )
        result["reduced_form"] = rf
        fs_ok = result.get("first_stage", {})
        if (
            main_result.get("p_value", 1) > 0.10
            and rf.get("pvalue", 1) < 0.10
            and fs_ok.get("f_stat", 0) > 10
        ):
            warnings_list.append(
                "Inconsistency: Reduced form significant but IV not. "
                "Check for heterogeneous effects or specification issues."
            )
    except Exception as exc:
        result["reduced_form"] = {"error": str(exc)}
        warnings_list.append(f"Reduced form analysis failed: {exc}")

    # Instrumentos alternativos
    if alternative_instruments:
        try:
            alt = test_alternative_instruments(
                df=df, outcome=outcome, endog=endog,
                instruments=alternative_instruments, controls=controls,
            )
            result["alternative_instruments"] = alt
            valid = [r["coef"] for r in alt if "coef" in r and not np.isnan(r["coef"])]
            if len(valid) > 1:
                cv = abs(np.std(valid) / np.mean(valid)) if np.mean(valid) != 0 else float("inf")
                if cv > 0.5:
                    warnings_list.append(
                        f"High variation across instruments (CV={cv:.1%}). "
                        "Results may be sensitive to instrument choice."
                    )
        except Exception as exc:
            result["alternative_instruments"] = []
            warnings_list.append(f"Alternative instruments testing failed: {exc}")

    if not warnings_list:
        warnings_list.append("All diagnostic tests passed. IV estimates appear robust.")

    result["warnings"] = warnings_list
    return result
