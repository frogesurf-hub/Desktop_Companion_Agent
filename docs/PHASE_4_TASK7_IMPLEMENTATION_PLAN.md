# Desktop Companion Agent — Phase 4 Task 7 Implementation Plan

Status: Active Implementation Baseline
Phase: 4 — Memory System
Task: 7 — Controlled Automatic Memory Learning
Current committed baseline: `843be83 feat(memory): add automatic memory learning service`
Current working increment: Task 7D3 — Inactive / Legacy Closure

---

## 1. Task Goal

Task 7 establishes the controlled write path from a completed conversation turn into durable factual Memory.

Before Task 7:

```text
Stored Memory
    ↓
Memory Retrieval
    ↓
PreparedMemoryContext
    ↓
PromptContextComposer
    ↓
Agent / Provider
```

After Task 7:

```text
Conversation Turn
当前聊天轮次
    ↓
Candidate Extraction
候选提取
    ↓
Eligibility Validation
资格与事实边界验证
    ↓
Existing Memory Resolution
已有记忆定位
    ↓
Conflict / Lifecycle Handling
冲突与生命周期处理
    ↓
Durable Recording
正式持久化
    ↓
MemoryLearningRepository
持久化契约
    ↓
SQLiteMemoryRepository
SQLite Adapter
    ↓
SQLite
事实 Source of Truth
```

Task 7 completes the `Learn → Store → Retrieve → Use` factual-memory loop.

---

## 2. Accepted Architecture Constraints

Task 7 must preserve the accepted Phase 4 architecture:

- factual Memory remains separate from fictional state;
- Character does not own Memory;
- Candidate Memory is not confirmed Memory;
- Candidate Memory never participates in normal Retrieval;
- automatic learning must not bypass Memory policy;
- `PromptContextComposer` remains composition-only;
- SQLite remains the durable factual source of truth;
- existing revision and conflict semantics remain authoritative;
- automatic learning is enabled by default and can be disabled;
- accepted automatic learning becomes active immediately;
- unsupported inference must not enter factual User Profile;
- Memory must not grant Tool / Permission authority;
- Task 8 remains responsible for runtime failure-isolation behavior;
- user-governance deletion must not be silently undone by ordinary automatic learning.
- Memory use cases depend on persistence contracts rather than directly on SQLite;

The implementation must reuse existing domain contracts instead of redesigning them.

---

## 3. Current Reusable Components

Task 7 builds on the existing implementation:

```text
Memory
MemoryRevision
MemoryDomain
MemoryScope
MemoryScopeKind
MemorySource
MemoryLifecycle
MemoryIdentityKey

MemoryRepository
SQLiteMemoryRepository

MemoryConflictPolicy
MemoryConflictDecision

MemoryRetentionPolicy

MemoryRetriever
MemoryRetrievalService
PreparedMemoryContext

MemoryLearningInput
MemoryCandidate
MemoryCandidateExtractor
MemoryLearningPolicy
MemoryEligibilityResult
ExistingMemoryResolver
ExistingMemoryResolution
MemoryLearningService
MemoryLearningResult

Clock / SystemClock

Agent
PromptContextComposer
Settings
```

Important existing `MemorySource` values:

```text
USER_EDIT
USER_EXPLICIT
AUTOMATIC_EXPLICIT_FACT
SYSTEM_OBSERVED
```

Automatic learning commits extracted explicit facts as:

```text
AUTOMATIC_EXPLICIT_FACT
```

unless another already-accepted contract explicitly owns the source.

---

## 4. Relationship Scope Correctness

Task 7A established the required Relationship isolation rule:

```text
GLOBAL_USER Memory
    → shared across Characters

RELATIONSHIP Memory
    → only CHARACTER(active_character_id)
```

Automatic Relationship learning must preserve the same scope rule during both Candidate eligibility and Existing Memory resolution.

---

## 5. Learning Input Boundary

Task 7 uses one completed runtime interaction turn as the learning input.

```text
MemoryLearningInput

- source_message_id
- user_text
- assistant_text
- active_character_id
- occurred_at
```

Requirements:

- contains only information available at the runtime boundary;
- does not require a Conversation database;
- does not depend on Provider-specific types;
- does not depend on Character personality/background content;
- carries the active Character identity required for Relationship scope validation.

