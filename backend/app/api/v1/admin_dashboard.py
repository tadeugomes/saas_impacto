"""Endpoints administrativos de dashboard de uso."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.api.deps import get_tenant_id, require_admin
from app.db.base import get_db
from app.db.models.tenant import Tenant
from app.schemas.admin import TenantUsageResponse
from app.services.dashboard_service import DashboardService, get_dashboard_service

router = APIRouter(prefix="/admin", tags=["Admin - Dashboard"])


@router.get(
    "/dashboard/usage",
    summary="Métricas agregadas de uso do tenant",
    response_model=TenantUsageResponse,
)
async def dashboard_usage(
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _: object = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
):
    """Retorna métricas de uso e atividade do tenant corrente."""
    plan_caps = {
        "basic": 100,
        "pro": 500,
        "enterprise": 2000,
    }
    tenant_plan = await _get_tenant_plan(db=db, tenant_id=tenant_id)
    rate_limit_cap = plan_caps.get(_normalize_plan(tenant_plan), 100)
    return await service.usage(db=db, tenant_id=tenant_id, rate_limit_cap=rate_limit_cap)


def _normalize_plan(plan: Optional[str]) -> str:
    normalized = (plan or "basic").strip().lower()
    if normalized not in {"basic", "pro", "enterprise"}:
        return "basic"
    return normalized


async def _get_tenant_plan(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    row = await db.execute(select(Tenant.plano).where(Tenant.id == tenant_id))
    return str(row.scalar_one_or_none() or "basic")
