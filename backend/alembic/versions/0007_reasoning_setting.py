"""Add model reasoning toggle to generation settings."""

from alembic import op
import sqlalchemy as sa

revision = "0007_reasoning_setting"
down_revision = "0006_repeat_penalty"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_settings",
        sa.Column(
            "reasoning",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("chat_settings", "reasoning")
