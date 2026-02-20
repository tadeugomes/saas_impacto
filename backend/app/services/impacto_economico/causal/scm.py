"""Synthetic Control Method (SCM) simplificado para o Módulo 5."""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize


class SCMNotAvailableError(NotImplementedError):
    """Compatibilidade histórica com o PR-07.

    Mantém a assinatura pública esperada pelos testes e pela pipeline.
    O método agora é implementado e, portanto, essa exceção não é mais
    levantada internamente por padrão.
    """

    def __init__(self, message: str = "SCM disponível (implementação local).") -> None:
        super().__init__(message)


def _safe_float(value: Any) -> float | None:
    if isinstance(value, (float, int, np.floating, np.integer)):
        v = float(value)
        return v if math.isfinite(v) else None
    return None


def _rmspe(actual: np.ndarray, synthetic: np.ndarray) -> float | None:
    if actual.size == 0 or synthetic.size == 0:
        return None
    diff = actual - synthetic
    return float(np.sqrt(np.nanmean(np.square(diff)))) if np.isfinite(diff).any() else None


def _extract_unit_frames(
    df: pd.DataFrame,
    outcome: str,
    treatment_year: int,
    controls: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    work = df.copy()
    required_cols = {"id_municipio", "ano", outcome}
    missing = required_cols - set(work.columns)
    if missing:
        raise ValueError(f"Colunas ausentes no painel SCM: {sorted(missing)}")

    work["id_municipio"] = work["id_municipio"].astype(str)
    if "treated" not in work.columns:
        work["treated"] = 0
    if "post" not in work.columns:
        work["post"] = (work["ano"] >= treatment_year).astype(int)

    treated_ids = sorted(work.loc[work["treated"] == 1, "id_municipio"].unique().tolist())
    if not treated_ids:
        raise ValueError("SCM exige ao menos um município tratado (treated=1).")

    treated_id = treated_ids[0]
    treated_df = work.loc[work["id_municipio"] == treated_id].copy()
    controls_df = work.loc[work["treated"] == 0].copy()
    if controls_df.empty:
        raise ValueError("Não há candidatos a doador com treated=0 no painel.")

    if controls:
        missing_controls = [c for c in controls if c not in work.columns]
        if missing_controls:
            raise ValueError(f"Covariáveis ausentes para SCM: {missing_controls}")

    # Remove municípios tratados adicionais da pool de doadores
    if len(treated_ids) > 1:
        controls_df = controls_df[~controls_df["id_municipio"].isin(treated_ids)]

    return treated_df, controls_df, treated_id


def _prepare_predictor_matrix(
    treated_df: pd.DataFrame,
    control_df: pd.DataFrame,
    outcome: str,
    treatment_year: int,
    controls: list[str] | None = None,
) -> tuple[np.ndarray, np.ndarray, list[str], pd.Series, pd.DataFrame, pd.Series]:
    features = [outcome] + (controls or [])
    pre_treated = treated_df[treated_df["ano"] < treatment_year]
    pre_controls = control_df[control_df["ano"] < treatment_year]

    if pre_treated.empty:
        raise ValueError("Não há observações pré-tratamento do tratado para SCM.")
    if pre_controls.empty:
        raise ValueError("Não há observações pré-tratamento dos controles para SCM.")

    treated_vec = pre_treated[features].mean(axis=0).to_numpy(dtype=float)
    control_pivot = (
        pre_controls.pivot_table(index="id_municipio", values=features, aggfunc="mean")
    )
    control_pivot = control_pivot.dropna(subset=features)
    if control_pivot.empty:
        raise ValueError("Controles sem variabilidade suficiente para SCM.")

    control_ids = control_pivot.index.astype(str).tolist()
    x0 = control_pivot.to_numpy(dtype=float)
    return x0, treated_vec, control_ids, pre_treated[["ano", outcome]], control_pivot, pre_controls["ano"].rename("year")


def _solve_non_negative_weights(x0: np.ndarray, target: np.ndarray) -> np.ndarray:
    n = x0.shape[0]

    def objective(w: np.ndarray) -> float:
        y = w @ x0
        return float(np.mean((target - y) ** 2))

    w0 = np.repeat(1.0 / max(n, 1), n)
    bounds = [(0.0, 1.0)] * n
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    result = minimize(
        objective,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 200, "ftol": 1e-9},
    )

    if not result.success or result.x is None:
        # fallback robusto
        x0_t = np.array(x0).T
        w, *_ = np.linalg.lstsq(x0_t, target, rcond=None)
        w = np.clip(w, 0.0, None)
        total = float(np.sum(w))
        if total == 0:
            w = np.repeat(1.0 / n, n)
        else:
            w = w / total
        return w.astype(float)

    return np.asarray(result.x, dtype=float)


