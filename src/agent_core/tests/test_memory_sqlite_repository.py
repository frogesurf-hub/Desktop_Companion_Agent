import asyncio
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
)

import agent_core.memory.persistence.sqlite_repository as sqlite_repository_module
from agent_core.memory import (
    Memory,
    MemoryDomain,
    MemoryIdentityKey,
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
from agent_core.memory.persistence.orm import (
    Base,
    MemoryRevisionRow,
)

_MEMORY_ID = UUID(
    "12345678-1234-5678-1234-567812345678"
)

_RELATIONSHIP_MEMORY_ID = UUID(
    "87654321-4321-8765-4321-876543218765"
)


async def _create_schema(
    connection: AsyncConnection,
) -> None:
    await connection.run_sync(
        Base.metadata.create_all,
    )


async def _build_repository(
    database_path: Path,
) -> tuple[
    AsyncEngine,
    SQLiteMemoryRepository,
]:
    engine = create_memory_engine(
        database_path
    )

    async with engine.begin() as connection:
        await _create_schema(connection)

    session_factory = (
        create_memory_session_factory(
            engine
        )
    )

    return (
        engine,
        SQLiteMemoryRepository(
            session_factory
        ),
    )


async def _exercise_round_trip(
    database_path: Path,
) -> None:
    engine, repository = (
        await _build_repository(
            database_path
        )
    )

    try:
        scope = MemoryScope(
            kind=MemoryScopeKind.GLOBAL_USER,
        )

        memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.USER_PROFILE,
            scope=scope,
            identity_key=MemoryIdentityKey(
                "user_profile.preference.programming_language"
            ),
        )

        recorded_at = datetime(
            2026,
            9,
            16,
            20,
            0,
            tzinfo=timezone(
                timedelta(hours=8),
            ),
        )

        occurred_at = datetime(
            2026,
            9,
            15,
            18,
            30,
            tzinfo=timezone(
                timedelta(hours=8),
            ),
        )

        revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="The user prefers C#.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=recorded_at,
            occurred_at=occurred_at,
        )

        await repository.create_memory(
            memory,
            revision,
        )

        loaded_memory = (
            await repository.get_memory(
                _MEMORY_ID
            )
        )

        loaded_revision = (
            await repository.get_active_revision(
                _MEMORY_ID
            )
        )

        revisions = (
            await repository.list_revisions(
                _MEMORY_ID
            )
        )

        assert loaded_memory == memory
        assert loaded_memory is not None
        assert loaded_memory.identity_key == (
            MemoryIdentityKey(
                "user_profile.preference.programming_language"
            )
        )
        assert loaded_revision is not None
        assert loaded_revision.content == (
            "The user prefers C#."
        )
        assert loaded_revision.recorded_at == (
            datetime(
                2026,
                9,
                16,
                12,
                0,
                tzinfo=UTC,
            )
        )
        assert loaded_revision.occurred_at == (
            datetime(
                2026,
                9,
                15,
                10,
                30,
                tzinfo=UTC,
            )
        )
        assert revisions == (
            loaded_revision,
        )
    finally:
        await engine.dispose()


async def _exercise_expire_active_revision(
    database_path: Path,
) -> None:
    engine, repository = (
        await _build_repository(
            database_path
        )
    )

    try:
        memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.WORKING_CONTEXT,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        )

        active_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="Temporary working context.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        await repository.create_memory(
            memory,
            active_revision,
        )

        await repository.expire_active_revision(
            _MEMORY_ID,
            active_revision.revision_number,
        )

        loaded_active = (
            await repository.get_active_revision(
                _MEMORY_ID
            )
        )

        revisions = (
            await repository.list_revisions(
                _MEMORY_ID
            )
        )

        assert loaded_active is None

        assert len(revisions) == 1

        expired_revision = revisions[0]

        assert (
            expired_revision.memory_id
            == active_revision.memory_id
        )
        assert (
            expired_revision.revision_number
            == active_revision.revision_number
        )
        assert (
            expired_revision.content
            == active_revision.content
        )
        assert (
            expired_revision.source
            is active_revision.source
        )
        assert (
            expired_revision.recorded_at
            == active_revision.recorded_at
        )
        assert (
            expired_revision.occurred_at
            == active_revision.occurred_at
        )
        assert (
            expired_revision.lifecycle
            is MemoryLifecycle.EXPIRED
        )

    finally:
        await engine.dispose()


