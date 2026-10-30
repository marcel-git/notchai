import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session

from app.db.session import session_scope
from app.db.customization import list_guidance
from app.repositories.conversation_repository import (
    AssistantStatus,
    add_assistant_message,
    add_user_message,
    get_model_history_with_ids,
    prepare_assistant_regeneration,
    update_context_summary,
    update_assistant_message,
)
from app.models.conversation import Conversation
from app.repositories.settings_repository import get_generation_settings
from app.services.model_service import (
    GenerationOptions,
    ContextSummaryEvent,
    GuidanceSavedEvent,
    REQUEST_TIMEOUT,
    SUMMARY_MESSAGE_PREFIX,
    SummarizationStatusEvent,
    stream_model,
)
from app.services.prompt_builder import build_prompt

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChatRun:
    conversation_id: UUID
    history: list[dict[str, str]]
    assistant_message_id: int
    options: GenerationOptions
    summarized_through_message_id: int | None


class EmptyModelResponseError(RuntimeError):
    pass


def prepare_message(conversation_id: UUID, message: str) -> ChatRun:
    with session_scope() as session:
        conversation = session.get(Conversation, str(conversation_id))
        if conversation is None:
            raise LookupError(f"Conversation {conversation_id} does not exist.")
        add_user_message(session, conversation_id, message)
        assistant_message_id = add_assistant_message(session, conversation_id)
        return _build_run(session, conversation, assistant_message_id)


def prepare_regeneration(message_id: int) -> ChatRun:
    with session_scope() as session:
        message = prepare_assistant_regeneration(session, message_id)
        conversation = session.get(Conversation, message.conversation_id)
        if conversation is None:
            raise LookupError(f"Conversation {message.conversation_id} does not exist.")
        return _build_run(session, conversation, message_id)


def _build_run(
    session: Session,
    conversation: Conversation,
    assistant_message_id: int,
) -> ChatRun:
    conversation_id = UUID(conversation.id)
    history = get_model_history_with_ids(
        session,
        conversation_id,
        conversation.summarized_through_message_id,
    )
    if conversation.context_summary is not None:
        history.insert(
            0,
            {
                "id": "conversation-summary",
                "role": "user",
                "content": f"{SUMMARY_MESSAGE_PREFIX}{conversation.context_summary}",
            },
        )
    prompt = build_prompt(
        conversation.character,
        conversation.persona,
        history,
        system_prompt=conversation.system_prompt,
        guidance=list_guidance(),
    )
    settings = get_generation_settings(session)
    options = GenerationOptions(**settings)
    return ChatRun(
        conversation_id,
        prompt,
        assistant_message_id,
        options,
        conversation.summarized_through_message_id,
    )


async def stream_chat(
    run: ChatRun,
) -> AsyncIterator[tuple[str, dict[str, str]]]:
    response_content = ""
    finished = False
    try:
        _update_assistant(run.assistant_message_id, response_content, "streaming")
        model_events = (
            stream_model(run.history, run.options)
            if run.summarized_through_message_id is None
            else stream_model(
                run.history,
                run.options,
                run.summarized_through_message_id,
            )
        )
        async for model_event in model_events:
            if isinstance(model_event, GuidanceSavedEvent):
                yield "guidance_saved", {}
                continue
            if isinstance(model_event, SummarizationStatusEvent):
                event = "summarizing" if model_event.is_active else "summary_finished"
                yield event, {}
                continue
            if isinstance(model_event, ContextSummaryEvent):
                _update_context_summary(run.conversation_id, model_event)
                continue
            token = model_event
            response_content += token
            _update_assistant(run.assistant_message_id, response_content, "streaming")
            yield "token", {"token": token}
        if not response_content.strip():
            raise EmptyModelResponseError()
        _update_assistant(run.assistant_message_id, response_content, "completed")
        finished = True
        yield "done", {}
    except asyncio.CancelledError:
        _update_assistant(run.assistant_message_id, response_content, "interrupted")
        finished = True
        raise
    except Exception as error:
        logger.exception("Failed to stream a response from the chat agent.")
        message = describe_model_error(
            error,
            run.options.model_name,
            run.options.num_predict,
        )
        _update_assistant(run.assistant_message_id, message, "failed")
        finished = True
        yield "error", {"error": message}
    finally:
        if not finished:
            _update_assistant(run.assistant_message_id, response_content, "interrupted")


def _update_assistant(
    message_id: int,
    content: str,
    status: AssistantStatus,
) -> None:
    with session_scope() as session:
        update_assistant_message(session, message_id, content, status)


def _update_context_summary(
    conversation_id: UUID,
    event: ContextSummaryEvent,
) -> None:
    with session_scope() as session:
        update_context_summary(
            session,
            conversation_id,
            event.summary,
            event.summarized_through_message_id,
        )


def describe_model_error(
    error: Exception,
    model_name: str,
    num_predict: int,
) -> str:
    details = str(error)
    lowered = details.lower()
    if isinstance(error, EmptyModelResponseError):
        return (
            "The local model finished without returning any visible text. "
            f"Reasoning may have used the full {num_predict}-token generation limit. "
            "Increase Response length (tokens) in Generation settings and try again."
        )
    if isinstance(error, (asyncio.TimeoutError, TimeoutError)):
        return f"The local model did not respond within {REQUEST_TIMEOUT:g} seconds."
    if "not found" in lowered or "pull model" in lowered:
        return (
            f"The selected Ollama model '{model_name}' is unavailable. "
            f"Pull it with `ollama pull {model_name}` and try again."
        )
    if (
        "connect" in lowered
        or "connection refused" in lowered
        or "connection attempts failed" in lowered
    ):
        return "Ollama is unavailable. Check that it is running and try again."
    if details:
        return f"The local model request failed: {details[:300]}"
    return "The local model request failed. Check the Ollama service and try again."
