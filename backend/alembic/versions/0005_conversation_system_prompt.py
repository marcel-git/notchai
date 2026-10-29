"""Persist each conversation's system prompt."""

from alembic import op
import sqlalchemy as sa

revision = "0005_conversation_system_prompt"
down_revision = "0004_remove_message_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("system_prompt", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversations", "system_prompt")