async def _exercise_expire_without_active_revision(
    database_path: Path,
) -> None:
    engine, repository = (
        await _build_repository(
            database_path
        )
    )

    try:
        with pytest.raises(
            ValueError,
            match="Expected ACTIVE revision does not exist",
        ):
            await repository.expire_active_revision(
                _MEMORY_ID,
                1,
            )

    finally:
        await engine.dispose()


async def _exercise_rejects_stale_expiration(
    database_path: Path,
) -> None:
    engine, repository = (
        await _build_repository(
            database_path
        )
    )

    try:
        memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.WORKING_CONTEXT,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        )

        first_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="Old working context.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        second_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=2,
            content="New working context.",
            source=MemorySource.USER_EDIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        await repository.create_memory(
            memory,
            first_revision,
        )

        await repository.replace_active_revision(
            _MEMORY_ID,
            second_revision,
        )

        with pytest.raises(
            ValueError,
            match="Expected ACTIVE revision does not exist",
        ):
            await repository.expire_active_revision(
                _MEMORY_ID,
                1,
            )

        active_revision = (
            await repository.get_active_revision(
                _MEMORY_ID
            )
        )

        assert active_revision == second_revision

    finally:
        await engine.dispose()


def test_sqlite_repository_rejects_stale_expiration(
    tmp_path: Path,
) -> None:
    asyncio.run(
        _exercise_rejects_stale_expiration(
            tmp_path / "memory.db"
        )
    )


def test_sqlite_repository_rejects_expire_without_active_revision(
    tmp_path: Path,
) -> None:
    asyncio.run(
        _exercise_expire_without_active_revision(
            tmp_path / "memory.db"
        )
    )


def test_sqlite_repository_expires_active_revision(
    tmp_path: Path,
) -> None:
    asyncio.run(
        _exercise_expire_active_revision(
            tmp_path / "memory.db"
        )
    )


def test_sqlite_repository_round_trips_memory(
    tmp_path: Path,
) -> None:
    asyncio.run(
        _exercise_round_trip(
            tmp_path / "memory.db"
        )
    )


async def _exercise_list_filters(
    database_path: Path,
) -> None:
    engine, repository = (
        await _build_repository(
            database_path
        )
    )

    try:
        global_memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.USER_PROFILE,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        )

        global_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="The user prefers C#.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        relationship_scope = MemoryScope(
            kind=MemoryScopeKind.CHARACTER,
            character_id="aria",
        )

        relationship_memory = Memory(
            memory_id=_RELATIONSHIP_MEMORY_ID,
            domain=MemoryDomain.RELATIONSHIP,
            scope=relationship_scope,
        )

        relationship_revision = MemoryRevision(
            memory_id=_RELATIONSHIP_MEMORY_ID,
            revision_number=1,
            content="The user and Aria completed a task.",
            source=MemorySource.SYSTEM_OBSERVED,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        await repository.create_memory(
            global_memory,
            global_revision,
        )

        await repository.create_memory(
            relationship_memory,
            relationship_revision,
        )

        relationship_memories = (
            await repository.list_memories(
                domain=MemoryDomain.RELATIONSHIP,
            )
        )

        aria_memories = (
            await repository.list_memories(
                scope=relationship_scope,
            )
        )

        assert relationship_memories == (
            relationship_memory,
        )

        assert aria_memories == (
            relationship_memory,
        )
    finally:
        await engine.dispose()


def test_sqlite_repository_filters_memories(
    tmp_path: Path,
) -> None:
    asyncio.run(
        _exercise_list_filters(
            tmp_path / "memory.db"
        )
    )


async def _exercise_invalid_initial_revision(
    database_path: Path,
) -> None:
    engine, repository = (
        await _build_repository(
            database_path
        )
    )

    try:
        memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.USER_PROFILE,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        )

        wrong_revision = MemoryRevision(
            memory_id=_RELATIONSHIP_MEMORY_ID,
            revision_number=1,
            content="Wrong revision.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        with pytest.raises(
            ValueError,
            match="must match",
        ):
            await repository.create_memory(
                memory,
                wrong_revision,
            )

        assert (
            await repository.get_memory(
                _MEMORY_ID
            )
            is None
        )
    finally:
        await engine.dispose()


