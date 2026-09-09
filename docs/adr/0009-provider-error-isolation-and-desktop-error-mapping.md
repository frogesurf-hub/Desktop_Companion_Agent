# ADR 0009 - Provider Error Isolation and Desktop Error Mapping

Status: Accepted

Date: Phase 1 DeepSeek adapter design

## Context

The concrete DeepSeek adapter will introduce vendor SDK exceptions, HTTP status codes, transport failures, timeouts, authentication failures, quota errors, and malformed-response possibilities.

Agent Core must remain provider-neutral.

The Desktop protocol already documents an `error` message with `payload.code` and `payload.message`, but the Phase 0 implementation did not consistently populate `code`.

Phase 1 requires a stable boundary between:

```text
vendor / SDK failure
    -> provider-neutral application failure
    -> Desktop protocol error
```

## Decision

Introduce a provider-neutral exception hierarchy:

```text
LLMProviderError
├── ProviderConfigurationError
├── ProviderAuthenticationError
├── ProviderQuotaError
├── ProviderRateLimitError
├── ProviderTimeoutError
├── ProviderConnectionError
├── ProviderRequestError
├── ProviderUnavailableError
└── ProviderResponseError
```

Vendor SDK exceptions must be translated inside the concrete adapter.

`asyncio.CancelledError` is not a provider failure and must propagate.

Provider failures exposed to Desktop use stable protocol codes and safe messages:

```text
PROVIDER_NOT_CONFIGURED
PROVIDER_AUTHENTICATION_FAILED
PROVIDER_QUOTA_EXHAUSTED
PROVIDER_RATE_LIMITED
PROVIDER_TIMEOUT
PROVIDER_UNAVAILABLE
PROVIDER_REQUEST_FAILED
PROVIDER_INVALID_RESPONSE
PROVIDER_ERROR
```

The Desktop protocol must not expose raw vendor exception strings, API keys, prompt content, reasoning content, or response bodies.

## DeepSeek Mapping

```text
missing local configuration -> ProviderConfigurationError
401 / 403                -> ProviderAuthenticationError
402                      -> ProviderQuotaError
429                      -> ProviderRateLimitError
timeout                  -> ProviderTimeoutError
connection failure       -> ProviderConnectionError
400 / 404 / 422          -> ProviderRequestError
5xx                      -> ProviderUnavailableError
invalid success response -> ProviderResponseError
other provider failure   -> LLMProviderError
```

## Retryability

Some categories are semantically retryable in principle:

- rate limit
- timeout
- connection
- service unavailable

Phase 1 still performs zero automatic retries.

This classification exists so future retry / fallback design does not need to inspect vendor exceptions.

## Consequences

- Agent can handle Provider failures without importing the OpenAI SDK
- DeepSeek-specific exceptions remain isolated
- WPF can continue displaying `payload.message`
- future Desktop UI may interpret `payload.code` without changing provider adapters
- logs can retain diagnostic category/status information while user-facing protocol messages remain safe
- protocol documentation must be updated when implementation lands
