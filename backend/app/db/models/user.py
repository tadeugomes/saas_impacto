"""
Modelo SQLAlchemy para User.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.db.models.tenant import Tenant
import uuid


class User(Base):
    """
    Representa um usuário do sistema.

    Atributos:
        id: UUID único
        tenant_id: UUID do tenant (organização)
        email: Email do usuário (único por tenant)
        nome: Nome completo
        hashed_password: Senha criptografada (bcrypt)
        ativo: Status do usuário
        roles: Array de roles (admin, analyst, viewer)
        created_at: Data de criação
        updated_at: Última atualização
        last_login: Último login
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    email = Column(String(255), nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)

    ativo = Column(Boolean, default=True, index=True)
    roles = Column(ARRAY(String), default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relacionamentos
    tenant = relationship("Tenant", back_populates="users")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, tenant_id={self.tenant_id})>"

    def has_role(self, role: str) -> bool:
        """Verifica se o usuário possui uma role específica."""
        return role in (self.roles or [])

    def is_admin(self) -> bool:
        """Verifica se o usuário é admin."""
        return self.has_role("admin")


# Adicionar relacionamento inverso no Tenant
Tenant.users = relationship("User", back_populates="tenant")
