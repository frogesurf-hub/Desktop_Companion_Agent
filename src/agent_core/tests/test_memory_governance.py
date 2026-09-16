import asyncio
from datetime import UTC, datetime
from uuid import UUID

import pytest

from agent_core.memory.governance import (
    MemoryDeletedError,
    MemoryGovernanceService,
    MemoryNotFoundError,
    MemoryStateError,
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
from agent_core.tests.fakes import FixedClock

_MEMORY_ID = UUID(
    "12345678-1234-5678-1234-567812345678"
)

_RELATIONSHIP_MEMORY_ID = UUID(
    "87654321-4321-8765-4321-876543218765"
)

_MISSING_MEMORY_ID = UUID(
    "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
)

_RECORDED_AT = datetime(
    2026,
    9,
    16,
    12,
    0,
    tzinfo=UTC,
)

_EDIT_RECORDED_AT = datetime(
    2026,
    9,
    16,
    13,
    0,
    tzinfo=UTC,
)


class ReadProbeMemoryRepository:
    """
    Governance 单元测试使用的内存 Repository Probe。

    不代表真实 Persistence 实现。
    """

    def __init__(
        self,
        *,
        memories: tuple[Memory, ...],
        revisions: dict[
            UUID,
            tuple[MemoryRevision, ...],
        ],
    ) -> None:
        self._memories = {
            memory.memory_id: memory
            for memory in memories
        }
        self._revisions = revisions

    async def create_memory(
        self,
        memory: Memory,
        initial_revision: MemoryRevision,
    ) -> None:
        raise AssertionError(
            "Read Governance must not create Memory"
        )

    async def get_memory(
        self,
        memory_id: UUID,
    ) -> Memory | None:
        return self._memories.get(
            memory_id
        )

    async def list_memories(
        self,
        *,
        domain: MemoryDomain | None = None,
        scope: MemoryScope | None = None,
    ) -> tuple[Memory, ...]:
        memories = tuple(
            self._memories.values()
        )

        if domain is not None:
            memories = tuple(
                memory
                for memory in memories
                if memory.domain is domain
            )

        if scope is not None:
            memories = tuple(
                memory
                for memory in memories
                if memory.scope == scope
            )

        return memories

    async def get_active_revision(
        self,
        memory_id: UUID,
    ) -> MemoryRevision | None:
        raise AssertionError(
            "Read Governance must use revision history"
        )

    async def list_revisions(
        self,
        memory_id: UUID,
    ) -> tuple[MemoryRevision, ...]:
        return self._revisions.get(
            memory_id,
            (),
        )

    async def replace_active_revision(
        self,
        memory_id: UUID,
        new_revision: MemoryRevision,
    ) -> None:
        raise AssertionError(
            "Read Governance must not edit Memory"
        )

    async def delete_memory(
        self,
        memory_id: UUID,
        tombstone_revision: MemoryRevision,
    ) -> None:
        raise AssertionError(
            "Read Governance must not delete Memory"
        )


class MutationProbeMemoryRepository(
    ReadProbeMemoryRepository
):
    """
    Governance Mutation 测试使用的 Repository Probe。
    """

    def __init__(
        self,
        *,
        memories: tuple[Memory, ...],
        revisions: dict[
            UUID,
            tuple[MemoryRevision, ...],
        ],
    ) -> None:
        super().__init__(
            memories=memories,
            revisions=revisions,
        )

        self.replace_calls: list[
            tuple[
                UUID,
                MemoryRevision,
            ]
        ] = []

        self.delete_calls: list[
            tuple[
                UUID,
                MemoryRevision,
            ]
        ] = []

    async def delete_memory(
        self,
        memory_id: UUID,
        tombstone_revision: MemoryRevision,
    ) -> None:
        self.delete_calls.append(
            (
                memory_id,
                tombstone_revision,
            )
        )

    async def replace_active_revision(
        self,
        memory_id: UUID,
        new_revision: MemoryRevision,
    ) -> None:
        self.replace_calls.append(
            (
                memory_id,
                new_revision,
            )
        )


class FailingMutationMemoryRepository(
    MutationProbeMemoryRepository
):
    """
    模拟 Persistence 写入失败。
    """

    async def replace_active_revision(
        self,
        memory_id: UUID,
        new_revision: MemoryRevision,
    ) -> None:
        self.replace_calls.append(
            (
                memory_id,
                new_revision,
            )
        )

        raise RuntimeError(
            "simulated replace failure"
        )

    async def delete_memory(
        self,
        memory_id: UUID,
        tombstone_revision: MemoryRevision,
    ) -> None:
        self.delete_calls.append(
            (
                memory_id,
                tombstone_revision,
            )
        )

        raise RuntimeError(
            "simulated delete failure"
        )


def test_edit_memory_propagates_repository_failure() -> None:
    memory = _global_memory()

    original_revision = MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=1,
        content="The user prefers Python.",
        source=MemorySource.USER_EXPLICIT,
        lifecycle=MemoryLifecycle.ACTIVE,
        recorded_at=_RECORDED_AT,
    )

    repository = FailingMutationMemoryRepository(
        memories=(memory,),
        revisions={
            _MEMORY_ID: (
                original_revision,
            ),
        },
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _EDIT_RECORDED_AT
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="simulated replace failure",
    ):
        asyncio.run(
            service.edit_memory(
                _MEMORY_ID,
                "The user prefers C#.",
            )
        )

    assert len(
        repository.replace_calls
    ) == 1

    assert repository.delete_calls == []


