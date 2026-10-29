from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    conversation_id: UUID

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, message: str) -> str:
        message = message.strip()
        if not message:
            raise ValueError("Message must not be blank.")
        return message


class CreateConversationRequest(BaseModel):
    id: UUID
    character_id: UUID
    persona_id: UUID | None = None
    system_prompt: str | None = Field(default=None, max_length=170_000)