async def _exercise_replace_active_revision(
    database_path: Path,
) -> None:
    engine, repository = (
        await _build_repository(
            database_path
        )
    )

    try:
        memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.USER_PROFILE,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        )

        first_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="The user prefers Python.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        second_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=2,
            content="The user prefers C#.",
            source=MemorySource.USER_EDIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        await repository.create_memory(
            memory,
            first_revision,
        )

        await repository.replace_active_revision(
            _MEMORY_ID,
            second_revision,
        )

        active_revision = (
            await repository.get_active_revision(
                _MEMORY_ID
            )
        )

        revisions = (
            await repository.list_revisions(
                _MEMORY_ID
            )
        )

        assert active_revision == second_revision

        assert len(revisions) == 2

        assert revisions[0].revision_number == 1
        assert (
            revisions[0].lifecycle
            is MemoryLifecycle.SUPERSEDED
        )

        assert revisions[0].content == (
            "The user prefers Python."
        )

        assert revisions[1] == second_revision

    finally:
        await engine.dispose()


async def _exercise_rejects_revision_gap(
    database_path: Path,
) -> None:
    engine, repository = (
        await _build_repository(
            database_path
        )
    )

    try:
        memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.USER_PROFILE,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        )

        first_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="Original.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        invalid_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=3,
            content="Skipped revision 2.",
            source=MemorySource.USER_EDIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        await repository.create_memory(
            memory,
            first_revision,
        )

        with pytest.raises(
            ValueError,
            match="must be 2",
        ):
            await repository.replace_active_revision(
                _MEMORY_ID,
                invalid_revision,
            )

        active_revision = (
            await repository.get_active_revision(
                _MEMORY_ID
            )
        )

        assert active_revision == first_revision

    finally:
        await engine.dispose()


async def _exercise_delete_memory(
    database_path: Path,
) -> None:
    engine, repository = (
        await _build_repository(
            database_path
        )
    )

    try:
        memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.USER_PROFILE,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        )

        first_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="The user prefers Python.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        second_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=2,
            content="The user prefers C#.",
            source=MemorySource.USER_EDIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        tombstone = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=3,
            content=None,
            source=MemorySource.USER_EDIT,
            lifecycle=MemoryLifecycle.DELETED,
            recorded_at=datetime.now(UTC),
        )

        await repository.create_memory(
            memory,
            first_revision,
        )

        await repository.replace_active_revision(
            _MEMORY_ID,
            second_revision,
        )

        await repository.delete_memory(
            _MEMORY_ID,
            tombstone,
        )

        loaded_memory = (
            await repository.get_memory(
                _MEMORY_ID
            )
        )

        active_revision = (
            await repository.get_active_revision(
                _MEMORY_ID
            )
        )

        revisions = (
            await repository.list_revisions(
                _MEMORY_ID
            )
        )

        assert loaded_memory == memory
        assert active_revision is None

        assert revisions == (
            tombstone,
        )

        assert revisions[0].content is None
        assert (
            revisions[0].lifecycle
            is MemoryLifecycle.DELETED
        )

    finally:
        await engine.dispose()


async def _exercise_rejects_non_deleted_tombstone(
    database_path: Path,
) -> None:
    engine, repository = (
        await _build_repository(
            database_path
        )
    )

    try:
        memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.USER_PROFILE,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        )

        first_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="Original content.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        invalid_tombstone = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=2,
            content="This is not a tombstone.",
            source=MemorySource.USER_EDIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        await repository.create_memory(
            memory,
            first_revision,
        )

        with pytest.raises(
            ValueError,
            match="must be DELETED",
        ):
            await repository.delete_memory(
                _MEMORY_ID,
                invalid_tombstone,
            )

        active_revision = (
            await repository.get_active_revision(
                _MEMORY_ID
            )
        )

        assert active_revision == first_revision

    finally:
        await engine.dispose()


async def _exercise_replace_rollback(
    database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine, repository = (
        await _build_repository(
            database_path
        )
    )

    try:
        memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.USER_PROFILE,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        )

        first_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="Original content.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        second_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=2,
            content="New content.",
            source=MemorySource.USER_EDIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        await repository.create_memory(
            memory,
            first_revision,
        )

        def fail_revision_mapping(
            revision: MemoryRevision,
        ) -> object:
            raise RuntimeError(
                "Injected revision mapping failure"
            )

        monkeypatch.setattr(
            sqlite_repository_module,
            "revision_to_row",
            fail_revision_mapping,
        )

        with pytest.raises(
            RuntimeError,
            match="Injected revision mapping failure",
        ):
            await repository.replace_active_revision(
                _MEMORY_ID,
                second_revision,
            )

        active_revision = (
            await repository.get_active_revision(
                _MEMORY_ID
            )
        )

        revisions = (
            await repository.list_revisions(
                _MEMORY_ID
            )
        )

        assert active_revision == first_revision
        assert revisions == (
            first_revision,
        )

    finally:
        await engine.dispose()


