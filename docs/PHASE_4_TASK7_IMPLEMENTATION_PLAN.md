# Desktop Companion Agent — Phase 4 Task 7 Implementation Plan

Status: Approved Implementation Baseline
Phase: 4 — Memory System
Task: 7 — Controlled Automatic Memory Learning
Repository baseline: `8ede434`
Last functional baseline: `6484849 feat(memory): integrate memory retrieval into agent runtime`

---

## 1. Task Goal

Task 7 establishes the controlled write path from a real conversation turn into durable factual Memory.

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

The runtime can already retrieve and use Memory, but it cannot safely learn new factual Memory from conversation.

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
Conflict Handling
冲突裁决
    ↓
Durable Recording
正式持久化
    ↓
MemoryRepository / SQLite
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
- `MemoryRepository` remains the persistence boundary;
- SQLite remains the durable factual source of truth;
- existing revision and conflict semantics remain authoritative;
- automatic learning is enabled by default and can be disabled;
- accepted automatic learning becomes active immediately;
- unsupported inference must not enter factual User Profile;
- Memory must not grant Tool / Permission authority;
- Task 8 remains responsible for failure-isolation behavior.

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

MemoryRepository
SQLiteMemoryRepository

MemoryConflictPolicy
MemoryConflictDecision

MemoryRetentionPolicy

MemoryRetriever
MemoryRetrievalService
PreparedMemoryContext

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

Automatic learning should normally commit learned explicit facts as:

```text
AUTOMATIC_EXPLICIT_FACT
```

unless an existing accepted contract requires another source.

---

## 4. Required Correctness Fix Before Automatic Relationship Learning

Current `MemoryRetrievalService` retrieves all Relationship Memory without restricting it to the active Character.

This is incompatible with the accepted Phase 4 scope rule:

```text
RELATIONSHIP
    → CHARACTER scope
```

Before Task 7 is allowed to automatically create Relationship Memory, retrieval must enforce active-character isolation.

Target behavior:

```text
GLOBAL_USER Memory
    → shared across Characters

RELATIONSHIP Memory
    → only CHARACTER(active_character_id)
```

This is a prerequisite correctness fix, not a redesign of the Retrieval subsystem.

---

## 5. Learning Input Boundary

Task 7 must not introduce a full Conversation / Session subsystem solely for Memory learning.

The current runtime has `Message`, but no stable `ConversationContext` aggregate or `conversation_id` architecture.

Therefore Task 7 uses a minimal runtime learning input representing one completed interaction turn.

Conceptual model:

```text
MemoryLearningInput
自动学习输入

- source_message_id
- user_text
- assistant_text
- active_character_id
- occurred_at / recorded_at context
```

Exact Python naming can be finalized during implementation.

Requirements:

- must contain only information already available at the runtime boundary;
- must not require a new Conversation database;
- must not depend on Provider-specific types;
- must not depend on Character personality/background data;
- may carry `active_character_id` so Relationship scope can be constructed correctly.

---

## 6. Candidate Memory Model

`MemoryCandidate` is a transient domain object representing uncommitted information.

Recommended fields:

```text
candidate_id
content
domain
scope
source
source_message_id
created_at
occurred_at (optional)
```

Optional fields may be added only when implementation demonstrates a concrete need.

### Explicitly excluded from the initial Candidate model

#### Numeric confidence

Do not introduce pseudo-precise values such as:

```text
0.72
0.88
0.95
```

Phase 4 has not accepted calibrated confidence scoring.

Eligibility should use explicit deterministic semantics where possible.

#### Persistent candidate status

Do not initially require:

```text
PENDING
ACCEPTED
REJECTED
```

unless Candidate persistence is later approved.

Validation outcome belongs to a separate result object.

#### conversation_id

Do not add it until the project has a real Conversation / Session identity model.

---

## 7. Candidate Persistence Decision

Task 7 does **not** introduce a `memory_candidates` SQLite table by default.

Initial lifecycle:

```text
Conversation Turn
    ↓
MemoryCandidate
    ↓
Validation / Resolution
    ├─ reject → discard
    └─ accept → durable Memory commit
```

Candidate persistence is deferred until a real product requirement exists, such as:

