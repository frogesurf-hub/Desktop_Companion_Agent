import logging
from uuid import UUID

from agent_core.memory.governance import (
    MemoryGovernance,
    MemoryGovernanceEntry,
    MemoryGovernanceError,
)
from agent_core.memory.health import (
    MemoryCapability,
    MemoryHealthTracker,
)
from agent_core.memory.models import (
    MemoryDomain,
    MemoryRevision,
    MemoryScope,
)

logger = logging.getLogger(__name__)


class HealthAwareMemoryGovernanceService:
    """
    Memory Governance health / observability boundary.

    Governance remains fail-closed:
    unexpected failures are recorded in Memory Health
    and then re-raised to the caller.
    """

    def __init__(
        self,
        *,
        governance: MemoryGovernance,
        health: MemoryHealthTracker,
    ) -> None:
        self._governance = governance
        self._health = health

    async def edit_memory(
        self,
        memory_id: UUID,
        new_content: str,
    ) -> MemoryGovernanceEntry:
        try:
            result = await self._governance.edit_memory(
                memory_id,
                new_content,
            )

        except MemoryGovernanceError:
            raise

        except Exception as exc:
            self._record_failure(
                exc
            )
            raise

        self._record_success()

        return result

    async def delete_memory(
        self,
        memory_id: UUID,
    ) -> MemoryGovernanceEntry:
        try:
            result = await self._governance.delete_memory(
                memory_id
            )

        except MemoryGovernanceError:
            raise

        except Exception as exc:
            self._record_failure(
                exc
            )
            raise

        self._record_success()

        return result

    async def list_memories(
        self,
        *,
        domain: MemoryDomain | None = None,
        scope: MemoryScope | None = None,
    ) -> tuple[MemoryGovernanceEntry, ...]:
        try:
            result = await self._governance.list_memories(
                domain=domain,
                scope=scope,
            )

        except MemoryGovernanceError:
            raise

        except Exception as exc:
            self._record_failure(
                exc
            )
            raise

        self._record_success()

        return result

    async def inspect_memory(
        self,
        memory_id: UUID,
    ) -> MemoryGovernanceEntry:
        try:
            result = await self._governance.inspect_memory(
                memory_id
            )

        except MemoryGovernanceError:
            raise

        except Exception as exc:
            self._record_failure(
                exc
            )
            raise

        self._record_success()

        return result

    async def get_history(
        self,
        memory_id: UUID,
    ) -> tuple[MemoryRevision, ...]:
        try:
            result = await self._governance.get_history(
                memory_id
            )

        except MemoryGovernanceError:
            raise

        except Exception as exc:
            self._record_failure(
                exc
            )
            raise

        self._record_success()

        return result

    def _record_success(self) -> None:
        self._health.mark_available(
            MemoryCapability.GOVERNANCE
        )

    def _record_failure(
        self,
        error: Exception,
    ) -> None:
        self._health.mark_degraded(
            MemoryCapability.GOVERNANCE,
            error,
        )

        logger.warning(
            "Memory governance failed: %s",
            type(error).__name__,
        )
