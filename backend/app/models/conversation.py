from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Text
from sqlmodel import Field, Relationship, SQLModel


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

class Character(SQLModel, table=True):
    __tablename__ = "characters"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        nullable=False,
        sa_type=Text,
    )
    name: str = Field(sa_type=Text)
    description: str = Field(sa_type=Text)
    personality: str = Field(sa_type=Text)
    background: str = Field(sa_type=Text)
    custom_instructions: str = Field(sa_type=Text)
    created_at: str = Field(default_factory=utc_timestamp, sa_type=Text)
    updated_at: str = Field(default_factory=utc_timestamp, sa_type=Text)
    conversations: list["Conversation"] = Relationship(
        back_populates="character",
        sa_relationship_kwargs={"passive_deletes": "all"},
    )


class Persona(SQLModel, table=True):
    __tablename__ = "personas"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        nullable=False,
        sa_type=Text,
    )
    name: str = Field(sa_type=Text)
    identity: str = Field(sa_type=Text)
    appearance: str = Field(sa_type=Text)
    background: str = Field(sa_type=Text)
    behavior: str = Field(sa_type=Text)
    created_at: str = Field(default_factory=utc_timestamp, sa_type=Text)
    updated_at: str = Field(default_factory=utc_timestamp, sa_type=Text)
    conversations: list["Conversation"] = Relationship(
        back_populates="persona",
        sa_relationship_kwargs={"passive_deletes": "all"},
    )


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        nullable=False,
        sa_type=Text,
    )
    title: str = Field(sa_type=Text)
    character_id: str | None = Field(
        default=None,
        sa_column=Column(
            Text,
            ForeignKey(
                "characters.id",
                name="fk_conversations_character_id_characters",
                ondelete="RESTRICT",
            ),
            nullable=True,
        ),
    )
    persona_id: str | None = Field(
        default=None,
        sa_column=Column(
            Text,
            ForeignKey(
                "personas.id",
                name="fk_conversations_persona_id_personas",
                ondelete="RESTRICT",
            ),
            nullable=True,
        ),
    )
    system_prompt: str | None = Field(default=None, sa_type=Text)
    created_at: str = Field(default_factory=utc_timestamp, sa_type=Text)
    updated_at: str = Field(default_factory=utc_timestamp, sa_type=Text)
    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    character: Character | None = Relationship(back_populates="conversations")
    persona: Persona | None = Relationship(back_populates="conversations")


class Message(SQLModel, table=True):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')"),
        CheckConstraint(
            "status IN ('pending', 'streaming', 'completed', 'interrupted', 'failed')"
        ),
        Index("messages_conversation_id_id", "conversation_id", "id"),
    )

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    conversation_id: str = Field(
        foreign_key="conversations.id",
        sa_type=Text,
        ondelete="CASCADE",
    )
    role: str = Field(sa_type=Text)
    content: str = Field(sa_type=Text)
    status: str = Field(sa_type=Text)
    is_superseded: bool = Field(default=False    )
    created_at: str = Field(default_factory=utc_timestamp, sa_type=Text)
    conversation: Conversation | None = Relationship(back_populates="messages")


class ChatSettings(SQLModel, table=True):
    __tablename__ = "chat_settings"

    id: str = Field(default="default", primary_key=True, nullable=False, sa_type=Text)
    model_name: str = Field(sa_type=Text)
    num_predict: int
    temperature: float
    top_p: float
    repeat_penalty: float = Field(default=1.05)
    reasoning: bool = Field(default=True)