---

## 6. Candidate Memory Model

`MemoryCandidate` is a transient, uncommitted factual candidate.

Current fields:

```text
candidate_id
content
domain
scope
source
source_message_id
created_at
identity_key (optional)
occurred_at (optional)
```

A Candidate:

- is not durable Memory;
- is not available to Retrieval;
- has no persistence authority;
- may carry a stable logical `MemoryIdentityKey`;
- must pass later policy / resolution / recording stages.

Task 7 does not introduce numeric confidence, persistent Candidate status, or `conversation_id`.

---

## 7. Candidate Persistence Decision

Task 7 does **not** introduce a `memory_candidates` table.

Lifecycle:

```text
Conversation Turn
    ↓
MemoryCandidate
    ↓
Eligibility / Resolution
    ├─ reject → discard
    └─ accept → durable Memory path
```

Candidate persistence remains deferred until a concrete product requirement exists.

---

## 8. Eligibility Policy

`MemoryLearningPolicy` performs deterministic admission checks after extraction.

Initial checks include:

- source must be `AUTOMATIC_EXPLICIT_FACT`;
- Candidate must originate from the current source message;
- Domain / Scope must be compatible;
- Relationship Candidate must target the active Character.

Boundary:

```text
Extractor
→ semantic candidate boundary

MemoryLearningPolicy
→ deterministic provenance / scope boundary
```

Semantic questions such as whether text is speculative, inferred, fictional, or explicit remain owned by the concrete Extractor in Task 7E.

---

## 9. Existing Memory Resolution

`ExistingMemoryResolver` answers:

```text
Which durable logical Memory, if any,
does this Candidate refer to?
```

Resolution kinds:

```text
NEW
DUPLICATE
EXISTING
```

Primary resolution:

```text
domain
+ scope
+ identity_key
    ↓
logical Memory lookup
```

Persistence guarantees for non-null identity keys:

```text
GLOBAL_USER
domain + GLOBAL_USER scope + identity_key
→ at most one logical Memory

CHARACTER
domain + character_id + identity_key
→ at most one logical Memory per Character
```

Keyless / legacy Memory may still participate in exact-content duplicate fallback.

Important rule:

```text
different non-null identity keys
+ same text
≠ duplicate
```

Resolver remains read-only and does not persist, replace, reactivate, or delete Memory.

---

## 10. Learning Service / Orchestration Boundary

`MemoryLearningService` is the Task 7 write-path use-case orchestrator.

```text
MemoryCandidate
    ↓
MemoryLearningPolicy
Eligibility
    ↓
ExistingMemoryResolver
Identity / duplicate resolution
    ↓
MemoryLearningService
Use-case orchestration
    ↓
MemoryConflictPolicy
ACTIVE conflict decision
    ↓
MemoryLearningRepository
Durable mutation boundary
```

It does not:

- extract natural-language Candidates;
- render Prompt content;
- perform Retrieval;
- implement SQL;
- own Character personality;
- expose WebSocket protocol;
- implement Task 8 runtime failure fallback;
- control Tools or Permission.

### 10.1 Current outcomes

```text
REJECTED
CREATED
DUPLICATE
IDENTITY_ADOPTED
KEPT_CURRENT
REPLACED
REACTIVATED
BLOCKED_DELETED
```

### 10.2 Base write behavior

```text
Ineligible Candidate
→ REJECTED
→ Resolver not called
→ no durable write

NEW
→ create Memory
→ create Revision 1 ACTIVE

DUPLICATE
→ no content Revision write

EXISTING + ACTIVE
→ MemoryConflictPolicy
    ├─ KEEP_CURRENT
    └─ REPLACE
```

### 10.3 Legacy identity adoption

When a keyed Candidate exactly duplicates an ACTIVE legacy/keyless Memory:

```text
legacy Memory(identity_key=None)
+ keyed Candidate
+ exact active duplicate
    ↓
adopt_identity_key()
    ↓
same logical Memory gains stable identity
```

No new content Revision is created because factual content did not change.

Identity adoption is one-way:

```text
NULL → identity_key
```

Reassigning a different identity key is rejected.

