"""Serviço de Elasticidade Fiscal — Módulo 6.

Estima a relação entre tonelagem movimentada e tributos pagos pelos portos
(ISS municipal e tributos federais) usando regressão OLS log-log com
efeitos fixos de porto.

Metodologia:
    ln(tributo_it) = alpha_i + beta * ln(tonelagem_it) + epsilon_it
    onde i = porto, t = ano, alpha_i = efeito fixo de porto.

    Erros padrão heteroscedasticidade-robustos (HC3).
    Amostra: 2018-2024. Outliers filtrados (trib > 500.000 R$ mil).

Limitação atual:
    ~8 obs/porto → não confiável para regressão port-específica.
    Usar elasticidade média do setor aplicada ao baseline real do porto.
"""
from __future__ import annotations

import logging
import math
from typing import Optional

import pandas as pd
import numpy as np

from app.data.tributos_portos import TRIBUTOS_PORTOS
from app.data.porto_municipio_ibge import PORTO_MUNICIPIO_MAP

logger = logging.getLogger(__name__)

# Threshold de outlier para tributos federais (R$ mil)
_OUTLIER_THRESHOLD = 500_000.0


def _build_tributos_df() -> pd.DataFrame:
    """Constrói DataFrame limpo do fixture sem tonelagem (sem BigQuery)."""
    rows = []
    for rec in TRIBUTOS_PORTOS:
        mapping = PORTO_MUNICIPIO_MAP.get(rec["porto"])
        if not mapping:
            continue
        rows.append({
            "porto": rec["porto"],
            "uf": rec["uf"],
            "id_municipio": mapping["id_municipio"],
            "nome_municipio": mapping["nome"],
            "ano": rec["ano"],
            "iss_r_mil": rec.get("iss_r_mil"),
            "trib_municipais_r_mil": rec.get("trib_municipais_r_mil"),
            "trib_federais_r_mil": rec.get("trib_federais_r_mil"),
        })
    return pd.DataFrame(rows)


def build_panel_df(bq_client=None) -> pd.DataFrame:
    """Constrói painel porto × ano com tributos e tonelagem.

    Tenta buscar tonelagem do BigQuery via bq_client.
    Se bq_client=None ou falhar, retorna painel sem tonelagem
    (regressão não será possível, mas composição/baseline funcionam).
    """
    df_trib = _build_tributos_df()

    if bq_client is None:
        logger.warning("fiscal_elasticity: bq_client=None, painel sem tonelagem.")
        return df_trib

    try:
        from app.db.bigquery.queries.module6_public_finance import (
            MART_IMPACTO_ECONOMICO_FQTN,
        )
        ids = df_trib["id_municipio"].dropna().unique().tolist()
        ids_str = ", ".join(f"'{i}'" for i in ids)
        sql = f"""
            SELECT
                CAST(id_municipio AS STRING) AS id_municipio,
                CAST(ano AS INT64) AS ano,
                tonelagem_antaq_oficial AS tonelagem_r_mil_ton
            FROM {MART_IMPACTO_ECONOMICO_FQTN}
            WHERE id_municipio IN ({ids_str})
              AND ano BETWEEN 2018 AND 2024
        """
        rows = list(bq_client.query(sql))
        df_ton = pd.DataFrame([dict(r) for r in rows])
        df_ton["id_municipio"] = df_ton["id_municipio"].astype(str)
        df_ton["ano"] = df_ton["ano"].astype(int)
        df_merged = df_trib.merge(df_ton, on=["id_municipio", "ano"], how="left")
        return df_merged
    except Exception as exc:
        logger.warning("fiscal_elasticity: falha ao buscar tonelagem BigQuery: %s", exc)
        return df_trib


