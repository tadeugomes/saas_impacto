"""Preferências de notificação por usuário para análises de impacto."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class NotificationPreference(Base):
    """Preferência de entrega de notificações de análise."""

    __tablename__ = "notification_preferences"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel = Column(String(20), nullable=False)
    endpoint = Column(String(255), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = ()