- manual candidate approval;
- candidate audit/history;
- delayed processing;
- retry queues;
- candidate-management UI.

This avoids introducing an unnecessary table, migration, repository, lifecycle and governance surface.

---

## 8. Eligibility Policy

Task 7 needs a deterministic policy boundary that decides whether a Candidate is allowed to proceed.

The Eligibility Policy performs deterministic admission checks after
Candidate extraction.

Initial rejection conditions:

- Candidate source is not `AUTOMATIC_EXPLICIT_FACT`;
- Candidate does not originate from the current source message;
- Candidate domain and scope are incompatible;
- Relationship Memory targets a Character other than the active Character.

Semantic questions such as whether a statement is explicit, speculative,
inferred from repetition, psychological interpretation, or Character
fiction belong to Candidate Extraction in Task 7E.

Therefore:

```text
Extractor
→ semantic candidate boundary

Eligibility Policy
→ deterministic provenance / scope boundary

Initial rejection targets:

- speculative personality inference;
- emotional or psychological diagnosis;
- unsupported preference inference;
- conclusions inferred only from repetition/frequency;
- Character fiction presented as real-user fact;
- empty or structurally invalid content;
- scope/domain combinations rejected by existing Memory domain rules.

Conceptual boundary:

```text
MemoryLearningPolicy
    input: MemoryCandidate
    output: eligibility result
```

The policy does not persist Memory.

---

## 9. Existing Memory Resolution

The existing `MemoryConflictPolicy` only resolves conflicts **after two revisions are known to belong to the same logical Memory**.

Task 7 must therefore introduce a distinct resolution boundary:

```text
MemoryCandidate
    ↓
ExistingMemoryResolver
    ↓
No match
    → create new Memory

Same logical fact
    → inspect current revision
    → conflict policy

Duplicate
    → keep existing / no-op
```

Responsibilities:

- locate whether the candidate corresponds to an existing logical Memory;
- distinguish new fact vs duplicate vs conflicting update;
- return the existing `memory_id` when appropriate.

It must not independently perform persistence mutation.

### Important distinction

```text
Conflict Detection / Identity Resolution
→ Which existing Memory does this candidate refer to?

Conflict Resolution
→ If it is the same Memory, should incoming information replace current information?
```

`MemoryConflictPolicy` already owns the second responsibility.

---

## 10. Learning Service / Orchestration Boundary

Task 7 requires one explicit use-case service that connects the learning stages.

Conceptual flow:

```text
MemoryLearningService
    ↓
Extractor
    ↓
Eligibility Policy
    ↓
Existing Memory Resolver
    ↓
MemoryConflictPolicy
    ↓
MemoryRepository
```

Responsibilities:

- orchestrate the learning pipeline;
- create a new `Memory` + initial `MemoryRevision` when no existing logical Memory matches;
- create a new revision when a valid replacement is accepted;
- preserve source/lifecycle/timestamp semantics;
- avoid writes for rejected or duplicate candidates;
- expose a stable result describing what happened.

It does not:

- render Prompt content;
- perform Retrieval;
- own Character personality;
- expose WebSocket protocol;
- implement Task 8 failure fallback;
- control Tools or Permission.

---

## 11. Extractor Boundary

The extraction layer converts runtime learning input into one or more `MemoryCandidate` objects.

Contract concept:

```text
MemoryCandidateExtractor

input:
    MemoryLearningInput

output:
    tuple[MemoryCandidate, ...]
```

The Extractor:

- identifies explicit candidate facts;
- selects a supported Memory domain;
- assigns valid scope;
- assigns `AUTOMATIC_EXPLICIT_FACT` provenance;
- does not persist;
- does not validate final eligibility;
- does not resolve conflicts.

The Extractor must not depend directly on:

- `Agent`;
- `SQLiteMemoryRepository`;
- SQLAlchemy;
- WPF;
- CharacterDefinition personality content;
- Tool system.

It may receive already-prepared runtime facts such as the active Character ID.

---

## 12. Extraction Strategy for Task 7

The accepted Phase 4 architecture does not mandate rule-based or LLM-assisted extraction.

For Task 7, implementation should proceed in two layers:

### Contract first

Establish the stable learning models and Protocol boundaries independently of extraction technology.

### Concrete extractor second

Select the smallest implementation capable of satisfying the initial automatic-learning requirements without granting unrestricted persistence authority.

If LLM-assisted extraction is used:

```text
LLM output
    ≠ Memory
