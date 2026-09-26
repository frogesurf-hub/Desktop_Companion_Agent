# Development Guide

## 1. Environment Setup

### Python Version

Required:

- Python 3.11

Recommended:

- Python 3.11.x
- Use a project-local virtual environment

### Create Virtual Environment

From the repository root:

```powershell
py -3.11 -m venv .venv
```

### Activate Virtual Environment

PowerShell:

```powershell
.\.venv\Scripts\activate
```

After activation, the prompt should contain:

```text
(.venv)
```

### Verify Python Version

```powershell
python --version
```

Expected:

```text
Python 3.11.x
```

### Install Project and Development Dependencies

Canonical development installation:

```powershell
pip install -e ".[dev]"
```

This installs:

- runtime dependencies declared in `pyproject.toml`;
- development dependencies from the `dev` extra (`pytest`, `ruff`, `mypy`);
- the current project in editable mode.

`pyproject.toml` is the canonical Python dependency source.

`src/agent_core/requirements.txt` remains legacy duplicate metadata and must not receive new dependency declarations. Retire or remove it only in a dedicated maintenance task.

---

## 2. Project Structure

Phase 4 high-level structure:

```text
Desktop_Companion_Agent
├── docs
│   ├── adr
│   ├── COMMUNICATION_PROTOCOL.md
│   ├── DEVELOPMENT.md
│   ├── DEVELOPMENT_UNDERSTANDING.md
│   ├── PHASE_0_CHECKPOINT.md
│   ├── PHASE_1_CHECKPOINT.md
│   ├── PHASE_2_CHECKPOINT.md
│   ├── PHASE_3_CHECKPOINT.md
│   ├── PHASE_4_MEMORY_SYSTEM_DESIGN.md
│   ├── PHASE_4_TASK8_TASK12_ARCHITECTURE_PLAN.md
│   ├── PHASE_4_TASK10_IMPLEMENTATION_PLAN.md
│   └── PHASE_4_TASK11_RUNTIME_ACCEPTANCE_PLAN.md
├── migrations
├── src
│   ├── agent_core
│   │   ├── characters
│   │   ├── communication
│   │   ├── composition
│   │   ├── config
│   │   ├── core
│   │   ├── events
│   │   ├── memory
│   │   ├── observability
│   │   ├── providers
│   │   ├── temporal
│   │   ├── tests
│   │   └── main.py
│   └── Desktop
│       └── DesktopCompanion.Desktop
├── tools
│   └── DesktopCompanion.ConnectionProbe
├── alembic.ini
├── .editorconfig
├── .env.example
├── .gitignore
├── pyproject.toml
├── PROJECT_STATE.md
├── ARCHITECTURE.md
├── DESIGN.md
├── MVP_DESIGN.md
├── PROJECT.md
├── README.md
├── ROADMAP.md
├── TECH_STACK.md
└── THIRD_PARTY.md
```

Responsibilities:

- `src/agent_core/`: Python Agent Core runtime and tests;
- `src/agent_core/memory/`: factual Memory domain, retrieval, learning, governance, health, protocol, and persistence boundaries;
- `migrations/`: Alembic Memory schema evolution;
- `src/Desktop/`: C# WPF desktop application;
- `tools/DesktopCompanion.ConnectionProbe/`: transport/protocol diagnostic client;
- `docs/`: technical documentation, task plans, checkpoint history, and ADRs;
- `pyproject.toml`: canonical Python project metadata, runtime dependencies, development dependencies, pytest, Ruff, and mypy configuration;
- `PROJECT_STATE.md`: primary current-state recovery document;
- root Markdown files: project-level architecture, design, roadmap, technology, and third-party policies.

Repository code and the latest confirmed Git commit are authoritative when older design/checkpoint documents describe an earlier implementation state.

---

## 3. Development Workflow

Normal development sequence:

```text
Context Recovery
        ↓
Requirement / Goal
        ↓
System Position / Boundary
        ↓
Design
        ↓
ADR when justified
        ↓
Task Breakdown
        ↓
Implementation
        ↓
Targeted Tests
        ↓
Ruff / mypy
        ↓
Working Diff Review
        ↓
Stage Explicit Files
        ↓
Staged Diff Review
        ↓
Commit
        ↓
Push
```