def _construct_synthetic_series(
    donor_panel: pd.DataFrame,
    outcome: str,
    donor_ids: list[str],
    weights: np.ndarray,
) -> pd.DataFrame:
    donor_matrix = donor_panel.pivot_table(index="ano", columns="id_municipio", values=outcome)
    donor_matrix = donor_matrix[donor_ids].copy()
    donor_matrix = donor_matrix.astype(float)
    used = donor_matrix.columns.tolist()
    used_weights = weights[: len(used)]
    donor_matrix["synthetic"] = donor_matrix @ used_weights
    return donor_matrix[["synthetic"]].reset_index()


def _event_study(
    treated_df: pd.DataFrame,
    synthetic_df: pd.DataFrame,
    outcome: str,
) -> list[dict[str, Any]]:
    merged = treated_df[["ano", outcome]].merge(synthetic_df, on="ano", how="left")
    if merged.empty:
        return []
    merged = merged.sort_values("ano").reset_index(drop=True)
    effect = merged[outcome].astype(float) - merged["synthetic"].astype(float)
    merged["effect"] = effect
    return [
        {
            "year": int(row["ano"]),
            "effect": _safe_float(row["effect"]),
            "treated": _safe_float(row[outcome]),
            "synthetic": _safe_float(row["synthetic"]),
        }
        for _, row in merged.iterrows()
    ]


def _in_space_placebos(
    treated_df: pd.DataFrame,
    control_df: pd.DataFrame,
    outcome: str,
    treatment_year: int,
    controls: list[str] | None,
    n_placebos: int,
    treated_ratio: float | None = None,
) -> tuple[list[dict[str, Any]], float | None]:
    donor_units = control_df["id_municipio"].astype(str).unique().tolist()
    if n_placebos <= 0 or not donor_units:
        return [], None

    candidates = donor_units[: min(n_placebos, len(donor_units))]
    placebo_rows: list[dict[str, Any]] = []
    ratios: list[float] = []

    base_pool = pd.concat([treated_df, control_df], ignore_index=True)
    for donor in candidates:
        pseudo_df = base_pool.copy()
        pseudo_df["treated"] = (pseudo_df["id_municipio"].astype(str) == donor).astype(int)
        pseudo_treated = pseudo_df[pseudo_df["id_municipio"] == donor].copy()
        pseudo_controls = pseudo_df[pseudo_df["id_municipio"] != donor].copy()

        try:
            x0, target, placebo_ids, _, _, _ = _prepare_predictor_matrix(
                pseudo_treated,
                pseudo_controls,
                outcome=outcome,
                treatment_year=treatment_year,
                controls=controls,
            )
            w = _solve_non_negative_weights(x0, target)
            synth = _construct_synthetic_series(
                donor_panel=pseudo_controls[["id_municipio", "ano", outcome]].copy(),
                outcome=outcome,
                donor_ids=placebo_ids,
                weights=w,
            )
        except Exception:
            continue

        pseudo_pre = pseudo_treated[pseudo_treated["ano"] < treatment_year].set_index("ano")[outcome]
        pseudo_post = pseudo_treated[pseudo_treated["ano"] >= treatment_year].set_index("ano")[outcome]
        synth_pre = synth.set_index("ano").loc[pseudo_pre.index]["synthetic"]
        synth_post = synth.set_index("ano").loc[pseudo_post.index]["synthetic"]

        pre_rmspe = _rmspe(
            pseudo_pre.to_numpy(dtype=float),
            synth_pre.to_numpy(dtype=float),
        )
        post_rmspe = _rmspe(
            pseudo_post.to_numpy(dtype=float),
            synth_post.to_numpy(dtype=float),
        )
        ratio = None
        if pre_rmspe not in (None, 0) and pre_rmspe is not None:
            ratio = float(post_rmspe / pre_rmspe) if post_rmspe is not None else None
            if ratio is not None:
                ratios.append(ratio)

        placebo_rows.append(
            {
                "unit": donor,
                "pre_rmspe": pre_rmspe,
                "post_rmspe": post_rmspe,
                "ratio": ratio,
                "n_donors": len(placebo_ids),
            }
        )

    p_value = None
    if ratios and treated_ratio is not None and math.isfinite(treated_ratio):
        p_value = float(sum(1 for r in ratios if r >= treated_ratio) / len(ratios))
    return placebo_rows, p_value


