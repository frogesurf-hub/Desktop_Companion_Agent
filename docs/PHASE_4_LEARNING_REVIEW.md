# Phase 4 Learning Review - Desktop Companion Agent

Date: 2026-09-27

Status: **Draft Complete — Owner Walkthrough Pending**

This document is the Phase 4 understanding / learning review required by:

```text
docs/DEVELOPMENT_UNDERSTANDING.md
```

It is intentionally separate from:

```text
docs/PHASE_4_CHECKPOINT.md
```

The checkpoint answers:

```text
What was built?
What was accepted?
What remains deferred?
```

This learning review answers:

```text
Why is the system designed this way?
Which concepts should the project owner understand?
Which details only need recognition?
What knowledge carries into Phase 5?
```

---

# 1. Phase 4 Added What?

## 1.1 Before Phase 4

Before Phase 4, Desktop Companion Agent could already:

```text
Desktop
    ↓
WebSocket
    ↓
Agent
    ↓
Character + Temporal Context
    ↓
PromptContextComposer
    ↓
Provider
    ↓
Desktop response
```

The system already knew:

```text
who the Character is
what time/date it is
how to call an LLM Provider
how to keep runtime Event boundaries
```

But it could not durably answer:

```text
What factual information did the user previously tell me?
What recent task context should survive restart?
What shared factual history belongs to one Character?
What did the user correct?
What has the user deleted?
```

The old runtime had conversation behavior, but no durable factual Memory ownership model.

---

## 1.2 After Phase 4

Phase 4 added the ability to:

```text
learn eligible facts
→ persist them
→ restart the Core
→ retrieve them later
→ feed them into prompt composition
→ inspect them
→ correct them
→ delete them
→ isolate Memory failure from ordinary chat
```

The important improvement is not just:

```text
"the program now has a database"
```

It is:

```text
the program now has an explicit factual Memory subsystem
with boundaries for meaning, storage, retrieval,
learning, governance, failure, and protocol access
```

---

# 2. The Central Phase 4 Idea

The most important Phase 4 idea is:

```text
Memory is not "some extra text inserted into the prompt."
```

Instead:

```text
Memory
= factual domain model
+ persistence boundary
+ lifecycle
+ retrieval
+ learning policy
+ conflict handling
+ governance
+ failure semantics
```

This is why Phase 4 became much larger than simply adding SQLite.

---

# 3. Old Knowledge Reused in Phase 4

Phase 4 reused concepts already introduced in earlier phases.

## 3.1 Protocol / Interface

Previously used for:

```text
LLMProvider
EventPublisher
Clock
```

Reused in Phase 4 for:

```text
MemoryRepository
MemoryRetriever
MemoryTurnLearner
MemoryGovernance
MessageProcessor
```

Why:

```text
business logic should depend on a capability contract,
not on one concrete implementation
```

Example:

```text
MemoryLearningService
    ↓
MemoryRepository

not

MemoryLearningService
    ↓
SQLiteMemoryRepository directly
```

This keeps the Memory use case independent from SQLite.

---

## 3.2 Dataclass / Domain Model

Previously used for explicit application data.

Reused for:

```text
Memory
MemoryRevision
MemoryScope
PreparedMemoryContext
MemoryCandidate
Memory health snapshots
```

Why:

```text
important system concepts should have named structure
instead of being loose dictionaries or prompt strings
```

---

## 3.3 async / await

Already used in:

```text
Provider
WebSocket
EventBus
```

Reused throughout:

```text
Repository IO
Retrieval
Learning
Governance
Protocol handling
```

Why:

database and Provider operations are IO boundaries and must not block the runtime unnecessarily.

---

## 3.4 Dependency Injection

Previously:

```text
Agent receives Provider / Character / Clock / Composer
```

Phase 4 extends this:

```text
Agent receives MemoryRetriever
Agent optionally receives MemoryTurnLearner
Memory services receive Repository / Policy / Clock
Runtime Router receives capability processors
```

Why:

```text
objects receive the capabilities they need
instead of constructing hidden dependencies internally
```

This improves testability and prevents ownership confusion.

---

## 3.5 Composition Root

