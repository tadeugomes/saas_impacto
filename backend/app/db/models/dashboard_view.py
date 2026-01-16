"""
Modelo SQLAlchemy para DashboardView (visões salvas).
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.db.models.user import User
import uuid


class DashboardView(Base):
    """
    Representa uma visão de dashboard salva por um usuário.

    Permite que os usuários salvem configurações de filtros,
    layout e outras preferências de visualização.

    Atributos:
        id: UUID único
        tenant_id: UUID do tenant
        user_id: UUID do usuário que criou
        nome: Nome da visão (ex: 'Portos SP - 2024')
        configuracao: JSONB com filtros, layout, etc.
        is_default: Se é a visão padrão do usuário
        created_at: Data de criação
        updated_at: Última atualização
    """

    __tablename__ = "dashboard_views"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    nome = Column(String(255), nullable=False)
    configuracao = Column(JSONB, nullable=False)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relacionamentos
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<DashboardView(id={self.id}, nome={self.nome}, user_id={self.user_id})>"
