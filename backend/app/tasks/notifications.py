"""Envio de notificações ao concluir análises de impacto."""

from __future__ import annotations

from app.core.logging import get_logger

import asyncio
from collections.abc import Mapping

from app.config import get_settings
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


async def _notify_sync(analysis_id: str, tenant_id: str) -> None:
    """Dispara notificações em background (implementação síncrona por etapas)."""
    from app.db.base import AsyncSessionLocal
    from app.db.models.economic_impact_analysis import EconomicImpactAnalysis
    from app.db.models.notification_preference import NotificationPreference
    from app.db.models.user import User
    from app.services.notification_service import NotificationService
    from app.services.notification_service import NotificationService as _Service
    from sqlalchemy import select

    settings = get_settings()
    if not settings.notifications_enabled:
        return

    async with AsyncSessionLocal() as db:
        analysis = await db.get(EconomicImpactAnalysis, analysis_id)
        if analysis is None or str(analysis.tenant_id) != tenant_id:
            return
        if not analysis.user_id:
            return
        service = _Service(tenant_id=analysis.tenant_id, user_id=analysis.user_id)
        preferences = await service.list_for_user(db)
        if not preferences:
            return

        payload = {
            "analysis_id": str(analysis.id),
            "tenant_id": str(analysis.tenant_id),
            "user_id": str(analysis.user_id),
            "method": analysis.method,
            "status": analysis.status,
        }

        # Importa utilitário HTTP/Email apenas aqui para manter dependências leves
        import httpx

        for pref in preferences:
            if not pref.enabled:
                continue
            if pref.channel == "webhook" and pref.endpoint:
                try:
                    async with httpx.AsyncClient(timeout=8.0) as client:
                        await client.post(pref.endpoint, json=payload)
                except Exception as exc:  # pragma: no cover - integração externa
                    logger.error("Webhook notification failed: %s", exc)
            elif pref.channel == "email" and (pref.endpoint):
                # Envio email mínimo: fallback por endpoint vazio -> pular silenciosamente.
                logger.info(
                    "Notificação email pendente de provedor SMTP: %s",
                    {"to": pref.endpoint, "analysis_id": analysis_id},
                )


@celery_app.task(name="app.tasks.notifications.notify_analysis_complete", bind=True)
def notify_analysis_complete(self, analysis_id: str, tenant_id: str) -> None:
    """Task Celery chamada ao finalizar análise causal."""
    logger.info("Notificação de análise %s iniciada (tenant=%s)", analysis_id, tenant_id)
    asyncio.run(_notify_sync(analysis_id, tenant_id))
