"""
Modelo SQLAlchemy para EconomicImpactAnalysis (runs de impacto econômico).

Cada registro representa uma execução de análise causal (DiD, IV, Panel IV
ou comparação multi-método) disparada por um tenant/usuário.

Isolamento por tenant via PostgreSQL Row Level Security (RLS).
A policy ``tenant_isolation`` garante que cada tenant enxerga apenas
suas próprias análises, sem necessidade de filtros explícitos no código.

Estados possíveis (coluna ``status``):
  queued   → análise enfileirada, aguardando worker
  running  → worker iniciou a execução
  success  → concluída com sucesso; resultados em result_summary/result_full
  failed   → falha; detalhe em error_message

Persistência dos resultados:
  result_summary  — JSONB com métricas principais (coef, p-value, ATT, …)
                    sempre preenchido em caso de success
  result_full     — JSONB com resultado completo do engine causal
                    preenchido para análises pequenas (< ~1 MB)
  artifact_path   — URI GCS (gs://bucket/path.json) para resultados grandes;
                    preenchido em alternativa (ou complemento) a result_full
"""
from __future__ import annotations

import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

# ── Valores válidos ───────────────────────────────────────────────────────────
VALID_STATUSES = ("queued", "running", "success", "failed")
VALID_METHODS = (
    "did", "iv", "panel_iv", "event_study", "compare",
    "scm", "augmented_scm",
)


class EconomicImpactAnalysis(Base):
    """
    Representa uma execução de análise causal de impacto econômico.

    Atributos
    ----------
    id:
        UUID primário gerado no cliente (evita round-trip ao BD).
    tenant_id:
        UUID do tenant dono da análise. Coluna-chave para RLS.
    user_id:
        UUID do usuário que disparou a análise (nullable; pode ser
        gerada por job automático sem usuário associado).
    status:
        Estado atual da análise: queued | running | success | failed.
    method:
        Método causal utilizado: did | iv | panel_iv | event_study | compare.
    request_params:
        JSONB com os parâmetros de entrada (municípios, período, outcome, …).
    result_summary:
        JSONB com métricas principais (coef ATT, IC, p-value, n_obs, …).
        Preenchido ao concluir com sucesso; indexado para consultas rápidas.
    result_full:
        JSONB com payload completo do engine causal (event study, placebo,
        sensitivity, specifications, warnings). Preenchido quando o tamanho
        permite armazenamento inline.
    artifact_path:
        URI GCS do resultado completo serializado (gs://…). Alternativa ou
        complemento ao result_full para payloads grandes.
    error_message:
        Mensagem de erro quando status='failed'.
    created_at:
        Timestamp de criação do registro (enfileiramento).
    updated_at:
        Última atualização (gerenciado pelo banco via trigger/ORM).
    started_at:
        Momento em que o worker iniciou a execução.
    completed_at:
        Momento de conclusão (sucesso ou falha).
    """

    __tablename__ = "economic_impact_analyses"

    # ── Chave primária ────────────────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="UUID gerado no cliente.",
    )

    # ── Isolamento multi-tenant ───────────────────────────────────────────────
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="UUID do tenant; usado pela policy RLS.",
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="UUID do usuário que disparou a análise (nullable).",
    )

    # ── Estado e método ───────────────────────────────────────────────────────
    status = Column(
        String(20),
        nullable=False,
        default="queued",
        index=True,
        comment="queued | running | success | failed",
    )
    method = Column(
        String(20),
        nullable=False,
        comment="did | iv | panel_iv | event_study | compare",
    )

    # ── Entrada ───────────────────────────────────────────────────────────────
    request_params = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Parâmetros de entrada da análise (municípios, período, outcome…).",
    )

    # ── Saída ─────────────────────────────────────────────────────────────────
    result_summary = Column(
        JSONB,
        nullable=True,
        comment="Métricas principais (coef, p-value, ATT, IC, n_obs…).",
    )
    result_full = Column(
        JSONB,
        nullable=True,
        comment="Payload completo do engine causal (inline para resultados < ~1 MB).",
    )
    artifact_path = Column(
        String(500),
        nullable=True,
        comment="URI GCS do resultado completo para payloads grandes (gs://…).",
    )
    error_message = Column(
        Text,
        nullable=True,
        comment="Detalhes do erro quando status='failed'.",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Momento de criação / enfileiramento.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Última atualização (ORM).",
    )
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Início da execução pelo worker.",
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Fim da execução (sucesso ou falha).",
    )

    # ── Constraints e índices compostos ──────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            f"status IN {VALID_STATUSES}",
            name="ck_economic_impact_analyses_status",
        ),
        CheckConstraint(
            f"method IN {VALID_METHODS}",
            name="ck_economic_impact_analyses_method",
        ),
        # Índice composto: listagem de análises por tenant + status (padrão de uso)
        Index(
            "ix_eia_tenant_status",
            "tenant_id",
            "status",
        ),
        # Índice composto: listagem por tenant + data (paginação decrescente)
        Index(
            "ix_eia_tenant_created",
            "tenant_id",
            "created_at",
        ),
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    tenant = relationship("Tenant")
    user = relationship("User")

    # ── Métodos de conveniência ───────────────────────────────────────────────

    @property
    def duration_seconds(self) -> float | None:
        """Duração da execução em segundos (None se ainda em curso)."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_terminal(self) -> bool:
        """True se o status não vai mais mudar (success ou failed)."""
        return self.status in ("success", "failed")

    def mark_running(self) -> None:
        """Transiciona para status='running' e registra started_at."""
        from datetime import datetime, timezone

        self.status = "running"
        self.started_at = datetime.now(tz=timezone.utc)

    def mark_success(
        self,
        result_summary: dict,
        result_full: dict | None = None,
        artifact_path: str | None = None,
    ) -> None:
        """Transiciona para status='success' e persiste resultados."""
        from datetime import datetime, timezone

        self.status = "success"
        self.completed_at = datetime.now(tz=timezone.utc)
        self.result_summary = result_summary
        if result_full is not None:
            self.result_full = result_full
        if artifact_path is not None:
            self.artifact_path = artifact_path

    def mark_failed(self, error_message: str) -> None:
        """Transiciona para status='failed' e registra a mensagem de erro."""
        from datetime import datetime, timezone

        self.status = "failed"
        self.completed_at = datetime.now(tz=timezone.utc)
        self.error_message = error_message

    def __repr__(self) -> str:
        return (
            f"<EconomicImpactAnalysis("
            f"id={self.id}, "
            f"tenant_id={self.tenant_id}, "
            f"method={self.method!r}, "
            f"status={self.status!r}"
            f")>"
        )
