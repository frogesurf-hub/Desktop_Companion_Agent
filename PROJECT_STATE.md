# Desktop Companion Agent - Project State

> Context checkpoint: Phase 2 completed on 2026-09-12.
>
> This file is the primary context-recovery document for future development sessions. If chat context is lost, read this file first, then `docs/PHASE_2_CHECKPOINT.md`, `ARCHITECTURE.md`, `ROADMAP.md`, and the relevant subsystem design / ADR documents.

## 1. Current Status

Current phase status:

- Phase 0 - Engineering Foundation / Cross-Language Vertical Slice: **Complete**
- Phase 1 - LLM Provider / Original AI MVP: **Complete**
- Phase 2 - Event System: **Complete**
- Next roadmap phase: **Phase 3 - Character System**

Current implementation baseline before the Phase 2 final-documentation commit:

```text
ccee378 Integrate event bus into runtime composition
```

Phase 2 added a provider-independent, business-domain-neutral runtime Event System without replacing or rewriting the working Phase 1 chat path.

The verified real vertical slice remains:

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

Alongside that request/response path, the Python runtime now owns an in-process EventBus foundation for future proactive modules.

## 2. What Phase 2 Proved

Phase 2 proved that the runtime can introduce an explicit asynchronous Event boundary without breaking the Phase 1 Provider/WebSocket vertical slice.

Verified properties:

- Runtime Events are immutable facts / notifications, not commands, permission grants, requests, or return-value carriers.
- Runtime Event metadata has a stable base contract.
- Event producers can depend on a narrow `EventPublisher` capability instead of owning EventBus lifecycle or subscription management.
- the concrete EventBus is asynchronous and in-process.
- subscriptions use exact Event types under the Phase 2 baseline.
- publication acceptance is bounded and explicit.
- queue overload fails fast with `EventBusFullError`; Phase 2 does not wait indefinitely for queue space.
- queue admission order determines Event dispatch order.
- subscribers for one Event may execute concurrently.
- the next Event does not begin dispatch until the current Event's subscribers settle.
- ordinary subscriber exceptions are isolated and do not stop sibling handlers or later Events.
- cancellation remains asyncio control flow and is not treated as an ordinary subscriber failure.
- EventBus lifecycle and graceful drain behavior are explicit and tested.
- EventBus observability records safe metadata without logging full Event payloads by default.
- EventBus runtime ownership belongs to the Python composition root.
- Provider cleanup remains protected when EventBus construction/start/close or server execution fails.
- the real WPF -> Python -> DeepSeek -> Python -> WPF path still works after EventBus integration.

Phase 2 deliberately did **not** implement Character, Memory, Perception, Situation, Attention, Behavior, Permission, Tools, Voice, Avatar, or a Desktop Event Bridge.

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
  -> establish Provider cleanup boundary
  -> create EventBus(queue_capacity=Settings)
  -> create Agent(provider)
  -> create WebSocketServer(agent)
  -> await EventBus.start()
  -> await WebSocketServer.run()
  -> finally await EventBus.close()
  -> finally await Provider.aclose()
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
├── events/
│   ├── __init__.py
│   ├── base.py
│   ├── bus.py
│   ├── errors.py
│   └── models.py
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

Implemented behavior includes:

- typed runtime settings via `pydantic-settings`
- `.env` / environment-variable support with `DCA_` prefix
- secrets represented with `SecretStr`
- `pyproject.toml` as the canonical Python dependency source
- OpenAI Python SDK isolated inside the DeepSeek adapter boundary
- console + rotating-file logging
- local WebSocket server
- JSON message parse / serialize
- malformed-input isolation
- async provider-neutral `LLMProvider` contract
- DeepSeek OpenAI-compatible Chat Completions adapter
- provider-neutral error hierarchy / safe Desktop error mapping
- explicit Provider timeout / zero SDK retries / asyncio cancellation propagation
- immutable Runtime Event foundation
- asynchronous bounded in-process EventBus
- exact-type Event routing
- fail-fast overload admission
- explicit EventBus lifecycle / graceful drain
- subscriber concurrency + ordinary failure isolation
- safe Event lifecycle observability
- composition-root ownership of EventBus and Provider lifetimes

