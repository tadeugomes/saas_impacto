"""Comparação e triangulação entre métodos causais.

Portado de new_impacto/src/causal/comparison.py.
Adaptação: ``create_comparison_report`` não salva CSV quando ``output_path``
é None (comportamento mantido); ``comparison_table`` é retornado como
``list[dict]`` (serializável) em vez de DataFrame.
"""
from __future__ import annotations

from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# compare_method_results
# ---------------------------------------------------------------------------


def compare_method_results(
    did_result: dict[str, Any] | None = None,
    scm_result: dict[str, Any] | None = None,
    iv_result: dict[str, Any] | None = None,
    outcome: str = "outcome",
) -> dict[str, Any]:
    """Compara estimativas causais entre DiD, SCM e IV.

    Parameters
    ----------
    did_result:
        Saída de ``run_did()`` ou ``run_did_with_diagnostics()``.
    scm_result:
        Saída de um Synthetic Control (opcional).
    iv_result:
        Saída de ``run_iv_2sls()`` ou ``run_iv_with_diagnostics()``.
    outcome:
        Nome da variável de resultado para relatório.

    Returns
    -------
    dict com chaves:
        comparison_table (list[dict]), consistency_assessment,
        recommended_estimate, interpretation_notes, methods_available, outcome
    """
    methods_data: list[dict] = []
    methods_available: list[str] = []

    # ── DiD ──────────────────────────────────────────────────────────────────
    if did_result is not None:
        methods_available.append("DiD")
        mr = did_result.get("main_result", did_result)
        did_coef = mr.get("coef", np.nan)
        did_se = mr.get("std_err", np.nan)
        did_pval = mr.get("p_value", np.nan)
        ci_lo = did_coef - 1.96 * did_se if not np.isnan(did_se) else np.nan
        ci_hi = did_coef + 1.96 * did_se if not np.isnan(did_se) else np.nan
        methods_data.append(
            {
                "Method": "DiD",
                "Estimate": did_coef,
                "SE": did_se,
                "CI_Lower": ci_lo,
                "CI_Upper": ci_hi,
                "P_Value": did_pval,
                "Significant": "Yes" if not np.isnan(did_pval) and did_pval < 0.05 else "No",
                "Notes": "Two-way FE",
            }
        )

    # ── SCM ──────────────────────────────────────────────────────────────────
    if scm_result is not None:
        methods_available.append("SCM")
        if "base_result" in scm_result:
            br = scm_result["base_result"]
            scm_att = getattr(br, "post_att", None) or br.get("post_att", np.nan)
        elif "augmented_result" in scm_result:
            ar = scm_result["augmented_result"]
            scm_att = getattr(ar, "post_att", None) or ar.get("post_att", np.nan)
        elif hasattr(scm_result, "post_att"):
            scm_att = scm_result.post_att
        else:
            scm_att = scm_result.get("post_att", np.nan)

        pt = scm_result.get("placebo_test", {}) if isinstance(scm_result, dict) else {}
        scm_pval = pt.get("p_value", np.nan)
        scm_sig = "Yes" if not np.isnan(scm_pval) and scm_pval < 0.05 else "N/A"
        methods_data.append(
            {
                "Method": "SCM",
                "Estimate": scm_att,
                "SE": np.nan,
                "CI_Lower": np.nan,
                "CI_Upper": np.nan,
                "P_Value": scm_pval,
                "Significant": scm_sig,
                "Notes": "Via placebo test" if not np.isnan(scm_pval) else "No SE/p-value",
            }
        )

    # ── IV ────────────────────────────────────────────────────────────────────
    if iv_result is not None:
        methods_available.append("IV")
        mr = iv_result.get("main_result", iv_result)
        # Estrutura aninhada do Panel IV
        if isinstance(mr, dict) and "main_result" in mr:
            mr = mr["main_result"]
        iv_coef = mr.get("coef", np.nan)
        iv_se = mr.get("std_err", np.nan)
        iv_pval = mr.get("p_value", np.nan)
        ci_lo = iv_coef - 1.96 * iv_se if not np.isnan(iv_se) else np.nan
        ci_hi = iv_coef + 1.96 * iv_se if not np.isnan(iv_se) else np.nan
        methods_data.append(
            {
                "Method": "IV",
                "Estimate": iv_coef,
                "SE": iv_se,
                "CI_Lower": ci_lo,
                "CI_Upper": ci_hi,
                "P_Value": iv_pval,
                "Significant": "Yes" if not np.isnan(iv_pval) and iv_pval < 0.05 else "No",
                "Notes": "2SLS",
            }
        )

    # ── Avaliação de consistência ─────────────────────────────────────────────
    estimates = [
        r["Estimate"] for r in methods_data if not np.isnan(r.get("Estimate", np.nan))
    ]
    signs = [np.sign(e) for e in estimates]

    if not estimates:
        consistency = "No valid estimates available"
        recommended = "Unable to provide recommendation"
        interpretation = "No valid results to compare"
    elif len(estimates) == 1:
        consistency = f"Only one method available: {methods_available[0]}"
        recommended = f"Single estimate: {estimates[0]:.4f}"
        interpretation = (
            "Cannot assess consistency with only one method. "
            "Consider implementing additional identification strategies."
        )
    else:
        sign_ok = all(s == signs[0] for s in signs)
        est_std = float(np.std(estimates))
        est_mean = float(np.mean(estimates))
        cv = abs(est_std / est_mean) if est_mean != 0 else float("inf")

        sign_msg = "✓ All methods agree on direction" if sign_ok else "✗ Methods disagree on direction"
        mag_msg = (
            f"✓ Low variation (CV={cv:.2%})"
            if cv < 0.25
            else (
                f"⚠ Moderate variation (CV={cv:.2%})"
                if cv < 0.50
                else f"✗ High variation (CV={cv:.2%})"
            )
        )
        sig_methods = [r["Method"] for r in methods_data if r.get("Significant") == "Yes"]
        pwr_msg = (
            "✓ All methods statistically significant"
            if len(sig_methods) == len(methods_data)
            else (
                f"⚠ Some methods significant ({len(sig_methods)}/{len(methods_data)}): {', '.join(sig_methods)}"
                if sig_methods
                else "✗ No methods statistically significant"
            )
        )
        consistency = f"{sign_msg}\n{mag_msg}\n{pwr_msg}"

        # Estimativa recomendada
        did_valid = False
        if did_result is not None:
            did_warns = (did_result.get("warnings", []) if isinstance(did_result, dict) else [])
            did_valid = not any("REJECT" in w or "FAIL" in w for w in did_warns)

        if did_valid and "DiD" in methods_available:
            did_est = next(r["Estimate"] for r in methods_data if r["Method"] == "DiD")
            recommended = f"DiD: {did_est:.4f} (passed diagnostics)"
        elif "IV" in methods_available:
            iv_row = next(r for r in methods_data if r["Method"] == "IV")
            if iv_row.get("Significant") == "Yes":
                recommended = f"IV: {iv_row['Estimate']:.4f} (statistically significant)"
            else:
                recommended = (
                    f"Range: [{min(estimates):.4f}, {max(estimates):.4f}] (IV not significant)"
                )
        else:
            recommended = f"SCM: Mean estimate = {est_mean:.4f}"

        if sign_ok and cv < 0.25:
            interpretation = (
                f"Strong consistency across methods. {outcome} shows a "
                f"{'positive' if signs[0] > 0 else 'negative'} effect with low variation."
            )
        elif sign_ok:
            interpretation = (
                f"Methods agree on direction ({'positive' if signs[0] > 0 else 'negative'}) "
                "but vary in magnitude. Consider reporting range of estimates."
            )
        else:
            interpretation = (
                "Methods disagree. Review validity of each method's assumptions. "
                f"Effect on {outcome} remains uncertain."
            )

    # NaN → None para serialização limpa
    def _clean(row: dict) -> dict:
        return {
            k: (None if isinstance(v, float) and np.isnan(v) else v)
            for k, v in row.items()
        }

    return {
        "comparison_table": [_clean(r) for r in methods_data],
        "consistency_assessment": consistency,
        "recommended_estimate": recommended,
        "interpretation_notes": interpretation,
        "methods_available": methods_available,
        "outcome": outcome,
    }