def test_delete_memory_propagates_repository_failure() -> None:
    memory = _global_memory()

    original_revision = MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=2,
        content="The user prefers C#.",
        source=MemorySource.USER_EDIT,
        lifecycle=MemoryLifecycle.ACTIVE,
        recorded_at=_RECORDED_AT,
    )

    repository = FailingMutationMemoryRepository(
        memories=(memory,),
        revisions={
            _MEMORY_ID: (
                original_revision,
            ),
        },
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _EDIT_RECORDED_AT
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="simulated delete failure",
    ):
        asyncio.run(
            service.delete_memory(
                _MEMORY_ID
            )
        )

    assert len(
        repository.delete_calls
    ) == 1

    assert repository.replace_calls == []


def test_edit_expired_memory_is_rejected() -> None:
    memory = _global_memory()

    expired_revision = _revision(
        memory_id=_MEMORY_ID,
        revision_number=2,
        content="Expired content.",
        lifecycle=MemoryLifecycle.EXPIRED,
    )

    repository = MutationProbeMemoryRepository(
        memories=(memory,),
        revisions={
            _MEMORY_ID: (
                expired_revision,
            ),
        },
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _EDIT_RECORDED_AT
        ),
    )

    with pytest.raises(
        MemoryStateError,
        match="is not ACTIVE",
    ):
        asyncio.run(
            service.edit_memory(
                _MEMORY_ID,
                "New content.",
            )
        )

    assert repository.replace_calls == []
    assert repository.delete_calls == []


def test_delete_expired_memory_is_rejected() -> None:
    memory = _global_memory()

    expired_revision = _revision(
        memory_id=_MEMORY_ID,
        revision_number=2,
        content="Expired content.",
        lifecycle=MemoryLifecycle.EXPIRED,
    )

    repository = MutationProbeMemoryRepository(
        memories=(memory,),
        revisions={
            _MEMORY_ID: (
                expired_revision,
            ),
        },
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _EDIT_RECORDED_AT
        ),
    )

    with pytest.raises(
        MemoryStateError,
        match="is not ACTIVE",
    ):
        asyncio.run(
            service.delete_memory(
                _MEMORY_ID
            )
        )

    assert repository.replace_calls == []
    assert repository.delete_calls == []