`main.py` remains the place where concrete runtime components are assembled.

Phase 4 added concrete construction of:

```text
Memory database
Repository
Health tracker
Retrieval service
Automatic Learning pipeline
Governance
Memory protocol handler
RuntimeMessageRouter
```

Why:

```text
domain/application code should not decide which concrete infrastructure
implementation the application boots with
```

---

## 3.6 EventBus Boundary

Phase 2 taught:

```text
Event = fact / notification
```

Phase 4 reused that lesson when Memory governance appeared.

Instead of:

```text
memory.edit
→ publish Event
→ somehow wait for a response
```

Phase 4 uses:

```text
memory.edit
→ explicit request routing
→ MemoryProtocolHandler
→ Governance
→ response
```

This preserves:

```text
Event != Command
```

---

## 3.7 pytest / mypy / Git Review

Phase 4 repeatedly used:

```text
targeted pytest
integration pytest
Ruff
mypy
working diff review
staged diff review
commit / push
```

The important lesson is that each tool catches a different class of problem.

```text
pytest
→ behavior

Ruff
→ static/style defects

mypy
→ type-contract defects

git diff
→ what actually changed

staged diff
→ what will actually be committed
```

---

# 4. New Knowledge Introduced in Phase 4

These concepts became real project architecture for the first time in Phase 4.

---

## 4.1 Persistence

Persistence means:

```text
state survives process lifetime
```

For Phase 4:

```text
Python Core stops
    ↓
SQLite remains
    ↓
Python Core restarts
    ↓
Memory still exists
```

This is different from:

```text
Python object exists in RAM
```

Phase 4 Task 11 explicitly proved persistence across a complete Core restart.

---

## 4.2 Repository

Repository is the durable-storage capability boundary.

```text
Memory use cases
    ↓
MemoryRepository
    ↓
SQLiteMemoryRepository
    ↓
SQLAlchemy / SQLite
```

The key lesson:

```text
Repository defines what the application needs from storage.
SQLite defines how one adapter performs it.
```

Repository does not decide business conflict semantics.

Example:

```text
Should this new fact replace the old fact?
```

belongs above Repository.

Repository only guarantees the requested persistence operation and its atomicity.

---

## 4.3 Database Migration

Once persistent user data exists, schema changes become a compatibility problem.

Phase 4 introduced:

```text
Alembic
```

Migration sequence:

```text
0001_memory
→ 0002_identity_key
→ 0003_identity_unique
```

Key lesson:

```text
changing Python classes is not enough
when old durable databases may already exist
```

The database itself needs an explicit evolution path.

---

## 4.4 Memory Domain

Phase 4 established four semantic domains:

```text
USER_PROFILE
WORKING_CONTEXT
EPISODIC
RELATIONSHIP
```

These answer:

```text
What does this factual Memory mean?
```

They do not answer:

```text
How long should it live?
Who can see it?
Is it currently active?
```

Those are separate dimensions.

This separation prevents one flat category list from mixing unrelated concepts.

---

## 4.5 Scope

Scope answers:

```text
Who / what context does this Memory belong to?
```

Phase 4:

```text
GLOBAL_USER
CHARACTER
```

Example:

```text
User prefers Python
→ GLOBAL_USER

User and Aria previously discussed a specific shared event
→ CHARACTER / aria
```

This prevents Character-specific relationship facts from leaking across Characters.

---

## 4.6 Lifecycle

Lifecycle answers:

```text
What is the current status of this revision?
```

Phase 4:

```text
ACTIVE
SUPERSEDED
EXPIRED
DELETED
```

This is different from domain.

Example:

```text
WORKING_CONTEXT
```

is what the Memory means.

```text
EXPIRED
```

is its lifecycle state.

---

## 4.7 Revision History

Correction does not simply overwrite a row.

Instead:

```text
Revision 1
old fact
ACTIVE

    ↓ correction

Revision 1
SUPERSEDED

Revision 2
new fact
ACTIVE
```

Why:

```text
the system must distinguish
"the fact changed"
from
"the old fact never existed"
```

Revision history supports transparent correction semantics.

---

## 4.8 Tombstone Delete

Delete is not the same as supersede.