### 3.2 Current DeepSeek Baseline

Configuration:

```text
DCA_MODEL_PROVIDER=deepseek
DCA_DEEPSEEK_API_KEY=<local secret>
DCA_DEEPSEEK_MODEL=deepseek-flash
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

`Agent` does not import `AsyncOpenAI`, DeepSeek HTTP status types, or vendor SDK exceptions.

### 3.3 Provider Contract

Agent-facing contract:

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

Phase 1/2 runtime performs zero automatic Provider retries.

### 3.4 Event Contract

Base Runtime Event:

```text
RuntimeEvent
├── source: str
├── event_id: UUID
├── occurred_at: timezone-aware UTC datetime
├── correlation_id: UUID | None
└── causation_id: UUID | None
```

Contract properties:

- frozen dataclass
- slot-based
- keyword-only construction
- default `event_id` generated with UUID
- default occurrence time generated in UTC
- aware timestamps normalized to UTC
- naive timestamps rejected
- blank `source` rejected
- Event-specific payload fields are added by concrete Event subclasses

Public capability boundary:

```python
class EventPublisher(Protocol):
    async def publish(self, event: RuntimeEvent) -> None: ...
```

Subscriber boundary is an asynchronous callable typed to one Runtime Event type.

### 3.5 EventBus Baseline

Phase 2 EventBus semantics:

```text
scope: in-process Python runtime
execution: async
queue: bounded in-memory queue
routing: exact concrete Event type
subscription registration: static before running
publish result: queue admission only
queue-full behavior: fail fast with EventBusFullError
ordering: queue admission order
subscriber execution for one Event: concurrent
cross-Event execution: next Event waits until current handlers settle
ordinary handler failure: isolated
persistence: none
wildcards: none
priority: none
retry: none
multiple dispatcher workers: none
restart policy: none
```

Lifecycle:

```text
NEW
  -> RUNNING
  -> CLOSING
  -> CLOSED
```

Important lifecycle properties:

- publication is accepted only while the bus is RUNNING
- `close()` drains already accepted Events
- repeated close is safe under the accepted Phase 2 semantics
- close from NEW is supported
- terminal cleanup leaves no intended live EventBus tasks
- cancellation remains distinct from ordinary handler failure

### 3.6 Event Observability

EventBus logs diagnostic metadata such as:

- lifecycle transition
- Event type
- Event ID
- sanitized source
- handler identity where useful
- handler / dispatch duration where useful
- exception type for failure diagnostics

Default Event logs must not include:

- `repr(event)`
- full Event payloads
- subscriber exception messages
- dispatcher exception messages
- arbitrary sensitive payload content

Tests explicitly verify known sensitive markers do not appear in captured Event System logs.

### 3.7 C# WPF Desktop

Current Desktop layering remains:

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

The independent Desktop receive loop remains an intentional long-term capability for future proactive messages.

Phase 2 did not modify C# source.

## 4. Current Protocol

Transport:

```text
ws://127.0.0.1:8765
```

Implemented Desktop protocol message behavior:

- `chat`
- `response`
- `error`

Provider error payloads contain stable safe `code` / `message` fields.

Documented but not implemented end-to-end:

- Desktop `event`
- `permission_request`
- `tool_request`
- `tool_response`
- memory / emotion / avatar events

Important distinction:

> Python Runtime Events are an internal in-process architecture boundary. They are not automatically Desktop protocol messages.

A Desktop Event Bridge remains deferred until a concrete later-phase requirement exists.

## 5. Configuration and Dependency Baseline

Python configuration currently includes:

```text
DCA_ENVIRONMENT
DCA_RUNTIME_MODE
DCA_WEBSOCKET_HOST
DCA_WEBSOCKET_PORT
DCA_EVENT_BUS_QUEUE_CAPACITY
DCA_MODEL_PROVIDER
DCA_DEEPSEEK_API_KEY
DCA_DEEPSEEK_MODEL
DCA_DEEPSEEK_TIMEOUT_SECONDS
DCA_DEEPSEEK_THINKING_ENABLED
DCA_LOG_LEVEL
```

EventBus queue capacity:

```text
default: 256
constraint: > 0
role: operational configuration, not an architecture constant
```

Important:

- real `.env` files are ignored and must never be committed
- API keys remain local secrets
- `pyproject.toml` is the canonical Python dependency source
- `src/agent_core/requirements.txt` remains legacy duplicate metadata and must not receive new dependencies
- Phase 2 added no third-party dependency

## 6. Validation Baseline

### Phase 1 checkpoint

Phase 1 final acceptance on 2026-09-09:

```text
66 pytest tests passed
Ruff passed
mypy passed on 28 source files
```

Real acceptance included ConnectionProbe, WPF, DeepSeek, deliberate authentication failure, and sensitive-log inspection.

### Phase 2 checkpoint

Phase 2 final project-owner acceptance on 2026-09-12:

```text
python -m pytest -q
-> 104 passed in 4.73s

