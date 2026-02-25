"""Event Study dinâmico com Two-Way Fixed Effects (TWFE).

Implementa regressão com efeitos fixos de unidade e tempo, estimando
coeficientes por período relativo ao tratamento (leads/lags).

Forma do modelo:
    y_it = Σ_{k!=-1} β_k * 1[treat_i=1] * 1[rel_time_it=k]
           + α_i + λ_t + γX_it + ε_it

Onde o período de referência é ``k=-1`` (último ano pré-tratamento).
"""
from __future__ import annotations

from typing import Iterable

import pandas as pd
import statsmodels.formula.api as smf


def _rel_time_token(rel_time: int) -> str:
    """Gera token seguro para uso em nomes de coluna/formula."""
    return f"m{abs(rel_time)}" if rel_time < 0 else f"p{rel_time}"


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
    reference_period: int = -1,
) -> dict:
    """Estima event study com TWFE e retorna série de coeficientes dinâmica.

    Returns
    -------
    dict com:
      - ``coefficients``: list[dict] com rel_time/coef/se/t_stat/pvalue/IC/período
      - ``n_obs``: observações usadas na regressão
      - ``formula``: fórmula statsmodels utilizada
      - ``reference_period``: período omitido da regressão
      - ``method``: identificador metodológico
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
            "reference_period": reference_period,
            "method": "twfe_event_study",
        }

    rel_times = sorted(data["rel_time"].unique())
    rel_times_to_include = [t for t in rel_times if t != reference_period]
    term_map: dict[int, str] = {}

    for t in rel_times_to_include:
        col = f"treat_x_rel_time_{_rel_time_token(int(t))}"
        data[col] = data[treat_col] * (data["rel_time"] == t).astype(int)
        term_map[int(t)] = col

    interaction_terms = [term_map[int(t)] for t in rel_times_to_include]
    formula_parts = interaction_terms.copy()
    if controls:
        formula_parts.extend(controls)

    formula = (
        f"{outcome} ~ "
        + " + ".join(formula_parts)
        + f" + C({unit_col}) + C({time_col})"
    )

    cols_to_check = [outcome, unit_col, time_col, treat_col] + controls
    data = data.dropna(subset=cols_to_check).copy()
    cluster = cluster_col or unit_col

    try:
        model = smf.ols(formula, data=data).fit(
            cov_type="cluster",
            cov_kwds={"groups": data[cluster]},
        )
    except Exception as exc:
        return {
            "coefficients": [],
            "n_obs": len(data),
            "formula": formula,
            "reference_period": reference_period,
            "method": "twfe_event_study",
            "error": str(exc),
        }

    coef_data: list[dict] = []
    for t in rel_times:
        if t == reference_period:
            coef_data.append(
                {
                    "rel_time": int(t),
                    "coef": 0.0,
                    "se": 0.0,
                    "t_stat": 0.0,
                    "pvalue": 1.0,
                    "ci_lower": 0.0,
                    "ci_upper": 0.0,
                    "period": "reference",
                    "significant_10pct": False,
                }
            )
            continue

        term = term_map.get(int(t))
        if not term:
            continue
        if term not in model.params:
            continue

        coef = float(model.params[term])
        se = float(model.bse[term])
        pvalue = float(model.pvalues[term])
        coef_data.append(
            {
                "rel_time": int(t),
                "coef": coef,
                "se": se,
                "t_stat": float(model.tvalues[term]),
                "pvalue": pvalue,
                "ci_lower": coef - 1.96 * se,
                "ci_upper": coef + 1.96 * se,
                "period": "pre" if int(t) < 0 else "post",
                "significant_10pct": pvalue < 0.10,
            }
        )

    coef_data.sort(key=lambda r: r["rel_time"])

    return {
        "coefficients": coef_data,
        "n_obs": int(model.nobs),
        "formula": formula,
        "reference_period": reference_period,
        "method": "twfe_event_study",
    }
