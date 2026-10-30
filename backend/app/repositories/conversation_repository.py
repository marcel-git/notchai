from typing import Any, Literal
from uuid import UUID

from sqlmodel import Session, select

from app.models.conversation import Conversation, Message, utc_timestamp

AssistantStatus = Literal["pending", "streaming", "completed", "interrupted", "failed"]


def _message_data(message: Message) -> dict[str, Any]:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "status": message.status,
        "is_superseded": message.is_superseded,
        "created_at": message.created_at,
    }


def _conversation_data(conversation: Conversation) -> dict[str, Any]:
    return {
        "id": conversation.id,
        "title": conversation.title,
        "character_id": conversation.character_id,
        "persona_id": conversation.persona_id,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": [_message_data(message) for message in conversation.messages],
    }


def create_conversation(
    session: Session,
    conversation_id: UUID,
    character_id: UUID | None = None,
    persona_id: UUID | None = None,
    system_prompt: str | None = None,
) -> dict[str, str | None]:
    conversation = Conversation(
        id=str(conversation_id),
        title="New conversation",
        character_id=str(character_id) if character_id else None,
        persona_id=str(persona_id) if persona_id else None,
        system_prompt=system_prompt,
    )
    session.add(conversation)
    session.flush()
    return {
        "id": conversation.id,
        "title": conversation.title,
        "character_id": conversation.character_id,
        "persona_id": conversation.persona_id,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
    }


def list_conversations(session: Session) -> list[dict[str, str | None]]:
    conversations = session.exec(
        select(Conversation).order_by(Conversation.updated_at.desc())
    ).all()
    return [
        {
            "id": conversation.id,
            "title": conversation.title,
            "character_id": conversation.character_id,
            "persona_id": conversation.persona_id,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
        }
        for conversation in conversations
    ]


def get_conversation(
    session: Session,
    conversation_id: UUID,
) -> dict[str, Any] | None:
    conversation = session.get(Conversation, str(conversation_id))
    return _conversation_data(conversation) if conversation is not None else None


def get_model_history(
    session: Session,
    conversation_id: UUID,
) -> list[dict[str, str]]:
    return [
        {"role": message["role"], "content": message["content"]}
        for message in get_model_history_with_ids(session, conversation_id)
    ]


def get_model_history_with_ids(
    session: Session,
    conversation_id: UUID,
    after_message_id: int | None = None,
) -> list[dict[str, str]]:
    query = select(Message).where(
        Message.conversation_id == str(conversation_id),
        Message.status == "completed",
        Message.is_superseded.is_(False),
    )
    if after_message_id is not None:
        query = query.where(Message.id > after_message_id)
    messages = session.exec(
        query.order_by(Message.id)
    ).all()
    return [
        {
            "id": str(message.id),
            "role": message.role,
            "content": message.content,
        }
        for message in messages
    ]


def update_context_summary(
    session: Session,
    conversation_id: UUID,
    summary: str,
    summarized_through_message_id: int,
) -> None:
    conversation = session.get(Conversation, str(conversation_id))
    if conversation is None:
        raise LookupError(f"Conversation {conversation_id} does not exist.")
    if not summary.strip():
        raise ValueError("A conversation summary cannot be empty.")
    conversation.context_summary = summary
    conversation.summarized_through_message_id = summarized_through_message_id


def add_user_message(
    session: Session,
    conversation_id: UUID,
    content: str,
) -> None:
    conversation = session.get(Conversation, str(conversation_id))
    if conversation is None:
        raise LookupError(f"Conversation {conversation_id} does not exist.")

    session.add(
        Message(
            conversation_id=conversation.id,
            role="user",
            content=content,
            status="completed",
        )
    )
    if conversation.title == "New conversation":
        conversation.title = content if len(content) <= 60 else f"{content[:57]}..."
    conversation.updated_at = utc_timestamp()


def add_assistant_message(session: Session, conversation_id: UUID) -> int:
    message = Message(
        conversation_id=str(conversation_id),
        role="assistant",
        content="",
        status="pending",
    )
    session.add(message)
    session.flush()
    if message.id is None:
        raise RuntimeError("The database did not assign an assistant message ID.")
    return message.id


def prepare_assistant_regeneration(session: Session, message_id: int) -> Message:
    message = session.get(Message, message_id)
    if message is None:
        raise LookupError(f"Message {message_id} does not exist.")
    if message.role != "assistant":
        raise ValueError("Only assistant messages can be regenerated.")
    if message.status not in ("completed", "failed", "interrupted"):
        raise ValueError("This assistant message cannot be regenerated right now.")
    newer_active_message = session.exec(
        select(Message.id)
        .where(
            Message.conversation_id == message.conversation_id,
            Message.id > message.id,
            Message.is_superseded.is_(False),
        )
        .limit(1)
    ).first()
    if newer_active_message is not None:
        raise ValueError("Only the latest response can be regenerated.")
    message.content = ""
    message.status = "pending"
    message.is_superseded = False
    _touch_conversation(session, message.conversation_id)
    return message


def rename_conversation(
    session: Session,
    conversation_id: UUID,
    title: str,
) -> bool:
    conversation = session.get(Conversation, str(conversation_id))
    if conversation is None:
        return False
    conversation.title = title
    conversation.updated_at = utc_timestamp()
    return True


def delete_conversation(session: Session, conversation_id: UUID) -> bool:
    conversation = session.get(Conversation, str(conversation_id))
    if conversation is None:
        return False
    session.delete(conversation)
    return True


def update_assistant_message(
    session: Session,
    message_id: int,
    content: str,
    status: AssistantStatus,
) -> None:
    message = session.get(Message, message_id)
    if message is None:
        raise LookupError(f"Assistant message {message_id} does not exist.")
    message.content = content
    message.status = status
    _touch_conversation(session, message.conversation_id)


def _supersede_following_messages(session: Session, message: Message) -> None:
    following_messages = session.exec(
        select(Message).where(
            Message.conversation_id == message.conversation_id,
            Message.id > message.id,
            Message.is_superseded.is_(False),
        )
    ).all()
    for following in following_messages:
        following.is_superseded = True


def _touch_conversation(session: Session, conversation_id: str) -> None:
    conversation = session.get(Conversation, conversation_id)
    if conversation is not None:
        conversation.updated_at = utc_timestamp()


def interrupt_incomplete_messages(session: Session) -> None:
    messages = session.exec(
        select(Message).where(Message.status.in_(("pending", "streaming")))
    ).all()
    for message in messages:
        message.status = "interrupted"