Do not skip directly from an idea to implementation when a change affects:

```text
architecture
public interfaces
permissions
persistent data
protocol contracts
runtime ownership
failure semantics
cross-process behavior
```

At a major Task or Phase boundary, also perform documentation synchronization and a recovery/checkpoint review.

---

## 4. Testing

### Run Python Tests

From the repository root:

```powershell
python -m pytest -q
```

pytest reads project configuration from `pyproject.toml`.

Tests are discovered under:

```text
src/agent_core/tests
```

No manual `PYTHONPATH` setup should be required after editable installation.

### Testing Principle

For normal implementation tasks:

- run tests directly related to the current change;
- add or update tests for changed behavior;
- run directly relevant Ruff / mypy checks;
- do not rely only on manual testing;
- do not automatically run the entire suite after every small edit.

For phase-final or runtime-acceptance work:

- run the complete Python regression;
- run full Ruff;
- run full mypy;
- build Desktop when relevant;
- perform real-runtime acceptance when the behavior crosses process/runtime boundaries.

The project owner performs final integration review and phase-final acceptance.

---

## 5. Python Code Quality

### Ruff

Run:

```powershell
python -m ruff check .
```

Purpose:

- detect unused imports;
- detect common Python mistakes;
- enforce import/style consistency;
- catch maintainability issues early.

Use automatic fixing only for clearly mechanical issues:

```powershell
python -m ruff check <paths> --fix
```

Review resulting diffs before staging.

### Formatting

If formatting is required:

```powershell
python -m ruff format <paths>
```

Do not reformat unrelated files as part of a focused change.

### Type Check

Run:

```powershell
python -m mypy src
```

Purpose:

- detect invalid type assumptions;
- improve interface clarity;
- reduce runtime errors;
- protect explicit cross-module contracts.

New public boundaries should prefer explicit typing.

---

## 6. C# / WPF Development

Desktop source:

```text
src/Desktop/DesktopCompanion.Desktop/
```

Current Desktop responsibilities include:

- application/window lifecycle;
- WPF presentation;
- local WebSocket transport;
- Agent client application service;
- independent receive loop for future proactive messages;
- correlated request/response handling;
- Memory management application service;
- Memory list / detail / edit / delete / history presentation.

The WPF layer must not own:

```text
Agent reasoning
Provider implementation
Memory persistence rules
Memory conflict/revision rules
Permission decisions
future Tool execution policy
```

### Build

Current solution:

```powershell
dotnet build .\src\Desktop\DesktopCompanion.Desktop\DesktopCompanion.Desktop.slnx
```

### Run

```powershell
dotnet run --project `
  .\src\Desktop\DesktopCompanion.Desktop\DesktopCompanion.Desktop\DesktopCompanion.Desktop.csproj
```

Before committing Desktop changes:

- confirm the solution builds;
- run relevant C# tests when they exist;
- verify changed UI behavior manually when necessary;
- confirm client-side state is not treated as committed server truth before successful responses.

C# automated tests do not yet exist.

---

## 7. Module Boundaries

The project follows explicit separation of responsibilities.

Current chat path:

```text
Desktop UI
    ↓
AgentClientService
    ↓
IAgentConnection
    ↓
WebSocket
    ↓
RuntimeMessageRouter
    ↓
Agent
    ↓
Memory Retrieval + Prepared Context
    ↓
PromptContextComposer
    ↓
LLMProvider
```

Current Memory governance path:

```text
WPF Memory UI
    ↓
MemoryManagementViewModel
    ↓
IMemoryClientService
    ↓
correlated AgentClientService request
    ↓
WebSocket
    ↓
RuntimeMessageRouter
    ↓
MemoryProtocolHandler
    ↓
Memory Governance
    ↓
