# Desktop Companion Agent - Project State

> Context checkpoint: Phase 1 completed on 2026-09-09.
>
> This file is the primary context-recovery document for future development sessions. If chat context is lost, read this file first, then `ARCHITECTURE.md`, `ROADMAP.md`, and the relevant subsystem documentation.

## 1. Current Status

Current phase:

- Phase 0: **Complete**
- Phase 1: **Complete**
- Next phase: **Phase 2 - Event System**
- Phase 1 implementation checkpoint before the final documentation commit: `cf3348d Wire DeepSeek provider into runtime`

Phase 1 completed the original AI MVP by replacing the Phase 0 echo path with a real provider-agnostic LLM path:

```text
WPF UI
  -> MainWindowViewModel
  -> AgentClientService
  -> IAgentConnection
  -> WebSocketAgentConnection
  -> JSON / AgentMessage
  -> WebSocket
  -> Python WebSocketServer
  -> Message
  -> Agent.process_message()
  -> LLMProvider
  -> DeepSeekProvider
  -> DeepSeek API
  -> LLMResponse
  -> protocol response
  -> WPF UI
```

The temporary Phase 0 `EchoLLMProvider` has been removed from the runtime.

The real end-to-end Phase 1 path was manually verified with both:

- `tools/DesktopCompanion.ConnectionProbe`
- the WPF Desktop UI

## 2. What Phase 1 Proved

Phase 1 proved that the cross-language runtime can support a real cloud LLM without coupling Agent Core to one provider SDK.

Verified properties:

- `Agent` depends on a provider-neutral asynchronous `LLMProvider` contract.
- DeepSeek-specific SDK types remain inside the concrete adapter.
- Provider request / response models are immutable and provider-neutral.
- Provider failures are translated into a provider-neutral error hierarchy.
- Provider failures are mapped to stable, safe Desktop protocol error codes/messages.
- a Provider failure does not terminate the active WebSocket connection.
- real API-key handling remains inside Settings / composition-root boundaries.
- the DeepSeek client is closed by the composition root even when the server exits with an exception.
- deterministic automated tests require neither external network access nor a real API key.
- the real WPF -> Python -> DeepSeek -> Python -> WPF path works.

The original AI MVP is now complete.

## 3. Current Implemented Architecture

### 3.1 Python Agent Core

Entry point:

```text
src/agent_core/main.py
```

Current composition:

```text
main.py
  -> get_settings()
  -> setup_logging()
  -> create DeepSeekProvider
  -> Agent(provider)
  -> WebSocketServer(agent)
  -> serve_forever()
  -> finally provider.aclose()
```

Implemented modules now include:

```text
src/agent_core/
├── communication/
│   └── websocket_server.py
├── config/
│   └── settings.py
├── core/
│   ├── agent.py
│   └── message.py
├── observability/
│   └── logging.py
├── providers/
│   ├── __init__.py
│   ├── base.py
│   ├── deepseek.py
│   ├── errors.py
│   └── models.py
├── tests/
└── main.py
```

Implemented behavior:

- typed runtime settings via `pydantic-settings`
- `.env` / environment-variable support with `DCA_` prefix
- secrets represented with `SecretStr`
- `pyproject.toml` as the canonical Python dependency source
- OpenAI Python SDK used only inside the DeepSeek adapter boundary
- console + rotating-file logging
- local WebSocket server
- JSON message parse / serialize
- protocol errors for invalid JSON, invalid structure, and binary messages
- invalid message isolation: one bad message does not kill the connection
- async provider-neutral LLM contract
- immutable provider-neutral message / request / response models
- deterministic fake provider infrastructure
- DeepSeek OpenAI-compatible Chat Completions adapter
- non-streaming Phase 1 provider path
- explicit provider timeout
- SDK automatic retries disabled
- asyncio cancellation propagation
- provider-neutral error hierarchy and retryability semantics
- safe Provider Error -> Desktop protocol mapping
- composition-root ownership of Provider lifecycle