Phase 4 uses a `DELETED` tombstone and removes prior factual revision content from normal retained history.

Conceptually:

```text
delete
!=
replace
```

The application can know:

```text
this logical Memory was deleted
```

without continuing to retain/expose the deleted factual content as normal history.

---

## 4.9 Retention

Retention answers:

```text
How long should something remain active?
```

Example:

```text
WORKING_CONTEXT
default = 7 days
```

This is why:

```text
Today Memory
Long-term Memory
```

were not accepted as parallel semantic domains.

Time duration is a lifecycle/retention dimension, not necessarily a new meaning category.

---

## 4.10 Retrieval

Retrieval means:

```text
stored Memory
    ↓
select eligible relevant factual context
    ↓
PreparedMemoryContext
```

It is not:

```text
dump all rows into the prompt
```

Important separation:

```text
Repository
→ storage access

Retrieval
→ choose usable context

PromptContextComposer
→ format already-prepared context
```

---

## 4.11 Prepared Context

`PreparedMemoryContext` is a boundary object.

It prevents:

```text
PromptContextComposer
→ directly querying the database
```

Instead:

```text
Memory subsystem
→ prepares factual context
→ Composer consumes it
```

This keeps Composer simple and prevents it from becoming a service locator.

---

## 4.12 Automatic Learning

Automatic learning is not:

```text
LLM says "remember this"
→ database write
```

Phase 4 deliberately inserts boundaries:

```text
candidate extraction
→ eligibility
→ existing Memory resolution
→ conflict policy
→ durable commit
```

The extractor proposes.

Policy decides whether the candidate is eligible.

Resolver identifies what logical fact it refers to.

Conflict policy decides replacement behavior.

Persistence commits the accepted result.

---

## 4.13 Logical Memory Identity

`memory_id` answers:

```text
Which durable object is this?
```

`MemoryIdentityKey` answers:

```text
Which semantic factual slot is this?
```

Example:

```text
user_profile.preference.programming_language
```

The value may change:

```text
C#
→ Rust
→ Python
```

while logical identity remains the same.

This enables deterministic:

```text
new fact
vs
duplicate
vs
update
```

without requiring vector similarity.

---

## 4.14 Conflict Resolution

Conflict Resolution answers:

```text
A candidate refers to an existing logical Memory.
What should happen now?
```

It does not decide identity.

That separation is important:

```text
ExistingMemoryResolver
→ which Memory?

MemoryConflictPolicy
→ what should happen to it?
```

This is a common mature-system pattern:

```text
identify first
decide second
persist third
```

---

## 4.15 Fail-Open vs Fail-Closed

This is one of the most important Phase 4 reliability concepts.

### Retrieval

If Memory retrieval fails:

```text
chat can still continue
```

So:

```text
fail-open
```

### Automatic Learning

If the model already produced a valid response but persistence fails:

```text
the valid response should not be retroactively destroyed
```

So learning also fails open for the chat response.

### Governance

If the user explicitly clicks Edit/Delete and persistence fails:

```text
the application must not say success
```

So governance:

```text
fail-closed
```

The general lesson:

```text
failure behavior depends on the meaning of the operation
```

There is no universal rule that every subsystem failure should stop the application.

---

## 4.16 Capability Health

Memory health is tracked per capability:

```text
RETRIEVAL
AUTOMATIC_LEARNING
GOVERNANCE
```

Why not one boolean:

```text
memory_ok = true / false
```

Because the runtime may be in states such as:

```text
retrieval unavailable
but chat still available

automatic learning degraded
but existing Memory readable

governance failed
but Provider still healthy
```

Capability health reflects partial degradation.

---

## 4.17 Explicit Runtime Routing

Before Memory governance, WebSocket requests could go directly to Agent because almost everything was `chat`.

Phase 4 adds:

```text
RuntimeMessageRouter
```

Now:

```text
chat
→ Agent

memory.*
→ MemoryProtocolHandler
```

Why:

```text
Agent should not become a universal application dispatcher
```

and:

```text
WebSocketServer should not become business logic
```

The router creates an application request-routing boundary.

---

## 4.18 Request Correlation

Desktop Memory management needs to send a request and later match the correct response.

