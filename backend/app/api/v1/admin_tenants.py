"""
Endpoints administrativos de Tenant.

Permite operações básicas de criação/listagem/edição de tenants e
controle de soft-delete.
"""

from __future__ import annotations

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.tenant import get_tenant_id
from app.db.base import get_db
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.schemas.admin import (
    TenantActivationUpdate,
    TenantCreate,
    TenantDetail,
    TenantListResponse,
    TenantUpdate,
)
from app.schemas.admin import TenantListItem
from app.services.tenant_permission_service import TenantPermissionService
from app.services.tenant_permission_service import get_tenant_permission_service


router = APIRouter(prefix="/admin/tenants", tags=["Admin - Tenants"])


def _as_tenant_payload(tenant: Tenant, users_count: Optional[int] = None) -> TenantListItem:
    """Converte entidade Tenant em payload de resposta."""
    payload = {
        "id": str(tenant.id),
        "nome": tenant.nome,
        "slug": tenant.slug,
        "plano": tenant.plano,
        "cnpj": tenant.cnpj,
        "ativo": tenant.ativo,
        "instalacoes_permitidas": tenant.instalacoes_permitidas,
        "updated_at": str(tenant.updated_at.isoformat()) if tenant.updated_at else None,
        "created_at": str(tenant.created_at.isoformat()) if tenant.created_at else None,
    }
    if users_count is not None:
        payload["users_count"] = users_count
    return TenantListItem.model_validate(payload)


@router.post(
    "",
    response_model=TenantDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Criar tenant",
)
async def create_tenant(
    payload: TenantCreate,
    _: object = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    permission_service: TenantPermissionService = Depends(get_tenant_permission_service),
) -> TenantDetail:
    """Cria novo tenant com política inicial."""
    normalized_payload = payload.dict(exclude_none=True)
    if normalized_payload.get("allowed_installations"):
        normalized_payload["instalacoes_permitidas"] = json.dumps(
            normalized_payload["allowed_installations"],
            ensure_ascii=False,
        )
    else:
        normalized_payload["instalacoes_permitidas"] = json.dumps(
            payload.instalacoes_permitidas or [],
            ensure_ascii=False,
        )

    tenant = Tenant(
        nome=normalized_payload["nome"],
        slug=normalized_payload["slug"],
        cnpj=normalized_payload.get("cnpj"),
        plano=normalized_payload["plano"],
        instalacoes_permitidas=normalized_payload["instalacoes_permitidas"],
        ativo=True,
    )
    db.add(tenant)
    await db.flush()

    # Pré-semeia permissões mínimas por role default para o tenant criado.
    try:
        for role in ("viewer", "analyst", "admin"):
            await permission_service.set_permissions_for_role(
                db=db,
                tenant_id=tenant.id,
                role=role,
                permissions=[],
            )
    except Exception:
        # Não falha o cadastro se o seed falhar parcialmente.
        await db.rollback()
        raise

    await db.commit()
    await db.refresh(tenant)

    # Compatibilidade com TenantDetail.
    return TenantDetail(
        id=str(tenant.id),
        nome=tenant.nome,
        slug=tenant.slug,
        cnpj=tenant.cnpj,
        plano=tenant.plano,
        ativo=tenant.ativo,
        instalacoes_permitidas=tenant.instalacoes_permitidas,
        updated_at=str(tenant.updated_at.isoformat()) if tenant.updated_at else None,
        created_at=str(tenant.created_at.isoformat()) if tenant.created_at else None,
    )