python -m ruff check .
-> All checks passed!

python -m mypy src
-> Success: no issues found in 38 source files
```

C# build:

```text
N/A for Phase 2 final acceptance because Phase 2 changed no C# source.
```

Manual runtime regression:

- Python Agent Core started normally.
- EventBus logged `event_bus_started queue_capacity=256`.
- WPF connected successfully.
- two consecutive WPF messages received real DeepSeek responses.
- Python observed two successful DeepSeek HTTP 200 responses.
- EventBus shutdown logged `event_bus_closing` and `event_bus_closed`.
- the Phase 1 vertical slice remained operational after Phase 2 integration.

Known existing shutdown debt observed during manual acceptance:

- closing WPF may produce `websockets.exceptions.ConnectionClosedError: no close frame received or sent` on the Python server side.
- this is an existing Desktop/WebSocket shutdown-hardening issue and is not an EventBus shutdown failure.

## 7. Development Baseline

Python:

- Python 3.11
- pytest
- Ruff
- mypy
- `pydantic-settings`
- `websockets`
- `openai`
- editable install through `pip install -e ".[dev]"`

Desktop:

- C# WPF
- target framework: .NET 8 Windows

Development workflow:

```text
Requirement / Goal
  -> Context Recovery
  -> Design
  -> Architecture Review
  -> ADR when required
  -> Task Breakdown
  -> Implementation
  -> Targeted pytest / Ruff / mypy
  -> Working diff review
  -> Stage specific files
  -> Staged diff review
  -> Commit
  -> Phase-final project-owner acceptance
  -> Final documentation / checkpoint
```

During implementation, use targeted checks. At a phase-final gate, the project owner runs the complete quality trio:

```powershell
python -m pytest -q
python -m ruff check .
python -m mypy src
```

## 8. Architectural Principles That Must Not Be Lost

### 8.1 Companion, not a turn-based chatbot

The runtime must eventually support proactive output without requiring a user request.

The C# independent receive loop and the Phase 2 Event System both preserve this direction.

### 8.2 Long-term proactive flow

```text
External World
  -> Perception
  -> Events
  -> Situation Engine
  -> Attention Engine
  -> Behavior Engine
  -> Voice / Avatar / Tools