Phase 4 uses:

```text
request Message.id
→ response payload.request_id
```

This allows multiple asynchronous requests to share one receive loop without guessing which response belongs to which operation.

---

# 5. A / B / C Mastery Classification

Not every Phase 4 concept needs the same depth of understanding.

---

## A. Must Understand

You should be able to explain **why these exist**.

### A1. Memory domain / scope / lifecycle are different dimensions

You should understand:

```text
domain
→ what the Memory means

scope
→ who it belongs to

lifecycle
→ its current status
```

### A2. Repository is a persistence boundary

You should understand why:

```text
Memory use cases
→ depend on MemoryRepository

not
→ depend directly on SQLite
```

### A3. Character and factual Memory must remain separate

```text
Character
→ persona

Memory
→ factual context
```

### A4. Relationship Memory is not Internal State

```text
shared factual history
!=
current affection / mood / trust
```

### A5. Prepared context protects Composer boundaries

Composer formats context.

It does not become a database/retrieval/conflict service.

### A6. Revision / governance semantics

You should understand why correction creates a new revision and why delete differs from supersede.

### A7. Fail-open vs fail-closed

You should be able to explain why:

```text
retrieval failure
→ chat may continue

governance write failure
→ must report failure
```

### A8. Intent / Memory does not grant Permission

```text
remembering a file path
!=
permission to open/delete that file
```

### A9. Event != request/command

You should understand why `memory.edit` uses explicit routing rather than EventBus RPC.

---

## B. Should Recognize

You do not need to reproduce these implementations from memory, but should know what role they play.

### B1. SQLAlchemy

```text
database adapter technology
```

### B2. Alembic

```text
database schema migration tool
```

### B3. MemoryIdentityKey

```text
logical factual-slot identity
```

### B4. MemoryHealthTracker

```text
records independent Memory capability health
```

### B5. Resilient wrappers

```text
isolate recoverable Memory failures
```

### B6. RuntimeMessageRouter

```text
routes request families to explicit capabilities
```

### B7. Correlated Desktop requests

```text
request.id
→ response.request_id
```

### B8. WPF service / ViewModel layering

```text
ViewModel
→ application service
→ transport

not
ViewModel
→ raw database/protocol business logic
```

---

## C. No Need to Deep-Dive Yet

You only need to know these exist and where they belong.

### C1. Alembic internal migration machinery

You do not need to memorize Alembic APIs.

### C2. SQLAlchemy mapping internals

You do not need to memorize ORM row mapping code.

### C3. SQLite transaction implementation details

Understand atomicity conceptually; detailed SQL behavior can remain implementation-level.

### C4. WPF binding mechanics

Phase 4 learning target is architecture, not mastering every XAML binding detail.

### C5. Packaging Alembic resources

Know this is a deployment debt; implementation belongs to future packaging work.

### C6. Vector retrieval / embeddings

They were intentionally not introduced.

Do not study them merely because they are common in external Memory/RAG systems.

---

# 6. The Real Phase 4 Engineering Process

Phase 4 did not follow a simple:

```text
write code
→ tests pass
→ done
```

The actual engineering loop was closer to:

```text
Recover Repository Baseline
恢复当前真实源码
        ↓
Clarify Memory Semantics
确认事实记忆含义
        ↓
Architecture Design
架构设计
        ↓
Architecture Review
架构审查
        ↓
ADR
冻结高影响决策
        ↓
Task Planning
任务拆分
        ↓
Define Contracts
定义边界
        ↓
Implementation
实现
        ↓
Targeted Unit / Integration Tests
定向测试
        ↓
Static Checks
Ruff / mypy
        ↓
Working Diff Review
工作区审查
        ↓
Staged Diff Review
暂存区审查
        ↓
Commit / Push
工程检查点
        ↓
Real Runtime Acceptance
真实运行时验收
        ↓
Defect Classification / Return Loop
问题分类并返回所属边界
        ↓
Final Documentation
最终文档
        ↓
Checkpoint / Learning Review
工程检查点 / 理解复盘
```

---

## 6.1 Why Recovery Comes First

The repository is the current source of truth.

Without recovery:

