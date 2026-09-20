import asyncio
from datetime import UTC, datetime
from uuid import UUID

from agent_core.memory.learning import (
    AutomaticMemoryTurnLearner,
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
    16,
    0,
    tzinfo=UTC,
)


class FakeExtractor:
    def __init__(
        self,
        candidates: tuple[
            MemoryCandidate,
            ...,
        ],
    ) -> None:
        self._candidates = candidates
        self.inputs: list[
            MemoryLearningInput
        ] = []

    async def extract(
        self,
        learning_input: MemoryLearningInput,
    ) -> tuple[
        MemoryCandidate,
        ...,
    ]:
        self.inputs.append(
            learning_input
        )

        return self._candidates


class FakeCandidateLearner:
    def __init__(self) -> None:
        self.calls: list[
            tuple[
                MemoryCandidate,
                MemoryLearningInput,
            ]
        ] = []

    async def learn_candidate(
        self,
        candidate: MemoryCandidate,
        *,
        learning_input: MemoryLearningInput,
    ) -> object:
        self.calls.append(
            (
                candidate,
                learning_input,
            )
        )

        return object()


def _learning_input() -> MemoryLearningInput:
    return MemoryLearningInput(
        source_message_id="message-1",
        user_text="I prefer C#.",
        assistant_text="Understood.",
        active_character_id="aria",
        occurred_at=_TIMESTAMP,
    )


def _candidate(
    candidate_id: int,
    content: str,
) -> MemoryCandidate:
    return MemoryCandidate(
        candidate_id=UUID(
            int=candidate_id
        ),
        content=content,
        domain=MemoryDomain.EPISODIC,
        scope=MemoryScope(
            kind=MemoryScopeKind.GLOBAL_USER,
        ),
        source=(
            MemorySource
            .AUTOMATIC_EXPLICIT_FACT
        ),
        source_message_id="message-1",
        created_at=_TIMESTAMP,
    )


def test_turn_learner_processes_candidates_in_order(
) -> None:
    first = _candidate(
        1,
        "First fact.",
    )

    second = _candidate(
        2,
        "Second fact.",
    )

    extractor = FakeExtractor(
        (
            first,
            second,
        )
    )

    candidate_learner = (
        FakeCandidateLearner()
    )

    learner = AutomaticMemoryTurnLearner(
        extractor=extractor,
        learning_service=candidate_learner,
    )

    learning_input = _learning_input()

    asyncio.run(
        learner.learn_turn(
            learning_input
        )
    )

    assert extractor.inputs == [
        learning_input,
    ]

    assert candidate_learner.calls == [
        (
            first,
            learning_input,
        ),
        (
            second,
            learning_input,
        ),
    ]


def test_turn_learner_handles_empty_extraction(
) -> None:
    extractor = FakeExtractor(
        ()
    )

    candidate_learner = (
        FakeCandidateLearner()
    )

    learner = AutomaticMemoryTurnLearner(
        extractor=extractor,
        learning_service=candidate_learner,
    )

    learning_input = _learning_input()

    asyncio.run(
        learner.learn_turn(
            learning_input
        )
    )

    assert extractor.inputs == [
        learning_input,
    ]

    assert candidate_learner.calls == []
