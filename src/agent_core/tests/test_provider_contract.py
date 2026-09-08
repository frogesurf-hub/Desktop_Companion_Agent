import asyncio

from agent_core.providers import (
    LLMMessage,
    LLMProvider,
    LLMRequest,
    LLMResponse,
)
from agent_core.tests.fakes import FakeLLMProvider


def _as_llm_provider(
    provider: LLMProvider,
) -> LLMProvider:
    """
    为静态类型检查提供显式 Provider 边界。
    """

    return provider


def test_fake_provider_returns_configured_response() -> None:
    """
    验证 Fake Provider 满足异步 Provider Contract。
    """

    expected_response = LLMResponse(
        content="fake response",
    )

    fake_provider = FakeLLMProvider(
        response=expected_response,
    )

    provider = _as_llm_provider(
        fake_provider,
    )

    request = LLMRequest(
        messages=(
            LLMMessage(
                role="user",
                content="hello",
            ),
        ),
    )

    response = asyncio.run(
        provider.generate(
            request,
        )
    )

    assert response == expected_response


def test_fake_provider_records_requests() -> None:
    """
    验证 Fake Provider 会保存收到的请求，
    供后续 Agent 集成测试断言。
    """

    fake_provider = FakeLLMProvider(
        response=LLMResponse(
            content="fake response",
        ),
    )

    request = LLMRequest(
        messages=(
            LLMMessage(
                role="user",
                content="hello",
            ),
        ),
    )

    asyncio.run(
        fake_provider.generate(
            request,
        )
    )

    assert fake_provider.requests == [
        request,
    ]
