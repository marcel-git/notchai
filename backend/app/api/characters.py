from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError

from app.db.session import session_scope
from app.repositories.profile_repository import (
    create_character,
    delete_character,
    get_character,
    list_characters,
    update_character,
)
from app.schemas.profiles import CharacterCreate, CharacterRead

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("", response_model=list[CharacterRead])
def characters() -> list[CharacterRead]:
    with session_scope() as session:
        return [CharacterRead.model_validate(item) for item in list_characters(session)]


@router.post("", response_model=CharacterRead, status_code=status.HTTP_201_CREATED)
def new_character(request: CharacterCreate) -> CharacterRead:
    with session_scope() as session:
        return CharacterRead.model_validate(create_character(session, request))


@router.get("/{character_id}", response_model=CharacterRead)
def character(character_id: UUID) -> CharacterRead:
    with session_scope() as session:
        result = get_character(session, character_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Character not found.")
        return CharacterRead.model_validate(result)


@router.put("/{character_id}", response_model=CharacterRead)
def edit_character(character_id: UUID, request: CharacterCreate) -> CharacterRead:
    with session_scope() as session:
        result = get_character(session, character_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Character not found.")
        return CharacterRead.model_validate(update_character(session, result, request))


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_character(character_id: UUID) -> Response:
    try:
        with session_scope() as session:
            result = get_character(session, character_id)
            if result is None:
                raise HTTPException(status_code=404, detail="Character not found.")
            delete_character(session, result)
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This character is used by a conversation and cannot be deleted.",
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
