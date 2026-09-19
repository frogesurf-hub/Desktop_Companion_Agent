from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from uuid import UUID, uuid4

from agent_core.memory.conflict import (
    MemoryConflictDecision,
    MemoryConflictPolicy,
)
from agent_core.memory.learning.models import (
    MemoryCandidate,
    MemoryLearningInput,
)
from agent_core.memory.learning.policy import (
    MemoryEligibilityResult,
    MemoryLearningPolicy,
)
from agent_core.memory.learning.resolver import (
    ExistingMemoryResolution,
    ExistingMemoryResolutionKind,
)
from agent_core.memory.models import (
    Memory,
    MemoryIdentityKey,
    MemoryLifecycle,
    MemoryRevision,
)


class MemoryLearningOutcome(Enum):
    """
    单个 Candidate 经过 Learning Service 后的结果。
    """

    REJECTED = "rejected"
    CREATED = "created"
    DUPLICATE = "duplicate"
    IDENTITY_ADOPTED = "identity_adopted"
    REPLACED = "replaced"
    REACTIVATED = "reactivated"
    KEPT_CURRENT = "kept_current"
    BLOCKED_DELETED = "blocked_deleted"


class MemoryLearningStateError(Exception):
    """
    Learning pipeline 遇到无法安全处理的
    durable Memory 状态。
    """


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class MemoryLearningResult:
    """
    单个 Candidate 的自动学习结果。
    """

    outcome: MemoryLearningOutcome
    eligibility: MemoryEligibilityResult
    memory: Memory | None = None
    revision: MemoryRevision | None = None

    def __post_init__(self) -> None:
        if (
            self.outcome
            is MemoryLearningOutcome.REJECTED
        ):
            if self.eligibility.eligible:
                raise ValueError(
                    "REJECTED learning result "
                    "must be ineligible"
                )

            if (
                self.memory is not None
                or self.revision is not None
            ):
                raise ValueError(
                    "REJECTED learning result must not "
                    "contain durable Memory state"
                )

            return

        if not self.eligibility.eligible:
            raise ValueError(
                "Accepted learning result "
                "must be eligible"
            )

        if (
            self.memory is None
            or self.revision is None
        ):
            raise ValueError(
                "Accepted learning result requires "
                "Memory and revision"
            )


class MemoryCandidateResolver(Protocol):
    """
    Learning Service 所需的 Candidate resolution 边界。
    """

    async def resolve(
        self,
        candidate: MemoryCandidate,
    ) -> ExistingMemoryResolution:
        ...


class MemoryLearningRepository(Protocol):
    """
    Task 7D Learning Service 所需的最小写入边界。
    """

    async def create_memory(
        self,
        memory: Memory,
        initial_revision: MemoryRevision,
    ) -> None:
        ...

    async def replace_active_revision(
        self,
        memory_id: UUID,
        new_revision: MemoryRevision,
    ) -> None:
        ...

    async def adopt_identity_key(
        self,
        memory_id: UUID,
        identity_key: MemoryIdentityKey,
    ) -> None:
        ...

    async def reactivate_memory(
        self,
        memory_id: UUID,
        new_revision: MemoryRevision,
    ) -> None:
        ...


