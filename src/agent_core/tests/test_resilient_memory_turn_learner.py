import asyncio
import logging
from datetime import UTC, datetime

import pytest

from agent_core.core.message import Message
from agent_core.memory import (
    MemoryCapability,
    MemoryHealthStatus,
    MemoryHealthTracker,
)
from agent_core.memory.learning import (
    MemoryLearningInput,
    ResilientMemoryTurnLearner,
)
from agent_core.providers import LLMResponse
from agent_core.tests.fakes import (
    FakeLLMProvider,
    FakeMemoryTurnLearner,
    create_test_agent,
)

_TIMESTAMP = datetime(
    2026,
    9,
    20,
    12,
    0,
    tzinfo=UTC,
)


class FailingMemoryTurnLearner:
    async def learn_turn(
        self,
        learning_input: MemoryLearningInput,
    ) -> None:
        raise RuntimeError(
            "sensitive-learning-content"
        )


def _learning_input() -> MemoryLearningInput:
    return MemoryLearningInput(
        source_message_id="message-1",
        user_text="private user fact",
        assistant_text="private assistant response",
        active_character_id="aria",
        occurred_at=_TIMESTAMP,
    )


def test_successful_learning_recovers_health(
) -> None:
    delegate = FakeMemoryTurnLearner()

    health = MemoryHealthTracker()

    health.mark_degraded(
        MemoryCapability.AUTOMATIC_LEARNING,
        RuntimeError(
            "previous learning failure"
        ),
    )

    learner = ResilientMemoryTurnLearner(
        learner=delegate,
        health=health,
    )

    learning_input = _learning_input()

    asyncio.run(
        learner.learn_turn(
            learning_input
        )
    )

    assert delegate.inputs == [
        learning_input,
    ]

    learning_health = (
        health.snapshot().automatic_learning
    )

    assert (
        learning_health.status
        is MemoryHealthStatus.AVAILABLE
    )

    assert (
        learning_health.last_error_type
        is None
    )


def test_learning_failure_is_contained_and_degrades_health(
    caplog: pytest.LogCaptureFixture,
) -> None:
    health = MemoryHealthTracker()

    learner = ResilientMemoryTurnLearner(
        learner=FailingMemoryTurnLearner(),
        health=health,
    )

    with caplog.at_level(
        logging.WARNING
    ):
        asyncio.run(
            learner.learn_turn(
                _learning_input()
            )
        )

    learning_health = (
        health.snapshot().automatic_learning
    )

    assert (
        learning_health.status
        is MemoryHealthStatus.DEGRADED
    )

    assert (
        learning_health.last_error_type
        == "RuntimeError"
    )

    assert (
        "Automatic Memory learning failed: RuntimeError"
        in caplog.text
    )

    assert (
        "sensitive-learning-content"
        not in caplog.text
    )

    assert (
        "private user fact"
        not in caplog.text
    )

    assert (
        "private assistant response"
        not in caplog.text
    )


def test_agent_response_survives_automatic_learning_failure(
) -> None:
    provider = FakeLLMProvider(
        response=LLMResponse(
            content="valid provider response",
        ),
    )

    health = MemoryHealthTracker()

    learner = ResilientMemoryTurnLearner(
        learner=FailingMemoryTurnLearner(),
        health=health,
    )

    agent = create_test_agent(
        provider,
        memory_learner=learner,
    )

    response = asyncio.run(
        agent.process_message(
            Message(
                id="message-1",
                type="chat",
                source="desktop",
                payload={
                    "message": "remember this fact",
                },
            )
        )
    )

    assert response.type == "response"

    assert (
        response.payload["message"]
        == "valid provider response"
    )

    assert len(provider.requests) == 1

    assert (
        "sensitive-learning-content"
        not in response.to_json()
    )

    assert (
        health.snapshot()
        .automatic_learning.status
        is MemoryHealthStatus.DEGRADED
    )
