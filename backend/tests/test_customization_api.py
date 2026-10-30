import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db import customization, session as database
from app.main import app


class CustomizationApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_chat_engine = database.engine
        self.original_customization_engine = customization.engine
        self.temporary_directory = tempfile.TemporaryDirectory()
        directory = Path(self.temporary_directory.name)
        database.engine = database.create_database_engine(directory / "chat.db")
        customization.engine = customization.create_customization_engine(
            directory / "customization.db"
        )
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)
        database.engine.dispose()
        customization.engine.dispose()
        database.engine = self.original_chat_engine
        customization.engine = self.original_customization_engine
        self.temporary_directory.cleanup()

    def test_guidance_can_be_created_listed_updated_and_deleted(self) -> None:
        endpoint = "/customizations/guidance"
        created = self.client.post(endpoint, json={"text": "Keep replies concise."})
        self.assertEqual(created.status_code, 201)
        entry = created.json()
        self.assertEqual(entry["text"], "Keep replies concise.")
        self.assertEqual(self.client.get(endpoint).json(), [entry])

        updated = self.client.patch(
            f"{endpoint}/{entry['id']}",
            json={"text": "Keep replies warm and concise."},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["text"], "Keep replies warm and concise.")

        deleted = self.client.delete(f"{endpoint}/{entry['id']}")
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(self.client.get(endpoint).json(), [])

    def test_context_meter_reports_global_guidance_separately(self) -> None:
        character = self.client.post(
            "/characters",
            json={
                "name": "Mira",
                "description": "An archivist",
                "personality": "Curious",
                "background": "A mountain library",
                "custom_instructions": "Stay thoughtful",
            },
        ).json()
        self.client.post(
            "/customizations/guidance",
            json={"text": "Never speak for my persona."},
        )
        conversation_id = str(uuid4())
        created = self.client.post(
            "/conversations",
            json={"id": conversation_id, "character_id": character["id"]},
        )
        self.assertEqual(created.status_code, 201)

        with patch(
            "app.services.context_meter.get_runtime_context_length",
            return_value=(8192, None),
        ):
            context = self.client.get(
                f"/conversations/{conversation_id}/context-meter"
            ).json()

        sections = {section["label"]: section for section in context["sections"]}
        self.assertIn("System prompt", sections)
        self.assertEqual(sections["Global user guidance"]["role"], "system")
        self.assertGreater(sections["Global user guidance"]["estimated_tokens"], 0)
        self.assertEqual(
            context["estimated_tokens_total"],
            sum(section["estimated_tokens"] for section in context["sections"]),
        )
