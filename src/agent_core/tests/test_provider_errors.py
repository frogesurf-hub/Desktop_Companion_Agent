from agent_core.providers import (
    LLMProviderError,
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


def test_all_provider_errors_inherit_from_base() -> None:
    """
    验证所有 Provider 错误都属于统一错误边界。
    """

    error_types: tuple[type[LLMProviderError], ...] = (
        ProviderConfigurationError,
        ProviderAuthenticationError,
        ProviderQuotaError,
        ProviderRateLimitError,
        ProviderTimeoutError,
        ProviderConnectionError,
        ProviderRequestError,
        ProviderUnavailableError,
        ProviderResponseError,
    )

    for error_type in error_types:
        error = error_type(
            "diagnostic message",
        )

        assert isinstance(
            error,
            LLMProviderError,
        )

        assert str(error) == "diagnostic message"


def test_retryable_provider_errors_are_classified() -> None:
    """
    验证未来原则上可以重试的错误类别。
    """

    retryable_errors: tuple[type[LLMProviderError], ...] = (
        ProviderRateLimitError,
        ProviderTimeoutError,
        ProviderConnectionError,
        ProviderUnavailableError,
    )

    for error_type in retryable_errors:
        assert error_type.retryable is True


def test_non_retryable_provider_errors_are_classified() -> None:
    """
    验证默认不可重试的错误类别。
    """

    non_retryable_errors: tuple[type[LLMProviderError], ...] = (
        LLMProviderError,
        ProviderConfigurationError,
        ProviderAuthenticationError,
        ProviderQuotaError,
        ProviderRequestError,
        ProviderResponseError,
    )

    for error_type in non_retryable_errors:
        assert error_type.retryable is False
