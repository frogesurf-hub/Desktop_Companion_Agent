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
        *,
        character_id: str,
    ) -> PreparedMemoryContext:
        """
        Retrieve prepared factual Memory context.

        Args:
            query:
                Current user input or retrieval hint.

            character_id:
                Current active Character identity.
                Used only for Character-scoped
                Relationship Memory isolation.

        Returns:
            PreparedMemoryContext:
                Factual Memory context prepared
                for prompt composition.
        """
        ...
