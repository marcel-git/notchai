"""Add character and persona profiles to conversations."""

from alembic import op
import sqlalchemy as sa

revision = "0002_characters_personas"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "characters",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("personality", sa.Text(), nullable=False),
        sa.Column("background", sa.Text(), nullable=False),
        sa.Column("custom_instructions", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "personas",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("identity", sa.Text(), nullable=False),
        sa.Column("appearance", sa.Text(), nullable=False),
        sa.Column("background", sa.Text(), nullable=False),
        sa.Column("behavior", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.add_column(sa.Column("character_id", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("persona_id", sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            "fk_conversations_character_id_characters",
            "characters",
            ["character_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_foreign_key(
            "fk_conversations_persona_id_personas",
            "personas",
            ["persona_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.drop_constraint(
            "fk_conversations_persona_id_personas",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_conversations_character_id_characters",
            type_="foreignkey",
        )
        batch_op.drop_column("persona_id")
        batch_op.drop_column("character_id")
    op.drop_table("personas")
    op.drop_table("characters")
