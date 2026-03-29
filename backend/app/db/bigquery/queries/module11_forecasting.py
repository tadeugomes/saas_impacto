"""
Queries do Módulo 11 — Forecast de Throughput Portuário.

Motor SARIMAX com 5 blocos de variáveis:
  1. Histórico (lags, MA, sazonalidade)
  2. Macro (câmbio, IBC-Br, Selic, IPCA)
  3. Operação (navios, espera, ocupação)
  4. Safra (CONAB)
  5. Clima (INMET precipitação, NOAA El Niño, ANA nível de rio)

Prioriza exógenas reais (Blocos 2-5) sobre derivadas do target (Bloco 1)
para permitir projeção via cenários no forecast out-of-sample.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


async def query_forecast_tonelagem(
    id_instalacao: Optional[str] = None,
    id_municipio: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-11.01: Forecast de Tonelagem — 60 meses (5 anos) com IC 80/95%.

    Treina SARIMAX priorizando exógenas reais (BACEN, INMET, CONAB) sobre
    lags do target. Projeção futura via cenário base (ScenarioEngine).
    """
    if not id_instalacao:
        return []

    from app.services.forecasting.feature_builder import FeatureBuilder
    from app.services.forecasting.sarimax_engine import SarimaxEngine
    from app.services.forecasting.scenario_engine import ScenarioEngine

    builder = FeatureBuilder()
    engine = SarimaxEngine()

    try:
        df = await builder.build_panel(id_instalacao, id_municipio)

        if df.empty or len(df) < 24:
            return [{"error": "Dados insuficientes (mínimo 24 meses)", "id_instalacao": id_instalacao}]

        exog_priority = builder.exogenous_features or None
        fit_info = engine.fit(df, target="tonelagem", exog_priority=exog_priority)

        # Projeção via cenário base para exógenas reais
        exog_future = None
        if engine._feature_names:
            try:
                scenario_gen = ScenarioEngine(engine._feature_names)
                scenarios = scenario_gen.generate_exog_scenarios(df, steps=60)
                exog_future = scenarios.get("base")
            except Exception:
                pass  # fallback interno do SarimaxEngine

        forecast = engine.forecast(steps=60, exog_future=exog_future)
        drivers = engine.decompose_drivers()

        result: Dict[str, Any] = {
            "id_instalacao": id_instalacao,
            "blocos_status": builder.blocks_status,
            "modelo": fit_info,
            "forecast": forecast,
            "drivers": drivers,
            "features_disponiveis": builder.feature_names,
        }

        try:
            from app.services.forecasting.forecast_interpreter import create_interpreter
            interpreter = create_interpreter(id_instalacao, df, target="tonelagem")
            result["interpretacao"] = interpreter.interpret_all(drivers=drivers)
        except Exception as ie:
            logger.warning("forecast_interpreter_error porto=%s: %s", id_instalacao, ie)

        return [result]
    except Exception as e:
        logger.error("forecast_tonelagem_error porto=%s: %s", id_instalacao, e)
        return [{"error": str(e)[:300], "id_instalacao": id_instalacao}]


