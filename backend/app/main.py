from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path
import sys

from fastapi import FastAPI

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.characters import router as characters_router
from app.api.conversations import router as conversations_router
from app.api.personas import router as personas_router
from app.api.settings import router as settings_router
from app.db.migrations import upgrade_database
from app.db.session import session_scope
from app.repositories.conversation_repository import interrupt_incomplete_messages


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    upgrade_database()
    with session_scope() as session:
        interrupt_incomplete_messages(session)
    yield


app = FastAPI(title="Local Ollama Chat API", lifespan=lifespan)
app.include_router(conversations_router)
app.include_router(characters_router)
app.include_router(personas_router)
app.include_router(settings_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=True,
    )
