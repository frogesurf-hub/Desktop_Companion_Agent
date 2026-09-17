import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from agent_core.memory.models import (
    Memory,
    MemoryDomain,
    MemoryLifecycle,
    MemoryRevision,
    MemoryScope,
    MemoryScopeKind,
    MemorySource,
)
from agent_core.memory.persistence.orm import Base
from agent_core.memory.persistence.sqlite_repository import (
    SQLiteMemoryRepository,
)
from agent_core.memory.retention import (
    MemoryRetentionPolicy,
)
from agent_core.memory.retention_service import (
    MemoryRetentionService,
)
from agent_core.temporal import Clock

_MEMORY_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)

_NOW = datetime(
    2026,
    9,
    17,
    12,
    0,
    tzinfo=UTC,
)


class FixedClock(Clock):
    def now(self) -> datetime:
        return _NOW


async def _build_repository(
    database_path: Path,
) -> tuple[
    AsyncEngine,
    SQLiteMemoryRepository,
]:
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{database_path}"
    )

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    return (
        engine,
        SQLiteMemoryRepository(
            session_factory
        ),
    )


async def _exercise_retention_integration(
    database_path: Path,
) -> None:
    engine, repository = await _build_repository(
        database_path
    )

    try:
        memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.WORKING_CONTEXT,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        )

        revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="Expired working context.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=(
                _NOW - timedelta(days=7)
            ),
        )

        await repository.create_memory(
            memory,
            revision,
        )

        service = MemoryRetentionService(
            repository=repository,
            policy=MemoryRetentionPolicy(
                working_context_retention_days=7,
            ),
            clock=FixedClock(),
        )

        result = await service.apply_due_expirations()

        assert result.checked_count == 1
        assert result.expired_memory_ids == (
            _MEMORY_ID,
        )

        assert (
            await repository.get_active_revision(
                _MEMORY_ID
            )
            is None
        )

        revisions = (
            await repository.list_revisions(
                _MEMORY_ID
            )
        )

        assert len(revisions) == 1
        assert (
            revisions[0].lifecycle
            is MemoryLifecycle.EXPIRED
        )
        assert revisions[0].content == (
            "Expired working context."
        )

    finally:
        await engine.dispose()


def test_retention_service_expires_sqlite_memory(
    tmp_path: Path,
) -> None:
    asyncio.run(
        _exercise_retention_integration(
            tmp_path / "memory.db"
        )
    )
