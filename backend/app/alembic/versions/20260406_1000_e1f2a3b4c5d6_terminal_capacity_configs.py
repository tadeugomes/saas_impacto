"""Create terminal_capacity_configs table for Module 12.

Revision ID: e1f2a3b4c5d6
Revises: 334455667788
Create Date: 2026-04-06
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e1f2a3b4c5d6"
down_revision: str = "334455667788"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "terminal_capacity_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("id_instalacao", sa.String(30), nullable=False, index=True),
        sa.Column("nome_terminal", sa.String(255), nullable=False),
        sa.Column("n_bercos", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "h_ef", sa.Float(), nullable=False, server_default="8000"
        ),
        sa.Column(
            "clearance_h", sa.Float(), nullable=False, server_default="3.0"
        ),
        sa.Column("bor_adm_override", sa.Float(), nullable=True),
        sa.Column(
            "fator_teu", sa.Float(), nullable=False, server_default="1.55"
        ),
        sa.Column("h_cli", sa.Float(), nullable=True),
        sa.Column("h_mnt", sa.Float(), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_terminal_capacity_configs"),
    )
    op.create_index(
        "ix_terminal_capacity_configs_tenant_instalacao",
        "terminal_capacity_configs",
        ["tenant_id", "id_instalacao"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_terminal_capacity_configs_tenant_instalacao",
        table_name="terminal_capacity_configs",
    )
    op.drop_table("terminal_capacity_configs")
