"""Augmented Synthetic Control Method simplificado (Ben-Michael et al., 2021).

Implementação prática para produção sem dependência externa:
- roda um SCM base para obter pesos,
- estima correção por regressão ridge sobre a diferença de pré-tratamento
  usando covariáveis de controle,
- retorna diagnóstico complementar `base_result`, `augmented_result` e placebo.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from .scm import (
    _extract_unit_frames,
    _prepare_predictor_matrix,
    _rmspe,
    _solve_non_negative_weights,
    _construct_synthetic_series,
    _in_space_placebos,
    _event_study,
    _safe_float,
)


class AugmentedSCMNotAvailableError(NotImplementedError):
    """Compatibilidade histórica do PR-07.

    O ASCM está disponível com implementação local.
    """

    def __init__(self, message: str = "ASCM disponível (implementação local).") -> None:
        super().__init__(message)


def _ridge_fit(x: np.ndarray, y: np.ndarray, ridge_lambda: float) -> np.ndarray:
    k = x.shape[1]
    alpha = float(ridge_lambda) if ridge_lambda > 0 else 1e-6
    xpx = x.T @ x
    beta = np.linalg.solve(xpx + alpha * np.eye(k), x.T @ y)
    return beta


def _autoselect_ridge(
    x: np.ndarray,
    y: np.ndarray,
) -> float:
    # grade curta para evitar custo, já suficiente para estabilizar.
    candidates = [0.0, 0.01, 0.1, 1.0, 10.0]
    best = {"lambda": 1.0, "loss": float("inf")}
    for lam in candidates:
        beta = _ridge_fit(x, y, lam)
        pred = x @ beta
        loss = float(np.mean((y - pred) ** 2))
        if loss < best["loss"]:
            best = {"lambda": lam, "loss": loss}
    return best["lambda"]


def run_augmented_scm(
    df: pd.DataFrame,
    outcome: str,
    treatment_year: int,
    controls: list[str] | None = None,
    ridge_lambda: float | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Executa ASCM e retorna apenas o resultado principal (sem painéis)."""
    out = run_augmented_scm_with_diagnostics(
        df=df,
        outcome=outcome,
        treatment_year=treatment_year,
        controls=controls,
        ridge_lambda=ridge_lambda,
        n_placebos=0,
    )
    return out.get("main_result", {})


