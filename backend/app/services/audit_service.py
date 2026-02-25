"""
Serviço de auditoria de eventos administrativos e operacionais.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import uuid
from inspect import isawaitable

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models.audit_log import AuditLog


class AuditService:
    """Persistência e consulta de logs de auditoria."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @staticmethod
    def _coerce_int(value: Optional[Any]) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    async def record_action(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID | str,
        action: str,
        resource: str,
        *,
        user_id: Optional[uuid.UUID | str] = None,
        status_code: Optional[int] = None,
        duration_ms: Optional[float | int] = None,
        bytes_processed: Optional[int] = None,
        ip: Optional[str] = None,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Registra um evento de auditoria (falha interna é sempre tolerada)."""
        try:
            tenant_uuid = uuid.UUID(str(tenant_id))
            user_uuid = uuid.UUID(str(user_id)) if user_id else None
            log = AuditLog(
                tenant_id=tenant_uuid,
                user_id=user_uuid,
                action=action,
                resource=resource,
                status_code=self._coerce_int(status_code),
                duration_ms=self._coerce_int(duration_ms),
                bytes_processed=self._coerce_int(bytes_processed),
                ip=ip,
                request_id=request_id,
                details=details or {},
            )
            maybe_awaitable = db.add(log)
            if isawaitable(maybe_awaitable):
                await maybe_awaitable
            await db.commit()
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            # Não quebra fluxo do endpoint por falha de auditoria
            return

    async def list_logs(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 50,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        user_id: Optional[str] = None,
        status_code: Optional[int] = None,
    ) -> tuple[list[AuditLog], int]:
        """Lista logs com filtros e paginação."""
        conditions = [AuditLog.tenant_id == tenant_id]

        if action:
            conditions.append(AuditLog.action == action)
        if resource:
            conditions.append(AuditLog.resource.ilike(f"%{resource}%"))
        if user_id:
            conditions.append(AuditLog.user_id == uuid.UUID(str(user_id)))
        if status_code is not None:
            conditions.append(AuditLog.status_code == self._coerce_int(status_code))

        base_query = select(AuditLog).where(and_(*conditions)).order_by(
            AuditLog.created_at.desc()
        )
        total_query = select(func.count()).select_from(base_query.subquery())

        count_result = await db.execute(total_query)
        total = int(count_result.scalar_one() or 0)

        page = max(page, 1)
        page_size = max(min(page_size, 500), 1)
        offset = (page - 1) * page_size
        result = await db.execute(
            base_query.offset(offset).limit(page_size)
        )
        items = list(result.scalars().all())

        return items, total

    async def purge_expired(self, db: AsyncSession) -> int:
        """Remove registros vencidos por retenção configurada."""
        retention_days = int(self.settings.audit_log_retention_days or 0)
        if retention_days <= 0:
            return 0

        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        delete_stmt = delete(AuditLog).where(AuditLog.created_at < cutoff)
        result = await db.execute(delete_stmt)
        await db.commit()
        return int(result.rowcount or 0)


def get_audit_service() -> AuditService:
    """Dependency provider."""
    return AuditService()