MemoryRepository
```

Do not collapse these boundaries into direct calls from UI or transport code to concrete Provider/Repository implementations.

Core modules should communicate through explicit interfaces, protocols, repositories, messages, events, providers, or adapters.

---

## 8. Communication Contract

Desktop and Python Agent Core communicate through the shared protocol boundary.

Primary protocol documentation:

```text
docs/COMMUNICATION_PROTOCOL.md
```

Implemented request families include chat and Phase 4 Memory governance.

Memory request/response capabilities include:

```text
memory.list
memory.inspect
memory.edit
memory.delete
memory.history
```

Responses correlate to requests through:

```text
request Message.id
-> response payload.request_id
```

Do not invent new message shapes only inside implementation code.

If a new message type is required:

1. define the boundary and ownership;
2. update protocol design/documentation;
3. define models/contracts;
4. implement both sides where cross-process;
5. add tests;
6. verify stable error behavior.

Request/response capabilities must not be hidden inside EventBus RPC.

---

## 9. Event / Command / Permission Rules

Persistent rules:

```text
Event != Command
Intent != Permission
Memory Context != Permission
Situation != Permission
```

Runtime Events describe facts or notifications.

Commands, queries, governance operations, and return-value requests require explicit capability boundaries.

Character intent, Memory content, Event existence, and future Behavior proposals do not grant sensitive authority.

Operations involving sensitive capabilities must eventually pass through the Permission system, including future access to:

- files;
- screenshots;
- microphone;
- shell execution;
- UI Automation;
- Computer Use;
- external messaging;
- destructive actions.

---

## 10. Character / Memory / State Separation

Persistent domain rules:

```text
Character
-> who the companion is

Memory
-> factual user/runtime history and durable context

Internal State
-> how the companion is currently feeling / evolving

Situation
-> semantic interpretation of current facts/events
```

Do not merge these for implementation convenience.

In particular:

```text
Character != Memory
Character != Internal State
Memory != Situation
Relationship Memory != Relationship Internal State
Real State != Fictional State
```

Fictional Character background and future fictional ephemeral state must not contaminate factual Memory, Tool reasoning, or Permission logic.

---

## 11. Memory Development Rules

Phase 4 factual Memory domains:

```text
USER_PROFILE
WORKING_CONTEXT
EPISODIC
RELATIONSHIP
```

Scope rules:

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

Memory content is revisioned rather than destructively overwritten.

Memory persistence boundary:

```text
Memory Domain
    ↓
MemoryRepository
    ↓
SQLiteMemoryRepository
    ↓
SQLAlchemy
    ↓
SQLite
```

Alembic owns schema evolution.

Runtime startup upgrades the Memory database to Alembic head before repository use.

The default database location comes from the operating-system user application-data directory through `platformdirs`.

Explicit override:

```text
DCA_MEMORY_DATABASE_PATH
```

Do not move default runtime data back into the Git repository/source tree.

Automatic Memory candidate extraction does not have unrestricted direct persistence authority.

Retrieval remains provider-independent.

Automatic learning may reuse the Provider boundary for candidate extraction, but Memory does not own Provider construction.

---

## 12. Memory Failure Semantics

Memory has independently tracked capabilities:

```text
RETRIEVAL
AUTOMATIC_LEARNING
GOVERNANCE
```

Required behavior:

```text
Retrieval failure
-> fail-open for ordinary chat

Automatic-learning failure
-> fail-open for an already-valid chat response

