from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from agent_core.memory.learning import (
    MemoryCandidate,
    MemoryLearningInput,
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
    20,
    0,
    tzinfo=timezone(
        timedelta(hours=8),
    ),
)


def test_learning_input_normalizes_time_to_utc() -> None:
    learning_input = MemoryLearningInput(
        source_message_id="message-1",
        user_text="I prefer C#.",
        assistant_text="Understood.",
        active_character_id="aria",
        occurred_at=_TIMESTAMP,
    )

    assert learning_input.occurred_at == datetime(
        2026,
        9,
        19,
        12,
        0,
        tzinfo=UTC,
    )


@pytest.mark.parametrize(
    (
        "source_message_id",
        "user_text",
        "active_character_id",
        "expected_field",
    ),
    [
        (
            " ",
            "I prefer C#.",
            "aria",
            "source_message_id",
        ),
        (
            "message-1",
            "",
            "aria",
            "user_text",
        ),
        (
            "message-1",
            "I prefer C#.",
            " ",
            "active_character_id",
        ),
    ],
)
def test_learning_input_rejects_blank_required_text(
    source_message_id: str,
    user_text: str,
    active_character_id: str,
    expected_field: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=f"{expected_field} must not be empty",
    ):
        MemoryLearningInput(
            source_message_id=source_message_id,
            user_text=user_text,
            assistant_text="Understood.",
            active_character_id=active_character_id,
            occurred_at=_TIMESTAMP,
        )


def test_learning_input_rejects_naive_time() -> None:
    with pytest.raises(
        ValueError,
        match="occurred_at must be timezone-aware",
    ):
        MemoryLearningInput(
            source_message_id="message-1",
            user_text="I prefer C#.",
            assistant_text="Understood.",
            active_character_id="aria",
            occurred_at=datetime(
                2026,
                9,
                19,
                12,
                0,
            ),
        )


def test_memory_candidate_preserves_memory_semantics() -> None:
    candidate = MemoryCandidate(
        candidate_id=UUID(
            "11111111-1111-1111-1111-111111111111"
        ),
        content="The user prefers C#.",
        domain=MemoryDomain.USER_PROFILE,
        scope=MemoryScope(
            kind=MemoryScopeKind.GLOBAL_USER,
        ),
        source=(
            MemorySource.AUTOMATIC_EXPLICIT_FACT
        ),
        source_message_id="message-1",
        created_at=_TIMESTAMP,
        occurred_at=_TIMESTAMP,
    )

    assert candidate.content == (
        "The user prefers C#."
    )

    assert (
        candidate.source
        is MemorySource.AUTOMATIC_EXPLICIT_FACT
    )

    assert candidate.created_at.tzinfo is UTC
    assert candidate.occurred_at is not None
    assert candidate.occurred_at.tzinfo is UTC


def test_memory_candidate_rejects_empty_content() -> None:
    with pytest.raises(
        ValueError,
        match="content must not be empty",
    ):
        MemoryCandidate(
            candidate_id=UUID(
                "11111111-1111-1111-1111-111111111111"
            ),
            content=" ",
            domain=MemoryDomain.USER_PROFILE,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
            source=(
                MemorySource.AUTOMATIC_EXPLICIT_FACT
            ),
            source_message_id="message-1",
            created_at=_TIMESTAMP,
        )


def test_memory_candidate_is_immutable() -> None:
    candidate = MemoryCandidate(
        candidate_id=UUID(
            "11111111-1111-1111-1111-111111111111"
        ),
        content="The user prefers C#.",
        domain=MemoryDomain.USER_PROFILE,
        scope=MemoryScope(
            kind=MemoryScopeKind.GLOBAL_USER,
        ),
        source=(
            MemorySource.AUTOMATIC_EXPLICIT_FACT
        ),
        source_message_id="message-1",
        created_at=_TIMESTAMP,
    )

    with pytest.raises(FrozenInstanceError):
        setattr(
            candidate,
            "content",
            "Modified.",
        )
