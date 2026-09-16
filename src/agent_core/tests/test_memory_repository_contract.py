import asyncio
from datetime import UTC, datetime
from uuid import UUID

from agent_core.memory import (
    Memory,
    MemoryDomain,
    MemoryLifecycle,
    MemoryRepository,
    MemoryRevision,
    MemoryScope,
    MemoryScopeKind,
    MemorySource,
)

_MEMORY_ID = UUID(
    "12345678-1234-5678-1234-567812345678"
)


class ContractProbeMemoryRepository:
    """
    仅用于验证 MemoryRepository Protocol 的测试实现。

    不代表真实 Persistence 行为。
    """

    def __init__(self) -> None:
        self.created: list[
            tuple[Memory, MemoryRevision]
        ] = []

    async def create_memory(
        self,
        memory: Memory,
        initial_revision: MemoryRevision,
    ) -> None:
        self.created.append(
            (
                memory,
                initial_revision,
            )
        )

    async def get_memory(
        self,
        memory_id: UUID,
    ) -> Memory | None:
        return None

    async def list_memories(
        self,
        *,
        domain: MemoryDomain | None = None,
        scope: MemoryScope | None = None,
    ) -> tuple[Memory, ...]:
        return ()

    async def get_active_revision(
        self,
        memory_id: UUID,
    ) -> MemoryRevision | None:
        return None

    async def list_revisions(
        self,
        memory_id: UUID,
    ) -> tuple[MemoryRevision, ...]:
        return ()

    async def replace_active_revision(
        self,
        memory_id: UUID,
        new_revision: MemoryRevision,
    ) -> None:
        return None

    async def delete_memory(
        self,
        memory_id: UUID,
        tombstone_revision: MemoryRevision,
    ) -> None:
        return None


def _as_memory_repository(
    repository: MemoryRepository,
) -> MemoryRepository:
    """
    为 mypy 提供显式 Persistence Contract 边界。
    """

    return repository


def test_structural_repository_implements_async_contract() -> None:
    repository = ContractProbeMemoryRepository()

    contract = _as_memory_repository(
        repository,
    )

    scope = MemoryScope(
        kind=MemoryScopeKind.GLOBAL_USER,
    )

    memory = Memory(
        memory_id=_MEMORY_ID,
        domain=MemoryDomain.USER_PROFILE,
        scope=scope,
    )

    revision = MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=1,
        content="The user prefers C#.",
        source=MemorySource.USER_EXPLICIT,
        lifecycle=MemoryLifecycle.ACTIVE,
        recorded_at=datetime.now(UTC),
    )

    asyncio.run(
        contract.create_memory(
            memory,
            revision,
        )
    )

    assert repository.created == [
        (
            memory,
            revision,
        )
    ]
