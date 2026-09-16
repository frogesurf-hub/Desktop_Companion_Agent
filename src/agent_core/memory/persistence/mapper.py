from datetime import datetime
from uuid import UUID

from agent_core.memory.models import (
    Memory,
    MemoryDomain,
    MemoryLifecycle,
    MemoryRevision,
    MemoryScope,
    MemoryScopeKind,
    MemorySource,
)
from agent_core.memory.persistence.orm import (
    MemoryRevisionRow,
    MemoryRow,
)


def memory_to_row(
    memory: Memory,
) -> MemoryRow:
    """
    将 Domain Memory 转换为 Persistence Row。
    """

    return MemoryRow(
        memory_id=str(memory.memory_id),
        domain=memory.domain.value,
        scope_kind=memory.scope.kind.value,
        character_id=memory.scope.character_id,
    )


def row_to_memory(
    row: MemoryRow,
) -> Memory:
    """
    将 Persistence Row 恢复为 Domain Memory。
    """

    scope = MemoryScope(
        kind=MemoryScopeKind(row.scope_kind),
        character_id=row.character_id,
    )

    return Memory(
        memory_id=UUID(row.memory_id),
        domain=MemoryDomain(row.domain),
        scope=scope,
    )


def revision_to_row(
    revision: MemoryRevision,
) -> MemoryRevisionRow:
    """
    将 Domain Revision 转换为 Persistence Row。
    """

    return MemoryRevisionRow(
        memory_id=str(revision.memory_id),
        revision_number=revision.revision_number,
        content=revision.content,
        source=revision.source.value,
        lifecycle=revision.lifecycle.value,
        recorded_at=revision.recorded_at.isoformat(),
        occurred_at=(
            revision.occurred_at.isoformat()
            if revision.occurred_at is not None
            else None
        ),
    )


def row_to_revision(
    row: MemoryRevisionRow,
) -> MemoryRevision:
    """
    将 Persistence Row 恢复为 Domain Revision。
    """

    return MemoryRevision(
        memory_id=UUID(row.memory_id),
        revision_number=row.revision_number,
        content=row.content,
        source=MemorySource(row.source),
        lifecycle=MemoryLifecycle(row.lifecycle),
        recorded_at=datetime.fromisoformat(
            row.recorded_at
        ),
        occurred_at=(
            datetime.fromisoformat(row.occurred_at)
            if row.occurred_at is not None
            else None
        ),
    )
