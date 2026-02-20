"""Schemas para preferências de notificação."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NotificationPreferenceCreate(BaseModel):
    """Payload de criação ou atualização individual."""

    channel: str = Field(..., description="email ou webhook")
    endpoint: str | None = Field(default=None, description="Email ou URL de webhook")
    enabled: bool = Field(default=True, description="Se a preferência está ativa.")


class NotificationPreferenceResponse(BaseModel):
    """Preferência persistida do usuário atual."""

    id: str
    channel: str
    endpoint: str | None
    enabled: bool
    created_at: str | None = None
    updated_at: str | None = None
