"""
Registro imutável de eventos de auditoria por tenant.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.db.base import Base


class AuditLog(Base):
    """Auditoria de operações sensíveis da aplicação."""

    __tablename__ = "audit_logs"

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
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String(80), nullable=False)
    resource = Column(String(120), nullable=False)
    status_code = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    bytes_processed = Column(Integer, nullable=True)
    ip = Column(String(45), nullable=True)
    details = Column(JSONB, default=dict, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    request_id = Column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_audit_logs_tenant_resource", "tenant_id", "resource"),
        Index("ix_audit_logs_action_created_at", "tenant_id", "action", "created_at"),
    )
