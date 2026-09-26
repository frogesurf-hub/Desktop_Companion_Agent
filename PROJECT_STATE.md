# Desktop Companion Agent - Project State

> Context checkpoint: Phase 4 Memory System runtime acceptance completed; Task 12 final documentation is in progress.
>
> This file is the primary current-state recovery document. Repository code and the latest confirmed Git commit remain the source of truth when historical documents describe an earlier phase.

## 1. Current Status

Current phase status:

- Phase 0 - Engineering Foundation / Cross-Language Vertical Slice: **Complete**
- Phase 1 - LLM Provider / Original AI MVP: **Complete**
- Phase 2 - Event System: **Complete**
- Phase 3 - Character System: **Complete**
- Phase 4 - Memory System: **Complete / final documentation in progress**
- Next roadmap phase: **Phase 5 - Situation Engine**

Latest confirmed implementation checkpoint before Task 12 documentation synchronization:

```text
3d7435c fix(memory): use platform app data for default database
```

Phase 4 added a factual, durable, governable Memory subsystem while preserving the previously accepted Provider, EventBus, Character, Temporal Context, and Desktop boundaries.

The current conversational vertical slice is:

```text
WPF UI
  -> MainWindowViewModel
  -> AgentClientService
  -> WebSocketAgentConnection
  -> WebSocket
  -> Python WebSocketServer
  -> RuntimeMessageRouter
  -> Agent
  -> Clock / TemporalContext
  -> active CharacterDefinition
  -> Memory Retrieval
  -> PreparedMemoryContext
  -> PromptContextComposer
  -> LLMProvider
  -> DeepSeekProvider
  -> DeepSeek API
  -> LLMResponse
  -> protocol response
  -> WPF UI
```

Automatic learning runs after eligible chat turns through an independent Memory learning boundary.

Memory governance uses a separate request/response path:

```text
WPF Memory UI
  -> MemoryManagementViewModel
  -> IMemoryClientService
  -> correlated Agent client request
  -> WebSocket
  -> RuntimeMessageRouter
  -> MemoryProtocolHandler
  -> Memory Governance
  -> MemoryRepository
  -> SQLite
```

The Python runtime continues to own the in-process EventBus introduced in Phase 2. Memory governance requests are not implemented as EventBus RPC.

---

## 2. What Phase 4 Proved

Phase 4 proved that durable factual Memory can participate in the real desktop runtime without collapsing Character, Prompt Composition, Provider, Event, Permission, or fictional-state boundaries.

Verified properties include:

- factual Memory has explicit semantic domain, scope, lifecycle, provenance, logical identity, and revision history;
- implemented domains are `USER_PROFILE`, `WORKING_CONTEXT`, `EPISODIC`, and `RELATIONSHIP`;
- `USER_PROFILE`, `WORKING_CONTEXT`, and ordinary `EPISODIC` Memory are globally user-scoped;
- `RELATIONSHIP` Memory is scoped to one Character;
- lifecycle states are `ACTIVE`, `SUPERSEDED`, `EXPIRED`, and `DELETED`;
- edits and corrections create revisions instead of destructively replacing history;
- successful replacement atomically supersedes the previous active revision and activates the new revision;
- deleted factual content does not participate in normal retrieval and is not re-exposed through normal governance history;
- `MemoryIdentityKey` gives automatic learning a deterministic logical identity boundary;
- SQLite is the durable local factual source of truth;
- SQLAlchemy remains inside the persistence adapter boundary;
- Alembic owns schema migrations;
- runtime startup upgrades the Memory database to Alembic head before repository access;
- the default Memory database path is resolved through the operating-system user application-data directory;
- `DCA_MEMORY_DATABASE_PATH` remains an explicit override;
- Working Context retention defaults to 7 days and is configurable from 1 through 30 days;
- retrieval produces bounded `PreparedMemoryContext` rather than exposing persistence to `PromptContextComposer`;
- automatic learning is enabled by default and can be disabled independently from retrieval and governance;
- automatic extraction does not receive unrestricted persistence authority;
- explicit/high-certainty facts pass through extraction, eligibility, resolution, conflict, and commit boundaries;
- unsupported/non-explicit input does not automatically become durable factual Memory;
- retrieval failure is fail-open for ordinary chat;
- automatic-learning failure is fail-open for an otherwise valid chat response;
- user governance is fail-closed and never reports a failed durable write as success;
- Memory health is tracked independently from overall chat availability;
- Memory governance is exposed through stable WebSocket request/response capabilities;
- `RuntimeMessageRouter` routes `chat` to Agent and `memory.*` to Memory protocol handling;
- EventBus remains a facts/notifications boundary and is not used as hidden RPC;
- WPF can list, inspect, edit, delete, and inspect permitted Memory history;
- a real Memory survives complete Python Core restart;
- persisted Memory is retrieved and reaches the real Provider context path;
- corrected Memory is used instead of superseded content;
- deleted Memory is no longer available to the runtime;
- disabling automatic learning does not disable chat, existing retrieval, or governance;
- Phase 4 final runtime acceptance preserved earlier Character, Temporal, Provider, EventBus, and log-safety behavior.

