"""Panel IV com dados municipais via 2SLS.

Portado de new_impacto/src/causal/iv_panel.py sem alterações funcionais.

A implementação:
1. Aplica within-transformation (demeaning por entidade) se ``entity_effects=True``.
2. Adiciona dummies de tempo se ``time_effects=True``.
3. Roda 2SLS padrão sobre os dados transformados.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.sandbox.regression.gmm import IV2SLS


def run_panel_iv(
    df: pd.DataFrame,
    outcome: str,
    endog: str,
    instrument: str,
    entity_col: str = "id_municipio",
    time_col: str = "ano",
    controls: Iterable[str] | None = None,
    entity_effects: bool = True,
    time_effects: bool = True,
) -> dict:
    """Panel IV com FE de entidade e/ou tempo.

    Returns
    -------
    dict com chaves:
        main_result (dict com coef/std_err/t_stat/p_value/ci_lower/ci_upper/n_obs/...),
        first_stage (dict com f_stat/f_pvalue/r2/interpretation/warning),
        model_info (dict com flags de FE),
        warnings (list[str])
    """
    controls = list(controls or [])
    warnings_list: list[str] = []

    required_cols = [outcome, endog, instrument, entity_col, time_col] + controls
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        return {
            "main_result": {},
            "first_stage": {},
            "model_info": {},
            "warnings": [f"Missing columns: {missing}"],
            "error": f"Missing columns: {missing}",
        }

    data = df[required_cols].copy().dropna()

    if len(data) == 0:
        return {
            "main_result": {},
            "first_stage": {},
            "model_info": {},
            "warnings": ["No valid observations after dropping missing values"],
            "error": "No data available",
        }

    n_entities = data[entity_col].nunique()
    n_time = data[time_col].nunique()

    try:
        # Passo 1: within-transformation por entidade
        vars_to_transform = [outcome, endog, instrument] + controls

        if entity_effects:
            for var in vars_to_transform:
                entity_means = data.groupby(entity_col)[var].transform("mean")
                data[f"{var}_within"] = data[var] - entity_means
            outcome_var = f"{outcome}_within"
            endog_var = f"{endog}_within"
            instrument_var = f"{instrument}_within"
            control_vars = [f"{c}_within" for c in controls]
        else:
            outcome_var = outcome
            endog_var = endog
            instrument_var = instrument
            control_vars = controls[:]

        # Passo 2: dummies de tempo
        if time_effects:
            time_dummies = pd.get_dummies(data[time_col], prefix="time", drop_first=True)
            data = pd.concat([data, time_dummies], axis=1)
            time_dummy_cols = time_dummies.columns.tolist()
        else:
            time_dummy_cols = []

        # Passo 3: arrays para 2SLS
        y = np.asarray(data[outcome_var], dtype=float)
        endog_x = np.asarray(data[endog_var], dtype=float)
        instr_z = np.asarray(data[instrument_var], dtype=float)

        all_controls = control_vars + time_dummy_cols
        if all_controls:
            ctrl_matrix = np.asarray(data[all_controls], dtype=float)
            exog = np.column_stack([endog_x, ctrl_matrix])
            instruments = np.column_stack([instr_z, ctrl_matrix])
        else:
            exog = endog_x[:, None]
            instruments = instr_z[:, None]

        exog = sm.add_constant(exog)
        instruments = sm.add_constant(instruments)

        # Passo 4: 2SLS
        fit = IV2SLS(y, exog, instruments).fit()
        coef = float(fit.params[1])
        se = float(fit.bse[1])

        main_result = {
            "outcome": outcome,
            "endog": endog,
            "instrument": instrument,
            "coef": coef,
            "std_err": se,
            "t_stat": float(fit.tvalues[1]),
            "p_value": float(fit.pvalues[1]),
            "ci_lower": coef - 1.96 * se,
            "ci_upper": coef + 1.96 * se,
            "n_obs": int(fit.nobs),
            "n_entities": int(n_entities),
            "n_time_periods": int(n_time),
        }

        # Passo 5: diagnóstico do primeiro estágio
        if all_controls:
            X_first = np.column_stack([instr_z, ctrl_matrix])
        else:
            X_first = instr_z[:, None]

        X_first = sm.add_constant(X_first)
        fs_model = sm.OLS(np.asarray(endog_x, dtype=float), X_first).fit()

        f_stat = float(fs_model.fvalue)
        f_pval = float(fs_model.f_pvalue)
        r2 = float(fs_model.rsquared)

        if f_stat > 16.38:
            fs_interp = "STRONG: F > 16.38 (Stock-Yogo critical value)"
            fs_warning = None
        elif f_stat > 10:
            fs_interp = "ADEQUATE: F > 10 (rule of thumb)"
            fs_warning = None
        else:
            fs_interp = "WEAK: F < 10. Instrument may be weak."
            fs_warning = f"WEAK INSTRUMENT (F={f_stat:.2f} < 10). Panel IV estimates may be biased."
            warnings_list.append(fs_warning)

        first_stage_result = {
            "f_stat": f_stat,
            "f_pvalue": f_pval,
            "r2": r2,
            "interpretation": fs_interp,
            "warning": fs_warning,
        }

        model_info = {
            "entity_effects": entity_effects,
            "time_effects": time_effects,
            "n_time_dummies": len(time_dummy_cols),
            "n_controls": len(controls),
            "transformation": "within" if entity_effects else "none",
        }

        return {
            "main_result": main_result,
            "first_stage": first_stage_result,
            "model_info": model_info,
            "warnings": warnings_list,
        }

    except Exception as exc:
        return {
            "main_result": {},
            "first_stage": {},
            "model_info": {},
            "warnings": [f"Panel IV estimation failed: {exc}"],
            "error": str(exc),
        }


def run_panel_iv_with_diagnostics(
    df: pd.DataFrame,
    outcome: str,
    endog: str,
    instrument: str,
    entity_col: str = "id_municipio",
    time_col: str = "ano",
    controls: Iterable[str] | None = None,
    alternative_specifications: bool = True,
) -> dict:
    """Panel IV completo com especificações alternativas para robustez.

    Roda especificação principal (two-way FE) + 3 alternativas.

    Returns
    -------
    dict com chaves: main_result, specifications (list[dict]), warnings
    """
    all_warnings: list[str] = []

    main_result = run_panel_iv(
        df=df, outcome=outcome, endog=endog, instrument=instrument,
        entity_col=entity_col, time_col=time_col,
        controls=controls, entity_effects=True, time_effects=True,
    )
    all_warnings.extend(main_result.get("warnings", []))

    results: dict = {"main_result": main_result}

    if alternative_specifications:
        specs: list[dict] = [
            {
                "specification": "Two-way FE (main)",
                "entity_effects": True,
                "time_effects": True,
                "n_controls": len(controls or []),
                "coef": main_result["main_result"].get("coef", float("nan")),
                "se": main_result["main_result"].get("std_err", float("nan")),
                "p_value": main_result["main_result"].get("p_value", float("nan")),
            }
        ]

        for label, ee, te in [
            ("Entity FE only", True, False),
            ("Time FE only", False, True),
            ("Pooled (no FE)", False, False),
        ]:
            r = run_panel_iv(
                df=df, outcome=outcome, endog=endog, instrument=instrument,
                entity_col=entity_col, time_col=time_col,
                controls=controls, entity_effects=ee, time_effects=te,
            )
            specs.append(
                {
                    "specification": label,
                    "entity_effects": ee,
                    "time_effects": te,
                    "n_controls": len(controls or []),
                    "coef": r["main_result"].get("coef", float("nan")),
                    "se": r["main_result"].get("std_err", float("nan")),
                    "p_value": r["main_result"].get("p_value", float("nan")),
                }
            )

        results["specifications"] = specs

    results["warnings"] = all_warnings
    return results
