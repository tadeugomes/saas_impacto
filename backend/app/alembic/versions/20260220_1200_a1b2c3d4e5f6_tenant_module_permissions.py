"""Create tenant_module_permissions for granular RBAC.

Revisão:
  - tabela `tenant_module_permissions` com chave primaria UUID
  - FK para tenants com CASCADE
  - campos: role, module_number, action
  - constraint única por (tenant_id, role, module_number, action)
  - constraints para módulo em 1..7 e action em {read, execute, write}
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a1b2c3d4e5f6"
down_revision: str = "d7e8f9a0b1c2"
branch_labels = None
depends_on = None


TABLE_NAME = "tenant_module_permissions"
VALID_ACTIONS = ("read", "execute", "write")


def upgrade() -> None:
    op.create_table(
        TABLE_NAME,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("module_number", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
            name="fk_tmp_tenant_id",
        ),
        sa.CheckConstraint(
            f"action IN {VALID_ACTIONS}",
            name="ck_tenant_module_permissions_action",
        ),
        sa.CheckConstraint(
            "module_number BETWEEN 1 AND 7",
            name="ck_tenant_module_permissions_module_number",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tenant_module_permissions"),
        sa.UniqueConstraint(
            "tenant_id",
            "role",
            "module_number",
            "action",
            name="uq_tenant_module_permission",
        ),
    )
    op.create_index(
        op.f("ix_tenant_module_permissions_tenant_id"),
        TABLE_NAME,
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tenant_module_permissions_role"),
        TABLE_NAME,
        ["role"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tenant_module_permissions_role"), table_name=TABLE_NAME)
    op.drop_index(op.f("ix_tenant_module_permissions_tenant_id"), table_name=TABLE_NAME)
    op.drop_table(TABLE_NAME)
