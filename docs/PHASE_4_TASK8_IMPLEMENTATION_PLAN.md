# Desktop Companion Agent — Phase 4 Task 8 Implementation Plan

Status: Completed
Phase: 4 — Memory System
Task: 8 — Memory Failure Isolation & Health Behavior
Completion checkpoint: `15b58b1 feat(memory): wire memory health runtime`
Current implementation status: Task 8A–8E completed and pushed
---

## 1. Task Goal

Task 8 makes Memory an optional runtime capability from the perspective of ordinary chat availability.

Accepted failure semantics:

```text
Retrieval failure
→ Memory degrades
→ empty PreparedMemoryContext
→ chat continues

Automatic-learning failure
→ Memory degrades
→ already-valid chat response still succeeds

Governance failure
→ operation fails truthfully
→ failure is observable through Memory health

Fatal non-Memory runtime failure
→ still propagates according to its owning subsystem
```

Task 8 implements ADR 0018 without moving Memory responsibility into Character, PromptContextComposer, EventBus, Provider, or future Behavior infrastructure.

---

## 2. Final Runtime Architecture

```text
MemoryHealthTracker
共享 Memory 健康状态
        │
        ├───────────────────────────────┐
        │                               │
        ↓                               ↓
ResilientMemoryRetriever       ResilientMemoryTurnLearner
检索故障隔离                    自动学习故障隔离
        ↓                               ↓
MemoryRetrievalService         AutomaticMemoryTurnLearner
记忆检索服务                    自动记忆学习
        │                               │
        └──────────────┬────────────────┘
                       ↓
              SQLiteMemoryRepository
              SQLite 持久化适配器
```

Governance currently has:

```text
HealthAwareMemoryGovernanceService
治理健康边界
        ↓
MemoryGovernanceService
治理业务逻辑
```

The governance wrapper is implemented and tested, but no live runtime consumer exists yet.

Task 8 intentionally does **not** instantiate an unused Governance service in `main.py` merely to complete a diagram. Task 9 will introduce the real WebSocket Governance consumer and should wire the same Memory health boundary there.

---

## 3. Accepted Boundaries

Task 8 preserves:

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

Capability categories:

```text
RETRIEVAL
AUTOMATIC_LEARNING
GOVERNANCE
```

Capability status:

```text
AVAILABLE
DEGRADED
UNAVAILABLE
```

Aggregate health:

```text
any UNAVAILABLE
→ UNAVAILABLE

else any DEGRADED
→ DEGRADED

else
→ AVAILABLE
```

Safe diagnostics may record:

```text
capability
status
last error type
```

They must not record:

```text
Memory content
full user text
full assistant text
full prompt
API secrets
raw SQL carrying factual content
```

---

## 5. Task Breakdown and Final Status

### Task 8A — Memory Health Contract

Status: Completed

Implemented:

- `MemoryCapability`;
- `MemoryHealthStatus`;
- immutable health snapshots;
- in-process `MemoryHealthTracker`;
- capability-local recovery.

Checkpoint:

```text
2831829 feat(memory): add memory health model
```

---

### Task 8B — Retrieval Fail-Open Boundary

Status: Completed

Implemented:

```text
MemoryRetriever failure
→ mark RETRIEVAL DEGRADED
→ safe warning log
→ empty PreparedMemoryContext
→ Agent continues to Provider
```

Successful retrieval marks the Retrieval capability AVAILABLE again.

Checkpoint:

```text
b8cea85 feat(memory): isolate memory retrieval failures
```

---

### Task 8C — Automatic-Learning Fail-Open Boundary

Status: Completed

Implemented:

```text
Provider response already exists
→ MemoryTurnLearner failure
→ mark AUTOMATIC_LEARNING DEGRADED
→ safe warning log
→ preserve provider response
```

Successful learning marks the Automatic Learning capability AVAILABLE again.

Checkpoint:

```text
494c536 feat(memory): isolate automatic learning failures
```

---

### Task 8D — Governance Fail-Closed + Health

Status: Completed

Implemented:

```text
Governance infrastructure failure
→ mark GOVERNANCE DEGRADED
→ safe warning log
→ re-raise failure
→ never report false success
```

Existing domain governance errors remain domain errors and are not rewritten into success.

Checkpoint:

```text
3c6672e feat(memory): track governance health failures
```

---

### Task 8E — Composition Root + Acceptance

Status: Completed

Implemented in `main.py`:

