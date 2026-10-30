from pydantic import BaseModel, Field, field_validator

from app.db.customization import MAX_GUIDANCE_LENGTH


class GuidanceEntry(BaseModel):
    id: int
    text: str


class GuidanceRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_GUIDANCE_LENGTH)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, text: str) -> str:
        text = text.strip()
        if not text:
            raise ValueError("Guidance must not be blank.")
        return text
