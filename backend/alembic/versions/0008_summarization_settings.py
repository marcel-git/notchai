"""Add configurable conversation summarization."""

from alembic import op
import sqlalchemy as sa

revision = "0008_summarization_settings"
down_revision = "0007_reasoning_setting"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_settings",
        sa.Column(
            "summarize_trigger_tokens",
            sa.Integer(),
            nullable=False,
            server_default="16384",
        ),
    )
    op.add_column(
        "chat_settings",
        sa.Column(
            "summarize_trigger_messages",
            sa.Integer(),
            nullable=False,
            server_default="40",
        ),
    )
    op.add_column(
        "conversations",
        sa.Column("context_summary", sa.Text(), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column("summarized_through_message_id", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversations", "summarized_through_message_id")
    op.drop_column("conversations", "context_summary")
    op.drop_column("chat_settings", "summarize_trigger_messages")
    op.drop_column("chat_settings", "summarize_trigger_tokens")
