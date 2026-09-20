import logging

from agent_core.memory.health import (
    MemoryCapability,
    MemoryHealthTracker,
)
from agent_core.memory.retrieval import (
    PreparedMemoryContext,
)
from agent_core.memory.retriever import (
    MemoryRetriever,
)

logger = logging.getLogger(__name__)


class ResilientMemoryRetriever:
    """
    Runtime Memory Retrieval failure-isolation boundary.

    Recoverable Memory retrieval failure:
    - marks Retrieval health as degraded;
    - emits only safe diagnostic metadata;
    - returns empty prepared Memory context;
    - does not make ordinary chat unavailable.
    """

    def __init__(
        self,
        *,
        retriever: MemoryRetriever,
        health: MemoryHealthTracker,
    ) -> None:
        self._retriever = retriever
        self._health = health

    async def retrieve(
        self,
        query: str,
        *,
        character_id: str,
    ) -> PreparedMemoryContext:
        try:
            context = await self._retriever.retrieve(
                query,
                character_id=character_id,
            )

        except Exception as exc:
            self._health.mark_degraded(
                MemoryCapability.RETRIEVAL,
                exc,
            )

            logger.warning(
                "Memory retrieval failed: %s",
                type(exc).__name__,
            )

            return PreparedMemoryContext()

        self._health.mark_available(
            MemoryCapability.RETRIEVAL
        )

        return context