### 10.4 EXPIRED reactivation

`EXPIRED` is an inactive retention state, not an ACTIVE conflict.

When the same logical Memory is resolved and its latest Revision is `EXPIRED`:

```text
EXPIRED latest Revision
+ new eligible explicit Candidate
    ↓
append next ACTIVE Revision
    ↓
REACTIVATED
```

The old `EXPIRED` Revision remains `EXPIRED`.

`MemoryConflictPolicy` is not used for this path because no ACTIVE factual revision is competing with the incoming Candidate.

### 10.5 DELETED blocking

`DELETED` represents user-governance deletion / forget semantics.

Ordinary automatic learning must not silently reverse it.

```text
DELETED tombstone
+ new automatic Candidate
    ↓
BLOCKED_DELETED
    ↓
no create
no replace
no reactivation
```

If future product behavior allows restoring deleted Memory, that must use an explicit governance / recovery semantic rather than ordinary automatic learning.

This blocking guarantee applies when the deleted logical Memory
can still be deterministically resolved, normally through a stable
non-null `MemoryIdentityKey`.

A legacy/keyless deleted tombstone has neither semantic identity nor
retained factual content available for safe automatic matching.
Task 7 does not guess that a later Candidate refers to such a tombstone.

This is an explicit compatibility limitation rather than permission to
semantically reconstruct deleted content.

### 10.6 Unsupported latest lifecycle

A logical Memory whose latest Revision is `SUPERSEDED` without a newer authoritative state is treated as invalid durable state.

```text
latest = SUPERSEDED
→ MemoryLearningStateError
```

The Learning Service must not guess recovery behavior for structurally inconsistent persistence state.

---

## 11. Learning Persistence Boundary

Task 7D uses a narrow `MemoryLearningRepository` Protocol rather than expanding unrelated callers to depend on the entire persistence surface.

Current mutation needs:

```text
create_memory()
replace_active_revision()
adopt_identity_key()
reactivate_memory()
```

`SQLiteMemoryRepository` provides these operations.

The automatic-learning service depends on capabilities, not on SQLAlchemy.

---

## 12. Extractor Boundary

`MemoryCandidateExtractor` converts runtime learning input into zero or more `MemoryCandidate` objects.

Conceptual contract:

```text
MemoryLearningInput
    ↓
MemoryCandidateExtractor
    ↓
tuple[MemoryCandidate, ...]
```

The Extractor:

- identifies explicit candidate facts;
- selects supported Memory domain;
- assigns valid scope;
- assigns `AUTOMATIC_EXPLICIT_FACT`;
- assigns identity key when a stable logical slot exists;
- does not persist;
- does not resolve conflicts;
- does not call `SQLiteMemoryRepository`.

Concrete extraction remains Task 7E.

---

## 13. Extraction Strategy for Task 7

Implementation order remains:

```text
stable contract first
    ↓
replaceable concrete extractor second
```

If LLM-assisted extraction is used:

```text
LLM output
≠ confirmed Memory
```

It must still pass through:

```text
Candidate
→ Eligibility
→ Existing Memory Resolution
→ Learning Service
→ Conflict / Lifecycle Handling
→ Repository
```

No extractor receives unrestricted direct persistence authority.

---

## 14. Automatic Learning Configuration

Task 7F adds runtime configuration equivalent to:

```text
automatic_learning_enabled: bool = True
```

Expected behavior:

```text
enabled = true
→ automatic learning pipeline may run

enabled = false
→ no automatic Memory writes
→ Retrieval remains available
→ manual Governance remains available
```

Configuration is runtime policy, not factual Memory.

---

## 15. Runtime Integration Point

Task 7F integrates learning after a normal assistant response is available.

```text
User Message
    ↓
Memory Retrieval
    ↓
Prompt Composition
    ↓
Provider
    ↓
Assistant Response
    ↓
Automatic Memory Learning
```

This ensures:

- the current prompt is not retroactively changed;
- the complete turn is available to the extractor;
- newly learned Memory becomes available to later Retrieval;
- learning remains an explicit use-case boundary.

Task 8 owns recoverable runtime failure isolation.

---

## 16. Implementation Breakdown and Current Status

### Task 7A — Scope Correctness + Learning Contracts

