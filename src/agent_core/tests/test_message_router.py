import asyncio

import pytest

from agent_core.core.message import Message
from agent_core.core.message_router import (
    RuntimeMessageRouter,
)


class RecordingProcessor:
    def __init__(
        self,
        response: Message,
    ) -> None:
        self.response = response
        self.messages: list[Message] = []

    async def process_message(
        self,
        message: Message,
    ) -> Message:
        self.messages.append(
            message
        )

        return self.response


def _request(
    message_type: str,
) -> Message:
    return Message(
        id="request-1",
        type=message_type,
        source="desktop",
        payload={},
    )


def test_router_sends_chat_to_chat_processor() -> None:
    chat_response = Message(
        type="response",
        source="agent",
        payload={
            "message": "hello",
        },
    )

    memory_response = Message(
        type="memory.list.result",
        source="agent_core",
        payload={},
    )

    chat_processor = RecordingProcessor(
        chat_response
    )

    memory_processor = RecordingProcessor(
        memory_response
    )

    router = RuntimeMessageRouter(
        chat_processor=chat_processor,
        memory_processor=memory_processor,
    )

    request = _request(
        "chat"
    )

    response = asyncio.run(
        router.process_message(
            request
        )
    )

    assert response is chat_response

    assert chat_processor.messages == [
        request,
    ]

    assert memory_processor.messages == []


@pytest.mark.parametrize(
    "message_type",
    [
        "memory.list",
        "memory.inspect",
        "memory.edit",
        "memory.delete",
        "memory.history",
    ],
)
def test_router_sends_memory_requests_to_memory_processor(
    message_type: str,
) -> None:
    chat_processor = RecordingProcessor(
        Message(
            type="response",
            source="agent",
            payload={},
        )
    )

    memory_response = Message(
        type=f"{message_type}.result",
        source="agent_core",
        payload={},
    )

    memory_processor = RecordingProcessor(
        memory_response
    )

    router = RuntimeMessageRouter(
        chat_processor=chat_processor,
        memory_processor=memory_processor,
    )

    request = _request(
        message_type
    )

    response = asyncio.run(
        router.process_message(
            request
        )
    )

    assert response is memory_response

    assert memory_processor.messages == [
        request,
    ]

    assert chat_processor.messages == []


def test_router_routes_unknown_memory_operation_to_memory_boundary(
) -> None:
    chat_processor = RecordingProcessor(
        Message(
            type="response",
            source="agent",
            payload={},
        )
    )

    memory_response = Message(
        type="error",
        source="agent_core",
        payload={
            "message": "Invalid Memory request",
        },
    )

    memory_processor = RecordingProcessor(
        memory_response
    )

    router = RuntimeMessageRouter(
        chat_processor=chat_processor,
        memory_processor=memory_processor,
    )

    request = _request(
        "memory.unknown"
    )

    response = asyncio.run(
        router.process_message(
            request
        )
    )

    assert response is memory_response
    assert memory_processor.messages == [
        request,
    ]
    assert chat_processor.messages == []


def test_router_rejects_unsupported_capability_family(
) -> None:
    chat_processor = RecordingProcessor(
        Message(
            type="response",
            source="agent",
            payload={},
        )
    )

    memory_processor = RecordingProcessor(
        Message(
            type="memory.list.result",
            source="agent_core",
            payload={},
        )
    )

    router = RuntimeMessageRouter(
        chat_processor=chat_processor,
        memory_processor=memory_processor,
    )

    response = asyncio.run(
        router.process_message(
            _request(
                "tool.execute"
            )
        )
    )

    assert response.type == "error"

    assert (
        response.payload["message"]
        == "Unsupported message type"
    )

    assert chat_processor.messages == []
    assert memory_processor.messages == []