```

It must still pass through:

```text
Candidate
→ Eligibility
→ Existing Memory Resolution
→ Conflict Policy
→ Repository
```

The extractor must never call `MemoryRepository` directly.

---

## 13. Automatic Learning Configuration

Add runtime configuration for automatic learning.

Conceptual setting:

```text
automatic_learning_enabled: bool = True
```

Expected behavior:

```text
enabled = true
    → Task 7 learning pipeline runs

enabled = false
    → no new automatic Memory is produced
    → existing Retrieval continues
    → manual Governance continues
```

Configuration is runtime policy, not factual Memory content.

Exact environment-variable spelling should follow the existing `Settings` naming convention.

---

## 14. Runtime Integration Point

Task 7 should integrate only after an ordinary chat turn has produced the information required by the learning input.

Conceptually:

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

Rationale:

- the learning input can include the completed turn;
- learning does not alter the already-composed current prompt;
- newly committed Memory becomes available on later Retrieval;
- learning remains a separate use-case boundary.

Task 8 will later define recoverable failure behavior so an automatic-learning write failure cannot retroactively fail an otherwise valid chat response.

Task 7 itself should keep the integration boundary explicit and testable.

---

## 15. Proposed Implementation Breakdown

Task 7 should be implemented as small reviewable increments.

### Task 7A — Scope Correctness + Learning Domain Contracts

Goals:

- fix Relationship Retrieval to respect active Character scope;
- introduce minimal learning-input model;
- introduce transient `MemoryCandidate`;
- introduce the `MemoryCandidateExtractor` Protocol;
- keep eligibility / validation-result semantics deferred to Task 7B.

Expected verification:

- targeted tests for Relationship scope;
- model validation tests;
- Protocol/static typing checks.

---

### Task 7B — Eligibility Policy

Goals:

- implement deterministic Candidate admission rules;
- validate automatic-learning provenance;
- validate source-message provenance;
- preserve Domain / Scope invariants;
- enforce active-Character isolation for Relationship candidates;
- keep semantic extraction decisions in Task 7E;
- keep policy independent from persistence.

Expected verification:

- supported automatic-learning source is accepted;
- unsupported source is rejected;
- mismatched source message is rejected;
- Domain / Scope mismatch is rejected;
- Relationship candidate for another Character is rejected.

---

### Task 7C — Existing Memory Resolution

Goals:

- add the boundary responsible for locating an existing logical Memory;
- distinguish:
  - new Memory;
  - duplicate;
  - conflicting update;
- keep matching separate from `MemoryConflictPolicy`.

Expected verification:

- no existing match;
- exact duplicate;
- existing logical fact found;
- domain/scope isolation;
- Relationship Character isolation.

The first matching algorithm should be deliberately simple and deterministic unless a stronger mechanism is justified during implementation.

No embeddings or vector database are introduced.

---

### Task 7D — Learning Service + Durable Recording

Goals:

- orchestrate candidate → validation → resolution → conflict → commit;
- reuse `MemoryConflictPolicy`;
- reuse `MemoryRepository`;
- create new logical Memory atomically;
- replace existing active revision through existing repository semantics;
- preserve revision/source/lifecycle/time rules.

Expected verification:

- accepted new candidate creates Memory revision 1;
- duplicate produces no unnecessary write;
- higher-authority/current policy behavior is preserved;
- valid replacement creates next revision;
- old revision becomes `SUPERSEDED`;
- rejected candidate does not persist.

---

### Task 7E — Concrete Candidate Extraction

Goals:

- implement the initial automatic extraction mechanism;
- prioritize explicit/high-certainty statements;
- avoid unsupported inference;
- produce only Candidate objects.

Expected verification:

- explicit preference;
- explicit user fact;
- explicit durable project/context;
- explicit episodic fact;
- Relationship candidate with active Character scope;
- speculative statement rejected or not emitted.

The concrete extraction mechanism must remain replaceable behind the extractor contract.

---

### Task 7F — Runtime + Settings Integration

Goals:

- add automatic-learning configuration;
- construct Task 7 components in the Composition Root;
- integrate learning after a successful conversation turn;
- preserve Provider, Retrieval and Composer boundaries;
- confirm disabled automatic learning performs no writes.

Expected verification:

```text
chat
→ response succeeds
→ eligible fact learned
→ later Retrieval sees it
```

and:

```text
automatic learning disabled
→ chat works
→ existing Retrieval works
→ no automatic write occurs
```

Failure fallback beyond the minimum safe contract remains Task 8.

---

## 16. Likely File Placement

Exact names may be adjusted after inspecting each implementation step, but the intended structure is:

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
├── retrieval.py
├── retriever.py
├── retrieval_policy.py
└── retrieval_service.py
```

