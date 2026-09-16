# Phase 4 Memory System Design

Status: Approved Design Baseline

Date: 2026-09-15

## 1. Purpose

Phase 4 establishes Memory as an independent, trustworthy, governable context subsystem for Desktop Companion Agent.

Memory provides prepared factual/user context to the runtime while preserving the existing architecture boundaries:

```text
Character != Memory
Character != Internal State
TemporalContext != Memory
Real State != Fictional State
Event != Command
Intent != Permission
Prompt composition != Permission
```

Phase 4 must not turn Character, PromptContextComposer, EventBus, Provider, or future Behavior infrastructure into Memory owners.

## 2. Accepted Product Decisions

The following product semantics are accepted for Phase 4:

- the application is local single-user first;
- the design must not hard-code one concrete user identity and should preserve a future path to multi-user/open-source use;
- Memory supports automatic learning;
- automatic learning is enabled by default and can be disabled by the user;
- accepted automatic learning becomes active immediately;
- the user can inspect, edit, and delete Memory;
- explicit user corrections supersede older conflicting facts;
- superseded factual history is retained;
- inferred preferences do not enter factual User Profile in the first implementation;
- Long-term Memory is lifecycle/retention semantics rather than a parallel semantic domain;
- Today Memory is lifecycle/time-filtering semantics rather than a parallel semantic domain;
- Relationship Memory stores shared history and is scoped per Character;
- affection, mood, trust, and similar evolving values belong to future Internal State;
- Fictional Ephemeral State remains isolated from factual Memory and is not persisted as factual Memory in Phase 4;
- recoverable Memory failures do not make ordinary chat unavailable;
- user-governance operations must report persistence failure accurately;
- a simple WPF Memory-management UI is included late in Phase 4.

Additional accepted scope decisions:

```text
User Profile        -> shared across Characters
Relationship Memory -> Character-scoped
Working Context     -> may survive application restart until retention expiry/clear
```

## 3. Semantic Memory Domains

Phase 4 defines four factual semantic domains:

```text
USER_PROFILE
WORKING_CONTEXT
EPISODIC
RELATIONSHIP
```

### 3.1 User Profile

Stable or durable real-user facts, explicit preferences, long-term goals, and user-controlled profile information.

User Profile is shared across Characters.

Model inference must not directly overwrite factual User Profile in the first Phase 4 implementation.

### 3.2 Working Context

Current or recently active task/project context that is useful across requests and application restarts.

Working Context is globally user-scoped in Phase 4 and may expire according to retention policy.

### 3.3 Episodic Memory

Real events and completed experiences with historical/time semantics.

Episodic Memory is globally user-scoped unless the event specifically represents a Character relationship experience.

### 3.4 Relationship Memory

Real shared history between the user and one Character.

Relationship Memory is Character-scoped.

It does not own mood, affection, trust scores, or other evolving Internal State.

## 4. Orthogonal Scope and Lifecycle

Semantic domain, scope, and lifecycle are separate concerns.

### 4.1 Scope

Initial scope concepts:

```text
GLOBAL_USER
CHARACTER
```

Examples:

| Content | Domain | Scope |
|---|---|---|
| User prefers C# | USER_PROFILE | GLOBAL_USER |
| User is working on Phase 4 | WORKING_CONTEXT | GLOBAL_USER |
| User completed Phase 3 | EPISODIC | GLOBAL_USER |
| User and Aria completed an important shared task | RELATIONSHIP | CHARACTER(Aria) |

Phase 4 remains single-user. Scope must not require account/authentication implementation.

### 4.2 Lifecycle

Initial lifecycle states:

```text
ACTIVE
SUPERSEDED
EXPIRED
DELETED
```

Only eligible ACTIVE Memory participates in normal retrieval.

Long-term and today-scoped behavior are retention/time semantics, not separate semantic domains.

## 5. Revision and Conflict Semantics

A Memory has stable logical identity and revision history.

Conceptually:

```text
MemoryId
  -> Revision 1
  -> Revision 2
  -> ...
```

Editing or explicit correction creates a new revision rather than silently destroying history.

For a successful replacement:

```text
old active revision -> SUPERSEDED
new revision        -> ACTIVE
```

The transition must be atomic.

Initial qualitative source authority, from highest to lowest:

```text
USER_EDIT
USER_EXPLICIT
AUTOMATIC_EXPLICIT_FACT
SYSTEM_OBSERVED
```

Phase 4 does not introduce pseudo-precise numeric confidence or importance scores without a separately justified design.

## 6. Delete Semantics

Delete/forget is distinct from supersede.

After successful deletion:

- deleted factual content must not participate in retrieval;
- normal governance/history surfaces must not expose the deleted factual content;
- implementation may retain a content-free tombstone when required for consistency;
- Phase 4 does not claim physical-media secure erasure or deletion from external OS backups.

