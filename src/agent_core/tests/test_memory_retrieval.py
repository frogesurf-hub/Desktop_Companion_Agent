from dataclasses import FrozenInstanceError

import pytest

from agent_core.memory.retrieval import (
    PreparedMemoryContext,
)


def test_prepared_memory_context_defaults_to_empty() -> None:
    context = PreparedMemoryContext()

    assert context.user_profile == ()
    assert context.working_context == ()
    assert context.relevant_episodes == ()
    assert context.relationship_context == ()
    assert context.is_empty is True


def test_prepared_memory_context_reports_non_empty() -> None:
    context = PreparedMemoryContext(
        user_profile=(
            "User prefers concise technical explanations.",
        ),
    )

    assert context.is_empty is False


@pytest.mark.parametrize(
    "field_name",
    [
        "user_profile",
        "working_context",
        "relevant_episodes",
        "relationship_context",
    ],
)
def test_each_memory_section_makes_context_non_empty(
    field_name: str,
) -> None:
    context = PreparedMemoryContext(
        **{
            field_name: (
                "Relevant factual memory.",
            ),
        }
    )

    assert context.is_empty is False


def test_prepared_memory_context_preserves_domain_separation() -> None:
    context = PreparedMemoryContext(
        user_profile=(
            "User likes strategy games.",
        ),
        working_context=(
            "User is currently developing Phase 4.",
        ),
        relevant_episodes=(
            "User completed the previous Memory task.",
        ),
        relationship_context=(
            "The assistant previously helped with this project.",
        ),
    )

    assert context.user_profile == (
        "User likes strategy games.",
    )

    assert context.working_context == (
        "User is currently developing Phase 4.",
    )

    assert context.relevant_episodes == (
        "User completed the previous Memory task.",
    )

    assert context.relationship_context == (
        "The assistant previously helped with this project.",
    )


def test_prepared_memory_context_is_immutable() -> None:
    context = PreparedMemoryContext()

    with pytest.raises(FrozenInstanceError):
        setattr(
            context,
            "user_profile",
            ("Modified.",),
        )