def _filter_regression_sample(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """Filtra amostra válida para regressão: sem nulos, sem outliers, tonelagem > 0."""
    required = ["porto", "ano", "tonelagem_r_mil_ton", target_col]
    if not all(c in df.columns for c in required):
        return pd.DataFrame()

    sample = df[required].dropna()
    sample = sample[sample["tonelagem_r_mil_ton"] > 0]
    sample = sample[sample[target_col] > 0]
    # Filtrar outliers
    sample = sample[sample[target_col] < _OUTLIER_THRESHOLD]
    # Log para fins de auditoria
    logger.info(
        "fiscal_elasticity: amostra regressão %s — %d obs de %d portos",
        target_col,
        len(sample),
        sample["porto"].nunique(),
    )
    return sample


def compute_elasticity_panel(df: pd.DataFrame) -> dict:
    """Roda regressões log-log com FE de porto para ISS e tributos federais.

    Retorna dict com 'municipal' e 'federal', cada um com:
        beta, ci_lower, ci_upper, r2, p_value, n_obs, n_portos
    Retorna None para cada dimensão se amostra insuficiente (< 10 obs).
    """
    import statsmodels.formula.api as smf

    results: dict = {"municipal": None, "federal": None}
    configs = [
        ("municipal", "iss_r_mil"),
        ("federal", "trib_federais_r_mil"),
    ]

    for key, col in configs:
        sample = _filter_regression_sample(df, col)
        if len(sample) < 10:
            logger.warning(
                "fiscal_elasticity: amostra insuficiente para %s (n=%d)", key, len(sample)
            )
            continue

        sample = sample.copy()
        sample["log_trib"] = np.log(sample[col])
        sample["log_ton"] = np.log(sample["tonelagem_r_mil_ton"])

        try:
            model = smf.ols(
                "log_trib ~ log_ton + C(porto)",
                data=sample,
            ).fit(cov_type="HC3")

            beta = float(model.params.get("log_ton", float("nan")))
            ci = model.conf_int().loc["log_ton"]
            p_value = float(model.pvalues.get("log_ton", float("nan")))
            r2 = float(model.rsquared)

            results[key] = {
                "beta": round(beta, 4),
                "ci_lower": round(float(ci.iloc[0]), 4),
                "ci_upper": round(float(ci.iloc[1]), 4),
                "r2": round(r2, 4),
                "p_value": round(p_value, 6),
                "n_obs": len(sample),
                "n_portos": int(sample["porto"].nunique()),
            }
        except Exception as exc:
            logger.error("fiscal_elasticity: erro na regressão %s: %s", key, exc)

    return results


def get_scatter_data(df: pd.DataFrame) -> list[dict]:
    """Retorna pontos para scatter chart: um por porto-ano com ISS e tonelagem."""
    if "tonelagem_r_mil_ton" not in df.columns:
        return []

    cols = ["porto", "uf", "ano", "tonelagem_r_mil_ton", "iss_r_mil", "trib_federais_r_mil"]
    available = [c for c in cols if c in df.columns]
    sample = df[available].dropna(subset=["tonelagem_r_mil_ton", "iss_r_mil"])
    sample = sample[sample["tonelagem_r_mil_ton"] > 0]
    sample = sample[sample["iss_r_mil"] > 0]
    sample = sample[sample["iss_r_mil"] < _OUTLIER_THRESHOLD]

    points = []
    for _, row in sample.iterrows():
        point: dict = {
            "porto": row["porto"],
            "uf": row["uf"],
            "ano": int(row["ano"]),
            "tonelagem_m_ton": round(float(row["tonelagem_r_mil_ton"]) / 1000, 3),
            "iss_r_mi": round(float(row["iss_r_mil"]) / 1000, 3),
        }
        fed = row.get("trib_federais_r_mil")
        if fed is not None and not math.isnan(float(fed)) and float(fed) < _OUTLIER_THRESHOLD:
            point["trib_federais_r_mi"] = round(float(fed) / 1000, 3)
        points.append(point)
    return points


def get_composition_data(df: pd.DataFrame) -> list[dict]:
    """Retorna split municipal/federal por porto (médias dos anos disponíveis)."""
    group_cols = ["porto", "uf"]
    needed = ["trib_municipais_r_mil", "trib_federais_r_mil"]
    available = [c for c in needed if c in df.columns]
    if not available:
        return []

    sample = df[group_cols + available].dropna(subset=available)
    # Filtrar outliers
    for col in available:
        sample = sample[sample[col] < _OUTLIER_THRESHOLD]

    grouped = (
        sample.groupby(group_cols)[available]
        .mean()
        .reset_index()
    )

    composition = []
    for _, row in grouped.iterrows():
        mun = float(row.get("trib_municipais_r_mil", 0) or 0)
        fed = float(row.get("trib_federais_r_mil", 0) or 0)
        total = mun + fed
        if total == 0:
            continue
        composition.append({
            "porto": row["porto"],
            "uf": row["uf"],
            "municipal_r_mi": round(mun / 1000, 3),
            "federal_r_mi": round(fed / 1000, 3),
            "total_r_mi": round(total / 1000, 3),
            "pct_municipal": round(mun / total * 100, 1),
            "pct_federal": round(fed / total * 100, 1),
        })

    return sorted(composition, key=lambda x: x["total_r_mi"], reverse=True)


def get_portos_disponiveis(df: pd.DataFrame) -> list[str]:
    """Retorna lista de portos com pelo menos 1 ano de ISS disponível."""
    if "iss_r_mil" not in df.columns:
        return []
    valid = df[df["iss_r_mil"].notna() & (df["iss_r_mil"] > 0)]
    return sorted(valid["porto"].unique().tolist())


def get_baseline_for_porto(df: pd.DataFrame, porto: str) -> dict:
    """Retorna baseline (ano mais recente) de ISS e trib_federais para um porto."""
    porto_df = df[df["porto"] == porto].sort_values("ano", ascending=False)
    for _, row in porto_df.iterrows():
        iss = row.get("iss_r_mil")
        fed = row.get("trib_federais_r_mil")
        if iss is not None and not math.isnan(float(iss)) and iss > 0:
            return {
                "porto": porto,
                "ano_referencia": int(row["ano"]),
                "baseline_municipal_r_mi": round(float(iss) / 1000, 3),
                "baseline_federal_r_mi": round(float(fed) / 1000, 3) if (fed is not None and not math.isnan(float(fed))) else None,
            }
    return {"porto": porto, "ano_referencia": None, "baseline_municipal_r_mi": None, "baseline_federal_r_mi": None}


def simulate_fiscal_impact(
    porto: Optional[str],
    shock_pct: float,
    elasticidades: dict,
    df: pd.DataFrame,
) -> dict:
    """Projeta impacto fiscal de um choque de tonelagem.

    Se porto=None ou sem dados, usa médias do setor como baseline.
    Aplica: delta = baseline * ((1 + shock/100)^beta - 1)
    """
    # Determinar baseline
    if porto and porto != "__media__":
        baseline_info = get_baseline_for_porto(df, porto)
    else:
        # Média do setor: média simples de todos os portos com ISS
        valid_iss = df[df["iss_r_mil"].notna() & (df["iss_r_mil"] > 0) & (df["iss_r_mil"] < _OUTLIER_THRESHOLD)]
        valid_fed = df[df["trib_federais_r_mil"].notna() & (df["trib_federais_r_mil"] > 0) & (df["trib_federais_r_mil"] < _OUTLIER_THRESHOLD)]
        baseline_info = {
            "porto": "Média do setor",
            "ano_referencia": None,
            "baseline_municipal_r_mi": round(valid_iss["iss_r_mil"].mean() / 1000, 3) if len(valid_iss) > 0 else None,
            "baseline_federal_r_mi": round(valid_fed["trib_federais_r_mil"].mean() / 1000, 3) if len(valid_fed) > 0 else None,
        }

    def project(baseline_val, elast_key):
        if baseline_val is None:
            return None, None, None
        el = elasticidades.get(elast_key)
        if not el:
            return None, None, None
        beta = el["beta"]
        ci_lo = el["ci_lower"]
        ci_hi = el["ci_upper"]
        multiplier = (1 + shock_pct / 100)
        delta = baseline_val * (multiplier**beta - 1)
        delta_lo = baseline_val * (multiplier**ci_lo - 1)
        delta_hi = baseline_val * (multiplier**ci_hi - 1)
        return (
            round(delta, 3),
            round(min(delta_lo, delta_hi), 3),
            round(max(delta_lo, delta_hi), 3),
        )

    delta_mun, ci_mun_lo, ci_mun_hi = project(baseline_info["baseline_municipal_r_mi"], "municipal")
    delta_fed, ci_fed_lo, ci_fed_hi = project(baseline_info["baseline_federal_r_mi"], "federal")

    el_mun = elasticidades.get("municipal", {})
    nota = (
        f"Baseline de {baseline_info['porto']}"
        + (f" ({baseline_info['ano_referencia']})" if baseline_info.get("ano_referencia") else "")
        + ", elasticidade da média do setor"
        + (f" (β={el_mun.get('beta', '—')}, n={el_mun.get('n_obs', '—')} obs)" if el_mun else "")
        + ". Análise associativa, não causal. Fonte: DFs dos operadores portuários 2018-2024."
    )

    return {
        "porto": baseline_info["porto"],
        "ano_referencia": baseline_info.get("ano_referencia"),
        "shock_pct": shock_pct,
        "baseline_municipal_r_mi": baseline_info["baseline_municipal_r_mi"],
        "baseline_federal_r_mi": baseline_info["baseline_federal_r_mi"],
        "delta_municipal_r_mi": delta_mun,
        "delta_federal_r_mi": delta_fed,
        "delta_municipal_ci": [ci_mun_lo, ci_mun_hi] if ci_mun_lo is not None else None,
        "delta_federal_ci": [ci_fed_lo, ci_fed_hi] if ci_fed_lo is not None else None,
        "elasticidade_usada": "media_setor",
        "nota": nota,
    }
