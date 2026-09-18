from typing import Protocol

from agent_core.memory.retrieval import PreparedMemoryContext


class MemoryRetriever(Protocol):
    """
    Runtime Memory retrieval contract.

    Agent depends on this protocol.
    Concrete retrieval implementation
    stays inside memory subsystem.
    """

    async def retrieve(
        self,
        query: str,
    ) -> PreparedMemoryContext:
        """
        Retrieve prepared memory context.

        Args:
            query:
                Current user input or retrieval hint.

        Returns:
            PreparedMemoryContext:
                Factual memory context prepared for composition.
        """
        ...