A failed user-requested delete/edit operation must be reported as failed and must never be acknowledged as successful when persistence did not commit.

## 7. Runtime Responsibilities

Memory is split by real use case without introducing a speculative universal MemoryManager.

Conceptual responsibilities:

```text
Memory Retrieval
Memory Learning / Recording
Memory Governance
Memory Persistence
```

### 7.1 Retrieval

Retrieval accepts request context and produces prepared Memory context.

It must not mutate Memory.

### 7.2 Learning / Recording

Automatic or explicit learning follows a controlled write path:

```text
input
 -> candidate extraction
 -> eligibility/policy validation
 -> conflict handling
 -> durable commit
```

Candidate extraction must not receive unrestricted direct persistence authority.

### 7.3 Governance

Governance supports user-driven:

```text
list
inspect
edit
delete
history
```

The late Phase 4 WPF Memory UI consumes this boundary.

### 7.4 Persistence

Persistence stores and retrieves Memory data.

It must not depend on Character personality, Prompt rendering, DeepSeek behavior, future Behavior decisions, or WPF UI concerns.

## 8. Automatic Learning Policy

Automatic learning is enabled by default and may be disabled by user configuration.

When disabled:

- retrieval of existing Memory continues;
- manual Memory management continues;
- automatic learning from chat is disabled.

Accepted automatic Memory becomes active immediately.

The first implementation prioritizes explicit, high-certainty user statements, such as:

- explicit stable preferences;
- explicit real-user facts;
- explicit long-term goals;
- explicit current durable projects/tasks;
- explicit important completed interaction events.

The first implementation does not persist as factual User Profile:

- speculative personality inference;
- implicit emotional diagnosis;
- Character fiction;
- uncertain preference inference;
- unsupported conclusions inferred only from frequency of discussion.

The exact extraction mechanism is a later implementation decision and must preserve the candidate/policy/commit boundary.

## 9. Retrieval and Prompt Composition

Target runtime flow:

```text
User Message
    |
    v
Agent
    |---- Clock -> TemporalContext
    |
    |---- Memory Retrieval -> PreparedMemoryContext
    |
    |---- CharacterDefinition
    |
    v
PromptContextComposer
    |
    |---- Character context
    |---- Temporal context
    |---- Prepared Memory context
    |---- User message
    |
    v
LLMRequest
```

PromptContextComposer remains a composition boundary.

It must not:

- query persistence;
- resolve conflicts;
- apply retention;
- perform automatic learning;
- mutate Memory.

PreparedMemoryContext should preserve domain separation conceptually, for example:

```text
user_profile
working_context
relevant_episodes
relationship_context
```

The exact Python representation belongs to implementation design.

Retrieval must be bounded. It must not assume that all accumulated Memory can always be inserted into every prompt.

## 10. Persistence Architecture

Phase 4 selects SQLite as the default local durable Memory source of truth.

Rationale:

- local-first desktop application;
- single-user first;
- zero external database daemon;
- transactions;
- structured query capability;
- revision/history support;
- simple packaging and backup;
- mature Python support;
- appropriate expected Phase 4 scale.

SQLAlchemy is used inside the persistence adapter.

SQLAlchemy types/models must not leak into the Memory domain contract.

Conceptually:

```text
Memory Domain
    |
Persistence Contract
    |
SQLite Memory Persistence Adapter
    |
SQLAlchemy
    |
SQLite
```

SQLite remains the durable factual source of truth.

Future vector indexes, caches, or embeddings are derived retrieval aids and must not become the only factual source.

Phase 4 does not introduce a vector database, embedding provider, RAG framework, Mem0, or LangGraph.

## 11. Schema Versioning

The Memory database requires explicit schema versioning/migrations because the application is expected to evolve and may be distributed to other users.

Phase 4 uses Alembic with SQLAlchemy for migration management.

Runtime code must not accumulate ad-hoc schema mutation logic as a substitute for migrations.

The exact initial schema is defined after Memory domain models are accepted.

## 12. Storage Location

The Memory database is application data.

It must not be stored in:

- the Git repository;
- the source tree;
- a fixed developer-specific path;
- an installation directory that assumes write access.

The runtime must resolve a platform-appropriate application-data path.

Phase 4 does not implement account synchronization or cloud Memory.

## 13. Retention Defaults

Initial default policy:

```text
USER_PROFILE      durable until superseded/deleted
WORKING_CONTEXT   7-day default retention, configurable from 1 to 30 days
EPISODIC          durable in Phase 4
RELATIONSHIP      durable in Phase 4
```

Retention policy is conceptually separate from factual records and persistence technology.

