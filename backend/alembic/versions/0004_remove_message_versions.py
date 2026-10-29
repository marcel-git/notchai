"""Remove message revision history."""

from alembic import op
import sqlalchemy as sa

revision = "0004_remove_message_versions"
down_revision = "0003_roleplay_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("message_versions")


def downgrade() -> None:
    op.create_table(
        "message_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
