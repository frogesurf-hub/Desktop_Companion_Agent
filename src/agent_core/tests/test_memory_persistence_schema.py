import asyncio
from pathlib import Path

from sqlalchemy import inspect
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncConnection

from agent_core.memory.persistence.database import (
    create_memory_engine,
)
from agent_core.memory.persistence.orm import Base


async def _create_schema(
    connection: AsyncConnection,
) -> None:
    await connection.run_sync(
        Base.metadata.create_all,
    )


def _inspect_table_names(
    connection: Connection,
) -> set[str]:
    inspector = inspect(connection)

    if inspector is None:
        raise RuntimeError(
            "SQLAlchemy could not inspect the "
            "synchronous database connection"
        )

    return set(
        inspector.get_table_names()
    )


async def _read_table_names(
    connection: AsyncConnection,
) -> set[str]:
    return await connection.run_sync(
        _inspect_table_names,
    )


async def _exercise_schema(
    database_path: Path,
) -> set[str]:
    engine = create_memory_engine(
        database_path,
    )

    try:
        async with engine.begin() as connection:
            await _create_schema(connection)

        async with engine.connect() as connection:
            return await _read_table_names(
                connection,
            )
    finally:
        await engine.dispose()


def test_memory_schema_creates_expected_tables(
    tmp_path: Path,
) -> None:
    table_names = asyncio.run(
        _exercise_schema(
            tmp_path / "memory.db",
        )
    )

    assert table_names == {
        "memories",
        "memory_revisions",
    }


async def _read_foreign_keys_enabled(
    database_path: Path,
) -> int:
    engine = create_memory_engine(
        database_path,
    )

    try:
        async with engine.connect() as connection:
            result = await connection.exec_driver_sql(
                "PRAGMA foreign_keys"
            )

            return int(
                result.scalar_one()
            )
    finally:
        await engine.dispose()


def test_memory_database_enables_foreign_keys(
    tmp_path: Path,
) -> None:
    enabled = asyncio.run(
        _read_foreign_keys_enabled(
            tmp_path / "memory.db",
        )
    )

    assert enabled == 1
