# Desktop Companion Agent — Phase 4 Tasks 8–12 Architecture Plan

Status: Proposed Architecture Baseline
Phase: 4 — Memory System
Scope: Tasks 8–12
Repository baseline reviewed: `8ede434`
Last functional baseline before Task 7: `6484849 feat(memory): integrate memory retrieval into agent runtime`

> This document defines architecture responsibilities, boundaries, data flow, capability increments, dependencies, and acceptance direction for Phase 4 Tasks 8–12.
>
> It intentionally does **not** freeze concrete Python class names, file names, database columns, WPF controls, or implementation details. Each Task must still inspect the then-current repository before its Implementation Plan is written.

---

# 1. Phase 4 Remaining Architecture Context

Phase 4 establishes Memory as an independent, factual, governable context subsystem.

The accepted architecture already separates:

```text
Memory Domain
记忆领域模型

Memory Persistence
持久化

Memory Governance
用户治理

Memory Retention / Conflict
保留与冲突语义

Memory Retrieval
记忆检索

Agent + Prompt Integration
Agent 与上下文集成

Automatic Learning
自动学习（Task 7）
```

Tasks 8–12 complete the operational and user-facing boundaries around this Memory subsystem.

Target Phase 4 end-state:

```text
Conversation / Runtime Input
运行时输入
        ↓
Automatic Learning
自动学习
        ↓
Memory Persistence
持久化
        ↓
Memory Retrieval
检索
        ↓
Agent / Prompt
运行时使用

        +-------------------------------+
        |                               |
        v                               v

Failure Isolation                 Governance
故障隔离                          用户治理
        ↓                               ↓
Memory Health                    WebSocket Protocol
健康状态                          桌面协议
                                        ↓
                                  WPF Memory UI
                                  记忆管理界面

        ↓
Runtime Acceptance
完整运行时验收
        ↓
Phase 4 Documentation
阶段文档固化
```

The final Phase 4 system must preserve:

```text
Character != Memory
Real State != Fictional State
Memory Context != Permission
Event != Command
Prompt Composition != Memory Persistence
Runtime Availability != Memory Availability
```

---

# 2. Task 8 — Memory Failure Isolation & Health Behavior

## 2.1 Goal

Task 8 makes Memory an optional runtime capability from the perspective of ordinary chat availability.

A recoverable Memory failure must not make the entire Agent unavailable.

The system must distinguish:

```text
Chat available
Memory healthy

Chat available
Memory degraded / unavailable

Governance operation failed

Fatal runtime failure
```

These are different states and must not be collapsed into one generic error.

---

## 2.2 Architecture Position

Task 8 sits between Memory use cases and the rest of the runtime.

It protects:

```text
Agent
PromptContextComposer
Provider
Desktop conversation path
```

from recoverable Memory subsystem failures.

Conceptual position:

```text
Agent Runtime
智能体运行时
        |
        +---- Memory Retrieval Boundary
        |       ↓
        |   Failure Isolation
        |       ↓
        |   PreparedMemoryContext
        |
        +---- Automatic Learning Boundary
        |       ↓
        |   Failure Isolation
        |
        +---- Governance Boundary
                ↓
            Fail-closed result
```

---

## 2.3 Failure Classes

Task 8 must separate at least three Memory failure semantics.

### Retrieval failure

Expected behavior:

```text
Memory read failure
        ↓
safe diagnostic / health update
        ↓
empty PreparedMemoryContext
        ↓
ordinary chat continues
```

Retrieval is **fail-open for chat**.

The runtime must never pretend that retrieved Memory exists when retrieval actually failed.

---

### Automatic-learning failure

Expected behavior:

```text
valid chat response produced
        ↓
automatic learning attempt
        ↓
write / validation / persistence failure
        ↓
failure remains observable
        ↓
chat response remains valid
```

Automatic learning is also **fail-open for ordinary chat**.

A failed learning write must not retroactively transform a successful chat turn into a failed chat turn.

---

### Governance failure

Expected behavior:

```text
user explicitly requests edit/delete
        ↓
persistence operation fails
        ↓
operation reported as failed
```

Governance is **fail-closed**.

The system must never tell the user that a Memory was edited or deleted when the durable operation did not succeed.

---

## 2.4 Memory Health

Task 8 should establish a minimal runtime-visible Memory health concept.

