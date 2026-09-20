from dataclasses import dataclass
from enum import Enum


class MemoryCapability(Enum):
    """
    Memory 子系统中可以独立判断健康状态的能力边界。
    """

    RETRIEVAL = "retrieval"
    AUTOMATIC_LEARNING = "automatic_learning"
    GOVERNANCE = "governance"


class MemoryHealthStatus(Enum):
    """
    单个 Memory capability 与整体 Memory 的健康状态。
    """

    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MemoryCapabilityHealth:
    """
    单个 Memory capability 的健康快照。
    """

    capability: MemoryCapability
    status: MemoryHealthStatus
    last_error_type: str | None = None


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MemoryHealthSnapshot:
    """
    Memory 子系统当前的只读健康快照。
    """

    retrieval: MemoryCapabilityHealth
    automatic_learning: MemoryCapabilityHealth
    governance: MemoryCapabilityHealth

    @property
    def status(self) -> MemoryHealthStatus:
        statuses = (
            self.retrieval.status,
            self.automatic_learning.status,
            self.governance.status,
        )

        if MemoryHealthStatus.UNAVAILABLE in statuses:
            return MemoryHealthStatus.UNAVAILABLE

        if MemoryHealthStatus.DEGRADED in statuses:
            return MemoryHealthStatus.DEGRADED

        return MemoryHealthStatus.AVAILABLE

    def for_capability(
        self,
        capability: MemoryCapability,
    ) -> MemoryCapabilityHealth:
        if capability is MemoryCapability.RETRIEVAL:
            return self.retrieval

        if (
            capability
            is MemoryCapability.AUTOMATIC_LEARNING
        ):
            return self.automatic_learning

        return self.governance


class MemoryHealthTracker:
    """
    Runtime 内存级 Memory health tracker。

    本类只记录 capability health，
    不负责重试、恢复、日志或业务决策。
    """

    def __init__(self) -> None:
        self._states = {
            capability: MemoryCapabilityHealth(
                capability=capability,
                status=MemoryHealthStatus.AVAILABLE,
            )
            for capability in MemoryCapability
        }

    def snapshot(self) -> MemoryHealthSnapshot:
        return MemoryHealthSnapshot(
            retrieval=self._states[
                MemoryCapability.RETRIEVAL
            ],
            automatic_learning=self._states[
                MemoryCapability.AUTOMATIC_LEARNING
            ],
            governance=self._states[
                MemoryCapability.GOVERNANCE
            ],
        )

    def mark_available(
        self,
        capability: MemoryCapability,
    ) -> None:
        self._states[capability] = (
            MemoryCapabilityHealth(
                capability=capability,
                status=MemoryHealthStatus.AVAILABLE,
            )
        )

    def mark_degraded(
        self,
        capability: MemoryCapability,
        error: Exception,
    ) -> None:
        self._states[capability] = (
            MemoryCapabilityHealth(
                capability=capability,
                status=MemoryHealthStatus.DEGRADED,
                last_error_type=type(error).__name__,
            )
        )

    def mark_unavailable(
        self,
        capability: MemoryCapability,
        error: Exception | None = None,
    ) -> None:
        self._states[capability] = (
            MemoryCapabilityHealth(
                capability=capability,
                status=MemoryHealthStatus.UNAVAILABLE,
                last_error_type=(
                    type(error).__name__
                    if error is not None
                    else None
                ),
            )
        )
