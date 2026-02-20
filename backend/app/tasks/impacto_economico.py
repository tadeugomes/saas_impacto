"""
Celery Task — Execução assíncrona de análises causais de impacto econômico.

Fluxo:
  1. Router cria o registro com status='queued' e despacha esta task via .delay()
  2. Worker pega a task da fila ``economic_impact``
  3. Task abre uma AsyncSession, ativa RLS, e delega ao AnalysisService._execute()
  4. _execute() marca running → roda pipeline causal → persiste success|failed

A task usa ``asyncio.run()`` para executar código async dentro do contexto
síncrono do worker Celery. Cada invocação cria seu próprio event loop isolado.

Retentativas:
  Em caso de exceção inesperada, a task tenta novamente até ``max_retries``
  vezes com backoff exponencial (``countdown = 2 ** self.request.retries * 60``).
  Erros de negócio (análise não encontrada, pipeline falhou) são capturados
  pelo AnalysisService e salvos como status='failed' — não disparam retry.
"""
from __future__ import annotations

import asyncio
import logging
import uuid

from celery import Task
from sqlalchemy import select, text

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


# ── Helper assíncrono ──────────────────────────────────────────────────────


async def _execute_analysis_async(analysis_id: str, tenant_id: str) -> None:
    """Executa o pipeline causal para a análise indicada.

    Abre uma AsyncSession dedicada (independente da sessão HTTP), ativa o
    contexto RLS e delega ao ``AnalysisService._execute()``.

    Parameters
    ----------
    analysis_id:
        UUID (str) da análise com status='queued'.
    tenant_id:
        UUID (str) do tenant; necessário para ativar o SET LOCAL RLS.
    """
    # Importações internas para evitar circular imports no load do módulo
    from app.db.base import AsyncSessionLocal
    from app.db.models.economic_impact_analysis import EconomicImpactAnalysis
    from app.schemas.impacto_economico import EconomicImpactAnalysisCreateRequest
    from app.services.impacto_economico.analysis_service import (
        AnalysisService,
        AnalysisNotFoundError,
    )

    _analysis_id = uuid.UUID(analysis_id)
    _tenant_id = uuid.UUID(tenant_id)

    async with AsyncSessionLocal() as db:
        # 1. Ativar contexto RLS para a sessão
        await db.execute(
            text("SET LOCAL app.current_tenant_id = :tid"),
            {"tid": tenant_id},
        )

        # 2. Buscar registro da análise
        stmt = select(EconomicImpactAnalysis).where(
            EconomicImpactAnalysis.id == _analysis_id,
            EconomicImpactAnalysis.tenant_id == _tenant_id,
        )
        result = await db.execute(stmt)
        analysis = result.scalar_one_or_none()

        if analysis is None:
            logger.error(
                "Análise %s não encontrada para tenant %s — task abortada.",
                analysis_id,
                tenant_id,
            )
            return  # Não há o que fazer; sem retry (seria idempotente)

        # 3. Reconstruir request a partir dos parâmetros persistidos
        try:
            request = EconomicImpactAnalysisCreateRequest(**analysis.request_params)
        except Exception as exc:
            logger.error(
                "Parâmetros inválidos para análise %s: %s — marcando como failed.",
                analysis_id,
                exc,
            )
            analysis.mark_failed(f"Parâmetros inválidos: {exc}")
            await db.commit()
            return

        # 4. Executar pipeline causal (marca running → success|failed internamente)
        service = AnalysisService(db=db, tenant_id=_tenant_id)
        await service._execute(analysis, request)

        logger.info("Análise %s concluída com status='%s'.", analysis_id, analysis.status)


# ── Task Celery ────────────────────────────────────────────────────────────


@celery_app.task(
    bind=True,
    name="app.tasks.impacto_economico.run_economic_impact_analysis",
    max_retries=3,
    acks_late=True,           # ack somente após conclusão (proteção a crash)
    reject_on_worker_lost=True,  # re-enfileira se o worker morrer
)
def run_economic_impact_analysis(
    self: Task,
    analysis_id: str,
    tenant_id: str,
) -> dict[str, str]:
    """Executa análise causal de impacto econômico em background.

    Chamada via::

        run_economic_impact_analysis.delay(str(analysis.id), str(tenant_id))

    Parameters
    ----------
    analysis_id:
        UUID (str) da análise criada com status='queued'.
    tenant_id:
        UUID (str) do tenant; propagado para ativar a policy RLS.

    Returns
    -------
    dict:
        ``{"analysis_id": "<uuid>", "status": "done"}`` em caso de sucesso.

    Raises
    ------
    Celery Retry:
        Em exceções inesperadas (falha de rede, BQ indisponível, etc.) a
        task é reenfileirada com backoff exponencial (60 s × 2^retry).
    """
    logger.info(
        "Worker iniciando análise %s (tenant=%s, tentativa=%d/%d)",
        analysis_id,
        tenant_id,
        self.request.retries + 1,
        self.max_retries + 1,
    )

    try:
        asyncio.run(_execute_analysis_async(analysis_id, tenant_id))
        logger.info("Task concluída para análise %s.", analysis_id)
        return {"analysis_id": analysis_id, "status": "done"}

    except Exception as exc:
        # Backoff exponencial: 60 s, 120 s, 240 s
        countdown = 60 * (2 ** self.request.retries)
        logger.exception(
            "Erro inesperado na análise %s (retry em %ds): %s",
            analysis_id,
            countdown,
            exc,
        )
        raise self.retry(exc=exc, countdown=countdown)