The health model should be capable of expressing at least:

```text
AVAILABLE
可用

DEGRADED / UNAVAILABLE
降级 / 不可用
```

Exact state names may be decided during Task 8 implementation.

Health represents Memory capability status, not overall Agent status.

Examples:

```text
Provider healthy
Memory unavailable
→ ordinary stateless chat may continue

Provider unavailable
Memory healthy
→ Memory may still be inspectable, but chat generation fails

Memory governance write failed
→ requested governance action fails truthfully
```

Task 8 must not turn Memory health into a global runtime orchestrator.

---

## 2.5 Observability

Memory failures must be diagnosable without leaking sensitive content.

Logs may include:

- failure boundary;
- operation category;
- exception type;
- Memory capability state;
- safe identifiers where appropriate;
- duration / operation metadata when useful.

Logs must not include by default:

- complete Memory content;
- full prompt text;
- full user conversation content;
- API secrets;
- raw SQL containing sensitive factual content when avoidable.

---

## 2.6 Responsibilities

Task 8 owns:

- recoverable Retrieval fallback;
- automatic-learning failure containment;
- truthful Governance failure behavior;
- minimal Memory health state / reporting boundary;
- tests proving chat continues when Memory is unavailable.

Task 8 does not own:

- reconnect/retry orchestration for every possible database failure;
- backup / restore;
- corruption repair UI;
- WPF Memory-management screen;
- WebSocket governance protocol;
- Provider failure semantics;
- global runtime supervision;
- advanced health dashboard.

---

## 2.7 Capability Increment

Before Task 8:

```text
Memory failure
→ may propagate into Agent/runtime paths
```

After Task 8:

```text
Recoverable Memory failure
→ Memory capability degrades
→ ordinary chat can continue
→ user governance never falsely reports success
```

---

## 2.8 Acceptance Direction

Task 8 acceptance should eventually cover:

```text
Retrieval DB failure
→ chat still returns Provider response
→ no Memory context injected

Automatic-learning write failure
→ response still succeeds
→ learning failure observable

Governance edit failure
→ edit reported failed

Governance delete failure
→ delete reported failed

Memory unavailable state
→ distinguishable from healthy state
```

---

# 3. Task 9 — WebSocket Memory Management Protocol

## 3.1 Goal

Task 9 exposes the existing Memory Governance capabilities through the Desktop/WebSocket boundary.

The Desktop client must be able to request Memory management without depending on Python persistence internals.

Target capabilities:

```text
list
inspect
edit
delete
history
```

This converts Memory Governance from an internal Python use case into a stable cross-language application capability.

---

## 3.2 Architecture Position

Task 9 belongs to the protocol/application boundary.

Conceptual path:

```text
WPF / Desktop
桌面客户端
        ↓
WebSocket Protocol
跨语言协议
        ↓
Memory Governance Application Boundary
Memory 治理边界
        ↓
MemoryGovernanceService
        ↓
MemoryRepository
        ↓
SQLite
```

The protocol must expose governance semantics, not database semantics.

The Desktop must never need to know:

- SQLAlchemy models;
- table names;
- transaction structure;
- repository implementation details;
- revision-row schema.

---

## 3.3 Protocol Responsibilities

Task 9 should define stable request/response semantics for:

### List

Request:

```text
list Memory
optionally filter by domain / scope
```

Response:

```text
safe summary entries
```

The list response should contain enough data to build the later WPF list without exposing unnecessary history or internals.

---

### Inspect

Request:

```text
memory_id
```

Response:

```text
logical Memory identity
current/latest visible revision
domain
scope
source
lifecycle
timestamps
```

Exact payload shape belongs to Task 9 implementation design.

---

### Edit

Request:

```text
memory_id
new user-provided content
```

Behavior:

```text
WebSocket
→ Governance
→ new USER_EDIT revision
→ persistence commit
→ success response
```

Failure must be truthful and stable.

---

### Delete

Request:

```text
memory_id
```

Behavior:

```text
WebSocket
→ Governance
→ delete/tombstone semantics
→ persistence commit
→ success response
```

Deleted factual content must not reappear through normal governance or retrieval surfaces.

---

### History

Request:

```text
memory_id
```

Response:

```text
permitted revision history
```

History must respect the accepted delete semantics.

