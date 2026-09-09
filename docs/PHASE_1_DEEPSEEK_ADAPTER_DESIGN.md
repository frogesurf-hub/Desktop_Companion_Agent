# Phase 1 - DeepSeek Adapter Design

Status: Accepted design baseline for Phase 1 implementation

## 1. Purpose

This document resolves the DeepSeek-specific design gate that follows:

- Phase 1 Provider Layer design
- Task 1 Provider Contract Foundation
- Task 2 Agent Integration

The goal is to connect the first real cloud LLM provider without weakening the provider-neutral Agent boundary or expanding Phase 1 into unrelated capabilities.

## 2. Current Runtime Baseline

The Python runtime now follows:

```text
WebSocketServer
    -> await Agent.process_message()
    -> await LLMProvider.generate()
```

The active runtime still uses a temporary `EchoLLMProvider` so the main branch remains executable until the real DeepSeek adapter is ready.

The Provider contract remains:

```text
LLMRequest
    -> async generate(...)
    -> LLMResponse
```

Streaming remains out of Phase 1 under ADR 0007.

## 3. Decisions

### 3.1 Default DeepSeek Model

Default:

```text
deepseek-v4-flash
```

The model is configuration-driven rather than hard-coded into Agent Core.

New setting:

```text
DCA_DEEPSEEK_MODEL=deepseek-v4-flash
```

`deepseek-v4-pro` remains a supported configuration option without requiring changes to the Agent contract.

Rationale:

- Phase 1 is a conversational MVP with no tools, memory, or complex autonomous planning.
- The current official DeepSeek documentation positions V4 Flash as faster and more cost-effective, while remaining competitive for simpler Agent tasks.
- The default can later be changed through configuration without modifying Core.

Legacy aliases such as `deepseek-chat` and `deepseek-reasoner` must not be used.

### 3.2 Thinking Mode

Phase 1 default:

```text
thinking = disabled
```

New setting:

```text
DCA_DEEPSEEK_THINKING_ENABLED=false
```

Rationale:

- the current MVP is an interactive desktop chat path
- DeepSeek V4 thinking mode is currently enabled by default
- leaving the vendor default implicit would introduce additional latency and reasoning-token cost into the MVP
- the current `LLMResponse` contract only requires final answer content
- Phase 1 does not need reasoning-content persistence or tool-call reasoning state

The adapter must therefore explicitly send:

```text
thinking.type = disabled
```

when the setting is false.

Thinking can be enabled later by configuration, but Phase 1 does not persist or expose reasoning content.

### 3.3 API Surface

Use the DeepSeek OpenAI-compatible Chat Completions API.

Do not use the Responses API in Phase 1.

Rationale:

- the Provider contract is already message-oriented
- `LLMRequest.messages` maps directly to Chat Completions `messages`
- Phase 1 does not need Responses-API-specific state, semantic event streaming, or tool orchestration
- using the smaller API surface reduces adapter translation and test complexity

### 3.4 Python Client

Use the official OpenAI Python SDK through:

```python
AsyncOpenAI
```

with DeepSeek's OpenAI-compatible base URL:

```text
https://api.deepseek.com
```

Rationale:

- DeepSeek explicitly documents OpenAI-compatible access
- the project's Provider contract is asynchronous
- the official OpenAI SDK provides an asynchronous client and typed exception hierarchy
- vendor SDK types remain inside the concrete adapter / composition root boundary

Add the runtime dependency to the canonical dependency source:

```text
pyproject.toml
```

Do not add it to the legacy duplicate `src/agent_core/requirements.txt`.

### 3.5 Streaming

Explicitly:

```text
stream = false
```

This preserves ADR 0007.

### 3.6 Request Timeout

Application request budget:

```text
60 seconds
```

New setting:

```text
DCA_DEEPSEEK_TIMEOUT_SECONDS=60
```

The adapter must enforce a bounded asynchronous timeout.

Recommended implementation:

```python
async with asyncio.timeout(timeout_seconds):
    ...
```

The adapter must translate an adapter-owned timeout into the provider-neutral timeout error.

Rationale:

- an interactive desktop request must not be allowed to remain pending for the vendor's very long default period
- a single explicit application budget gives predictable Phase 1 behavior
- the timeout remains configurable for future tuning

The SDK transport timeout may also be configured to the same value, but the application timeout is the authoritative request budget.

### 3.7 Retry Policy

Phase 1 automatic retries:

```text
0
```

Configure the OpenAI SDK with:

```text
max_retries = 0
```

Do not implement a custom retry loop in Phase 1.

Rationale:

- retry behavior must be explicit rather than inherited silently from the SDK
- the SDK currently retries selected connection, timeout, rate-limit, and server errors by default
- automatic retries increase interactive latency
- provider documentation does not establish an application-level idempotency guarantee for this project's chat request
- duplicate inference / billing risk should not be introduced without an explicit retry/idempotency policy
- a later reliability phase can add bounded retry, backoff, request identifiers, fallback, and observability as one coherent design

