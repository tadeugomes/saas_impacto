"""Endpoints administrativos de dashboard de uso."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tenant_id, require_admin
from app.db.base import get_db
from app.schemas.admin import TenantUsageResponse
from app.services.dashboard_service import DashboardService, get_dashboard_service

router = APIRouter(prefix="/admin", tags=["Admin - Dashboard"])


@router.get(
    "/dashboard/usage",
    summary="Métricas agregadas de uso do tenant",
    response_model=TenantUsageResponse,
)
async def dashboard_usage(
    tenant_id=Depends(get_tenant_id),
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
    # Tenant plan vem do banco normalmente. Sem acesso aqui, usa limites default.
    rate_limit_cap = plan_caps.get("enterprise", 2000)
    return await service.usage(db=db, tenant_id=tenant_id, rate_limit_cap=rate_limit_cap)
