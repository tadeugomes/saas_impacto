"""Perfil e preferências do usuário autenticado."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.base import get_db
from app.db.models.user import User
from app.schemas.notification import (
    NotificationPreferenceCreate,
    NotificationPreferenceResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/users", tags=["Usuários"])


def _to_response(item) -> NotificationPreferenceResponse:
    return NotificationPreferenceResponse(
        id=str(item.id),
        channel=item.channel,
        endpoint=item.endpoint,
        enabled=item.enabled,
        created_at=(item.created_at.isoformat() if item.created_at else None),
        updated_at=(item.updated_at.isoformat() if item.updated_at else None),
    )


@router.get(
    "/me/notifications",
    response_model=list[NotificationPreferenceResponse],
    summary="Listar preferências de notificação",
)
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationPreferenceResponse]:
    """Retorna as preferências de notificação do usuário logado."""
    service = NotificationService(current_user.tenant_id, current_user.id)
    rows = await service.list_for_user(db)
    return [_to_response(item) for item in rows]


@router.put(
    "/me/notifications",
    response_model=list[NotificationPreferenceResponse],
    summary="Atualizar preferências de notificação",
)
async def update_notifications(
    payload: list[NotificationPreferenceCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationPreferenceResponse]:
    """Substitui a lista de preferências do usuário atual."""
    service = NotificationService(current_user.tenant_id, current_user.id)
    rows = await service.upsert_many(db, payload)
    return [_to_response(item) for item in rows]
