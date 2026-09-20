from agent_core.memory import (
    MemoryCapability,
    MemoryHealthStatus,
    MemoryHealthTracker,
)


def test_memory_health_starts_available() -> None:
    health = MemoryHealthTracker()

    snapshot = health.snapshot()

    assert (
        snapshot.status
        is MemoryHealthStatus.AVAILABLE
    )

    for capability in MemoryCapability:
        capability_health = (
            snapshot.for_capability(
                capability
            )
        )

        assert (
            capability_health.status
            is MemoryHealthStatus.AVAILABLE
        )

        assert (
            capability_health.last_error_type
            is None
        )


def test_degraded_capability_degrades_overall_memory_health(
) -> None:
    health = MemoryHealthTracker()

    health.mark_degraded(
        MemoryCapability.RETRIEVAL,
        RuntimeError(
            "simulated retrieval failure"
        ),
    )

    snapshot = health.snapshot()

    assert (
        snapshot.status
        is MemoryHealthStatus.DEGRADED
    )

    retrieval = snapshot.for_capability(
        MemoryCapability.RETRIEVAL
    )

    assert (
        retrieval.status
        is MemoryHealthStatus.DEGRADED
    )

    assert (
        retrieval.last_error_type
        == "RuntimeError"
    )

    assert (
        snapshot.automatic_learning.status
        is MemoryHealthStatus.AVAILABLE
    )

    assert (
        snapshot.governance.status
        is MemoryHealthStatus.AVAILABLE
    )


def test_unavailable_capability_makes_memory_unavailable(
) -> None:
    health = MemoryHealthTracker()

    health.mark_degraded(
        MemoryCapability.RETRIEVAL,
        RuntimeError(
            "temporary retrieval failure"
        ),
    )

    health.mark_unavailable(
        MemoryCapability.GOVERNANCE,
        OSError(
            "database unavailable"
        ),
    )

    snapshot = health.snapshot()

    assert (
        snapshot.status
        is MemoryHealthStatus.UNAVAILABLE
    )

    governance = snapshot.for_capability(
        MemoryCapability.GOVERNANCE
    )

    assert (
        governance.status
        is MemoryHealthStatus.UNAVAILABLE
    )

    assert (
        governance.last_error_type
        == "OSError"
    )


def test_capability_can_recover_independently(
) -> None:
    health = MemoryHealthTracker()

    health.mark_degraded(
        MemoryCapability.RETRIEVAL,
        RuntimeError(
            "temporary retrieval failure"
        ),
    )

    health.mark_degraded(
        MemoryCapability.AUTOMATIC_LEARNING,
        ValueError(
            "temporary learning failure"
        ),
    )

    health.mark_available(
        MemoryCapability.RETRIEVAL
    )

    snapshot = health.snapshot()

    assert (
        snapshot.retrieval.status
        is MemoryHealthStatus.AVAILABLE
    )

    assert (
        snapshot.retrieval.last_error_type
        is None
    )

    assert (
        snapshot.automatic_learning.status
        is MemoryHealthStatus.DEGRADED
    )

    assert (
        snapshot.status
        is MemoryHealthStatus.DEGRADED
    )
