import asyncio
from datetime import UTC, datetime
from uuid import UUID

from agent_core.memory.learning import (
    MemoryCandidate,
    MemoryCandidateExtractor,
    MemoryLearningInput,
)
from agent_core.memory.models import (
    MemoryDomain,
    MemoryScope,
    MemoryScopeKind,
    MemorySource,
)


class FakeMemoryCandidateExtractor:
    async def extract(
        self,
        learning_input: MemoryLearningInput,
    ) -> tuple[MemoryCandidate, ...]:
        return (
            MemoryCandidate(
                candidate_id=UUID(
                    "11111111-1111-1111-1111-111111111111"
                ),
                content=learning_input.user_text,
                domain=MemoryDomain.USER_PROFILE,
                scope=MemoryScope(
                    kind=MemoryScopeKind.GLOBAL_USER,
                ),
                source=(
                    MemorySource.AUTOMATIC_EXPLICIT_FACT
                ),
                source_message_id=(
                    learning_input.source_message_id
                ),
                created_at=learning_input.occurred_at,
                occurred_at=learning_input.occurred_at,
            ),
        )


def test_extractor_contract_can_be_implemented() -> None:
    extractor: MemoryCandidateExtractor = (
        FakeMemoryCandidateExtractor()
    )

    learning_input = MemoryLearningInput(
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
            tzinfo=UTC,
        ),
    )

    candidates = asyncio.run(
        extractor.extract(
            learning_input,
        )
    )

    assert len(candidates) == 1

    assert candidates[0].content == (
        "I prefer C#."
    )
