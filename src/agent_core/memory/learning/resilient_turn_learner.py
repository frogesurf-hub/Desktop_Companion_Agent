import logging

from agent_core.memory.health import (
    MemoryCapability,
    MemoryHealthTracker,
)
from agent_core.memory.learning.models import (
    MemoryLearningInput,
)
from agent_core.memory.learning.turn_learner import (
    MemoryTurnLearner,
)

logger = logging.getLogger(__name__)


class ResilientMemoryTurnLearner:
    """
    Runtime Automatic Memory Learning failure-isolation boundary.

    A failed automatic-learning attempt must not invalidate
    an already successful assistant response.
    """

    def __init__(
        self,
        *,
        learner: MemoryTurnLearner,
        health: MemoryHealthTracker,
    ) -> None:
        self._learner = learner
        self._health = health

    async def learn_turn(
        self,
        learning_input: MemoryLearningInput,
    ) -> None:
        try:
            await self._learner.learn_turn(
                learning_input
            )

        except Exception as exc:
            self._health.mark_degraded(
                MemoryCapability.AUTOMATIC_LEARNING,
                exc,
            )

            logger.warning(
                "Automatic Memory learning failed: %s",
                type(exc).__name__,
            )

            return

        self._health.mark_available(
            MemoryCapability.AUTOMATIC_LEARNING
        )
