# Phase 1 Checkpoint - Desktop Companion Agent

Date: 2026-09-09

Status: **Complete**

## 1. Phase Goal

Phase 1 completed the original AI MVP by replacing the Phase 0 echo-only Agent path with a real, provider-agnostic LLM path.

Target:

```text
WPF Desktop
  -> WebSocket
  -> Python Agent Core
  -> LLM Provider contract
  -> DeepSeek Adapter
  -> DeepSeek API
  -> Python Agent Core
  -> WebSocket
  -> WPF Desktop
```

Constraints preserved throughout the phase:

- Agent Core must not depend directly on one provider SDK.
- no DeepSeek model / SDK / HTTP / timeout / retry / streaming / error behavior was assumed before the Provider Layer design gate.
- `pyproject.toml` is the canonical Python dependency source.
- development tasks use targeted tests; the project owner performs final full-suite acceptance.
- no source code was silently modified outside the explicit task scope.

## 2. Phase Outcome

Phase 1 is complete.

The runtime now has a real DeepSeek-backed vertical slice while preserving explicit architecture boundaries.

Verified real flow:

```text
WPF
  -> C# Agent client
  -> WebSocket
  -> Python WebSocketServer
  -> Agent
  -> LLMProvider
  -> DeepSeekProvider
  -> DeepSeek API
  -> LLMResponse
  -> Agent protocol response
  -> WebSocket
  -> WPF
```

The Phase 0 temporary Echo provider has been removed.

## 3. Provider Layer

### 3.1 Contract

Agent-facing contract:

```python
async def generate(request: LLMRequest) -> LLMResponse
```

Implemented with `typing.Protocol`.

Provider-neutral models:

```text
LLMMessage
LLMRequest
LLMResponse
LLMRole
```

The models are immutable dataclasses.

Current roles:

```text
system
user
assistant
```

### 3.2 Async / Streaming Decision

ADR 0007 establishes:

- asynchronous Provider contract
- complete-response Provider boundary
- no streaming in Phase 1

### 3.3 Test Infrastructure

Deterministic Provider fakes were added for:

- successful Provider responses
- Provider failures
- Agent integration tests
- WebSocket failure-survival tests

Ordinary automated tests require no external network and no real API key.

## 4. DeepSeek Integration

Phase 1 DeepSeek baseline:

```text
default model: deepseek-v4-flash
client: openai.AsyncOpenAI
base URL: https://api.deepseek.com
API: OpenAI-compatible Chat Completions
streaming: false
thinking: disabled by default
timeout: 60 seconds by default
SDK retries: 0
```

Configuration:

```text
DCA_MODEL_PROVIDER=deepseek
DCA_DEEPSEEK_API_KEY=
DCA_DEEPSEEK_MODEL=deepseek-v4-flash
DCA_DEEPSEEK_TIMEOUT_SECONDS=60
DCA_DEEPSEEK_THINKING_ENABLED=false
```

The model, timeout, and thinking mode are configurable.

### 4.1 Thinking

Phase 1 explicitly controls thinking through the DeepSeek-compatible request body.

Default:

```text
thinking.type = disabled
```

Reasoning content is not persisted or exposed through `LLMResponse`.

### 4.2 Timeout

The adapter enforces:

- configured SDK timeout
- configured application-level `asyncio.timeout`

Default application budget:

```text
60 seconds
```

### 4.3 Retry

OpenAI SDK automatic retries are explicitly disabled:

```text
max_retries = 0
```

Phase 1 performs no custom automatic retry loop.

### 4.4 Cancellation

`asyncio.CancelledError` propagates unchanged.

Phase 1 does not add a Desktop user-cancellation protocol.

### 4.5 Lifecycle

`DeepSeekProvider` owns the async SDK client.

The composition root owns provider lifetime:

```text
create provider
  -> inject Agent
  -> run WebSocketServer
  -> finally await provider.aclose()
```

Cleanup is tested for both normal and exceptional server exit.

## 5. Provider Error Boundary

Phase 1 introduced:

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

Semantic retryability is recorded, but Phase 1 does not automatically retry.

Retryable in principle:

```text
ProviderRateLimitError
ProviderTimeoutError
ProviderConnectionError
ProviderUnavailableError
```

No vendor SDK exception type crosses this boundary.

## 6. Desktop Protocol Error Mapping

Provider errors are converted to safe Desktop protocol errors.

Codes:

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

Example:

```json
{
  "type": "error",
  "payload": {
    "code": "PROVIDER_AUTHENTICATION_FAILED",
    "message": "AI provider authentication failed."
  }
}
```

Raw Provider diagnostics are not exposed to Desktop.

The current WPF UI remains backward compatible because it reads `payload.message`.

## 7. Composition Root

Phase 1 replaced the temporary Echo runtime with the real DeepSeek runtime.

`main.py` now:

```text
Settings
  -> validate provider selection
  -> unwrap SecretStr
  -> create DeepSeekProvider
  -> create Agent(provider)
  -> create WebSocketServer(agent)
  -> await server.run()
  -> finally await provider.aclose()
```

Startup fails fast when:

- `DCA_MODEL_PROVIDER` is unsupported
- DeepSeek API key is missing

There is no silent Echo fallback.

## 8. Dependency Baseline

Canonical Python dependency workflow:

```powershell
pip install -e ".[dev]"
```

Canonical dependency declaration:

```text
pyproject.toml
```

Phase 1 added:

```text
openai>=3.10.0,<4
```

Acceptance environment installed:

```text
openai 3.10.0
```

`src/agent_core/requirements.txt` remains legacy duplicate metadata and is not used for new dependency declarations.

