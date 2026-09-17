from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from agent_core.memory.conflict import (
    MemoryConflictDecision,
    MemoryConflictPolicy,
)
from agent_core.memory.models import (
    MemoryLifecycle,
    MemoryRevision,
    MemorySource,
)

_MEMORY_ID = UUID(
    "12345678-1234-5678-1234-567812345678"
)

_RECORDED_AT = datetime(
    2026,
    9,
    17,
    10,
    0,
    tzinfo=UTC,
)


def _revision(
    *,
    source: MemorySource,
    recorded_at: datetime = _RECORDED_AT,
    occurred_at: datetime | None = None,
    lifecycle: MemoryLifecycle = (
        MemoryLifecycle.ACTIVE
    ),
    memory_id: UUID = _MEMORY_ID,
) -> MemoryRevision:
    return MemoryRevision(
        memory_id=memory_id,
        revision_number=1,
        content="Conflict candidate.",
        source=source,
        lifecycle=lifecycle,
        recorded_at=recorded_at,
        occurred_at=occurred_at,
    )


@pytest.mark.parametrize(
    (
        "current_source",
        "incoming_source",
    ),
    [
        (
            MemorySource.SYSTEM_OBSERVED,
            MemorySource.AUTOMATIC_EXPLICIT_FACT,
        ),
        (
            MemorySource.AUTOMATIC_EXPLICIT_FACT,
            MemorySource.USER_EXPLICIT,
        ),
        (
            MemorySource.USER_EXPLICIT,
            MemorySource.USER_EDIT,
        ),
    ],
)
def test_higher_authority_replaces_current(
    current_source: MemorySource,
    incoming_source: MemorySource,
) -> None:
    policy = MemoryConflictPolicy()

    current = _revision(
        source=current_source,
        occurred_at=(
            _RECORDED_AT
            + timedelta(days=10)
        ),
    )

    incoming = _revision(
        source=incoming_source,
        occurred_at=(
            _RECORDED_AT
            - timedelta(days=10)
        ),
    )

    assert (
        policy.decide(
            current,
            incoming,
        )
        is MemoryConflictDecision.REPLACE
    )


@pytest.mark.parametrize(
    (
        "current_source",
        "incoming_source",
    ),
    [
        (
            MemorySource.USER_EDIT,
            MemorySource.USER_EXPLICIT,
        ),
        (
            MemorySource.USER_EXPLICIT,
            MemorySource.AUTOMATIC_EXPLICIT_FACT,
        ),
        (
            MemorySource.AUTOMATIC_EXPLICIT_FACT,
            MemorySource.SYSTEM_OBSERVED,
        ),
    ],
)
def test_lower_authority_keeps_current(
    current_source: MemorySource,
    incoming_source: MemorySource,
) -> None:
    policy = MemoryConflictPolicy()

    current = _revision(
        source=current_source,
        occurred_at=(
            _RECORDED_AT
            - timedelta(days=10)
        ),
    )

    incoming = _revision(
        source=incoming_source,
        occurred_at=(
            _RECORDED_AT
            + timedelta(days=10)
        ),
    )

    assert (
        policy.decide(
            current,
            incoming,
        )
        is MemoryConflictDecision.KEEP_CURRENT
    )


def test_equal_authority_newer_fact_replaces_current() -> None:
    policy = MemoryConflictPolicy()

    current = _revision(
        source=MemorySource.USER_EXPLICIT,
        occurred_at=_RECORDED_AT,
    )

    incoming = _revision(
        source=MemorySource.USER_EXPLICIT,
        occurred_at=(
            _RECORDED_AT
            + timedelta(days=1)
        ),
    )

    assert (
        policy.decide(
            current,
            incoming,
        )
        is MemoryConflictDecision.REPLACE
    )


def test_equal_authority_older_fact_keeps_current() -> None:
    policy = MemoryConflictPolicy()

    current = _revision(
        source=MemorySource.USER_EXPLICIT,
        occurred_at=_RECORDED_AT,
    )

    incoming = _revision(
        source=MemorySource.USER_EXPLICIT,
        occurred_at=(
            _RECORDED_AT
            - timedelta(days=1)
        ),
    )

    assert (
        policy.decide(
            current,
            incoming,
        )
        is MemoryConflictDecision.KEEP_CURRENT
    )


def test_equal_authority_equal_fact_time_keeps_current() -> None:
    policy = MemoryConflictPolicy()

    current = _revision(
        source=MemorySource.USER_EXPLICIT,
        occurred_at=_RECORDED_AT,
    )

    incoming = _revision(
        source=MemorySource.USER_EXPLICIT,
        occurred_at=_RECORDED_AT,
    )

    assert (
        policy.decide(
            current,
            incoming,
        )
        is MemoryConflictDecision.KEEP_CURRENT
    )


def test_occurred_at_has_priority_over_recorded_at() -> None:
    policy = MemoryConflictPolicy()

    current = _revision(
        source=MemorySource.USER_EXPLICIT,
        recorded_at=_RECORDED_AT,
        occurred_at=_RECORDED_AT,
    )

    incoming = _revision(
        source=MemorySource.USER_EXPLICIT,
        recorded_at=(
            _RECORDED_AT
            + timedelta(days=30)
        ),
        occurred_at=(
            _RECORDED_AT
            - timedelta(days=1)
        ),
    )

    assert (
        policy.decide(
            current,
            incoming,
        )
        is MemoryConflictDecision.KEEP_CURRENT
    )


def test_recorded_at_is_used_when_occurred_at_is_missing() -> None:
    policy = MemoryConflictPolicy()

    current = _revision(
        source=MemorySource.USER_EXPLICIT,
        recorded_at=_RECORDED_AT,
    )

    incoming = _revision(
        source=MemorySource.USER_EXPLICIT,
        recorded_at=(
            _RECORDED_AT
            + timedelta(seconds=1)
        ),
    )

    assert (
        policy.decide(
            current,
            incoming,
        )
        is MemoryConflictDecision.REPLACE
    )


def test_mismatched_memory_ids_are_rejected() -> None:
    policy = MemoryConflictPolicy()

    current = _revision(
        source=MemorySource.USER_EXPLICIT,
    )

    incoming = _revision(
        source=MemorySource.USER_EXPLICIT,
        memory_id=uuid4(),
    )

    with pytest.raises(
        ValueError,
        match="same Memory",
    ):
        policy.decide(
            current,
            incoming,
        )


def test_non_active_current_revision_is_rejected() -> None:
    policy = MemoryConflictPolicy()

    current = _revision(
        source=MemorySource.USER_EXPLICIT,
        lifecycle=MemoryLifecycle.EXPIRED,
    )

    incoming = _revision(
        source=MemorySource.USER_EXPLICIT,
    )

    with pytest.raises(
        ValueError,
        match="Current conflict revision must be ACTIVE",
    ):
        policy.decide(
            current,
            incoming,
        )


def test_non_active_incoming_revision_is_rejected() -> None:
    policy = MemoryConflictPolicy()

    current = _revision(
        source=MemorySource.USER_EXPLICIT,
    )

    incoming = _revision(
        source=MemorySource.USER_EXPLICIT,
        lifecycle=MemoryLifecycle.SUPERSEDED,
    )

    with pytest.raises(
        ValueError,
        match="Incoming conflict revision must be ACTIVE",
    ):
        policy.decide(
            current,
            incoming,
        )