Deleted factual content must not be re-exposed merely because a history endpoint exists.

---

## 3.4 Protocol Error Boundary

Task 9 must map internal Memory/governance failures to stable Desktop-safe errors.

Conceptual categories:

```text
MEMORY_NOT_FOUND
MEMORY_INVALID_REQUEST
MEMORY_UNAVAILABLE
MEMORY_OPERATION_FAILED
```

Exact names are implementation details.

The protocol must not expose:

- raw SQLite errors;
- SQLAlchemy exceptions;
- stack traces;
- filesystem paths;
- sensitive Memory content through exception strings.

---

## 3.5 EventBus Boundary

Memory-management requests remain request/response protocol operations.

They are not converted into EventBus request/response messages.

This preserves the existing architecture rule:

```text
Event = fact / notification
Command / query = explicit application boundary
```

If a future asynchronous consumer needs to know that a Memory changed, that can justify a separate Memory Event later.

Task 9 does not invent one preemptively.

---

## 3.6 Responsibilities

Task 9 owns:

- cross-language Memory-management message types;
- request/response payload contracts;
- governance operation mapping;
- safe Memory protocol errors;
- protocol serialization/deserialization tests;
- integration tests across WebSocket and Governance.

Task 9 does not own:

- WPF layout;
- Memory database operations directly;
- automatic learning;
- Retrieval ranking;
- Permission system;
- EventBus-based governance.

---

## 3.7 Capability Increment

Before Task 9:

```text
Memory Governance exists only inside Python runtime
```

After Task 9:

```text
Desktop client
→ can list / inspect / edit / delete / inspect history
→ through stable WebSocket protocol
```

---

## 3.8 Acceptance Direction

Task 9 acceptance should cover:

```text
Desktop-style request
→ list Memory

inspect existing Memory
→ correct safe payload

edit Memory
→ durable revision update

delete Memory
→ retrieval/governance no longer exposes deleted fact

history
→ correct allowed revision history

invalid memory_id
→ stable protocol error

Memory unavailable
→ stable safe error
```

---

# 4. Task 10 — Simple WPF Memory Management UI

## 4.1 Goal

Task 10 gives the user direct visibility and control over factual Memory.

The WPF UI should provide a minimal usable management surface for:

```text
Memory List
记忆列表

Memory Detail
记忆详情

Edit
修改

Delete
删除

History
历史（如果 Task 9 exposes it for the initial UI）
```

The purpose is governance and transparency, not visual polish.

---

## 4.2 Architecture Position

Task 10 remains inside the existing Desktop layering.

Target path:

```text
Memory View
WPF 界面
        ↓
ViewModel
展示状态与交互
        ↓
Application Service
应用服务
        ↓
IAgentConnection / existing transport boundary
连接抽象
        ↓
WebSocket
        ↓
Task 9 Memory Protocol
```

The WPF UI must not bypass existing transport abstractions.

---

## 4.3 UI Responsibilities

The first UI should allow the user to:

- load a Memory list;
- distinguish basic domain/scope information;
- select one Memory;
- inspect details;
- edit content;
- delete Memory;
- receive truthful success/failure feedback;
- understand when Memory is unavailable.

Optional history presentation depends on Task 9 final protocol and UI complexity, but the architecture should preserve the path.

---

## 4.4 State Handling

The UI must distinguish:

```text
loading
loaded
empty
operation in progress
operation succeeded
operation failed
Memory unavailable
```

The UI should not treat an empty Memory list as equivalent to Memory subsystem failure.

That distinction becomes possible because of Task 8 health/failure semantics and Task 9 protocol errors.

---

## 4.5 Governance Semantics

The WPF UI is a client of Governance.

It must not independently implement:

- conflict resolution;
- deletion semantics;
- revision creation;
- retention decisions;
- scope invariants.

For example:

```text
Edit button
→ sends governance edit request

Python Governance
→ decides and persists revision behavior
```

The Desktop displays the result; it does not own Memory business rules.

---

## 4.6 Responsibilities

Task 10 owns:

- minimal Memory-management views;
- ViewModel state;
- Desktop application-service calls;
- user-visible success/failure feedback;
- integration with Task 9 protocol;
- basic UI refresh after edit/delete.

Task 10 does not own:

