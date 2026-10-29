from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine

from app.db import session as database

ALEMBIC_CONFIG = Path(__file__).resolve().parents[2] / "alembic.ini"


def upgrade_database(target_engine: Engine | None = None) -> None:
    selected_engine = target_engine or database.engine
    config = Config(str(ALEMBIC_CONFIG))
    with selected_engine.connect() as connection:
        sqlite = connection.dialect.name == "sqlite"
        if sqlite:
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            connection.commit()
        try:
            with connection.begin():
                config.attributes["connection"] = connection
                command.upgrade(config, "head")
        except BaseException:
            if sqlite:
                connection.exec_driver_sql("PRAGMA foreign_keys=ON")
                connection.commit()
            raise
        if sqlite:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.commit()
            violations = connection.exec_driver_sql("PRAGMA foreign_key_check").all()
            if violations:
                raise RuntimeError(f"SQLite foreign-key violations after migration: {violations}")
