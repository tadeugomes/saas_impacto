"""
Endpoints administrativos (auditoria, compliance e controles operacionais).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.tenant import get_tenant_id
from app.db.base import get_db
from app.schemas.audit import AuditLogItem, AuditLogListResponse
from app.services.audit_service import AuditService, get_audit_service


router = APIRouter(
    prefix="/admin",
    tags=["Admin - Compliance"],
)


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="Consultar logs de auditoria",
    description="""
    Consulta os eventos auditados do tenant atual.

    Suporta paginação e filtros por `action`, `resource`, `user_id` e `status_code`.
    """,
)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    action: str | None = Query(None),
    resource: str | None = Query(None),
    user_id: str | None = Query(None),
    status_code: int | None = Query(None),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _: object = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditLogListResponse:
    """Lista logs de auditoria do tenant com paginação."""
    try:
        items, total = await audit_service.list_logs(
            db=db,
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            action=action,
            resource=resource,
            user_id=user_id,
            status_code=status_code,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar auditoria: {str(exc)}",
        )

    page_count = (total + page_size - 1) // page_size
    return AuditLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=page_count,
        items=[
            AuditLogItem(
                id=str(item.id),
                tenant_id=str(item.tenant_id),
                user_id=str(item.user_id) if item.user_id else None,
                action=item.action,
                resource=item.resource,
                status_code=item.status_code,
                duration_ms=item.duration_ms,
                bytes_processed=item.bytes_processed,
                ip=item.ip,
                details=dict(item.details or {}),
                request_id=item.request_id,
                created_at=item.created_at,
            )
            for item in items
        ],
    )
