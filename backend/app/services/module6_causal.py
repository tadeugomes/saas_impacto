"""
Estimação causal de impacto fiscal — Módulo 6.

Eleva IND-6.10 e IND-6.11 de correlações/OLS pooled para estimadores
de painel com efeitos fixos bidirecionais (Two-Way FE / within-estimator),
controlando para heterogeneidade permanente de municípios e choques
comuns de tempo.

Modelos
-------
IND-6.10 — Coeficiente de Painel FE (substitui Pearson pooled):
    receita_fiscal_total_{it}
        = β · tonelagem_{it} + α_i + δ_t + ε_{it}

IND-6.11 — Elasticidade de Painel FE (substitui OLS pooled log-log):
    ln(receita_fiscal_{it})
        = β · ln(tonelagem_{it}) + α_i + δ_t + ε_{it}

onde α_i = efeito fixo de município (absorve diferenças permanentes entre
cidades) e δ_t = efeito fixo de ano (absorve tendências comuns nacionais).

Erros-padrão são clusterizados por município (cluster-robust SE).

Nota metodológica
-----------------
Esta especificação é mais rigorosa que a OLS/Pearson pooled atual porque
remove a confusão causada por características permanentes de cada município
e por ciclos econômicos nacionais compartilhados.
Não é, todavia, uma estimativa de efeito causal no sentido de IV/DiD
(não há grupo de controle nem instrumento exógeno).
O label correto é "Painel FE (within-estimator)", não "causal DiD".
"""
from __future__ import annotations

import logging
import math
from typing import Any

import pandas as pd
import statsmodels.formula.api as smf

from app.db.bigquery.client import BigQueryClient, get_bigquery_client
from app.db.bigquery.queries.module6_public_finance import (
    BD_DADOS_FINBRA,
    MART_IMPACTO_ECONOMICO_FQTN,
)

logger = logging.getLogger(__name__)

# ── Mínimo de observações (municípios × anos) para estimar Panel FE ──────────
_MIN_UNIT_YEARS = 30  # ~5 municípios × 6 anos ou 3 municípios × 10 anos
_MIN_UNITS = 3         # precisamos de ao menos 3 municípios para efeitos fixos


# ============================================================================
# Query de painel fiscal × tonelagem
# ============================================================================

def _build_fiscal_panel_query(id_municipio: str | None = None) -> str:
    """
    Retorna SQL que produz painel (id_municipio, ano, tonelagem, receita_fiscal_total).

    Usa o mart M5 (tonelagem ANTAQ) e o FINBRA (ICMS + ISS) como fontes.
    Se ``id_municipio`` for fornecido, filtra apenas aquele município e seus
    vizinhos (estado inteiro) para ter observações suficientes para FE.
    """
    # Quando município específico é fornecido, mantemos o estado inteiro
    # para ter variação cross-sectional que permite identificar efeito fixo.
    municipio_filter = ""
    if id_municipio:
        # Extrai UF (primeiros 2 dígitos do código IBGE)
        uf_prefix = id_municipio[:2]
        municipio_filter = f"AND SUBSTRING(CAST(m.id_municipio AS STRING), 1, 2) = '{uf_prefix}'"

    return f"""
    WITH receitas_tributarias AS (
        SELECT
            CAST(id_municipio AS STRING) AS id_municipio,
            CAST(ano AS INT64)           AS ano,
            SUM(CASE
                WHEN conta_bd = 'Cota-Parte do ICMS'
                THEN CAST(valor AS FLOAT64) ELSE 0 END) AS icms,
            SUM(CASE
                WHEN conta_bd = 'Imposto sobre Serviços de Qualquer Natureza - ISSQN'
                THEN CAST(valor AS FLOAT64) ELSE 0 END) AS iss
        FROM `{BD_DADOS_FINBRA}`
        WHERE
            conta_bd IN (
                'Cota-Parte do ICMS',
                'Imposto sobre Serviços de Qualquer Natureza - ISSQN'
            )
            AND estagio_bd = 'Receitas Brutas Realizadas'
            AND valor IS NOT NULL
        GROUP BY id_municipio, ano
    ),
    receita_fiscal AS (
        SELECT
            id_municipio,
            ano,
            icms + iss AS receita_fiscal_total
        FROM receitas_tributarias
        WHERE icms + iss > 0
    ),
    painel AS (
        SELECT
            CAST(m.id_municipio AS STRING)      AS id_municipio,
            CAST(m.ano AS INT64)                AS ano,
            m.tonelagem_antaq_oficial           AS tonelagem,
            r.receita_fiscal_total
        FROM `{MART_IMPACTO_ECONOMICO_FQTN}` m
        INNER JOIN receita_fiscal r
            ON  CAST(m.id_municipio AS STRING) = r.id_municipio
            AND CAST(m.ano AS INT64)           = r.ano
        WHERE
            m.tonelagem_antaq_oficial IS NOT NULL
            AND m.tonelagem_antaq_oficial > 0
            AND r.receita_fiscal_total  > 0
            {municipio_filter}
    )
    SELECT
        id_municipio,
        ano,
        tonelagem,
        receita_fiscal_total
    FROM painel
    ORDER BY id_municipio, ano
    """


# ============================================================================
# Estimação Panel FE
# ============================================================================