```text
old chat memory
→ may describe stale code
```

So every Task starts by confirming:

```text
HEAD
working tree
current source
current ADR / task context
```

---

## 6.2 Why Architecture Comes Before Implementation

Memory affects:

```text
persistence
user data
runtime failures
cross-process protocol
Character boundaries
future Permission boundaries
```

Those are expensive to undo later.

So Phase 4 established semantic boundaries before coding details.

---

## 6.3 Why ADR Exists

ADR records decisions expected to survive chat/context loss.

Examples:

```text
SQLite is factual source of truth
EventBus is not RPC
Memory has explicit domains/scopes/lifecycle
logical identity keys exist
```

These are architecture decisions, not temporary implementation comments.

---

## 6.4 Why Tests Were Layered

Phase 4 required several evidence levels.

```text
unit tests
→ one policy/class behaves correctly

integration tests
→ multiple real components compose correctly

real runtime acceptance
→ WPF/Core/Provider/SQLite actually work together
```

One layer cannot replace all others.

---

## 6.5 Why Manual Runtime Acceptance Mattered

Task 10 real WPF acceptance found:

```text
Memory DB had zero schema tables
```

Unit tests had not proven the actual production composition root performed schema bootstrap.

That exposed:

```text
implementation defect
```

The fix was:

```text
runtime Alembic bootstrap before Repository use
```

This is a major lesson:

```text
tested components
!=
tested production composition
```

---

## 6.6 Why Final Reality Review Mattered

Task 12 discovered:

```text
ADR 0017
→ database should live in OS application-data location

actual default
→ repo/data/memory.db
```

The Memory runtime itself worked, but architecture and implementation disagreed.

Classification:

```text
implementation / architecture deviation
```

The fix introduced `platformdirs` and real runtime acceptance of the new default path.

This shows why final documentation is not clerical work.

A documentation/reality review can expose implementation defects.

---

## 6.7 Why Incident Classification Mattered

Task 11 encountered:

```text
mobile-hotspot failures
abrupt WPF disconnect
accidental local .csproj corruption
```

These were not all Memory bugs.

Correct classification prevented unnecessary redesign.

The project distinguishes:

```text
implementation defect
contract mismatch
test defect
environment/configuration issue
external Provider issue
```

This avoids treating every red screen as the same type of failure.

---

# 7. Final Phase 4 Data Flow

## 7.1 Chat + Retrieval

```text
User
用户
    ↓
WPF Desktop
桌面客户端
    ↓
WebSocket
跨进程协议
    ↓
RuntimeMessageRouter
运行时路由
    ↓
Agent
智能体
    ├───────────────────────────────┐
    ↓                               ↓
Clock / Character               Memory Retrieval
时间 / 角色                     记忆检索
                                    ↓
                              MemoryRepository
                               持久化边界
                                    ↓
                                  SQLite
                              事实 Source of Truth
                                    ↓
                           PreparedMemoryContext
                           准备后的事实记忆上下文
    └────────────────┬──────────────┘
                     ↓
            PromptContextComposer
              上下文组装器
                     ↓
                 LLMProvider
                模型提供商
                     ↓
                  Response
                     ↓
                  Desktop
```

---

## 7.2 Automatic Learning

```text
User + Assistant completed turn
用户 + 助手完整轮次
        ↓
LLMMemoryCandidateExtractor
候选事实提取
        ↓
MemoryLearningPolicy
资格判断
        ↓
ExistingMemoryResolver
逻辑记忆定位
        ↓
MemoryConflictPolicy
冲突策略
        ↓
MemoryLearningService
记忆学习服务
        ↓
MemoryRepository
持久化边界
        ↓
SQLite
```

The key ownership rule is:

```text
Extractor proposes.
Policy decides eligibility.
Resolver identifies.
Conflict policy decides replacement.
Repository persists.
```

---

## 7.3 User Governance

```text
WPF Memory UI
记忆管理界面
        ↓
MemoryManagementViewModel
        ↓
MemoryClientService
        ↓
correlated WebSocket request
关联请求
        ↓
RuntimeMessageRouter
        ↓
MemoryProtocolHandler
        ↓
MemoryGovernance
        ↓
MemoryRepository
        ↓
SQLite
```

