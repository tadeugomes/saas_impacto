"""Schemas para preferências de notificação."""

from __future__ import annotations

from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field, TypeAdapter, field_validator
from typing import Literal, Optional


class NotificationPreferenceCreate(BaseModel):
    """Payload de criação ou atualização individual."""

    channel: Literal["email", "webhook"] = Field(..., description="email ou webhook")
    endpoint: str = Field(description="Email ou URL do webhook de destino")
    enabled: bool = Field(default=True, description="Se a preferência está ativa.")

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, value: str, info) -> str:
        if not value or not value.strip():
            raise ValueError("endpoint é obrigatório")

        channel = info.data.get("channel")
        normalized = value.strip()
        if channel == "email":
            # Validação robusta de email com parser de schema do Pydantic
            TypeAdapter(EmailStr).validate_python(normalized)
        elif channel == "webhook":
            # URL de callback válida para webhook (http/https)
            TypeAdapter(AnyHttpUrl).validate_python(normalized)
        else:  # pragma: no cover - guard clause para schema inconsistente
            raise ValueError("channel inválido")

        return normalized


class NotificationPreferenceResponse(BaseModel):
    """Preferência persistida do usuário atual."""

    id: str
    channel: str
    endpoint: Optional[str]
    enabled: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
