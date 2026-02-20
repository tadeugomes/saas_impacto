"""Create notification preferences table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "112233445566"
down_revision: str = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("endpoint", sa.String(length=255), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.PrimaryKeyConstraint("id", name="pk_notification_preferences"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "channel IN ('email', 'webhook')",
            name="ck_notification_preferences_channel",
        ),
    )
    op.create_index(
        "ix_notification_preferences_user_channel",
        "notification_preferences",
        ["user_id", "channel"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_notification_preferences_user_channel", table_name="notification_preferences")
    op.drop_table("notification_preferences")