Phase 4 deliberately did **not** implement Internal State, Situation, Attention, Perception, Behavior, Permission, Tools, Voice, Avatar, cloud Memory sync, multi-user accounts, vector search, embedding retrieval, or local-LLM fallback routing.

---

## 3. Current Implemented Architecture

### 3.1 Python Composition Root

Entry point:

```text
src/agent_core/main.py
```

Current high-level composition:

```text
Settings
  -> Logging
  -> active Character loading / resolution
  -> PromptContextComposer
  -> SystemClock
  -> Memory schema upgrade
  -> Memory engine / session factory / SQLiteMemoryRepository
  -> MemoryHealthTracker
  -> MemoryRetrievalService
  -> ResilientMemoryRetriever
  -> DeepSeekProvider
  -> optional Automatic Memory Learning pipeline
  -> EventBus
  -> Agent
  -> MemoryGovernanceService
  -> HealthAwareMemoryGovernanceService
  -> MemoryProtocolHandler
  -> RuntimeMessageRouter
  -> WebSocketServer
```

Lifecycle ownership remains explicit:

```text
composition root
  -> start EventBus
  -> run WebSocket server
  -> close EventBus
  -> close Provider
```

### 3.2 Memory Domain

Core concepts:

```text
Memory
MemoryRevision
MemoryDomain
MemoryScope
MemoryScopeKind
MemoryLifecycle
MemorySource
MemoryIdentityKey
```

Semantic domains:

```text
USER_PROFILE
WORKING_CONTEXT
EPISODIC
RELATIONSHIP
```

Scopes:

```text
GLOBAL_USER
CHARACTER
```

Domain/scope rules:

```text
USER_PROFILE      -> GLOBAL_USER
WORKING_CONTEXT   -> GLOBAL_USER
EPISODIC          -> GLOBAL_USER
RELATIONSHIP      -> CHARACTER
```

Lifecycle:

```text
ACTIVE
SUPERSEDED
EXPIRED
DELETED
```

Source authority, highest to lowest:

```text
USER_EDIT
USER_EXPLICIT
AUTOMATIC_EXPLICIT_FACT
SYSTEM_OBSERVED
```

Memory context never grants Tool or Permission authority.

### 3.3 Memory Persistence

Persistence architecture:

```text
Memory Domain
  -> MemoryRepository contract
  -> SQLiteMemoryRepository
  -> SQLAlchemy
  -> SQLite
```

Schema evolution:

```text
Alembic
  0001_memory
  -> 0002_identity_key
  -> 0003_identity_unique
```

Runtime schema bootstrap occurs before repository use.

Default database location:

```text
platform-specific user application-data directory
  -> Desktop Companion Agent
  -> memory.db
```

On Windows this resolves under the current user's Local App Data directory.

Explicit override:

```text
DCA_MEMORY_DATABASE_PATH
```

The database is not intended to default to the Git repository or source tree.

### 3.4 Memory Retrieval

Runtime path:

```text
user request
  -> MemoryRetrievalService
  -> MemoryRetrievalPolicy
  -> eligible ACTIVE Memory
  -> PreparedMemoryContext
  -> PromptContextComposer
  -> Provider request
```

