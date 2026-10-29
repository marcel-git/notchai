import json
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import APIRouter, HTTPException

from app.db.session import session_scope
from app.repositories.settings_repository import (
    get_generation_settings,
    update_generation_settings,
)
from app.schemas.roleplay import GenerationSettingsRead, GenerationSettingsUpdate
from app.services.model_service import OLLAMA_BASE_URL

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=GenerationSettingsRead)
def settings() -> GenerationSettingsRead:
    with session_scope() as session:
        return GenerationSettingsRead.model_validate(get_generation_settings(session))


@router.put("", response_model=GenerationSettingsRead)
def save_settings(request: GenerationSettingsUpdate) -> GenerationSettingsRead:
    with session_scope() as session:
        values = update_generation_settings(session, request.model_dump())
        return GenerationSettingsRead.model_validate(values)


@router.get("/models", response_model=list[str])
def available_models() -> list[str]:
    try:
        with urlopen(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=5) as response:
            result = json.load(response)
    except (URLError, TimeoutError) as error:
        raise HTTPException(
            status_code=503,
            detail="Ollama is unavailable. Check that it is running, then reload models.",
        ) from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise HTTPException(
            status_code=502,
            detail="Ollama returned an invalid model list.",
        ) from error

    if not isinstance(result, dict) or not isinstance(result.get("models"), list):
        raise HTTPException(status_code=502, detail="Ollama returned an invalid model list.")
    names = [
        item["name"]
        for item in result["models"]
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    ]
    return sorted(names)
