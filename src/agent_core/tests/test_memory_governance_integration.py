import asyncio
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from agent_core.memory.governance import (
    MemoryGovernanceService,
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
from agent_core.memory.persistence import (
    SQLiteMemoryRepository,
    create_memory_engine,
    create_memory_session_factory,
)
from agent_core.memory.persistence.orm import Base
from agent_core.tests.fakes import FixedClock

_MEMORY_ID = UUID(
    "12345678-1234-5678-1234-567812345678"
)

_INITIAL_RECORDED_AT = datetime(
    2026,
    9,
    16,
    10,
    0,
    tzinfo=UTC,
)

_EDIT_RECORDED_AT = datetime(
    2026,
    9,
    16,
    11,
    0,
    tzinfo=UTC,
)

_DELETE_RECORDED_AT = datetime(
    2026,
    9,
    16,
    12,
    0,
    tzinfo=UTC,
)


async def _create_schema(
    connection: AsyncConnection,
) -> None:
    await connection.run_sync(
        Base.metadata.create_all,
    )


async def _exercise_governance_with_sqlite(
    database_path: Path,
) -> None:
    engine = create_memory_engine(
        database_path
    )

    try:
        async with engine.begin() as connection:
            await _create_schema(
                connection
            )

        repository = SQLiteMemoryRepository(
            create_memory_session_factory(
                engine
            )
        )

        memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.USER_PROFILE,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        )

        initial_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="The user prefers Python.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=_INITIAL_RECORDED_AT,
        )

        await repository.create_memory(
            memory,
            initial_revision,
        )

        edit_service = MemoryGovernanceService(
            repository=repository,
            clock=FixedClock(
                _EDIT_RECORDED_AT
            ),
        )

        initial_entry = (
            await edit_service.inspect_memory(
                _MEMORY_ID
            )
        )

        assert initial_entry.memory == memory
        assert (
            initial_entry.latest_revision
            == initial_revision
        )

        edited_entry = (
            await edit_service.edit_memory(
                _MEMORY_ID,
                "The user prefers C#.",
            )
        )

        assert (
            edited_entry.latest_revision.revision_number
            == 2
        )
        assert (
            edited_entry.latest_revision.content
            == "The user prefers C#."
        )
        assert (
            edited_entry.latest_revision.source
            is MemorySource.USER_EDIT
        )
        assert (
            edited_entry.latest_revision.lifecycle
            is MemoryLifecycle.ACTIVE
        )
        assert (
            edited_entry.latest_revision.recorded_at
            == _EDIT_RECORDED_AT
        )

        history_after_edit = (
            await edit_service.get_history(
                _MEMORY_ID
            )
        )

        assert len(history_after_edit) == 2

        assert (
            history_after_edit[0].lifecycle
            is MemoryLifecycle.SUPERSEDED
        )

        assert (
            history_after_edit[1]
            == edited_entry.latest_revision
        )

        persisted_active_revision = (
            await repository.get_active_revision(
                _MEMORY_ID
            )
        )

        assert (
            persisted_active_revision
            == edited_entry.latest_revision
        )

        delete_service = MemoryGovernanceService(
            repository=repository,
            clock=FixedClock(
                _DELETE_RECORDED_AT
            ),
        )

        deleted_entry = (
            await delete_service.delete_memory(
                _MEMORY_ID
            )
        )

        assert (
            deleted_entry.latest_revision.revision_number
            == 3
        )
        assert (
            deleted_entry.latest_revision.lifecycle
            is MemoryLifecycle.DELETED
        )
        assert (
            deleted_entry.latest_revision.content
            is None
        )
        assert (
            deleted_entry.latest_revision.recorded_at
            == _DELETE_RECORDED_AT
        )

        inspected_deleted = (
            await delete_service.inspect_memory(
                _MEMORY_ID
            )
        )

        assert (
            inspected_deleted.latest_revision
            == deleted_entry.latest_revision
        )

        history_after_delete = (
            await delete_service.get_history(
                _MEMORY_ID
            )
        )

        assert history_after_delete == (
            deleted_entry.latest_revision,
        )

        assert (
            await repository.get_active_revision(
                _MEMORY_ID
            )
            is None
        )

    finally:
        await engine.dispose()


def test_governance_round_trips_through_sqlite(
    tmp_path: Path,
) -> None:
    asyncio.run(
        _exercise_governance_with_sqlite(
            tmp_path / "memory.db"
        )
    )
