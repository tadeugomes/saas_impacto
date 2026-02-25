"""Fluxo de registro de cliente (onboarding self-service)."""

from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.core.security import get_password_hash
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.schemas.admin import OnboardingCompanyRequest
from app.services.tenant_permission_service import TenantPermissionService


class OnboardingService:
    """Responsável por criação de tenant + usuário admin inicial."""

    async def register(
        self,
        db: AsyncSession,
        payload: OnboardingCompanyRequest,
        permission_service: TenantPermissionService,
    ) -> tuple[Tenant, User]:
        """Cria tenant e usuário admin, com rollback em qualquer falha."""
        slug = self._build_slug(payload.empresa)

        existing_tenant = await db.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        if existing_tenant.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um tenant com este identificador.",
            )

        tenant = Tenant(
            nome=payload.empresa.strip(),
            slug=slug,
            cnpj=payload.cnpj,
            plano=payload.plano,
            ativo=True,
            instalacoes_permitidas="[]",
        )
        db.add(tenant)
        await db.flush()

        existing_user = await db.execute(
            select(User).where(
                User.email == payload.email_admin,
                User.tenant_id == tenant.id,
            )
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email de admin já cadastrado.",
            )

        admin_user = User(
            tenant_id=tenant.id,
            nome=payload.nome_admin.strip(),
            email=payload.email_admin.strip().lower(),
            hashed_password=get_password_hash(payload.senha_admin),
            ativo=True,
            roles=["admin"],
        )
        db.add(admin_user)

        await db.flush()
        for role in ("viewer", "analyst", "admin"):
            await permission_service.set_permissions_for_role(
                db=db,
                tenant_id=tenant.id,
                role=role,
                permissions=[],
            )

        await db.commit()
        await db.refresh(admin_user)
        await db.refresh(tenant)
        return tenant, admin_user

    @staticmethod
    def _build_slug(name: str) -> str:
        """Gera slug seguro a partir do nome da empresa."""
        normalized = (name or "").strip().lower()
        normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
        normalized = normalized.strip("-")
        return normalized[:50] if len(normalized) <= 50 else normalized[:50]
