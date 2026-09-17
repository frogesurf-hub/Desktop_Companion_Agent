from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from agent_core.memory.models import (
    Memory,
    MemoryDomain,
    MemoryLifecycle,
    MemoryRevision,
)


def _normalize_evaluation_time(
    value: datetime,
) -> datetime:
    """
    验证 Retention evaluation time 并统一为 UTC。
    """

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(
            "Retention evaluation time "
            "must be timezone-aware"
        )

    return value.astimezone(UTC)


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MemoryRetentionPolicy:
    """
    Phase 4 factual Memory retention 规则。

    当前只有 WORKING_CONTEXT 自动过期。
    这里只计算规则，不执行持久化 mutation。
    """

    working_context_retention_days: int

    def __post_init__(self) -> None:
        if not (
            1
            <= self.working_context_retention_days
            <= 30
        ):
            raise ValueError(
                "working_context_retention_days "
                "must be between 1 and 30"
            )

    def expiration_deadline(
        self,
        memory: Memory,
        revision: MemoryRevision,
    ) -> datetime | None:
        """
        返回当前 Revision 的 retention deadline。

        没有自动过期策略的 Domain 返回 None。
        """

        self._validate_memory_revision_pair(
            memory,
            revision,
        )

        if (
            memory.domain
            is not MemoryDomain.WORKING_CONTEXT
        ):
            return None

        return (
            revision.recorded_at
            + timedelta(
                days=self.working_context_retention_days
            )
        )

    def should_expire(
        self,
        memory: Memory,
        revision: MemoryRevision,
        *,
        now: datetime,
    ) -> bool:
        """
        判断一个 ACTIVE Revision 当前是否应该过期。
        """

        self._validate_memory_revision_pair(
            memory,
            revision,
        )

        if (
            revision.lifecycle
            is not MemoryLifecycle.ACTIVE
        ):
            return False

        deadline = self.expiration_deadline(
            memory,
            revision,
        )

        if deadline is None:
            return False

        current_time = _normalize_evaluation_time(
            now
        )

        return current_time >= deadline

    @staticmethod
    def _validate_memory_revision_pair(
        memory: Memory,
        revision: MemoryRevision,
    ) -> None:
        if revision.memory_id != memory.memory_id:
            raise ValueError(
                "MemoryRevision memory_id "
                "must match Memory memory_id"
            )