# ---------------------------------------------------------------------------
# create_comparison_report
# ---------------------------------------------------------------------------


def create_comparison_report(
    results_by_outcome: dict[str, dict[str, Any]],
    state: str = "State",
    output_path: str | None = None,
) -> list[dict]:
    """Relatório de comparação para múltiplos outcomes e métodos.

    Parameters
    ----------
    results_by_outcome:
        ``{outcome: {'did': ..., 'scm': ..., 'iv': ...}}``
    state:
        Identificador do estado para o relatório.
    output_path:
        Caminho opcional para salvar CSV (não-obrigatório no SaaS).

    Returns
    -------
    list[dict] — linhas do relatório (serializable).
    """
    all_rows: list[dict] = []

    for outcome, method_results in results_by_outcome.items():
        comparison = compare_method_results(
            did_result=method_results.get("did"),
            scm_result=method_results.get("scm"),
            iv_result=method_results.get("iv"),
            outcome=outcome,
        )
        for row in comparison["comparison_table"]:
            all_rows.append({"State": state, "Outcome": outcome, **row})

    if output_path:
        try:
            import pandas as pd  # optional for CSV export

            pd.DataFrame(all_rows).to_csv(output_path, index=False)
        except Exception:
            pass  # não quebra se pandas/path falhar

    return all_rows
