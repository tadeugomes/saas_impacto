"""
Modelo SQLAlchemy para Tenant (Organização).
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
import uuid


class Tenant(Base):
    """
    Representa uma organização/tenant no sistema SaaS.

    Atributos:
        id: UUID único
        nome: Nome da organização
        slug: Slug único para URLs (ex: 'organizacao-exemplo')
        cnpj: CNPJ da empresa (opcional)
        ativo: Status da organização
        plano: Plano do SaaS (basic, pro, enterprise)
        bq_project_filter: Filtro de projeto BigQuery (opcional)
        instalacoes_permitidas: JSON array com instalações permitidas
        created_at: Data de criação
        updated_at: Última atualização
    """

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    cnpj = Column(String(20), unique=True, nullable=True)
    ativo = Column(Boolean, default=True, index=True)
    plano = Column(String(50), default="basic")

    # Configurações de isolamento
    bq_project_filter = Column(String(100), nullable=True)
    instalacoes_permitidas = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, nome={self.nome}, slug={self.slug})>"
