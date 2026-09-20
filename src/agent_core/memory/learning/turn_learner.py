from typing import Protocol

from agent_core.memory.learning.extractor import (
    MemoryCandidateExtractor,
)
from agent_core.memory.learning.models import (
    MemoryCandidate,
    MemoryLearningInput,
)


class MemoryTurnLearner(Protocol):
    """
    Agent Runtime 所需的完整聊天轮次学习边界。
    """

    async def learn_turn(
        self,
        learning_input: MemoryLearningInput,
    ) -> None:
        ...


class _MemoryCandidateLearner(Protocol):
    """
    Turn Learner 内部所需的 Candidate 写入能力。
    """

    async def learn_candidate(
        self,
        candidate: MemoryCandidate,
        *,
        learning_input: MemoryLearningInput,
    ) -> object:
        ...


class AutomaticMemoryTurnLearner:
    """
    将一次完整聊天轮次串入 Automatic Memory Learning。

    Extractor
    → Candidate
    → Learning Service
    """

    def __init__(
        self,
        *,
        extractor: MemoryCandidateExtractor,
        learning_service: _MemoryCandidateLearner,
    ) -> None:
        self._extractor = extractor
        self._learning_service = learning_service

    async def learn_turn(
        self,
        learning_input: MemoryLearningInput,
    ) -> None:
        candidates = await self._extractor.extract(
            learning_input
        )

        for candidate in candidates:
            await self._learning_service.learn_candidate(
                candidate,
                learning_input=learning_input,
            )
