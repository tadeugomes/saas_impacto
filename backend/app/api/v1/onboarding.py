"""Rotas de onboarding inicial de tenant e admin."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.admin import (
    OnboardingCompanyRequest,
    OnboardingCompanyResponse,
)
from app.services.auth_service import AuthService
from app.services.onboarding_service import OnboardingService
from app.services.tenant_permission_service import get_tenant_permission_service
from app.services.tenant_permission_service import TenantPermissionService


router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post(
    "/register",
    response_model=OnboardingCompanyResponse,
    summary="Cadastro inicial de cliente (self-service)",
)
async def register_company(
    payload: OnboardingCompanyRequest,
    db: AsyncSession = Depends(get_db),
    permission_service: TenantPermissionService = Depends(
        get_tenant_permission_service,
    ),
) -> OnboardingCompanyResponse:
    """Cria tenant + usuário admin e já retorna tokens de acesso."""
    onboarding_service = OnboardingService()
    tenant, admin_user = await onboarding_service.register(
        db=db,
        payload=payload,
        permission_service=permission_service,
    )

    auth_service = AuthService(db)
    tokens = await auth_service.create_tokens(admin_user)
    return OnboardingCompanyResponse(
        tenant_id=str(tenant.id),
        user_id=str(admin_user.id),
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
    )
