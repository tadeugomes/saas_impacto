"""
Endpoints do Módulo 11 — Forecasting Assíncrono via Celery.

Padrão fire-and-poll:
  POST /indicators/forecast/run    → despacha task, retorna task_id
  GET  /indicators/forecast/status/{task_id} → status + resultado quando pronto
  GET  /indicators/forecast/cached/{id_instalacao} → resultado do cache (se existir)
  POST /indicators/forecast/precompute → dispara pre-computação manual (admin)

O frontend usa o padrão:
  1. POST run → recebe task_id
  2. Polling em GET status/{task_id} a cada 3s até state=SUCCESS ou FAILURE
  3. Exibe resultado
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.deps import require_indicator_permission, require_admin
from app.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/indicators/forecast",
    tags=["Módulo 11 — Forecasting"],
)


# ── Schemas ────────────────────────────────────────────────────────────────


def _current_year() -> int:
    from datetime import datetime
    return datetime.now().year


class ForecastRunRequest(BaseModel):
    id_instalacao: str = Field(..., description="Nome do porto (ex: 'Santos')")
    id_municipio: Optional[str] = Field(None, description="Código IBGE do município")
    ano_inicio: int = Field(2014, ge=2010, le=2023, description="Ano de início da série")
    ano_fim: int = Field(default_factory=_current_year, ge=2014, le=2030, description="Ano de fim da série (default: ano corrente)")
    incluir_backtest: bool = Field(True, description="Incluir backtesting walk-forward")


class CenariosRunRequest(BaseModel):
    id_instalacao: str = Field(..., description="Nome do porto")
    id_municipio: Optional[str] = Field(None)
    ano_inicio: int = Field(2014, ge=2010, le=2023)
    ano_fim: int = Field(default_factory=_current_year, ge=2014, le=2030)


class PrecomputeRequest(BaseModel):
    portos: Optional[list[str]] = Field(
        None,
        description="Lista de portos. Se vazio, usa a lista padrão do sistema.",
    )


class TaskStatusResponse(BaseModel):
    task_id: str
    state: str  # PENDING | STARTED | SUCCESS | FAILURE | RETRY
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[str] = None


# ── Helpers ────────────────────────────────────────────────────────────────


def _get_celery_task_status(task_id: str) -> Dict[str, Any]:
    """Lê estado da task diretamente do Celery result backend (Redis)."""
    from celery.result import AsyncResult
    from app.tasks.celery_app import celery_app

    result = AsyncResult(task_id, app=celery_app)
    state = result.state

    if state == "SUCCESS":
        return {"state": "SUCCESS", "result": result.result}
    if state == "FAILURE":
        return {
            "state": "FAILURE",
            "error": str(result.result) if result.result else "Erro desconhecido",
        }
    if state == "STARTED":
        return {"state": "STARTED", "progress": "Modelo em treinamento..."}
    # PENDING ou RETRY
    return {"state": state, "progress": "Aguardando worker disponível..."}


async def _get_cached_forecast(id_instalacao: str, task_type: str = "forecast") -> Optional[Dict]:
    """Busca resultado de forecast no cache Redis (pre-computado ou de execução anterior)."""
    try:
        from app.core.redis import get_redis_client

        redis = await get_redis_client()
        key = f"forecast:{task_type}:{id_instalacao.lower().replace(' ', '_')}"
        raw = await redis.get(key)
        if raw:
            return json.loads(raw)
    except Exception as exc:
        logger.warning("forecast_cache_read_error: %s", exc)
    return None


# ── Endpoints ──────────────────────────────────────────────────────────────


@router.post(
    "/run",
    summary="Iniciar Forecast de Tonelagem (assíncrono)",
    description="""
Despacha o pipeline SARIMAX para a fila Celery e retorna imediatamente
com um `task_id`. Use GET /forecast/status/{task_id} para acompanhar.

**Tempo estimado:** 1 a 3 minutos dependendo do porto e do número de features.

