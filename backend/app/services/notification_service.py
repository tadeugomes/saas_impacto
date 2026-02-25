"""Serviços para preferências de notificação do usuário."""

from __future__ import annotations

import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.notification import NotificationPreferenceCreate
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
        payload: Iterable[NotificationPreferenceCreate],
    ) -> list[NotificationPreference]:
        """Substitui as preferências do usuário e retorna o estado atual."""
        await db.execute(
            NotificationPreference.__table__.delete().where(
                NotificationPreference.tenant_id == self.tenant_id,
                NotificationPreference.user_id == self.user_id,
            )
        )

        # Última preferência enviada por canal vence (ex.: overwrite no front).
        normalized_payload: dict[str, NotificationPreferenceCreate] = {}
        for item in payload:
            channel = item.channel.strip().lower()
            normalized_payload[channel] = NotificationPreferenceCreate(
                channel=channel,
                endpoint=item.endpoint.strip(),
                enabled=item.enabled,
            )

        new_rows: list[NotificationPreference] = []
        for channel, row in normalized_payload.items():
            db_row = NotificationPreference(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                channel=channel,
                endpoint=row.endpoint.strip(),
                enabled=row.enabled,
            )
            db.add(db_row)
            new_rows.append(db_row)

        await db.commit()
        return new_rows
