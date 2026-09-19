from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def _build_alembic_config(
    database_path: Path,
) -> Config:
    config = Config(
        "alembic.ini"
    )

    config.attributes[
        "configure_logger"
    ] = False

    database_url = (
        "sqlite:///"
        f"{database_path.resolve().as_posix()}"
    )

    config.set_main_option(
        "sqlalchemy.url",
        database_url,
    )

    return config


def test_initial_memory_migration_upgrade_and_downgrade(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path / "memory.db"
    )

    config = _build_alembic_config(
        database_path
    )

    command.upgrade(
        config,
        "head",
    )

    engine = create_engine(
        "sqlite:///"
        f"{database_path.resolve().as_posix()}"
    )

    try:
        inspector = inspect(engine)

        memory_columns = {
            column["name"]
            for column in inspector.get_columns(
                "memories"
            )
        }

        assert "identity_key" in memory_columns

        assert {
            "memories",
            "memory_revisions",
        }.issubset(
            set(
                inspector.get_table_names()
            )
        )

        revision_indexes = {
            index["name"]
            for index in inspector.get_indexes(
                "memory_revisions"
            )
        }

        memory_indexes = {
            index["name"]
            for index in inspector.get_indexes(
                "memories"
            )
        }

        assert (
            "uq_memory_global_identity"
            in memory_indexes
        )

        assert (
            "uq_memory_character_identity"
            in memory_indexes
        )

        assert (
            "uq_memory_active_revision"
            in revision_indexes
        )

    finally:
        engine.dispose()

    command.downgrade(
        config,
        "base",
    )

    engine = create_engine(
        "sqlite:///"
        f"{database_path.resolve().as_posix()}"
    )

    try:
        inspector = inspect(engine)

        remaining_tables = set(
            inspector.get_table_names()
        )

        assert "memories" not in remaining_tables
        assert (
            "memory_revisions"
            not in remaining_tables
        )

    finally:
        engine.dispose()


def test_identity_key_migration_preserves_legacy_memory(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path / "memory.db"
    )

    config = _build_alembic_config(
        database_path
    )

    command.upgrade(
        config,
        "0001_memory",
    )

    engine = create_engine(
        "sqlite:///"
        f"{database_path.resolve().as_posix()}"
    )

    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO memories (
                        memory_id,
                        domain,
                        scope_kind,
                        character_id
                    )
                    VALUES (
                        :memory_id,
                        :domain,
                        :scope_kind,
                        NULL
                    )
                    """
                ),
                {
                    "memory_id": (
                        "12345678-1234-5678-1234-567812345678"
                    ),
                    "domain": "user_profile",
                    "scope_kind": "global_user",
                },
            )
    finally:
        engine.dispose()

    command.upgrade(
        config,
        "head",
    )

    engine = create_engine(
        "sqlite:///"
        f"{database_path.resolve().as_posix()}"
    )

    try:
        inspector = inspect(engine)

        memory_columns = {
            column["name"]
            for column in inspector.get_columns(
                "memories"
            )
        }

        assert "identity_key" in memory_columns

        with engine.connect() as connection:
            identity_key = connection.execute(
                text(
                    """
                    SELECT identity_key
                    FROM memories
                    WHERE memory_id = :memory_id
                    """
                ),
                {
                    "memory_id": (
                        "12345678-1234-5678-1234-567812345678"
                    ),
                },
            ).scalar_one()

        assert identity_key is None

    finally:
        engine.dispose()
