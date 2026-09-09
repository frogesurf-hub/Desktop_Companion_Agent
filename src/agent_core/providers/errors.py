from typing import ClassVar


class LLMProviderError(Exception):
    """
    所有 LLM Provider 错误的统一基类。

    retryable 只描述错误类别在语义上是否适合未来重试，
    Phase 1 当前仍然不会执行自动重试。
    """

    retryable: ClassVar[bool] = False


class ProviderConfigurationError(LLMProviderError):
    """
    Provider 本地配置缺失或无效。
    """


class ProviderAuthenticationError(LLMProviderError):
    """
    Provider 身份验证失败。
    """


class ProviderQuotaError(LLMProviderError):
    """
    Provider 配额、余额或计费资源不足。
    """


class ProviderRateLimitError(LLMProviderError):
    """
    Provider 请求受到速率限制。
    """

    retryable: ClassVar[bool] = True


class ProviderTimeoutError(LLMProviderError):
    """
    Provider 请求超过允许的时间预算。
    """

    retryable: ClassVar[bool] = True


class ProviderConnectionError(LLMProviderError):
    """
    无法与 Provider 建立或维持网络连接。
    """

    retryable: ClassVar[bool] = True


class ProviderRequestError(LLMProviderError):
    """
    Provider 拒绝了当前请求。
    """


class ProviderUnavailableError(LLMProviderError):
    """
    Provider 服务暂时不可用。
    """

    retryable: ClassVar[bool] = True


class ProviderResponseError(LLMProviderError):
    """
    Provider 返回的成功响应无法满足统一契约。
    """
