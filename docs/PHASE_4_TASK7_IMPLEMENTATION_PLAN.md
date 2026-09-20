# Desktop Companion Agent — Phase 4 Task 7 Implementation Plan

Status: Completed
Phase: 4 — Memory System
Task: 7 — Controlled Automatic Memory Learning
Final implementation baseline: `dc03908 feat(memory): wire automatic learning composition root`

---

## 1. Goal

Task 7 establishes the controlled write path from a completed conversation turn into durable factual Memory.

Final runtime flow:

```text
Conversation Turn
    ↓
LLMMemoryCandidateExtractor
semantic candidate extraction
    ↓
MemoryLearningPolicy
eligibility / provenance / scope validation
    ↓
ExistingMemoryResolver
logical identity / duplicate resolution
    ↓
MemoryLearningService
conflict + lifecycle orchestration
    ↓
MemoryLearningRepository
persistence contract
    ↓
SQLiteMemoryRepository
    ↓
SQLite
```

The completed factual-memory loop is now:

```text
Learn → Store → Retrieve → Use
```

---

## 2. Architecture Constraints Preserved

Task 7 preserves the accepted Phase 4 architecture:

- factual Memory remains separate from fictional state;
- Character does not own Memory;
- Candidate Memory is transient and unconfirmed;
- Candidate Memory never participates in normal Retrieval;
- automatic learning cannot bypass deterministic Memory policy;
- `PromptContextComposer` remains composition-only;
- SQLite remains the durable factual source of truth;
- use cases depend on persistence contracts rather than directly on SQLite;
- `Intent != Permission` remains unchanged;
- Memory never grants Tool or Permission authority;
- Relationship Memory remains Character-scoped;
- user-governance deletion cannot be silently reversed by ordinary automatic learning;
- Task 8 remains responsible for broad runtime failure isolation and diagnostics.

---

## 3. Learning Input and Candidate Boundary

A completed runtime interaction is represented by:

```text
MemoryLearningInput
- source_message_id
- user_text
- assistant_text
- active_character_id
- occurred_at
```

The extractor produces transient:

```text
MemoryCandidate
- candidate_id
- content
- domain
- scope
- source
- source_message_id
- created_at
- identity_key (optional)
- occurred_at (optional)
```

The LLM is allowed to propose only:

```text
content
domain
identity_key
```

The following remain locally controlled:

```text
candidate_id
source
source_message_id
scope / character_id
created_at
occurred_at
persistence authority
```

Candidate persistence is intentionally not introduced. Rejected Candidates are discarded; accepted Candidates move through the durable Memory path.

---

## 4. Eligibility Policy

`MemoryLearningPolicy` performs deterministic admission checks after extraction.

Current checks include:

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

---

## 5. Logical Memory Identity

`MemoryIdentityKey` represents a stable semantic factual slot owned by logical Memory.

Primary resolution:

```text
domain
+ scope
+ identity_key
→ logical Memory
```

Persistence guarantees:

```text
GLOBAL_USER
Domain + GLOBAL_USER scope + identity_key
→ at most one logical Memory

CHARACTER
Domain + character_id + identity_key
→ at most one logical Memory per Character
```

Keyless / legacy Memory may still participate in deterministic exact-content duplicate fallback.

Important rule:

```text
different non-null identity keys
+ same text
≠ duplicate
```

### Canonical identity across paraphrases

The real DeepSeek acceptance test initially exposed unstable keys for two paraphrases of the same game-development language preference.

The extraction prompt was refined so identity is generated from the semantic slot rather than surface wording.

The accepted canonical result for both paraphrases became:

```text
user_profile.preference.game_development.programming_language
```

This preserves meaningful context without encoding the current value into the key.

---

## 6. Existing Memory Resolution

`ExistingMemoryResolver` returns:

```text
NEW
DUPLICATE
EXISTING
```

It is read-only and does not persist, replace, reactivate, or delete Memory.

Resolution is identity-first, then deterministic exact-content fallback for keyless / legacy compatibility.

No fuzzy semantic matching, embeddings, or vector database are introduced in Task 7.

---

## 7. Learning Service and Lifecycle Semantics

`MemoryLearningService` orchestrates:

```text
Eligibility
→ Existing Memory Resolution
→ Conflict / Lifecycle decision
→ Durable mutation
```

Supported outcomes:

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

### NEW

```text
NEW
→ create Memory
→ create Revision 1 ACTIVE
```

### DUPLICATE

```text
exact duplicate
→ no unnecessary content Revision
```

