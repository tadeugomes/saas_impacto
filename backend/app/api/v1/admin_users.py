"""
Endpoints de administração de usuários.

Permite listar usuários por tenant e ajustar status/roles.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.base import get_db
from app.db.models.user import User
from app.schemas.admin import UserAdminItem, UserAdminListResponse, UserStatusUpdate


router = APIRouter(prefix="/admin", tags=["Admin - Usuários"])


@router.get(
    "/tenants/{tenant_id}/users",
    response_model=UserAdminListResponse,
    summary="Listar usuários do tenant",
    description="""
    Retorna usuários do tenant, paginados.
    """,
)
async def list_tenant_users(
    tenant_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ativo: Optional[bool] = Query(None, description="Filtrar por ativos/inativos"),
    nome: Optional[str] = Query(None, description="Busca por nome/email"),
    _: object = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserAdminListResponse:
    """Lista usuários do tenant com paginação e filtros."""
    conditions = [User.tenant_id == tenant_id]

    if ativo is not None:
        conditions.append(User.ativo.is_(ativo))

    if nome:
        normalized = f"%{nome.strip()}%"
        conditions.append(
            or_(
                User.nome.ilike(normalized),
                User.email.ilike(normalized),
            )
        )

    total_result = await db.execute(select(func.count()).select_from(User).where(*conditions))
    total = int(total_result.scalar_one() or 0)

    offset = (page - 1) * page_size
    result = await db.execute(
        select(User)
        .where(*conditions)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = list(result.scalars().all())

    page_count = (total + page_size - 1) // page_size
    return UserAdminListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=page_count,
        items=[
            UserAdminItem(
                id=str(user.id),
                email=user.email,
                nome=user.nome,
                roles=list(user.roles or []),
                ativo=bool(user.ativo),
                created_at=user.created_at.isoformat() if user.created_at else "",
                updated_at=user.updated_at.isoformat() if user.updated_at else None,
                last_login=user.last_login.isoformat() if user.last_login else None,
            )
            for user in rows
        ],
    )


@router.patch(
    "/users/{user_id}",
    response_model=UserAdminItem,
    summary="Atualizar usuário",
    description="Atualiza status e/ou roles do usuário.",
)
async def update_user(
    user_id: uuid.UUID,
    payload: UserStatusUpdate,
    _: object = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserAdminItem:
    """Atualiza usuário sem remover o histórico de acesso."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user não encontrado",
        )

    updates = payload.model_dump(exclude_none=True)
    if "roles" in updates and updates["roles"] is not None:
        roles = [str(role).strip().lower() for role in updates["roles"] if str(role).strip()]
        user.roles = roles

    if "ativo" in updates and updates["ativo"] is not None:
        user.ativo = bool(updates["ativo"])

    await db.commit()
    await db.refresh(user)

    return UserAdminItem(
        id=str(user.id),
        email=user.email,
        nome=user.nome,
        roles=list(user.roles or []),
        ativo=bool(user.ativo),
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@router.delete(
    "/users/{user_id}",
    summary="Desativar usuário",
    description="Marca o usuário como inativo (soft delete).",
)
async def deactivate_user(
    user_id: uuid.UUID,
    _: object = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Desativa usuário sem remover dados."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user não encontrado",
        )

    user.ativo = False
    await db.commit()
    return {"status": "ok", "user_id": str(user.id), "ativo": "false"}