def test_delete_memory_builds_tombstone() -> None:
    memory = _global_memory()

    original_revision = MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=2,
        content="The user prefers C#.",
        source=MemorySource.USER_EDIT,
        lifecycle=MemoryLifecycle.ACTIVE,
        recorded_at=_RECORDED_AT,
        occurred_at=_RECORDED_AT,
    )

    repository = MutationProbeMemoryRepository(
        memories=(memory,),
        revisions={
            _MEMORY_ID: (
                original_revision,
            ),
        },
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _EDIT_RECORDED_AT
        ),
    )

    entry = asyncio.run(
        service.delete_memory(
            _MEMORY_ID
        )
    )

    assert len(
        repository.delete_calls
    ) == 1

    deleted_memory_id, tombstone = (
        repository.delete_calls[0]
    )

    assert deleted_memory_id == _MEMORY_ID
    assert tombstone.revision_number == 3
    assert tombstone.content is None
    assert (
        tombstone.source
        is MemorySource.USER_EDIT
    )
    assert (
        tombstone.lifecycle
        is MemoryLifecycle.DELETED
    )
    assert (
        tombstone.recorded_at
        == _EDIT_RECORDED_AT
    )
    assert tombstone.occurred_at is None

    assert entry.memory == memory
    assert (
        entry.latest_revision
        == tombstone
    )

    assert repository.replace_calls == []


def test_delete_missing_memory_is_rejected() -> None:
    repository = MutationProbeMemoryRepository(
        memories=(),
        revisions={},
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _EDIT_RECORDED_AT
        ),
    )

    with pytest.raises(
        MemoryNotFoundError,
        match="does not exist",
    ):
        asyncio.run(
            service.delete_memory(
                _MISSING_MEMORY_ID
            )
        )

    assert repository.delete_calls == []


def test_delete_deleted_memory_is_rejected() -> None:
    memory = _global_memory()

    tombstone = _revision(
        memory_id=_MEMORY_ID,
        revision_number=3,
        content=None,
        lifecycle=MemoryLifecycle.DELETED,
    )

    repository = MutationProbeMemoryRepository(
        memories=(memory,),
        revisions={
            _MEMORY_ID: (
                tombstone,
            ),
        },
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _EDIT_RECORDED_AT
        ),
    )

    with pytest.raises(
        MemoryDeletedError,
        match="is deleted",
    ):
        asyncio.run(
            service.delete_memory(
                _MEMORY_ID
            )
        )

    assert repository.delete_calls == []


def test_edit_missing_memory_is_rejected() -> None:
    repository = MutationProbeMemoryRepository(
        memories=(),
        revisions={},
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _EDIT_RECORDED_AT
        ),
    )

    with pytest.raises(
        MemoryNotFoundError,
        match="does not exist",
    ):
        asyncio.run(
            service.edit_memory(
                _MISSING_MEMORY_ID,
                "New content.",
            )
        )

    assert repository.replace_calls == []


def test_edit_deleted_memory_is_rejected() -> None:
    memory = _global_memory()

    tombstone = _revision(
        memory_id=_MEMORY_ID,
        revision_number=2,
        content=None,
        lifecycle=MemoryLifecycle.DELETED,
    )

    repository = MutationProbeMemoryRepository(
        memories=(memory,),
        revisions={
            _MEMORY_ID: (
                tombstone,
            ),
        },
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _EDIT_RECORDED_AT
        ),
    )

    with pytest.raises(
        MemoryDeletedError,
        match="is deleted",
    ):
        asyncio.run(
            service.edit_memory(
                _MEMORY_ID,
                "New content.",
            )
        )

    assert repository.replace_calls == []


