from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID


class MemoryDomain(Enum):
    """
    Factual Memory 的语义域。
    """

    USER_PROFILE = "user_profile"
    WORKING_CONTEXT = "working_context"
    EPISODIC = "episodic"
    RELATIONSHIP = "relationship"


class MemoryScopeKind(Enum):
    """
    Memory 的作用范围类型。
    """

    GLOBAL_USER = "global_user"
    CHARACTER = "character"


class MemoryLifecycle(Enum):
    """
    Memory Revision 的生命周期状态。
    """

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    DELETED = "deleted"


class MemorySource(Enum):
    """
    Memory 内容的来源类型。

    Source authority 的优先级策略属于后续
    conflict handling，不由 Enum 声明顺序决定。
    """

    USER_EDIT = "user_edit"
    USER_EXPLICIT = "user_explicit"
    AUTOMATIC_EXPLICIT_FACT = "automatic_explicit_fact"
    SYSTEM_OBSERVED = "system_observed"


def _normalize_aware_datetime(
    field_name: str,
    value: datetime,
) -> datetime:
    """
    验证 Memory 时间字段并统一规范为 UTC。
    """

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(
            f"MemoryRevision {field_name} "
            "must be timezone-aware"
        )

    return value.astimezone(UTC)


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MemoryScope:
    """
    单条 Memory 的作用范围。

    GLOBAL_USER 不绑定 Character；
    CHARACTER 必须绑定具体 character_id。
    """

    kind: MemoryScopeKind
    character_id: str | None = None

    def __post_init__(self) -> None:
        """
        保证 Scope 不进入不可能状态。
        """

        if self.kind is MemoryScopeKind.GLOBAL_USER:
            if self.character_id is not None:
                raise ValueError(
                    "MemoryScope GLOBAL_USER "
                    "must not define character_id"
                )

            return

        if (
            self.character_id is None
            or not self.character_id.strip()
        ):
            raise ValueError(
                "MemoryScope CHARACTER "
                "requires character_id"
            )


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class Memory:
    """
    一条逻辑 Memory 的稳定身份。

    内容本身保存在 MemoryRevision 中。
    同一 Memory 的多个 Revision 共用 memory_id、
    domain 和 scope。
    """

    memory_id: UUID
    domain: MemoryDomain
    scope: MemoryScope

    def __post_init__(self) -> None:
        """
        验证 Phase 4 已接受的 Domain / Scope 契约。
        """

        if self.domain is MemoryDomain.RELATIONSHIP:
            required_scope = MemoryScopeKind.CHARACTER
        else:
            required_scope = MemoryScopeKind.GLOBAL_USER

        if self.scope.kind is not required_scope:
            raise ValueError(
                f"Memory domain {self.domain.name} "
                f"requires {required_scope.name} scope"
            )


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MemoryRevision:
    """
    一条逻辑 Memory 的不可变内容版本。

    recorded_at 表示被系统记录的时间；
    occurred_at 表示事件实际发生时间，可不存在。
    """

    memory_id: UUID
    revision_number: int
    content: str | None
    source: MemorySource
    lifecycle: MemoryLifecycle
    recorded_at: datetime
    occurred_at: datetime | None = None

    def __post_init__(self) -> None:
        """
        验证 Revision 的最小领域约束。
        """

        if self.revision_number <= 0:
            raise ValueError(
                "MemoryRevision revision_number "
                "must be positive"
            )

        if self.lifecycle is MemoryLifecycle.DELETED:
            if self.content is not None:
                raise ValueError(
                    "Deleted MemoryRevision "
                    "must not retain content"
                )
        elif (
            self.content is None
            or not self.content.strip()
        ):
            raise ValueError(
                "MemoryRevision content "
                "must not be empty"
            )

        normalized_recorded_at = (
            _normalize_aware_datetime(
                "recorded_at",
                self.recorded_at,
            )
        )

        object.__setattr__(
            self,
            "recorded_at",
            normalized_recorded_at,
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