Status: Completed

Implemented:

- active-Character Relationship retrieval isolation;
- `MemoryLearningInput`;
- `MemoryCandidate`;
- `MemoryCandidateExtractor` Protocol.

### Task 7B — Eligibility Policy

Status: Completed

Implemented:

- automatic-learning source admission;
- source-message provenance checks;
- Domain / Scope validation;
- active-Character Relationship isolation.

### Task 7C — Existing Memory Resolution

Status: Completed

Implemented:

```text
7C1
Logical Memory Identity Contract

7C2
Identity Persistence + Alembic migration

7C3-A
Identity Lookup + Persistence Uniqueness

7C3-B
ExistingMemoryResolver
```

Key behavior:

- identity-first resolution;
- deterministic exact-content legacy fallback;
- no fuzzy semantic matching;
- no embeddings / vector database;
- Character-scoped logical identity isolation.

### Task 7D — Learning Service + Durable Recording

Status: Completed — ready for checkpoint

#### Task 7D1 — Learning persistence primitives

Completed:

- `adopt_identity_key()`;
- `reactivate_memory()`;
- repository-level tests.

#### Task 7D2 — MemoryLearningService basic flow

Completed:

```text
REJECTED
CREATED
DUPLICATE
KEPT_CURRENT
REPLACED
```

#### Task 7D3 — Inactive / Legacy closure

implemented:

```text
IDENTITY_ADOPTED
REACTIVATED
BLOCKED_DELETED
unsupported SUPERSEDED latest → state error
```

Targeted validation at current working state:

```text
63 passed
Ruff: passed
mypy: passed (92 source files)
git diff --check: clean
```

Task 7D3 — Inactive / Legacy closure
Status: Completed

D3 is complete after staged review, commit, and push.

### Task 7E — Concrete Candidate Extraction

Status: Pending

Goals:

- implement initial replaceable extractor;
- prioritize explicit / high-certainty factual statements;
- avoid unsupported inference;
- assign supported domain, scope, provenance and logical identity;
- produce only transient Candidate objects.

Required coverage includes:

- explicit preference;
- explicit user fact;
- explicit durable project/context;
- explicit episodic fact;
- Relationship fact with active Character scope;
- speculative / inferred statements not emitted as factual Memory.

### Task 7F — Runtime + Settings Integration

Status: Pending

Goals:

- add automatic-learning configuration;
- construct Task 7 components in Composition Root;
- integrate learning after successful conversation turns;
- preserve Provider / Retrieval / Composer boundaries;
- verify disabled automatic learning performs no writes.

Expected acceptance:

```text
chat succeeds
→ eligible explicit fact learned
→ later Retrieval sees learned Memory
```

and:

```text
automatic learning disabled
→ chat works
→ Retrieval works
→ no automatic write
```

Failure isolation beyond the minimum safe integration remains Task 8.

---

## 17. File Placement

Current Task 7 structure:

```text
src/agent_core/memory/
├── learning/
│   ├── __init__.py
│   ├── models.py
│   ├── extractor.py
│   ├── policy.py
│   ├── resolver.py
│   └── service.py
│
├── models.py
├── repository.py
├── conflict.py
├── persistence/
│   ├── orm.py
│   ├── mapper.py
│   └── sqlite_repository.py
├── retrieval.py
├── retriever.py
├── retrieval_policy.py
└── retrieval_service.py
```

Later Task 7F integration may affect:

```text
src/agent_core/core/agent.py
src/agent_core/main.py
src/agent_core/config/settings.py
```

No file should be created merely to satisfy a diagram.

---

## 18. Testing Strategy

Required Task 7 behavior coverage now includes:

```text
Candidate model invariants
Eligibility accepted / rejected cases
Relationship scope isolation

Logical identity normalization
Identity persistence
Identity uniqueness
Character identity isolation

NEW resolution
DUPLICATE resolution
EXISTING resolution
Legacy exact-content fallback
Different identity keys are not merged

New Memory creation
Duplicate suppression
Conflict KEEP_CURRENT
Conflict REPLACE
Revision increment
Source preservation

Legacy identity adoption
EXPIRED reactivation
DELETED automatic-resurrection blocking
Invalid latest lifecycle rejection

Automatic-learning enabled
Automatic-learning disabled
Runtime learning integration
Later Retrieval sees learned Memory
```

