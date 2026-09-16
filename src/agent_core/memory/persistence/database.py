from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _enable_sqlite_foreign_keys(
    dbapi_connection: Any,
    _connection_record: Any,
) -> None:
    cursor = dbapi_connection.cursor()

    try:
        cursor.execute(
            "PRAGMA foreign_keys=ON"
        )
    finally:
        cursor.close()


def build_sqlite_url(
    database_path: Path,
) -> str:
    """
    将本地 SQLite 文件路径转换为 SQLAlchemy async URL。
    """

    resolved_path = database_path.expanduser().resolve()

    return (
        "sqlite+aiosqlite:///"
        f"{resolved_path.as_posix()}"
    )


def create_memory_engine(
    database_path: Path,
) -> AsyncEngine:
    """
    创建 Memory SQLite async engine。

    调用者负责 engine.dispose()。
    """

    engine = create_async_engine(
        build_sqlite_url(database_path),
    )

    event.listen(
        engine.sync_engine,
        "connect",
        _enable_sqlite_foreign_keys,
    )

    return engine


def create_memory_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """
    创建 Memory Persistence 使用的 Session Factory。
    """

    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


@asynccontextmanager
async def open_memory_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """
    提供一个明确生命周期的 AsyncSession。

    Transaction 边界仍由具体 Repository 操作决定。
    """

    async with session_factory() as session:
        yield session
