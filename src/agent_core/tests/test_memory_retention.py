from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

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

_MEMORY_ID = UUID(
    "12345678-1234-5678-1234-567812345678"
)

_RECORDED_AT = datetime(
    2026,
    9,
    10,
    12,
    0,
    tzinfo=UTC,
)


def _memory(
    domain: MemoryDomain,
) -> Memory:
    return Memory(
        memory_id=_MEMORY_ID,
        domain=domain,
        scope=MemoryScope(
            kind=MemoryScopeKind.GLOBAL_USER,
        ),
    )


def _revision(
    *,
    lifecycle: MemoryLifecycle = (
        MemoryLifecycle.ACTIVE
    ),
    recorded_at: datetime = _RECORDED_AT,
    occurred_at: datetime | None = None,
) -> MemoryRevision:
    return MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=1,
        content="Current project context.",
        source=MemorySource.USER_EXPLICIT,
        lifecycle=lifecycle,
        recorded_at=recorded_at,
        occurred_at=occurred_at,
    )


def test_working_context_deadline_uses_recorded_at() -> None:
    policy = MemoryRetentionPolicy(
        working_context_retention_days=7
    )

    memory = _memory(
        MemoryDomain.WORKING_CONTEXT
    )

    occurred_at = datetime(
        2026,
        9,
        1,
        8,
        0,
        tzinfo=UTC,
    )

    revision = _revision(
        occurred_at=occurred_at
    )

    assert policy.expiration_deadline(
        memory,
        revision,
    ) == (
        _RECORDED_AT
        + timedelta(days=7)
    )


def test_working_context_before_deadline_is_active() -> None:
    policy = MemoryRetentionPolicy(
        working_context_retention_days=7
    )

    memory = _memory(
        MemoryDomain.WORKING_CONTEXT
    )

    revision = _revision()

    assert (
        policy.should_expire(
            memory,
            revision,
            now=(
                _RECORDED_AT
                + timedelta(days=7)
                - timedelta(seconds=1)
            ),
        )
        is False
    )


def test_working_context_at_deadline_expires() -> None:
    policy = MemoryRetentionPolicy(
        working_context_retention_days=7
    )

    memory = _memory(
        MemoryDomain.WORKING_CONTEXT
    )

    revision = _revision()

    assert (
        policy.should_expire(
            memory,
            revision,
            now=(
                _RECORDED_AT
                + timedelta(days=7)
            ),
        )
        is True
    )


def test_new_revision_resets_retention_window() -> None:
    policy = MemoryRetentionPolicy(
        working_context_retention_days=7
    )

    memory = _memory(
        MemoryDomain.WORKING_CONTEXT
    )

    later_recorded_at = (
        _RECORDED_AT
        + timedelta(days=5)
    )

    revision = _revision(
        recorded_at=later_recorded_at
    )

    assert policy.expiration_deadline(
        memory,
        revision,
    ) == (
        later_recorded_at
        + timedelta(days=7)
    )


@pytest.mark.parametrize(
    "domain",
    [
        MemoryDomain.USER_PROFILE,
        MemoryDomain.EPISODIC,
    ],
)
def test_non_retained_domains_do_not_auto_expire(
    domain: MemoryDomain,
) -> None:
    policy = MemoryRetentionPolicy(
        working_context_retention_days=7
    )

    memory = _memory(domain)
    revision = _revision()

    assert (
        policy.expiration_deadline(
            memory,
            revision,
        )
        is None
    )

    assert (
        policy.should_expire(
            memory,
            revision,
            now=(
                _RECORDED_AT
                + timedelta(days=365)
            ),
        )
        is False
    )


def test_relationship_memory_does_not_auto_expire() -> None:
    policy = MemoryRetentionPolicy(
        working_context_retention_days=7
    )

    memory = Memory(
        memory_id=_MEMORY_ID,
        domain=MemoryDomain.RELATIONSHIP,
        scope=MemoryScope(
            kind=MemoryScopeKind.CHARACTER,
            character_id="aria",
        ),
    )

    revision = _revision()

    assert (
        policy.expiration_deadline(
            memory,
            revision,
        )
        is None
    )

    assert (
        policy.should_expire(
            memory,
            revision,
            now=(
                _RECORDED_AT
                + timedelta(days=365)
            ),
        )
        is False
    )


def test_non_active_revision_does_not_expire_again() -> None:
    policy = MemoryRetentionPolicy(
        working_context_retention_days=7
    )

    memory = _memory(
        MemoryDomain.WORKING_CONTEXT
    )

    revision = _revision(
        lifecycle=MemoryLifecycle.EXPIRED
    )

    assert (
        policy.should_expire(
            memory,
            revision,
            now=(
                _RECORDED_AT
                + timedelta(days=30)
            ),
        )
        is False
    )


@pytest.mark.parametrize(
    "retention_days",
    [
        0,
        31,
    ],
)
def test_invalid_retention_days_are_rejected(
    retention_days: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="between 1 and 30",
    ):
        MemoryRetentionPolicy(
            working_context_retention_days=(
                retention_days
            )
        )


def test_mismatched_memory_revision_is_rejected() -> None:
    policy = MemoryRetentionPolicy(
        working_context_retention_days=7
    )

    memory = _memory(
        MemoryDomain.WORKING_CONTEXT
    )

    revision = MemoryRevision(
        memory_id=uuid4(),
        revision_number=1,
        content="Different memory.",
        source=MemorySource.USER_EXPLICIT,
        lifecycle=MemoryLifecycle.ACTIVE,
        recorded_at=_RECORDED_AT,
    )

    with pytest.raises(
        ValueError,
        match="must match",
    ):
        policy.should_expire(
            memory,
            revision,
            now=_RECORDED_AT,
        )


def test_naive_evaluation_time_is_rejected() -> None:
    policy = MemoryRetentionPolicy(
        working_context_retention_days=7
    )

    memory = _memory(
        MemoryDomain.WORKING_CONTEXT
    )

    revision = _revision()

    naive_now = datetime(
        2026,
        9,
        20,
        12,
        0,
    )

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        policy.should_expire(
            memory,
            revision,
            now=naive_now,
        )
