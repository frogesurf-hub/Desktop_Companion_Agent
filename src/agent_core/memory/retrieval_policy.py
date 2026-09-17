from dataclasses import dataclass

from agent_core.memory.models import (
    MemoryDomain,
)


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MemoryRetrievalLimits:
    """
    Retrieval 阶段的数量限制。

    防止过多 Memory 进入 Prompt Context。
    """

    max_user_profile: int = 10
    max_working_context: int = 10
    max_relevant_episodes: int = 5
    max_relationship_context: int = 5


@dataclass(
    frozen=True,
    slots=True,
)
class MemoryRetrievalPolicy:
    """
    定义 Memory Retrieval 的规则。
    """

    limits: MemoryRetrievalLimits

    def limit_for_domain(
        self,
        domain: MemoryDomain,
    ) -> int:
        if domain.name == "USER_PROFILE":
            return self.limits.max_user_profile

        if domain.name == "WORKING_CONTEXT":
            return self.limits.max_working_context

        if domain.name == "EPISODIC":
            return self.limits.max_relevant_episodes

        if domain.name == "RELATIONSHIP":
            return self.limits.max_relationship_context

        return 0
