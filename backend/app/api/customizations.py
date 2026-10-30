from fastapi import APIRouter, HTTPException, Response, status

from app.db.customization import (
    add_guidance,
    get_guidance_entries,
    remove_guidance,
    update_guidance,
)
from app.schemas.customization import GuidanceEntry, GuidanceRequest

router = APIRouter(
    prefix="/customizations/guidance",
    tags=["customizations"],
)


@router.get("", response_model=list[GuidanceEntry])
def guidance_entries() -> list[dict[str, int | str]]:
    return get_guidance_entries()


@router.post("", response_model=GuidanceEntry, status_code=status.HTTP_201_CREATED)
def create_guidance(request: GuidanceRequest) -> GuidanceEntry:
    try:
        result = add_guidance(request.text)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if result == "That guidance is already saved.":
        raise HTTPException(status_code=409, detail=result)
    return _get_guidance(request.text)


@router.patch("/{guidance_id}", response_model=GuidanceEntry)
def edit_guidance(guidance_id: int, request: GuidanceRequest) -> GuidanceEntry:
    try:
        updated = update_guidance(guidance_id, request.text)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if not updated:
        raise HTTPException(status_code=404, detail="Guidance not found.")
    return _get_guidance(request.text)


@router.delete(
    "/{guidance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_guidance(guidance_id: int) -> Response:
    if not remove_guidance(guidance_id):
        raise HTTPException(status_code=404, detail="Guidance not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_guidance(text: str) -> GuidanceEntry:
    for entry in get_guidance_entries():
        if entry["text"] == text:
            return GuidanceEntry.model_validate(entry)
    raise RuntimeError("The saved guidance entry could not be retrieved.")
