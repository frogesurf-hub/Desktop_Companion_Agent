from agent_core.memory.models import (
    MemoryDomain,
    MemoryScope,
    MemoryScopeKind,
)
from agent_core.memory.repository import MemoryRepository
from agent_core.memory.retrieval import PreparedMemoryContext
from agent_core.memory.retrieval_policy import (
    MemoryRetrievalPolicy,
)


class MemoryRetrievalService:
    """
    执行 Memory Retrieval。

    根据 RetrievalPolicy 从 Repository 获取
    当前请求允许访问的 factual Memory，
    最终生成 PreparedMemoryContext。
    """

    def __init__(
        self,
        *,
        repository: MemoryRepository,
        policy: MemoryRetrievalPolicy,
    ) -> None:
        self._repository = repository
        self._policy = policy

    async def retrieve(
        self,
        query: str,
        *,
        character_id: str,
    ) -> PreparedMemoryContext:
        """
        获取当前用户与当前 Character 可访问的 Memory Context。
        """
        user_profile: list[str] = []
        working_context: list[str] = []
        relevant_episodes: list[str] = []
        relationship_context: list[str] = []

        global_memories = (
            await self._repository.list_memories(
                scope=MemoryScope(
                    kind=MemoryScopeKind.GLOBAL_USER,
                ),
            )
        )

        relationship_memories = (
            await self._repository.list_memories(
                domain=MemoryDomain.RELATIONSHIP,
                scope=MemoryScope(
                    kind=MemoryScopeKind.CHARACTER,
                    character_id=character_id,
                ),
            )
        )

        memories = (
            *global_memories,
            *relationship_memories,
        )

        for memory in memories:
            revision = (
                await self._repository.get_active_revision(
                    memory.memory_id
                )
            )

            if revision is None:
                continue

            if revision.content is None:
                continue

            if memory.domain is MemoryDomain.USER_PROFILE:
                if (
                    len(user_profile)
                    < self._policy.limit_for_domain(
                        memory.domain
                    )
                ):
                    user_profile.append(
                        revision.content
                    )

            elif (
                memory.domain
                is MemoryDomain.WORKING_CONTEXT
            ):
                if (
                    len(working_context)
                    < self._policy.limit_for_domain(
                        memory.domain
                    )
                ):
                    working_context.append(
                        revision.content
                    )

            elif memory.domain is MemoryDomain.EPISODIC:
                if (
                    len(relevant_episodes)
                    < self._policy.limit_for_domain(
                        memory.domain
                    )
                ):
                    relevant_episodes.append(
                        revision.content
                    )

            elif (
                memory.domain
                is MemoryDomain.RELATIONSHIP
            ):
                if (
                    len(relationship_context)
                    < self._policy.limit_for_domain(
                        memory.domain
                    )
                ):
                    relationship_context.append(
                        revision.content
                    )

        return PreparedMemoryContext(
            user_profile=tuple(user_profile),
            working_context=tuple(
                working_context
            ),
            relevant_episodes=tuple(
                relevant_episodes
            ),
            relationship_context=tuple(
                relationship_context
            ),
        )
