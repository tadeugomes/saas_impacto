"""
Schemas de auditoria para logs de segurança e conformidade.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AuditLogItem(BaseModel):
    """Item individual de log retornado para listagens."""

    id: str = Field(..., description="ID do log")
    tenant_id: str = Field(..., description="Tenant dono do evento")
    user_id: Optional[str] = Field(None, description="Usuário que disparou a ação")
    action: str = Field(..., description="Tipo de ação auditada")
    resource: str = Field(..., description="Recurso/endpoint alvo")
    status_code: Optional[int] = Field(None, description="Status HTTP retornado")
    duration_ms: Optional[int] = Field(
        None,
        description="Duração da operação em milissegundos",
    )
    bytes_processed: Optional[int] = Field(
        None,
        description="Bytes processados (quando aplicável)",
    )
    ip: Optional[str] = Field(None, description="IP do cliente")
    details: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = Field(None, description="ID de trace da request")
    created_at: datetime = Field(..., description="Timestamp do evento")


class AuditLogListResponse(BaseModel):
    """Página de auditoria por tenant."""

    total: int = Field(..., description="Total de registros encontrados")
    page: int = Field(..., description="Página atual (1-indexed)")
    page_size: int = Field(..., description="Tamanho da página")
    total_pages: int = Field(..., description="Total de páginas")
    items: List[AuditLogItem] = Field(default_factory=list)