class MemoryLearningService:
    """
    Automatic Memory Learning 的用例编排边界。

    本层负责：
    Eligibility
    → Resolution
    → Conflict
    → Durable mutation

    不负责：
    - Candidate extraction
    - SQL / SQLite implementation
    - Prompt composition
    - Runtime failure isolation
    """

    def __init__(
        self,
        *,
        repository: MemoryLearningRepository,
        policy: MemoryLearningPolicy,
        resolver: MemoryCandidateResolver,
        conflict_policy: MemoryConflictPolicy,
    ) -> None:
        self._repository = repository
        self._policy = policy
        self._resolver = resolver
        self._conflict_policy = conflict_policy

    async def learn_candidate(
        self,
        candidate: MemoryCandidate,
        *,
        learning_input: MemoryLearningInput,
    ) -> MemoryLearningResult:
        eligibility = self._policy.evaluate(
            candidate,
            learning_input=learning_input,
        )

        if not eligibility.eligible:
            return MemoryLearningResult(
                outcome=MemoryLearningOutcome.REJECTED,
                eligibility=eligibility,
            )

        resolution = await self._resolver.resolve(
            candidate
        )

        if (
            resolution.kind
            is ExistingMemoryResolutionKind.NEW
        ):
            return await self._create_memory(
                candidate,
                eligibility=eligibility,
            )

        memory, current_revision = (
            self._require_existing_state(
                resolution
            )
        )

        if (
            resolution.kind
            is ExistingMemoryResolutionKind.DUPLICATE
        ):
            if (
                candidate.identity_key is not None
                and memory.identity_key is None
            ):
                await self._repository.adopt_identity_key(
                    memory.memory_id,
                    candidate.identity_key,
                )

                adopted_memory = Memory(
                    memory_id=memory.memory_id,
                    domain=memory.domain,
                    scope=memory.scope,
                    identity_key=candidate.identity_key,
                )

                return MemoryLearningResult(
                    outcome=(
                        MemoryLearningOutcome
                        .IDENTITY_ADOPTED
                    ),
                    eligibility=eligibility,
                    memory=adopted_memory,
                    revision=current_revision,
                )

            return MemoryLearningResult(
                outcome=MemoryLearningOutcome.DUPLICATE,
                eligibility=eligibility,
                memory=memory,
                revision=current_revision,
            )

        if (
            resolution.kind
            is not ExistingMemoryResolutionKind.EXISTING
        ):
            raise MemoryLearningStateError(
                "Unsupported existing-memory "
                "resolution"
            )

        if (
            current_revision.lifecycle
            is MemoryLifecycle.DELETED
        ):
            return MemoryLearningResult(
                outcome=(
                    MemoryLearningOutcome
                    .BLOCKED_DELETED
                ),
                eligibility=eligibility,
                memory=memory,
                revision=current_revision,
            )

        if (
            current_revision.lifecycle
            is MemoryLifecycle.EXPIRED
        ):
            incoming_revision = (
                self._build_revision(
                    candidate,
                    memory_id=memory.memory_id,
                    revision_number=(
                        current_revision.revision_number
                        + 1
                    ),
                )
            )

            await self._repository.reactivate_memory(
                memory.memory_id,
                incoming_revision,
            )

            return MemoryLearningResult(
                outcome=(
                    MemoryLearningOutcome.REACTIVATED
                ),
                eligibility=eligibility,
                memory=memory,
                revision=incoming_revision,
            )

        if (
            current_revision.lifecycle
            is not MemoryLifecycle.ACTIVE
        ):
            raise MemoryLearningStateError(
                "Existing Memory latest revision "
                "has unsupported lifecycle"
            )

        incoming_revision = (
            self._build_revision(
                candidate,
                memory_id=memory.memory_id,
                revision_number=(
                    current_revision.revision_number
                    + 1
                ),
            )
        )

        decision = self._conflict_policy.decide(
            current_revision,
            incoming_revision,
        )

        if (
            decision
            is MemoryConflictDecision.KEEP_CURRENT
        ):
            return MemoryLearningResult(
                outcome=(
                    MemoryLearningOutcome.KEPT_CURRENT
                ),
                eligibility=eligibility,
                memory=memory,
                revision=current_revision,
            )

        await self._repository.replace_active_revision(
            memory.memory_id,
            incoming_revision,
        )

        return MemoryLearningResult(
            outcome=MemoryLearningOutcome.REPLACED,
            eligibility=eligibility,
            memory=memory,
            revision=incoming_revision,
        )

    async def _create_memory(
        self,
        candidate: MemoryCandidate,
        *,
        eligibility: MemoryEligibilityResult,
    ) -> MemoryLearningResult:
        memory = Memory(
            memory_id=uuid4(),
            domain=candidate.domain,
            scope=candidate.scope,
            identity_key=candidate.identity_key,
        )

        revision = self._build_revision(
            candidate,
            memory_id=memory.memory_id,
            revision_number=1,
        )

        await self._repository.create_memory(
            memory,
            revision,
        )

        return MemoryLearningResult(
            outcome=MemoryLearningOutcome.CREATED,
            eligibility=eligibility,
            memory=memory,
            revision=revision,
        )

    @staticmethod
    def _build_revision(
        candidate: MemoryCandidate,
        *,
        memory_id: UUID,
        revision_number: int,
    ) -> MemoryRevision:
        return MemoryRevision(
            memory_id=memory_id,
            revision_number=revision_number,
            content=candidate.content,
            source=candidate.source,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=candidate.created_at,
            occurred_at=candidate.occurred_at,
        )

    @staticmethod
    def _require_existing_state(
        resolution: ExistingMemoryResolution,
    ) -> tuple[
        Memory,
        MemoryRevision,
    ]:
        if (
            resolution.memory is None
            or resolution.latest_revision is None
        ):
            raise MemoryLearningStateError(
                "Existing resolution is missing "
                "durable Memory state"
            )

        return (
            resolution.memory,
            resolution.latest_revision,
        )
