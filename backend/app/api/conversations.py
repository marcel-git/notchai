import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from app.db.session import session_scope
from app.schemas.chat import ChatRequest, CreateConversationRequest
from app.schemas.roleplay import (
    ContextMeterData,
    ConversationTitleRequest,
    PromptInspection,
    PromptPreviewRequest,
)
from app.repositories.conversation_repository import (
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    rename_conversation,
)
from app.repositories.profile_repository import get_character, get_persona
from app.repositories.settings_repository import get_generation_settings
from app.models.conversation import Conversation as ConversationModel
from app.services.chat_service import (
    ChatRun,
    prepare_message,
    prepare_regeneration,
    stream_chat,
)
from app.services.context_meter import build_context_meter
from app.services.prompt_builder import build_system_prompt

router = APIRouter()


def encode_event(event: str, data: dict[str, str]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_response(run: ChatRun) -> AsyncIterator[str]:
    async for event, data in stream_chat(run):
        yield encode_event(event, data)


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    with session_scope() as session:
        if get_conversation(session, request.conversation_id) is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    run = prepare_message(request.conversation_id, request.message)
    return _streaming_response(run)


@router.post("/messages/{message_id}/regenerate")
async def regenerate(message_id: int) -> StreamingResponse:
    try:
        run = prepare_regeneration(message_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return _streaming_response(run)


@router.get("/conversations")
async def conversations() -> list[dict[str, str | None]]:
    with session_scope() as session:
        return list_conversations(session)


@router.post(
    "/conversations/prompt-preview",
    response_model=PromptInspection,
)
async def preview_conversation_prompt(
    request: PromptPreviewRequest,
) -> PromptInspection:
    with session_scope() as session:
        character = get_character(session, request.character_id)
        if character is None:
            raise HTTPException(status_code=404, detail="Character not found.")
        persona = (
            get_persona(session, request.persona_id)
            if request.persona_id is not None
            else None
        )
        if request.persona_id is not None and persona is None:
            raise HTTPException(status_code=404, detail="Persona not found.")
        settings = get_generation_settings(session)
        return PromptInspection(
            conversation_id=None,
            **settings,
            system_prompt=build_system_prompt(character, persona),
        )


@router.post("/conversations", status_code=201)
async def new_conversation(
    request: CreateConversationRequest,
) -> dict[str, str | None]:
    with session_scope() as session:
        if get_conversation(session, request.id) is not None:
            raise HTTPException(status_code=409, detail="Conversation already exists.")
        character = get_character(session, request.character_id)
        if character is None:
            raise HTTPException(status_code=404, detail="Character not found.")
        persona = (
            get_persona(session, request.persona_id)
            if request.persona_id is not None
            else None
        )
        if request.persona_id is not None and persona is None:
            raise HTTPException(status_code=404, detail="Persona not found.")
        system_prompt = request.system_prompt
        if system_prompt is None:
            system_prompt = build_system_prompt(character, persona)
        return create_conversation(
            session,
            request.id,
            request.character_id,
            request.persona_id,
            system_prompt,
        )


@router.get("/conversations/{conversation_id}")
async def conversation(conversation_id: UUID) -> dict:
    with session_scope() as session:
        result = get_conversation(session, conversation_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        return result


@router.patch("/conversations/{conversation_id}")
async def update_conversation_title(
    conversation_id: UUID,
    request: ConversationTitleRequest,
) -> dict[str, str | None]:
    with session_scope() as session:
        if not rename_conversation(session, conversation_id, request.title):
            raise HTTPException(status_code=404, detail="Conversation not found.")
        result = get_conversation(session, conversation_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        return {
            "id": result["id"],
            "title": result["title"],
            "character_id": result["character_id"],
            "persona_id": result["persona_id"],
            "created_at": result["created_at"],
            "updated_at": result["updated_at"],
        }


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_conversation(conversation_id: UUID) -> Response:
    with session_scope() as session:
        if not delete_conversation(session, conversation_id):
            raise HTTPException(status_code=404, detail="Conversation not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/conversations/{conversation_id}/prompt",
    response_model=PromptInspection,
)
async def inspect_prompt(conversation_id: UUID) -> PromptInspection:
    with session_scope() as session:
        conversation = session.get(ConversationModel, str(conversation_id))
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        system_prompt = conversation.system_prompt
        if system_prompt is None:
            system_prompt = build_system_prompt(
                conversation.character,
                conversation.persona,
            )
        settings = get_generation_settings(session)
        return PromptInspection(
            conversation_id=conversation_id,
            **settings,
            system_prompt=system_prompt,
        )


@router.get(
    "/conversations/{conversation_id}/context-meter",
    response_model=ContextMeterData,
)
def inspect_context_meter(conversation_id: UUID) -> ContextMeterData:
    with session_scope() as session:
        conversation = session.get(ConversationModel, str(conversation_id))
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        return build_context_meter(session, conversation)


def _streaming_response(run: ChatRun) -> StreamingResponse:
    return StreamingResponse(
        stream_response(run),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