def test_edit_memory_builds_user_edit_revision() -> None:
    memory = _global_memory()

    original_revision = MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=1,
        content="The user prefers Python.",
        source=MemorySource.USER_EXPLICIT,
        lifecycle=MemoryLifecycle.ACTIVE,
        recorded_at=_RECORDED_AT,
        occurred_at=_RECORDED_AT,
    )

    repository = MutationProbeMemoryRepository(
        memories=(memory,),
        revisions={
            _MEMORY_ID: (
                original_revision,
            ),
        },
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _EDIT_RECORDED_AT
        ),
    )

    entry = asyncio.run(
        service.edit_memory(
            _MEMORY_ID,
            "The user prefers C#.",
        )
    )

    assert len(
        repository.replace_calls
    ) == 1

    replaced_memory_id, new_revision = (
        repository.replace_calls[0]
    )

    assert replaced_memory_id == _MEMORY_ID
    assert new_revision.revision_number == 2
    assert (
        new_revision.content
        == "The user prefers C#."
    )
    assert (
        new_revision.source
        is MemorySource.USER_EDIT
    )
    assert (
        new_revision.lifecycle
        is MemoryLifecycle.ACTIVE
    )
    assert (
        new_revision.recorded_at
        == _EDIT_RECORDED_AT
    )

    assert (
        new_revision.occurred_at
        == original_revision.occurred_at
    )

    assert entry.memory == memory
    assert (
        entry.latest_revision
        == new_revision
    )


def test_list_memories_applies_scope_filter() -> None:
    global_memory = _global_memory()
    relationship_memory = _relationship_memory()

    global_revision = _revision(
        memory_id=_MEMORY_ID,
        revision_number=1,
        content="The user prefers C#.",
        lifecycle=MemoryLifecycle.ACTIVE,
    )

    relationship_revision = _revision(
        memory_id=_RELATIONSHIP_MEMORY_ID,
        revision_number=1,
        content="The user and Aria completed a task.",
        lifecycle=MemoryLifecycle.ACTIVE,
    )

    relationship_scope = relationship_memory.scope

    repository = ReadProbeMemoryRepository(
        memories=(
            global_memory,
            relationship_memory,
        ),
        revisions={
            _MEMORY_ID: (
                global_revision,
            ),
            _RELATIONSHIP_MEMORY_ID: (
                relationship_revision,
            ),
        },
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _RECORDED_AT
        ),
    )

    entries = asyncio.run(
        service.list_memories(
            scope=relationship_scope,
        )
    )

    assert len(entries) == 1
    assert entries[0].memory == relationship_memory
    assert (
        entries[0].latest_revision
        == relationship_revision
    )


def _global_memory() -> Memory:
    return Memory(
        memory_id=_MEMORY_ID,
        domain=MemoryDomain.USER_PROFILE,
        scope=MemoryScope(
            kind=MemoryScopeKind.GLOBAL_USER,
        ),
    )


def _relationship_memory() -> Memory:
    return Memory(
        memory_id=_RELATIONSHIP_MEMORY_ID,
        domain=MemoryDomain.RELATIONSHIP,
        scope=MemoryScope(
            kind=MemoryScopeKind.CHARACTER,
            character_id="aria",
        ),
    )


def _revision(
    *,
    memory_id: UUID,
    revision_number: int,
    content: str | None,
    lifecycle: MemoryLifecycle,
) -> MemoryRevision:
    return MemoryRevision(
        memory_id=memory_id,
        revision_number=revision_number,
        content=content,
        source=MemorySource.USER_EDIT,
        lifecycle=lifecycle,
        recorded_at=_RECORDED_AT,
    )


def test_inspect_memory_returns_latest_revision() -> None:
    memory = _global_memory()

    first_revision = _revision(
        memory_id=_MEMORY_ID,
        revision_number=1,
        content="The user prefers Python.",
        lifecycle=MemoryLifecycle.SUPERSEDED,
    )

    second_revision = _revision(
        memory_id=_MEMORY_ID,
        revision_number=2,
        content="The user prefers C#.",
        lifecycle=MemoryLifecycle.ACTIVE,
    )

    repository = ReadProbeMemoryRepository(
        memories=(memory,),
        revisions={
            _MEMORY_ID: (
                first_revision,
                second_revision,
            ),
        },
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _RECORDED_AT
        ),
    )

    entry = asyncio.run(
        service.inspect_memory(
            _MEMORY_ID
        )
    )

    assert entry.memory == memory
    assert entry.latest_revision == second_revision


