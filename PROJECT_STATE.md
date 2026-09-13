# Desktop Companion Agent - Project State

> Context checkpoint: Phase 3 completed on 2026-09-13.
>
> This file is the primary context-recovery document for future development sessions. If chat context is lost, read this file first, then `docs/PHASE_3_CHECKPOINT.md`, `ARCHITECTURE.md`, `ROADMAP.md`, and the relevant subsystem design / ADR documents.

## 1. Current Status

Current phase status:

- Phase 0 - Engineering Foundation / Cross-Language Vertical Slice: **Complete**
- Phase 1 - LLM Provider / Original AI MVP: **Complete**
- Phase 2 - Event System: **Complete**
- Phase 3 - Character System: **Complete**
- Next roadmap phase: **Phase 4 - Memory System**

Current implementation baseline before the Phase 3 final-documentation commit:

```text
a172a43 Update Agent integration test fixtures
```

Phase 3 added a structured Character System, runtime temporal context, and provider-neutral prompt/context composition without replacing the verified Provider/WebSocket/EventBus runtime.

The verified real vertical slice is now:

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
  -> Clock.now()
  -> TemporalContext
  -> active CharacterDefinition
  -> PromptContextComposer
  -> LLMRequest
  -> LLMProvider
  -> DeepSeekProvider
  -> DeepSeek API
  -> LLMResponse
  -> protocol response
  -> WPF UI
```

Alongside that request/response path, the Python runtime continues to own the in-process EventBus foundation introduced in Phase 2.

## 2. What Phase 3 Proved

Phase 3 proved that stable Character identity and runtime temporal truth can participate in the real LLM request path without collapsing Provider, Event, factual-state, or future Memory boundaries.

Verified properties:

- Character definition is explicit domain data rather than an ad-hoc prompt blob.
- TOML is a human-editable external serialization format, not the Character domain model.
- the default built-in Character is `Aria`.
- runtime Character selection belongs to the composition root.
- external Character definition directories and active Character IDs are configurable.
- Character does not own Memory.
- Character does not own Internal State.
- Character intent does not grant permission or tool authority.
- Character fiction does not override mathematics, science, runtime facts, user facts, or tool results.
- `Clock` is the sole runtime source of current date/time truth.
- `TemporalContext` is a derived per-request snapshot.
- `PromptContextComposer` consumes prepared context and produces a provider-neutral `LLMRequest`.
- Composer does not load Character, query Clock, query Memory, call Provider, publish Events, permission-check, or execute tools.
- Agent receives Character / Composer / Clock through explicit dependency injection.
- Provider error mapping remains unchanged.
- unsupported Desktop messages are still rejected before Provider execution.
- Character loading failure does not create Provider or EventBus resources.
- the real WPF -> Python -> DeepSeek -> Python -> WPF path works with Character and Temporal Context active.
- manual runtime acceptance confirmed Aria identity/style, mathematically correct `sqrt(2)` reasoning, correct runtime date/weekday, and factual-reality priority over Character fiction.
- deliberate Provider authentication failure and sensitive-log review remained safe after Character integration.

Phase 3 deliberately did **not** implement Memory persistence, User Profile learning, Internal State, Scheduler, Perception, Situation, Attention, Behavior, Permission, Tools, Voice, Avatar, dynamic Character switching UI, Character hot reload, or a Desktop Event Bridge.

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
  -> load / resolve active Character
  -> create PromptContextComposer
  -> create SystemClock
  -> create DeepSeekProvider
  -> establish Provider cleanup boundary
  -> create EventBus(queue_capacity=Settings)
  -> create Agent(provider, character, composer, clock)
  -> create WebSocketServer(agent)
  -> await EventBus.start()
  -> await WebSocketServer.run()
  -> finally await EventBus.close()
  -> finally await Provider.aclose()
```

Implemented modules now include:

