"""
Permissões granuladas por tenant, role, módulo e ação.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class TenantModulePermission(Base):
    """Define autorização por tenant/role para módulo+ação.

    Exemplo:
    - tenant_id=...;
    - role="analyst";
    - module_number=5;
    - action="execute";
    """

    __tablename__ = "tenant_module_permissions"

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
    role = Column(String(50), nullable=False)
    module_number = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "role",
            "module_number",
            "action",
            name="uq_tenant_module_permission",
        ),
    )