## 9. Design / ADR Artifacts

Phase 1 persistent design documents:

```text
docs/PHASE_1_PROVIDER_LAYER_DESIGN.md
docs/PHASE_1_DEEPSEEK_ADAPTER_DESIGN.md
```

Phase 1 ADRs:

```text
0007-async-non-streaming-provider-contract-for-phase-1.md
0008-deepseek-v4-flash-via-async-openai-chat-completions.md
0009-provider-error-isolation-and-desktop-error-mapping.md
```

The ADR index is:

```text
docs/adr/README.md
```

## 10. Key Git Anchors

Confirmed Phase 1 anchors recorded during development:

```text
1a07d94  Design Phase 1 provider layer
e85143c  Update ADR index for Phase 1
25fb631  Add async LLM provider contract
d6f5f72  Design DeepSeek provider integration
b88ed5c  Add provider error hierarchy
98834c6  Add DeepSeek provider configuration
8268031  Implement DeepSeek provider adapter
cf3348d  Wire DeepSeek provider into runtime
```

The repository `git log --oneline` is the authoritative full commit history. Some intermediate implementation commits are intentionally not duplicated here because their IDs were not recorded in the checkpoint conversation.

## 11. Final Real Acceptance

### 11.1 Secret / Configuration

Verified:

- `.env` is ignored by Git
- real API key exists only in local `.env`
- safe configuration preflight reports:
  - provider = `deepseek`
  - model = `deepseek-v4-flash`
  - API key present = true
  - timeout = `60.0`
  - thinking = false
- no API key is printed by the preflight or normal startup logs

### 11.2 Agent Core Startup

Verified:

```text
Configured model provider: deepseek
Configured DeepSeek model: deepseek-v4-flash
WebSocket endpoint: 127.0.0.1:8765
```

The WebSocket server starts successfully.

### 11.3 ConnectionProbe

Verified real request:

```text
C# ConnectionProbe
  -> Python
  -> DeepSeek API
  -> Python
  -> C#
```

The probe received `type=response` with a real model-generated answer.

Python logs recorded:

```text
POST https://api.deepseek.com/chat/completions
HTTP/1.1 200 OK
```

### 11.4 WPF End-to-End

Verified first request:

```text
You: 请只回复：PHASE1_DEEPSEEK_OK
Agent: PHASE1_DEEPSEEK_OK
```

Verified second request on the same live runtime:

```text
You: 用一句话说明 2+3 等于多少。
Agent: 2加3等于5。
```

Both produced HTTP 200 Provider calls.

### 11.5 Real Authentication Failure

The local API key was deliberately replaced with an invalid value.

Verified WPF output:

```text
AI provider authentication failed.
```

Verified Python behavior:

```text
HTTP/1.1 401 Authorization Required
LLM provider request failed: ProviderAuthenticationError
```

Verified:

- Agent Core did not crash
- raw SDK exception was not shown in WPF
- invalid key was not displayed
- safe protocol mapping worked

The valid local key was restored after the test.

### 11.6 Log Safety

Recent logs were manually inspected.

No observed leakage of:

- API key
- full user prompt
- full model response
- Authorization header
- raw Provider response body
- reasoning content

## 12. Final Quality Gate

Project owner ran the final complete Python validation:

```text
python -m pytest -q
-> 66 passed in 4.69s

python -m ruff check .
-> All checks passed!

python -m mypy src
-> Success: no issues found in 28 source files
```

The WPF real UI flow was manually accepted.

Final Git working tree was confirmed clean.

## 13. Original MVP Status

The original `MVP_DESIGN.md` completion chain is now verified:

```text
Desktop
+
Agent Core
+
Provider
+
Communication
```

Therefore:

- Phase 0 engineering/cross-language foundation: **Complete**
- Phase 1 real LLM/provider integration: **Complete**
- original AI MVP: **Complete**

Future phases should build on this vertical slice rather than reopen provider coupling unless a new provider capability requires an explicit design change.

## 14. Known Remaining Technical Debt

1. Desktop WebSocket endpoint is still hard-coded in `App.xaml.cs`.
2. C# automated tests do not yet exist.
3. protocol version field remains documented but not implemented.
4. WPF reconnect/retry recovery is not implemented.
5. Desktop shutdown/disposal still needs long-running hardening.
6. legacy `src/agent_core/requirements.txt` remains and should eventually be retired.
7. Provider models support only `system`, `user`, and `assistant`.
8. streaming is intentionally absent.
9. automatic retries are intentionally absent.
10. local-model / cloud-fallback routing is not implemented.
11. WPF does not yet use Provider error `code` for code-specific UI.
12. prompt/persona composition, memory, tools, perception, behavior, and proactive runtime logic remain future phases.

Completed Phase 0 cleanup:

- `Potocol -> Protocol`: complete via `81d2747`
- canonical dependency policy: `pyproject.toml + pip install -e ".[dev]"`

## 15. Next Phase

Next:

```text
Phase 2 - Event System
```

Goal:

Introduce the Event Bus / runtime event model.

Planned scope:

- event envelope
- event routing
- subscriber boundaries
- event lifecycle / logging
- Desktop / runtime event bridge where needed

Do not pull Character, Memory, Perception, Situation, Attention, Behavior, Permission, or Tool implementation into Phase 2 unless a minimal interface is necessary for the event contract.

## 16. Phase 1 Closeout

Phase 1 changed Desktop Companion Agent from:

```text
cross-language echo vertical slice
```

into:

```text
real provider-agnostic AI MVP
```

The project now has a validated architectural foundation for the later companion-specific systems: events, character, memory, situation, attention, perception, behavior, embodiment, voice, and tools.
