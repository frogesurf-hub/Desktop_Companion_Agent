# Desktop Companion Agent — Phase 4 Task 8 Implementation Plan

Status: Active Implementation Baseline
Phase: 4 — Memory System
Task: 8 — Memory Failure Isolation & Health Behavior
Repository baseline reviewed: `dc03908 feat(memory): wire automatic learning composition root`

---

## 1. Task Goal

Task 8 makes Memory an optional runtime capability from the perspective of ordinary chat availability.

The accepted failure semantics are:

```text
Retrieval failure
→ Memory degrades
→ empty PreparedMemoryContext
→ chat continues

Automatic-learning failure
→ Memory degrades
→ failure remains observable
→ already-valid chat response still succeeds

Governance failure
→ operation fails truthfully
→ no false success

Fatal non-Memory runtime failure
→ still propagates according to its owning subsystem
```

Task 8 implements ADR 0018 without moving Memory responsibility into Character, PromptContextComposer, EventBus, Provider, or future Behavior infrastructure.

---

## 2. Existing Baseline

Task 7 completed the factual-memory loop:

```text
Conversation Turn
→ LLMMemoryCandidateExtractor
→ MemoryLearningPolicy
→ ExistingMemoryResolver
→ MemoryConflictPolicy / lifecycle handling
→ MemoryLearningService
→ SQLiteMemoryRepository
→ later Retrieval
```

Current runtime wiring:

```text
Agent
├─ MemoryRetriever
├─ MemoryTurnLearner | None
├─ LLMProvider
├─ PromptContextComposer
└─ Clock
```

Current weakness:

```text
MemoryRetriever raises
→ Agent chat path fails

MemoryTurnLearner raises
→ successful provider response is lost to caller

Governance repository raises
→ exception propagates
```

The third behavior is already directionally correct for fail-closed governance; Task 8 must preserve it while making failure observable through Memory health.

---

## 3. Accepted Boundaries

Task 8 must preserve:

```text
Runtime Availability != Memory Availability
Character != Memory
Real State != Fictional State
Memory Context != Permission
Event != Command
Prompt Composition != Memory Persistence
```

Task 8 does not redesign:

- Memory domains;
- logical identity;
- conflict policy;
- retention semantics;
- automatic-learning extraction;
- WebSocket governance protocol;
- WPF governance UI;
- Provider error semantics;
- EventBus semantics.

---

## 4. Memory Health Model

Task 8 introduces a minimal runtime-visible Memory health boundary.

### Capability categories

```text
RETRIEVAL
AUTOMATIC_LEARNING
GOVERNANCE
```

### Capability status

```text
AVAILABLE
DEGRADED
UNAVAILABLE
```

`DEGRADED` means a recoverable operation failure has occurred at that capability boundary.

`UNAVAILABLE` is reserved for a capability that is explicitly known to be unavailable. Task 8 does not infer global unavailability from every single exception.

### Aggregate health

Overall Memory health is derived:

```text
any UNAVAILABLE
→ UNAVAILABLE

else any DEGRADED
→ DEGRADED

else
→ AVAILABLE
```

This prevents one failed learning write from incorrectly declaring Retrieval unavailable.

### Safe diagnostics

Health may record:

```text
capability
status
last error type
```

Health must not record:

```text
Memory content
full user text
full prompt
API secrets
raw SQL with factual content
```

---

## 5. Task Breakdown

### Task 8A — Memory Health Contract

Goal:

- define capability/status enums;
- define immutable health snapshots;
- define mutable in-process health tracker;
- keep health independent from Agent and persistence implementation.

Files expected:

```text
src/agent_core/memory/health.py
src/agent_core/memory/__init__.py
src/agent_core/tests/test_memory_health.py
```

No runtime behavior changes yet.

---

### Task 8B — Retrieval Fail-Open Boundary

Goal:

```text
MemoryRetriever failure
→ mark RETRIEVAL DEGRADED
→ safe warning log
→ PreparedMemoryContext()
→ Agent continues to Provider
```

Preferred architecture:

```text
Agent
→ ResilientMemoryRetriever
→ existing MemoryRetriever
```

Agent should not learn SQLAlchemy exception types.

Success should mark the Retrieval capability AVAILABLE again.

Acceptance:

```text
repository/retrieval failure
→ provider still receives request
→ prompt contains no fabricated Memory
→ response succeeds
→ health shows Retrieval degraded
```

---

### Task 8C — Automatic-Learning Fail-Open Boundary

Goal:

```text
Provider response already exists
→ MemoryTurnLearner failure
→ mark AUTOMATIC_LEARNING DEGRADED
→ safe warning log
→ preserve provider response
```

Preferred architecture:

```text
Agent
→ ResilientMemoryTurnLearner
→ AutomaticMemoryTurnLearner
```