def run_scm(
    df: pd.DataFrame,
    outcome: str,
    treatment_year: int,
    controls: list[str] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Executa SCM e retorna o `main_result`."""
    result = run_scm_with_diagnostics(
        df=df,
        outcome=outcome,
        treatment_year=treatment_year,
        controls=controls,
        n_placebos=0,
    )
    return result.get("main_result", {})


def run_scm_with_diagnostics(
    df: pd.DataFrame,
    outcome: str,
    treatment_year: int,
    controls: list[str] | None = None,
    n_placebos: int = 50,
    **kwargs: Any,
) -> dict[str, Any]:
    """Executa SCM com placebo e série de evento."""
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
                "treated_unit": None,
                "post_att": None,
                "pre_rmspe": None,
                "post_rmspe": None,
                "ratio_post_pre": None,
                "w_optimal": [],
                "donor_units": [],
            },
            "placebo_test": {"p_value": None, "in_space_placebos": []},
            "event_study": [],
            "main_result": {
                "post_att": None,
                "pre_rmspe": None,
                "post_rmspe": None,
                "ratio_post_pre": None,
                "w_optimal": [],
                "donor_units": [],
            },
            "warnings": [str(exc)],
            "treated_unit": None,
        }

    x0, target, donor_ids, pre_treated, _control_agg, _ = _prepare_predictor_matrix(
        treated_df=treated_df,
        control_df=control_df,
        outcome=outcome,
        treatment_year=treatment_year,
        controls=controls,
    )

    weights = _solve_non_negative_weights(x0=x0, target=target)
    synthetic_df = _construct_synthetic_series(
        donor_panel=control_df[["id_municipio", "ano", outcome]].copy(),
        outcome=outcome,
        donor_ids=donor_ids,
        weights=weights,
    )

    treated_series = treated_df[["ano", outcome]].sort_values("ano").copy()
    pre_mask = treated_series["ano"] < treatment_year
    post_mask = treated_series["ano"] >= treatment_year
    synth = synthetic_df.set_index("ano")
    pre_actual = treated_series.loc[pre_mask].set_index("ano")[outcome]
    post_actual = treated_series.loc[post_mask].set_index("ano")[outcome]
    pre_synth = synth.loc[pre_actual.index].squeeze()
    post_synth = synth.loc[post_actual.index].squeeze()

    pre_rmspe = _rmspe(pre_actual.to_numpy(dtype=float), pre_synth.to_numpy(dtype=float))
    post_rmspe = _rmspe(post_actual.to_numpy(dtype=float), post_synth.to_numpy(dtype=float))
    ratio_post_pre = None
    if pre_rmspe not in (None, 0.0) and pre_rmspe is not None and post_rmspe is not None:
        ratio_post_pre = float(post_rmspe / pre_rmspe) if pre_rmspe > 0 else None

    if post_actual.size:
        post_att = float((post_actual - post_synth).mean())
    else:
        post_att = None

    if post_rmspe is not None and pre_rmspe is not None and ratio_post_pre is not None and ratio_post_pre > 2:
        warnings.append("RMSPE pós-tratamento ficou muito acima do pré (possível má qualidade do sintético).")

    placebo_rows, p_value = _in_space_placebos(
        treated_df=treated_df,
        control_df=control_df,
        outcome=outcome,
        treatment_year=treatment_year,
        controls=controls,
        n_placebos=n_placebos,
        treated_ratio=ratio_post_pre,
    )

    event_study = _event_study(
        treated_df=treated_df,
        synthetic_df=synthetic_df,
        outcome=outcome,
    )

    base_result = {
        "treated_unit": treated_id,
        "post_att": post_att,
        "pre_rmspe": pre_rmspe,
        "post_rmspe": post_rmspe,
        "ratio_post_pre": ratio_post_pre,
        "w_optimal": [_safe_float(v) for v in weights],
        "donor_units": donor_ids,
        "n_units_used": len(weights),
        "n_units_available": len(donor_ids),
        "warnings": warnings,
    }

    return {
        "base_result": base_result,
        "placebo_test": {
            "p_value": _safe_float(p_value),
            "in_space_placebos": placebo_rows,
        },
        "event_study": event_study,
        "main_result": {
            "post_att": post_att,
            "pre_rmspe": pre_rmspe,
            "post_rmspe": post_rmspe,
            "ratio_post_pre": ratio_post_pre,
            "w_optimal": [_safe_float(v) for v in weights],
            "donor_units": donor_ids,
        },
        "warnings": warnings,
    }
