"""economic_impact_analyses + RLS

Cria a tabela ``economic_impact_analyses`` com:
  - Colunas de estado, método, parâmetros e resultados (JSONB)
  - Índices simples e compostos para os padrões de acesso esperados
  - Check constraints para status e method
  - PostgreSQL Row Level Security (RLS) com policy de isolamento por tenant

A policy ``tenant_isolation`` garante que cada tenant enxerga apenas
suas próprias análises via ``current_setting('app.current_tenant_id', true)``.

Revision ID: c8f3a1d92b47
Revises: 9039ac2604a6
Create Date: 2026-02-19 15:00:00.000000-03:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision: str = "c8f3a1d92b47"
down_revision: Union[str, None] = "9039ac2604a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Constantes de domínio (espelham o model)
# ---------------------------------------------------------------------------
TABLE_NAME = "economic_impact_analyses"

VALID_STATUSES = ("queued", "running", "success", "failed")
VALID_METHODS = ("did", "iv", "panel_iv", "event_study", "compare")

# ---------------------------------------------------------------------------
# SQL DDL para RLS
# ---------------------------------------------------------------------------
_RLS_ENABLE = f"ALTER TABLE {TABLE_NAME} ENABLE ROW LEVEL SECURITY"

# FORCE garante que RLS se aplica também ao dono da tabela (role que roda
# as migrations). Sem FORCE, o superuser e o owner bypassam as policies.
_RLS_FORCE = f"ALTER TABLE {TABLE_NAME} FORCE ROW LEVEL SECURITY"

# Policy única que cobre todas as operações (SELECT, INSERT, UPDATE, DELETE).
# current_setting(..., true) retorna NULL (não lança exceção) quando a variável
# não está definida — o cast para UUID resultará em NULL, sem match com nenhum
# tenant_id real, impedindo acesso.
_POLICY_CREATE = f"""
CREATE POLICY tenant_isolation
    ON {TABLE_NAME}
    USING (
        tenant_id = current_setting('app.current_tenant_id', true)::UUID
    )
    WITH CHECK (
        tenant_id = current_setting('app.current_tenant_id', true)::UUID
    )
"""

_POLICY_DROP = f"DROP POLICY IF EXISTS tenant_isolation ON {TABLE_NAME}"
_RLS_DISABLE = f"ALTER TABLE {TABLE_NAME} DISABLE ROW LEVEL SECURITY"
_RLS_NO_FORCE = f"ALTER TABLE {TABLE_NAME} NO FORCE ROW LEVEL SECURITY"


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    # ── 1. Criar tabela ────────────────────────────────────────────────────
    op.create_table(
        TABLE_NAME,
        # Chave primária
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            comment="UUID gerado no cliente.",
        ),
        # Isolamento multi-tenant
        sa.Column(
            "tenant_id",
            sa.UUID(),
            nullable=False,
            comment="UUID do tenant; usado pela policy RLS.",
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=True,
            comment="UUID do usuário que disparou a análise (nullable).",
        ),
        # Estado e método
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="queued",
            comment="queued | running | success | failed",
        ),
        sa.Column(
            "method",
            sa.String(length=20),
            nullable=False,
            comment="did | iv | panel_iv | event_study | compare",
        ),
        # Entrada
        sa.Column(
            "request_params",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
            comment="Parâmetros de entrada da análise.",
        ),
        # Saída
        sa.Column(
            "result_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Métricas principais (coef, p-value, ATT, IC, n_obs…).",
        ),
        sa.Column(
            "result_full",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Payload completo do engine causal (inline < ~1 MB).",
        ),
        sa.Column(
            "artifact_path",
            sa.String(length=500),
            nullable=True,
            comment="URI GCS do resultado completo para payloads grandes.",
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
            comment="Detalhes do erro quando status='failed'.",
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Momento de criação / enfileiramento.",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Última atualização.",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Início da execução pelo worker.",
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Fim da execução (sucesso ou falha).",
        ),
        # Constraints de integridade
        sa.CheckConstraint(
            f"status IN {VALID_STATUSES}",
            name="ck_economic_impact_analyses_status",
        ),
        sa.CheckConstraint(
            f"method IN {VALID_METHODS}",
            name="ck_economic_impact_analyses_method",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
            name="fk_eia_tenant_id",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL",
            name="fk_eia_user_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_economic_impact_analyses"),
    )

    # ── 2. Índices simples ─────────────────────────────────────────────────
    op.create_index(
        op.f("ix_economic_impact_analyses_tenant_id"),
        TABLE_NAME,
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_economic_impact_analyses_user_id"),
        TABLE_NAME,
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_economic_impact_analyses_status"),
        TABLE_NAME,
        ["status"],
        unique=False,
    )

    # ── 3. Índices compostos ───────────────────────────────────────────────
    # Padrão: listar análises de um tenant por estado (GET /analyses?status=running)
    op.create_index(
        "ix_eia_tenant_status",
        TABLE_NAME,
        ["tenant_id", "status"],
        unique=False,
    )
    # Padrão: listar análises de um tenant em ordem cronológica (paginação)
    op.create_index(
        "ix_eia_tenant_created",
        TABLE_NAME,
        ["tenant_id", "created_at"],
        unique=False,
    )

    # ── 4. Row Level Security ──────────────────────────────────────────────
    op.execute(_RLS_ENABLE)
    op.execute(_RLS_FORCE)
    op.execute(_POLICY_CREATE)


# ---------------------------------------------------------------------------
# downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    # ── 1. Remover RLS antes de dropar a tabela ────────────────────────────
    op.execute(_POLICY_DROP)
    op.execute(_RLS_NO_FORCE)
    op.execute(_RLS_DISABLE)

    # ── 2. Remover índices compostos ───────────────────────────────────────
    op.drop_index("ix_eia_tenant_created", table_name=TABLE_NAME)
    op.drop_index("ix_eia_tenant_status", table_name=TABLE_NAME)

    # ── 3. Remover índices simples ─────────────────────────────────────────
    op.drop_index(
        op.f("ix_economic_impact_analyses_status"), table_name=TABLE_NAME
    )
    op.drop_index(
        op.f("ix_economic_impact_analyses_user_id"), table_name=TABLE_NAME
    )
    op.drop_index(
        op.f("ix_economic_impact_analyses_tenant_id"), table_name=TABLE_NAME
    )

    # ── 4. Remover tabela ──────────────────────────────────────────────────
    op.drop_table(TABLE_NAME)
