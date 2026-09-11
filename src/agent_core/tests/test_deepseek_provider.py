import asyncio
from dataclasses import dataclass

import openai
import pytest

import agent_core.providers.deepseek as deepseek_module
from agent_core.providers import (
    LLMMessage,
    LLMProviderError,
    LLMRequest,
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
from agent_core.providers.deepseek import DeepSeekProvider


@dataclass
class FakeSDKMessage:
    content: str | None


@dataclass
class FakeSDKChoice:
    message: FakeSDKMessage


@dataclass
class FakeSDKResponse:
    choices: list[FakeSDKChoice]


class FakeCompletions:
    def __init__(
        self,
        response: object | None = None,
        error: BaseException | None = None,
        delay_seconds: float = 0.0,
    ) -> None:
        self._response = response
        self._error = error
        self._delay_seconds = delay_seconds

        self.calls: list[
            dict[str, object]
        ] = []

    async def create(
        self,
        **kwargs: object,
    ) -> object:
        self.calls.append(
            kwargs,
        )

        if self._delay_seconds > 0:
            await asyncio.sleep(
                self._delay_seconds,
            )

        if self._error is not None:
            raise self._error

        return self._response


class FakeChat:
    def __init__(
        self,
        completions: FakeCompletions,
    ) -> None:
        self.completions = completions


class FakeAsyncOpenAI:
    def __init__(
        self,
        completions: FakeCompletions,
    ) -> None:
        self.chat = FakeChat(
            completions,
        )

        self.closed = False

    async def close(self) -> None:
        self.closed = True


class FakeAPIStatusError(
    openai.APIStatusError,
):
    def __init__(
        self,
        status_code: int,
    ) -> None:
        Exception.__init__(
            self,
            f"HTTP {status_code}",
        )

        self.status_code = status_code


class FakeAPITimeoutError(
    openai.APITimeoutError,
):
    def __init__(self) -> None:
        Exception.__init__(
            self,
            "timeout",
        )


class FakeAPIConnectionError(
    openai.APIConnectionError,
):
    def __init__(self) -> None:
        Exception.__init__(
            self,
            "connection",
        )


class FakeAPIResponseValidationError(
    openai.APIResponseValidationError,
):
    def __init__(self) -> None:
        Exception.__init__(
            self,
            "validation",
        )


class FakeGenericAPIError(
    openai.APIError,
):
    def __init__(self) -> None:
        Exception.__init__(
            self,
            "generic API error",
        )


def install_fake_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    response: object | None = None,
    error: BaseException | None = None,
    delay_seconds: float = 0.0,
) -> tuple[
    FakeAsyncOpenAI,
    list[dict[str, object]],
]:
    """
    替换 DeepSeekProvider 内部的 AsyncOpenAI，
    避免真实网络和 API Key。
    """

    completions = FakeCompletions(
        response=response,
        error=error,
        delay_seconds=delay_seconds,
    )

    client = FakeAsyncOpenAI(
        completions,
    )

    constructor_calls: list[
        dict[str, object]
    ] = []

    def fake_async_openai(
        **kwargs: object,
    ) -> FakeAsyncOpenAI:
        constructor_calls.append(
            kwargs,
        )

        return client

    monkeypatch.setattr(
        deepseek_module,
        "AsyncOpenAI",
        fake_async_openai,
    )

    return (
        client,
        constructor_calls,
    )


def create_request() -> LLMRequest:
    return LLMRequest(
        messages=(
            LLMMessage(
                role="system",
                content="system message",
            ),
            LLMMessage(
                role="user",
                content="user message",
            ),
            LLMMessage(
                role="assistant",
                content="assistant message",
            ),
        ),
    )


def test_deepseek_provider_maps_request_and_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    验证 Provider-neutral request
    会正确映射为 DeepSeek Chat Completions 请求。
    """

    fake_response = FakeSDKResponse(
        choices=[
            FakeSDKChoice(
                message=FakeSDKMessage(
                    content="DeepSeek response",
                ),
            ),
        ],
    )

    client, constructor_calls = install_fake_client(
        monkeypatch,
        response=fake_response,
    )

    provider = DeepSeekProvider(
        api_key="test-key",
        model="deepseek-flash",
        timeout_seconds=60.0,
        thinking_enabled=False,
    )

    response = asyncio.run(
        provider.generate(
            create_request(),
        )
    )

    assert response.content == "DeepSeek response"

    assert constructor_calls == [
        {
            "api_key": "test-key",
            "base_url": "https://api.deepseek.com",
            "timeout": 60.0,
            "max_retries": 0,
        },
    ]

    calls = client.chat.completions.calls

    assert len(calls) == 1

    assert calls[0]["model"] == "deepseek-flash"

    assert calls[0]["stream"] is False

    assert calls[0]["extra_body"] == {
        "thinking": {
            "type": "disabled",
        },
    }

    assert calls[0]["messages"] == [
        {
            "role": "system",
            "content": "system message",
        },
        {
            "role": "user",
            "content": "user message",
        },
        {
            "role": "assistant",
            "content": "assistant message",
        },
    ]


def test_deepseek_provider_can_enable_thinking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    验证 thinking 配置会显式映射到请求。
    """

    fake_response = FakeSDKResponse(
        choices=[
            FakeSDKChoice(
                message=FakeSDKMessage(
                    content="response",
                ),
            ),
        ],
    )

    client, _ = install_fake_client(
        monkeypatch,
        response=fake_response,
    )

    provider = DeepSeekProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        timeout_seconds=60.0,
        thinking_enabled=True,
    )

    asyncio.run(
        provider.generate(
            create_request(),
        )
    )

    assert (
        client.chat.completions.calls[0][
            "extra_body"
        ]
        == {
            "thinking": {
                "type": "enabled",
            },
        }
    )