### Legacy identity adoption

```text
legacy Memory(identity_key=None)
+ keyed exact duplicate Candidate
→ adopt_identity_key()
```

No new content Revision is created because factual content did not change.

### ACTIVE conflict

```text
ACTIVE current revision
+ incoming Candidate
→ MemoryConflictPolicy
    ├─ KEEP_CURRENT
    └─ REPLACE
```

### EXPIRED reactivation

```text
latest = EXPIRED
+ eligible explicit Candidate
→ append next ACTIVE Revision
→ REACTIVATED
```

The old EXPIRED Revision remains EXPIRED.

### DELETED blocking

```text
resolvable DELETED logical Memory
+ automatic Candidate
→ BLOCKED_DELETED
→ no create / replace / reactivation
```

This guarantee applies when the deleted logical Memory can still be deterministically resolved, normally through a stable non-null `MemoryIdentityKey`.

A legacy/keyless deleted tombstone has neither retained factual content nor a stable semantic identity available for safe matching. Task 7 does not guess that a later Candidate refers to such a tombstone.

### Unsupported lifecycle

A logical Memory whose latest Revision is unexpectedly `SUPERSEDED` without a newer authoritative state is treated as invalid durable state and raises `MemoryLearningStateError`.

---

## 8. Concrete Candidate Extraction

Task 7 uses `LLMMemoryCandidateExtractor` behind the provider-neutral `MemoryCandidateExtractor` boundary.

```text
MemoryLearningInput
    ↓
LLMMemoryCandidateExtractor
    ↓
LLMProvider
    ↓
strict local structured-output validation
    ↓
MemoryCandidate[]
```

The extractor:

- only extracts facts explicitly stated by the user;
- rejects speculative / uncertain statements;
- does not turn assistant-only assertions into user facts;
- keeps fictional Character state outside factual Memory;
- assigns Relationship scope from the local active Character;
- assigns `AUTOMATIC_EXPLICIT_FACT` locally;
- uses `Clock.now()` for Candidate creation time;
- does not reinterpret chat time as event occurrence time;
- does not persist or resolve conflicts.

Structured output fails closed:

- invalid JSON → rejected;
- unknown Memory domain → rejected;
- unknown / extra fields → rejected;
- attempts to supply authority fields such as `source` or `character_id` → rejected.

Task 7 does not expand the Phase 1 provider contract solely to add provider-specific structured-output APIs.

---

## 9. Turn-Level Runtime Boundary

Task 7F introduces:

```text
MemoryTurnLearner
```

as the only automatic-learning dependency known by `Agent`.

Concrete runtime implementation:

```text
AutomaticMemoryTurnLearner
→ MemoryCandidateExtractor
→ MemoryLearningService
```

Multiple Candidates from the same turn are processed sequentially:

```text
Candidate 1 write
→ Candidate 2 resolves against updated durable state
```

No parallel Candidate writes are introduced.

The `Agent` runtime order is:

```text
Memory Retrieval
→ Prompt Composition
→ Provider.generate()
→ successful assistant response
→ MemoryTurnLearner.learn_turn()
→ response returned
```

Provider failure does not produce a completed turn and therefore does not trigger Memory Learning.

---

## 10. Settings and Composition Root

Runtime setting:

```text
automatic_learning_enabled: bool = True
```

Environment setting:

```text
DCA_AUTOMATIC_LEARNING_ENABLED=true
```

Default behavior:

```text
enabled = true
→ automatic learning pipeline is constructed
```

Disabled behavior:

```text
enabled = false
→ memory_learner = None
→ chat remains available
→ Memory Retrieval remains available
→ manual Governance remains available
→ no automatic Memory writes
```

`main.py` owns concrete assembly because it is the Composition Root:

```text
LLMMemoryCandidateExtractor
→ ExistingMemoryResolver
→ MemoryLearningService
→ AutomaticMemoryTurnLearner
→ Agent
```

`Agent` itself remains isolated from Extractor, ConflictPolicy, SQLAlchemy, and SQLite details.

---

## 11. Real DeepSeek Semantic Acceptance

Real-provider acceptance covered:

```text
explicit preference
current working context
completed episodic event
Relationship fact
uncertain / speculative statement
assistant-only claimed user fact
paraphrased identity stability
```

Accepted behavior:

```text
explicit preference
→ USER_PROFILE

current project / progress
→ WORKING_CONTEXT

completed event
→ EPISODIC

shared history with active Character
→ RELATIONSHIP + CHARACTER(active_character_id)

uncertain future Rust interest
→ no Candidate

fact asserted only by assistant
→ no Candidate
```