async def query_cenarios_tonelagem(
    id_instalacao: Optional[str] = None,
    id_municipio: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-11.02: Cenários de Tonelagem — base/otimista/pessimista.

    Gera 3 cenários ajustando variáveis macro e climáticas.
    """
    if not id_instalacao:
        return []

    from app.services.forecasting.feature_builder import FeatureBuilder
    from app.services.forecasting.sarimax_engine import SarimaxEngine
    from app.services.forecasting.scenario_engine import ScenarioEngine

    builder = FeatureBuilder()
    engine = SarimaxEngine()

    try:
        df = await builder.build_panel(id_instalacao, id_municipio)

        if df.empty or len(df) < 24:
            return [{"error": "Dados insuficientes (mínimo 24 meses)"}]

        exog_priority = builder.exogenous_features or None
        engine.fit(df, target="tonelagem", exog_priority=exog_priority)

        scenario_gen = ScenarioEngine(engine._feature_names)
        exog_scenarios = scenario_gen.generate_exog_scenarios(df, steps=60)

        forecasts = {}
        for name, exog_future in exog_scenarios.items():
            forecasts[name] = engine.forecast(steps=60, exog_future=exog_future)

        result = scenario_gen.format_scenarios_response(forecasts, df)
        result["id_instalacao"] = id_instalacao
        result["blocos_status"] = builder.blocks_status

        try:
            from app.services.forecasting.forecast_interpreter import create_interpreter
            interpreter = create_interpreter(id_instalacao, df, target="tonelagem")
            drivers = engine.decompose_drivers()
            result["interpretacao"] = interpreter.interpret_all(
                drivers=drivers,
                scenarios=result,
            )
        except Exception as ie:
            logger.warning("cenarios_interpreter_error porto=%s: %s", id_instalacao, ie)

        return [result]
    except Exception as e:
        logger.error("cenarios_error porto=%s: %s", id_instalacao, e)
        return [{"error": str(e)[:300], "id_instalacao": id_instalacao}]


async def query_decomposicao_drivers(
    id_instalacao: Optional[str] = None,
    id_municipio: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-11.03: Decomposição de Drivers — peso de cada variável no forecast.

    Usa coeficientes padronizados (|coef| * std) para comparação justa
    entre features de escalas diferentes.
    """
    if not id_instalacao:
        return []

    from app.services.forecasting.feature_builder import FeatureBuilder
    from app.services.forecasting.sarimax_engine import SarimaxEngine

    builder = FeatureBuilder()
    engine = SarimaxEngine()

    try:
        df = await builder.build_panel(id_instalacao, id_municipio)

        if df.empty or len(df) < 24:
            return [{"error": "Dados insuficientes"}]

        exog_priority = builder.exogenous_features or None
        engine.fit(df, target="tonelagem", exog_priority=exog_priority)
        drivers = engine.decompose_drivers()

        # Agrupa por bloco usando categorização do FeatureBuilder
        blocos = {
            "Histórico": [],
            "Macroeconomia": [],
            "Operação": [],
            "Safra": [],
            "Clima": [],
        }

        for d in drivers:
            feat = d["feature"]
            if any(k in feat for k in ["ton_lag", "ton_ma", "ton_mom", "ton_yoy", "sin_", "cos_"]):
                blocos["Histórico"].append(d)
            elif any(k in feat for k in ["cambio", "ibc", "selic", "ipca"]):
                blocos["Macroeconomia"].append(d)
            elif any(k in feat for k in ["navios", "tempo_espera", "tempo_atracacao", "calado", "atracoes"]):
                blocos["Operação"].append(d)
            elif any(k in feat for k in ["safra", "conab"]):
                blocos["Safra"].append(d)
            elif any(k in feat for k in ["precip", "oni", "nivel", "chuva"]):
                blocos["Clima"].append(d)
            else:
                blocos["Histórico"].append(d)  # Default

        bloco_importancias = []
        for bloco, features in blocos.items():
            imp = sum(f["importancia_pct"] for f in features)
            bloco_importancias.append({
                "bloco": bloco,
                "importancia_pct": round(imp, 1),
                "n_features": len(features),
                "features": features,
            })

        return [{
            "id_instalacao": id_instalacao,
            "blocos_status": builder.blocks_status,
            "drivers": drivers,
            "blocos": sorted(bloco_importancias, key=lambda x: -x["importancia_pct"]),
            "composicao": {
                "nota_metodologica": (
                    "Importância calculada pelo coeficiente padronizado: "
                    "|coef| x desvio-padrão da variável no período de treino. "
                    "Percentuais somam 100%."
                ),
            },
        }]
    except Exception as e:
        logger.error("drivers_error: %s", e)
        return [{"error": str(e)[:300]}]


async def query_backtesting(
    id_instalacao: Optional[str] = None,
    id_municipio: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-11.04: Backtesting — walk-forward nos últimos 12 meses.

    Treina no histórico, prevê os últimos 12 meses, compara com real.
    """
    if not id_instalacao:
        return []

    from app.services.forecasting.feature_builder import FeatureBuilder
    from app.services.forecasting.sarimax_engine import SarimaxEngine

    builder = FeatureBuilder()
    engine = SarimaxEngine()

    try:
        df = await builder.build_panel(id_instalacao, id_municipio)

        if df.empty or len(df) < 36:
            return [{"error": "Dados insuficientes para backtest (mínimo 36 meses)"}]

        exog_priority = builder.exogenous_features or None
        result = engine.backtest(
            df, target="tonelagem", test_months=12,
            exog_priority=exog_priority,
        )
        result["id_instalacao"] = id_instalacao
        result["blocos_status"] = builder.blocks_status

        return [result]
    except Exception as e:
        logger.error("backtest_error: %s", e)
        return [{"error": str(e)[:300]}]


async def query_forecast_fob_comercio(
    id_municipio: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    IND-11.05: Forecast de FOB Comércio Exterior — 12 meses.

    Prevê valor FOB total (exportações + importações) usando
    variáveis macro como exógenas.
    """
    if not id_municipio:
        return []

    from app.db.bigquery.client import get_bigquery_client
    from app.services.forecasting.sarimax_engine import SarimaxEngine
    import pandas as pd

    bq = get_bigquery_client()

    sql = f"""
    SELECT
        CAST(ano AS INT64) AS ano,
        CAST(mes AS INT64) AS mes,
        SUM(valor_fob_dolar) AS fob_usd
    FROM (
        SELECT ano, mes, valor_fob_dolar
        FROM `basedosdados.br_me_comex_stat.municipio_exportacao`
        WHERE id_municipio = '{id_municipio}'
        UNION ALL
        SELECT ano, mes, valor_fob_dolar
        FROM `basedosdados.br_me_comex_stat.municipio_importacao`
        WHERE id_municipio = '{id_municipio}'
    )
    GROUP BY ano, mes
    ORDER BY ano, mes
    """

    try:
        rows = await bq.execute_query(sql, timeout_ms=30000)
        if not rows or len(rows) < 24:
            return [{"error": "Dados insuficientes de comércio exterior"}]

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(
            df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2) + "-01"
        )
        df = df.set_index("date").sort_index()
        df["fob_usd"] = pd.to_numeric(df["fob_usd"], errors="coerce")

        engine = SarimaxEngine()
        engine.fit(df, target="fob_usd", exog_cols=[])  # Sem exógenas
        forecast = engine.forecast(steps=12)

        return [{
            "id_municipio": id_municipio,
            "forecast": forecast,
        }]
    except Exception as e:
        logger.error("forecast_fob_error: %s", e)
        return [{"error": str(e)[:300]}]


QUERIES_MODULE_11 = {
    "IND-11.01": query_forecast_tonelagem,
    "IND-11.02": query_cenarios_tonelagem,
    "IND-11.03": query_decomposicao_drivers,
    "IND-11.04": query_backtesting,
    "IND-11.05": query_forecast_fob_comercio,
}
