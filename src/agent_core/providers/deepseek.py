import asyncio

import openai
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from agent_core.providers import (
    LLMMessage,
    LLMProviderError,
    LLMRequest,
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

DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class DeepSeekProvider:
    """
    DeepSeek 的 OpenAI-compatible LLM Provider Adapter。

    负责：
    - Provider-neutral 请求转换
    - DeepSeek Chat Completions 调用
    - timeout / cancellation
    - vendor error translation
    - Provider-neutral 响应转换
    - SDK client 生命周期
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float,
        thinking_enabled: bool,
    ) -> None:
        if not api_key.strip():
            raise ProviderConfigurationError(
                "DeepSeek API key is missing",
            )

        if not model.strip():
            raise ProviderConfigurationError(
                "DeepSeek model is missing",
            )

        if timeout_seconds <= 0:
            raise ProviderConfigurationError(
                "DeepSeek timeout must be greater than zero",
            )

        self._model = model
        self._timeout_seconds = timeout_seconds
        self._thinking_enabled = thinking_enabled

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=DEEPSEEK_BASE_URL,
            timeout=timeout_seconds,
            max_retries=0,
        )

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        调用 DeepSeek 并返回完整非流式响应。
        """

        sdk_messages = [
            self._to_sdk_message(
                message,
            )
            for message in request.messages
        ]

        thinking_type = (
            "enabled"
            if self._thinking_enabled
            else "disabled"
        )

        try:
            async with asyncio.timeout(
                self._timeout_seconds,
            ):
                response = (
                    await self._client.chat.completions.create(
                        model=self._model,
                        messages=sdk_messages,
                        stream=False,
                        extra_body={
                            "thinking": {
                                "type": thinking_type,
                            },
                        },
                    )
                )

        except asyncio.CancelledError:
            raise

        except TimeoutError as exc:
            raise ProviderTimeoutError(
                "DeepSeek request exceeded application timeout",
            ) from exc

        except openai.APITimeoutError as exc:
            raise ProviderTimeoutError(
                "DeepSeek SDK request timed out",
            ) from exc

        except openai.APIConnectionError as exc:
            raise ProviderConnectionError(
                "DeepSeek connection failed",
            ) from exc

        except openai.APIResponseValidationError as exc:
            raise ProviderResponseError(
                "DeepSeek SDK could not validate the response",
            ) from exc

        except openai.APIStatusError as exc:
            raise self._map_status_error(
                exc,
            ) from exc

        except openai.APIError as exc:
            raise LLMProviderError(
                "DeepSeek API request failed",
            ) from exc

        if not response.choices:
            raise ProviderResponseError(
                "DeepSeek response contains no choices",
            )

        content = response.choices[0].message.content

        if content is None or content == "":
            raise ProviderResponseError(
                "DeepSeek response contains no final text",
            )

        return LLMResponse(
            content=content,
        )

    async def aclose(self) -> None:
        """
        关闭 Provider 持有的异步 SDK client。
        """

        await self._client.close()

    @staticmethod
    def _to_sdk_message(
        message: LLMMessage,
    ) -> ChatCompletionMessageParam:
        """
        将 Provider-neutral LLMMessage
        转换为 OpenAI-compatible message。
        """

        if message.role == "system":
            return {
                "role": "system",
                "content": message.content,
            }

        if message.role == "user":
            return {
                "role": "user",
                "content": message.content,
            }

        if message.role == "assistant":
            return {
                "role": "assistant",
                "content": message.content,
            }

        raise ProviderRequestError(
            "Unsupported LLM message role",
        )

    @staticmethod
    def _map_status_error(
        error: openai.APIStatusError,
    ) -> LLMProviderError:
        """
        将 HTTP / SDK status error
        转换为 Provider-neutral error。
        """

        status_code = error.status_code

        if status_code in {
            401,
            403,
        }:
            return ProviderAuthenticationError(
                f"DeepSeek authentication failed "
                f"with status {status_code}",
            )

        if status_code == 402:
            return ProviderQuotaError(
                "DeepSeek quota or balance is insufficient",
            )

        if status_code == 429:
            return ProviderRateLimitError(
                "DeepSeek rate limit exceeded",
            )

        if 400 <= status_code < 500:
            return ProviderRequestError(
                f"DeepSeek rejected the request "
                f"with status {status_code}",
            )

        if status_code >= 500:
            return ProviderUnavailableError(
                f"DeepSeek service failed "
                f"with status {status_code}",
            )

        return LLMProviderError(
            f"DeepSeek API failed "
            f"with status {status_code}",
        )