@router.get("", response_model=TenantListResponse, summary="Listar tenants")
async def list_tenants(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _: object = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantListResponse:
    """Lista tenants com paginação."""
    del tenant_id
    total_result = await db.execute(select(func.count()).select_from(Tenant))
    total = int(total_result.scalar_one() or 0)
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Tenant).order_by(Tenant.created_at.desc()).offset(offset).limit(page_size)
    )
    rows = list(result.scalars().all())

    users_count_result = await db.execute(
        select(
            User.tenant_id,
            func.count(User.id).label("total_users"),
        )
        .group_by(User.tenant_id)
    )
    users_map = {str(row[0]): int(row[1] or 0) for row in users_count_result.all()}

    page_count = (total + page_size - 1) // page_size
    return TenantListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=page_count,
        items=[
            _as_tenant_payload(tenant, users_count=users_map.get(str(tenant.id), 0))
            for tenant in rows
        ],
    )


@router.get(
    "/{tenant_uuid}",
    response_model=TenantDetail,
    summary="Detalhar tenant",
)
async def get_tenant(
    tenant_uuid: uuid.UUID,
    _: object = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantDetail:
    """Detalha tenant por id."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="tenant não encontrado",
        )

    return TenantDetail(
        id=str(tenant.id),
        nome=tenant.nome,
        slug=tenant.slug,
        cnpj=tenant.cnpj,
        plano=tenant.plano,
        ativo=tenant.ativo,
        instalacoes_permitidas=tenant.instalacoes_permitidas,
        updated_at=str(tenant.updated_at.isoformat()) if tenant.updated_at else None,
        created_at=str(tenant.created_at.isoformat()) if tenant.created_at else None,
    )


@router.patch(
    "/{tenant_uuid}",
    response_model=TenantDetail,
    summary="Atualizar tenant",
)
async def patch_tenant(
    tenant_uuid: uuid.UUID,
    payload: TenantUpdate,
    _: object = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantDetail:
    """Atualiza nome/plano/ativo/cnpj do tenant."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="tenant não encontrado",
        )

    updates = payload.dict(exclude_none=True)
    if updates.get("instalacoes_permitidas") is not None:
        updates["instalacoes_permitidas"] = json.dumps(
            updates["instalacoes_permitidas"],
            ensure_ascii=False,
        )

    for key, value in updates.items():
        setattr(tenant, key, value)

    await db.commit()
    await db.refresh(tenant)

    return TenantDetail(
        id=str(tenant.id),
        nome=tenant.nome,
        slug=tenant.slug,
        cnpj=tenant.cnpj,
        plano=tenant.plano,
        ativo=tenant.ativo,
        instalacoes_permitidas=tenant.instalacoes_permitidas,
        updated_at=str(tenant.updated_at.isoformat()) if tenant.updated_at else None,
        created_at=str(tenant.created_at.isoformat()) if tenant.created_at else None,
    )


@router.patch(
    "/{tenant_uuid}/status",
    response_model=TenantDetail,
    summary="Atualizar status do tenant",
)
async def update_tenant_status(
    tenant_uuid: uuid.UUID,
    payload: TenantActivationUpdate,
    _: object = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantDetail:
    """Atualiza apenas o estado ativo/inativo do tenant."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="tenant não encontrado",
        )

    tenant.ativo = bool(payload.ativo)
    await db.commit()
    await db.refresh(tenant)

    return TenantDetail(
        id=str(tenant.id),
        nome=tenant.nome,
        slug=tenant.slug,
        cnpj=tenant.cnpj,
        plano=tenant.plano,
        ativo=tenant.ativo,
        instalacoes_permitidas=tenant.instalacoes_permitidas,
        updated_at=str(tenant.updated_at.isoformat()) if tenant.updated_at else None,
        created_at=str(tenant.created_at.isoformat()) if tenant.created_at else None,
    )


@router.delete(
    "/{tenant_uuid}",
    summary="Desativar tenant (soft delete)",
)
async def deactivate_tenant(
    tenant_uuid: uuid.UUID,
    _: object = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Desativa tenant sem remover dados físicos."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="tenant não encontrado",
        )

    tenant.ativo = False
    await db.commit()
    return {"status": "ok", "tenant_id": str(tenant.id), "ativo": str(tenant.ativo)}
