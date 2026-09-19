import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from agent_core.memory.conflict import (
    MemoryConflictPolicy,
)
from agent_core.memory.learning import (
    ExistingMemoryResolution,
    ExistingMemoryResolutionKind,
    MemoryCandidate,
    MemoryLearningInput,
    MemoryLearningOutcome,
    MemoryLearningPolicy,
    MemoryLearningService,
    MemoryLearningStateError,
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

_CREATED_AT = datetime(
    2026,
    9,
    19,
    14,
    0,
    tzinfo=UTC,
)

_OCCURRED_AT = _CREATED_AT - timedelta(
    minutes=5
)

_MEMORY_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)


class StubMemoryCandidateResolver:
    def __init__(
        self,
        resolution: ExistingMemoryResolution,
    ) -> None:
        self._resolution = resolution
        self.calls: list[MemoryCandidate] = []

    async def resolve(
        self,
        candidate: MemoryCandidate,
    ) -> ExistingMemoryResolution:
        self.calls.append(candidate)

        return self._resolution


class ProbeMemoryLearningRepository:
    def __init__(self) -> None:
        self.create_calls: list[
            tuple[
                Memory,
                MemoryRevision,
            ]
        ] = []

        self.replace_calls: list[
            tuple[
                UUID,
                MemoryRevision,
            ]
        ] = []

        self.adopt_calls: list[
            tuple[
                UUID,
                MemoryIdentityKey,
            ]
        ] = []

        self.reactivate_calls: list[
            tuple[
                UUID,
                MemoryRevision,
            ]
        ] = []

    async def create_memory(
        self,
        memory: Memory,
        initial_revision: MemoryRevision,
    ) -> None:
        self.create_calls.append(
            (
                memory,
                initial_revision,
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

    async def adopt_identity_key(
        self,
        memory_id: UUID,
        identity_key: MemoryIdentityKey,
    ) -> None:
        self.adopt_calls.append(
            (
                memory_id,
                identity_key,
            )
        )

    async def reactivate_memory(
        self,
        memory_id: UUID,
        new_revision: MemoryRevision,
    ) -> None:
        self.reactivate_calls.append(
            (
                memory_id,
                new_revision,
            )
        )


def _scope() -> MemoryScope:
    return MemoryScope(
        kind=MemoryScopeKind.GLOBAL_USER,
    )


def _identity_key() -> MemoryIdentityKey:
    return MemoryIdentityKey(
        "user_profile.preference.programming_language"
    )


def _candidate(
    *,
    content: str = "The user prefers C#.",
    source: MemorySource = (
        MemorySource.AUTOMATIC_EXPLICIT_FACT
    ),
) -> MemoryCandidate:
    return MemoryCandidate(
        candidate_id=UUID(
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        ),
        content=content,
        domain=MemoryDomain.USER_PROFILE,
        scope=_scope(),
        source=source,
        source_message_id="message-1",
        created_at=_CREATED_AT,
        occurred_at=_OCCURRED_AT,
        identity_key=_identity_key(),
    )


def _learning_input() -> MemoryLearningInput:
    return MemoryLearningInput(
        source_message_id="message-1",
        user_text="I prefer C#.",
        assistant_text="Understood.",
        active_character_id="aria",
        occurred_at=_CREATED_AT,
    )


def _memory() -> Memory:
    return Memory(
        memory_id=_MEMORY_ID,
        domain=MemoryDomain.USER_PROFILE,
        scope=_scope(),
        identity_key=_identity_key(),
    )


def _revision(
    *,
    source: MemorySource,
    content: str = "The user prefers Python.",
    revision_number: int = 2,
) -> MemoryRevision:
    return MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=revision_number,
        content=content,
        source=source,
        lifecycle=MemoryLifecycle.ACTIVE,
        recorded_at=(
            _CREATED_AT
            - timedelta(hours=1)
        ),
        occurred_at=(
            _OCCURRED_AT
            - timedelta(hours=1)
        ),
    )


def _service(
    *,
    resolution: ExistingMemoryResolution,
    repository: ProbeMemoryLearningRepository,
) -> tuple[
    MemoryLearningService,
    StubMemoryCandidateResolver,
]:
    resolver = StubMemoryCandidateResolver(
        resolution
    )

    return (
        MemoryLearningService(
            repository=repository,
            policy=MemoryLearningPolicy(),
            resolver=resolver,
            conflict_policy=MemoryConflictPolicy(),
        ),
        resolver,
    )


def test_learning_service_rejects_ineligible_candidate(
) -> None:
    repository = ProbeMemoryLearningRepository()

    service, resolver = _service(
        resolution=ExistingMemoryResolution(
            kind=ExistingMemoryResolutionKind.NEW,
        ),
        repository=repository,
    )

    result = asyncio.run(
        service.learn_candidate(
            _candidate(
                source=MemorySource.USER_EXPLICIT,
            ),
            learning_input=_learning_input(),
        )
    )

    assert (
        result.outcome
        is MemoryLearningOutcome.REJECTED
    )

    assert resolver.calls == []
    assert repository.create_calls == []
    assert repository.replace_calls == []


def test_learning_service_creates_new_memory() -> None:
    repository = ProbeMemoryLearningRepository()

    service, resolver = _service(
        resolution=ExistingMemoryResolution(
            kind=ExistingMemoryResolutionKind.NEW,
        ),
        repository=repository,
    )

    candidate = _candidate()

    result = asyncio.run(
        service.learn_candidate(
            candidate,
            learning_input=_learning_input(),
        )
    )

    assert (
        result.outcome
        is MemoryLearningOutcome.CREATED
    )

    assert resolver.calls == [
        candidate,
    ]

    assert len(repository.create_calls) == 1

    memory, revision = (
        repository.create_calls[0]
    )

    assert result.memory == memory
    assert result.revision == revision

    assert memory.domain is candidate.domain
    assert memory.scope == candidate.scope
    assert (
        memory.identity_key
        == candidate.identity_key
    )

    assert revision.memory_id == memory.memory_id
    assert revision.revision_number == 1
    assert revision.content == candidate.content
    assert revision.source is candidate.source

    assert (
        revision.lifecycle
        is MemoryLifecycle.ACTIVE
    )

    assert (
        revision.recorded_at
        == candidate.created_at
    )

    assert (
        revision.occurred_at
        == candidate.occurred_at
    )

    assert repository.replace_calls == []


def test_learning_service_skips_duplicate() -> None:
    repository = ProbeMemoryLearningRepository()

    memory = _memory()

    revision = _revision(
        source=MemorySource.USER_EXPLICIT,
        content="The user prefers C#.",
    )

    service, _ = _service(
        resolution=ExistingMemoryResolution(
            kind=(
                ExistingMemoryResolutionKind
                .DUPLICATE
            ),
            memory=memory,
            latest_revision=revision,
        ),
        repository=repository,
    )

    result = asyncio.run(
        service.learn_candidate(
            _candidate(),
            learning_input=_learning_input(),
        )
    )

    assert (
        result.outcome
        is MemoryLearningOutcome.DUPLICATE
    )

    assert result.memory == memory
    assert result.revision == revision

    assert repository.create_calls == []
    assert repository.replace_calls == []


def test_learning_service_keeps_higher_authority_current_revision(
) -> None:
    repository = ProbeMemoryLearningRepository()

    memory = _memory()

    current_revision = _revision(
        source=MemorySource.USER_EXPLICIT,
    )

    service, _ = _service(
        resolution=ExistingMemoryResolution(
            kind=(
                ExistingMemoryResolutionKind
                .EXISTING
            ),
            memory=memory,
            latest_revision=current_revision,
        ),
        repository=repository,
    )

    result = asyncio.run(
        service.learn_candidate(
            _candidate(
                content="The user prefers Rust.",
            ),
            learning_input=_learning_input(),
        )
    )

    assert (
        result.outcome
        is MemoryLearningOutcome.KEPT_CURRENT
    )

    assert result.memory == memory
    assert result.revision == current_revision

    assert repository.create_calls == []
    assert repository.replace_calls == []


def test_learning_service_replaces_lower_authority_current_revision(
) -> None:
    repository = ProbeMemoryLearningRepository()

    memory = _memory()

    current_revision = _revision(
        source=MemorySource.SYSTEM_OBSERVED,
    )

    service, _ = _service(
        resolution=ExistingMemoryResolution(
            kind=(
                ExistingMemoryResolutionKind
                .EXISTING
            ),
            memory=memory,
            latest_revision=current_revision,
        ),
        repository=repository,
    )

    candidate = _candidate(
        content="The user prefers Rust.",
    )

    result = asyncio.run(
        service.learn_candidate(
            candidate,
            learning_input=_learning_input(),
        )
    )

    assert (
        result.outcome
        is MemoryLearningOutcome.REPLACED
    )

    assert len(repository.replace_calls) == 1

    memory_id, revision = (
        repository.replace_calls[0]
    )

    assert memory_id == memory.memory_id
    assert result.memory == memory
    assert result.revision == revision

    assert revision.revision_number == 3
    assert revision.content == candidate.content
    assert revision.source is candidate.source

    assert (
        revision.lifecycle
        is MemoryLifecycle.ACTIVE
    )

    assert (
        revision.recorded_at
        == candidate.created_at
    )

    assert (
        revision.occurred_at
        == candidate.occurred_at
    )

    assert repository.create_calls == []


def test_learning_service_adopts_identity_for_legacy_duplicate(
) -> None:
    repository = ProbeMemoryLearningRepository()

    legacy_memory = Memory(
        memory_id=_MEMORY_ID,
        domain=MemoryDomain.USER_PROFILE,
        scope=_scope(),
    )

    current_revision = _revision(
        source=MemorySource.USER_EXPLICIT,
        content="The user prefers C#.",
    )

    service, _ = _service(
        resolution=ExistingMemoryResolution(
            kind=(
                ExistingMemoryResolutionKind
                .DUPLICATE
            ),
            memory=legacy_memory,
            latest_revision=current_revision,
        ),
        repository=repository,
    )

    candidate = _candidate()

    result = asyncio.run(
        service.learn_candidate(
            candidate,
            learning_input=_learning_input(),
        )
    )

    assert (
        result.outcome
        is MemoryLearningOutcome.IDENTITY_ADOPTED
    )

    assert repository.adopt_calls == [
        (
            _MEMORY_ID,
            _identity_key(),
        )
    ]

    assert result.memory is not None
    assert (
        result.memory.identity_key
        == candidate.identity_key
    )

    assert result.revision == current_revision

    assert repository.create_calls == []
    assert repository.replace_calls == []
    assert repository.reactivate_calls == []


def test_learning_service_reactivates_expired_memory(
) -> None:
    repository = ProbeMemoryLearningRepository()

    memory = _memory()

    expired_revision = MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=2,
        content="The user prefers Python.",
        source=MemorySource.AUTOMATIC_EXPLICIT_FACT,
        lifecycle=MemoryLifecycle.EXPIRED,
        recorded_at=(
            _CREATED_AT
            - timedelta(days=10)
        ),
        occurred_at=(
            _OCCURRED_AT
            - timedelta(days=10)
        ),
    )

    service, _ = _service(
        resolution=ExistingMemoryResolution(
            kind=(
                ExistingMemoryResolutionKind
                .EXISTING
            ),
            memory=memory,
            latest_revision=expired_revision,
        ),
        repository=repository,
    )

    candidate = _candidate(
        content="The user prefers Rust.",
    )

    result = asyncio.run(
        service.learn_candidate(
            candidate,
            learning_input=_learning_input(),
        )
    )

    assert (
        result.outcome
        is MemoryLearningOutcome.REACTIVATED
    )

    assert len(repository.reactivate_calls) == 1

    memory_id, revision = (
        repository.reactivate_calls[0]
    )

    assert memory_id == _MEMORY_ID
    assert revision.revision_number == 3
    assert revision.content == candidate.content

    assert (
        revision.lifecycle
        is MemoryLifecycle.ACTIVE
    )

    assert result.memory == memory
    assert result.revision == revision

    assert repository.create_calls == []
    assert repository.replace_calls == []
    assert repository.adopt_calls == []


