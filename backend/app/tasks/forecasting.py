"""
Celery Tasks — Forecasting de Throughput Portuário (Módulo 11).

Fluxo:
  1. API recebe POST /indicators/forecast/run → despacha esta task via .delay()
     e retorna imediatamente com {"task_id": "...", "status": "queued"}
  2. Worker pega a task da fila ``forecasting``
  3. Task roda FeatureBuilder + SarimaxEngine + backtest
  4. Resultado salvo em Redis com TTL de 24h
  5. Frontend consulta GET /indicators/forecast/status/{task_id} até status=SUCCESS

Beat schedule (pre-computação diária):
  - Toda madrugada, pré-computa os portos cadastrados nos tenants ativos
  - Resultado fica em cache no Redis — requisição do usuário serve do cache instantaneamente

Retentativas:
  - Falhas transitórias de rede/BigQuery: até 3 retentativas com backoff exponencial
  - Falhas de dados (série curta, porto inválido): não disparam retry (erro de negócio)
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from celery import Task

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# TTL do resultado em Redis: 24 horas
FORECAST_CACHE_TTL = 86_400

# Portos pré-computados no beat schedule diário
DEFAULT_PORTOS_PRECOMPUTE = [
    "Santos",
    "Paranaguá",
    "Itajaí",
    "Rio Grande",
    "Suape",
    "Vila do Conde",
    "Itaguaí",
    "São Francisco do Sul",
]


# ── Helpers assíncronos ────────────────────────────────────────────────────


async def _run_forecast_pipeline(
    id_instalacao: str,
    id_municipio: Optional[str],
    ano_inicio: int,
    ano_fim: Optional[int],
    incluir_backtest: bool,
) -> Dict[str, Any]:
    """
    Executa o pipeline completo de forecasting para um porto.

    Retorna dict com modelo, forecast 60m, drivers e (opcional) backtest.
    """
    from app.services.forecasting.feature_builder import FeatureBuilder
    from app.services.forecasting.sarimax_engine import SarimaxEngine

    builder = FeatureBuilder()
    engine = SarimaxEngine()

    df = await builder.build_panel(
        id_instalacao=id_instalacao,
        id_municipio=id_municipio,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
    )

    if df.empty or len(df) < 24:
        raise ValueError(
            f"Dados insuficientes para {id_instalacao}: "
            f"{len(df)} meses (mínimo 24)"
        )

    # Passa exógenas reais como prioritárias para o stepwise
    exog_priority = builder.exogenous_features or None

    fit_info = engine.fit(
        df, target="tonelagem", exog_priority=exog_priority,
    )

    # Forecast com cenário base para exógenas reais
    from app.services.forecasting.scenario_engine import ScenarioEngine

    exog_future = None
    if engine._feature_names:
        try:
            scenario_gen = ScenarioEngine(engine._feature_names)
            scenarios = scenario_gen.generate_exog_scenarios(df, steps=60)
            exog_future = scenarios.get("base")
        except Exception as e:
            logger.warning("forecast_scenario_fallback: %s", e)

    forecast = engine.forecast(steps=60, exog_future=exog_future)
    drivers = engine.decompose_drivers()

    result: Dict[str, Any] = {
        "id_instalacao": id_instalacao,
        "id_municipio": id_municipio,
        "n_meses_treino": len(df),
        "blocos_status": builder.blocks_status,
        "feature_blocks": {
            k: len(v) for k, v in builder.feature_blocks.items()
        },
        "modelo": fit_info,
        "forecast": forecast,
        "drivers": drivers,
        "features_disponiveis": builder.feature_names,
    }

    if incluir_backtest and len(df) >= 36:
        result["backtest"] = engine.backtest(
            df, target="tonelagem", test_months=12,
            exog_priority=exog_priority,
        )

    # Interpretação em linguagem de negócio
    try:
        from app.services.forecasting.forecast_interpreter import create_interpreter
        interpreter = create_interpreter(id_instalacao, df, target="tonelagem")
        result["interpretacao"] = interpreter.interpret_all(
            backtest=result.get("backtest"),
            drivers=drivers,
        )
    except Exception as e:
        logger.warning("forecast_interpreter_error: %s", e)

    return result


async def _run_cenarios_pipeline(
    id_instalacao: str,
    id_municipio: Optional[str],
    ano_inicio: int,
    ano_fim: Optional[int],
) -> Dict[str, Any]:
    """Gera cenários base/otimista/pessimista via ScenarioEngine."""
    from app.services.forecasting.feature_builder import FeatureBuilder
    from app.services.forecasting.sarimax_engine import SarimaxEngine
    from app.services.forecasting.scenario_engine import ScenarioEngine

    builder = FeatureBuilder()
    engine = SarimaxEngine()

    df = await builder.build_panel(
        id_instalacao=id_instalacao,
        id_municipio=id_municipio,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
    )

    if df.empty or len(df) < 24:
        raise ValueError(f"Dados insuficientes para cenários: {len(df)} meses")

    engine.fit(df, target="tonelagem")
    scenario_gen = ScenarioEngine(engine._feature_names)
    exog_scenarios = scenario_gen.generate_exog_scenarios(df, steps=60)

    forecasts = {}
    for name, exog_future in exog_scenarios.items():
        forecasts[name] = engine.forecast(steps=60, exog_future=exog_future)

    result = scenario_gen.format_scenarios_response(forecasts, df)
    result["id_instalacao"] = id_instalacao

    # Interpretação de cenários em linguagem de negócio
    try:
        from app.services.forecasting.forecast_interpreter import create_interpreter
        interpreter = create_interpreter(id_instalacao, df, target="tonelagem")
        drivers = engine.decompose_drivers()
        result["interpretacao"] = interpreter.interpret_all(
            drivers=drivers,
            scenarios=result,
        )
    except Exception as e:
        logger.warning("cenarios_interpreter_error: %s", e)

    return result


async def _store_in_redis(key: str, value: Dict[str, Any], ttl: int) -> None:
    """Salva resultado diretamente no Redis com TTL."""
    import json
    from app.core.redis import get_redis_client

    redis = await get_redis_client()
    await redis.set(key, json.dumps(value), ex=ttl)


async def _get_from_redis(key: str) -> Optional[Dict[str, Any]]:
    """Recupera resultado do Redis."""
    import json
    from app.core.redis import get_redis_client

    redis = await get_redis_client()
    raw = await redis.get(key)
    if raw is None:
        return None
    return json.loads(raw)


def _build_cache_key(id_instalacao: str, task_type: str = "forecast") -> str:
    """Chave padronizada no Redis para resultado de forecast."""
    return f"forecast:{task_type}:{id_instalacao.lower().replace(' ', '_')}"


# ── Celery Tasks ───────────────────────────────────────────────────────────


@celery_app.task(
    bind=True,
    name="app.tasks.forecasting.run_forecast",
    queue="forecasting",
    max_retries=3,
    default_retry_delay=120,
    soft_time_limit=900,   # 15 min
    time_limit=1200,       # 20 min
)
def run_forecast(
    self: Task,
    id_instalacao: str,
    id_municipio: Optional[str] = None,
    ano_inicio: int = 2014,
    ano_fim: Optional[int] = None,
    incluir_backtest: bool = True,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Task principal: treina SARIMAX + gera forecast 60m + (opcional) backtest.

    Armazena resultado no Redis com TTL de 24h para cache.
    """
    logger.info(
        "forecast_task_start porto=%s tenant=%s", id_instalacao, tenant_id
    )

    try:
        result = asyncio.run(
            _run_forecast_pipeline(
                id_instalacao=id_instalacao,
                id_municipio=id_municipio,
                ano_inicio=ano_inicio,
                ano_fim=ano_fim,
                incluir_backtest=incluir_backtest,
            )
        )

        # Salva no Redis para cache de 24h
        cache_key = _build_cache_key(id_instalacao, "forecast")
        asyncio.run(_store_in_redis(cache_key, result, FORECAST_CACHE_TTL))

        logger.info(
            "forecast_task_success porto=%s meses=%d",
            id_instalacao,
            result.get("n_meses_treino", 0),
        )
        return result

    except ValueError as exc:
        # Erro de negócio (dados insuficientes, porto inválido) — não faz retry
        logger.warning("forecast_task_business_error porto=%s: %s", id_instalacao, exc)
        return {"error": str(exc), "id_instalacao": id_instalacao}

    except Exception as exc:
        logger.error(
            "forecast_task_error porto=%s tentativa=%d: %s",
            id_instalacao,
            self.request.retries,
            exc,
        )
        countdown = 2 ** self.request.retries * 60
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(
    bind=True,
    name="app.tasks.forecasting.run_cenarios",
    queue="forecasting",
    max_retries=2,
    default_retry_delay=120,
    soft_time_limit=900,
    time_limit=1200,
)
def run_cenarios(
    self: Task,
    id_instalacao: str,
    id_municipio: Optional[str] = None,
    ano_inicio: int = 2014,
    ano_fim: Optional[int] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Task de cenários: gera projeções base/otimista/pessimista.
    """
    logger.info("cenarios_task_start porto=%s", id_instalacao)

    try:
        result = asyncio.run(
            _run_cenarios_pipeline(
                id_instalacao=id_instalacao,
                id_municipio=id_municipio,
                ano_inicio=ano_inicio,
                ano_fim=ano_fim,
            )
        )

        cache_key = _build_cache_key(id_instalacao, "cenarios")
        asyncio.run(_store_in_redis(cache_key, result, FORECAST_CACHE_TTL))

        logger.info("cenarios_task_success porto=%s", id_instalacao)
        return result

    except ValueError as exc:
        logger.warning("cenarios_task_business_error porto=%s: %s", id_instalacao, exc)
        return {"error": str(exc), "id_instalacao": id_instalacao}

    except Exception as exc:
        logger.error("cenarios_task_error porto=%s: %s", id_instalacao, exc)
        countdown = 2 ** self.request.retries * 60
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(
    name="app.tasks.forecasting.precompute_forecasts",
    queue="forecasting",
    soft_time_limit=3600,  # 1h para rodar todos os portos
    time_limit=4200,
)
def precompute_forecasts(
    portos: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Task de pre-computação diária (acionada pelo beat schedule).

    Roda o forecast para cada porto da lista e armazena no Redis.
    Quando o usuário abre o módulo 11, o resultado já está em cache.
    """
    portos_list = portos or DEFAULT_PORTOS_PRECOMPUTE
    logger.info("precompute_start n_portos=%d", len(portos_list))

    resultados = {"sucesso": [], "erro": []}

    for porto in portos_list:
        try:
            result = asyncio.run(
                _run_forecast_pipeline(
                    id_instalacao=porto,
                    id_municipio=None,
                    ano_inicio=2014,
                    ano_fim=None,  # None = ano corrente (dinâmico)
                    incluir_backtest=False,  # backtest opcional no pre-compute
                )
            )
            cache_key = _build_cache_key(porto, "forecast")
            asyncio.run(_store_in_redis(cache_key, result, FORECAST_CACHE_TTL))
            resultados["sucesso"].append(porto)
            logger.info("precompute_ok porto=%s", porto)

        except Exception as exc:
            resultados["erro"].append({"porto": porto, "erro": str(exc)[:200]})
            logger.warning("precompute_fail porto=%s: %s", porto, exc)

    logger.info(
        "precompute_done sucesso=%d erro=%d",
        len(resultados["sucesso"]),
        len(resultados["erro"]),
    )
    return resultados
