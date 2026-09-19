import asyncio
from datetime import UTC, datetime
from uuid import UUID

import pytest

from agent_core.memory.learning import (
    ExistingMemoryResolutionKind,
    ExistingMemoryResolver,
    ExistingMemoryStateError,
    MemoryCandidate,
)
from agent_core.memory.models import (
    Memory,
    MemoryDomain,
    MemoryIdentityKey,
    MemoryLifecycle,
    MemoryRevision,
    MemoryScope,
    MemoryScopeKind,
    MemorySource,
)

_NOW = datetime(
    2026,
    9,
    19,
    12,
    0,
    tzinfo=UTC,
)

_MEMORY_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)

_OTHER_MEMORY_ID = UUID(
    "22222222-2222-2222-2222-222222222222"
)


class FakeMemoryResolutionRepository:
    def __init__(
        self,
        *,
        memories: tuple[Memory, ...] = (),
        revisions: dict[
            UUID,
            tuple[MemoryRevision, ...],
        ] | None = None,
    ) -> None:
        self._memories = memories
        self._revisions = (
            revisions
            if revisions is not None
            else {}
        )

    async def find_memory_by_identity(
        self,
        *,
        domain: MemoryDomain,
        scope: MemoryScope,
        identity_key: MemoryIdentityKey,
    ) -> Memory | None:
        matches = tuple(
            memory
            for memory in self._memories
            if memory.domain is domain
            and memory.scope == scope
            and memory.identity_key == identity_key
        )

        if len(matches) > 1:
            raise AssertionError(
                "Fake repository contains duplicate "
                "logical identities"
            )

        if not matches:
            return None

        return matches[0]

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
        revisions = self._revisions.get(
            memory_id,
            (),
        )

        active = tuple(
            revision
            for revision in revisions
            if (
                revision.lifecycle
                is MemoryLifecycle.ACTIVE
            )
        )

        if len(active) > 1:
            raise AssertionError(
                "Fake repository has multiple "
                "ACTIVE revisions"
            )

        if not active:
            return None

        return active[0]

    async def list_revisions(
        self,
        memory_id: UUID,
    ) -> tuple[MemoryRevision, ...]:
        return self._revisions.get(
            memory_id,
            (),
        )


def _scope() -> MemoryScope:
    return MemoryScope(
        kind=MemoryScopeKind.GLOBAL_USER,
    )


def _identity_key() -> MemoryIdentityKey:
    return MemoryIdentityKey(
        "user_profile.preference.programming_language"
    )


def _memory(
    *,
    memory_id: UUID = _MEMORY_ID,
    identity_key: MemoryIdentityKey | None = None,
) -> Memory:
    return Memory(
        memory_id=memory_id,
        domain=MemoryDomain.USER_PROFILE,
        scope=_scope(),
        identity_key=identity_key,
    )


def _revision(
    *,
    memory_id: UUID = _MEMORY_ID,
    content: str | None = "The user prefers C#.",
    lifecycle: MemoryLifecycle = (
        MemoryLifecycle.ACTIVE
    ),
    revision_number: int = 1,
) -> MemoryRevision:
    return MemoryRevision(
        memory_id=memory_id,
        revision_number=revision_number,
        content=content,
        source=MemorySource.USER_EXPLICIT,
        lifecycle=lifecycle,
        recorded_at=_NOW,
    )


def _candidate(
    *,
    content: str = "The user prefers C#.",
    identity_key: MemoryIdentityKey | None = None,
) -> MemoryCandidate:
    return MemoryCandidate(
        candidate_id=UUID(
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        ),
        content=content,
        domain=MemoryDomain.USER_PROFILE,
        scope=_scope(),
        source=(
            MemorySource.AUTOMATIC_EXPLICIT_FACT
        ),
        source_message_id="message-1",
        created_at=_NOW,
        identity_key=identity_key,
    )


def test_resolver_returns_new_when_no_match_exists() -> None:
    resolver = ExistingMemoryResolver(
        FakeMemoryResolutionRepository()
    )

    result = asyncio.run(
        resolver.resolve(
            _candidate(),
        )
    )

    assert (
        result.kind
        is ExistingMemoryResolutionKind.NEW
    )
    assert result.memory is None
    assert result.latest_revision is None


def test_resolver_returns_duplicate_for_identity_match_with_same_content(
) -> None:
    memory = _memory(
        identity_key=_identity_key(),
    )
    revision = _revision()

    resolver = ExistingMemoryResolver(
        FakeMemoryResolutionRepository(
            memories=(memory,),
            revisions={
                memory.memory_id: (
                    revision,
                ),
            },
        )
    )

    result = asyncio.run(
        resolver.resolve(
            _candidate(
                identity_key=_identity_key(),
            ),
        )
    )

    assert (
        result.kind
        is ExistingMemoryResolutionKind.DUPLICATE
    )
    assert result.memory == memory
    assert result.latest_revision == revision


def test_resolver_returns_existing_for_identity_match_with_new_content(
) -> None:
    memory = _memory(
        identity_key=_identity_key(),
    )
    revision = _revision()

    resolver = ExistingMemoryResolver(
        FakeMemoryResolutionRepository(
            memories=(memory,),
            revisions={
                memory.memory_id: (
                    revision,
                ),
            },
        )
    )

    result = asyncio.run(
        resolver.resolve(
            _candidate(
                content="The user prefers Rust.",
                identity_key=_identity_key(),
            ),
        )
    )

    assert (
        result.kind
        is ExistingMemoryResolutionKind.EXISTING
    )
    assert result.memory == memory
    assert result.latest_revision == revision


