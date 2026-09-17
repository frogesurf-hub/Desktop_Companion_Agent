import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

from agent_core.memory.models import (
    Memory,
    MemoryDomain,
    MemoryLifecycle,
    MemoryRevision,
    MemoryScope,
    MemoryScopeKind,
    MemorySource,
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
    0,
    0,
    tzinfo=UTC,
)


class FixedClock(Clock):
    def now(self) -> datetime:
        return _NOW


class RetentionProbeRepository:
    def __init__(
        self,
        *,
        memories: tuple[Memory, ...],
        active_revisions: dict[
            UUID,
            MemoryRevision | None,
        ],
    ) -> None:
        self._memories = memories
        self._active_revisions = active_revisions

        self.expire_calls: list[
            tuple[UUID, int]
        ] = []

    async def list_memories(
        self,
        *,
        domain: MemoryDomain | None = None,
        scope: MemoryScope | None = None,
    ) -> tuple[Memory, ...]:
        memories = self._memories

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
        return self._active_revisions.get(
            memory_id
        )

    async def expire_active_revision(
        self,
        memory_id: UUID,
        expected_revision_number: int,
    ) -> None:
        self.expire_calls.append(
            (
                memory_id,
                expected_revision_number,
            )
        )

    async def create_memory(
        self,
        memory: Memory,
        initial_revision: MemoryRevision,
    ) -> None:
        raise AssertionError(
            "Retention must not create Memory"
        )

    async def get_memory(
        self,
        memory_id: UUID,
    ) -> Memory | None:
        raise AssertionError(
            "Retention must not inspect Memory directly"
        )

    async def list_revisions(
        self,
        memory_id: UUID,
    ) -> tuple[MemoryRevision, ...]:
        raise AssertionError(
            "Retention must not read history"
        )

    async def replace_active_revision(
        self,
        memory_id: UUID,
        new_revision: MemoryRevision,
    ) -> None:
        raise AssertionError(
            "Retention must not edit Memory"
        )

    async def delete_memory(
        self,
        memory_id: UUID,
        tombstone_revision: MemoryRevision,
    ) -> None:
        raise AssertionError(
            "Retention must not delete Memory"
        )


def _working_memory() -> Memory:
    return Memory(
        memory_id=_MEMORY_ID,
        domain=MemoryDomain.WORKING_CONTEXT,
        scope=MemoryScope(
            kind=MemoryScopeKind.GLOBAL_USER,
        ),
    )


def _revision(
    *,
    recorded_at: datetime,
) -> MemoryRevision:
    return MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=1,
        content="Temporary working context.",
        source=MemorySource.USER_EXPLICIT,
        lifecycle=MemoryLifecycle.ACTIVE,
        recorded_at=recorded_at,
    )


def test_retention_service_expires_due_working_context() -> None:
    memory = _working_memory()

    revision = _revision(
        recorded_at=(
            _NOW - timedelta(days=7)
        ),
    )

    repository = RetentionProbeRepository(
        memories=(memory,),
        active_revisions={
            _MEMORY_ID: revision,
        },
    )

    service = MemoryRetentionService(
        repository=repository,
        policy=MemoryRetentionPolicy(
            working_context_retention_days=7,
        ),
        clock=FixedClock(),
    )

    result = asyncio.run(
        service.apply_due_expirations()
    )

    assert result.checked_count == 1
    assert result.expired_memory_ids == (
        _MEMORY_ID,
    )

    assert repository.expire_calls == [
        (
            _MEMORY_ID,
            revision.revision_number,
        )
    ]


def test_retention_service_keeps_fresh_working_context() -> None:
    memory = _working_memory()

    revision = _revision(
        recorded_at=(
            _NOW - timedelta(days=6)
        ),
    )

    repository = RetentionProbeRepository(
        memories=(memory,),
        active_revisions={
            _MEMORY_ID: revision,
        },
    )

    service = MemoryRetentionService(
        repository=repository,
        policy=MemoryRetentionPolicy(
            working_context_retention_days=7,
        ),
        clock=FixedClock(),
    )

    result = asyncio.run(
        service.apply_due_expirations()
    )

    assert result.checked_count == 1
    assert result.expired_memory_ids == ()
    assert repository.expire_calls == []


def test_retention_service_skips_memory_without_active_revision() -> None:
    memory = _working_memory()

    repository = RetentionProbeRepository(
        memories=(memory,),
        active_revisions={
            _MEMORY_ID: None,
        },
    )

    service = MemoryRetentionService(
        repository=repository,
        policy=MemoryRetentionPolicy(
            working_context_retention_days=7,
        ),
        clock=FixedClock(),
    )

    result = asyncio.run(
        service.apply_due_expirations()
    )

    assert result.checked_count == 0
    assert result.expired_memory_ids == ()
    assert repository.expire_calls == []


def test_retention_service_only_scans_working_context() -> None:
    memory = Memory(
        memory_id=_MEMORY_ID,
        domain=MemoryDomain.USER_PROFILE,
        scope=MemoryScope(
            kind=MemoryScopeKind.GLOBAL_USER,
        ),
    )

    revision = _revision(
        recorded_at=(
            _NOW - timedelta(days=365)
        ),
    )

    repository = RetentionProbeRepository(
        memories=(memory,),
        active_revisions={
            _MEMORY_ID: revision,
        },
    )

    service = MemoryRetentionService(
        repository=repository,
        policy=MemoryRetentionPolicy(
            working_context_retention_days=7,
        ),
        clock=FixedClock(),
    )

    result = asyncio.run(
        service.apply_due_expirations()
    )

    assert result.checked_count == 0
    assert result.expired_memory_ids == ()
    assert repository.expire_calls == []
