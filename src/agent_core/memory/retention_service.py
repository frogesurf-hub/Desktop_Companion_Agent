from dataclasses import dataclass
from uuid import UUID

from agent_core.memory.models import (
    MemoryDomain,
)
from agent_core.memory.repository import MemoryRepository
from agent_core.memory.retention import MemoryRetentionPolicy
from agent_core.temporal import Clock


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MemoryRetentionResult:
    """
    一次 Retention 执行的结果。
    """

    checked_count: int
    expired_memory_ids: tuple[UUID, ...]


class MemoryRetentionService:
    """
    执行 Memory retention use case。

    Policy 负责判断是否到期。
    Repository 负责持久化状态变化。
    Service 只负责协调两者。
    """

    def __init__(
        self,
        repository: MemoryRepository,
        policy: MemoryRetentionPolicy,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._policy = policy
        self._clock = clock

    async def apply_due_expirations(
        self,
    ) -> MemoryRetentionResult:
        """
        检查所有 WORKING_CONTEXT Memory，
        并将已经到期的 ACTIVE Revision 标记为 EXPIRED。
        """

        memories = await self._repository.list_memories(
            domain=MemoryDomain.WORKING_CONTEXT,
        )

        now = self._clock.now()

        checked_count = 0
        expired_memory_ids: list[UUID] = []

        for memory in memories:
            active_revision = (
                await self._repository.get_active_revision(
                    memory.memory_id
                )
            )

            if active_revision is None:
                continue

            checked_count += 1

            if not self._policy.should_expire(
                memory,
                active_revision,
                now=now,
            ):
                continue

            await self._repository.expire_active_revision(
                memory.memory_id,
                active_revision.revision_number,
            )

            expired_memory_ids.append(
                memory.memory_id
            )

        return MemoryRetentionResult(
            checked_count=checked_count,
            expired_memory_ids=tuple(
                expired_memory_ids
            ),
        )
