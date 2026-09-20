from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from agent_core.memory.models import (
    Memory,
    MemoryDomain,
    MemoryLifecycle,
    MemoryRevision,
    MemoryScope,
    MemorySource,
)
from agent_core.memory.repository import MemoryRepository
from agent_core.temporal import Clock


class MemoryGovernanceError(Exception):
    """
    Memory Governance use case 的基础异常。
    """


class MemoryNotFoundError(MemoryGovernanceError):
    """
    请求治理的逻辑 Memory 不存在。
    """


class MemoryStateError(MemoryGovernanceError):
    """
    持久化 Memory 处于无法治理的不完整状态。
    """


class MemoryDeletedError(MemoryStateError):
    """
    请求治理的 Memory 已进入 DELETED 状态。
    """


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MemoryGovernanceEntry:
    """
    Governance 读取单条 Memory 时的组合结果。

    latest_revision 表示持久化历史中的最新 Revision。
    Mutation use cases 会另外验证其 lifecycle 是否允许变更。
    """

    memory: Memory
    latest_revision: MemoryRevision


class MemoryGovernance(Protocol):
    """
    Memory Governance application capability contract.

    Callers depend on governance semantics rather than
    the concrete service or persistence implementation.
    """

    async def edit_memory(
        self,
        memory_id: UUID,
        new_content: str,
    ) -> MemoryGovernanceEntry:
        ...

    async def delete_memory(
        self,
        memory_id: UUID,
    ) -> MemoryGovernanceEntry:
        ...

    async def list_memories(
        self,
        *,
        domain: MemoryDomain | None = None,
        scope: MemoryScope | None = None,
    ) -> tuple[MemoryGovernanceEntry, ...]:
        ...

    async def inspect_memory(
        self,
        memory_id: UUID,
    ) -> MemoryGovernanceEntry:
        ...

    async def get_history(
        self,
        memory_id: UUID,
    ) -> tuple[MemoryRevision, ...]:
        ...


class MemoryGovernanceService:
    def __init__(
        self,
        repository: MemoryRepository,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._clock = clock

    async def edit_memory(
        self,
        memory_id: UUID,
        new_content: str,
    ) -> MemoryGovernanceEntry:
        """
        用户显式修改一条现有 ACTIVE Memory。
        """

        entry = await self.inspect_memory(
            memory_id
        )

        latest_revision = entry.latest_revision

        if (
            latest_revision.lifecycle
            is MemoryLifecycle.DELETED
        ):
            raise MemoryDeletedError(
                f"Memory {memory_id} is deleted"
            )

        if (
            latest_revision.lifecycle
            is not MemoryLifecycle.ACTIVE
        ):
            raise MemoryStateError(
                f"Memory {memory_id} latest revision "
                "is not ACTIVE"
            )

        new_revision = MemoryRevision(
            memory_id=memory_id,
            revision_number=(
                latest_revision.revision_number + 1
            ),
            content=new_content,
            source=MemorySource.USER_EDIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=self._clock.now(),
            occurred_at=latest_revision.occurred_at,
        )

        await self._repository.replace_active_revision(
            memory_id,
            new_revision,
        )

        return MemoryGovernanceEntry(
            memory=entry.memory,
            latest_revision=new_revision,
        )

    async def delete_memory(
        self,
        memory_id: UUID,
    ) -> MemoryGovernanceEntry:
        """
        用户显式删除一条现有 ACTIVE Memory。
        """

        entry = await self.inspect_memory(
            memory_id
        )

        latest_revision = entry.latest_revision

        if (
            latest_revision.lifecycle
            is MemoryLifecycle.DELETED
        ):
            raise MemoryDeletedError(
                f"Memory {memory_id} is deleted"
            )

        if (
            latest_revision.lifecycle
            is not MemoryLifecycle.ACTIVE
        ):
            raise MemoryStateError(
                f"Memory {memory_id} latest revision "
                "is not ACTIVE"
            )

        tombstone = MemoryRevision(
            memory_id=memory_id,
            revision_number=(
                latest_revision.revision_number + 1
            ),
            content=None,
            source=MemorySource.USER_EDIT,
            lifecycle=MemoryLifecycle.DELETED,
            recorded_at=self._clock.now(),
            occurred_at=None,
        )

        await self._repository.delete_memory(
            memory_id,
            tombstone,
        )

        return MemoryGovernanceEntry(
            memory=entry.memory,
            latest_revision=tombstone,
        )

    async def list_memories(
        self,
        *,
        domain: MemoryDomain | None = None,
        scope: MemoryScope | None = None,
    ) -> tuple[MemoryGovernanceEntry, ...]:
        """
        列出符合 Domain / Scope 条件的治理视图。

        这是治理视角，不执行 Agent Retrieval eligibility。
        """

        memories = await self._repository.list_memories(
            domain=domain,
            scope=scope,
        )

        entries: list[MemoryGovernanceEntry] = []

        for memory in memories:
            entries.append(
                await self._build_entry(memory)
            )

        return tuple(entries)

    async def inspect_memory(
        self,
        memory_id: UUID,
    ) -> MemoryGovernanceEntry:
        """
        查看单条逻辑 Memory 及其最新 Revision。
        """

        memory = await self._repository.get_memory(
            memory_id
        )

        if memory is None:
            raise MemoryNotFoundError(
                f"Memory {memory_id} does not exist"
            )

        return await self._build_entry(
            memory
        )

    async def get_history(
        self,
        memory_id: UUID,
    ) -> tuple[MemoryRevision, ...]:
        """
        查看指定 Memory 当前仍被持久化的 Revision 历史。
        """

        memory = await self._repository.get_memory(
            memory_id
        )

        if memory is None:
            raise MemoryNotFoundError(
                f"Memory {memory_id} does not exist"
            )

        revisions = (
            await self._repository.list_revisions(
                memory.memory_id
            )
        )

        if not revisions:
            raise MemoryStateError(
                f"Memory {memory_id} has no revisions"
            )

        return revisions

    async def _build_entry(
        self,
        memory: Memory,
    ) -> MemoryGovernanceEntry:
        revisions = (
            await self._repository.list_revisions(
                memory.memory_id
            )
        )

        if not revisions:
            raise MemoryStateError(
                f"Memory {memory.memory_id} "
                "has no revisions"
            )

        return MemoryGovernanceEntry(
            memory=memory,
            latest_revision=revisions[-1],
        )