Retrieval is query-only and does not mutate Memory.

Prepared context preserves semantic separation such as:

```text
user_profile
working_context
relevant_episodes
relationship_context
```

Relationship retrieval is restricted to the active Character.

Recoverable retrieval failure:

```text
Memory read failure
  -> Memory health degraded
  -> empty PreparedMemoryContext
  -> ordinary chat continues
```

### 3.5 Automatic Memory Learning

Runtime learning path:

```text
completed chat turn
  -> LLMMemoryCandidateExtractor
  -> MemoryLearningPolicy
  -> ExistingMemoryResolver
  -> MemoryConflictPolicy
  -> MemoryLearningService
  -> MemoryRepository
  -> SQLite
```

`ResilientMemoryTurnLearner` isolates recoverable learning failure from the already-valid chat response.

Configuration:

```text
DCA_AUTOMATIC_LEARNING_ENABLED=true
```

When disabled:

```text
new automatic learning stops
existing retrieval continues
manual governance continues
ordinary chat continues
```

Logical identity uses `MemoryIdentityKey` where a stable factual slot exists.

### 3.6 Governance and Health

Governance capabilities:

```text
list
inspect
edit
delete
history
```

Governance owns revision and deletion semantics. Desktop does not implement those business rules independently.

Failure behavior:

```text
Retrieval failure
-> fail-open for chat

Automatic-learning failure
-> fail-open for chat

Governance persistence failure
-> fail-closed for requested operation
```

Runtime health is represented separately for Memory capability state.

### 3.7 Runtime Request Routing

Current request/response routing:

```text
WebSocketServer
  -> RuntimeMessageRouter
       |- chat
       |   -> Agent
       |
       `- memory.*
           -> MemoryProtocolHandler
```

The router owns request-type routing only.

Memory protocol supports:

```text
memory.list
memory.inspect
memory.edit
memory.delete
memory.history
```

Responses use request correlation through:

```text
request Message.id
-> response payload.request_id
```

Stable Memory protocol error codes include:

```text
MEMORY_INVALID_REQUEST
MEMORY_NOT_FOUND
MEMORY_DELETED
MEMORY_INVALID_STATE
MEMORY_OPERATION_FAILED
```

### 3.8 Character / Temporal / Composer Boundary

Phase 3 boundaries remain valid:

- Character definition owns persona/identity/style data, not factual Memory;
- `Clock` remains the runtime current-time authority;
- `TemporalContext` remains one derived per-request snapshot;
- `PromptContextComposer` consumes already-prepared Character, Temporal, and Memory context;
- Composer does not query persistence, resolve conflicts, learn Memory, call Provider, publish Events, permission-check, or execute Tools;
- Character fiction cannot override real runtime facts;
- Character intent and Memory content do not grant Permission.

### 3.9 Provider Layer

Provider-neutral Agent contract:

```python
async def generate(request: LLMRequest) -> LLMResponse
```

Concrete current provider:

```text
DeepSeekProvider
  -> openai.AsyncOpenAI
  -> DeepSeek OpenAI-compatible Chat Completions
```

Current baseline:

```text
async
non-streaming
thinking disabled by default
60-second default application timeout
zero automatic SDK retries
asyncio cancellation propagation
safe provider-neutral errors
```

### 3.10 Event System

Phase 2 Event System remains unchanged in principle:

```text
RuntimeEvent
EventPublisher
EventBus
```

Persistent rule:

```text
Fact / notification
-> EventBus

Command / query / request
-> explicit capability boundary
```

Memory request/response operations therefore do not use EventBus as RPC.

### 3.11 C# WPF Desktop

Desktop layering now includes Memory management:

```text
App.xaml.cs
  -> MainWindow
  -> MainWindowViewModel
  -> AgentClientService
  -> IAgentConnection
  -> WebSocketAgentConnection

Memory UI
  -> MemoryManagementViewModel
  -> IMemoryClientService
  -> correlated AgentClientService request
  -> shared WebSocket transport