def test_resolver_falls_back_to_exact_duplicate_for_legacy_memory(
) -> None:
    memory = _memory()
    revision = _revision()

    resolver = ExistingMemoryResolver(
        FakeMemoryResolutionRepository(
            memories=(memory,),
            revisions={
                memory.memory_id: (
                    revision,
                ),
            },
        )
    )

    result = asyncio.run(
        resolver.resolve(
            _candidate(
                identity_key=_identity_key(),
            ),
        )
    )

    assert (
        result.kind
        is ExistingMemoryResolutionKind.DUPLICATE
    )
    assert result.memory == memory


def test_resolver_does_not_merge_different_identity_keys_by_content(
) -> None:
    existing_identity = MemoryIdentityKey(
        "user_profile.preference.favorite_language"
    )

    candidate_identity = MemoryIdentityKey(
        "user_profile.preference.work_language"
    )

    memory = _memory(
        identity_key=existing_identity,
    )

    revision = _revision(
        content="C#",
    )

    resolver = ExistingMemoryResolver(
        FakeMemoryResolutionRepository(
            memories=(memory,),
            revisions={
                memory.memory_id: (
                    revision,
                ),
            },
        )
    )

    result = asyncio.run(
        resolver.resolve(
            _candidate(
                content="C#",
                identity_key=candidate_identity,
            ),
        )
    )

    assert (
        result.kind
        is ExistingMemoryResolutionKind.NEW
    )
    assert result.memory is None
    assert result.latest_revision is None


@pytest.mark.parametrize(
    "lifecycle",
    [
        MemoryLifecycle.EXPIRED,
        MemoryLifecycle.DELETED,
    ],
)
def test_resolver_preserves_inactive_identity_as_existing(
    lifecycle: MemoryLifecycle,
) -> None:
    memory = _memory(
        identity_key=_identity_key(),
    )

    revision = _revision(
        content=(
            None
            if lifecycle is MemoryLifecycle.DELETED
            else "Expired working fact."
        ),
        lifecycle=lifecycle,
    )

    resolver = ExistingMemoryResolver(
        FakeMemoryResolutionRepository(
            memories=(memory,),
            revisions={
                memory.memory_id: (
                    revision,
                ),
            },
        )
    )

    result = asyncio.run(
        resolver.resolve(
            _candidate(
                identity_key=_identity_key(),
            ),
        )
    )

    assert (
        result.kind
        is ExistingMemoryResolutionKind.EXISTING
    )
    assert result.memory == memory
    assert result.latest_revision == revision


def test_resolver_does_not_treat_expired_content_as_duplicate(
) -> None:
    memory = _memory()
    revision = _revision(
        lifecycle=MemoryLifecycle.EXPIRED,
    )

    resolver = ExistingMemoryResolver(
        FakeMemoryResolutionRepository(
            memories=(memory,),
            revisions={
                memory.memory_id: (
                    revision,
                ),
            },
        )
    )

    result = asyncio.run(
        resolver.resolve(
            _candidate(),
        )
    )

    assert (
        result.kind
        is ExistingMemoryResolutionKind.NEW
    )


def test_resolver_rejects_identity_memory_without_revision(
) -> None:
    memory = _memory(
        identity_key=_identity_key(),
    )

    resolver = ExistingMemoryResolver(
        FakeMemoryResolutionRepository(
            memories=(memory,),
        )
    )

    with pytest.raises(
        ExistingMemoryStateError,
        match="has no revisions",
    ):
        asyncio.run(
            resolver.resolve(
                _candidate(
                    identity_key=_identity_key(),
                ),
            )
        )


def test_resolver_does_not_cross_character_scope() -> None:
    identity_key = MemoryIdentityKey(
        "relationship.shared_project"
    )

    other_scope = MemoryScope(
        kind=MemoryScopeKind.CHARACTER,
        character_id="other",
    )

    aria_scope = MemoryScope(
        kind=MemoryScopeKind.CHARACTER,
        character_id="aria",
    )

    memory = Memory(
        memory_id=_OTHER_MEMORY_ID,
        domain=MemoryDomain.RELATIONSHIP,
        scope=other_scope,
        identity_key=identity_key,
    )

    revision = MemoryRevision(
        memory_id=_OTHER_MEMORY_ID,
        revision_number=1,
        content="Shared project.",
        source=MemorySource.USER_EXPLICIT,
        lifecycle=MemoryLifecycle.ACTIVE,
        recorded_at=_NOW,
    )

    candidate = MemoryCandidate(
        candidate_id=UUID(
            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        ),
        content="Shared project.",
        domain=MemoryDomain.RELATIONSHIP,
        scope=aria_scope,
        source=(
            MemorySource.AUTOMATIC_EXPLICIT_FACT
        ),
        source_message_id="message-1",
        created_at=_NOW,
        identity_key=identity_key,
    )

    resolver = ExistingMemoryResolver(
        FakeMemoryResolutionRepository(
            memories=(memory,),
            revisions={
                memory.memory_id: (
                    revision,
                ),
            },
        )
    )

    result = asyncio.run(
        resolver.resolve(candidate)
    )

    assert (
        result.kind
        is ExistingMemoryResolutionKind.NEW
    )
