"""Create audit log table for compliance and observability."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b2c3d4e5f6a7"
down_revision: str = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("resource", sa.String(length=120), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("bytes_processed", sa.Integer(), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "request_id",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            index=True,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_audit_logs_tenant_resource",
        "audit_logs",
        ["tenant_id", "resource"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_action_created_at",
        "audit_logs",
        ["tenant_id", "action", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_action_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_resource", table_name="audit_logs")
    op.drop_table("audit_logs")