@pytest.mark.parametrize(
    (
        "api_key",
        "model",
        "timeout_seconds",
    ),
    [
        (
            "",
            "deepseek-v4-flash",
            60.0,
        ),
        (
            "test-key",
            "",
            60.0,
        ),
        (
            "test-key",
            "deepseek-v4-flash",
            0.0,
        ),
    ],
)
def test_invalid_configuration_is_rejected(
    api_key: str,
    model: str,
    timeout_seconds: float,
) -> None:
    """
    验证 Adapter 自身也保护关键配置边界。
    """

    with pytest.raises(
        ProviderConfigurationError,
    ):
        DeepSeekProvider(
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
            thinking_enabled=False,
        )


def test_application_timeout_is_translated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    验证 asyncio application timeout
    会转换为 ProviderTimeoutError。
    """

    install_fake_client(
        monkeypatch,
        response=None,
        delay_seconds=0.1,
    )

    provider = DeepSeekProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        timeout_seconds=0.01,
        thinking_enabled=False,
    )

    with pytest.raises(
        ProviderTimeoutError,
    ):
        asyncio.run(
            provider.generate(
                create_request(),
            )
        )


def test_sdk_timeout_is_translated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_client(
        monkeypatch,
        error=FakeAPITimeoutError(),
    )

    provider = DeepSeekProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        timeout_seconds=60.0,
        thinking_enabled=False,
    )

    with pytest.raises(
        ProviderTimeoutError,
    ):
        asyncio.run(
            provider.generate(
                create_request(),
            )
        )


def test_connection_error_is_translated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_client(
        monkeypatch,
        error=FakeAPIConnectionError(),
    )

    provider = DeepSeekProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        timeout_seconds=60.0,
        thinking_enabled=False,
    )

    with pytest.raises(
        ProviderConnectionError,
    ):
        asyncio.run(
            provider.generate(
                create_request(),
            )
        )


@pytest.mark.parametrize(
    (
        "status_code",
        "expected_error",
    ),
    [
        (
            401,
            ProviderAuthenticationError,
        ),
        (
            403,
            ProviderAuthenticationError,
        ),
        (
            402,
            ProviderQuotaError,
        ),
        (
            429,
            ProviderRateLimitError,
        ),
        (
            400,
            ProviderRequestError,
        ),
        (
            404,
            ProviderRequestError,
        ),
        (
            422,
            ProviderRequestError,
        ),
        (
            500,
            ProviderUnavailableError,
        ),
        (
            503,
            ProviderUnavailableError,
        ),
    ],
)
def test_status_errors_are_translated(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    expected_error: type[LLMProviderError],
) -> None:
    install_fake_client(
        monkeypatch,
        error=FakeAPIStatusError(
            status_code,
        ),
    )

    provider = DeepSeekProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        timeout_seconds=60.0,
        thinking_enabled=False,
    )

    with pytest.raises(
        expected_error,
    ):
        asyncio.run(
            provider.generate(
                create_request(),
            )
        )


def test_sdk_response_validation_error_is_translated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_client(
        monkeypatch,
        error=FakeAPIResponseValidationError(),
    )

    provider = DeepSeekProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        timeout_seconds=60.0,
        thinking_enabled=False,
    )

    with pytest.raises(
        ProviderResponseError,
    ):
        asyncio.run(
            provider.generate(
                create_request(),
            )
        )


def test_generic_sdk_error_is_translated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_client(
        monkeypatch,
        error=FakeGenericAPIError(),
    )

    provider = DeepSeekProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        timeout_seconds=60.0,
        thinking_enabled=False,
    )

    with pytest.raises(
        LLMProviderError,
    ):
        asyncio.run(
            provider.generate(
                create_request(),
            )
        )


@pytest.mark.parametrize(
    "response",
    [
        FakeSDKResponse(
            choices=[],
        ),
        FakeSDKResponse(
            choices=[
                FakeSDKChoice(
                    message=FakeSDKMessage(
                        content=None,
                    ),
                ),
            ],
        ),
        FakeSDKResponse(
            choices=[
                FakeSDKChoice(
                    message=FakeSDKMessage(
                        content="",
                    ),
                ),
            ],
        ),
    ],
)
def test_invalid_success_response_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    response: FakeSDKResponse,
) -> None:
    install_fake_client(
        monkeypatch,
        response=response,
    )

    provider = DeepSeekProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        timeout_seconds=60.0,
        thinking_enabled=False,
    )

    with pytest.raises(
        ProviderResponseError,
    ):
        asyncio.run(
            provider.generate(
                create_request(),
            )
        )


def test_cancellation_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    验证外部 asyncio cancellation
    不会被包装成 Provider Error。
    """

    install_fake_client(
        monkeypatch,
        delay_seconds=60.0,
    )

    provider = DeepSeekProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        timeout_seconds=60.0,
        thinking_enabled=False,
    )

    async def scenario() -> None:
        task = asyncio.create_task(
            provider.generate(
                create_request(),
            )
        )

        await asyncio.sleep(0)

        task.cancel()

        with pytest.raises(
            asyncio.CancelledError,
        ):
            await task

    asyncio.run(
        scenario(),
    )


def test_aclose_closes_sdk_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = install_fake_client(
        monkeypatch,
    )

    provider = DeepSeekProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        timeout_seconds=60.0,
        thinking_enabled=False,
    )

    asyncio.run(
        provider.aclose(),
    )

    assert client.closed is True
