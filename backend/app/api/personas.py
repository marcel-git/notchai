from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError

from app.db.session import session_scope
from app.repositories.profile_repository import (
    create_persona,
    delete_persona,
    get_persona,
    list_personas,
    update_persona,
)
from app.schemas.profiles import PersonaCreate, PersonaRead

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("", response_model=list[PersonaRead])
def personas() -> list[PersonaRead]:
    with session_scope() as session:
        return [PersonaRead.model_validate(item) for item in list_personas(session)]


@router.post("", response_model=PersonaRead, status_code=status.HTTP_201_CREATED)
def new_persona(request: PersonaCreate) -> PersonaRead:
    with session_scope() as session:
        return PersonaRead.model_validate(create_persona(session, request))


@router.get("/{persona_id}", response_model=PersonaRead)
def persona(persona_id: UUID) -> PersonaRead:
    with session_scope() as session:
        result = get_persona(session, persona_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Persona not found.")
        return PersonaRead.model_validate(result)


@router.put("/{persona_id}", response_model=PersonaRead)
def edit_persona(persona_id: UUID, request: PersonaCreate) -> PersonaRead:
    with session_scope() as session:
        result = get_persona(session, persona_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Persona not found.")
        return PersonaRead.model_validate(update_persona(session, result, request))


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_persona(persona_id: UUID) -> Response:
    try:
        with session_scope() as session:
            result = get_persona(session, persona_id)
            if result is None:
                raise HTTPException(status_code=404, detail="Persona not found.")
            delete_persona(session, result)
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This persona is used by a conversation and cannot be deleted.",
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
