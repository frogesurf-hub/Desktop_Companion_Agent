from typing import Protocol

from agent_core.memory.learning.models import (
    MemoryCandidate,
    MemoryLearningInput,
)


class MemoryCandidateExtractor(Protocol):
    """
    Automatic Memory Learning 的候选提取边界。

    Extractor 只负责：
    Learning Input -> Candidate

    不负责：
    - eligibility validation
    - duplicate/conflict detection
    - Memory persistence
    """

    async def extract(
        self,
        learning_input: MemoryLearningInput,
    ) -> tuple[MemoryCandidate, ...]:
        ...
