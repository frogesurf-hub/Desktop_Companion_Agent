import logging

from agent_core.core.message import Message
from agent_core.providers import (
    LLMMessage,
    LLMProvider,
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

logger = logging.getLogger(__name__)

_PROVIDER_ERROR_PROTOCOL_MAP: tuple[
    tuple[
        type[LLMProviderError],
        str,
        str,
    ],
    ...,
] = (
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
)


class Agent:
    """
    Agent 核心逻辑。

    当前阶段负责：
    - 接收协议 Message
    - 转换为 Provider-neutral LLM 请求
    - 调用注入的 LLM Provider
    - 将 Provider 响应转换回协议 Message
    - 将 Provider 错误转换为安全的协议 error Message

    后续会继续接入：
    - Memory
    - Behavior
    - Tool
    """

    def __init__(
        self,
        provider: LLMProvider,
        name: str = "Desktop Companion",
    ) -> None:
        self.name = name
        self._provider = provider

    async def process_message(
        self,
        message: Message,
    ) -> Message:
        """
        异步处理输入消息并返回统一 Message。
        """

        if message.type == "chat":
            user_text = message.payload.get(
                "message",
                "",
            )

            request = LLMRequest(
                messages=(
                    LLMMessage(
                        role="user",
                        content=user_text,
                    ),
                ),
            )

            try:
                provider_response = await self._provider.generate(
                    request,
                )

            except LLMProviderError as exc:
                logger.warning(
                    "LLM provider request failed: %s",
                    type(exc).__name__,
                )

                code, safe_message = self._map_provider_error(
                    exc,
                )

                return Message(
                    type="error",
                    source=self.name,
                    payload={
                        "code": code,
                        "message": safe_message,
                    },
                )

            return Message(
                type="response",
                source=self.name,
                payload={
                    "message": provider_response.content,
                },
            )

        return Message(
            type="error",
            source=self.name,
            payload={
                "message": "Unsupported message type",
            },
        )

    @staticmethod
    def _map_provider_error(
        error: LLMProviderError,
    ) -> tuple[str, str]:
        """
        将 Provider-neutral error
        转换为稳定的 Desktop protocol code/message。
        """

        for (
            error_type,
            code,
            safe_message,
        ) in _PROVIDER_ERROR_PROTOCOL_MAP:
            if isinstance(
                error,
                error_type,
            ):
                return (
                    code,
                    safe_message,
                )

        return (
            "PROVIDER_ERROR",
            "AI provider request failed.",
        )
