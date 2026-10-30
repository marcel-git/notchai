"""Add repeat penalty to generation settings."""

from alembic import op
import sqlalchemy as sa

revision = "0006_repeat_penalty"
down_revision = "0005_conversation_system_prompt"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_settings",
        sa.Column(
            "repeat_penalty",
            sa.Float(),
            nullable=False,
            server_default="1.05",
        ),
    )


def downgrade() -> None:
    op.drop_column("chat_settings", "repeat_penalty")