```

The Memory ViewModel distinguishes loading, empty, busy, success, failure, selection, history visibility, and connection state.

Desktop Memory operations update local UI state only after a successful server response.

---

## 4. Current Protocol

Transport:

```text
ws://127.0.0.1:8765
```

Implemented request/response families:

```text
chat
response
error

memory.list
memory.list.result

memory.inspect
memory.inspect.result

memory.edit
memory.edit.result

memory.delete
memory.delete.result

memory.history
memory.history.result
```

Memory responses correlate through `payload.request_id`.

Provider and Memory failures are mapped to stable Desktop-safe errors rather than exposing raw SDK, SQLAlchemy, SQLite, filesystem, or traceback details.

Internal Python Runtime Events are still not automatically Desktop protocol messages.

Deferred protocol families include future Permission, Tool, proactive Event Bridge, Avatar, and other later-phase capabilities.

---

## 5. Configuration and Dependency Baseline

Current important runtime configuration includes:

```text
DCA_ENVIRONMENT
DCA_RUNTIME_MODE
DCA_WEBSOCKET_HOST
DCA_WEBSOCKET_PORT
DCA_EVENT_BUS_QUEUE_CAPACITY

DCA_CHARACTER_DEFINITIONS_DIR
DCA_ACTIVE_CHARACTER_ID

DCA_WORKING_CONTEXT_RETENTION_DAYS
DCA_MEMORY_DATABASE_PATH
DCA_AUTOMATIC_LEARNING_ENABLED

DCA_MODEL_PROVIDER
DCA_DEEPSEEK_API_KEY
DCA_DEEPSEEK_MODEL
DCA_DEEPSEEK_TIMEOUT_SECONDS
DCA_DEEPSEEK_THINKING_ENABLED

DCA_LOG_LEVEL
```

Memory defaults:

```text
working_context retention = 7 days
allowed retention range = 1..30 days
automatic learning = enabled
database path = platform-specific user application-data directory
```

Canonical Python dependency source:

```text
pyproject.toml
```

Phase 4 persistence/runtime dependencies include:

```text
sqlalchemy
aiosqlite
alembic
platformdirs
```

Real `.env` files remain ignored and must never be committed.

---

## 6. Validation Baseline

### Phase 1

```text
66 pytest tests passed
Ruff passed
mypy passed on 28 source files
```

### Phase 2

```text
104 passed
Ruff passed
mypy passed on 38 source files
```

### Phase 3

```text
145 passed
Ruff passed
mypy passed on 51 source files
```

### Phase 4

Task 11 final runtime acceptance:

```text
python -m pytest -q
-> 355 passed in 10.03s

python -m ruff check .
-> All checks passed

python -m mypy src
-> Success: no issues found in 111 source files

dotnet build DesktopCompanion.Desktop.slnx
-> succeeded

git diff --check
-> clean
```

Real Phase 4 acceptance verified:

```text
automatic explicit learning
non-explicit input not persisted
SQLite durability
complete Python Core restart persistence
retrieval into Provider context
correction / revision semantics
delete semantics
Character scope isolation
automatic-learning disabled mode
Memory failure isolation
WebSocket governance
WPF governance
Provider-safe error behavior
runtime log safety
```

Task 12 storage-location correction was then verified with:

```text
355 passed in 10.06s
Ruff clean
mypy clean on 111 source files
```

Real startup without `DCA_MEMORY_DATABASE_PATH` resolved the database under the operating-system user application-data directory, created the database, ran Alembic through `0003_identity_unique`, and started the runtime successfully.

---

## 7. Development Baseline

Python:

```text
Python 3.11
pytest
Ruff
mypy
pydantic-settings
websockets
openai
SQLAlchemy
aiosqlite
Alembic
platformdirs
```

Desktop:

```text
C# WPF
.NET 8 Windows
```

Normal task workflow:

```text
Context Recovery
-> Goal / Boundary
-> Design
-> ADR when justified
-> Implementation
-> Targeted verification
-> Ruff / mypy
-> Working diff review
-> Stage explicit files
-> Staged diff review
-> Commit
-> Push
```

Phase-final workflow additionally includes:

```text
full Python regression
Desktop build when relevant
real runtime acceptance
log-safety inspection
final documentation
checkpoint
```

Repository code and confirmed Git commits outrank stale historical documentation.

---

## 8. Architectural Principles That Must Not Be Lost

### 8.1 Companion, not only a turn-based chatbot

The long-term runtime must support proactive behavior without requiring every output to begin with a user chat request.

The independent Desktop receive loop and Event System preserve that direction.

### 8.2 Long-term proactive flow

Target direction remains:

```text
External World
-> Perception
-> Events
-> Situation Engine
-> Attention Engine
-> Behavior Engine
-> Voice / Avatar / Tools
```

Phase 4 Memory provides factual context to future runtime decisions; it does not become the future Decision/Behavior orchestrator.

### 8.3 Intent != Permission

Character intent, Memory content, Runtime Events, and future Behavior proposals do not grant Tool or Action authority.

Sensitive actions must pass through a dedicated Permission boundary.

### 8.4 Real and fictional state remain separate

```text
Character fiction
!= factual Memory

