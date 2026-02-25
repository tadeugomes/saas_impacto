"""Harden notification preferences constraints."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "223344556677"
down_revision: str = "112233445566"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Garante somente uma preferência por (tenant, usuário, canal).
    op.execute(
        """
        DELETE FROM notification_preferences n1
        USING notification_preferences n2
        WHERE
            n1.tenant_id = n2.tenant_id
            AND n1.user_id = n2.user_id
            AND n1.channel = n2.channel
            AND (
                n1.updated_at < n2.updated_at
                OR (n1.updated_at = n2.updated_at AND n1.id < n2.id)
            )
        """
    )

    op.alter_column(
        "notification_preferences",
        "endpoint",
        existing_type=sa.VARCHAR(length=255),
        nullable=False,
    )
    op.drop_index("ix_notification_preferences_user_channel", table_name="notification_preferences")
    op.create_index(
        "ix_notification_preferences_user_channel",
        "notification_preferences",
        ["tenant_id", "user_id", "channel"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_notification_preferences_user_channel", table_name="notification_preferences")
    op.create_index(
        "ix_notification_preferences_user_channel",
        "notification_preferences",
        ["user_id", "channel"],
        unique=False,
    )
    op.alter_column(
        "notification_preferences",
        "endpoint",
        existing_type=sa.VARCHAR(length=255),
        nullable=True,
    )