Phase 4 should preserve the ability to make retention configurable without introducing a plugin framework.

For Phase 4, `working_context.retention_days` must be configured within the inclusive range `1..30`.

## 14. Failure Isolation

### 14.1 Runtime retrieval failure

A recoverable Memory-read failure must not make ordinary chat unavailable.

```text
Memory read failure
 -> safe error reporting/logging
 -> empty PreparedMemoryContext
 -> continue chat
```

### 14.2 Automatic-learning write failure

If the chat response itself is otherwise valid, an automatic Memory-write failure must not retroactively fail ordinary chat.

The failure must remain observable to diagnostics.

### 14.3 Governance write failure

User-driven edit/delete failures are fail-closed:

```text
write failed
 -> operation reported failed
 -> never claim success
```

### 14.4 Startup/persistence health

A missing database may be initialized/migrated normally.

An older supported schema is migrated.

Database corruption or an unusable persistence layer may still allow core chat to operate without Memory, but Memory-unavailable status must be visible rather than silently pretending that Memory is healthy.

## 15. Transaction Boundaries

Operations that change multiple persistence records must be atomic.

At minimum:

### Create

```text
logical Memory record
+ first revision
```

commit together.

### Edit/correction

```text
old active revision -> superseded
+ new active revision
```

commit together.

### Delete

All application-required content removal/tombstone updates commit together.

Partial success must roll back.

## 16. Configuration

Memory behavior settings belong to application configuration/policy, not factual Memory content.

Examples:

```text
automatic_learning.enabled
working_context.retention_days
```

For Phase 4, `working_context.retention_days` defaults to `7` and accepts values from `1` through `30`.

Exact configuration names are deferred to implementation tasks.

## 17. EventBus Boundary

Phase 4 does not require Memory requests to pass through EventBus.

Retrieval, governance commands, and persistence operations remain explicit request/service boundaries.

Memory Events may be added only when a real asynchronous fact-notification consumer appears.

No speculative Memory Event family is required by this design.

## 18. Permission Boundary

Memory content and automatic learning do not create Tool authority.

Memory retrieval, Character intent, future Behavior proposals, and future runtime admission decisions cannot grant permission for sensitive actions.

Permission remains a separate boundary.

## 19. Cross-Phase Runtime Compatibility

Phase 4 must remain compatible with the accepted future runtime direction recorded by ADR 0019.

In particular:

- Memory must provide prepared context and must not become a future Behavior/Decision orchestrator;
- automatic learning must not require a permanently resident local LLM;
- Memory must not directly control Avatar, TTS, local LLM, or future capability execution;
- future Unified Decision logic may consume system/user/capability state but does not take ownership of Memory persistence;
- future Cloud/Local capability routing remains outside the Memory domain.

No Unified Decision Layer, Avatar policy, TTS runtime, or Local LLM runtime is implemented in Phase 4 solely because ADR 0019 exists.

## 20. Phase 4 Implementation Order

Approved implementation sequence:

```text
Task 0  Memory design + ADRs
Task 1  Memory domain models
Task 2  Persistence contract + SQLite implementation + migrations
Task 3  Governance core
Task 4  Retention + conflict behavior
Task 5  Retrieval + PreparedMemoryContext
Task 6  Agent + Composer integration
Task 7  Automatic learning pipeline
Task 8  Failure isolation / health behavior
Task 9  WebSocket Memory-management protocol
Task 10 Simple WPF Memory UI
Task 11 Runtime acceptance
Task 12 Phase 4 final documentation
```

Each implementation task follows the established small-step quality loop:

```text
implementation
 -> targeted pytest
 -> Ruff
 -> mypy
 -> git diff --check
 -> working diff review
 -> stage explicit files
 -> staged diff --check
 -> staged diff review
 -> commit
```

Phase-final validation runs complete Python quality gates and required real runtime acceptance.

## 21. Explicit Non-Decisions

This design intentionally does not yet decide:

- exact Python class names beyond concepts required by individual tasks;
- exact SQL table/column layout before domain models are accepted;
- automatic-learning extraction algorithm;
- LLM-based classification;
- embedding model/provider;
- vector search/index technology;
- RAG framework;
- cache implementation;
- multi-user accounts/authentication;
- cloud synchronization;
- relationship/Internal-State scoring;
- Fictional Ephemeral State persistence;
- advanced Memory summarization/compression;
- automatic inference confidence scoring;
- background daemons for Memory extraction;
- speculative EventBus integration;
- concrete local LLM;
- concrete TTS engine;
- Avatar rendering implementation;
- Unified Decision Layer implementation;
- resource thresholds;
- heavy-capability process/IPC topology.

Those cross-phase runtime decisions are either constrained at a high level by ADR 0019 or deferred to their owning future phases.
