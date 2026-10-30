import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Column,
    Engine,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.engine import URL

BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
CUSTOMIZATION_DATABASE_PATH = Path(
    os.getenv(
        "CUSTOMIZATION_DATABASE_PATH",
        str(BACKEND_DIRECTORY / "data" / "customization.db"),
    )
)
MAX_GUIDANCE_COUNT = 100
MAX_GUIDANCE_LENGTH = 300

metadata = MetaData()
guidance_table = Table(
    "guidance",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("text", Text, nullable=False, unique=True),
    Column("created_at", Text, nullable=False),
)


def create_customization_engine(path: Path = CUSTOMIZATION_DATABASE_PATH) -> Engine:
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        URL.create("sqlite", database=str(path)),
        connect_args={"check_same_thread": False},
    )


engine = create_customization_engine()


def initialize_customization_database() -> None:
    metadata.create_all(engine)


def list_guidance() -> list[str]:
    initialize_customization_database()
    with engine.connect() as connection:
        rows = connection.execute(
            select(guidance_table.c.text).order_by(guidance_table.c.id)
        )
        return list(rows.scalars())


def get_guidance_entries() -> list[dict[str, int | str]]:
    initialize_customization_database()
    with engine.connect() as connection:
        rows = connection.execute(
            select(guidance_table.c.id, guidance_table.c.text).order_by(
                guidance_table.c.id
            )
        )
        return [
            {"id": row.id, "text": row.text}
            for row in rows
        ]


def add_guidance(text: str) -> str:
    normalized = _normalize_guidance(text)

    initialize_customization_database()
    with engine.begin() as connection:
        if connection.execute(
            select(guidance_table.c.id).where(guidance_table.c.text == normalized)
        ).first():
            return "That guidance is already saved."
        count = connection.execute(
            select(func.count()).select_from(guidance_table)
        ).scalar_one()
        if count >= MAX_GUIDANCE_COUNT:
            raise ValueError(
                f"The guidance list is full ({MAX_GUIDANCE_COUNT} entries). "
                "Remove an entry before adding another."
            )
        connection.execute(
            guidance_table.insert().values(
                text=normalized,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        )
    return "Guidance saved for all conversations."


def update_guidance(guidance_id: int, text: str) -> bool:
    normalized = _normalize_guidance(text)
    initialize_customization_database()
    with engine.begin() as connection:
        existing = connection.execute(
            select(guidance_table.c.id).where(guidance_table.c.id == guidance_id)
        ).first()
        if existing is None:
            return False
        duplicate = connection.execute(
            select(guidance_table.c.id).where(
                guidance_table.c.text == normalized,
                guidance_table.c.id != guidance_id,
            )
        ).first()
        if duplicate:
            raise ValueError("That guidance is already saved.")
        result = connection.execute(
            guidance_table.update()
            .where(guidance_table.c.id == guidance_id)
            .values(text=normalized)
        )
    return result.rowcount > 0


def remove_guidance(guidance_id: int) -> bool:
    initialize_customization_database()
    with engine.begin() as connection:
        result = connection.execute(
            guidance_table.delete().where(guidance_table.c.id == guidance_id)
        )
    return result.rowcount > 0


def _normalize_guidance(text: str) -> str:
    normalized = text.strip()
    if not normalized:
        raise ValueError("Guidance must not be blank.")
    if len(normalized) > MAX_GUIDANCE_LENGTH:
        raise ValueError(
            f"Guidance must be {MAX_GUIDANCE_LENGTH} characters or fewer."
        )
    return normalized
