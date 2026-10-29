from logging.config import fileConfig

from alembic import context
from alembic.operations import ops
from sqlmodel import SQLModel

from app.db.session import engine
from app.models import Character, ChatSettings, Conversation, Message, Persona

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def process_revision_directives(_context, _revision, directives) -> None:
    for directive in directives:
        _filter_primary_key_nullability(directive.upgrade_ops)


def _filter_primary_key_nullability(container) -> None:
    retained = []
    for operation in container.ops:
        if isinstance(operation, ops.ModifyTableOps):
            _filter_primary_key_nullability(operation)
        elif _is_legacy_message_foreign_key(operation):
            # The baseline adopts legacy message foreign keys without rebuilding them.
            continue
        elif isinstance(operation, ops.AlterColumnOp):
            table = target_metadata.tables.get(operation.table_name)
            column = table.c.get(operation.column_name) if table is not None else None
            if column is not None and column.primary_key:
                # SQLite reflection reports primary keys as nullable.
                operation.modify_nullable = None
                if not operation.has_changes():
                    continue
        retained.append(operation)
    container.ops = retained


def _is_legacy_message_foreign_key(operation) -> bool:
    if isinstance(operation, ops.CreateForeignKeyOp):
        return (
            operation.source_table == "messages"
            and operation.referent_table == "conversations"
            and operation.local_cols == ["conversation_id"]
            and operation.remote_cols == ["id"]
        )
    if isinstance(operation, ops.DropConstraintOp):
        replacement = operation._reverse
        return (
            operation.table_name == "messages"
            and operation.constraint_type == "foreignkey"
            and isinstance(replacement, ops.CreateForeignKeyOp)
            and replacement.source_table == "messages"
            and replacement.referent_table == "conversations"
            and replacement.local_cols == ["conversation_id"]
            and replacement.remote_cols == ["id"]
        )
    return False


def run_migrations_offline() -> None:
    context.configure(
        url=engine.url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        process_revision_directives=process_revision_directives,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is None:
        with engine.connect() as connection:
            _run_migrations(connection)
    else:
        _run_migrations(connection)


def _run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=True,
        process_revision_directives=process_revision_directives,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
