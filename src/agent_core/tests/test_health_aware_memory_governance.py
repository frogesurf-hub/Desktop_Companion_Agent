import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

import pytest

from agent_core.memory import (
    HealthAwareMemoryGovernanceService,
    MemoryCapability,
    MemoryDomain,
    MemoryGovernanceEntry,
    MemoryHealthStatus,
    MemoryHealthTracker,
    MemoryLifecycle,
    MemoryNotFoundError,
    MemoryRevision,
    MemoryScope,
    MemoryScopeKind,
    MemorySource,
)
from agent_core.memory.models import Memory

_MEMORY_ID = UUID(
    "12345678-1234-5678-1234-567812345678"
)

_TIMESTAMP = datetime(
    2026,
    9,
    20,
    12,
    0,
    tzinfo=UTC,
)


def _entry() -> MemoryGovernanceEntry:
    memory = Memory(
        memory_id=_MEMORY_ID,
        domain=MemoryDomain.USER_PROFILE,
        scope=MemoryScope(
            kind=MemoryScopeKind.GLOBAL_USER,
        ),
    )

    revision = MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=1,
        content="User prefers C#.",
        source=MemorySource.USER_EDIT,
        lifecycle=MemoryLifecycle.ACTIVE,
        recorded_at=_TIMESTAMP,
    )

    return MemoryGovernanceEntry(
        memory=memory,
        latest_revision=revision,
    )


class FakeGovernanceService:
    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error
        self.entry = _entry()

    async def edit_memory(
        self,
        memory_id: UUID,
        new_content: str,
    ) -> MemoryGovernanceEntry:
        if self.error is not None:
            raise self.error

        return self.entry

    async def delete_memory(
        self,
        memory_id: UUID,
    ) -> MemoryGovernanceEntry:
        if self.error is not None:
            raise self.error

        return self.entry

    async def list_memories(
        self,
        *,
        domain=None,
        scope=None,
    ):
        if self.error is not None:
            raise self.error

        return (
            self.entry,
        )

    async def inspect_memory(
        self,
        memory_id: UUID,
    ) -> MemoryGovernanceEntry:
        if self.error is not None:
            raise self.error

        return self.entry

    async def get_history(
        self,
        memory_id: UUID,
    ):
        if self.error is not None:
            raise self.error

        return (
            self.entry.latest_revision,
        )


def test_successful_governance_operation_recovers_health(
) -> None:
    health = MemoryHealthTracker()

    health.mark_degraded(
        MemoryCapability.GOVERNANCE,
        RuntimeError(
            "previous failure"
        ),
    )

    governance = HealthAwareMemoryGovernanceService(
        governance=FakeGovernanceService(),
        health=health,
    )

    entry = asyncio.run(
        governance.inspect_memory(
            _MEMORY_ID
        )
    )

    assert (
        entry.memory.memory_id
        == _MEMORY_ID
    )

    governance_health = (
        health.snapshot().governance
    )

    assert (
        governance_health.status
        is MemoryHealthStatus.AVAILABLE
    )

    assert (
        governance_health.last_error_type
        is None
    )


def test_edit_failure_is_fail_closed_and_degrades_health(
    caplog: pytest.LogCaptureFixture,
) -> None:
    health = MemoryHealthTracker()

    governance = HealthAwareMemoryGovernanceService(
        governance=FakeGovernanceService(
            error=RuntimeError(
                "sensitive-governance-content"
            )
        ),
        health=health,
    )

    with (
        caplog.at_level(
            logging.WARNING
        ),
        pytest.raises(
            RuntimeError,
            match="sensitive-governance-content",
        ),
    ):
        asyncio.run(
            governance.edit_memory(
                _MEMORY_ID,
                "private replacement content",
            )
        )

    governance_health = (
        health.snapshot().governance
    )

    assert (
        governance_health.status
        is MemoryHealthStatus.DEGRADED
    )

    assert (
        governance_health.last_error_type
        == "RuntimeError"
    )

    assert (
        "Memory governance failed: RuntimeError"
        in caplog.text
    )

    assert (
        "sensitive-governance-content"
        not in caplog.text
    )

    assert (
        "private replacement content"
        not in caplog.text
    )


def test_delete_failure_is_fail_closed_and_degrades_health(
) -> None:
    health = MemoryHealthTracker()

    governance = HealthAwareMemoryGovernanceService(
        governance=FakeGovernanceService(
            error=RuntimeError(
                "delete persistence failed"
            )
        ),
        health=health,
    )

    with pytest.raises(
        RuntimeError,
        match="delete persistence failed",
    ):
        asyncio.run(
            governance.delete_memory(
                _MEMORY_ID
            )
        )

    assert (
        health.snapshot().governance.status
        is MemoryHealthStatus.DEGRADED
    )


def test_domain_error_does_not_degrade_governance_health(
) -> None:
    health = MemoryHealthTracker()

    governance = HealthAwareMemoryGovernanceService(
        governance=FakeGovernanceService(
            error=MemoryNotFoundError(
                "memory does not exist"
            )
        ),
        health=health,
    )

    with pytest.raises(
        MemoryNotFoundError,
        match="does not exist",
    ):
        asyncio.run(
            governance.inspect_memory(
                _MEMORY_ID
            )
        )

    governance_health = (
        health.snapshot().governance
    )

    assert (
        governance_health.status
        is MemoryHealthStatus.AVAILABLE
    )

    assert (
        governance_health.last_error_type
        is None
    )


def test_domain_error_does_not_recover_degraded_governance_health(
) -> None:
    health = MemoryHealthTracker()

    health.mark_degraded(
        MemoryCapability.GOVERNANCE,
        RuntimeError(
            "previous persistence failure"
        ),
    )

    governance = HealthAwareMemoryGovernanceService(
        governance=FakeGovernanceService(
            error=MemoryNotFoundError(
                "memory does not exist"
            )
        ),
        health=health,
    )

    with pytest.raises(
        MemoryNotFoundError,
        match="does not exist",
    ):
        asyncio.run(
            governance.inspect_memory(
                _MEMORY_ID
            )
        )

    governance_health = (
        health.snapshot().governance
    )

    assert (
        governance_health.status
        is MemoryHealthStatus.DEGRADED
    )

    assert (
        governance_health.last_error_type
        == "RuntimeError"
    )
