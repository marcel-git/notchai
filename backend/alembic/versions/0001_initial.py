"""Create the conversation and message tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing_tables = set(inspect(bind).get_table_names())
    application_tables = {"conversations", "messages"}

    if existing_tables.intersection(application_tables):
        if not application_tables.issubset(existing_tables):
            raise RuntimeError(
                "The existing database has an incomplete chat schema."
            )
        expected_columns = {
            "conversations": {"id", "title", "created_at", "updated_at"},
            "messages": {
                "id",
                "conversation_id",
                "role",
                "content",
                "status",
                "created_at",
            },
        }
        for table, expected in expected_columns.items():
            actual = {column["name"] for column in inspect(bind).get_columns(table)}
            if actual != expected:
                raise RuntimeError(
                    f"The existing {table} table does not match the initial schema."
                )
    else:
        op.create_table(
            "conversations",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("created_at", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_table(
            "messages",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("conversation_id", sa.Text(), nullable=False),
            sa.Column("role", sa.Text(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("status", sa.Text(), nullable=False),
            sa.Column("created_at", sa.Text(), nullable=False),
            sa.CheckConstraint(
                "role IN ('user', 'assistant')"
            ),
            sa.CheckConstraint(
                "status IN ('pending', 'streaming', 'completed', "
                "'interrupted', 'failed')",
            ),
            sa.ForeignKeyConstraint(
                ["conversation_id"],
                ["conversations.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "messages_conversation_id_id",
            "messages",
            ["conversation_id", "id"],
            unique=False,
        )

    op.execute("PRAGMA user_version = 0")


def downgrade() -> None:
    op.drop_index("messages_conversation_id_id", table_name="messages")
    op.drop_table("messages")
    op.drop_table("conversations")
