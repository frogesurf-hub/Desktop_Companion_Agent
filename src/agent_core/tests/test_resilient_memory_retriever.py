import asyncio
import logging

from agent_core.core.message import Message
from agent_core.memory import (
    MemoryCapability,
    MemoryHealthStatus,
    MemoryHealthTracker,
    ResilientMemoryRetriever,
)
from agent_core.memory.retrieval import (
    PreparedMemoryContext,
)
from agent_core.providers import LLMResponse
from agent_core.tests.fakes import (
    FakeLLMProvider,
    FakeMemoryRetriever,
    create_test_agent,
)


class FailingMemoryRetriever:
    async def retrieve(
        self,
        query: str,
        *,
        character_id: str,
    ) -> PreparedMemoryContext:
        raise RuntimeError(
            "sensitive-memory-content"
        )


def test_successful_retrieval_returns_context_and_recovers_health(
) -> None:
    expected_context = PreparedMemoryContext(
        user_profile=(
            "User likes programming.",
        ),
    )

    delegate = FakeMemoryRetriever(
        expected_context
    )

    health = MemoryHealthTracker()

    health.mark_degraded(
        MemoryCapability.RETRIEVAL,
        RuntimeError(
            "previous retrieval failure"
        ),
    )

    retriever = ResilientMemoryRetriever(
        retriever=delegate,
        health=health,
    )

    context = asyncio.run(
        retriever.retrieve(
            "hello",
            character_id="aria",
        )
    )

    assert context == expected_context

    assert delegate.queries == [
        "hello",
    ]

    assert delegate.character_ids == [
        "aria",
    ]

    retrieval_health = (
        health.snapshot().retrieval
    )

    assert (
        retrieval_health.status
        is MemoryHealthStatus.AVAILABLE
    )

    assert (
        retrieval_health.last_error_type
        is None
    )


def test_retrieval_failure_returns_empty_context_and_degrades_health(
    caplog,
) -> None:
    health = MemoryHealthTracker()

    retriever = ResilientMemoryRetriever(
        retriever=FailingMemoryRetriever(),
        health=health,
    )

    with caplog.at_level(
        logging.WARNING
    ):
        context = asyncio.run(
            retriever.retrieve(
                "private user query",
                character_id="aria",
            )
        )

    assert context.is_empty

    retrieval_health = (
        health.snapshot().retrieval
    )

    assert (
        retrieval_health.status
        is MemoryHealthStatus.DEGRADED
    )

    assert (
        retrieval_health.last_error_type
        == "RuntimeError"
    )

    assert (
        "Memory retrieval failed: RuntimeError"
        in caplog.text
    )

    assert (
        "sensitive-memory-content"
        not in caplog.text
    )

    assert (
        "private user query"
        not in caplog.text
    )


def test_agent_chat_continues_when_memory_retrieval_fails(
) -> None:
    provider = FakeLLMProvider(
        response=LLMResponse(
            content="chat still works",
        ),
    )

    health = MemoryHealthTracker()

    resilient_retriever = (
        ResilientMemoryRetriever(
            retriever=FailingMemoryRetriever(),
            health=health,
        )
    )

    agent = create_test_agent(
        provider,
        memory_retriever=resilient_retriever,
    )

    response = asyncio.run(
        agent.process_message(
            Message(
                type="chat",
                source="desktop",
                payload={
                    "message": "hello",
                },
            )
        )
    )

    assert response.type == "response"

    assert (
        response.payload["message"]
        == "chat still works"
    )

    assert len(provider.requests) == 1

    system_content = (
        provider.requests[0]
        .messages[0]
        .content
    )

    assert (
        "sensitive-memory-content"
        not in system_content
    )

    assert (
        health.snapshot().retrieval.status
        is MemoryHealthStatus.DEGRADED
    )