### 3.2 Current DeepSeek Baseline

Phase 1 configuration:

```text
DCA_MODEL_PROVIDER=deepseek
DCA_DEEPSEEK_API_KEY=<local secret>
DCA_DEEPSEEK_MODEL=deepseek-v4-flash
DCA_DEEPSEEK_TIMEOUT_SECONDS=60
DCA_DEEPSEEK_THINKING_ENABLED=false
```

Provider implementation baseline:

```text
client: openai.AsyncOpenAI
base URL: https://api.deepseek.com
API style: OpenAI-compatible Chat Completions
streaming: false
thinking: explicitly disabled by default
application timeout: 60 seconds by default
SDK max_retries: 0
```

The model, timeout, and thinking flag are configurable.

`Agent` does not import `AsyncOpenAI`, DeepSeek HTTP status types, or vendor SDK exceptions.

### 3.3 Provider Contract

Public Agent-facing contract:

```python
async def generate(request: LLMRequest) -> LLMResponse
```

Provider-neutral models:

```text
LLMMessage
LLMRequest
LLMResponse
LLMRole
```

Current supported roles:

```text
system
user
assistant
```

Provider error boundary:

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

Phase 1 performs zero automatic retries. Retryability flags record semantics for future reliability work only.

### 3.4 Desktop Error Mapping

Provider failures are exposed to Desktop using:

```json
{
  "type": "error",
  "payload": {
    "code": "PROVIDER_TIMEOUT",
    "message": "AI provider request timed out."
  }
}
```

Stable Phase 1 Provider error codes:

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

The current WPF client still primarily displays `payload["message"]`; it does not yet implement code-specific UI behavior.

### 3.5 C# WPF Desktop

Current layers remain:

```text
App.xaml.cs                 Composition Root
      |
      v
MainWindow                  Presentation view
      |
      v
MainWindowViewModel         Presentation state / interaction
      |
      v
AgentClientService          Application-level Agent client behavior
      |
      v
IAgentConnection            Transport abstraction
      |
      v
WebSocketAgentConnection    WebSocket + JSON transport
      |
      v
AgentMessage                Protocol model
```

Implemented behavior:

- connect / disconnect to Agent Core
- send `AgentMessage`
- receive fragmented WebSocket messages correctly
- independent background receive loop
- `MessageReceived` / `ReceiveFailed` events
- WPF Dispatcher handoff for UI updates
- basic connection status
- basic chat input and message history
- display real DeepSeek responses
- display safe Provider error messages

### 3.6 Connection Probe

Diagnostic project:

```text
tools/DesktopCompanion.ConnectionProbe/
```

Phase 1 real acceptance verified:

```text
C# ConnectionProbe
  -> WebSocket
  -> Python Agent
  -> DeepSeekProvider
  -> DeepSeek API
  -> Python
  -> C#
```

## 4. Current Protocol

Transport:

```text
ws://127.0.0.1:8765
```

Message envelope:

```json
{
  "id": "uuid",
  "type": "chat",
  "timestamp": "ISO8601 UTC",
  "source": "desktop",
  "payload": {}
}
```

Implemented message behavior:

- `chat`
- `response`
- `error`

Provider error messages now include a stable `payload.code` and safe `payload.message`.

Documented but not yet implemented end-to-end:

- `event`
- `permission_request`
- `tool_request`
- `tool_response`
- memory / emotion / avatar events

## 5. Configuration and Dependency Baseline

Python configuration currently includes:

```text
DCA_ENVIRONMENT
DCA_RUNTIME_MODE
DCA_WEBSOCKET_HOST
DCA_WEBSOCKET_PORT
DCA_MODEL_PROVIDER
DCA_DEEPSEEK_API_KEY
DCA_DEEPSEEK_MODEL
DCA_DEEPSEEK_TIMEOUT_SECONDS
DCA_DEEPSEEK_THINKING_ENABLED
DCA_LOG_LEVEL
```