```text
src/agent_core/
├── characters/
│   ├── definitions/
│   │   └── aria.toml
│   ├── errors.py
│   ├── loader.py
│   └── models.py
├── communication/
│   └── websocket_server.py
├── composition/
│   └── composer.py
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
├── temporal/
│   ├── clock.py
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
- structured `CharacterDefinition` domain
- human-editable TOML Character definitions
- built-in default Character `Aria`
- runtime active-Character selection through Settings
- explicit `Clock` / `SystemClock` temporal authority
- derived per-request `TemporalContext`
- provider-neutral `PromptContextComposer`
- runtime rules that preserve factual truth over Character fiction
- explicit Agent injection of Character / Composer / Clock
- composition-root ownership of Character selection, EventBus, and Provider lifetimes

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

Phase 1-3 runtime performs zero automatic Provider retries.

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

Phases 2 and 3 did not modify C# source.

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
DCA_CHARACTER_DEFINITIONS_DIR
DCA_ACTIVE_CHARACTER_ID
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
- Phases 2 and 3 added no third-party dependency

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

### Phase 3 checkpoint

Phase 3 final project-owner acceptance on 2026-09-13:

```text
python -m pytest -q
-> 145 passed in 4.99s

python -m ruff check .
-> All checks passed!

python -m mypy src
-> Success: no issues found in 51 source files

git diff --check
-> clean
```

C# build:

```text
N/A for Phase 3 final acceptance because Phase 3 changed no C# source.
```

Manual runtime acceptance:

- Python Agent Core started successfully.
- WPF connected successfully.
- default Character identified herself as `Aria`.
- ordinary conversation showed visible Character style without blocking task-oriented use.
- a real `sqrt(2)` irrationality proof remained mathematically correct.
- runtime temporal context produced `2026-09-13`, Sunday.
- the model explicitly preferred verifiable mathematical / scientific reality over conflicting Character settings.
- real DeepSeek-backed responses returned through WPF.
- deliberate Provider authentication failure still mapped to the existing safe protocol error boundary.
- runtime log review did not reveal API keys, Authorization headers, complete user/system prompts, complete model responses, raw response bodies, or reasoning content.

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

Phase 2 implemented the Event infrastructure layer. Phase 3 added Character, temporal truth, and prompt/context composition. Situation, Attention, Behavior, Perception, Permission, Tools, Voice, and Avatar remain future work.

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

Phase 3 ADRs:

```text
0013 Character definitions are structured domain data
0014 Character consumes User Context; Memory owns User Profile
0015 Runtime temporal truth comes from Clock context
```

## 10. Phase 3 Git Anchors

Confirmed development anchors:

```text
ecc1fce Record Phase 3 character architecture decisions
e648a19 Establish Phase 3 character domain models
21e658f Add Character definition loading
39f8537 Add runtime temporal context
cb1c5b0 Add Character context composition
5ecee74 Integrate Character context into runtime
a172a43 Update Agent integration test fixtures
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
12. WPF still renders Markdown / LaTeX syntax as plain text.
13. dynamic Character switching UI is not implemented.
14. Character hot reload is not implemented.
15. Memory / User Profile persistence remains future work.
16. Runtime Events are internal only; there is no Desktop Event Bridge yet.
17. Event persistence, replay, priority, wildcard routing, dynamic unsubscribe, multiple dispatcher workers, and restart/supervision policy remain intentionally absent from the current Event baseline.
18. The repository does not yet enforce a canonical text EOL policy through a dedicated `.gitattributes`; keep `git diff --check` in the review workflow.
19. Generated caches, logs, local `.env`, build outputs, and `.git` must remain excluded from checkpoint/source archives.

## 12. Phase 4 Entry Point

Next roadmap phase:

> Phase 4 - Memory System

Goal:

Introduce explicit Memory ownership and separated memory domains without allowing temporary, fictional, or low-confidence state to contaminate factual user context.

Expected scope:

- User Profile
- Working Context
- Episodic Memory
- Long-term Memory
- Relationship Memory
- Today Memory
- Fictional Ephemeral State
- retrieval / persistence / retention / conflict rules

Phase 4 must preserve:

```text
Character != Memory
Character != Internal State
TemporalContext != Memory
Prompt composition != Permission
Intent != Permission
Real State != Fictional State
```

Character and `PromptContextComposer` should consume prepared memory/user context rather than owning Memory persistence, retrieval, learning, retention, or conflict behavior.

Before implementation:

- recover context from the Phase 3 checkpoint and current code
- preserve the verified Provider/WebSocket/EventBus/Character runtime
- design Memory ownership and retrieval contracts before implementation
- do not redesign Character merely to make Memory convenient
- do not allow fictional or ephemeral state to enter factual user-profile storage

## 13. Context Recovery Procedure

When continuing this project in a new conversation/session:

1. read `PROJECT_STATE.md`
2. read `docs/PHASE_3_CHECKPOINT.md`
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