Relationship Memory
!= mood / affection / trust Internal State
```

Fictional Ephemeral State is not persisted as factual Memory.

### 8.5 Memory is factual context, not global orchestration

Memory owns factual persistence, retrieval, learning, retention/conflict, and governance.

Memory does not own:

```text
Character personality
Internal State
Behavior decisions
Permission
Provider routing
Tools
Avatar
TTS
```

### 8.6 Event != Command

EventBus remains for facts/notifications.

Synchronous requests, commands, governance, and future capability operations use explicit boundaries.

### 8.7 Local-first, cloud-enhanced

Current default LLM path remains cloud DeepSeek.

The architecture preserves future local capability/fallback work without making a local model a mandatory resident dependency.

### 8.8 Stable interfaces over hidden coupling

Continue using:

```text
Protocols / interfaces
adapters
repositories
explicit request routing
dependency injection
composition roots
explicit lifecycle ownership
```

UI must not own Agent reasoning, Memory business rules, Provider internals, or Permission logic.

---

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
0008 DeepSeek via async OpenAI-compatible Chat Completions
0009 Provider error isolation and Desktop error mapping
```

Phase 2 ADRs:

```text
0010 Events are facts; commands remain explicit boundaries
0011 async bounded in-process EventBus
0012 fail-fast EventBus overload admission
```

Phase 3 ADRs:

```text
0013 Character definitions are structured domain data
0014 Character consumes User Context; Memory owns User Profile
0015 runtime temporal truth comes from Clock context
```

Phase 4 ADRs:

```text
0016 factual Memory domains, scopes, lifecycle, and revisions
0017 SQLite default durable Memory source of truth
0018 explicit failure-isolated Memory boundaries
0019 adaptive future runtime decision/capability boundaries
0020 logical Memory identity key
0021 explicit runtime routing for request/response capabilities
```

`docs/adr/README.md` is the ADR index.

---

## 10. Phase 4 Git Anchors

Important confirmed Phase 4 anchors include:

```text
6484849 feat(memory): integrate memory retrieval into agent runtime

b64d4d76 feat(memory): establish automatic learning contracts
ebdc2ce0 feat(memory): add learning eligibility policy
ca351db feat(memory): add logical memory identity keys
4fadc5a feat(memory): persist logical memory identity keys
2d91b09 feat(memory): add logical memory identity lookup
f2d15ba feat(memory): add existing memory resolver
066a9dd feat(memory): add learning persistence primitives
843be83 feat(memory): add automatic memory learning service
39da336 feat(memory): close automatic learning lifecycle states
ff49fae feat(memory): add llm memory candidate extractor
1cf2962 feat(memory): stabilize candidate identity extraction

2831829 feat(memory): add memory health model
b8cea85 feat(memory): isolate memory retrieval failures
494c536 feat(memory): isolate automatic learning failures
3c6672e feat(memory): track governance health failures
15b58b1 feat(memory): wire memory health runtime

ab0e083 feat(protocol): add runtime message routing boundary
b4844ab feat(memory): add memory governance protocol handler
66a51e3 feat(memory): wire websocket governance runtime
c0c5ecd feat(desktop): add memory protocol contracts
c8cc364 fix(memory): reject incompatible memory list filters
0bd1812 test(memory): add websocket governance acceptance

4ee3c5e feat(desktop): add correlated agent requests
3ca8091 feat(desktop): add memory application service
ccc6397 feat(desktop): add memory management view model
804ddc2 feat(desktop): add memory management ui
94cce5d fix(memory): bootstrap runtime database schema
3b9aa2b docs(memory): close task 10 acceptance

5d47e1b docs(memory): add task 11 runtime acceptance plan
eb57eb4 test(memory): add integrated runtime lifecycle acceptance
1ddfb9e docs(memory): complete phase 4 runtime acceptance

3d7435c fix(memory): use platform app data for default database
```

