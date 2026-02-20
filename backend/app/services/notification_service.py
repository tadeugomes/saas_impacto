"""Serviços para preferências de notificação do usuário."""

from __future__ import annotations

import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification_preference import NotificationPreference


class NotificationService:
    """CRUD mínimo para preferences de notificação por usuário."""

    def __init__(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def list_for_user(self, db: AsyncSession) -> list[NotificationPreference]:
        """Retorna preferências do usuário atual."""
        stmt = select(NotificationPreference).where(
            NotificationPreference.tenant_id == self.tenant_id,
            NotificationPreference.user_id == self.user_id,
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def upsert_many(
        self,
        db: AsyncSession,
        payload: Iterable[NotificationPreference],
    ) -> list[NotificationPreference]:
        """Substitui as preferências do usuário e retorna o estado atual."""
        await db.execute(
            NotificationPreference.__table__.delete().where(
                NotificationPreference.tenant_id == self.tenant_id,
                NotificationPreference.user_id == self.user_id,
            )
        )

        new_rows: list[NotificationPreference] = []
        seen_channels: set[str] = set()
        for item in payload:
            channel = item.channel.strip().lower()
            if channel in seen_channels:
                continue
            seen_channels.add(channel)
            row = NotificationPreference(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                channel=channel,
                endpoint=(item.endpoint or "").strip(),
                enabled=item.enabled,
            )
            db.add(row)
            new_rows.append(row)

        await db.commit()
        return new_rows