Potential integration changes:

```text
src/agent_core/core/agent.py
src/agent_core/main.py
src/agent_core/config/settings.py
src/agent_core/memory/__init__.py
```

Tests should mirror the corresponding contracts and behaviors.

No file should be created merely to satisfy this layout if implementation does not require it.

---

## 17. Testing Strategy

Each subtask should use targeted tests first.

Required Task 7 behavior coverage should include:

```text
Candidate model invariants
Eligibility accepted/rejected cases
Relationship scope isolation
New Memory creation
Duplicate suppression
Existing Memory resolution
Conflict replacement
Revision increment
Source preservation
Automatic-learning enabled
Automatic-learning disabled
Runtime learning integration
Later Retrieval sees learned Memory
```

Task 7 should preserve existing tests.

Quality gates:

```text
targeted pytest
python -m ruff check .
python -m mypy src
git diff --check
working diff review
staged diff --check
staged diff review
```

Full pytest remains owner-level acceptance at the appropriate checkpoint, following the existing development contract.

---

## 18. Explicit Non-Goals

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

## 19. Completion Criteria

Task 7 is complete when all of the following are true:

1. A completed chat turn can enter a controlled learning boundary.
2. Candidate information is structurally separate from confirmed Memory.
3. Unsupported or invalid candidates cannot write factual Memory.
4. Candidate extraction cannot directly persist Memory.
5. Existing Memory can be resolved before conflict handling.
6. Existing `MemoryConflictPolicy` participates in replacement decisions.
7. New accepted facts can create durable Memory.
8. Accepted updates can produce correct revisions.
9. Duplicate candidates do not create unnecessary duplicate Memory.
10. Relationship Memory respects active Character scope.
11. Automatic learning can be disabled without disabling Retrieval/Governance.
12. Newly learned Memory is available to later Retrieval.
13. Existing Agent / Provider / Character / Composer boundaries remain intact.
14. Targeted tests, Ruff, mypy and diff checks pass.
15. Final staged diff is reviewed before commit.
16. Task 7 receives a clear commit and is pushed to the remote repository.

---

## 20. Recommended Commit Structure

Prefer several small semantic commits if needed during development, followed by one clear Task checkpoint.

Possible sequence:

```text
fix(memory): enforce relationship retrieval scope
feat(memory): add automatic learning contracts
feat(memory): add learning eligibility and resolution
feat(memory): add durable automatic memory recording
feat(memory): add automatic candidate extraction
feat(memory): integrate automatic learning into runtime
```

If the implementation remains compact enough, related steps may be combined, but each commit must remain reviewable.

---

## 21. Documentation Synchronization

Before or during Task 7 implementation:

1. update `docs/PHASE_4_TASK_WORKFLOW.md`
   - Task 6 → Completed
   - Next Starting Point → Task 7;

2. add this implementation plan under `docs/`;

3. after Task 7 completion, update current task/recovery context to the final commit and validation state.

The design and implementation must continue to follow:

```text
docs/DEVELOPMENT_UNDERSTANDING.md
docs/PHASE_4_MEMORY_SYSTEM_DESIGN.md
ADR 0016
ADR 0017
ADR 0018
current Git repository source
```

Current repository source remains the highest-priority engineering baseline.