The repository Git history remains authoritative for the complete Phase 4 commit sequence.

---

## 11. Known Technical Debt / Deferred Work

Current known debt and intentional deferrals include:

1. Desktop WebSocket endpoint remains hard-coded in `App.xaml.cs`.
2. C# automated tests still do not exist.
3. WPF reconnect/retry/connection-state recovery remains limited.
4. Abrupt WPF shutdown may produce a missing WebSocket close-handshake message.
5. WPF still renders Markdown / LaTeX syntax as plain text.
6. `src/agent_core/requirements.txt` remains legacy duplicate dependency metadata.
7. Provider streaming and automatic retries remain intentionally unsupported.
8. Local-model / cloud-fallback routing is not implemented.
9. Runtime Events remain internal; no Desktop Event Bridge exists.
10. Event persistence/replay, wildcard routing, subscriber priority, dynamic unsubscribe, multiple workers, and restart supervision remain deferred.
11. Dynamic Character switching UI and Character hot reload remain deferred.
12. Memory backup/restore UI, encryption at rest, cloud synchronization, and multi-user accounts are not implemented.
13. Vector retrieval, embeddings, RAG frameworks, fuzzy semantic identity, and numeric confidence scoring are intentionally absent from Phase 4.
14. Standalone/package distribution must ensure Alembic migration resources are shipped with the Python runtime.
15. Phase 4 does not physically guarantee secure erasure from OS/filesystem backups after application-level deletion.
16. A canonical repository-wide text EOL policy is not yet enforced through dedicated `.gitattributes`.

These items should be addressed only when their owning phase or a concrete requirement justifies them.

---

## 12. Phase 5 Entry Point

Next roadmap phase:

> Phase 5 - Situation Engine

Goal:

Convert low-level runtime facts/events into higher-level semantic situations without making Situation responsible for Attention, Behavior execution, Permission, or Memory persistence.

Expected conceptual position:

```text
Perception / Runtime Facts / Events
        ↓
Situation Engine
        ↓
semantic Situation
        ↓
future Attention Engine
        ↓
future Behavior Engine
```

Phase 5 must preserve the boundaries established through Phase 4:

```text
Character != Memory
Character != Internal State
Memory != Situation
Memory Context != Permission
Event != Command
Intent != Permission
Real State != Fictional State
```

Before Phase 5 implementation:

```text
recover repository latest commit
read Phase 4 checkpoint / final acceptance
inspect current Event and Memory boundaries
define Situation inputs/outputs before implementation
avoid turning Situation into Behavior or Permission logic
```

No Situation Engine implementation is part of Phase 4.

---

## 13. Context Recovery Procedure

When continuing the project in a new conversation/session:

1. inspect the latest confirmed Git commit and working-tree state;
2. read `PROJECT_STATE.md`;
3. read `docs/PHASE_4_TASK11_RUNTIME_ACCEPTANCE_PLAN.md` until the final Phase 4 checkpoint is created;
4. read `ARCHITECTURE.md`;
5. read `ROADMAP.md`;
6. read `docs/adr/README.md` and relevant ADRs;
7. read `docs/DEVELOPMENT_UNDERSTANDING.md`;
8. read the current phase design/task documents;
9. inspect affected source files directly from the repository;
10. treat current repository code and accepted ADRs as authoritative when historical design documents describe an earlier implementation state.

Historical checkpoints and task plans remain useful development records but may intentionally describe earlier states.

Chat history is supplementary context, not the authoritative project state.