- persistence;
- automatic learning;
- conflict rules;
- advanced search;
- tagging;
- bulk edit;
- backup/restore;
- visual redesign of the entire Desktop app;
- rich Memory analytics.

---

## 4.7 Capability Increment

Before Task 10:

```text
Memory can be governed through protocol,
but normal users have no UI
```

After Task 10:

```text
User
→ can see what the Agent remembers
→ can correct it
→ can delete it
→ can observe Memory failure truthfully
```

This is a major trust/transparency milestone for Phase 4.

---

## 4.8 Acceptance Direction

Task 10 acceptance should cover:

```text
Open Memory UI
→ list loads

Select Memory
→ detail displayed

Edit
→ protocol request
→ persisted result
→ UI refresh

Delete
→ confirmation flow if adopted
→ persisted deletion
→ item disappears from normal list/retrieval

Memory unavailable
→ UI shows unavailable/error state
→ app remains usable
```

Exact visual layout belongs to Task 10 implementation design.

---

# 5. Task 11 — Phase 4 Runtime Acceptance

## 5.1 Goal

Task 11 proves that Phase 4 works as one coherent system, not only as isolated unit-tested modules.

Task 11 is primarily validation and integration acceptance.

It should validate the complete Memory lifecycle:

```text
Learn
学习
    ↓
Store
存储
    ↓
Restart
重启
    ↓
Retrieve
检索
    ↓
Use
使用
    ↓
Govern
治理
    ↓
Fail Safely
故障降级
```

---

## 5.2 Acceptance Matrix

Task 11 should verify at least the following categories.

### A. Automatic learning

```text
explicit eligible user fact
→ candidate
→ accepted
→ durable Memory
```

Also verify:

```text
unsupported inference
→ not persisted
```

---

### B. Persistence across restart

```text
Memory learned / created
→ application stops
→ application restarts
→ Memory still exists
```

This proves SQLite is functioning as durable factual source of truth.

---

### C. Retrieval and prompt use

```text
stored Memory
→ later user request
→ Retrieval
→ PreparedMemoryContext
→ PromptContextComposer
→ Provider response can use remembered fact
```

Acceptance should distinguish:

```text
Memory exists in DB
```

from:

```text
Memory actually reached runtime context
```

Both matter.

---

### D. Revision and correction

```text
existing fact
→ user edits / explicit correction
→ old ACTIVE revision superseded
→ new revision ACTIVE
→ retrieval uses new fact
```

---

### E. Delete semantics

```text
user deletes Memory
→ operation commits
→ deleted factual content no longer retrieved
→ normal governance surface no longer exposes deleted factual content
```

---

### F. Domain/scope isolation

At minimum:

```text
USER_PROFILE
→ shared globally

RELATIONSHIP
→ only active Character
```

No Character-specific relationship fact may leak into another Character context.

---

### G. Automatic-learning configuration

```text
automatic_learning_enabled = false
→ chat still works
→ existing Retrieval still works
→ Governance still works
→ no new automatic Memory created
```

---

### H. Failure isolation

Verify:

```text
Memory retrieval failure
→ chat still works

automatic-learning write failure
→ chat response still valid

governance write failure
→ operation reports failure

Memory unavailable
→ distinguishable from empty Memory
```

---

### I. WebSocket governance

Verify real Desktop protocol behavior for:

```text
list
inspect
edit
delete
history
safe errors
```

---

### J. WPF governance UI

Verify real user flow:

```text
open Memory UI
→ list
→ inspect
→ edit
→ delete
→ UI reflects committed state
```

---

### K. Regression

Phase 4 must preserve earlier accepted behavior:

```text
WPF → WebSocket → Agent → Provider → WPF

Character behavior
Temporal factual context
Provider-safe error mapping
EventBus lifecycle
Sensitive-log rules
```

---

## 5.3 Quality Gates

Task 11 should include full project-owner validation.

Expected categories:

```text
Full pytest
Ruff
mypy
git diff --check
C# build
manual runtime acceptance
log-safety inspection
Git working-tree confirmation
```

Exact final test counts are not predetermined.

The acceptance record must report actual observed results.

---

## 5.4 Responsibilities

Task 11 owns:

- full integration acceptance;
- regression acceptance;
- real runtime verification;
- final quality gate results;
- identifying unresolved defects before Phase 4 closure.

Task 11 does not own:

