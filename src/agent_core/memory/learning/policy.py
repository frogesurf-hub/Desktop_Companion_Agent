from dataclasses import dataclass
from enum import Enum

from agent_core.memory.learning.models import (
    MemoryCandidate,
    MemoryLearningInput,
)
from agent_core.memory.models import (
    MemoryDomain,
    MemoryScopeKind,
    MemorySource,
)


class MemoryEligibilityReason(Enum):
    """
    Automatic Memory Learning 的资格判断结果。

    ELIGIBLE 表示 Candidate 可以进入下一阶段。
    其他值表示确定性的拒绝原因。
    """

    ELIGIBLE = "eligible"
    UNSUPPORTED_SOURCE = "unsupported_source"
    SOURCE_MESSAGE_MISMATCH = "source_message_mismatch"
    DOMAIN_SCOPE_MISMATCH = "domain_scope_mismatch"
    ACTIVE_CHARACTER_MISMATCH = (
        "active_character_mismatch"
    )


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MemoryEligibilityResult:
    """
    MemoryCandidate 的资格判断结果。
    """

    reason: MemoryEligibilityReason

    @property
    def eligible(self) -> bool:
        return (
            self.reason
            is MemoryEligibilityReason.ELIGIBLE
        )


class MemoryLearningPolicy:
    """
    Automatic Memory Learning 的确定性资格策略。

    这里只验证 Candidate 是否满足进入后续
    Resolution / Conflict / Persistence 流程的条件。

    不负责：
    - 自然语言 Candidate extraction
    - Existing Memory resolution
    - Conflict handling
    - Persistence
    """

    def evaluate(
        self,
        candidate: MemoryCandidate,
        *,
        learning_input: MemoryLearningInput,
    ) -> MemoryEligibilityResult:
        """
        判断 Candidate 是否允许继续进入学习流水线。
        """

        if (
            candidate.source
            is not MemorySource.AUTOMATIC_EXPLICIT_FACT
        ):
            return MemoryEligibilityResult(
                reason=(
                    MemoryEligibilityReason.UNSUPPORTED_SOURCE
                ),
            )

        if (
            candidate.source_message_id
            != learning_input.source_message_id
        ):
            return MemoryEligibilityResult(
                reason=(
                    MemoryEligibilityReason
                    .SOURCE_MESSAGE_MISMATCH
                ),
            )

        if (
            candidate.domain
            is MemoryDomain.RELATIONSHIP
        ):
            required_scope = (
                MemoryScopeKind.CHARACTER
            )
        else:
            required_scope = (
                MemoryScopeKind.GLOBAL_USER
            )

        if candidate.scope.kind is not required_scope:
            return MemoryEligibilityResult(
                reason=(
                    MemoryEligibilityReason
                    .DOMAIN_SCOPE_MISMATCH
                ),
            )

        if (
            candidate.domain
            is MemoryDomain.RELATIONSHIP
            and candidate.scope.character_id
            != learning_input.active_character_id
        ):
            return MemoryEligibilityResult(
                reason=(
                    MemoryEligibilityReason
                    .ACTIVE_CHARACTER_MISMATCH
                ),
            )

        return MemoryEligibilityResult(
            reason=MemoryEligibilityReason.ELIGIBLE,
        )
