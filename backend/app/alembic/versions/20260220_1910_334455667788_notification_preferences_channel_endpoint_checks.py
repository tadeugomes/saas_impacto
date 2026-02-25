"""Add stricter constraints to notification endpoint semantics."""

from __future__ import annotations

from alembic import op

revision: str = "334455667788"
down_revision: str = "223344556677"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_notification_preferences_endpoint_by_channel",
        "notification_preferences",
        "(channel = 'email' AND endpoint ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$') "
        "OR (channel = 'webhook' AND endpoint ~* '^https?://.+')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_notification_preferences_endpoint_by_channel",
        "notification_preferences",
        type_="check",
    )