```

Phase 2 implements only the Event infrastructure layer from this flow.

### 8.3 Intent != Permission

Character intent never grants system permission.

Runtime Events must not be interpreted as implicit authorization.

Sensitive actions must pass through a dedicated Permission / capability boundary in a later phase.

### 8.4 Real and fictional state must remain separate

Fictional state must not contaminate user facts, factual reasoning, memory retrieval, or tool decisions.

### 8.5 Local-first, cloud-enhanced

Target runtime modes remain Offline / Local / Hybrid / Cloud.

Cloud failure must not erase the companion's basic local runtime behavior.

The current implementation has safe Provider failure handling but still has no local fallback router.

### 8.6 Stable interfaces over hidden coupling

Continue using:

- Protocol / interface boundaries
- adapters
- Event boundaries
- dependency injection
- composition roots
- explicit lifecycle ownership

Do not move Provider, Memory, Tool, Perception, or Agent reasoning logic into the UI.

## 9. Important Persistent Decisions

Phase 0 ADRs:

```text
0001 WPF Desktop + Python Agent Core
0002 WebSocket Desktop/Core transport
0003 layered Desktop client
0004 local-first Provider abstraction
0005 Intent is not Permission
0006 real / fictional state separation
```

Phase 1 ADRs:

```text
0007 async non-streaming Provider contract
0008 DeepSeek V4 Flash via async OpenAI-compatible Chat Completions
0009 Provider error isolation and Desktop error mapping
```

Phase 2 ADRs:

```text
0010 Runtime Events are facts; commands remain explicit boundaries
0011 async bounded in-process EventBus
0012 fail-fast EventBus overload admission
```

ADR 0012 supersedes only the queue-full waiting/backpressure portion of ADR 0011. Other accepted ADR 0011 decisions remain in force.

## 10. Phase 2 Git Anchors

Confirmed development anchors:

```text
c0ace0d Design Phase 2 event system
31734de Establish Phase 2 runtime event contracts
242ed9e Correct Phase 2 event bus overload architecture
55c8624 Implement Phase 2 event bus core
ad23a10 Add event bus lifecycle and failure isolation
5b161c1 Add event lifecycle observability
ccee378 Integrate event bus into runtime composition
```

The repository `git log --oneline` remains authoritative for complete history.

## 11. Known Technical Debt / Cleanup Candidates

1. Desktop WebSocket endpoint remains hard-coded in `App.xaml.cs`; shared endpoint configuration is not implemented.
2. C# automated tests still do not exist.
3. Python `Message` validation remains lightweight; documented protocol versioning is not implemented.
4. WPF reconnect / retry / connection-state recovery is not implemented.
5. Desktop shutdown/disposal is not hardened; abrupt WPF disconnect can produce a missing close-frame error in Python WebSocket logs.
6. `src/agent_core/requirements.txt` remains legacy duplicate dependency metadata.
7. Provider roles remain limited to `system`, `user`, and `assistant`.
8. streaming remains intentionally unsupported in the current Provider path.
9. automatic Provider retries remain intentionally unsupported.
10. local-model / cloud-fallback routing is not implemented.
11. WPF displays Provider error messages but does not yet implement code-specific UI behavior.
12. prompt/persona composition, Memory, Tools, Perception, Situation, Attention, Behavior, Avatar, and Voice remain future work.
13. Runtime Events are internal only; there is no Desktop Event Bridge yet.
14. Event persistence, replay, priority, wildcard routing, dynamic unsubscribe, multiple dispatcher workers, and restart/supervision policy are intentionally absent from the Phase 2 baseline.
15. The repository does not yet enforce a canonical text EOL policy through a dedicated `.gitattributes`; keep `git diff --check` in the review workflow.
16. Generated caches, logs, local `.env`, build outputs, and `.git` must remain excluded from checkpoint/source archives.

## 12. Phase 3 Entry Point

Next roadmap phase:

> Phase 3 - Character System

Goal:

Define stable character and user-context boundaries on top of the Phase 0-2 runtime foundation.

Expected roadmap scope:

- Identity
- Persona
- Speech Style
- Preferences
- Core Values
- User Profile boundary
- prompt / context composition interfaces

Before implementation:

- recover context from the Phase 2 checkpoint and current code
- preserve the verified Provider/WebSocket/EventBus runtime
- design Character System contracts before implementation
- do not allow personality to override truth, permission, security, or factual-state boundaries
- do not pull Memory, Perception, Situation, Attention, Behavior, Permission, Tools, Voice, or Avatar implementation into Phase 3 unless a minimal contract boundary is strictly required

## 13. Context Recovery Procedure

When continuing this project in a new conversation/session:

1. read `PROJECT_STATE.md`
2. read `docs/PHASE_2_CHECKPOINT.md`
3. read `ARCHITECTURE.md`
4. read `ROADMAP.md`
5. read `DESIGN.md`
6. read `TECH_STACK.md`
7. read `THIRD_PARTY.md`
8. read `docs/DEVELOPMENT.md`
9. read the current phase's design / architecture-review / ADR documents
10. inspect current source files, `git status`, and recent Git history
11. treat current repository code as authoritative when historical documentation conflicts with implementation

Historical checkpoint and design documents remain useful for development history but may intentionally describe earlier implementation states. Chat history is supplementary context, not the authoritative project state.
