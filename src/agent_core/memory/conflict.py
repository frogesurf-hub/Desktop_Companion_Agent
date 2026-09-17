from datetime import datetime
from enum import Enum

from agent_core.memory.models import (
    MemoryLifecycle,
    MemoryRevision,
    MemorySource,
)


class MemoryConflictDecision(Enum):
    """
    Conflict Policy 对候选 Revision 的决策。
    """

    REPLACE = "replace"
    KEEP_CURRENT = "keep_current"


_SOURCE_AUTHORITY = {
    MemorySource.USER_EDIT: 4,
    MemorySource.USER_EXPLICIT: 3,
    MemorySource.AUTOMATIC_EXPLICIT_FACT: 2,
    MemorySource.SYSTEM_OBSERVED: 1,
}


def _fact_time(
    revision: MemoryRevision,
) -> datetime:
    """
    返回用于比较事实新旧的时间。

    如果知道事实实际发生时间，优先使用 occurred_at；
    否则退回系统记录时间 recorded_at。
    """

    if revision.occurred_at is not None:
        return revision.occurred_at

    return revision.recorded_at


class MemoryConflictPolicy:
    """
    Phase 4 factual Memory 的确定性冲突规则。

    本层只决定是否允许 replacement，
    不执行持久化，不负责寻找语义冲突候选。
    """

    def decide(
        self,
        current_revision: MemoryRevision,
        incoming_revision: MemoryRevision,
    ) -> MemoryConflictDecision:
        self._validate_revisions(
            current_revision,
            incoming_revision,
        )

        current_authority = _SOURCE_AUTHORITY[
            current_revision.source
        ]

        incoming_authority = _SOURCE_AUTHORITY[
            incoming_revision.source
        ]

        if incoming_authority > current_authority:
            return MemoryConflictDecision.REPLACE

        if incoming_authority < current_authority:
            return MemoryConflictDecision.KEEP_CURRENT

        if (
            _fact_time(incoming_revision)
            > _fact_time(current_revision)
        ):
            return MemoryConflictDecision.REPLACE

        return MemoryConflictDecision.KEEP_CURRENT

    @staticmethod
    def _validate_revisions(
        current_revision: MemoryRevision,
        incoming_revision: MemoryRevision,
    ) -> None:
        if (
            current_revision.memory_id
            != incoming_revision.memory_id
        ):
            raise ValueError(
                "Conflict revisions must belong "
                "to the same Memory"
            )

        if (
            current_revision.lifecycle
            is not MemoryLifecycle.ACTIVE
        ):
            raise ValueError(
                "Current conflict revision "
                "must be ACTIVE"
            )

        if (
            incoming_revision.lifecycle
            is not MemoryLifecycle.ACTIVE
        ):
            raise ValueError(
                "Incoming conflict revision "
                "must be ACTIVE"
            )