Governance is explicit request/response behavior.

It is not EventBus RPC.

---

## 7.4 Failure Behavior

```text
Retrieval fails
    ↓
empty prepared Memory
    ↓
chat continues
```

```text
Automatic Learning fails
    ↓
Memory health degraded
    ↓
already-valid chat response remains valid
```

```text
Governance write fails
    ↓
operation reports failure
    ↓
UI must not claim durable success
```

---

# 8. Owner Walkthrough

Before this learning review is marked Complete, the project owner should explain the following once in their own words.

This is not an exam and does not block code correctness.

Answer briefly.

### Q1

Why does `Agent` depend on `MemoryRetriever` instead of directly depending on `SQLiteMemoryRepository`?

### Q2

What is the difference between:

```text
Memory Domain
Memory Scope
Memory Lifecycle
```

Use one example if useful.

### Q3

Why can Memory Retrieval fail-open for ordinary chat, while Edit/Delete governance should fail-closed?

### Q4

Why is:

```text
Relationship Memory
```

not the same thing as:

```text
Relationship Internal State / affection / trust
```

### Q5

Explain the main Phase 4 flow in your own words:

```text
Where does information enter?
Where is Memory stored?
When is it retrieved?
Where does retrieved Memory go?
Where is automatic learning performed?
```

After the owner walkthrough, record only the major correction points here if any.

---

# 9. Knowledge Map into Phase 5

Phase 5 is Situation Engine.

It will reuse several Phase 4 lessons.

## Already Established

```text
explicit domain models
Protocol boundaries
dependency injection
composition root
Event != Command
Intent != Permission
prepared context
failure isolation
Repository boundary
runtime request routing
staged-diff engineering workflow
```

---

## Understanding Still Forming

```text
how domain boundaries evolve across many subsystems
how runtime health should affect higher-level behavior
how factual Memory should influence Situation without owning it
how asynchronous facts and synchronous requests coexist
```

Phase 5 will reinforce these.

---

## Phase 5 Will Reuse Directly

### Event boundary

Situation will likely consume runtime facts/events.

It must not redefine EventBus as command RPC.

### Domain modeling

Situation will need explicit data structures rather than ad-hoc strings.

### Ownership boundaries

```text
Memory
→ factual history/context

Situation
→ interpretation of current facts/events
```

Situation must not own Memory persistence.

### Dependency injection

Situation consumers/producers should depend on explicit capabilities, not concrete global services.

### Failure semantics

Phase 5 should define:

```text
what happens if Situation cannot be produced?
what can degrade?
what must fail?
```

before implementation.

### Prepared data

Just as Composer receives `PreparedMemoryContext`, future engines should prefer prepared/explicit inputs rather than reaching into unrelated infrastructure.

---

# 10. Phase 5 Boundary Preview

The expected conceptual direction is:

```text
Runtime Facts / Events
运行时事实 / 事件
        ↓
Situation Engine
情境引擎
        ↓
Semantic Situation
语义情境
        ↓
future Attention Engine
未来注意力引擎
        ↓
future Behavior Engine
未来行为引擎
```

Phase 5 must preserve:

```text
Memory != Situation
Situation != Attention
Situation != Behavior
Situation != Permission
Event != Command
Intent != Permission
```

A Situation may use factual context.

It must not become a global orchestrator.

---

# 11. Phase 4 Learning Summary

The most important conceptual progression of Phase 4 is:

```text
"remember some text"
    ↓
"model factual Memory explicitly"
    ↓
"separate meaning / scope / lifecycle"
    ↓
"separate domain from persistence"
    ↓
"separate retrieval from composition"
    ↓
"separate extraction from persistence authority"
    ↓
"separate identity resolution from conflict policy"
    ↓
"separate health/failure behavior by capability"
    ↓
"expose governance through explicit request routing"
```

The Phase 4 learning target is not:

```text
memorize every SQLAlchemy/Alembic/WPF line
```

It is:

```text
understand why the system has these boundaries,
what responsibility each boundary owns,
and where a future change should approximately go
```

If that is clear, Phase 4 has achieved its software-engineering learning goal.
