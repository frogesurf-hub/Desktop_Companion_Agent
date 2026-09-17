from agent_core.memory.models import (
    MemoryDomain,
)
from agent_core.memory.retrieval_policy import (
    MemoryRetrievalLimits,
    MemoryRetrievalPolicy,
)


def test_default_limits_are_defined() -> None:
    limits = MemoryRetrievalLimits()

    assert limits.max_user_profile == 10
    assert limits.max_working_context == 10
    assert limits.max_relevant_episodes == 5
    assert limits.max_relationship_context == 5


def test_policy_returns_limit_for_each_domain() -> None:
    policy = MemoryRetrievalPolicy(
        limits=MemoryRetrievalLimits(),
    )

    assert (
        policy.limit_for_domain(
            MemoryDomain.USER_PROFILE,
        )
        == 10
    )

    assert (
        policy.limit_for_domain(
            MemoryDomain.WORKING_CONTEXT,
        )
        == 10
    )

    assert (
        policy.limit_for_domain(
            MemoryDomain.EPISODIC,
        )
        == 5
    )

    assert (
        policy.limit_for_domain(
            MemoryDomain.RELATIONSHIP,
        )
        == 5
    )
