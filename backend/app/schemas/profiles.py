from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CharacterFields(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=20_000)
    personality: str = Field(default="", max_length=20_000)
    background: str = Field(default="", max_length=20_000)
    custom_instructions: str = Field(default="", max_length=20_000)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, name: str) -> str:
        name = name.strip()
        if not name:
            raise ValueError("Name must not be blank.")
        return name


class CharacterCreate(CharacterFields):
    pass


class CharacterRead(CharacterFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class PersonaFields(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    identity: str = Field(default="", max_length=20_000)
    appearance: str = Field(default="", max_length=20_000)
    background: str = Field(default="", max_length=20_000)
    behavior: str = Field(default="", max_length=20_000)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, name: str) -> str:
        name = name.strip()
        if not name:
            raise ValueError("Name must not be blank.")
        return name


class PersonaCreate(PersonaFields):
    pass


class PersonaRead(PersonaFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
