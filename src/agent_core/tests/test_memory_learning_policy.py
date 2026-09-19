from datetime import UTC, datetime
from uuid import UUID

import pytest

from agent_core.memory.learning import (
    MemoryCandidate,
    MemoryEligibilityReason,
    MemoryLearningInput,
    MemoryLearningPolicy,
)
from agent_core.memory.models import (
    MemoryDomain,
    MemoryScope,
    MemoryScopeKind,
    MemorySource,
)

_TIMESTAMP = datetime(
    2026,
    9,
    19,
    12,
    0,
    tzinfo=UTC,
)


def _learning_input(
    *,
    source_message_id: str = "message-1",
    active_character_id: str = "aria",
) -> MemoryLearningInput:
    return MemoryLearningInput(
        source_message_id=source_message_id,
        user_text="I prefer C#.",
        assistant_text="Understood.",
        active_character_id=active_character_id,
        occurred_at=_TIMESTAMP,
    )


def _candidate(
    *,
    domain: MemoryDomain = (
        MemoryDomain.USER_PROFILE
    ),
    scope: MemoryScope | None = None,
    source: MemorySource = (
        MemorySource.AUTOMATIC_EXPLICIT_FACT
    ),
    source_message_id: str = "message-1",
) -> MemoryCandidate:
    if scope is None:
        scope = MemoryScope(
            kind=MemoryScopeKind.GLOBAL_USER,
        )

    return MemoryCandidate(
        candidate_id=UUID(
            "11111111-1111-1111-1111-111111111111"
        ),
        content="The user prefers C#.",
        domain=domain,
        scope=scope,
        source=source,
        source_message_id=source_message_id,
        created_at=_TIMESTAMP,
        occurred_at=_TIMESTAMP,
    )


@pytest.mark.parametrize(
    "domain",
    [
        MemoryDomain.USER_PROFILE,
        MemoryDomain.WORKING_CONTEXT,
        MemoryDomain.EPISODIC,
    ],
)
def test_policy_accepts_global_automatic_explicit_fact(
    domain: MemoryDomain,
) -> None:
    policy = MemoryLearningPolicy()

    result = policy.evaluate(
        _candidate(
            domain=domain,
        ),
        learning_input=_learning_input(),
    )

    assert result.eligible is True
    assert (
        result.reason
        is MemoryEligibilityReason.ELIGIBLE
    )


def test_policy_accepts_relationship_for_active_character(
) -> None:
    policy = MemoryLearningPolicy()

    result = policy.evaluate(
        _candidate(
            domain=MemoryDomain.RELATIONSHIP,
            scope=MemoryScope(
                kind=MemoryScopeKind.CHARACTER,
                character_id="aria",
            ),
        ),
        learning_input=_learning_input(),
    )

    assert result.eligible is True


def test_policy_rejects_non_automatic_source() -> None:
    policy = MemoryLearningPolicy()

    result = policy.evaluate(
        _candidate(
            source=MemorySource.USER_EXPLICIT,
        ),
        learning_input=_learning_input(),
    )

    assert result.eligible is False
    assert (
        result.reason
        is MemoryEligibilityReason.UNSUPPORTED_SOURCE
    )


def test_policy_rejects_source_message_mismatch() -> None:
    policy = MemoryLearningPolicy()

    result = policy.evaluate(
        _candidate(
            source_message_id="other-message",
        ),
        learning_input=_learning_input(),
    )

    assert result.eligible is False
    assert (
        result.reason
        is MemoryEligibilityReason
        .SOURCE_MESSAGE_MISMATCH
    )


def test_policy_rejects_global_domain_with_character_scope(
) -> None:
    policy = MemoryLearningPolicy()

    result = policy.evaluate(
        _candidate(
            domain=MemoryDomain.USER_PROFILE,
            scope=MemoryScope(
                kind=MemoryScopeKind.CHARACTER,
                character_id="aria",
            ),
        ),
        learning_input=_learning_input(),
    )

    assert result.eligible is False
    assert (
        result.reason
        is MemoryEligibilityReason.DOMAIN_SCOPE_MISMATCH
    )


def test_policy_rejects_relationship_with_global_scope(
) -> None:
    policy = MemoryLearningPolicy()

    result = policy.evaluate(
        _candidate(
            domain=MemoryDomain.RELATIONSHIP,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        ),
        learning_input=_learning_input(),
    )

    assert result.eligible is False
    assert (
        result.reason
        is MemoryEligibilityReason.DOMAIN_SCOPE_MISMATCH
    )


def test_policy_rejects_relationship_for_other_character(
) -> None:
    policy = MemoryLearningPolicy()

    result = policy.evaluate(
        _candidate(
            domain=MemoryDomain.RELATIONSHIP,
            scope=MemoryScope(
                kind=MemoryScopeKind.CHARACTER,
                character_id="other",
            ),
        ),
        learning_input=_learning_input(
            active_character_id="aria",
        ),
    )

    assert result.eligible is False
    assert (
        result.reason
        is MemoryEligibilityReason
        .ACTIVE_CHARACTER_MISMATCH
    )
