"""Schemas para preferências de notificação."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Literal


class NotificationPreferenceCreate(BaseModel):
    """Payload de criação ou atualização individual."""

    channel: Literal["email", "webhook"] = Field(..., description="email ou webhook")
    endpoint: str | None = Field(default=None, description="Email ou URL de webhook")
    enabled: bool = Field(default=True, description="Se a preferência está ativa.")

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, value: str | None, info) -> str | None:
        if value is None or not value.strip():
            raise ValueError("endpoint é obrigatório para canal 'email' e 'webhook'")
        return value.strip()


class NotificationPreferenceResponse(BaseModel):
    """Preferência persistida do usuário atual."""

    id: str
    channel: str
    endpoint: str | None
    enabled: bool
    created_at: str | None = None
    updated_at: str | None = None