def test_inspect_deleted_memory_returns_tombstone() -> None:
    memory = _global_memory()

    tombstone = _revision(
        memory_id=_MEMORY_ID,
        revision_number=3,
        content=None,
        lifecycle=MemoryLifecycle.DELETED,
    )

    repository = ReadProbeMemoryRepository(
        memories=(memory,),
        revisions={
            _MEMORY_ID: (
                tombstone,
            ),
        },
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _RECORDED_AT
        ),
    )

    entry = asyncio.run(
        service.inspect_memory(
            _MEMORY_ID
        )
    )

    assert (
        entry.latest_revision.lifecycle
        is MemoryLifecycle.DELETED
    )
    assert entry.latest_revision.content is None


def test_list_memories_applies_governance_filters() -> None:
    global_memory = _global_memory()
    relationship_memory = _relationship_memory()

    global_revision = _revision(
        memory_id=_MEMORY_ID,
        revision_number=1,
        content="The user prefers C#.",
        lifecycle=MemoryLifecycle.ACTIVE,
    )

    relationship_revision = _revision(
        memory_id=_RELATIONSHIP_MEMORY_ID,
        revision_number=1,
        content="The user and Aria completed a task.",
        lifecycle=MemoryLifecycle.ACTIVE,
    )

    repository = ReadProbeMemoryRepository(
        memories=(
            global_memory,
            relationship_memory,
        ),
        revisions={
            _MEMORY_ID: (
                global_revision,
            ),
            _RELATIONSHIP_MEMORY_ID: (
                relationship_revision,
            ),
        },
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _RECORDED_AT
        )
    )

    entries = asyncio.run(
        service.list_memories(
            domain=MemoryDomain.RELATIONSHIP,
        )
    )

    assert len(entries) == 1
    assert entries[0].memory == relationship_memory
    assert (
        entries[0].latest_revision
        == relationship_revision
    )


def test_get_history_preserves_revision_order() -> None:
    memory = _global_memory()

    first_revision = _revision(
        memory_id=_MEMORY_ID,
        revision_number=1,
        content="The user prefers Python.",
        lifecycle=MemoryLifecycle.SUPERSEDED,
    )

    second_revision = _revision(
        memory_id=_MEMORY_ID,
        revision_number=2,
        content="The user prefers C#.",
        lifecycle=MemoryLifecycle.ACTIVE,
    )

    repository = ReadProbeMemoryRepository(
        memories=(memory,),
        revisions={
            _MEMORY_ID: (
                first_revision,
                second_revision,
            ),
        },
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _RECORDED_AT
        ),
    )

    history = asyncio.run(
        service.get_history(
            _MEMORY_ID
        )
    )

    assert history == (
        first_revision,
        second_revision,
    )


def test_inspect_missing_memory_raises() -> None:
    repository = ReadProbeMemoryRepository(
        memories=(),
        revisions={},
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _RECORDED_AT
        ),
    )
    with pytest.raises(
        MemoryNotFoundError,
        match="does not exist",
    ):
        asyncio.run(
            service.inspect_memory(
                _MISSING_MEMORY_ID
            )
        )


def test_revisionless_memory_is_invalid_governance_state() -> None:
    memory = _global_memory()

    repository = ReadProbeMemoryRepository(
        memories=(memory,),
        revisions={},
    )

    service = MemoryGovernanceService(
        repository=repository,
        clock=FixedClock(
            _RECORDED_AT
        ),
    )

    with pytest.raises(
        MemoryStateError,
        match="has no revisions",
    ):
        asyncio.run(
            service.inspect_memory(
                _MEMORY_ID
            )
        )