def _run_panel_fe(
    df: pd.DataFrame,
    outcome: str,
    treatment: str,
    log_log: bool = False,
) -> dict[str, Any]:
    """
    Within-estimator (TWFE) com erros-padrão clusterizados por município.

    Parameters
    ----------
    df:
        DataFrame com colunas [id_municipio, ano, <outcome>, <treatment>].
    outcome:
        Nome da coluna de saída (receita_fiscal_total).
    treatment:
        Nome da coluna de tratamento (tonelagem).
    log_log:
        Se True, aplica log natural a ambas as variáveis antes da estimação.

    Returns
    -------
    dict com chaves: coef, std_err, p_value, ci_lower, ci_upper, n_obs,
        n_municipios, method, log_log, outcome.
    """
    work = df[[outcome, treatment, "id_municipio", "ano"]].dropna().copy()

    if log_log:
        work = work[work[outcome] > 0].copy()
        work = work[work[treatment] > 0].copy()
        work[outcome] = work[outcome].apply(math.log)
        work[treatment] = work[treatment].apply(math.log)

    n_obs = len(work)
    n_units = work["id_municipio"].nunique()

    if n_obs < _MIN_UNIT_YEARS or n_units < _MIN_UNITS:
        return _insufficient_data_result(outcome, n_obs, n_units, log_log)

    formula = (
        f"{outcome} ~ {treatment}"
        f" + C(id_municipio) + C(ano)"
    )

    try:
        model = smf.ols(formula, data=work).fit(
            cov_type="cluster",
            cov_kwds={"groups": work["id_municipio"]},
        )
    except Exception as exc:
        logger.warning("Panel FE falhou para %s: %s", outcome, exc)
        return _error_result(outcome, n_obs, n_units, log_log, str(exc))

    if treatment not in model.params:
        return _error_result(
            outcome, n_obs, n_units, log_log,
            f"Parâmetro '{treatment}' não estimado (possível colinearidade).",
        )

    coef = float(model.params[treatment])
    se = float(model.bse[treatment])
    pval = float(model.pvalues[treatment])
    ci = model.conf_int(alpha=0.05).loc[treatment]
    ci_lower = float(ci.iloc[0])
    ci_upper = float(ci.iloc[1])

    return {
        "coef": round(coef, 6),
        "std_err": round(se, 6),
        "p_value": round(pval, 4),
        "ci_lower": round(ci_lower, 6),
        "ci_upper": round(ci_upper, 6),
        "n_obs": n_obs,
        "n_municipios": n_units,
        "r2_within": round(float(model.rsquared), 4),
        "method": "panel_fe",
        "log_log": log_log,
        "outcome": outcome,
        "significant": pval < 0.05,
        "error": None,
    }


def _insufficient_data_result(
    outcome: str, n_obs: int, n_units: int, log_log: bool
) -> dict[str, Any]:
    return {
        "coef": None,
        "std_err": None,
        "p_value": None,
        "ci_lower": None,
        "ci_upper": None,
        "n_obs": n_obs,
        "n_municipios": n_units,
        "r2_within": None,
        "method": "panel_fe",
        "log_log": log_log,
        "outcome": outcome,
        "significant": None,
        "error": (
            f"Dados insuficientes para Panel FE: "
            f"{n_obs} obs. em {n_units} municípios "
            f"(mínimo: {_MIN_UNIT_YEARS} obs. em {_MIN_UNITS} municípios)."
        ),
    }


def _error_result(
    outcome: str, n_obs: int, n_units: int, log_log: bool, msg: str
) -> dict[str, Any]:
    return {
        "coef": None,
        "std_err": None,
        "p_value": None,
        "ci_lower": None,
        "ci_upper": None,
        "n_obs": n_obs,
        "n_municipios": n_units,
        "r2_within": None,
        "method": "panel_fe",
        "log_log": log_log,
        "outcome": outcome,
        "significant": None,
        "error": msg,
    }


# ============================================================================
# Ponto de entrada público
# ============================================================================

async def estimate_panel_fe_m6(
    codigo: str,
    id_municipio: str | None,
    bq_client: BigQueryClient | None = None,
) -> dict[str, Any] | None:
    """
    Estima Panel FE para IND-6.10 (coeficiente) ou IND-6.11 (elasticidade).

    Retorna None se ``codigo`` não for IND-6.10 ou IND-6.11.
    Retorna dict com resultado (ou erro) nos demais casos.

    Parameters
    ----------
    codigo:
        Código do indicador. Apenas IND-6.10 e IND-6.11 são tratados.
    id_municipio:
        Código IBGE do município. Se fornecido, o painel é restrito ao
        estado do município (para ter variação cross-sectional adequada).
    bq_client:
        Cliente BigQuery. Se None, usa o cliente global.
    """
    if codigo not in {"IND-6.10", "IND-6.11"}:
        return None

    bq = bq_client or get_bigquery_client()
    log_log = codigo == "IND-6.11"
    outcome = "receita_fiscal_total"
    treatment = "tonelagem"

    query = _build_fiscal_panel_query(id_municipio)
    try:
        rows = await bq.execute_query(query)
    except Exception as exc:
        logger.warning("BigQuery falhou para Panel FE M6 (%s): %s", codigo, exc)
        return {
            "coef": None, "std_err": None, "p_value": None,
            "ci_lower": None, "ci_upper": None,
            "n_obs": 0, "n_municipios": 0, "r2_within": None,
            "method": "panel_fe", "log_log": log_log, "outcome": outcome,
            "significant": None,
            "error": f"Falha ao buscar painel no BigQuery: {exc}",
        }

    if not rows:
        return _insufficient_data_result(outcome, 0, 0, log_log)

    df = pd.DataFrame(rows)
    for col in [outcome, treatment, "ano"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return _run_panel_fe(df, outcome=outcome, treatment=treatment, log_log=log_log)
