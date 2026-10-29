from uuid import UUID

from sqlmodel import Session

from app.models.conversation import Conversation
from app.repositories.conversation_repository import get_model_history
from app.repositories.settings_repository import get_generation_settings
from app.schemas.roleplay import ContextMeterData, ContextSection
from app.services.model_service import get_runtime_context_length
from app.services.prompt_builder import build_prompt


def build_context_meter(
    session: Session,
    conversation: Conversation,
) -> ContextMeterData:
    history = get_model_history(session, UUID(conversation.id))
    context = build_prompt(
        conversation.character,
        conversation.persona,
        history,
        system_prompt=conversation.system_prompt,
    )
    sections = []
    message_counts = {"user": 0, "assistant": 0}
    for item in context:
        role = item["role"]
        if role == "system":
            label = "System prompt"
        else:
            message_counts[role] += 1
            label = f"{role.capitalize()} message {message_counts[role]}"
        sections.append(
            ContextSection(
                label=label,
                role=role,
                estimated_tokens=estimate_tokens(item["content"]),
            )
        )
    settings = get_generation_settings(session)
    context_length, context_note = get_runtime_context_length(settings["model_name"])
    return ContextMeterData(
        conversation_id=conversation.id,
        model_name=settings["model_name"],
        runtime_context_length=context_length,
        context_note=context_note,
        estimated_tokens_total=sum(section.estimated_tokens for section in sections),
        sections=sections,
    )


def estimate_tokens(content: str) -> int:
    return (len(content) + 3) // 4