def test_learning_service_does_not_resurrect_deleted_memory(
) -> None:
    repository = ProbeMemoryLearningRepository()

    memory = _memory()

    tombstone = MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=3,
        content=None,
        source=MemorySource.USER_EDIT,
        lifecycle=MemoryLifecycle.DELETED,
        recorded_at=(
            _CREATED_AT
            - timedelta(days=1)
        ),
    )

    service, _ = _service(
        resolution=ExistingMemoryResolution(
            kind=(
                ExistingMemoryResolutionKind
                .EXISTING
            ),
            memory=memory,
            latest_revision=tombstone,
        ),
        repository=repository,
    )

    result = asyncio.run(
        service.learn_candidate(
            _candidate(
                content="The user prefers Rust.",
            ),
            learning_input=_learning_input(),
        )
    )

    assert (
        result.outcome
        is MemoryLearningOutcome.BLOCKED_DELETED
    )

    assert result.memory == memory
    assert result.revision == tombstone

    assert repository.create_calls == []
    assert repository.replace_calls == []
    assert repository.adopt_calls == []
    assert repository.reactivate_calls == []


def test_learning_service_rejects_superseded_latest_state(
) -> None:
    repository = ProbeMemoryLearningRepository()

    memory = _memory()

    superseded_revision = MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=2,
        content="Old fact.",
        source=MemorySource.USER_EXPLICIT,
        lifecycle=MemoryLifecycle.SUPERSEDED,
        recorded_at=(
            _CREATED_AT
            - timedelta(days=1)
        ),
    )

    service, _ = _service(
        resolution=ExistingMemoryResolution(
            kind=(
                ExistingMemoryResolutionKind
                .EXISTING
            ),
            memory=memory,
            latest_revision=superseded_revision,
        ),
        repository=repository,
    )

    with pytest.raises(
        MemoryLearningStateError,
        match="unsupported lifecycle",
    ):
        asyncio.run(
            service.learn_candidate(
                _candidate(),
                learning_input=_learning_input(),
            )
        )

    assert repository.create_calls == []
    assert repository.replace_calls == []
    assert repository.adopt_calls == []
    assert repository.reactivate_calls == []
