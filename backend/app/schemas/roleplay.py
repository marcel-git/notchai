from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ConversationTitleRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, title: str) -> str:
        title = title.strip()
        if not title:
            raise ValueError("Title must not be blank.")
        return title


class GenerationSettingsUpdate(BaseModel):
    model_name: str = Field(min_length=1, max_length=200)
    num_predict: int = Field(ge=1, le=32768)
    temperature: float = Field(ge=0, le=2)
    top_p: float = Field(gt=0, le=1)

    @field_validator("model_name")
    @classmethod
    def model_name_must_not_be_blank(cls, model_name: str) -> str:
        model_name = model_name.strip()
        if not model_name:
            raise ValueError("Model name must not be blank.")
        return model_name


class GenerationSettingsRead(GenerationSettingsUpdate):
    pass


class PromptPreviewRequest(BaseModel):
    character_id: UUID
    persona_id: UUID | None = None


class PromptInspection(BaseModel):
    conversation_id: UUID | None
    model_name: str
    num_predict: int
    temperature: float
    top_p: float
    system_prompt: str


class ContextSection(BaseModel):
    label: str
    role: Literal["system", "user", "assistant"]
    estimated_tokens: int


class ContextMeterData(BaseModel):
    conversation_id: UUID
    model_name: str
    runtime_context_length: int | None
    context_note: str | None
    estimated_tokens_total: int
    sections: list[ContextSection]
