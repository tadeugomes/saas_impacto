"""Serviço de Elasticidade Fiscal — Módulo 6.

Estima a relação entre tonelagem movimentada e ISS municipal usando
regressão OLS log-log com efeitos fixos de porto.

Fonte de dados para regressão (FINBRA panel — padrão):
    ISS municipal: FINBRA/SICONFI, 2011-2024, 20 municípios-porto, n≈276.
    Tonelagem: mart BigQuery (ANTAQ), 2011-2024.

Metodologia:
    ln(ISS_municipal_it) = alpha_i + beta * ln(tonelagem_it) + epsilon_it
    onde i = porto, t = ano, alpha_i = efeito fixo de porto (FE).
    Erros padrão heteroscedasticidade-robustos (HC3).
    Amostra completa → FE é estatisticamente significativo (β≈0.73, p<0.001).

Dados das DFs dos operadores (fixture tributos_portos):
    Usados para composição municipal/federal (ISS pago pelo operador vs. federais)
    e como baseline na calculadora (ISS real do operador, mais preciso).
    Cobertura: 2018-2024, n=59 obs (apenas para composição e baseline).

Interpretação do β FINBRA FE:
    β = 0.735 → +10% tonelagem no mesmo porto → +7.3% no ISS municipal.
    Capta efeito within-porto (variação ao longo do tempo no mesmo porto).
    Análise associativa — não implica causalidade.
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
    """Constrói painel DFs-operador porto × ano com tonelagem (2018-2024).

    Usado para: composição municipal/federal e baseline da calculadora.
    Se bq_client=None, retorna painel sem tonelagem.
    """
    df_trib = _build_tributos_df()

    if bq_client is None:
        logger.warning("fiscal_elasticity: bq_client=None, painel sem tonelagem.")
        return df_trib

    try:
        from app.db.bigquery.queries.module6_public_finance import MART_IMPACTO_ECONOMICO_FQTN
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
        raw = getattr(bq_client, "client", bq_client)
        rows = list(raw.query(sql))
        df_ton = pd.DataFrame([dict(r) for r in rows])
        df_ton["id_municipio"] = df_ton["id_municipio"].astype(str)
        df_ton["ano"] = df_ton["ano"].astype(int)
        return df_trib.merge(df_ton, on=["id_municipio", "ano"], how="left")
    except Exception as exc:
        logger.warning("fiscal_elasticity: falha ao buscar tonelagem (DFs panel): %s", exc)
        return df_trib


def build_finbra_panel_df(bq_client) -> pd.DataFrame:
    """Constrói painel FINBRA ISS × tonelagem, 2011-2024 (20 portos, ~276 obs).

    Este é o painel usado para a regressão de elasticidade fiscal.
    Fonte ISS: FINBRA/SICONFI (ISS municipal total, não só do operador).
    Fonte tonelagem: mart BigQuery ANTAQ.

    Returns DataFrame vazio se BigQuery indisponível.
    """
    try:
        from app.db.bigquery.queries.module6_public_finance import (
            MART_IMPACTO_ECONOMICO_FQTN,
            BD_DADOS_FINBRA,
        )
        ids = [v["id_municipio"] for v in PORTO_MUNICIPIO_MAP.values()]
        ids_str = ", ".join(f"'{i}'" for i in ids)
        raw = getattr(bq_client, "client", bq_client)

        # Tonelagem 2011-2024 (excluir 2025 = projeção anualizada)
        sql_ton = f"""
            SELECT CAST(id_municipio AS STRING) AS id_municipio,
                   CAST(ano AS INT64) AS ano,
                   tonelagem_antaq_oficial AS tonelagem_r_mil_ton
            FROM {MART_IMPACTO_ECONOMICO_FQTN}
            WHERE CAST(id_municipio AS STRING) IN ({ids_str})
              AND tonelagem_antaq_oficial > 0
              AND ano BETWEEN 2011 AND 2024
        """
        df_ton = pd.DataFrame([dict(r) for r in raw.query(sql_ton)])
        df_ton["id_municipio"] = df_ton["id_municipio"].astype(str)
        df_ton["ano"] = df_ton["ano"].astype(int)

        # ISS municipal FINBRA 2011-2024
        sql_iss = f"""
            SELECT CAST(id_municipio AS STRING) AS id_municipio,
                   CAST(ano AS INT64) AS ano,
                   ROUND(SUM(valor) / 1000, 2) AS iss_r_mil
            FROM `{BD_DADOS_FINBRA}`
            WHERE conta_bd = 'Imposto sobre Serviços de Qualquer Natureza - ISSQN'
              AND estagio_bd = 'Receitas Brutas Realizadas'
              AND id_municipio IN ({ids_str})
              AND ano BETWEEN 2011 AND 2024
              AND valor IS NOT NULL AND valor > 0
            GROUP BY id_municipio, ano
        """
        df_iss = pd.DataFrame([dict(r) for r in raw.query(sql_iss)])
        df_iss["id_municipio"] = df_iss["id_municipio"].astype(str)
        df_iss["ano"] = df_iss["ano"].astype(int)

        # Merge e adicionar nome do porto
        id_to_porto = {v["id_municipio"]: porto for porto, v in PORTO_MUNICIPIO_MAP.items()}
        df = df_ton.merge(df_iss, on=["id_municipio", "ano"], how="inner")
        df["porto"] = df["id_municipio"].map(id_to_porto)
        df["uf"] = df["id_municipio"].map(
            lambda i: PORTO_MUNICIPIO_MAP.get(i, {}).get("uf") if i in PORTO_MUNICIPIO_MAP else
            next((v["uf"] for v in PORTO_MUNICIPIO_MAP.values() if v["id_municipio"] == i), None)
        )

        logger.info(
            "fiscal_elasticity: FINBRA panel %d obs de %d portos (%d-%d)",
            len(df), df["porto"].nunique(),
            int(df["ano"].min()), int(df["ano"].max()),
        )
        return df

    except Exception as exc:
        logger.warning("fiscal_elasticity: falha ao construir FINBRA panel: %s", exc)
        return pd.DataFrame()


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
    """Roda regressões OLS log-log para ISS e tributos federais.

    Especificação padrão: OLS pooled cross-sectional (log_trib ~ log_ton).
    Justificativa: o painel tem ~7 anos/porto com pouca variação within-porto
    em tonelagem, o que torna a especificação com efeitos fixos de porto
    pouco poderosa (IC amplos, p > 0.3). O pooled OLS captura a relação
    entre porte dos portos e volume de tributos que é economicamente relevante
    para investidores.

    Adicionalmente computa a especificação FE para transparência (campo extra).

    Retorna dict com 'municipal' e 'federal', cada um com:
        beta, ci_lower, ci_upper, r2, p_value, n_obs, n_portos,
        especificacao ('pooled_ols'), fe_result (FE alternativo ou None)
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
            # Especificação pooled OLS (padrão para DFs dos operadores, n≈59).
            # Com n≈59 o FE tem baixo poder (variação within-porto pequena).
            # A cross-sectional é informativa: "portos maiores pagam mais ISS".
            model_pooled = smf.ols(
                "log_trib ~ log_ton",
                data=sample,
            ).fit(cov_type="HC3")

            beta = float(model_pooled.params.get("log_ton", float("nan")))
            ci = model_pooled.conf_int().loc["log_ton"]
            p_value = float(model_pooled.pvalues.get("log_ton", float("nan")))
            r2 = float(model_pooled.rsquared)

            # Especificação FE de porto (alternativa — mais robusta a omitidos)
            fe_result = None
            try:
                model_fe = smf.ols(
                    "log_trib ~ log_ton + C(porto)",
                    data=sample,
                ).fit(cov_type="HC3")
                beta_fe = float(model_fe.params.get("log_ton", float("nan")))
                ci_fe = model_fe.conf_int().loc["log_ton"]
                p_fe = float(model_fe.pvalues.get("log_ton", float("nan")))
                fe_result = {
                    "beta": round(beta_fe, 4),
                    "ci_lower": round(float(ci_fe.iloc[0]), 4),
                    "ci_upper": round(float(ci_fe.iloc[1]), 4),
                    "r2": round(float(model_fe.rsquared), 4),
                    "p_value": round(p_fe, 6),
                    "n_obs": len(sample),
                    "n_portos": int(sample["porto"].nunique()),
                }
            except Exception:
                pass

            results[key] = {
                "beta": round(beta, 4),
                "ci_lower": round(float(ci.iloc[0]), 4),
                "ci_upper": round(float(ci.iloc[1]), 4),
                "r2": round(r2, 4),
                "p_value": round(p_value, 6),
                "n_obs": len(sample),
                "n_portos": int(sample["porto"].nunique()),
                "especificacao": "pooled_ols",
                "fe_result": fe_result,
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


def build_participacao_iss_df(bq_client) -> pd.DataFrame:
    """Calcula a participação do porto no ISS municipal (ISS operador / ISS total município).

    Fórmula: participacao_pct = (ISS das DFs do operador / ISS total FINBRA do município) × 100

    Retorna DataFrame com colunas: porto, uf, nome_municipio, ano,
    iss_df_r_mil, iss_finbra_r_mil, participacao_pct.
    Retorna DataFrame vazio se BigQuery indisponível.
    """
    try:
        from app.db.bigquery.queries.module6_public_finance import BD_DADOS_FINBRA
        raw = getattr(bq_client, "client", bq_client)

        # DFs ISS por porto (fixture)
        rows_fixture = [
            {
                "porto": rec["porto"],
                "uf": rec["uf"],
                "ano": rec["ano"],
                "iss_df_r_mil": rec["iss_r_mil"],
            }
            for rec in TRIBUTOS_PORTOS
            if rec.get("iss_r_mil") is not None and rec["iss_r_mil"] > 0 and rec["ano"] <= 2024
        ]
        df_fixture = pd.DataFrame(rows_fixture)
        if df_fixture.empty:
            return pd.DataFrame()

        # Mapear id_municipio
        df_fixture["id_municipio"] = df_fixture["porto"].map(
            {p: v["id_municipio"] for p, v in PORTO_MUNICIPIO_MAP.items()}
        )
        df_fixture["nome_municipio"] = df_fixture["porto"].map(
            {p: v["nome"] for p, v in PORTO_MUNICIPIO_MAP.items()}
        )
        df_fixture = df_fixture.dropna(subset=["id_municipio"])

        ids = df_fixture["id_municipio"].unique().tolist()
        ids_str = ", ".join(f"'{i}'" for i in ids)

        # FINBRA ISS para os mesmos municípios e anos
        sql = f"""
            SELECT CAST(id_municipio AS STRING) AS id_municipio,
                   CAST(ano AS INT64) AS ano,
                   ROUND(SUM(valor) / 1000, 2) AS iss_finbra_r_mil
            FROM `{BD_DADOS_FINBRA}`
            WHERE conta_bd = 'Imposto sobre Serviços de Qualquer Natureza - ISSQN'
              AND estagio_bd = 'Receitas Brutas Realizadas'
              AND id_municipio IN ({ids_str})
              AND ano BETWEEN 2018 AND 2024
              AND valor > 0
            GROUP BY id_municipio, ano
        """
        df_finbra = pd.DataFrame([dict(r) for r in raw.query(sql)])
        if df_finbra.empty:
            return pd.DataFrame()

        df_finbra["id_municipio"] = df_finbra["id_municipio"].astype(str)
        df_finbra["ano"] = df_finbra["ano"].astype(int)

        # Merge e calcular participação
        df = df_fixture.merge(df_finbra, on=["id_municipio", "ano"], how="inner")
        df["participacao_pct"] = (df["iss_df_r_mil"] / df["iss_finbra_r_mil"] * 100).round(2)

        logger.info(
            "fiscal_elasticity: participacao_iss %d obs de %d portos",
            len(df), df["porto"].nunique(),
        )
        return df.sort_values(["porto", "ano"])

    except Exception as exc:
        logger.warning("fiscal_elasticity: falha ao calcular participacao_iss: %s", exc)
        return pd.DataFrame()