Canonical identity stability was verified after prompt refinement.

---

## 12. Real End-to-End Runtime Acceptance

Task 7F3 used:

```text
real DeepSeek
real SQLite
real Memory persistence
real Memory Retrieval
```

with an isolated temporary acceptance database.

### Enabled path

```text
real chat
→ response
→ automatic extraction
→ durable SQLite Memory
→ later Retrieval sees learned fact
```

Observed durable Memory:

```text
domain:
working_context

identity_key:
working_context.desktop_companion_agent.task7_f3.acceptance_codename

content:
The user's current Desktop Companion Agent Task7 F3 acceptance codename is cobalt-river-731.
```

Later Retrieval returned the same learned fact.

### Disabled path

```text
automatic_learning_enabled = false
→ chat still succeeds
→ Memory count does not increase
→ disabled marker is not persisted
→ previously stored Memory remains retrievable
```

Final acceptance marker:

```text
TASK7_F3_ACCEPTANCE_OK
```

The temporary acceptance database, WAL, and SHM files were removed after success.

---

## 13. Final Validation

Final owner-run validation:

```text
python -m pytest -q
→ 308 passed in 12.85s

python -m ruff check .
→ All checks passed

python -m mypy src
→ Success: no issues found in 96 source files

git diff --check
→ clean

git status --short
→ clean
```

Task 7 therefore satisfies its implementation and quality gates.

---

## 14. Final Task Status

```text
Task 7A  Scope correctness + learning contracts        ✅
Task 7B  Eligibility policy                            ✅
Task 7C  Existing Memory resolution                    ✅
Task 7D  Learning service + durable recording          ✅
Task 7E  Concrete LLM candidate extraction             ✅
Task 7F1 Agent runtime hook                             ✅
Task 7F2 Settings + Composition Root wiring             ✅
Task 7F3 Real runtime acceptance                        ✅
```

Final status:

```text
Task 7 — Controlled Automatic Memory Learning
COMPLETE
```

---

## 15. Final Confirmed Task 7 Commit Progression

```text
b64d4d76 feat(memory): establish automatic learning contracts
ebdc2ce0 feat(memory): add learning eligibility policy
ca351db  feat(memory): add logical memory identity keys
4fadc5a  feat(memory): persist logical memory identity keys
2d91b09  feat(memory): add logical memory identity lookup
f2d15ba  feat(memory): add existing memory resolver
066a9dd  feat(memory): add learning persistence primitives
843be83  feat(memory): add automatic memory learning service
39da336  feat(memory): close automatic learning lifecycle states
ff49fae  feat(memory): add llm memory candidate extractor
1cf2962  feat(memory): stabilize candidate identity extraction
709a0b5  feat(memory): integrate automatic learning with agent runtime
dc03908  feat(memory): wire automatic learning composition root
```

Task 7 completes at:

```text
dc03908
```

---

## 16. Explicit Non-Goals Preserved

Task 7 does not implement:

- Candidate review UI;
- Candidate SQLite persistence;
- Conversation / Session subsystem;
- embeddings;
- vector search;
- RAG framework;
- Mem0 integration;
- LangGraph integration;
- semantic retrieval ranking;
- automatic summarization/compression;
- Memory WebSocket management protocol;
- WPF Memory management UI;
- broad Memory runtime failure isolation;
- Permission;
- Tools;
- Situation / Attention / Behavior;
- Mood / affection / trust state;
- fictional-state persistence.

These remain outside Task 7 unless separately approved.

---

## 17. Deferred Runtime Lifecycle Follow-up

One pre-existing runtime lifecycle issue remains outside Task 7 scope:

```text
create_memory_engine()
→ caller owns AsyncEngine disposal
```

The current Composition Root creates the Memory engine, but explicit:

```python
await memory_engine.dispose()
```

is not yet part of the normal shutdown path.

This did not block Task 7 functional acceptance and should be handled as a separate runtime-lifecycle increment rather than mixed into the completed automatic-learning feature.

Desired ownership rule:

```text
Composition Root creates Memory engine
→ Composition Root disposes Memory engine
```

The follow-up should cover both normal shutdown and exceptional startup/runtime paths.

---

## 18. Documentation Authority

Task 7 remains governed by:

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

Task 7 does not add a new architecture decision requiring a separate ADR beyond the already accepted lifecycle, persistence, failure-boundary, and logical-identity decisions.

Current repository source remains the highest-priority engineering baseline.
