import asyncio
from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from agent_core.characters import CharacterDefinition
from agent_core.composition import PromptContextComposer
from agent_core.core.agent import Agent
from agent_core.core.message import Message
from agent_core.providers import (
    LLMProvider,
    LLMProviderError,
    LLMResponse,
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderConnectionError,
    ProviderQuotaError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from agent_core.tests.fakes import (
    FailingLLMProvider,
    FakeLLMProvider,
    FixedClock,
)


def _create_character() -> CharacterDefinition:
    """
    创建 Agent 测试使用的稳定 Character。
    """

    return CharacterDefinition(
        character_id="test",
        display_name="Test",
        identity="A test companion.",
        persona="Calm.",
        speech_style="Concise.",
    )


def _create_clock() -> FixedClock:
    """
    创建 Agent 测试使用的确定性 Clock。
    """

    return FixedClock(
        datetime(
            2026,
            9,
            13,
            20,
            0,
            tzinfo=timezone(
                timedelta(hours=8),
            ),
        )
    )


def _create_agent(
    provider: LLMProvider,
) -> Agent:
    """
    使用 Phase 3 Runtime dependencies 创建 Agent。
    """

    return Agent(
        provider=provider,
        character=_create_character(),
        composer=PromptContextComposer(),
        clock=_create_clock(),
    )



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

    restored = Message.from_json(
        json_data,
    )

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

    agent = _create_agent(
        provider,
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

    assert (
        response.payload["message"]
        == "来自 Provider 的回复"
    )

    assert len(provider.requests) == 1

    request = provider.requests[0]

    assert len(request.messages) == 2

    assert request.messages[0].role == "system"

    assert request.messages[1].role == "user"
    assert request.messages[1].content == "你好"

    system_content = request.messages[0].content

    assert "[Runtime Rules]" in system_content
    assert "[Temporal Context]" in system_content
    assert "[Character Identity]" in system_content

    assert "Character ID: test" in system_content
    assert "Display name: Test" in system_content

    assert "Current date: 2026-09-13" in system_content
    assert "Current weekday: Sunday" in system_content


@pytest.mark.parametrize(
    (
        "error_type",
        "expected_code",
        "expected_message",
    ),
    [
        (
            ProviderConfigurationError,
            "PROVIDER_NOT_CONFIGURED",
            "AI provider is not configured.",
        ),
        (
            ProviderAuthenticationError,
            "PROVIDER_AUTHENTICATION_FAILED",
            "AI provider authentication failed.",
        ),
        (
            ProviderQuotaError,
            "PROVIDER_QUOTA_EXHAUSTED",
            "AI provider quota or balance is insufficient.",
        ),
        (
            ProviderRateLimitError,
            "PROVIDER_RATE_LIMITED",
            "AI provider is rate-limited. Please try again later.",
        ),
        (
            ProviderTimeoutError,
            "PROVIDER_TIMEOUT",
            "AI provider request timed out.",
        ),
        (
            ProviderConnectionError,
            "PROVIDER_UNAVAILABLE",
            "AI provider is temporarily unavailable.",
        ),
        (
            ProviderUnavailableError,
            "PROVIDER_UNAVAILABLE",
            "AI provider is temporarily unavailable.",
        ),
        (
            ProviderRequestError,
            "PROVIDER_REQUEST_FAILED",
            "AI provider rejected the request.",
        ),
        (
            ProviderResponseError,
            "PROVIDER_INVALID_RESPONSE",
            "AI provider returned an invalid response.",
        ),
        (
            LLMProviderError,
            "PROVIDER_ERROR",
            "AI provider request failed.",
        ),
    ],
)
def test_agent_maps_provider_error_to_safe_protocol_error(
    error_type: type[LLMProviderError],
    expected_code: str,
    expected_message: str,
) -> None:
    """
    验证 Provider 错误会转换成稳定且安全的协议错误。
    """

    internal_diagnostic = (
        "internal provider diagnostic that must not reach desktop"
    )

    provider = FailingLLMProvider(
        error=error_type(
            internal_diagnostic,
        ),
    )

    agent = _create_agent(
        provider,
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

    assert response.type == "error"

    assert response.payload == {
        "code": expected_code,
        "message": expected_message,
    }

    assert internal_diagnostic not in response.to_json()

    assert len(provider.requests) == 1


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

    agent = _create_agent(
        provider,
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

    assert (
        response.payload["message"]
        == "Unsupported message type"
    )

    assert provider.requests == []