Retryable failures are still classified in the internal Provider Error Contract so future retry/fallback logic has a stable boundary.

### 3.8 Cancellation Semantics

Phase 1 supports cooperative asyncio task cancellation.

Rules:

1. `asyncio.CancelledError` must not be converted into a provider failure.
2. The adapter must allow cancellation to propagate to the caller.
3. The 60-second application timeout is translated into a Provider timeout error.
4. Phase 1 does not define a Desktop protocol message for user-requested cancellation.
5. Phase 1 does not add a cancel button or per-request cancellation UI.

This keeps runtime shutdown / task cancellation correct without expanding the Desktop protocol.

## 4. DeepSeek Provider Configuration

Extend `Settings` with provider-specific fields:

```text
deepseek_api_key
deepseek_model
deepseek_timeout_seconds
deepseek_thinking_enabled
```

Recommended defaults:

```text
deepseek_model = "deepseek-v4-flash"
deepseek_timeout_seconds = 60.0
deepseek_thinking_enabled = False
```

No API-key default is allowed.

`.env.example` should document:

```text
DCA_DEEPSEEK_API_KEY=
DCA_DEEPSEEK_MODEL=deepseek-v4-flash
DCA_DEEPSEEK_TIMEOUT_SECONDS=60
DCA_DEEPSEEK_THINKING_ENABLED=false
```

The API key must remain a `SecretStr` in Settings and must only be unwrapped at the concrete-provider construction boundary.

## 5. DeepSeek Adapter Responsibility

Proposed module:

```text
src/agent_core/providers/deepseek.py
```

Responsibilities:

- own the DeepSeek/OpenAI-compatible client
- convert `LLMMessage` objects to Chat Completions messages
- issue one non-streaming request
- explicitly control thinking mode
- enforce the application timeout
- convert the final text into `LLMResponse`
- translate SDK / HTTP failures into provider-neutral errors
- reject structurally invalid responses
- expose async cleanup for the owned client

The adapter must not:

- accept Desktop protocol `Message`
- return Desktop protocol `Message`
- contain WPF behavior
- contain retry loops
- contain memory logic
- contain prompt/personality policy
- expose SDK response types to Agent Core

## 6. Provider Lifecycle

`DeepSeekProvider` owns its asynchronous SDK client and should expose:

```python
async def aclose() -> None:
    ...
```

`aclose()` does not need to become part of the `LLMProvider` Agent-facing Protocol in Phase 1.

The composition root creates the concrete provider and owns its lifetime:

```text
create DeepSeekProvider
    -> inject into Agent
    -> run WebSocketServer
    -> finally await provider.aclose()
```

This preserves a narrow Agent-facing contract while still closing external network resources correctly.

## 7. Request Mapping

Provider-neutral input:

```python
LLMRequest(
    messages=(
        LLMMessage(role="user", content="你好"),
    )
)
```

DeepSeek Chat Completions request:

```text
model = configured DeepSeek model
messages = role/content message list
stream = false
thinking = explicitly enabled or disabled
```

Phase 1 does not send:

- tools
- response_format
- temperature
- top_p
- presence_penalty
- frequency_penalty
- user_id
- reasoning history
- max_tokens override

Those parameters require an explicit product or subsystem requirement before being added.

## 8. Response Mapping

Expected success path:

```text
response
  -> choices[0]
  -> message.content
  -> LLMResponse(content=...)
```

The adapter must treat the response as invalid when:

- no choice exists
- the first choice has no final text content
- the SDK returns a response shape that cannot satisfy the Provider contract

Invalid response shape becomes a provider-neutral response error.

Reasoning content is not copied into `LLMResponse` in Phase 1.

## 9. Provider Error Contract

Add a provider-neutral error hierarchy under:

```text
src/agent_core/providers/errors.py
```

Proposed hierarchy:

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

No OpenAI SDK exception type may cross this boundary.

### 9.1 Retryability Semantics

Internal classification:

```text
Configuration      non-retryable
Authentication     non-retryable
Quota              non-retryable
Rate limit         retryable in principle
Timeout            retryable in principle
Connection         retryable in principle
Bad request        non-retryable
Unavailable        retryable in principle
Invalid response   non-retryable by default
```

"Retryable in principle" does not mean Phase 1 automatically retries.

It records semantics for later retry/fallback policy.

## 10. DeepSeek Error Mapping

DeepSeek / SDK failures should map approximately as follows:

```text
Missing API key
    -> ProviderConfigurationError

401 / 403
    -> ProviderAuthenticationError

402
    -> ProviderQuotaError

429
    -> ProviderRateLimitError

Adapter application timeout
SDK API timeout
    -> ProviderTimeoutError

SDK connection failure
    -> ProviderConnectionError

400 / 404 / 422 and other request-level 4xx
    -> ProviderRequestError

500 / 503 and other server 5xx
    -> ProviderUnavailableError

Unusable success response
SDK response-validation failure
    -> ProviderResponseError

Other SDK provider failures
    -> LLMProviderError
```

The adapter should preserve the original exception through exception chaining for local diagnostics, but raw vendor error text must not be copied into the Desktop protocol.