async def _exercise_delete_rollback(
    database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine, repository = (
        await _build_repository(
            database_path
        )
    )

    try:
        memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.USER_PROFILE,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        )

        first_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="Original content.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        tombstone = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=2,
            content=None,
            source=MemorySource.USER_EDIT,
            lifecycle=MemoryLifecycle.DELETED,
            recorded_at=datetime.now(UTC),
        )

        await repository.create_memory(
            memory,
            first_revision,
        )

        def fail_revision_mapping(
            revision: MemoryRevision,
        ) -> object:
            raise RuntimeError(
                "Injected tombstone mapping failure"
            )

        monkeypatch.setattr(
            sqlite_repository_module,
            "revision_to_row",
            fail_revision_mapping,
        )

        with pytest.raises(
            RuntimeError,
            match="Injected tombstone mapping failure",
        ):
            await repository.delete_memory(
                _MEMORY_ID,
                tombstone,
            )

        active_revision = (
            await repository.get_active_revision(
                _MEMORY_ID
            )
        )

        revisions = (
            await repository.list_revisions(
                _MEMORY_ID
            )
        )

        assert active_revision == first_revision
        assert revisions == (
            first_revision,
        )

    finally:
        await engine.dispose()


async def _exercise_database_rejects_multiple_active_revisions(
    database_path: Path,
) -> None:
    engine, repository = (
        await _build_repository(
            database_path
        )
    )

    session_factory = (
        create_memory_session_factory(
            engine
        )
    )

    try:
        memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.USER_PROFILE,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        )

        first_revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="Original content.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )

        await repository.create_memory(
            memory,
            first_revision,
        )

        async with session_factory() as session:
            with pytest.raises(IntegrityError):
                async with session.begin():
                    session.add(
                        MemoryRevisionRow(
                            memory_id=str(_MEMORY_ID),
                            revision_number=2,
                            content="Illegal second active revision.",
                            source=MemorySource.USER_EDIT.value,
                            lifecycle=MemoryLifecycle.ACTIVE.value,
                            recorded_at=datetime.now(
                                UTC
                            ).isoformat(),
                            occurred_at=None,
                        )
                    )

                    await session.flush()

        active_revision = (
            await repository.get_active_revision(
                _MEMORY_ID
            )
        )

        revisions = (
            await repository.list_revisions(
                _MEMORY_ID
            )
        )

        assert active_revision == first_revision
        assert revisions == (
            first_revision,
        )

    finally:
        await engine.dispose()


def test_memory_database_rejects_multiple_active_revisions(
    tmp_path: Path,
) -> None:
    asyncio.run(
        _exercise_database_rejects_multiple_active_revisions(
            tmp_path / "memory.db"
        )
    )


def test_sqlite_repository_rolls_back_failed_delete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(
        _exercise_delete_rollback(
            tmp_path / "memory.db",
            monkeypatch,
        )
    )


def test_sqlite_repository_rolls_back_failed_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(
        _exercise_replace_rollback(
            tmp_path / "memory.db",
            monkeypatch,
        )
    )


def test_sqlite_repository_rejects_non_deleted_tombstone(
    tmp_path: Path,
) -> None:
    asyncio.run(
        _exercise_rejects_non_deleted_tombstone(
            tmp_path / "memory.db"
        )
    )


def test_sqlite_repository_deletes_content_and_keeps_tombstone(
    tmp_path: Path,
) -> None:
    asyncio.run(
        _exercise_delete_memory(
            tmp_path / "memory.db"
        )
    )


def test_sqlite_repository_rejects_revision_gap(
    tmp_path: Path,
) -> None:
    asyncio.run(
        _exercise_rejects_revision_gap(
            tmp_path / "memory.db"
        )
    )


def test_sqlite_repository_replaces_active_revision(
    tmp_path: Path,
) -> None:
    asyncio.run(
        _exercise_replace_active_revision(
            tmp_path / "memory.db"
        )
    )


def test_sqlite_repository_rejects_mismatched_initial_revision(
    tmp_path: Path,
) -> None:
    asyncio.run(
        _exercise_invalid_initial_revision(
            tmp_path / "memory.db"
        )
    )
