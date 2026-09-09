import asyncio

from agent_core.core.agent import Agent
from agent_core.core.message import Message
from agent_core.providers import (
    LLMMessage,
    LLMRequest,
    LLMResponse,
)
from agent_core.tests.fakes import FakeLLMProvider


def test_message_create() -> None:
    """
    测试 Message 是否可以正常创建。
    """

    message = Message(
        type="chat",
        source="desktop",
        payload={
            "message": "你好",
        },
    )

    assert message.type == "chat"
    assert message.source == "desktop"
    assert message.payload["message"] == "你好"


def test_message_json() -> None:
    """
    测试 Message JSON 转换。
    """

    message = Message(
        type="chat",
        source="desktop",
        payload={
            "message": "hello",
        },
    )

    json_data = message.to_json()

    restored = Message.from_json(json_data)

    assert restored.type == "chat"
    assert restored.payload["message"] == "hello"


def test_agent_uses_provider_for_chat_message() -> None:
    """
    验证 Agent 会把 chat Message 转换为 LLMRequest，
    并将 Provider 响应转换回协议 response Message。
    """

    provider = FakeLLMProvider(
        response=LLMResponse(
            content="来自 Provider 的回复",
        ),
    )

    agent = Agent(
        provider=provider,
    )

    message = Message(
        type="chat",
        source="desktop",
        payload={
            "message": "你好",
        },
    )

    response = asyncio.run(
        agent.process_message(
            message,
        )
    )

    assert response.type == "response"
    assert response.payload["message"] == "来自 Provider 的回复"

    assert provider.requests == [
        LLMRequest(
            messages=(
                LLMMessage(
                    role="user",
                    content="你好",
                ),
            ),
        ),
    ]


def test_agent_rejects_unsupported_message_without_calling_provider() -> None:
    """
    验证非 chat Message 仍返回协议错误，
    且不会调用 LLM Provider。
    """

    provider = FakeLLMProvider(
        response=LLMResponse(
            content="unused",
        ),
    )

    agent = Agent(
        provider=provider,
    )

    message = Message(
        type="unsupported",
        source="desktop",
        payload={},
    )

    response = asyncio.run(
        agent.process_message(
            message,
        )
    )

    assert response.type == "error"
    assert response.payload["message"] == "Unsupported message type"
    assert provider.requests == []
