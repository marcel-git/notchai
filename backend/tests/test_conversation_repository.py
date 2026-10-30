import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    text,
)
from sqlmodel import Session, SQLModel

from app.db import customization, session as database
from app.db.migrations import upgrade_database
from app.models import Conversation, Message
from app.repositories.conversation_repository import (
    add_assistant_message,
    add_user_message,
    create_conversation,
    get_conversation,
    get_model_history,
    interrupt_incomplete_messages,
    update_assistant_message,
)
from app.services.chat_service import prepare_message, stream_chat
from app.services.model_service import (
    ContextSummaryEvent,
    GuidanceSavedEvent,
    SummarizationStatusEvent,
)


class ConversationRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_engine = database.engine
        self.original_customization_engine = customization.engine
        self.temporary_directory = tempfile.TemporaryDirectory()
        directory = Path(self.temporary_directory.name)
        self.engine = database.create_database_engine(
            directory / "chat.db"
        )
        customization.engine = customization.create_customization_engine(
            directory / "customization.db"
        )
        database.engine = self.engine
        upgrade_database(self.engine)
        self.conversation_id = uuid4()
        with database.session_scope() as session:
            create_conversation(session, self.conversation_id)

    def tearDown(self) -> None:
        self.engine.dispose()
        customization.engine.dispose()
        database.engine = self.original_engine
        customization.engine = self.original_customization_engine
        self.temporary_directory.cleanup()

    def test_persists_conversation_messages_and_model_history(self) -> None:
        with database.session_scope() as session:
            add_user_message(session, self.conversation_id, "Hello")
            assistant_id = add_assistant_message(session, self.conversation_id)

        with database.session_scope() as session:
            pending = get_conversation(session, self.conversation_id)
            self.assertEqual(pending["messages"][1]["status"], "pending")
            update_assistant_message(session, assistant_id, "Hi", "completed")

        with database.session_scope() as session:
            conversation = get_conversation(session, self.conversation_id)
            self.assertEqual(conversation["messages"][1]["content"], "Hi")
            self.assertEqual(conversation["messages"][1]["status"], "completed")
            self.assertEqual(
                get_model_history(session, self.conversation_id),
                [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi"},
                ],
            )

    def test_restart_marks_pending_and_streaming_messages_interrupted(self) -> None:
        with database.session_scope() as session:
            add_assistant_message(session, self.conversation_id)
            streaming_id = add_assistant_message(session, self.conversation_id)
            update_assistant_message(
                session, streaming_id, "Partial text", "streaming"
            )

        with database.session_scope() as session:
            interrupt_incomplete_messages(session)

        with database.session_scope() as session:
            messages = get_conversation(session, self.conversation_id)["messages"]
        self.assertEqual(messages[0]["status"], "interrupted")
        self.assertEqual(messages[1]["status"], "interrupted")
        self.assertEqual(messages[1]["content"], "Partial text")

    def test_persists_user_before_streaming_and_completes_assistant(self) -> None:
        run = prepare_message(self.conversation_id, "Hello")
        with database.session_scope() as session:
            pending = get_conversation(session, self.conversation_id)
        user_message_id = pending["messages"][0]["id"]
        self.assertEqual(pending["messages"][0]["content"], "Hello")
        self.assertEqual(pending["messages"][1]["status"], "pending")

        async def fake_stream(history, _options, _summarized_through_message_id=None):
            self.assertEqual(
                history[-1],
                {"id": str(user_message_id), "role": "user", "content": "Hello"},
            )
            yield "Hello back"

        async def collect_events():
            events = []
            async for event, data in stream_chat(run):
                events.append((event, data))
                if event == "token":
                    with database.session_scope() as session:
                        streaming = get_conversation(session, self.conversation_id)
                    self.assertEqual(streaming["messages"][1]["status"], "streaming")
            return events

        with patch("app.services.chat_service.stream_model", fake_stream):
            events = asyncio.run(collect_events())

        self.assertEqual(
            events,
            [("token", {"token": "Hello back"}), ("done", {})],
        )
        with database.session_scope() as session:
            completed = get_conversation(session, self.conversation_id)
        self.assertEqual(completed["messages"][1]["status"], "completed")
        self.assertEqual(completed["messages"][1]["content"], "Hello back")

    def test_stream_chat_surfaces_guidance_saved_event_without_rule_text(self) -> None:
        run = prepare_message(self.conversation_id, "Remember a preference.")

        async def fake_stream(_history, _options):
            yield GuidanceSavedEvent()
            yield "I will remember that."

        async def collect_events():
            return [event async for event in stream_chat(run)]

        with patch("app.services.chat_service.stream_model", fake_stream):
            events = asyncio.run(collect_events())

        self.assertEqual(
            events,
            [
                ("guidance_saved", {}),
                ("token", {"token": "I will remember that."}),
                ("done", {}),
            ],
        )

    def test_stream_chat_surfaces_summarization_status(self) -> None:
        run = prepare_message(self.conversation_id, "Continue the scene.")

        async def fake_stream(_history, _options):
            yield SummarizationStatusEvent(True)
            yield SummarizationStatusEvent(False)
            yield "The scene continues."

        async def collect_events():
            return [event async for event in stream_chat(run)]

        with patch("app.services.chat_service.stream_model", fake_stream):
            events = asyncio.run(collect_events())

        self.assertEqual(
            events,
            [
                ("summarizing", {}),
                ("summary_finished", {}),
                ("token", {"token": "The scene continues."}),
                ("done", {}),
            ],
        )

    def test_summarized_context_is_reused_without_changing_visible_transcript(self) -> None:
        run = prepare_message(self.conversation_id, "First scene.")
        summarized_through = int(run.history[-1]["id"])

        async def fake_stream(_history, _options):
            yield ContextSummaryEvent("The party entered the archive.", summarized_through)
            yield "They found a map."

        async def collect_events():
            return [event async for event in stream_chat(run)]

        with patch("app.services.chat_service.stream_model", fake_stream):
            events = asyncio.run(collect_events())
        self.assertEqual(events[-1], ("done", {}))

        with database.session_scope() as session:
            conversation = session.get(Conversation, str(self.conversation_id))
            self.assertEqual(
                conversation.context_summary,
                "The party entered the archive.",
            )
            self.assertEqual(
                conversation.summarized_through_message_id,
                summarized_through,
            )
            visible_history = get_conversation(session, self.conversation_id)
            self.assertEqual(visible_history["messages"][0]["content"], "First scene.")
            self.assertEqual(
                visible_history["messages"][1]["content"],
                "They found a map.",
            )

        next_run = prepare_message(self.conversation_id, "What is on the map?")
        self.assertEqual(next_run.history[0]["id"], "conversation-summary")
        self.assertIn("The party entered the archive.", next_run.history[0]["content"])
        self.assertNotIn("First scene.", [item["content"] for item in next_run.history])
        self.assertEqual(next_run.history[-1]["content"], "What is on the map?")

    def test_initial_migration_adopts_existing_tables_without_losing_data(self) -> None:
        existing_engine = database.create_database_engine(
            Path(self.temporary_directory.name) / "existing.db"
        )
        try:
            self.assertIn(Conversation.__tablename__, SQLModel.metadata.tables)
            self.assertIn(Message.__tablename__, SQLModel.metadata.tables)
            legacy_metadata = MetaData()
            conversations = Table(
                "conversations",
                legacy_metadata,
                Column("id", Text, primary_key=True),
                Column("title", Text, nullable=False),
                Column("created_at", Text, nullable=False),
                Column("updated_at", Text, nullable=False),
            )
            messages = Table(
                "messages",
                legacy_metadata,
                Column("id", Integer, primary_key=True, autoincrement=True),
                Column(
                    "conversation_id",
                    Text,
                    ForeignKey("conversations.id", ondelete="CASCADE"),
                    nullable=False,
                ),
                Column("role", Text, nullable=False),
                Column("content", Text, nullable=False),
                Column("status", Text, nullable=False),
                Column("created_at", Text, nullable=False),
                CheckConstraint("role IN ('user', 'assistant')"),
                CheckConstraint(
                    "status IN ('pending', 'streaming', 'completed', "
                    "'interrupted', 'failed')"
                ),
            )
            Index("messages_conversation_id_id", messages.c.conversation_id, messages.c.id)
            legacy_metadata.create_all(existing_engine)
            conversation_id = uuid4()
            timestamp = "2026-01-01T00:00:00+00:00"
            with existing_engine.begin() as connection:
                connection.execute(
                    conversations.insert().values(
                        id=str(conversation_id),
                        title="Existing chat",
                        created_at=timestamp,
                        updated_at=timestamp,
                    )
                )
                connection.execute(
                    messages.insert().values(
                        conversation_id=str(conversation_id),
                        role="user",
                        content="Existing message",
                        status="completed",
                        created_at=timestamp,
                    )
                )

            upgrade_database(existing_engine)

            with Session(existing_engine) as session:
                conversation = get_conversation(session, conversation_id)
                self.assertEqual(
                    conversation["messages"][0]["content"],
                    "Existing message",
                )
            with existing_engine.connect() as connection:
                revision = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one()
            self.assertEqual(revision, "0008_summarization_settings")
        finally:
            existing_engine.dispose()


if __name__ == "__main__":
    unittest.main()
