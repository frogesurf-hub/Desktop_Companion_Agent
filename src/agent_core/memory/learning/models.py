from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from agent_core.memory.models import (
    MemoryDomain,
    MemoryScope,
    MemorySource,
)


def _normalize_aware_datetime(
    field_name: str,
    value: datetime,
) -> datetime:
    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(UTC)


def _require_non_blank(
    field_name: str,
    value: str,
) -> None:
    if not value.strip():
        raise ValueError(
            f"{field_name} must not be empty"
        )


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MemoryLearningInput:
    """
    一次自动 Memory Learning 的运行时输入。

    只包含已经存在于当前 runtime 的事实数据，
    不引入 Conversation / Session 子系统。
    """

    source_message_id: str
    user_text: str
    assistant_text: str
    active_character_id: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        _require_non_blank(
            "source_message_id",
            self.source_message_id,
        )

        _require_non_blank(
            "user_text",
            self.user_text,
        )

        _require_non_blank(
            "active_character_id",
            self.active_character_id,
        )

        normalized_occurred_at = (
            _normalize_aware_datetime(
                "occurred_at",
                self.occurred_at,
            )
        )

        object.__setattr__(
            self,
            "occurred_at",
            normalized_occurred_at,
        )


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MemoryCandidate:
    """
    尚未被确认或持久化的 factual Memory 候选。

    Candidate 不是 Memory，
    不能参与 Retrieval，
    也没有持久化权限。
    """

    candidate_id: UUID
    content: str
    domain: MemoryDomain
    scope: MemoryScope
    source: MemorySource
    source_message_id: str
    created_at: datetime
    occurred_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_non_blank(
            "content",
            self.content,
        )

        _require_non_blank(
            "source_message_id",
            self.source_message_id,
        )

        normalized_created_at = (
            _normalize_aware_datetime(
                "created_at",
                self.created_at,
            )
        )

        object.__setattr__(
            self,
            "created_at",
            normalized_created_at,
        )

        if self.occurred_at is not None:
            normalized_occurred_at = (
                _normalize_aware_datetime(
                    "occurred_at",
                    self.occurred_at,
                )
            )

            object.__setattr__(
                self,
                "occurred_at",
                normalized_occurred_at,
            )