Important:

- real `.env` files are ignored and must never be committed
- `DCA_DEEPSEEK_API_KEY` is consumed only by the runtime composition root / concrete provider boundary
- `pyproject.toml` is the canonical Python dependency source
- `src/agent_core/requirements.txt` is legacy duplicate dependency metadata and should not receive new dependencies

Current runtime dependency added in Phase 1:

```text
openai>=3.10.0,<4
```

The Phase 1 acceptance environment used OpenAI Python SDK `3.10.0`.

## 6. Validation Baseline

Phase 1 final project-owner acceptance on 2026-09-09:

```text
python -m pytest -q
-> 66 passed in 4.69s

python -m ruff check .
-> All checks passed!

python -m mypy src
-> Success: no issues found in 28 source files
```

Manual acceptance:

- real `.env` confirmed ignored
- safe configuration preflight passed
- Python Agent Core started with DeepSeek
- ConnectionProbe received a real DeepSeek response
- WPF received a real DeepSeek response
- a second WPF request succeeded on the same connection
- deliberately invalid API key produced the safe WPF message:
  `AI provider authentication failed.`
- Python logged the provider-neutral category `ProviderAuthenticationError`
- logs were inspected for API-key, prompt, response, authorization-header, raw-body, and reasoning-content leakage
- valid runtime configuration was restored
- final pre-documentation Git working tree was clean

## 7. Development Baseline

Python:

- Python 3.11
- pytest
- Ruff
- mypy
- `pydantic-settings`
- `websockets`
- `openai`
- editable install through `pyproject.toml`

Desktop:

- C# WPF
- target framework: .NET 8 Windows

Development workflow:

```text
Requirement / Goal
  -> Design
  -> Task Breakdown
  -> Implementation
  -> Targeted Tests
  -> Quality Checks
  -> Documentation Update
  -> Git Review
  -> Commit
  -> Final project-owner acceptance
```

AI-assisted development rule:

- development AI runs only tests directly related to its modifications
- no full pytest by default
- project owner performs final full-suite acceptance

## 8. Architectural Principles That Must Not Be Lost

### 8.1 Companion, not a turn-based chatbot

The runtime must eventually support proactive output without requiring a user request.

The C# independent receive loop already preserves this direction.

### 8.2 Situation Engine + Attention Engine are core differentiators

Long-term flow:

```text
External World
  -> Perception
  -> Events
  -> Situation Engine
  -> Attention Engine
  -> Behavior Engine
```

The Agent should decide whether to ignore, notice, speak, wait, move, or request an action.

### 8.3 Intent != Permission

Character intent never grants system permission.

Sensitive actions must pass through a dedicated permission/capability boundary.

### 8.4 Real and fictional state must remain separate

Fictional daily-life flavor must not contaminate:

- user facts
- factual reasoning
- memory retrieval
- tool decisions

### 8.5 Local-first, cloud-enhanced

Target runtime modes remain:

- Offline
- Local AI
- Hybrid
- Cloud

Long-term requirement:

> Cloud failure must not erase the companion's basic local runtime behavior.

Phase 1 provides safe cloud-provider failure handling but does **not** yet implement local fallback or provider routing.

### 8.6 Stable interfaces over hidden coupling

Continue using:

- interfaces
- adapters
- event boundaries
- dependency injection
- composition roots

Do not move transport, protocol, provider, memory, or tool implementation directly into UI code.

## 9. Third-Party Reference Decisions

Primary references carried forward from Phase 0:

- OpenMeido: desktop companion / memory / provider / proactive interaction reference
- Project AIRI: digital-life, avatar, voice, extensible companion reference
- screenpipe: event-driven desktop perception and activity timeline reference
- Microsoft UFO: Windows-native / UI Automation reference
- Agent-S: vision / GUI computer-use fallback reference

Reference principle:

