"""Modelo de configuração de capacidade por terminal portuário (Módulo 12)."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class TerminalCapacityConfig(Base):
    """Parâmetros calibráveis para cálculo de capacidade de cais por terminal.

    Cada registro mapeia uma instalação ANTAQ (``id_instalacao``) aos
    parâmetros necessários pela Eq. 1b e Quadro 17 da metodologia
    LabPortos/UFMA.
    """

    __tablename__ = "terminal_capacity_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identificação
    id_instalacao = Column(
        String(30),
        nullable=False,
        index=True,
        comment="Código da instalação portuária ANTAQ (ex: BRSSZ)",
    )
    nome_terminal = Column(String(255), nullable=False)

    # Parâmetros de capacidade
    n_bercos = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Número de berços operacionais",
    )
    h_ef = Column(
        Float,
        nullable=False,
        default=8000.0,
        comment="Horas efetivas de operação por ano (Eq. 1c)",
    )
    clearance_h = Column(
        Float,
        nullable=False,
        default=3.0,
        comment="Intervalo entre atracações (parâmetro 'a', horas)",
    )
    bor_adm_override = Column(
        Float,
        nullable=True,
        comment="BOR admissível customizado; null = usa Quadro 17 automático",
    )
    fator_teu = Column(
        Float,
        nullable=False,
        default=1.55,
        comment="Fator de conversão TEU/contêiner (Quadro 8)",
    )

    # Horas de indisponibilidade (opcionais, para cálculo de H_ef)
    h_cli = Column(
        Float,
        nullable=True,
        comment="Horas de indisponibilidade climática por ano",
    )
    h_mnt = Column(
        Float,
        nullable=True,
        comment="Horas de manutenção por ano",
    )

    notas = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<TerminalCapacityConfig("
            f"id_instalacao={self.id_instalacao!r}, "
            f"nome_terminal={self.nome_terminal!r}, "
            f"n_bercos={self.n_bercos})>"
        )
