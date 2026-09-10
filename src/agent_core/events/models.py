from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class RuntimeEvent:
    """
    Agent Runtime 内部事件的统一元数据基础。

    事件表示已经发生的事实或通知，
    不承担命令、查询、权限或返回值语义。
    """

    source: str
    event_id: UUID = field(
        default_factory=uuid4,
    )
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )
    correlation_id: UUID | None = None
    causation_id: UUID | None = None

    def __post_init__(self) -> None:
        """
        验证并规范化 Runtime Event 的公共元数据。
        """

        if not self.source.strip():
            raise ValueError(
                "RuntimeEvent source must not be empty"
            )

        if (
            self.occurred_at.tzinfo is None
            or self.occurred_at.utcoffset() is None
        ):
            raise ValueError(
                "RuntimeEvent occurred_at must be timezone-aware"
            )

        object.__setattr__(
            self,
            "occurred_at",
            self.occurred_at.astimezone(UTC),
        )
