from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


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
