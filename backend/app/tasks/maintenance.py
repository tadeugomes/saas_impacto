"""Tarefas de manutenção e rotina operacional."""

from __future__ import annotations

from app.core.logging import get_logger
from app.db.base import AsyncSessionLocal
from app.services.audit_service import AuditService
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)
audit_service = AuditService()


@celery_app.task(name="app.tasks.maintenance.purge_expired_audit_logs")
def purge_expired_audit_logs() -> int:
    """Executa purge de logs de auditoria já vencidos.

    Retorna a quantidade de registros removidos.
    """
    async def _run() -> int:
        async with AsyncSessionLocal() as db:
            total = await audit_service.purge_expired(db)
            return total

    import asyncio

    deleted = asyncio.run(_run())
    logger.info("maintenance.purge_expired_audit_logs", deleted=deleted)
    return deleted


def purge_expired_audit_logs_sync() -> int:
    """Executa o mesmo job sem scheduler."""
    return purge_expired_audit_logs()