Each subtask continues to use:

```text
targeted pytest
python -m ruff check .
python -m mypy src
git diff --check
working diff review
staged diff --check
staged diff review
commit
push
```

Full pytest remains an owner-level acceptance gate at the appropriate Task / Phase checkpoint.

---

## 19. Explicit Non-Goals

Task 7 does not implement:

- Candidate review UI;
- Candidate SQLite persistence;
- full Conversation / Session subsystem;
- embeddings;
- vector search;
- RAG framework;
- Mem0 integration;
- LangGraph integration;
- advanced semantic ranking;
- automatic summarization/compression;
- Memory WebSocket management protocol;
- WPF Memory management UI;
- broad Memory failure-isolation behavior;
- Permission;
- Tools;
- Situation / Attention / Behavior;
- Mood / affection / trust state;
- fictional-state persistence.

These remain outside Task 7 unless the owner explicitly changes scope.

---

## 20. Completion Criteria

Task 7 is complete when all of the following are true:

1. A completed chat turn can enter a controlled automatic-learning boundary.
2. Candidate information is structurally separate from confirmed Memory.
3. Invalid Candidates cannot write factual Memory.
4. Candidate extraction cannot directly persist Memory.
5. Existing logical Memory is resolved before conflict handling.
6. Logical identity is deterministic within Domain + Scope.
7. Legacy/keyless exact duplicates can safely adopt a stable identity key.
8. Existing `MemoryConflictPolicy` controls ACTIVE-vs-ACTIVE replacement.
9. New accepted facts can create durable Memory.
10. Accepted ACTIVE updates can produce correct revisions.
11. EXPIRED logical Memory can be reactivated through a new ACTIVE revision.
12. A resolvable DELETED logical Memory cannot be silently resurrected
    by ordinary automatic learning.
13. Duplicate Candidates do not create unnecessary duplicate Memory.
14. Relationship Memory respects active Character scope.
15. Automatic learning can be disabled without disabling Retrieval/Governance.
16. Newly learned Memory is available to later Retrieval.
17. Existing Agent / Provider / Character / Composer boundaries remain intact.
18. Targeted tests, Ruff, mypy and diff checks pass.
19. Final staged diff is reviewed before commit.
20. Task 7 receives clear commits and is pushed to the remote repository.

---

## 21. Actual Commit Progression

Current confirmed Task 7 commits:

```text
b64d4d76 feat(memory): establish automatic learning contracts
ebdc2ce0 feat(memory): add learning eligibility policy
ca351db  feat(memory): add logical memory identity keys
4fadc5a  feat(memory): persist logical memory identity keys
2d91b09  feat(memory): add logical memory identity lookup
f2d15ba  feat(memory): add existing memory resolver
066a9dd  feat(memory): add learning persistence primitives
843be83  feat(memory): add automatic memory learning service
```

Suggested next checkpoint for Task 7D3:

```text
feat(memory): close automatic learning lifecycle states
```

Task 7E and Task 7F should continue with separate reviewable commits.

---

## 22. Documentation Synchronization

Task 7 documentation must stay synchronized with the implementation rather than the original proposal.

Current authoritative inputs remain:

```text
Current Git repository source
docs/DEVELOPMENT_UNDERSTANDING.md
docs/PHASE_4_MEMORY_SYSTEM_DESIGN.md
docs/PHASE_4_TASK7_IMPLEMENTATION_PLAN.md
ADR 0016
ADR 0017
ADR 0018
ADR 0020
```

Task 7D lifecycle behavior is consistent with ADR 0016:

```text
ACTIVE
SUPERSEDED
EXPIRED
DELETED
```

Task 7 does not require a new ADR solely for the D3 implementation because:

- logical identity is already owned by ADR 0020;
- lifecycle / delete semantics are already owned by ADR 0016;
- D3 defines how the accepted Task 7 learning use case applies those existing decisions.

If later product requirements change deleted-Memory recovery semantics, that change should receive an explicit architecture / owner decision before implementation.

Current repository source remains the highest-priority engineering baseline.
