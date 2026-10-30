from typing import TypedDict

from sqlmodel import Session

from app.models.conversation import ChatSettings
from app.services.model_service import (
    DEFAULT_NUM_PREDICT,
    DEFAULT_REASONING,
    DEFAULT_REPEAT_PENALTY,
    DEFAULT_SUMMARIZE_TRIGGER_MESSAGES,
    DEFAULT_SUMMARIZE_TRIGGER_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    MODEL_NAME,
)


class GenerationSettingsData(TypedDict):
    model_name: str
    num_predict: int
    temperature: float
    top_p: float
    repeat_penalty: float
    reasoning: bool
    summarize_trigger_tokens: int
    summarize_trigger_messages: int


def get_generation_settings(session: Session) -> GenerationSettingsData:
    settings = session.get(ChatSettings, "default")
    if settings is None:
        settings = ChatSettings(
            id="default",
            model_name=MODEL_NAME,
            num_predict=DEFAULT_NUM_PREDICT,
            temperature=DEFAULT_TEMPERATURE,
            top_p=DEFAULT_TOP_P,
            repeat_penalty=DEFAULT_REPEAT_PENALTY,
            reasoning=DEFAULT_REASONING,
            summarize_trigger_tokens=DEFAULT_SUMMARIZE_TRIGGER_TOKENS,
            summarize_trigger_messages=DEFAULT_SUMMARIZE_TRIGGER_MESSAGES,
        )
        session.add(settings)
        session.flush()
    return _settings_data(settings)


def update_generation_settings(
    session: Session,
    values: GenerationSettingsData,
) -> GenerationSettingsData:
    settings = session.get(ChatSettings, "default")
    if settings is None:
        settings = ChatSettings(id="default", **values)
        session.add(settings)
    else:
        settings.model_name = values["model_name"]
        settings.num_predict = values["num_predict"]
        settings.temperature = values["temperature"]
        settings.top_p = values["top_p"]
        settings.repeat_penalty = values["repeat_penalty"]
        settings.reasoning = values["reasoning"]
        settings.summarize_trigger_tokens = values["summarize_trigger_tokens"]
        settings.summarize_trigger_messages = values["summarize_trigger_messages"]
    session.flush()
    return _settings_data(settings)


def _settings_data(settings: ChatSettings) -> GenerationSettingsData:
    return {
        "model_name": settings.model_name,
        "num_predict": settings.num_predict,
        "temperature": settings.temperature,
        "top_p": settings.top_p,
        "repeat_penalty": settings.repeat_penalty,
        "reasoning": settings.reasoning,
        "summarize_trigger_tokens": settings.summarize_trigger_tokens,
        "summarize_trigger_messages": settings.summarize_trigger_messages,
    }
