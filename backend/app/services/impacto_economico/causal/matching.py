"""Matching de controles para métodos baseados em unidade-sintética."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.db.bigquery.client import BigQueryClient
from app.db.bigquery.marts.module5 import MART_IMPACTO_ECONOMICO_FQTN


DEFAULT_MATCHING_FEATURES = [
    "pib_per_capita",
    "populacao",
    "empregos_totais",
    "empregos_portuarios",
    "comercio_total_dolar",
    "toneladas_antaq_oficial",
]


def _safe_scale(values: pd.Series) -> pd.Series:
    std = float(values.std())
    if std == 0 or np.isnan(std):
        return values
    return (values - float(values.mean())) / std


def _scope_where(scope: str, treated_ids: list[str]) -> str:
    if scope != "state" or not treated_ids:
        return ""
    states = sorted({str(x)[:2] for x in treated_ids if str(x).strip()})
    if not states:
        return ""
    quoted = ", ".join(f"'{s}'" for s in states)
    return f"AND SUBSTR(id_municipio, 1, 2) IN ({quoted})"


def _matching_query(
    treated_ids: list[str],
    ano_inicio: int,
    ano_fim: int,
    scope: str,
) -> str:
    scope_where = _scope_where(scope, treated_ids)
    features = ", ".join(DEFAULT_MATCHING_FEATURES)
    return f"""
    SELECT
        CAST(id_municipio AS STRING) AS id_municipio,
        CAST(ano AS INT64) AS ano,
        {features}
    FROM {MART_IMPACTO_ECONOMICO_FQTN}
    WHERE ano BETWEEN {ano_inicio} AND {ano_fim}
      {scope_where}
      AND id_municipio IS NOT NULL
    """


def _prepare_panel(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["id_municipio", "ano"] + DEFAULT_MATCHING_FEATURES)
    df = pd.DataFrame(rows)
    df["id_municipio"] = df["id_municipio"].astype(str)
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    for col in DEFAULT_MATCHING_FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["id_municipio", "ano"]).copy()


def _summarize_balance(
    treated_profile: dict[str, float],
    selected_profiles: pd.DataFrame,
) -> dict[str, dict[str, float]]:
    selected_mean = (
        selected_profiles.mean().to_dict()
        if not selected_profiles.empty else {}
    )
    treated_mean = {k: float(v) for k, v in treated_profile.items() if pd.notna(v)}
    selected_mean = {
        k: float(v) for k, v in selected_mean.items() if pd.notna(v)
    }
    return {
        "treated": treated_mean,
        "selected_controls": selected_mean,
        "n_features": len(DEFAULT_MATCHING_FEATURES),
    }


async def suggest_control_matches(
    treated_ids: list[str],
    treatment_year: int,
    scope: str = "state",
    n_controls: int = 20,
    ano_inicio: int = 2010,
    ano_fim: int = 2023,
    features: list[str] | None = None,
) -> dict[str, Any]:
    """Sugere controles para SCM via distância padronizada no pré-tratamento."""
    if treatment_year <= ano_inicio:
        raise ValueError("treatment_year deve ser maior que ano_inicio.")
    if n_controls <= 0:
        raise ValueError("n_controls deve ser positivo.")

    feature_cols = features or DEFAULT_MATCHING_FEATURES
    missing = [f for f in feature_cols if f not in DEFAULT_MATCHING_FEATURES]
    if missing:
        raise ValueError(f"Feature inválida para matching: {missing}")

    treated_ids = [str(x) for x in treated_ids]
    if not treated_ids:
        raise ValueError("É necessário informar pelo menos um tratado.")

    bq = BigQueryClient()
    rows = await bq.execute_query(
        _matching_query(
            treated_ids=treated_ids,
            ano_inicio=ano_inicio,
            ano_fim=min(ano_fim, treatment_year - 1),
            scope=scope,
        )
    )
    df = _prepare_panel(rows)

    if df.empty:
        raise ValueError(
            "Não foi possível carregar painel para matching. Verifique o mart ou o período."
        )

    pre = df[df["ano"] < treatment_year].copy()
    if pre.empty:
        raise ValueError("Sem observações pré-tratamento para calcular distância.")

    treated_profile = (
        pre.loc[pre["id_municipio"].isin(treated_ids), feature_cols]
        .mean()
    )
    if treated_profile.isnull().all():
        raise ValueError(
            "Municípios tratados não possuem features suficientes no período pré-tratamento."
        )
    candidates = pre.loc[~pre["id_municipio"].isin(treated_ids), ["id_municipio"] + feature_cols].copy()
    candidates = candidates.groupby("id_municipio").mean()

    if candidates.empty:
        raise ValueError("Nenhum controle candidato encontrado após filtro.")

    # padronização robusta: z-score por feature
    scaled = candidates[feature_cols].copy()
    scaled = scaled.apply(_safe_scale)
    target = treated_profile[feature_cols].astype(float)
    target_scaled = _safe_scale(target)

    common_cols = target_scaled.index.tolist()
    diff = (scaled[common_cols] - target_scaled[common_cols]).fillna(0.0)
    distances = np.linalg.norm(diff.to_numpy(), axis=1)
    nrm = float(np.max(distances)) or 1.0
    similarities = 1.0 - (distances / max(nrm, 1e-12))
    ranked = (
        pd.DataFrame(
            {
                "id_municipio": candidates.index.astype(str),
                "distance": distances,
                "similarity_score": similarities,
            }
        )
        .sort_values(["distance", "id_municipio"])
        .head(n_controls)
        .reset_index(drop=True)
    )

    suggested = [
        {
            "id_municipio": str(row["id_municipio"]),
            "distance": _safe_scalar(row["distance"]),
            "similarity_score": _safe_scalar(row["similarity_score"]),
            "is_treated": False,
        }
        for _, row in ranked.iterrows()
    ]

    return {
        "suggested_controls": suggested,
        "n_treated": len(set(treated_ids)),
        "n_candidates": int(len(candidates)),
        "scope": scope,
        "treatment_year": treatment_year,
        "features": feature_cols,
        "balance_table": _summarize_balance(
            treated_profile=treated_profile.to_dict(),
            selected_profiles=candidates.loc[
                candidates.index.isin(ranked["id_municipio"].tolist()),
                feature_cols,
            ],
        ),
    }


def _safe_scalar(value: Any) -> float | None:
    if isinstance(value, (int, float, np.integer, np.floating)):
        v = float(value)
        return v if np.isfinite(v) else None
    return None
