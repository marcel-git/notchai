import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessageChunk, HumanMessage, ToolMessage

from app.db import customization
from app.services.model_service import (
    ContextSummaryEvent,
    GenerationOptions,
    GuidanceSavedEvent,
    ModelStreamEvent,
    SUMMARY_MESSAGE_PREFIX,
    SummarizationStatusEvent,
    stream_model,
)
from app.services.prompt_builder import build_prompt, strip_guidance_section


class CustomizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_engine = customization.engine
        self.temporary_directory = tempfile.TemporaryDirectory()
        customization.engine = customization.create_customization_engine(
            Path(self.temporary_directory.name) / "customization.db"
        )
        customization.initialize_customization_database()

    def tearDown(self) -> None:
        customization.engine.dispose()
        customization.engine = self.original_engine
        self.temporary_directory.cleanup()

    def test_guidance_persists_and_is_appended_to_system_prompt(self) -> None:
        customization.add_guidance("Keep replies concise.")
        prompt = build_prompt(
            None,
            None,
            [{"role": "user", "content": "Hello"}],
            guidance=customization.list_guidance(),
        )
        self.assertEqual(prompt[0]["role"], "system")
        self.assertIn("- Keep replies concise.", prompt[0]["content"])
        self.assertEqual(prompt[1], {"role": "user", "content": "Hello"})

    def test_preview_guidance_is_not_frozen_into_a_conversation_prompt(self) -> None:
        customization.add_guidance("Keep replies concise.")
        initial_prompt = build_prompt(
            None,
            None,
            [],
            system_prompt="Character instructions.",
            guidance=customization.list_guidance(),
        )[0]["content"]
        stored_prompt = strip_guidance_section(
            initial_prompt,
            customization.list_guidance(),
        )

        customization.add_guidance("Do not speak for my persona.")
        next_prompt = build_prompt(
            None,
            None,
            [],
            system_prompt=stored_prompt,
            guidance=customization.list_guidance(),
        )[0]["content"]

        self.assertEqual(stored_prompt, "Character instructions.")
        self.assertIn("- Keep replies concise.", next_prompt)
        self.assertIn("- Do not speak for my persona.", next_prompt)
        self.assertEqual(next_prompt.count("Global user guidance:"), 1)

    def test_agent_streams_guidance_saved_event_and_keeps_system_prompt_separate(self) -> None:
        test_case = self

        class FakeAgent:
            async def astream(self, _input, *, config, stream_mode):
                test_case.assertEqual(config["recursion_limit"], 7)
                test_case.assertEqual(
                    stream_mode,
                    ["messages", "updates", "values", "custom"],
                )
                yield "messages", (
                    AIMessageChunk(content="I will remember that."),
                    {"langgraph_node": "model"},
                )
                customization.add_guidance("Keep replies concise.")
                yield "updates", {
                    "tools": {
                        "messages": [
                            ToolMessage(
                                content="Guidance saved for all conversations.",
                                tool_call_id="call-1",
                                name="remember_guidance",
                            )
                        ]
                    }
                }
                yield "values", {"messages": []}

        async def collect() -> list[ModelStreamEvent]:
            return [
                token
                async for token in stream_model(
                    [
                        {"role": "system", "content": "System instructions."},
                        {
                            "id": "1",
                            "role": "user",
                            "content": "Keep replies concise.",
                        },
                    ],
                    GenerationOptions("test-model", 100, 0.7, 0.9),
                )
            ]

        with (
            patch("app.services.model_service.ChatOllama") as ollama,
            patch(
                "app.services.model_service.create_agent",
                return_value=FakeAgent(),
            ) as create_agent,
        ):
            output = asyncio.run(collect())

        self.assertEqual(output, ["I will remember that.", GuidanceSavedEvent()])
        self.assertEqual(customization.list_guidance(), ["Keep replies concise."])
        self.assertEqual(ollama.call_args.kwargs["model"], "test-model")
        self.assertEqual(
            create_agent.call_args.kwargs["system_prompt"],
            "System instructions.",
        )
        self.assertEqual(
            create_agent.call_args.kwargs["middleware"][0].trigger,
            [("tokens", 16384), ("messages", 40)],
        )

    def test_stream_model_persists_the_summarized_message_boundary(self) -> None:
        class FakeAgent:
            async def astream(self, _input, *, config, stream_mode):
                yield "values", {
                    "messages": [
                        HumanMessage(
                            content=f"{SUMMARY_MESSAGE_PREFIX}Important plot details.",
                            additional_kwargs={"lc_source": "summarization"},
                        ),
                        HumanMessage(content="Latest message.", id="12"),
                    ]
                }

        async def collect() -> list[ModelStreamEvent]:
            return [
                event
                async for event in stream_model(
                    [
                        {"role": "system", "content": "System instructions."},
                        {"id": "10", "role": "user", "content": "Old message."},
                        {"id": "11", "role": "assistant", "content": "Old reply."},
                        {"id": "12", "role": "user", "content": "Latest message."},
                    ],
                    GenerationOptions("test-model", 100, 0.7, 0.9),
                    summarized_through_message_id=8,
                )
            ]

        with (
            patch("app.services.model_service.ChatOllama"),
            patch(
                "app.services.model_service.create_agent",
                return_value=FakeAgent(),
            ),
        ):
            output = asyncio.run(collect())

        self.assertEqual(
            output,
            [ContextSummaryEvent("Important plot details.", 11)],
        )

    def test_summarization_status_streams_while_middleware_is_running(self) -> None:
        history = [
            {
                "id": str(index),
                "role": "user" if index % 2 == 0 else "assistant",
                "content": f"Scene {index}: " + ("A detailed event. " * 80),
            }
            for index in range(1, 23)
        ]
        options = GenerationOptions(
            "test-model",
            100,
            0.1,
            0.9,
            summarize_trigger_tokens=256,
            summarize_trigger_messages=40,
        )
        fake_model = FakeListChatModel(
            responses=["The first scene established an archive.", "The answer is ready."]
        )

        async def collect() -> list[ModelStreamEvent]:
            return [event async for event in stream_model(history, options)]

        with (
            patch(
                "app.services.model_service.ChatOllama",
                return_value=fake_model,
            ),
            patch("app.services.model_service.CUSTOMIZATION_TOOLS", []),
        ):
            output = asyncio.run(collect())

        statuses = [
            event for event in output if isinstance(event, SummarizationStatusEvent)
        ]
        self.assertEqual(
            statuses,
            [SummarizationStatusEvent(True), SummarizationStatusEvent(False)],
        )
        self.assertIn(
            ContextSummaryEvent(
                "The first scene established an archive.",
                2,
            ),
            output,
        )

    def test_model_reasoning_option_is_passed_to_ollama(self) -> None:
        class FakeAgent:
            async def astream(self, _input, *, config, stream_mode):
                yield "messages", (
                    AIMessageChunk(content="Answer."),
                    {"langgraph_node": "model"},
                )
                yield "values", {"messages": []}

        async def collect() -> list[ModelStreamEvent]:
            return [
                event
                async for event in stream_model(
                    [{"role": "user", "content": "Hello"}],
                    GenerationOptions(
                        "test-model",
                        100,
                        0.7,
                        0.9,
                        reasoning=False,
                    ),
                )
            ]

        with (
            patch("app.services.model_service.ChatOllama") as ollama,
            patch(
                "app.services.model_service.create_agent",
                return_value=FakeAgent(),
            ),
        ):
            output = asyncio.run(collect())

        self.assertEqual(output, ["Answer."])
        self.assertFalse(ollama.call_args.kwargs["reasoning"])

    def test_guidance_is_bounded_and_duplicate_saves_are_idempotent(self) -> None:
        message = customization.add_guidance("Keep replies concise.")
        self.assertEqual(message, "Guidance saved for all conversations.")
        self.assertEqual(
            customization.add_guidance("Keep replies concise."),
            "That guidance is already saved.",
        )
        with self.assertRaises(ValueError):
            customization.add_guidance("x" * (customization.MAX_GUIDANCE_LENGTH + 1))