Agent should not own Memory exception classification.

Acceptance:

```text
learning extraction / resolution / write failure
→ chat response remains response
→ failure observable through health/logging
```

---

### Task 8D — Governance Fail-Closed + Health

Current Governance already propagates repository mutation failures.

Task 8 must preserve:

```text
edit/delete persistence failure
→ exception / failure result
→ never report success
```

Add a governance boundary or instrumentation layer that:

- records GOVERNANCE degradation;
- does not swallow failures;
- does not rewrite domain errors such as MemoryNotFoundError into success;
- keeps protocol-safe mapping deferred to Task 9.

Acceptance:

```text
edit failure
→ caller receives failure
→ health records Governance degradation

delete failure
→ caller receives failure
→ health records Governance degradation
```

---

### Task 8E — Composition Root + Acceptance

Wire one shared Memory health tracker into the Task 8 boundaries.

Target runtime:

```text
MemoryHealthTracker
        │
        ├─ resilient Retrieval
        ├─ resilient Automatic Learning
        └─ health-aware Governance
```

Task 8 runtime acceptance:

```text
Retrieval failure
→ chat succeeds
→ empty Memory context

Learning failure
→ provider response succeeds

Governance failure
→ operation fails truthfully

Memory health
→ distinguishable from healthy state
```

Task 8 completion also requires:

```text
targeted pytest
full pytest
Ruff
mypy
git diff --check
staged review
```

---

## 6. Error Catching Policy

Failure-isolation boundaries may catch broad `Exception` only at the explicit outer Memory capability boundary.

Reason:

- persistence adapters may surface SQLAlchemy / sqlite / filesystem exceptions;
- extraction may surface provider-neutral parsing or provider errors;
- Agent must not depend on every concrete Memory implementation error type.

The broad catch is allowed only where the architecture explicitly says:

```text
Memory capability failed
→ degrade safely
```

Internal domain services should continue to use specific validation/state errors.

Never catch:

```text
BaseException
KeyboardInterrupt
SystemExit
```

---

## 7. Logging Policy

Safe examples:

```text
Memory retrieval failed: OperationalError
Automatic Memory learning failed: MemoryCandidateExtractionError
Memory governance failed: IntegrityError
```

Do not log:

```text
candidate.content
revision.content
user_text
assistant_text
prompt body
API key
raw database row
```

---

## 8. Governance Semantics

Task 8 does not convert Governance into fail-open behavior.

Correct:

```text
repository.replace_active_revision raises
→ edit_memory does not return success
```

Incorrect:

```text
repository write fails
→ log warning
→ return fake edited Memory
```

Task 9 will later map these failures into stable Desktop-safe protocol errors.

---

## 9. Health Recovery Semantics

A successful operation at a capability boundary may mark that capability `AVAILABLE` again.

This recovery is capability-local:

```text
Retrieval succeeds
→ RETRIEVAL AVAILABLE

AUTOMATIC_LEARNING may still be DEGRADED
```

Aggregate health is derived from all capability states.

No background health probe is introduced in Task 8.

---

## 10. Explicit Non-Goals

Task 8 does not implement:

- automatic retries;
- database backup/restore;
- corruption repair;
- reconnect orchestration;
- WPF health dashboard;
- Memory WebSocket protocol;
- global runtime supervisor;
- Provider health;
- EventBus health;
- vector search;
- new Memory domains;
- new automatic-learning semantics.

The pre-existing `memory_engine.dispose()` runtime ownership issue remains a separate lifecycle follow-up and is not silently folded into Memory failure semantics.

---

## 11. Completion Criteria

Task 8 is complete when:

1. Memory health can distinguish Retrieval, Automatic Learning, and Governance capability state.
2. Retrieval failure degrades to empty prepared context.
3. Retrieval failure does not prevent ordinary Provider chat.
4. Retrieval failure does not fabricate Memory context.
5. Automatic-learning failure does not invalidate an already successful chat response.
6. Automatic-learning failure remains observable.
7. Governance edit failure remains fail-closed.
8. Governance delete failure remains fail-closed.
9. Governance failure becomes visible in Memory health.
10. Logs avoid sensitive Memory/conversation content.
11. Memory health is independent from Agent/Provider health.
12. Existing Task 7 behavior remains intact when Memory is healthy.
13. Targeted and full quality gates pass.

---

## 12. Planned Checkpoints

Suggested reviewable commits:

```text
Task 8A
feat(memory): add memory health model

Task 8B
feat(memory): isolate memory retrieval failures

Task 8C
feat(memory): isolate automatic learning failures

Task 8D
feat(memory): track governance health failures

Task 8E
feat(memory): wire memory health runtime
```

Exact checkpoint messages may change to match the final implementation.
