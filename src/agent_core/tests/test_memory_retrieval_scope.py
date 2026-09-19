import asyncio
from datetime import UTC, datetime
from uuid import UUID

from agent_core.memory import (
    Memory,
    MemoryDomain,
    MemoryLifecycle,
    MemoryRetrievalLimits,
    MemoryRetrievalPolicy,
    MemoryRetrievalService,
    MemoryRevision,
    MemoryScope,
    MemoryScopeKind,
    MemorySource,
)

_PROFILE_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)

_ARIA_RELATIONSHIP_ID = UUID(
    "22222222-2222-2222-2222-222222222222"
)

_OTHER_RELATIONSHIP_ID = UUID(
    "33333333-3333-3333-3333-333333333333"
)

_RECORDED_AT = datetime(
    2026,
    9,
    19,
    12,
    0,
    tzinfo=UTC,
)


class RetrievalProbeMemoryRepository:
    def __init__(
        self,
        *,
        memories: tuple[Memory, ...],
        revisions: dict[
            UUID,
            MemoryRevision,
        ],
    ) -> None:
        self._memories = memories
        self._revisions = revisions

    async def create_memory(
        self,
        memory: Memory,
        initial_revision: MemoryRevision,
    ) -> None:
        raise AssertionError(
            "Retrieval must not create Memory"
        )

    async def get_memory(
        self,
        memory_id: UUID,
    ) -> Memory | None:
        for memory in self._memories:
            if memory.memory_id == memory_id:
                return memory

        return None

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
        return self._revisions.get(
            memory_id
        )

    async def list_revisions(
        self,
        memory_id: UUID,
    ) -> tuple[MemoryRevision, ...]:
        revision = self._revisions.get(
            memory_id
        )

        if revision is None:
            return ()

        return (revision,)

    async def replace_active_revision(
        self,
        memory_id: UUID,
        new_revision: MemoryRevision,
    ) -> None:
        raise AssertionError(
            "Retrieval must not edit Memory"
        )

    async def expire_active_revision(
        self,
        memory_id: UUID,
        expected_revision_number: int,
    ) -> None:
        raise AssertionError(
            "Retrieval must not expire Memory"
        )

    async def delete_memory(
        self,
        memory_id: UUID,
        tombstone_revision: MemoryRevision,
    ) -> None:
        raise AssertionError(
            "Retrieval must not delete Memory"
        )


def _revision(
    memory_id: UUID,
    content: str,
) -> MemoryRevision:
    return MemoryRevision(
        memory_id=memory_id,
        revision_number=1,
        content=content,
        source=MemorySource.USER_EXPLICIT,
        lifecycle=MemoryLifecycle.ACTIVE,
        recorded_at=_RECORDED_AT,
    )


def test_retrieval_only_includes_active_character_relationship_memory(
) -> None:
    global_scope = MemoryScope(
        kind=MemoryScopeKind.GLOBAL_USER,
    )

    aria_scope = MemoryScope(
        kind=MemoryScopeKind.CHARACTER,
        character_id="aria",
    )

    other_scope = MemoryScope(
        kind=MemoryScopeKind.CHARACTER,
        character_id="other",
    )

    memories = (
        Memory(
            memory_id=_PROFILE_ID,
            domain=MemoryDomain.USER_PROFILE,
            scope=global_scope,
        ),
        Memory(
            memory_id=_ARIA_RELATIONSHIP_ID,
            domain=MemoryDomain.RELATIONSHIP,
            scope=aria_scope,
        ),
        Memory(
            memory_id=_OTHER_RELATIONSHIP_ID,
            domain=MemoryDomain.RELATIONSHIP,
            scope=other_scope,
        ),
    )

    repository = RetrievalProbeMemoryRepository(
        memories=memories,
        revisions={
            _PROFILE_ID: _revision(
                _PROFILE_ID,
                "User likes programming.",
            ),
            _ARIA_RELATIONSHIP_ID: _revision(
                _ARIA_RELATIONSHIP_ID,
                "User and Aria completed Phase 3.",
            ),
            _OTHER_RELATIONSHIP_ID: _revision(
                _OTHER_RELATIONSHIP_ID,
                "Other Character private history.",
            ),
        },
    )

    service = MemoryRetrievalService(
        repository=repository,
        policy=MemoryRetrievalPolicy(
            limits=MemoryRetrievalLimits(),
        ),
    )

    context = asyncio.run(
        service.retrieve(
            "What do you remember?",
            character_id="aria",
        )
    )

    assert context.user_profile == (
        "User likes programming.",
    )

    assert context.relationship_context == (
        "User and Aria completed Phase 3.",
    )

    assert (
        "Other Character private history."
        not in context.relationship_context
    )
