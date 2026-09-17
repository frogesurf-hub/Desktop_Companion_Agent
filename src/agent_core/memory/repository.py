from typing import Protocol
from uuid import UUID

from agent_core.memory.models import (
    Memory,
    MemoryDomain,
    MemoryRevision,
    MemoryScope,
)


class MemoryRepository(Protocol):
    """
    Memory durable persistence 的异步公共契约。

    上层 Memory use cases 只依赖这个边界，
    不依赖 SQLite、SQLAlchemy 或其他具体存储实现。
    """

    async def create_memory(
        self,
        memory: Memory,
        initial_revision: MemoryRevision,
    ) -> None:
        """
        原子创建逻辑 Memory 与第一版 Revision。
        """

        ...

    async def get_memory(
        self,
        memory_id: UUID,
    ) -> Memory | None:
        """
        按稳定 memory_id 读取逻辑 Memory。
        """

        ...

    async def list_memories(
        self,
        *,
        domain: MemoryDomain | None = None,
        scope: MemoryScope | None = None,
    ) -> tuple[Memory, ...]:
        """
        按可选 Domain / Scope 列出逻辑 Memory。
        """

        ...

    async def get_active_revision(
        self,
        memory_id: UUID,
    ) -> MemoryRevision | None:
        """
        读取指定 Memory 当前 ACTIVE Revision。
        """

        ...

    async def list_revisions(
        self,
        memory_id: UUID,
    ) -> tuple[MemoryRevision, ...]:
        """
        按 revision_number 顺序读取版本历史。
        """

        ...

    async def replace_active_revision(
        self,
        memory_id: UUID,
        new_revision: MemoryRevision,
    ) -> None:
        """
        原子 supersede 当前 ACTIVE Revision，
        并写入新的 ACTIVE Revision。

        是否应该发生语义上的冲突覆盖，
        不由 Repository 决定。
        """

        ...

    async def expire_active_revision(
        self,
        memory_id: UUID,
        expected_revision_number: int,
    ) -> None:
        """
        原子地将指定的当前 ACTIVE Revision 标记为 EXPIRED。

        只有当前 ACTIVE Revision 的 revision_number
        与 expected_revision_number 一致时才执行。
        """

        ...

    async def delete_memory(
        self,
        memory_id: UUID,
        tombstone_revision: MemoryRevision,
    ) -> None:
        """
        原子执行删除所需的数据清理与 tombstone 写入。

        用户是否允许删除属于 Governance；
        Repository 只保证持久化操作的原子性。
        """

        ...