Governance persistence failure
-> fail-closed for the requested operation
-> do not report durable success
```

A missing/unavailable Memory capability must not silently masquerade as a successful persistent write.

Health tracking does not itself own retry or recovery policy.

---

## 13. Local and Online Separation

Target runtime modes remain:

```text
Offline
Local
Hybrid
Cloud
```

Current implementation uses cloud DeepSeek for the default LLM path.

Current behavior includes provider-safe failure handling, but local-model/cloud fallback routing is not yet implemented.

Do not claim local fallback exists merely because `runtime_mode` supports broader future modes.

The architecture should continue to preserve future local-provider adapters without coupling Agent Core to one vendor.

---

## 14. Configuration and Secrets

Never commit secrets.

Examples:

```text
.env
API keys
access tokens
private credentials
```

Use:

```text
.env.example
```

for documented variable names without real values.

Current important runtime settings include:

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

Important current defaults:

```text
EventBus queue capacity = 256
Working Context retention = 7 days
Automatic Memory Learning = enabled
Memory DB = platform-specific user application-data directory
Provider retries = 0
Provider streaming = disabled
```

Operational defaults remain configurable unless an ADR explicitly makes them semantic guarantees.

---

## 15. Git Workflow

### Check Current State

```powershell
git status --short
```

Run Git commands from the repository root.

### Stage Focused Files

Prefer explicit staging:

```powershell
git add path/to/file1 path/to/file2
```

Avoid `git add .` when a focused file list is known.

### Review Before Commit

Required focused review flow:

```powershell
git diff --check
git status --short
git --no-pager diff

git add <explicit files>

git --no-pager diff --cached --check
git diff --cached --name-only
git --no-pager diff --cached
```

Before committing, confirm:

- only intended files are staged;
- tests/quality gates appropriate to the change passed;
- no secrets/generated runtime data are staged;
- documentation matches the implemented contract;
- commit scope is coherent.

---

## 16. Commit Scope

Commits should be small enough to understand and revert.

Good examples:

```text
feat(memory): add memory health model
feat(protocol): add runtime message routing boundary
fix(memory): bootstrap runtime database schema
fix(memory): use platform app data for default database
docs(memory): complete phase 4 runtime acceptance
```

Avoid mixing unrelated changes such as:

```text
Memory persistence
+ unrelated WPF redesign
+ Provider refactor
+ formatting sweep
```

in one commit.

Commit messages should describe the completed result.

---

## 17. Documentation Rules

Project-level current-state documents:

```text
PROJECT_STATE.md
ARCHITECTURE.md
ROADMAP.md
```

Detailed subsystem/task documentation belongs under:

```text
docs/
```

Architecture decisions belong under:

```text
docs/adr/
```

Important source priority during recovery/review:

```text
current repository code
confirmed Git history
accepted ADRs
current project-state documentation
current phase/task documents
historical checkpoints
chat history
```

When implementation changes a documented contract, update the relevant documentation in the same development stage.

Historical task plans/checkpoints may intentionally describe an earlier state. Do not rewrite historical records merely to make them look current.

---

## 18. Third-Party Code and References

Before copying or adapting external code:

1. identify the source repository;
2. check its license;
3. record the source in `THIRD_PARTY.md` when required;
4. distinguish between architectural inspiration, adapted implementation, copied component, and external runtime integration.

Do not copy source code merely because it is publicly visible.

Current Phase 4 dependency additions such as SQLAlchemy, aiosqlite, Alembic, and platformdirs are normal package dependencies, not copied source code.

---

## 19. AI-Assisted Development

AI tools are development assistants, not project owners.

When using Codex, Claude, GPT, or similar tools:

- provide relevant project state and architectural context;
- state the exact modification scope;
- identify boundary rules;
- require relevant targeted tests;
- inspect generated diffs;
- stage explicit files;
- do not allow unrelated redesign;
- do not treat AI output as authoritative over repository reality.

The project owner performs final integration review and full acceptance.

For this project, development discussion should distinguish:

```text
Implementation defect
Contract mismatch
Test defect
Environment/configuration issue
External Provider issue
```

Do not weaken an acceptance criterion merely to obtain a green result.

---

## 20. Error Handling and Logging

Long-term application behavior must use structured logging rather than raw `print()` diagnostics.

Logging levels:

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Errors should preserve enough metadata for diagnosis without leaking sensitive user data.

Do not log by default:

```text
API keys
Authorization headers
complete user prompts
complete model responses
raw Provider response bodies
reasoning content
full sensitive Memory payloads
```

External Provider failures must remain distinguishable from internal runtime failures.

Memory infrastructure errors must not be exposed to Desktop as raw SQLite/SQLAlchemy/filesystem diagnostics.

---

## 21. Maintainability Principles

The project prioritizes:

- explicit module boundaries;
- replaceable Providers/adapters;
- repository boundaries for persistence;
- testable business logic;
- documented protocol/architecture contracts;
- local-first direction;
- permission-first sensitive actions;
- backward-compatible evolution where practical;
- explicit migrations for persistent data;
- minimal hidden global state;
- explicit runtime lifecycle ownership.

Do not simplify architecture only to reduce short-term implementation difficulty when that would introduce hidden coupling or confused ownership.

---

## 22. Definition of Done

A normal development task is complete when all relevant items are satisfied:

- implementation is finished;
- targeted tests pass;
- relevant Ruff/mypy checks pass;
- working diff is reviewed;
- staged diff is reviewed;
- architectural boundaries remain valid;
- permissions/failure semantics remain correct;
- documentation is updated when necessary;
- no secrets or generated runtime artifacts are committed;
- commit accurately represents the change;
- push/remote state is confirmed when required.

A phase-final acceptance additionally requires:

```text
full Python regression
full Ruff
full mypy
Desktop build when relevant
real-runtime acceptance where needed
sensitive-log review where needed
current-state documentation synchronization
phase checkpoint
clean repository state
```

---

## 23. Current Development Baseline

Phase 4 accepted runtime baseline:

```text
Python 3.11
C# WPF / .NET 8 Windows