- hiding failed tests;
- redesigning unfinished architecture inside acceptance;
- declaring Phase 4 complete with known unaccepted critical paths.

If Task 11 finds a defect, development returns to the owning Task/boundary, fixes it, then acceptance is rerun.

---

## 5.5 Capability Increment

Task 11 does not primarily add a new feature.

It changes project status from:

```text
individual Phase 4 parts implemented
```

to:

```text
Phase 4 Memory System verified as an integrated runtime capability
```

---

# 6. Task 12 — Phase 4 Final Documentation & Checkpoint

## 6.1 Goal

Task 12 converts the implemented and accepted Phase 4 system into durable project knowledge.

The repository must be sufficient for a future conversation or contributor to reconstruct:

- what Phase 4 built;
- why the architecture looks this way;
- which decisions are frozen;
- what remains deferred;
- what the final validation proved;
- what Phase 5 can safely assume.

---

## 6.2 Required Documentation Outputs

Task 12 should update or create the following categories.

### Project State

Update:

```text
PROJECT_STATE.md
```

It should describe the final actual Memory architecture and current runtime baseline.

---

### Roadmap

Update:

```text
ROADMAP.md
```

Expected Phase state transition:

```text
Phase 4 — Complete
Phase 5 — Next
```

The Memory domain list should reflect the implemented semantic model rather than old candidate wording.

---

### Phase 4 Checkpoint

Create a final checkpoint document covering:

```text
Phase 4 scope
implemented capabilities
accepted architecture
major Tasks
validation results
manual acceptance
known debt
explicit non-goals
latest commit
```

This becomes the primary historical Phase 4 completion record.

---

### ADR Index / ADR Updates

Review:

```text
docs/adr/README.md
```

Any architecture decision actually introduced during Tasks 7–10 that is high-impact and durable should be recorded as an ADR.

Do not create ADRs merely to inflate documentation.

Examples of decisions that may justify ADR treatment if finalized during implementation:

- automatic-learning extraction trust boundary;
- candidate persistence decision;
- Memory health/failure semantics;
- Desktop Memory protocol boundary.

Whether these require new ADRs depends on what is already fully covered by ADR 0016–0018.

---

### Task / Recovery Context

Update the current Phase 4 recovery document so it no longer points to old Tasks.

At Phase completion it should clearly indicate:

```text
Phase 4 complete
latest commit
final validation
next phase
known debt / breakpoint
```

---

### Development Understanding Review

The project collaboration contract requires a Phase 4 learning review.

This should summarize:

```text
What Phase 4 added

Previously known concepts reused

New concepts introduced

A / B / C mastery classification

Real Phase 4 engineering process

Final bilingual data-flow diagram

Knowledge map into Phase 5
```

This is separate from the engineering checkpoint.

---

## 6.3 Final Phase 4 Architecture Diagram

Task 12 should document the actual final system, approximately:

```text
Desktop / WPF
桌面客户端
        ↓
WebSocket Protocol
跨语言协议
        ↓
Agent Core
智能体核心
        ├────────────────────────────────────┐
        │                                    │
        ↓                                    ↓
Memory Retrieval                       Memory Governance
记忆检索                               记忆治理
        ↓                                    ↓
PreparedMemoryContext                  MemoryRepository
准备好的记忆上下文                     持久化边界
        ↓                                    ↓
PromptContextComposer                  SQLite
上下文组装                             事实 Source of Truth
        ↓
LLM Provider

Conversation Turn
当前交互
        ↓
Automatic Memory Learning
自动学习
        ↓
Eligibility / Resolution / Conflict
资格 / 定位 / 冲突
        ↓
MemoryRepository
持久化
```

With Task 8:

```text
Memory failure
→ isolated capability degradation
→ ordinary chat may remain available
```

The final diagram must reflect actual implementation, not pre-implementation expectations.

---

## 6.4 Source Checkpoint

After Phase 4 final acceptance:

```text
commit + push
```

is the primary repository checkpoint.

A final source archive may also be created:

```text
Desktop_Companion_Agent_phase4_final.zip
```

This archive is optional but appropriate at a Phase boundary under the current development contract.

---

## 6.5 Responsibilities

Task 12 owns:

- final architecture documentation;
- final state/roadmap synchronization;
- checkpoint record;
- ADR index consistency;
- Phase 4 learning review;
- transition context for Phase 5.