Se já houver resultado em cache (pre-computado ou de execução recente nas últimas 24h),
o campo `cached` retorna `true` e o resultado está disponível imediatamente em
GET /forecast/cached/{id_instalacao}.
""",
)
async def run_forecast(
    request: ForecastRunRequest,
    current_user: User = Depends(require_indicator_permission("read")),
) -> JSONResponse:
    # Verifica se já existe resultado em cache antes de disparar nova task
    cached = await _get_cached_forecast(request.id_instalacao, "forecast")
    if cached:
        return JSONResponse(
            content={
                "task_id": None,
                "state": "SUCCESS",
                "cached": True,
                "message": "Resultado disponível em cache (últimas 24h). "
                           f"Use GET /forecast/cached/{request.id_instalacao}",
                "id_instalacao": request.id_instalacao,
            }
        )

    from app.tasks.forecasting import run_forecast as forecast_task

    task = forecast_task.apply_async(
        kwargs={
            "id_instalacao": request.id_instalacao,
            "id_municipio": request.id_municipio,
            "ano_inicio": request.ano_inicio,
            "ano_fim": request.ano_fim,
            "incluir_backtest": request.incluir_backtest,
            "tenant_id": str(current_user.tenant_id) if hasattr(current_user, "tenant_id") else None,
        },
        queue="forecasting",
    )

    logger.info(
        "forecast_task_dispatched porto=%s task_id=%s user=%s",
        request.id_instalacao,
        task.id,
        current_user.id,
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "task_id": task.id,
            "state": "PENDING",
            "cached": False,
            "message": "Forecast iniciado. Consulte o status em GET /forecast/status/{task_id}",
            "id_instalacao": request.id_instalacao,
            "poll_interval_seconds": 5,
        },
    )


@router.post(
    "/cenarios/run",
    summary="Iniciar Cenários de Forecast (assíncrono)",
    description="Despacha geração de cenários base/otimista/pessimista para a fila Celery.",
)
async def run_cenarios(
    request: CenariosRunRequest,
    current_user: User = Depends(require_indicator_permission("read")),
) -> JSONResponse:
    cached = await _get_cached_forecast(request.id_instalacao, "cenarios")
    if cached:
        return JSONResponse(
            content={
                "task_id": None,
                "state": "SUCCESS",
                "cached": True,
                "message": f"Resultado em cache. Use GET /forecast/cached/{request.id_instalacao}?tipo=cenarios",
                "id_instalacao": request.id_instalacao,
            }
        )

    from app.tasks.forecasting import run_cenarios as cenarios_task

    task = cenarios_task.apply_async(
        kwargs={
            "id_instalacao": request.id_instalacao,
            "id_municipio": request.id_municipio,
            "ano_inicio": request.ano_inicio,
            "ano_fim": request.ano_fim,
            "tenant_id": str(current_user.tenant_id) if hasattr(current_user, "tenant_id") else None,
        },
        queue="forecasting",
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "task_id": task.id,
            "state": "PENDING",
            "cached": False,
            "message": "Cenários iniciados. Consulte o status em GET /forecast/status/{task_id}",
            "id_instalacao": request.id_instalacao,
            "poll_interval_seconds": 5,
        },
    )


@router.get(
    "/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="Status da Task de Forecast",
    description="""
Consulta o estado atual de uma task de forecast.

**Estados possíveis:**
- `PENDING`: na fila, aguardando worker
- `STARTED`: worker iniciou o processamento
- `SUCCESS`: concluído — `result` contém o payload completo
- `FAILURE`: falhou — `error` contém a mensagem
- `RETRY`: em nova tentativa após erro transitório
""",
)
def get_forecast_status(
    task_id: str,
    current_user: User = Depends(require_indicator_permission("read")),
) -> TaskStatusResponse:
    info = _get_celery_task_status(task_id)
    return TaskStatusResponse(
        task_id=task_id,
        state=info["state"],
        result=info.get("result"),
        error=info.get("error"),
        progress=info.get("progress"),
    )


@router.get(
    "/cached/{id_instalacao}",
    summary="Resultado em Cache do Forecast",
    description="""
Retorna o resultado de forecast armazenado em cache (pre-computado ou de execução anterior).

Use `?tipo=cenarios` para buscar cenários em vez do forecast principal.

Retorna 404 se não houver resultado em cache para o porto.
""",
)
async def get_cached_forecast(
    id_instalacao: str,
    tipo: str = Query("forecast", pattern="^(forecast|cenarios)$"),
    current_user: User = Depends(require_indicator_permission("read")),
) -> JSONResponse:
    cached = await _get_cached_forecast(id_instalacao, tipo)
    if not cached:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Sem resultado em cache para '{id_instalacao}' (tipo={tipo}). "
                "Inicie o processamento via POST /forecast/run"
            ),
        )
    return JSONResponse(content={"cached": True, "data": cached})


@router.post(
    "/precompute",
    summary="Pre-computar Forecasts (admin)",
    description="""
Dispara pre-computação manual de forecasts para uma lista de portos.
Se `portos` for vazio, usa a lista padrão do sistema.

**Requer role admin.**
""",
)
async def trigger_precompute(
    request: PrecomputeRequest,
    _: User = Depends(require_admin),
) -> JSONResponse:
    from app.tasks.forecasting import precompute_forecasts

    task = precompute_forecasts.apply_async(
        kwargs={"portos": request.portos},
        queue="forecasting",
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "task_id": task.id,
            "state": "PENDING",
            "message": "Pre-computação iniciada.",
            "portos": request.portos or "lista padrão do sistema",
        },
    )


@router.get(
    "/cache/clear/{id_instalacao}",
    summary="Limpar Cache de um Porto (admin)",
    description="Remove resultado em cache para forçar nova computação.",
)
async def clear_forecast_cache(
    id_instalacao: str,
    tipo: str = Query("forecast", pattern="^(forecast|cenarios)$"),
    _: User = Depends(require_admin),
) -> JSONResponse:
    try:
        from app.core.redis import get_redis_client

        redis = await get_redis_client()
        key = f"forecast:{tipo}:{id_instalacao.lower().replace(' ', '_')}"
        deleted = await redis.delete(key)
        return JSONResponse(
            content={
                "deleted": bool(deleted),
                "key": key,
                "message": "Cache removido." if deleted else "Chave não encontrada no cache.",
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao limpar cache: {exc}",
        )