WebSocket Desktop <-> Python transport
Provider-neutral async LLMProvider
DeepSeek AsyncOpenAI adapter

bounded in-process EventBus
structured Character System
Clock / TemporalContext
PromptContextComposer

factual Memory domain
SQLite / SQLAlchemy persistence
Alembic migrations
runtime schema bootstrap
PreparedMemoryContext retrieval
Automatic Memory Learning
Memory revision/conflict/deletion semantics
Memory health / failure isolation
RuntimeMessageRouter
WebSocket Memory governance
WPF Memory management
```

Phase progression:

```text
Phase 0
cross-language runtime foundation
COMPLETE

Phase 1
real LLM / Provider path
COMPLETE

Phase 2
Event System
COMPLETE

Phase 3
Character / Temporal / Composition
COMPLETE

Phase 4
Memory System
COMPLETE / final documentation in progress

Phase 5
Situation Engine
NEXT
```

Phase 4 final Task 11 acceptance:

```text
355 pytest tests passed
Ruff passed
mypy passed on 111 source files
Desktop build succeeded
git diff --check clean
```

Task 12 storage-location correction retained:

```text
355 pytest tests passed
Ruff passed
mypy passed on 111 source files
```

Real Phase 4 runtime acceptance proved:

```text
automatic explicit learning
non-explicit input not persisted
durability across complete Python Core restart
retrieval into Provider context
revision/correction semantics
delete semantics
Character-scoped Relationship isolation
automatic-learning-disabled behavior
failure isolation
WebSocket governance
WPF governance
Provider-safe errors
runtime log safety
```

Current Provider constraints:

```text
non-streaming
zero automatic retries
no local-model/cloud fallback router
roles remain system/user/assistant
```

Current Event System constraints:

```text
internal Python runtime only
exact-type routing
no persistence/replay
no wildcard subscription
no subscriber priority
no dynamic unsubscribe
no automatic Event retry
single dispatcher
no restart/supervision policy
no Desktop Event Bridge
```

Current known Runtime/Desktop debt includes:

```text
hard-coded Desktop WebSocket endpoint
no C# automated tests
limited reconnect/retry recovery
abrupt WPF shutdown may miss close handshake
plain-text Markdown/LaTeX rendering
standalone packaging must include Alembic migration resources
```

Current recovery entry points during Task 12:

```text
PROJECT_STATE.md
ARCHITECTURE.md
ROADMAP.md
docs/PHASE_4_TASK11_RUNTIME_ACCEPTANCE_PLAN.md
docs/adr/README.md
docs/DEVELOPMENT_UNDERSTANDING.md
```

Task 12 will create the final Phase 4 checkpoint. After that checkpoint exists, it should become the primary phase-specific recovery document for Phase 5 context restoration.

This document should continue evolving with each major runtime phase.