```text
create one MemoryHealthTracker
        ↓
wrap MemoryRetrievalService
with ResilientMemoryRetriever
        ↓
wrap AutomaticMemoryTurnLearner
with ResilientMemoryTurnLearner
        ↓
inject resilient boundaries into Agent
```

Important runtime invariant:

```text
Retrieval wrapper
and
Automatic Learning wrapper
share the same MemoryHealthTracker instance
```

When automatic learning is disabled:

```text
memory_learner = None
```

while Retrieval remains available through `ResilientMemoryRetriever`.

Governance runtime wiring is intentionally deferred until Task 9 introduces the real Governance protocol consumer.

Suggested checkpoint:

```text
feat(memory): wire memory health runtime
```

---

## 6. Error Catching Policy

Broad `Exception` catching is allowed only at explicit outer Memory capability boundaries where the architecture says:

```text
Memory capability failed
→ degrade safely
```

This applies to:

- resilient Retrieval;
- resilient Automatic Learning;
- health-aware Governance instrumentation.

Internal domain services continue to use specific validation/state errors.

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

Governance remains fail-closed.

Correct:

```text
repository mutation fails
→ governance operation fails
→ caller receives failure
→ health records degradation
```

Incorrect:

```text
repository mutation fails
→ warning only
→ fake success returned
```

Task 9 will later map Governance failures into stable Desktop-safe protocol errors.

---

## 9. Health Recovery Semantics

Recovery is capability-local:

```text
Retrieval succeeds
→ RETRIEVAL AVAILABLE

Automatic Learning may still be DEGRADED
```

No background health probe is introduced in Task 8.

---

## 10. Verification

Task 8E targeted integration validation:

```text
27 passed
```

Covered:

```text
test_main.py
test_memory_health.py
test_resilient_memory_retriever.py
test_resilient_memory_turn_learner.py
test_health_aware_memory_governance.py
```

Full Python regression:

```text
323 passed in 8.41s
```

Static / diff quality gates:

```text
Ruff
→ All checks passed

mypy
→ Success: no issues found in 104 source files

git diff --check
→ clean
```

Current Task 8E working tree before staging:

```text
M src/agent_core/main.py
M src/agent_core/tests/test_main.py
```

---

## 11. Completion Criteria

Task 8 implementation satisfies the intended behavior when:

1. Memory health distinguishes Retrieval, Automatic Learning, and Governance capability state.
2. Retrieval failure degrades to empty prepared context.
3. Retrieval failure does not prevent ordinary Provider chat.
4. Retrieval failure does not fabricate Memory context.
5. Automatic-learning failure does not invalidate an already successful chat response.
6. Automatic-learning failure remains observable.
7. Governance edit failure remains fail-closed.
8. Governance delete failure remains fail-closed.
9. Governance infrastructure failure becomes visible in Memory health.
10. Logs avoid sensitive Memory/conversation content.
11. Memory health remains independent from Agent/Provider health.
12. Existing Task 7 behavior remains intact while Memory is healthy.
13. One shared runtime health tracker is used by the live Retrieval and Automatic Learning boundaries.
14. Governance is not artificially instantiated without a real runtime consumer.
15. Targeted and full quality gates pass.
16. Final staged diff is reviewed before checkpoint commit.

Task 8 formally completed at checkpoint:

15b58b1 feat(memory): wire memory health runtime

---

## 12. Actual Task 8 Commit Progression

Confirmed commits:

```text
2831829 feat(memory): add memory health model
b8cea85 feat(memory): isolate memory retrieval failures
494c536 feat(memory): isolate automatic learning failures
3c6672e feat(memory): track governance health failures
15b58b1 feat(memory): wire memory health runtime
```

Task 8E completion checkpoint:

```text
15b58b1 feat(memory): wire memory health runtime
```

---

## 13. Explicit Non-Goals

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

## 14. Transition to Task 9

After Task 8 is checkpointed, Task 9 can assume:

```text
Memory Retrieval
→ safe fail-open runtime boundary

Automatic Learning
→ safe fail-open runtime boundary

Governance
→ fail-closed health-aware boundary exists

MemoryHealthTracker
→ capability-local health model exists
```

Task 9 will add the real Desktop-facing Governance consumer:

```text
WPF / Desktop
    ↓
WebSocket Memory Protocol
    ↓
HealthAwareMemoryGovernanceService
    ↓
MemoryGovernanceService
    ↓
SQLiteMemoryRepository
```

At that point Governance runtime wiring should use the same accepted health semantics rather than inventing a second health system.
