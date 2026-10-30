import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.messages import AIMessageChunk, ToolMessage

from app.db import customization
from app.services.model_service import (
    GenerationOptions,
    GuidanceSavedEvent,
    ModelStreamEvent,
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

    def test_model_can_save_guidance_through_a_tool_call(self) -> None:
        class FakeModel:
            def __init__(self) -> None:
                self.round = 0

            def bind_tools(self, _tools):
                return self

            async def astream(self, messages):
                if self.round == 0:
                    self.round += 1
                    yield AIMessageChunk(
                        content="",
                        tool_call_chunks=[
                            {
                                "name": "remember_guidance",
                                "args": (
                                    '{"guidance":"Keep replies concise."}'
                                ),
                                "id": "call-1",
                                "index": 0,
                            }
                        ],
                    )
                    return

                self.assert_tool_response(messages)
                yield AIMessageChunk(content="I will remember that.")

            @staticmethod
            def assert_tool_response(messages) -> None:
                if not isinstance(messages[-1], ToolMessage):
                    raise AssertionError("The tool result was not sent to the model.")

        model = FakeModel()

        async def collect() -> list[ModelStreamEvent]:
            return [
                token
                async for token in stream_model(
                    [{"role": "user", "content": "Keep replies concise."}],
                    GenerationOptions("test-model", 100, 0.7, 0.9),
                )
            ]

        with patch("app.services.model_service.ChatOllama", return_value=model):
            output = asyncio.run(collect())

        self.assertEqual(output, [GuidanceSavedEvent(), "I will remember that."])
        self.assertEqual(customization.list_guidance(), ["Keep replies concise."])

    def test_model_reasoning_option_is_passed_to_ollama(self) -> None:
        class FakeModel:
            def bind_tools(self, _tools):
                return self

            async def astream(self, _messages):
                yield AIMessageChunk(content="Answer.")

        model = FakeModel()

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

        with patch(
            "app.services.model_service.ChatOllama",
            return_value=model,
        ) as ollama:
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
