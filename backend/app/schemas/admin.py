"""
Schemas de administração para Tenant e usuários.

Inclui payloads para CRUD básico de tenant e gerenciamento de usuários.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


ALLOWED_PLANS = {"basic", "pro", "enterprise"}


class TenantBase(BaseModel):
    """Dados base de tenant."""

    nome: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100)
    plano: str = Field(default="basic", description="Plano de assinatura do tenant")

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("slug é obrigatório")
        if " " in normalized:
            raise ValueError("slug não pode conter espaços")
        return normalized

    @field_validator("plano")
    @classmethod
    def _validate_plano(cls, value: str) -> str:
        normalized = (value or "").strip().lower()
        if normalized not in ALLOWED_PLANS:
            raise ValueError(f"plano inválido: {normalized}")
        return normalized


class TenantCreate(TenantBase):
    """Payload de criação de tenant."""

    cnpj: Optional[str] = Field(default=None, max_length=20)
    allowed_installations: List[str] = Field(default_factory=list)
    instalacoes_permitidas: Optional[str] = None

    @field_validator("cnpj")
    @classmethod
    def _normalize_cnpj(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return "".join(ch for ch in value if ch.isdigit()) or None


class TenantUpdate(BaseModel):
    """Payload de atualização parcial de tenant."""

    nome: Optional[str] = Field(default=None, min_length=2, max_length=255)
    plano: Optional[str] = Field(default=None)
    ativo: Optional[bool] = None
    instalacoes_permitidas: Optional[List[str]] = None
    cnpj: Optional[str] = Field(default=None, max_length=20)

    @field_validator("plano")
    @classmethod
    def _validate_plano(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in ALLOWED_PLANS:
            raise ValueError(f"plano inválido: {normalized}")
        return normalized

    @field_validator("cnpj")
    @classmethod
    def _normalize_cnpj(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return "".join(ch for ch in value if ch.isdigit()) or None


class TenantDetail(TenantBase):
    """Representação de tenant em resposta."""

    id: str
    ativo: bool
    cnpj: Optional[str] = None
    instalacoes_permitidas: Optional[str] = None
    updated_at: Optional[str] = None
    created_at: Optional[str] = None


class TenantListItem(TenantDetail):
    """Item de lista de tenants."""

    pass


class TenantListResponse(BaseModel):
    """Página de tenants."""

    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[TenantListItem]


class TenantActivationUpdate(BaseModel):
    """Payload explícito para ativação/inativação de tenant."""

    ativo: bool


class UserAdminItem(BaseModel):
    """Item de usuário para administração."""

    id: str
    email: str
    nome: str
    roles: List[str]
    ativo: bool
    created_at: str
    updated_at: Optional[str] = None
    last_login: Optional[str] = None


class UserAdminListResponse(BaseModel):
    """Lista paginada de usuários do tenant."""

    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[UserAdminItem]


class UserAdminUpdate(BaseModel):
    """Atualização de status/roles para usuário."""

    roles: Optional[List[str]] = None
    ativo: Optional[bool] = None

    @field_validator("roles")
    @classmethod
    def _normalize_roles(cls, roles: Optional[List[str]]) -> Optional[List[str]]:
        if roles is None:
            return None
        normalized = [str(role).strip().lower() for role in roles if str(role).strip()]
        if not normalized:
            return []
        return normalized


class UserStatusUpdate(BaseModel):
    """Payload de atualização de status/roles com semântica explícita."""

    ativo: Optional[bool] = None
    roles: Optional[List[str]] = None


class OnboardingCompanyRequest(BaseModel):
    """Dados para criação de tenant + admin via autoatendimento."""

    empresa: str = Field(..., min_length=2, max_length=255)
    cnpj: Optional[str] = Field(default=None, max_length=20)
    plano: str = Field(default="basic")
    nome_admin: str = Field(..., min_length=2, max_length=255)
    email_admin: str = Field(..., min_length=5, max_length=255)
    senha_admin: str = Field(..., min_length=8, max_length=128)

    @field_validator("plano")
    @classmethod
    def _normalize_plan(cls, value: str) -> str:
        normalized = (value or "").strip().lower()
        if normalized not in ALLOWED_PLANS:
            raise ValueError(f"plano inválido: {normalized}")
        return normalized

    @field_validator("cnpj")
    @classmethod
    def _normalize_cnpj(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return "".join(ch for ch in value if ch.isdigit()) or None


class OnboardingCompanyResponse(BaseModel):
    """Resposta de sucesso do fluxo de cadastro inicial."""

    tenant_id: str
    user_id: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TenantUsageIndicatorsItem(BaseModel):
    """Indicador mais consultado no período."""

    codigo: str
    nome: str
    acessos: int


class TenantUsageResponse(BaseModel):
    """Payload resumido de uso do tenant."""

    total_analises: int
    analises_sucesso: int
    analises_falha: int
    usuarios_ativos_7d: int
    usuarios_ativos_30d: int
    bq_bytes_last_30d: int
    taxa_rate_limit: Optional[float] = None
    top_indicadores: List[TenantUsageIndicatorsItem]