- borrow architecture and lessons, not entire product architecture
- respect each project's license before copying code
- prefer reimplementation of project-specific core systems

See `THIRD_PARTY.md` for the persistent reference register.

## 10. Important Phase 1 Decisions

Persistent Phase 1 ADRs:

```text
0007 async non-streaming Provider contract
0008 DeepSeek V4 Flash via async OpenAI-compatible Chat Completions
0009 Provider error isolation and Desktop error mapping
```

Important decisions:

- Provider contract is asynchronous.
- Phase 1 is non-streaming.
- default configured model is `deepseek-v4-flash`.
- thinking is explicitly disabled by default.
- application timeout defaults to 60 seconds.
- SDK automatic retries are disabled.
- cancellation propagates as asyncio control flow.
- vendor exceptions do not cross the Provider boundary.
- Provider diagnostics do not cross the Desktop protocol boundary.

## 11. Known Technical Debt / Cleanup Candidates

Known after Phase 1:

1. Desktop WebSocket endpoint remains hard-coded in `App.xaml.cs`; Desktop-side configuration/shared endpoint configuration is not implemented.
2. C# automated tests still do not exist. Current C# confidence comes from successful runtime/build behavior, ConnectionProbe, and manual WPF acceptance.
3. Python `Message` validation remains lightweight; the documented protocol version field is not implemented.
4. WPF reconnect / retry / connection-state recovery is not implemented.
5. Desktop shutdown/disposal behavior works for the MVP but has not been hardened for long-running production use.
6. `src/agent_core/requirements.txt` remains as legacy duplicate dependency metadata. `pyproject.toml` is now canonical; the legacy file should eventually be removed or clearly retired in a dedicated maintenance task.
7. The current Provider model boundary supports only `system`, `user`, and `assistant` roles.
8. Phase 1 has no streaming support by design.
9. Phase 1 has no automatic provider retries by design.
10. Phase 1 has no local-model or cloud-fallback routing; that remains a later roadmap item.
11. WPF currently displays Provider error `message` but does not make code-specific UI decisions from `payload.code`.
12. Phase 1 sends a minimal chat request; prompt/persona composition, memory, tools, and behavior context are not implemented.
13. Generated development caches and local environment files must remain excluded from source/checkpoint archives.

Completed cleanup from the Phase 0 list:

- `Potocol/ -> Protocol/` was completed in commit `81d2747`.
- canonical dependency policy is now `pyproject.toml + pip install -e ".[dev]"`.

## 12. Phase 2 Entry Point

Next phase:

> Phase 2 - Event System

Goal:

Establish the Event Bus / runtime event model so future modules communicate through explicit event boundaries rather than hard-calling each other.

Expected Phase 2 scope from `ROADMAP.md`:

- event envelope
- event routing
- subscriber boundaries
- event lifecycle / logging
- Desktop / runtime event bridge where needed

Before implementation:

- treat the current Phase 1 repository state and this checkpoint as the baseline
- preserve the working Provider / WebSocket vertical slice
- design the Event System before changing runtime coupling
- do not pull Character, Memory, Perception, Situation, Attention, or Tool behavior into Phase 2 unless the event contract strictly requires a minimal boundary

## 13. Context Recovery Procedure

When continuing this project in a new conversation/session:

1. read `PROJECT_STATE.md`
2. read `docs/PHASE_1_CHECKPOINT.md`
3. read `ARCHITECTURE.md`
4. read `ROADMAP.md`
5. read `DESIGN.md`
6. read `TECH_STACK.md`
7. read `THIRD_PARTY.md`
8. read `docs/DEVELOPMENT.md`
9. read the subsystem design / ADR documents relevant to the current task
10. inspect current source files, `git status`, and recent Git history
11. treat repository code as authoritative when historical documentation conflicts with implementation

Historical checkpoint documents remain useful for development history but can contain intentionally stale implementation details. Chat history is supplementary context, not the authoritative project state.
