import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.db import session as database
from app.db.migrations import upgrade_database
from app.main import app


class RoleplayControlsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_engine = database.engine
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.engine = database.create_database_engine(
            Path(self.temporary_directory.name) / "roleplay.db"
        )
        database.engine = self.engine
        upgrade_database(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()
        database.engine = self.original_engine
        self.temporary_directory.cleanup()

    def test_latest_only_regeneration_settings_prompt_inspection_and_conversation_crud(self) -> None:
        with TestClient(app) as client:
            character = client.post(
                "/characters",
                json={
                    "name": "Mira",
                    "description": "An archivist",
                    "personality": "Curious",
                    "background": "A mountain library",
                    "custom_instructions": "Stay thoughtful",
                },
            ).json()
            persona = client.post(
                "/personas",
                json={
                    "name": "Avery",
                    "identity": "A cartographer",
                    "appearance": "A blue cloak",
                    "background": "A missing atlas",
                    "behavior": "Be curious",
                },
            ).json()
            preview = client.post(
                "/conversations/prompt-preview",
                json={
                    "character_id": character["id"],
                    "persona_id": persona["id"],
                },
            )
            self.assertEqual(preview.status_code, 200)
            self.assertIsNone(preview.json()["conversation_id"])
            self.assertIn("Mira", preview.json()["system_prompt"])
            self.assertIn("Avery", preview.json()["system_prompt"])
            custom_system_prompt = (
                preview.json()["system_prompt"] + "\nKeep replies concise and atmospheric."
            )
            conversation_id = str(uuid4())
            created = client.post(
                "/conversations",
                json={
                    "id": conversation_id,
                    "character_id": character["id"],
                    "persona_id": persona["id"],
                    "system_prompt": custom_system_prompt,
                },
            )
            self.assertEqual(created.status_code, 201)

            async def first_response(history, options):
                self.assertEqual(history[0], {"role": "system", "content": custom_system_prompt})
                self.assertEqual(history[-1]["content"], "Original question")
                self.assertEqual(options.model_name, "mridiot918/qwen3.6-27b-uncensored")
                yield "Original answer"

            with patch("app.services.chat_service.stream_model", first_response):
                first = client.post(
                    "/chat",
                    json={
                        "conversation_id": conversation_id,
                        "message": "Original question",
                    },
                )
            self.assertIn("event: done", first.text)

            async def second_response(_history, _options):
                yield "Follow-up answer"

            with patch("app.services.chat_service.stream_model", second_response):
                second = client.post(
                    "/chat",
                    json={
                        "conversation_id": conversation_id,
                        "message": "Follow-up question",
                    },
                )
            self.assertIn("event: done", second.text)

            original = client.get(f"/conversations/{conversation_id}").json()
            first_assistant_id = original["messages"][1]["id"]
            self.assertEqual(
                client.put(
                    f"/messages/{original['messages'][0]['id']}",
                    json={"content": "Revised question"},
                ).status_code,
                404,
            )
            older_regeneration = client.post(
                f"/messages/{first_assistant_id}/regenerate",
            )
            self.assertEqual(older_regeneration.status_code, 409)
            self.assertIn("latest response", older_regeneration.json()["detail"])
            latest_assistant_id = original["messages"][-1]["id"]

            async def replacement_response(_history, _options):
                yield "Replacement answer"

            with patch("app.services.chat_service.stream_model", replacement_response):
                regenerated = client.post(f"/messages/{latest_assistant_id}/regenerate")
            self.assertIn("event: done", regenerated.text)
            after_regenerate = client.get(f"/conversations/{conversation_id}").json()
            replacement = after_regenerate["messages"][-1]
            self.assertEqual(replacement["content"], "Replacement answer")
            self.assertNotIn("versions", replacement)

            settings = client.put(
                "/settings",
                json={
                    "model_name": "local-test-model",
                    "num_predict": 768,
                    "temperature": 0.35,
                    "top_p": 0.82,
                },
            )
            self.assertEqual(settings.status_code, 200)
            self.assertEqual(client.get("/settings").json()["model_name"], "local-test-model")
            self.assertEqual(client.get("/settings").json()["num_predict"], 768)
            prompt = client.get(f"/conversations/{conversation_id}/prompt").json()
            self.assertEqual(prompt["model_name"], "local-test-model")
            self.assertEqual(prompt["system_prompt"], custom_system_prompt)
            self.assertNotIn("messages", prompt)

            async def configured_response(_history, options):
                self.assertEqual(options.model_name, "local-test-model")
                self.assertEqual(options.num_predict, 768)
                self.assertEqual(options.temperature, 0.35)
                self.assertEqual(options.top_p, 0.82)
                yield "Configured response"

            with patch("app.services.chat_service.stream_model", configured_response):
                configured_chat = client.post(
                    "/chat",
                    json={
                        "conversation_id": conversation_id,
                        "message": "Check the updated generation settings",
                    },
                )
            self.assertIn("event: done", configured_chat.text)

            renamed = client.patch(
                f"/conversations/{conversation_id}",
                json={"title": "The revised journey"},
            )
            self.assertEqual(renamed.json()["title"], "The revised journey")
            self.assertEqual(client.delete(f"/conversations/{conversation_id}").status_code, 204)
            self.assertEqual(client.get(f"/conversations/{conversation_id}").status_code, 404)

    def test_empty_model_response_is_failed_instead_of_completed(self) -> None:
        with TestClient(app) as client:
            character = client.post(
                "/characters",
                json={
                    "name": "Mira",
                    "description": "An archivist",
                    "personality": "Curious",
                    "background": "A mountain library",
                    "custom_instructions": "Stay thoughtful",
                },
            ).json()
            persona = client.post(
                "/personas",
                json={
                    "name": "Avery",
                    "identity": "A cartographer",
                    "appearance": "A blue cloak",
                    "background": "A missing atlas",
                    "behavior": "Be curious",
                },
            ).json()
            conversation_id = str(uuid4())
            client.post(
                "/conversations",
                json={
                    "id": conversation_id,
                    "character_id": character["id"],
                    "persona_id": persona["id"],
                },
            )

            async def empty_response(_history, _options):
                if False:
                    yield ""

            with patch("app.services.chat_service.stream_model", empty_response):
                response = client.post(
                    "/chat",
                    json={
                        "conversation_id": conversation_id,
                        "message": "Please answer",
                    },
                )

            self.assertIn("event: error", response.text)
            self.assertNotIn("event: done", response.text)
            assistant = client.get(f"/conversations/{conversation_id}").json()["messages"][-1]
            self.assertEqual(assistant["status"], "failed")
            self.assertIn("without returning any visible text", assistant["content"])
            self.assertIn("4096-token generation limit", assistant["content"])

    def test_conversation_can_start_as_stranger_without_a_persona(self) -> None:
        with TestClient(app) as client:
            character = client.post(
                "/characters",
                json={
                    "name": "Mira",
                    "description": "An archivist",
                    "personality": "Curious",
                    "background": "A mountain library",
                    "custom_instructions": "Stay thoughtful",
                },
            ).json()
            preview = client.post(
                "/conversations/prompt-preview",
                json={"character_id": character["id"]},
            )
            self.assertEqual(preview.status_code, 200)
            self.assertIn("Name: Stranger", preview.json()["system_prompt"])

            conversation_id = str(uuid4())
            created = client.post(
                "/conversations",
                json={
                    "id": conversation_id,
                    "character_id": character["id"],
                    "persona_id": None,
                    "system_prompt": preview.json()["system_prompt"],
                },
            )
            self.assertEqual(created.status_code, 201)
            self.assertIsNone(created.json()["persona_id"])

            async def stranger_response(history, _options):
                self.assertIn("Name: Stranger", history[0]["content"])
                yield "Hello, stranger."

            with patch("app.services.chat_service.stream_model", stranger_response):
                response = client.post(
                    "/chat",
                    json={
                        "conversation_id": conversation_id,
                        "message": "Hello.",
                    },
                )
            self.assertIn("event: done", response.text)

    def test_context_meter_includes_system_history_and_runtime_limit(self) -> None:
        with TestClient(app) as client:
            character = client.post(
                "/characters",
                json={
                    "name": "Mira",
                    "description": "An archivist",
                    "personality": "Curious",
                    "background": "A mountain library",
                    "custom_instructions": "Stay thoughtful",
                },
            ).json()
            conversation_id = str(uuid4())
            created = client.post(
                "/conversations",
                json={
                    "id": conversation_id,
                    "character_id": character["id"],
                    "system_prompt": "Custom system prompt",
                },
            )
            self.assertEqual(created.status_code, 201)

            async def fake_response(_history, _options):
                yield "An assistant reply."

            with patch("app.services.chat_service.stream_model", fake_response):
                response = client.post(
                    "/chat",
                    json={"conversation_id": conversation_id, "message": "A user message."},
                )
            self.assertIn("event: done", response.text)

            with patch(
                "app.services.context_meter.get_runtime_context_length",
                return_value=(65536, None),
            ):
                meter = client.get(
                    f"/conversations/{conversation_id}/context-meter"
                )

            self.assertEqual(meter.status_code, 200)
            data = meter.json()
            self.assertEqual(data["runtime_context_length"], 65536)
            self.assertEqual(
                [(section["role"], section["label"]) for section in data["sections"]],
                [
                    ("system", "System prompt"),
                    ("user", "User message 1"),
                    ("assistant", "Assistant message 1"),
                ],
            )
            self.assertEqual(
                data["estimated_tokens_total"],
                sum(section["estimated_tokens"] for section in data["sections"]),
            )


if __name__ == "__main__":
    unittest.main()
