"""
Schemas Pydantic para Autenticação.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


class UserLogin(BaseModel):
    """Schema para login de usuário."""

    email: EmailStr
    password: str = Field(..., min_length=6)


class UserRegister(BaseModel):
    """Schema para registro de novo usuário."""

    email: EmailStr
    password: str = Field(..., min_length=6)
    nome: str = Field(..., min_length=2, max_length=255)
    tenant_slug: str = Field(..., min_length=2, max_length=100)


class Token(BaseModel):
    """Schema para resposta de token."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Payload do token JWT."""

    sub: uuid.UUID  # user_id
    tenant_id: uuid.UUID
    exp: Optional[datetime] = None


class UserResponse(BaseModel):
    """Schema para resposta de usuário."""

    id: uuid.UUID
    email: EmailStr
    nome: str
    tenant_id: uuid.UUID
    roles: list[str]
    ativo: bool
    created_at: datetime

    class Config:
        from_attributes = True
