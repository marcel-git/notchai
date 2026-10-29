import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import URL, Engine, create_engine, event
from sqlmodel import Session

BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
DATABASE_PATH = Path(
    os.getenv("CHAT_DATABASE_PATH", str(BACKEND_DIRECTORY / "data" / "chat.db"))
)
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


def create_database_engine(path: Path = DATABASE_PATH) -> Engine:
    engine = create_engine(
        URL.create("sqlite", database=str(path)),
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = create_database_engine()


@contextmanager
def session_scope() -> Iterator[Session]:
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise
