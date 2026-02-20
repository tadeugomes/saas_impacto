"""Envio de notificações ao concluir análises de impacto."""

from __future__ import annotations

from app.config import get_settings
from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

import asyncio

import httpx

logger = get_logger(__name__)


def _build_notification_payload(analysis) -> dict[str, str]:
    """Monta payload comum de notificação."""
    return {
        "analysis_id": str(analysis.id),
        "tenant_id": str(analysis.tenant_id),
        "user_id": str(analysis.user_id),
        "method": analysis.method,
        "status": analysis.status,
    }


async def _send_webhook(endpoint: str, payload: dict[str, str]) -> None:
    """Dispara POST no endpoint de webhook configurado."""
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.post(endpoint, json=payload)
        response.raise_for_status()


async def _send_email(endpoint: str, payload: dict[str, str]) -> None:
    """Dispara e-mail de notificação usando SendGrid HTTP API."""
    settings = get_settings()
    if not settings.sendgrid_api_key:
        logger.warning(
            "SendGrid não configurado; notificação por email será ignorada.",
            extra={"analysis_id": payload["analysis_id"], "to": endpoint},
        )
        return

    message = (
        f"Sua análise terminou.\n\n"
        f"ID: {payload['analysis_id']}\n"
        f"Tenant: {payload['tenant_id']}\n"
        f"Método: {payload['method']}\n"
        f"Status: {payload['status']}"
    )
    request_payload = {
        "personalizations": [
            {
                "to": [{"email": endpoint}],
            }
        ],
        "from": {"email": settings.sendgrid_from_email},
        "subject": "Notificação de análise concluída",
        "content": [
            {"type": "text/plain", "value": message},
        ],
    }

    headers = {
        "Authorization": f"Bearer {settings.sendgrid_api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=request_payload,
            headers=headers,
        )
        response.raise_for_status()


async def _notify_sync(analysis_id: str, tenant_id: str) -> list[str]:
    """Dispara notificações em background (implementação síncrona)."""
    from app.db.base import AsyncSessionLocal
    from app.services.notification_service import NotificationService

    settings = get_settings()
    if not settings.notifications_enabled:
        return []

    async with AsyncSessionLocal() as db:
        from app.db.models.economic_impact_analysis import EconomicImpactAnalysis

        analysis = await db.get(EconomicImpactAnalysis, analysis_id)
        if analysis is None or str(analysis.tenant_id) != tenant_id:
            return []
        if not analysis.user_id:
            return []

        service = NotificationService(tenant_id=analysis.tenant_id, user_id=analysis.user_id)
        preferences = await service.list_for_user(db)
        if not preferences:
            return []

        payload = _build_notification_payload(analysis)
        failures: list[str] = []
        for pref in preferences:
            if not pref.enabled:
                continue
            if not pref.endpoint:
                failures.append(f"{pref.channel}:<sem endpoint>")
                logger.warning(
                    "Preferência de notificação sem endpoint, ignorando.",
                    extra={"analysis_id": analysis_id, "channel": pref.channel},
                )
                continue
            if pref.channel == "webhook":
                try:
                    await _send_webhook(pref.endpoint, payload)
                except Exception as exc:
                    failures.append(f"webhook:{pref.endpoint}")
                    logger.error(
                        "Falha no envio de webhook: %s",
                        str(exc),
                        extra={"analysis_id": analysis_id, "endpoint": pref.endpoint},
                    )
            elif pref.channel == "email":
                try:
                    await _send_email(pref.endpoint, payload)
                except Exception as exc:
                    failures.append(f"email:{pref.endpoint}")
                    logger.error(
                        "Falha no envio de email: %s",
                        str(exc),
                        extra={"analysis_id": analysis_id, "email": pref.endpoint},
                    )
            else:
                failures.append(f"channel:{pref.channel}")
                logger.error(
                    "Canal de notificação desconhecido: %s",
                    pref.channel,
                    extra={"analysis_id": analysis_id},
                )

        return failures


@celery_app.task(
    name="app.tasks.notifications.notify_analysis_complete",
    bind=True,
    max_retries=3,
    acks_late=True,
    reject_on_worker_lost=True,
)
def notify_analysis_complete(self, analysis_id: str, tenant_id: str) -> dict[str, str]:
    """Task Celery chamada ao finalizar análise causal."""
    logger.info(
        "Notificação de análise %s iniciada (tenant=%s, tentativa=%s)",
        analysis_id,
        tenant_id,
        self.request.retries + 1,
    )

    try:
        failures = asyncio.run(_notify_sync(analysis_id, tenant_id))
        if failures:
            raise RuntimeError(f"Falha no envio para {len(failures)} destino(s): {', '.join(failures)}")
        return {"analysis_id": analysis_id, "status": "done"}
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            logger.error(
                "Notificação de análise %s falhou após %d tentativas: %s",
                analysis_id,
                self.request.retries + 1,
                exc,
            )
            return {"analysis_id": analysis_id, "status": "failed"}

        countdown = 60 * (2**self.request.retries)
        logger.warning(
            "Falha temporária no envio da análise %s. Retentando em %ds",
            analysis_id,
            countdown,
        )
        raise self.retry(exc=exc, countdown=countdown)
