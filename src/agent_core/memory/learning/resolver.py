from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from uuid import UUID

from agent_core.memory.learning.models import (
    MemoryCandidate,
)
from agent_core.memory.models import (
    Memory,
    MemoryDomain,
    MemoryIdentityKey,
    MemoryLifecycle,
    MemoryRevision,
    MemoryScope,
)


class ExistingMemoryResolutionKind(Enum):
    """
    Candidate 与 durable logical Memory 的关系。
    """

    NEW = "new"
    DUPLICATE = "duplicate"
    EXISTING = "existing"


class ExistingMemoryResolutionError(Exception):
    """
    Existing Memory Resolution 基础错误。
    """


class ExistingMemoryStateError(
    ExistingMemoryResolutionError
):
    """
    持久化 Memory 缺少 Resolver 所需的
    revision state。
    """


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class ExistingMemoryResolution:
    """
    ExistingMemoryResolver 的确定性结果。
    """

    kind: ExistingMemoryResolutionKind
    memory: Memory | None = None
    latest_revision: MemoryRevision | None = None

    def __post_init__(self) -> None:
        if (
            self.kind
            is ExistingMemoryResolutionKind.NEW
        ):
            if (
                self.memory is not None
                or self.latest_revision is not None
            ):
                raise ValueError(
                    "NEW resolution must not "
                    "contain existing Memory state"
                )

            return

        if (
            self.memory is None
            or self.latest_revision is None
        ):
            raise ValueError(
                "Existing resolution requires "
                "Memory and latest revision"
            )


class MemoryResolutionRepository(Protocol):
    """
    ExistingMemoryResolver 所需的最小读取边界。

    SQLiteMemoryRepository 通过结构化 typing
    满足此 Protocol。
    """

    async def find_memory_by_identity(
        self,
        *,
        domain: MemoryDomain,
        scope: MemoryScope,
        identity_key: MemoryIdentityKey,
    ) -> Memory | None:
        ...

    async def list_memories(
        self,
        *,
        domain: MemoryDomain | None = None,
        scope: MemoryScope | None = None,
    ) -> tuple[Memory, ...]:
        ...

    async def get_active_revision(
        self,
        memory_id: UUID,
    ) -> MemoryRevision | None:
        ...

    async def list_revisions(
        self,
        memory_id: UUID,
    ) -> tuple[MemoryRevision, ...]:
        ...


class ExistingMemoryResolver:
    """
    定位 Candidate 对应的 durable logical Memory。

    本层只负责 identity / duplicate resolution。

    不负责：
    - eligibility
    - conflict decision
    - persistence mutation
    """

    def __init__(
        self,
        repository: MemoryResolutionRepository,
    ) -> None:
        self._repository = repository

    async def resolve(
        self,
        candidate: MemoryCandidate,
    ) -> ExistingMemoryResolution:
        if candidate.identity_key is not None:
            memory = (
                await self._repository
                .find_memory_by_identity(
                    domain=candidate.domain,
                    scope=candidate.scope,
                    identity_key=candidate.identity_key,
                )
            )

            if memory is not None:
                latest_revision = (
                    await self._latest_revision(
                        memory
                    )
                )

                return self._existing_result(
                    candidate=candidate,
                    memory=memory,
                    latest_revision=latest_revision,
                )

        duplicate = (
            await self._find_exact_duplicate(
                candidate
            )
        )

        if duplicate is not None:
            memory, revision = duplicate

            return ExistingMemoryResolution(
                kind=(
                    ExistingMemoryResolutionKind
                    .DUPLICATE
                ),
                memory=memory,
                latest_revision=revision,
            )

        return ExistingMemoryResolution(
            kind=ExistingMemoryResolutionKind.NEW,
        )

    async def _latest_revision(
        self,
        memory: Memory,
    ) -> MemoryRevision:
        revisions = (
            await self._repository.list_revisions(
                memory.memory_id
            )
        )

        if not revisions:
            raise ExistingMemoryStateError(
                f"Memory {memory.memory_id} "
                "has no revisions"
            )

        return revisions[-1]

    def _existing_result(
        self,
        *,
        candidate: MemoryCandidate,
        memory: Memory,
        latest_revision: MemoryRevision,
    ) -> ExistingMemoryResolution:
        if self._is_exact_active_duplicate(
            candidate,
            latest_revision,
        ):
            kind = (
                ExistingMemoryResolutionKind.DUPLICATE
            )
        else:
            kind = (
                ExistingMemoryResolutionKind.EXISTING
            )

        return ExistingMemoryResolution(
            kind=kind,
            memory=memory,
            latest_revision=latest_revision,
        )

    async def _find_exact_duplicate(
        self,
        candidate: MemoryCandidate,
    ) -> tuple[
        Memory,
        MemoryRevision,
    ] | None:
        memories = (
            await self._repository.list_memories(
                domain=candidate.domain,
                scope=candidate.scope,
            )
        )

        for memory in memories:
            if (
                candidate.identity_key is not None
                and memory.identity_key is not None
            ):
                continue
            revision = (
                await self._repository
                .get_active_revision(
                    memory.memory_id
                )
            )

            if revision is None:
                continue

            if self._is_exact_active_duplicate(
                candidate,
                revision,
            ):
                return (
                    memory,
                    revision,
                )

        return None

    @staticmethod
    def _is_exact_active_duplicate(
        candidate: MemoryCandidate,
        revision: MemoryRevision,
    ) -> bool:
        if (
            revision.lifecycle
            is not MemoryLifecycle.ACTIVE
        ):
            return False

        if revision.content is None:
            return False

        return (
            candidate.content.strip()
            == revision.content.strip()
        )