Task 12 does not own:

- introducing new Memory features;
- silently fixing major architecture defects without returning to their owning Task;
- rewriting history to hide deviations from the original plan.

Documentation must describe what was actually built and accepted.

---

## 6.6 Capability Increment

Task 12 changes the project from:

```text
Phase 4 works in code
```

to:

```text
Phase 4 is reproducible, reviewable, recoverable,
and ready for Phase 5 development
```

---

# 7. Cross-Task Dependency Chain

The recommended dependency order remains:

```text
Task 7
Controlled Automatic Learning
受控自动学习
        ↓
Task 8
Failure Isolation & Health
故障隔离与健康状态
        ↓
Task 9
WebSocket Memory Management Protocol
记忆管理协议
        ↓
Task 10
Simple WPF Memory UI
基础记忆管理界面
        ↓
Task 11
Runtime Acceptance
完整运行时验收
        ↓
Task 12
Final Documentation
最终文档与检查点
```

Reasoning:

```text
Task 7
creates the final major Memory business capability

Task 8
makes that capability safe to run

Task 9
exposes Governance across the language/process boundary

Task 10
gives the user direct control

Task 11
proves the complete system

Task 12
freezes the accepted result into project knowledge
```

---

# 8. Cross-Task Boundary Rules

The following boundaries should remain stable across Tasks 8–12.

## Memory vs Agent

```text
Memory provides factual context.
Memory does not control Agent behavior.
```

## Memory vs Character

```text
Character defines persona.
Memory owns factual user/history context.
```

## Memory vs Internal State

```text
Relationship Memory
= factual shared history

Mood / affection / trust
= future Internal State
```

## Memory vs Provider

```text
Provider generates model output.
Provider does not own durable Memory.
```

## Memory vs Prompt Composer

```text
Composer consumes prepared context.
Composer does not query or mutate Memory.
```

## Memory vs EventBus

```text
Memory request/response use cases
do not become EventBus RPC.

Events are introduced only for real asynchronous facts.
```

## Memory vs Permission

```text
Remembering something
does not grant authority to execute an action.
```

## Desktop vs Persistence

```text
Desktop consumes protocol/application contracts.
Desktop never depends on SQL/SQLAlchemy/database schema.
```

---

# 9. Phase 4 Final Capability Target

When Tasks 7–12 are complete, the project should support the following coherent product behavior:

```text
1. User says an explicit durable fact.
2. Automatic learning evaluates it safely.
3. Accepted fact is stored durably.
4. Application can restart.
5. Later requests retrieve relevant stored Memory.
6. Prompt composition uses that factual context.
7. User can inspect what is remembered.
8. User can correct a remembered fact.
9. User can delete a remembered fact.
10. Relationship Memory stays Character-scoped.
11. Automatic learning can be disabled.
12. Memory failure does not necessarily make chat unavailable.
13. Governance failure is never reported as success.
14. Desktop and Python communicate through stable Memory protocol.
15. WPF gives the user a basic Memory-management surface.
16. Full runtime acceptance proves the complete flow.
17. Final docs preserve the architecture and validation baseline.
```

This is the target boundary for Phase 4.

---

# 10. Deferred Beyond Phase 4

The following remain outside Tasks 8–12 unless the owner explicitly changes Phase scope:

- semantic vector search;
- embeddings;
- external vector database;
- RAG framework;
- Mem0 runtime integration;
- LangGraph runtime integration;
- multi-user accounts;
- cloud Memory sync;
- advanced Memory summarization;
- candidate-review workflow;
- advanced Memory search UI;
- bulk Memory management;
- Mood / affection / trust model;
- Situation Engine;
- Attention Engine;
- Perception Layer;
- Behavior Engine;
- Avatar;
- Voice;
- Tool Permission implementation;
- unrestricted Computer Use;
- local-model routing.

---

# 11. Implementation Planning Rule

This document is an architecture plan, not an implementation freeze.

Before starting each Task:

```text
1. Read current repository HEAD.
2. Read current Phase / Task context.
3. Inspect affected real code.
4. Confirm this architecture plan still matches reality.
5. Resolve any architecture mismatch.
6. Write that Task's Implementation Plan.
7. Only then implement.
```

The current Git repository remains the source of truth over this document if later accepted implementation changes the architecture.
