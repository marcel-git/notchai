from uuid import UUID

from sqlmodel import Session, select

from app.models.conversation import Character, Persona, utc_timestamp
from app.schemas.profiles import CharacterCreate, PersonaCreate


def list_characters(session: Session) -> list[Character]:
    return session.exec(select(Character).order_by(Character.name)).all()


def get_character(session: Session, profile_id: UUID) -> Character | None:
    return session.get(Character, str(profile_id))


def create_character(session: Session, fields: CharacterCreate) -> Character:
    character = Character(**fields.model_dump())
    session.add(character)
    session.flush()
    return character


def update_character(
    session: Session,
    character: Character,
    fields: CharacterCreate,
) -> Character:
    for field, value in fields.model_dump().items():
        setattr(character, field, value)
    character.updated_at = utc_timestamp()
    session.flush()
    return character


def delete_character(session: Session, character: Character) -> None:
    session.delete(character)
    session.flush()


def list_personas(session: Session) -> list[Persona]:
    return session.exec(select(Persona).order_by(Persona.name)).all()


def get_persona(session: Session, profile_id: UUID) -> Persona | None:
    return session.get(Persona, str(profile_id))


def create_persona(session: Session, fields: PersonaCreate) -> Persona:
    persona = Persona(**fields.model_dump())
    session.add(persona)
    session.flush()
    return persona


def update_persona(
    session: Session,
    persona: Persona,
    fields: PersonaCreate,
) -> Persona:
    for field, value in fields.model_dump().items():
        setattr(persona, field, value)
    persona.updated_at = utc_timestamp()
    session.flush()
    return persona


def delete_persona(session: Session, persona: Persona) -> None:
    session.delete(persona)
    session.flush()