def run_augmented_scm_with_diagnostics(
    df: pd.DataFrame,
    outcome: str,
    treatment_year: int,
    controls: list[str] | None = None,
    ridge_lambda: float | None = None,
    n_placebos: int = 50,
    run_in_time_placebo: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    warnings: list[str] = []
    try:
        treated_df, control_df, treated_id = _extract_unit_frames(
            df=df,
            outcome=outcome,
            treatment_year=treatment_year,
            controls=controls,
        )
    except ValueError as exc:
        return {
            "base_result": {
                "post_att": None,
                "pre_rmspe": None,
                "post_rmspe": None,
                "w_optimal": [],
                "donor_units": [],
            },
            "augmented_result": {
                "post_att": None,
                "pre_rmspe": None,
                "post_rmspe": None,
                "ridge_lambda": None,
                "w_optimal": [],
                "donor_units": [],
            },
            "placebo_test": {"p_value": None, "in_time_placebos": [], "in_space_placebos": []},
            "event_study": [],
            "main_result": {"post_att": None},
            "warnings": [str(exc)],
            "treated_unit": None,
        }

    x0, target, donor_ids, pre_treated, control_agg, _years = _prepare_predictor_matrix(
        treated_df=treated_df,
        control_df=control_df,
        outcome=outcome,
        treatment_year=treatment_year,
        controls=controls,
    )

    w = _solve_non_negative_weights(x0=x0, target=target)
    synthetic_df = _construct_synthetic_series(
        donor_panel=control_df[["id_municipio", "ano", outcome]].copy(),
        outcome=outcome,
        donor_ids=donor_ids,
        weights=w,
    )

    treated_series = treated_df[["ano", outcome]].sort_values("ano").copy()
    pre_mask = treated_series["ano"] < treatment_year
    post_mask = treated_series["ano"] >= treatment_year
    synth_series = synthetic_df.set_index("ano")["synthetic"]
    pre_actual = treated_series.loc[pre_mask].set_index("ano")[outcome]
    post_actual = treated_series.loc[post_mask].set_index("ano")[outcome]
    pre_synth = synth_series.loc[pre_actual.index]
    post_synth = synth_series.loc[post_actual.index]

    base_pre_rmspe = _rmspe(pre_actual.to_numpy(dtype=float), pre_synth.to_numpy(dtype=float))
    base_post_rmspe = _rmspe(post_actual.to_numpy(dtype=float), post_synth.to_numpy(dtype=float))
    base_post_att = float((post_actual - post_synth).mean()) if post_actual.size else None

    treated_pre = treated_df[treated_df["ano"] < treatment_year].sort_values("ano")
    treated_pre_controls = (
        treated_pre[controls or []].to_numpy(dtype=float)
        if controls
        else np.empty((len(pre_actual), 0))
    )
    ridge_val = ridge_lambda
    if controls:
        # Correção em nível de série temporal usando controles observados do tratado.
        treat_residual = pre_actual.to_numpy(dtype=float) - pre_synth.loc[pre_actual.index].to_numpy(dtype=float)
        if treated_pre_controls.ndim == 1:
            treated_pre_controls = treated_pre_controls.reshape(-1, 1)
        if ridge_lambda is None:
            ridge_val = _autoselect_ridge(treated_pre_controls, treat_residual)

        beta = _ridge_fit(treated_pre_controls, treat_residual, float(ridge_val))
        treated_post = treated_df[treated_df["ano"] >= treatment_year].sort_values("ano")
        post_controls = treated_post[controls or []].to_numpy(dtype=float)
        if post_controls.ndim == 1:
            post_controls = post_controls.reshape(-1, 1)
        bias = post_controls @ beta if post_controls.size else 0.0
        if post_actual.size:
            adj_post = post_synth.loc[post_actual.index].to_numpy(dtype=float) + bias
            adj_post = np.asarray(adj_post)
            aug_post_att = float(np.mean(post_actual.to_numpy(dtype=float) - adj_post))
            aug_post_rmspe = _rmspe(
                post_actual.to_numpy(dtype=float),
                adj_post,
            )
        else:
            aug_post_att = None
            aug_post_rmspe = None
    else:
        # sem controles, ASCM reduz ao SCM com lambda neutro
        aug_post_att = base_post_att
        aug_post_rmspe = base_post_rmspe
        ridge_val = 0.0

    event_study = _event_study(
        treated_df=treated_df,
        synthetic_df=synthetic_df,
        outcome=outcome,
    )

    placebo_rows, p_value = _in_space_placebos(
        treated_df=treated_df,
        control_df=control_df,
        outcome=outcome,
        treatment_year=treatment_year,
        controls=controls,
        n_placebos=n_placebos,
        treated_ratio=None,
    )
    if run_in_time_placebo:
        in_time_placebos = []
    else:
        in_time_placebos = []

    if base_pre_rmspe is not None and math.isfinite(base_pre_rmspe) and base_pre_rmspe < 1e-9 and controls:
        warnings.append(
            "RMSPE pré-tratamento muito baixo: doador pode estar over-ajustado."
        )

    base_result = {
        "treated_unit": treated_id,
        "post_att": _safe_float(base_post_att),
        "pre_rmspe": _safe_float(base_pre_rmspe),
        "post_rmspe": _safe_float(base_post_rmspe),
        "w_optimal": [_safe_float(v) for v in w],
        "donor_units": donor_ids,
        "n_units_used": len(w),
        "n_units_available": len(donor_ids),
    }
    augmented_result = {
        "treated_unit": treated_id,
        "post_att": _safe_float(aug_post_att),
        "pre_rmspe": _safe_float(base_pre_rmspe),
        "post_rmspe": _safe_float(aug_post_rmspe),
        "ridge_lambda": _safe_float(ridge_val),
        "w_optimal": [_safe_float(v) for v in w],
        "donor_units": donor_ids,
    }

    return {
        "base_scm_result": base_result,
        "augmented_result": augmented_result,
        "placebo_test": {
            "p_value": _safe_float(p_value),
            "in_time_placebos": in_time_placebos,
            "in_space_placebos": placebo_rows,
        },
        "event_study": event_study,
        "main_result": {
            "post_att": _safe_float(aug_post_att),
            "pre_rmspe": _safe_float(base_pre_rmspe),
            "post_rmspe": _safe_float(aug_post_rmspe),
            "w_optimal": [_safe_float(v) for v in w],
            "donor_units": donor_ids,
            "ridge_lambda": _safe_float(ridge_val),
        },
        "warnings": warnings,
    }
