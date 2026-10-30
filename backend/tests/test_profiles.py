import tempfile
import unittest
from pathlib import Path
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db import session as database
from app.db.migrations import upgrade_database
from app.main import app
from app.models.conversation import Character, Conversation, Persona
from app.repositories.conversation_repository import add_user_message
from app.services.chat_service import prepare_message


class ProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_engine = database.engine
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.engine = database.create_database_engine(
            Path(self.temporary_directory.name) / "profiles.db"
        )
        database.engine = self.engine
        upgrade_database(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()
        database.engine = self.original_engine
        self.temporary_directory.cleanup()

    def test_profile_crud_conversation_association_and_delete_protection(self) -> None:
        with TestClient(app) as client:
            character_response = client.post(
                "/characters",
                json={
                    "name": "Mira",
                    "description": "A careful archivist",
                    "personality": "Curious",
                    "background": "Raised in a mountain library",
                    "custom_instructions": "Speak thoughtfully",
                },
            )
            persona_response = client.post(
                "/personas",
                json={
                    "name": "Traveler",
                    "identity": "A wandering cartographer",
                    "appearance": "Weathered cloak",
                    "background": "Searching for a lost map",
                    "behavior": "Ask questions before trusting others",
                },
            )
            self.assertEqual(character_response.status_code, 201)
            self.assertEqual(persona_response.status_code, 201)
            character_id = character_response.json()["id"]
            persona_id = persona_response.json()["id"]

            conversation_id = str(uuid4())
            conversation_response = client.post(
                "/conversations",
                json={
                    "id": conversation_id,
                    "character_id": character_id,
                    "persona_id": persona_id,
                },
            )
            self.assertEqual(conversation_response.status_code, 201)
            reused_persona_response = client.post(
                "/conversations",
                json={
                    "id": str(uuid4()),
                    "character_id": character_id,
                    "persona_id": persona_id,
                },
            )
            self.assertEqual(reused_persona_response.status_code, 201)
            with database.session_scope() as session:
                add_user_message(session, UUID(conversation_id), "Hello, Mira.")

            edited_character = client.put(
                f"/characters/{character_id}",
                json={
                    "name": "Mira",
                    "description": "Now a bold explorer",
                    "personality": "Curious and brave",
                    "background": "Raised in a mountain library",
                    "custom_instructions": "Speak thoughtfully",
                },
            )
            self.assertEqual(edited_character.status_code, 200)
            stored = client.get(f"/conversations/{conversation_id}").json()
            self.assertEqual(stored["character_id"], character_id)
            self.assertEqual(stored["persona_id"], persona_id)
            self.assertEqual(stored["messages"][0]["content"], "Hello, Mira.")

            self.assertEqual(client.get("/characters").json()[0]["name"], "Mira")
            self.assertEqual(
                client.get(f"/characters/{character_id}").json()["id"],
                character_id,
            )
            self.assertEqual(
                client.delete(f"/characters/{character_id}").status_code,
                409,
            )
            self.assertEqual(client.delete(f"/personas/{persona_id}").status_code, 409)

            unused_persona = client.post(
                "/personas",
                json={"name": "Unused"},
            ).json()
            self.assertEqual(
                client.delete(f"/personas/{unused_persona['id']}").status_code,
                204,
            )

    def test_model_prompt_distinguishes_agent_character_and_user_persona(self) -> None:
        with Session(self.engine) as session:
            character = Character(
                name="Mira",
                description="An archivist",
                personality="Curious",
                background="Library keeper",
                custom_instructions="Be thoughtful",
            )
            persona = Persona(
                name="Traveler",
                identity="A cartographer",
                appearance="Blue cloak",
                background="Lost map",
                behavior="Ask questions",
            )
            session.add(character)
            session.add(persona)
            session.flush()
            conversation = Conversation(
                title="New conversation",
                character_id=character.id,
                persona_id=persona.id,
            )
            session.add(conversation)
            session.commit()
            conversation_id = conversation.id

        run = prepare_message(UUID(conversation_id), "Hello")
        system_prompt = run.history[0]["content"]
        self.assertIn("Play the selected character as the agent", system_prompt)
        self.assertIn("Mira", system_prompt)
        self.assertIn("Persona played by the user", system_prompt)
        self.assertIn("Traveler", system_prompt)
        self.assertEqual(
            run.history[-1],
            {"id": "1", "role": "user", "content": "Hello"},
        )


if __name__ == "__main__":
    unittest.main()