## 11. Desktop Protocol Error Contract

The existing communication protocol already defines:

```text
type = "error"
payload.code
payload.message
```

Phase 1 should make the implementation conform to that documented shape for Provider failures.

Provider failure mapping:

```text
ProviderConfigurationError
    -> PROVIDER_NOT_CONFIGURED
    -> "AI provider is not configured."

ProviderAuthenticationError
    -> PROVIDER_AUTHENTICATION_FAILED
    -> "AI provider authentication failed."

ProviderQuotaError
    -> PROVIDER_QUOTA_EXHAUSTED
    -> "AI provider quota or balance is insufficient."

ProviderRateLimitError
    -> PROVIDER_RATE_LIMITED
    -> "AI provider is rate-limited. Please try again later."

ProviderTimeoutError
    -> PROVIDER_TIMEOUT
    -> "AI provider request timed out."

ProviderConnectionError
ProviderUnavailableError
    -> PROVIDER_UNAVAILABLE
    -> "AI provider is temporarily unavailable."

ProviderRequestError
    -> PROVIDER_REQUEST_FAILED
    -> "AI provider rejected the request."

ProviderResponseError
    -> PROVIDER_INVALID_RESPONSE
    -> "AI provider returned an invalid response."

Fallback LLMProviderError
    -> PROVIDER_ERROR
    -> "AI provider request failed."
```

The Desktop payload remains backward-compatible because `message` is retained. The current WPF client reads `payload["message"]` and can ignore the new `code` field until a later UI task uses it.

Do not expose:

- API keys
- raw SDK exception strings
- response bodies
- prompt text
- reasoning content

through the Desktop protocol.

## 12. Logging Policy

Provider logs may include:

- provider name
- configured model
- error category
- HTTP status code when available
- provider request identifier when safely available
- request duration

Provider logs must not include:

- API key
- full prompt / user message
- raw response body
- reasoning content
- raw authorization headers

The adapter should log categories, not secrets or conversation content.

## 13. Testing Strategy

### Unit tests - DeepSeek adapter

Use a fake / mocked SDK client.

No real network and no real API key.

Verify:

- request model -> SDK message conversion
- selected model
- `stream=False`
- thinking disabled by default
- response content conversion
- timeout conversion
- each provider error mapping category
- invalid response conversion
- cancellation propagation
- client cleanup

### Agent tests

Use provider-neutral fake providers / provider-neutral errors.

Do not make Agent tests depend on OpenAI SDK exception classes.

Verify:

- successful provider result still produces protocol `response`
- provider failure produces protocol `error` with stable `code` and safe `message`

### Main / composition-root tests

Verify:

- settings are read
- API key is unwrapped only for provider construction
- real `DeepSeekProvider` replaces the temporary Echo provider
- provider is closed when runtime exits
- WebSocketServer still receives the Agent

### Real manual acceptance

Only after deterministic tests pass:

```text
WPF
-> WebSocket
-> Python Agent
-> DeepSeekProvider
-> DeepSeek API
-> Python
-> WPF
```

The manual acceptance must use a real local `.env` that is never committed.

## 14. Implementation Tasks After Design Acceptance

### Task 3A - Provider Error Foundation

- add provider-neutral error hierarchy
- add error-contract tests

### Task 3B - DeepSeek Configuration and Dependency

- add `openai` to `pyproject.toml`
- extend Settings
- update `.env.example`
- update configuration tests

### Task 3C - DeepSeek Adapter

- implement `DeepSeekProvider`
- implement request/response mapping
- implement timeout / cancellation
- implement SDK error translation
- implement cleanup
- add deterministic adapter tests

### Task 3D - Provider Error -> Protocol Integration

- update Agent to catch provider-neutral errors
- produce documented protocol error codes
- update Agent / WebSocket tests
- update `COMMUNICATION_PROTOCOL.md`

### Task 3E - Composition Root

- replace `EchoLLMProvider` with `DeepSeekProvider`
- safely unwrap API key
- own provider lifecycle
- update `main.py` tests

### Task 3F - Real MVP Acceptance

- install updated editable dependencies
- configure real `.env`
- start Agent Core
- start WPF
- verify a real model response
- verify failure behavior
- inspect logs for secret / prompt leakage

## 15. Definition of Done for the DeepSeek Integration

DeepSeek integration is ready for Phase 1 final acceptance when:

- no DeepSeek-specific type leaks into Agent Core
- `deepseek-v4-flash` is the default configurable model
- thinking is explicitly disabled by default
- Chat Completions is non-streaming
- one request has a 60-second application budget
- SDK automatic retries are disabled
- asyncio cancellation is preserved
- Provider errors are vendor-neutral
- Desktop Provider errors have stable safe codes/messages
- no ordinary automated test needs external network access
- no ordinary automated test needs a real API key
- the SDK client is closed correctly
- targeted pytest passes
- targeted Ruff passes
- targeted mypy passes
- real WPF -> DeepSeek -> WPF acceptance succeeds
- full final test suite remains project-owner controlled
