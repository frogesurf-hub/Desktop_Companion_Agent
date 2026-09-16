from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from agent_core.memory import (
    Memory,
    MemoryDomain,
    MemoryLifecycle,
    MemoryRevision,
    MemoryScope,
    MemoryScopeKind,
    MemorySource,
)

_MEMORY_ID = UUID(
    "12345678-1234-5678-1234-567812345678"
)


def _global_scope() -> MemoryScope:
    return MemoryScope(
        kind=MemoryScopeKind.GLOBAL_USER,
    )


def _character_scope() -> MemoryScope:
    return MemoryScope(
        kind=MemoryScopeKind.CHARACTER,
        character_id="aria",
    )


def test_global_user_scope_has_no_character() -> None:
    scope = _global_scope()

    assert scope.kind is MemoryScopeKind.GLOBAL_USER
    assert scope.character_id is None


def test_character_scope_preserves_character_id() -> None:
    scope = _character_scope()

    assert scope.kind is MemoryScopeKind.CHARACTER
    assert scope.character_id == "aria"


def test_global_user_scope_rejects_character_id() -> None:
    with pytest.raises(
        ValueError,
        match="must not define character_id",
    ):
        MemoryScope(
            kind=MemoryScopeKind.GLOBAL_USER,
            character_id="aria",
        )


@pytest.mark.parametrize(
    "character_id",
    [
        None,
        "",
        "   ",
    ],
)
def test_character_scope_requires_character_id(
    character_id: str | None,
) -> None:
    with pytest.raises(
        ValueError,
        match="requires character_id",
    ):
        MemoryScope(
            kind=MemoryScopeKind.CHARACTER,
            character_id=character_id,
        )


@pytest.mark.parametrize(
    "domain",
    [
        MemoryDomain.USER_PROFILE,
        MemoryDomain.WORKING_CONTEXT,
        MemoryDomain.EPISODIC,
    ],
)
def test_global_domains_require_global_scope(
    domain: MemoryDomain,
) -> None:
    with pytest.raises(
        ValueError,
        match="requires GLOBAL_USER scope",
    ):
        Memory(
            memory_id=_MEMORY_ID,
            domain=domain,
            scope=_character_scope(),
        )


def test_relationship_memory_requires_character_scope() -> None:
    with pytest.raises(
        ValueError,
        match="requires CHARACTER scope",
    ):
        Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.RELATIONSHIP,
            scope=_global_scope(),
        )


def test_memory_preserves_identity_domain_and_scope() -> None:
    scope = _global_scope()

    memory = Memory(
        memory_id=_MEMORY_ID,
        domain=MemoryDomain.USER_PROFILE,
        scope=scope,
    )

    assert memory.memory_id == _MEMORY_ID
    assert memory.domain is MemoryDomain.USER_PROFILE
    assert memory.scope == scope

def test_relationship_memory_preserves_character_scope() -> None:
    scope = _character_scope()

    memory = Memory(
        memory_id=_MEMORY_ID,
        domain=MemoryDomain.RELATIONSHIP,
        scope=scope,
    )

    assert memory.domain is MemoryDomain.RELATIONSHIP
    assert memory.scope == scope
    assert memory.scope.character_id == "aria"


def test_memory_revision_preserves_content_and_metadata() -> None:
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
        0,
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

    assert revision.memory_id == _MEMORY_ID
    assert revision.revision_number == 1
    assert revision.content == "The user prefers C#."
    assert revision.source is MemorySource.USER_EXPLICIT
    assert revision.lifecycle is MemoryLifecycle.ACTIVE
    assert revision.recorded_at.tzinfo is UTC
    assert revision.occurred_at is not None
    assert revision.occurred_at.tzinfo is UTC

    assert revision.recorded_at == datetime(
        2026,
        9,
        16,
        12,
        0,
        tzinfo=UTC,
    )
    assert revision.occurred_at == datetime(
        2026,
        9,
        15,
        10,
        0,
        tzinfo=UTC,
    )


@pytest.mark.parametrize(
    "revision_number",
    [
        0,
        -1,
    ],
)
def test_memory_revision_requires_positive_number(
    revision_number: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="must be positive",
    ):
        MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=revision_number,
            content="Valid content.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )


@pytest.mark.parametrize(
    "content",
    [
        None,
        "",
        "   ",
    ],
)
def test_non_deleted_revision_requires_content(
    content: str | None,
) -> None:
    with pytest.raises(
        ValueError,
        match="content must not be empty",
    ):
        MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content=content,
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
        )


def test_deleted_revision_requires_content_to_be_removed() -> None:
    with pytest.raises(
        ValueError,
        match="must not retain content",
    ):
        MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=2,
            content="Content that should be deleted.",
            source=MemorySource.USER_EDIT,
            lifecycle=MemoryLifecycle.DELETED,
            recorded_at=datetime.now(UTC),
        )


def test_deleted_revision_allows_content_free_tombstone() -> None:
    revision = MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=2,
        content=None,
        source=MemorySource.USER_EDIT,
        lifecycle=MemoryLifecycle.DELETED,
        recorded_at=datetime.now(UTC),
    )

    assert revision.content is None
    assert revision.lifecycle is MemoryLifecycle.DELETED


def test_memory_revision_rejects_naive_recorded_at() -> None:
    with pytest.raises(
        ValueError,
        match="recorded_at must be timezone-aware",
    ):
        MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="Valid content.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime(
                2026,
                9,
                16,
                20,
                0,
            ),
        )


def test_memory_revision_rejects_naive_occurred_at() -> None:
    with pytest.raises(
        ValueError,
        match="occurred_at must be timezone-aware",
    ):
        MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content="Valid content.",
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=datetime.now(UTC),
            occurred_at=datetime(
                2026,
                9,
                15,
                18,
                0,
            ),
        )


def test_memory_models_are_immutable() -> None:
    scope = _global_scope()

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

    with pytest.raises(FrozenInstanceError):
        setattr(
            scope,
            "character_id",
            "aria",
        )

    with pytest.raises(FrozenInstanceError):
        setattr(
            memory,
            "domain",
            MemoryDomain.EPISODIC,
        )

    with pytest.raises(FrozenInstanceError):
        setattr(
            revision,
            "content",
            "Changed content.",
        )
