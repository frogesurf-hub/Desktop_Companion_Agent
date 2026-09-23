# Desktop Companion Agent — Phase 4 Task 11 Runtime Acceptance Plan

Status: Completed
Phase: 4 — Memory System
Task: 11 — Phase 4 Runtime Acceptance

Repository baseline reviewed:
`3b9aa2b docs(memory): close task 10 acceptance`

Task 11 implementation checkpoint reviewed:
`eb57eb4 test(memory): add integrated runtime lifecycle acceptance`

Current acceptance status:
Task 11A–11D completed and accepted

---

## 1. Task Goal

Task 11 proves that Phase 4 works as one coherent runtime capability rather than as a collection of individually implemented modules.

The acceptance target is:

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

Task 11 is primarily validation and integration acceptance.

It must not introduce new product behavior unless acceptance exposes a real defect that belongs to an earlier Task boundary.

---

## 2. System Position

Current Phase 4 dependency chain:

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
WebSocket Memory Governance
记忆治理协议
        ↓
Task 10
WPF Memory Management UI
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

Task 11 does not primarily add a new runtime layer.

It changes the project state from:

```text
Phase 4 parts implemented
```

to:

```text
Phase 4 Memory System verified as one integrated runtime capability
```

---

## 3. Current Repository Reality

Task 11 began from:

```text
3b9aa2b docs(memory): close task 10 acceptance
```

Task 11 acceptance implementation reached:

```text
5d47e1b docs(memory): add task 11 runtime acceptance plan
eb57eb4 test(memory): add integrated runtime lifecycle acceptance
```

Task 10 closure already records:

```text
real WPF Memory governance acceptance
354 passed
Ruff clean
mypy clean
Desktop build succeeded
fresh Runtime DB schema bootstrap accepted
```

Task 11 therefore should not blindly repeat every Task 9/10 acceptance step.

Instead, it should:

```text
reuse strong existing evidence
+
fill cross-module acceptance gaps
+
run final full regression and real-runtime checks
```

---

## 4. Existing Automated Evidence

The current repository already contains strong focused coverage.

### Automatic learning

Relevant tests include:

```text
src/agent_core/tests/test_memory_learning_llm_extractor.py
src/agent_core/tests/test_memory_learning_policy.py
src/agent_core/tests/test_memory_turn_learner.py
src/agent_core/tests/test_memory_learning_service.py
```

Current coverage includes:

```text
supported candidate extraction
empty extraction
invalid structured output rejection
model authority-field rejection

eligible automatic explicit facts
domain/scope validation
active Character relationship validation

turn candidate processing
empty extraction handling

new Memory creation
duplicate handling
authority conflict behavior
expired Memory reactivation
deleted Memory non-resurrection
```

### Retrieval and prompt composition

Relevant tests include:

```text
src/agent_core/tests/test_memory_retrieval_scope.py
src/agent_core/tests/test_agent.py
src/agent_core/tests/test_context_composer.py
```

Current evidence includes:

```text
USER_PROFILE retrieval
active Character RELATIONSHIP isolation

Agent receives PreparedMemoryContext
→ PromptContextComposer
→ provider request contains [Memory Context]
```

Task 11B closed the remaining integration gap with:

```text
src/agent_core/tests/test_memory_runtime_acceptance.py
```

The accepted deterministic path is now:

```text
SQLite
→ persistence runtime restart
→ MemoryRetrievalService
→ Agent
→ PromptContextComposer
→ FakeLLMProvider actual request
→ Governance edit
→ corrected retrieval
→ Governance delete
→ deleted fact absent from retrieval and provider prompt
```

### Governance and persistence

Relevant tests include:

```text
src/agent_core/tests/test_memory_governance.py
src/agent_core/tests/test_memory_governance_integration.py
src/agent_core/tests/test_memory_sqlite_repository.py
src/agent_core/tests/test_memory_websocket_integration.py
src/agent_core/tests/test_memory_migrations.py
```

Current evidence includes:

```text
SQLite round-trip
revision replacement
transaction rollback
delete tombstone semantics
deleted content removal
history redaction
WebSocket list / inspect / edit / delete / history
safe protocol failures
runtime DB schema bootstrap
migration idempotence
```

### Failure isolation and health

Relevant tests include:

```text
src/agent_core/tests/test_resilient_memory_retriever.py
src/agent_core/tests/test_resilient_memory_turn_learner.py
src/agent_core/tests/test_health_aware_memory_governance.py
src/agent_core/tests/test_memory_websocket_integration.py
```

Current evidence includes:

```text
retrieval failure
→ empty PreparedMemoryContext
→ chat survives
→ health degraded

automatic-learning failure
→ chat response survives
→ health degraded

governance failure
→ operation fails truthfully
→ health degraded

WebSocket infrastructure failure
→ safe MEMORY_OPERATION_FAILED
→ sensitive internal failure text not exposed
```

### Runtime composition

Relevant test:

```text
src/agent_core/tests/test_main.py
```

Current evidence includes:

```text
Memory DB schema upgrade occurs before runtime repository use
shared MemoryHealthTracker wiring
automatic_learning_enabled = false
→ memory learner omitted
→ resilient retriever remains wired

runtime cleanup
EventBus lifecycle
Provider cleanup
```

---

## 5. Acceptance Matrix — Repository Reality Review

### A. Automatic Learning

Required:

```text
explicit eligible fact
→ candidate
→ accepted
→ durable Memory

unsupported inference
→ not persisted
```

Current status:

```text
explicit learning path
→ strong automated component coverage
→ real Task 10 runtime acceptance already proved one explicit fact persisted

unsupported inference
→ extraction can return no candidates
→ but real-runtime non-explicit input has not been explicitly accepted
```

Task 11 action:

```text
REAL RUNTIME REQUIRED

Send one deliberately non-memory-worthy / non-explicit message.
Confirm no new Memory is created.
```

---

### B. Persistence Across Restart

Required:

```text
Memory exists
→ Core stops
→ Core restarts
→ same Memory still exists
```

Current status:

```text
SQLite persistence is strongly tested.
Task 10 restarted WPF while Core remained alive.

A real Core restart persistence acceptance is still required.
```

Task 11 action:

```text
REAL RUNTIME REQUIRED
```

---

### C. Retrieval and Prompt Use

Required:

```text
stored Memory
→ later request
→ Retrieval
→ PreparedMemoryContext
→ PromptContextComposer
→ Provider request uses remembered fact
```

Current status:

```text
Retrieval is tested.
Agent → Composer → Provider request Memory injection is tested.

The complete SQLite → Retrieval → Agent → Provider-request path
should be accepted as one integrated path.
```

Task 11 action:

```text
ADD ONE HIGH-VALUE INTEGRATION ACCEPTANCE TEST

and

REAL RUNTIME CONFIRMATION
```

The automated test should use a deterministic fake Provider and assert the actual provider request contains the durable Memory content.

This avoids using model output alone as proof that Memory reached the prompt.

---

### D. Revision and Correction

Required:

```text
old ACTIVE revision
→ correction/edit
→ old SUPERSEDED
→ new ACTIVE
→ Retrieval uses new content
```

Current status:

```text
revision lifecycle is strongly covered
WebSocket edit/history acceptance is already present

retrieval-after-edit should be part of the Task 11 integrated lifecycle test
```

Task 11 action:

```text
COVER IN THE SAME INTEGRATION ACCEPTANCE TEST
```

---

### E. Delete Semantics

Required:

```text
delete commits
→ deleted fact no longer retrieved
→ normal governance no longer exposes factual content
```

Current status:

```text
STRONGLY COVERED

WebSocket integration already proves:
delete tombstone
content = None
history no longer exposes old factual text
final list excludes deleted Memory
retrieval no longer returns deleted content

Task 10 also accepted WPF delete flow.
```

Task 11 action:

```text
REUSE EXISTING EVIDENCE

Optionally include delete as the final step of the integrated lifecycle test.
No separate manual repetition is required unless another Task 11 step exposes a defect.
```

---

### F. Domain / Scope Isolation

Required:

```text
USER_PROFILE
→ global

RELATIONSHIP
→ active Character only
```

Current status:

```text
STRONGLY COVERED

test_memory_retrieval_scope.py
proves other Character relationship content is excluded.

Learning policy and SQLite identity tests also enforce scope rules.
```

Task 11 action:

```text
REUSE AUTOMATED EVIDENCE
```

---

### G. Automatic Learning Disabled

Required:

```text
automatic_learning_enabled = false
→ chat works
→ Retrieval works
→ Governance works
→ no new automatic Memory
```

Current status:

```text
test_main.py proves learner wiring is disabled
while ResilientMemoryRetriever remains present.

The full runtime behavior has not yet been accepted as one scenario.
```

Task 11 action:

```text
REAL RUNTIME REQUIRED

Use a temporary database and configuration override.
Do not alter the normal development Memory DB.
```

---

### H. Failure Isolation

Required:

```text
retrieval failure
→ chat works

learning write failure
→ chat response remains valid

governance failure
→ operation reports failure

unavailable
!=
empty
```

Current status:

```text
STRONGLY COVERED BY TARGETED AUTOMATED TESTS

Task 10 also encountered a real zero-schema Memory failure,
where chat remained available and Memory UI reported failure.
That defect is now fixed by runtime schema bootstrap.
```

Task 11 action:

```text
REUSE AUTOMATED + HISTORICAL REAL-RUNTIME EVIDENCE

Do not deliberately corrupt the primary development DB only to repeat a failure.
```

---

### I. WebSocket Governance

Required:

```text
list
inspect
edit
delete
history
safe errors
```

Current status:

```text
STRONGLY COVERED

src/agent_core/tests/test_memory_websocket_integration.py

Task 9 final acceptance also covered the protocol boundary.
```

Task 11 action:

```text
REUSE EXISTING EVIDENCE
```

---

### J. WPF Governance UI

Required:

```text
list
inspect
edit
history
delete
committed UI state
```

Current status:

```text
REAL TASK 10 ACCEPTANCE PASSED
```

Task 11 action:

```text
REUSE TASK 10 ACCEPTANCE RECORD

No need to repeat the entire UI script unless Task 11 changes Desktop code.
```

---

### K. Regression

Required:

```text
WPF → WebSocket → Agent → Provider → WPF

Character behavior
Temporal factual context
Provider-safe errors
EventBus lifecycle
Sensitive-log rules
```

Current status:

```text
automated regression coverage exists across earlier phases
```

Task 11 action:

```text
FULL QUALITY GATE
+
one normal real WPF chat round-trip
+
final runtime log-safety inspection
```

---

## 6. Task 11 Implementation Strategy

Task 11 should be split into four acceptance checkpoints.

### Task 11A — Acceptance Baseline

Goal:

```text
freeze current HEAD
map A–K to evidence
identify only real gaps
```

Output:

```text
this acceptance plan
```

No product code change.

---

### Task 11B — Integrated Memory Lifecycle Acceptance Test

Add one focused integration test.

Suggested file:

```text
src/agent_core/tests/test_memory_runtime_acceptance.py
```

Target path:

```text
temporary SQLite DB
→ schema upgrade
→ real SQLiteMemoryRepository
→ durable Memory
→ dispose/recreate persistence runtime
→ real MemoryRetrievalService
→ real Agent
→ real PromptContextComposer
→ FakeLLMProvider
→ inspect actual provider request
→ governance correction
→ retrieval uses corrected value
→ governance delete
→ retrieval no longer contains deleted value
```

This test must not:

```text
call the real external LLM
depend on WPF
duplicate every lower-level unit test
introduce new product behavior
```

Its job is to connect already-implemented boundaries.

---

### Task 11C — Real Runtime Acceptance

Use the actual Python Core and WPF Desktop.

Use a dedicated temporary acceptance DB.

Recommended environment override:

```text
DCA_MEMORY_DATABASE_PATH=data/task11_acceptance.db
```

Acceptance scenario:

```text
1. Start Core + WPF
2. Connect
3. Send explicit durable user fact
4. Confirm Memory appears
5. Stop Core completely
6. Restart Core
7. Reconnect WPF
8. Confirm Memory still exists
9. Ask a later question requiring the remembered fact
10. Confirm response uses the remembered fact
11. Send one non-explicit / non-memory-worthy message
12. Confirm no new Memory entry is created
13. Edit the remembered fact
14. Ask again
15. Confirm corrected fact is used
16. Delete the Memory
17. Ask again
18. Confirm deleted fact is no longer available from Memory
```

Then run a second isolated scenario:

```text
automatic_learning_enabled = false

→ chat works
→ existing Memory retrieval works
→ Memory governance works
→ new explicit fact does not create automatic Memory
```

Use a temporary DB/configuration override.

Do not modify the normal project Memory database for acceptance-only configuration cases.

---

## 7. How Task 11 Proves Prompt Use

Model output alone is not sufficient proof that Memory reached the prompt.

A model might answer from:

```text
current user message
model prior knowledge
coincidental inference
```

Therefore Task 11 uses two complementary proofs.

### Deterministic automated proof

```text
SQLite Memory
→ real Retrieval
→ Agent
→ PromptContextComposer
→ FakeLLMProvider.requests[0]
→ assert remembered content exists in system prompt
```

This proves actual runtime context flow.

### Real product proof

```text
persisted Memory
→ Core restart
→ later WPF conversation
→ observed response uses the fact
```

This proves the user-facing behavior.

Both are required because they prove different things.

---

## 8. Failure Handling Rule

If an acceptance step fails:

```text
identify owning boundary
→ classify failure
→ return to owning Task/boundary
→ fix defect
→ rerun affected acceptance
```

Failure classes:

```text
Implementation defect
Contract mismatch
Test defect
Environment/configuration issue
External Provider issue
```

Task 11 must not hide or weaken an acceptance criterion to obtain a green result.

---

## 9. Final Quality Gates

After Task 11 acceptance changes:

```text
python -m pytest -q
python -m ruff check .
python -m mypy src

dotnet build   src/Desktop/DesktopCompanion.Desktop/DesktopCompanion.Desktop.slnx

git diff --check
git status --short
```

Also verify:

```text
real Core startup
real WPF chat
Memory lifecycle acceptance
automatic-learning-disabled acceptance
runtime log-safety review
working tree state
```

Report actual test counts.

Do not predeclare an expected final pytest count.

---

## 10. Log-Safety Inspection

Inspect the acceptance runtime logs for accidental exposure of:

```text
API key
Authorization header
complete user prompt
complete model response
raw Provider response body
reasoning content
full Memory payloads where not required
SQLite exception internals presented to Desktop
```

Metadata-oriented operational logging is acceptable.

User-visible Memory content inside the explicitly opened Memory management UI is expected behavior and is not a logging leak.

---

## 11. Confirmed Task 11 Checkpoints

```text
Task 11A
5d47e1b docs(memory): add task 11 runtime acceptance plan

Task 11B
eb57eb4 test(memory): add integrated runtime lifecycle acceptance

Task 11C
manual real-runtime acceptance
(no product source commit required)

Task 11D
this documentation closure checkpoint
```

---

## 12. Task 11 Completion Criteria

Task 11 is complete when all of the following are true:

1. Automatic explicit learning is accepted end-to-end.
2. Non-explicit / unsupported input is shown not to create Memory.
3. Durable Memory survives a real Core restart.
4. SQLite Memory is proven to reach the actual provider request context.
5. User-facing runtime behavior can use the persisted fact after restart.
6. A correction creates the expected new active state.
7. Retrieval uses the corrected value rather than the superseded value.
8. Deleted content is no longer retrieved.
9. Relationship Memory remains active-Character scoped.
10. Automatic learning can be disabled without disabling chat, retrieval, or governance.
11. Retrieval failure remains fail-open for chat.
12. Automatic-learning failure remains fail-open for chat.
13. Governance failure remains fail-closed and truthful.
14. WebSocket governance acceptance remains green.
15. WPF governance acceptance remains valid.
16. Earlier Character / Temporal / Provider / EventBus behavior remains green.
17. Runtime logs pass the sensitive-data inspection.
18. Full Python quality gates pass.
19. Desktop build passes.
20. Repository acceptance state is documented and checkpointed.

All 20 completion criteria were accepted by automated evidence,
real Runtime acceptance, final quality gates, or previously accepted
Task 9/10 evidence explicitly reused by this plan.

---

## 13. Capability Delta

Before Task 11:

```text
Phase 4 components are implemented
and individually accepted
```

After Task 11:

```text
Phase 4 Memory System is demonstrated as a coherent,
restart-safe, governable, failure-isolated runtime capability
```

That accepted state becomes the input to Task 12 final documentation and Phase 4 closure.

---

## 14. Actual Task 11B Integrated Acceptance Result

Task 11B added:

```text
src/agent_core/tests/test_memory_runtime_acceptance.py
```

Targeted validation result:

```text
pytest
→ 1 passed

Ruff
→ All checks passed

mypy
→ Success: no issues found in 1 source file
```

The test deterministically proves:

```text
temporary SQLite DB
→ schema upgrade
→ Memory persisted
→ first engine disposed
→ second engine / repository created
→ same Memory recovered
→ real MemoryRetrievalService
→ real Agent
→ real PromptContextComposer
→ FakeLLMProvider actual request contains Memory
→ governance edit
→ old revision SUPERSEDED
→ corrected revision ACTIVE
→ corrected value reaches provider request
→ governance delete
→ deleted content removed
→ Retrieval empty
→ provider prompt no longer contains Memory context
```

This is a persistence-runtime restart boundary, not a substitute for
the real Core process restart accepted in Task 11C.

---

## 15. Actual Task 11C Real Runtime Acceptance

Task 11C used a dedicated temporary database:

```text
data/task11_acceptance.db
```

The primary development Memory database was not used for acceptance-only state.

### 15.1 Run A — Automatic Learning

A fresh Runtime started with:

```text
DCA_MEMORY_DATABASE_PATH=data/task11_acceptance.db
DCA_AUTOMATIC_LEARNING_ENABLED=true
```

The Runtime automatically upgraded the fresh database through:

```text
0001_memory
→ 0002_identity_key
→ 0003_identity_unique
```

The WPF client connected successfully.

The explicit test fact:

```text
Task11 acceptance code = ORBIT-4729
```

was learned as:

```text
domain = working_context
scope = global_user
source = automatic_explicit_fact
lifecycle = active
```

Accepted real path:

```text
WPF
→ WebSocket
→ Agent
→ DeepSeek
→ automatic candidate extraction
→ learning eligibility / persistence
→ SQLite
→ governance
→ WPF Memory UI
```

### 15.2 Run B — Real Core Restart and Retrieval

The Python Core process was fully stopped and a new Python Runtime
was started against the same `task11_acceptance.db`.

After reconnect, the `ORBIT-4729` Memory remained present.

A later user question did not include the answer, and the real Agent
returned `ORBIT-4729`.

Together with Task 11B deterministic provider-request inspection, this accepts:

```text
durable SQLite Memory
→ Core process restart
→ Retrieval
→ PreparedMemoryContext
→ PromptContextComposer
→ real Provider
→ WPF response
```

### 15.3 Run C — Non-Explicit Input and Correction

A normal knowledge question about a binary tree produced a normal response.

After Memory Refresh:

```text
Memory count unchanged
→ no new durable Memory
```

The existing Memory was then edited through WPF:

```text
Revision 1
ORBIT-4729
→ SUPERSEDED

Revision 2
NOVA-8306
→ ACTIVE
→ source = user_edit
```

A later real chat request returned `NOVA-8306`.

### 15.4 Run D — Automatic Learning Disabled

The same Runtime database was restarted with:

```text
DCA_AUTOMATIC_LEARNING_ENABLED=false
```

Existing Memory remained retrievable and ordinary chat remained available.

A new explicit-looking fact:

```text
Task11 second acceptance marker = NEBULA-1942
```

did not create a new Memory entry.

Governance edit remained functional:

```text
Revision 1
ORBIT-4729
→ SUPERSEDED

Revision 2
NOVA-8306
→ SUPERSEDED

Revision 3
AURORA-2604
→ ACTIVE
→ source = user_edit
```

The real Agent returned `AURORA-2604`.

Finally, the Memory was deleted through WPF. A later request explicitly
constrained to currently available Memory reported that no Task11
acceptance-code Memory was available.

This user-facing result is consistent with the deterministic Task 11B proof
that deleted content no longer reaches retrieval or the provider prompt.

---

## 16. Runtime Incidents Observed During Acceptance

Two external network interruptions occurred while using a mobile hotspot.

The Desktop received the existing safe Provider error:

```text
AI provider is temporarily unavailable.
```

After network recovery, normal chat resumed.

Classification:

```text
External Provider / Network Environment Issue
```

This was not classified as a Memory implementation defect.

It also reconfirmed that Provider connectivity failures remain mapped to
safe user-facing protocol errors.

An abrupt WPF / WebSocket shutdown also produced the already-known
missing-close-handshake message. This remains known shutdown-hardening debt
and did not invalidate Memory persistence or acceptance.

During one restart attempt, the Desktop `.csproj` again contained accidental
local trailing content after the XML root and failed with `MSB4025`.
The tracked file was restored from Git and the Desktop build passed.
No Task 11 product source change was required.

---

## 17. Final Quality Gates

Observed final results:

```text
Full Python regression
→ 355 passed in 10.03s

Ruff
→ All checks passed

mypy
→ Success: no issues found in 111 source files

Desktop
→ dotnet build DesktopCompanion.Desktop.slnx
→ succeeded

git diff --check
→ clean

git status --short
→ clean
```

The acceptance-only environment variables were removed after the runtime test.

The temporary database:

```text
data/task11_acceptance.db
```

was removed after acceptance.

Final Git status remained clean before documentation closure.

---

## 18. Final Log-Safety Acceptance

The runtime log was searched for all Task 11 marker values:

```text
ORBIT-4729
NOVA-8306
AURORA-2604
NEBULA-1942
```

Result:

```text
no matches
```

A broad search for `Authorization` returned historical HTTP status lines such as:

```text
HTTP/1.1 401 Authorization Required
```

These were HTTP status descriptions, not Authorization request headers
or credentials.

A stricter search for:

```text
Authorization\s*:
Bearer <token-like value>
api[_-]?key[:=]
reasoning_content
```

returned:

```text
no matches
```

A separate search for:

```text
raw response
response body
request body
system prompt
user prompt
```

also returned:

```text
no matches
```

Task 11 therefore accepts that the inspected runtime logs did not expose:

```text
Task 11 factual Memory contents
Authorization headers
Bearer credentials
API keys
reasoning content
raw request/response bodies
system prompts
user prompts
```

---

## 19. Final Acceptance Matrix

```text
A  Automatic Learning                 ACCEPTED
B  Persistence Across Core Restart    ACCEPTED
C  Retrieval + Prompt Use             ACCEPTED
D  Revision / Correction              ACCEPTED
E  Delete Semantics                   ACCEPTED
F  Domain / Scope Isolation           ACCEPTED
G  Automatic Learning Disabled        ACCEPTED
H  Failure Isolation                  ACCEPTED
I  WebSocket Governance               ACCEPTED
J  WPF Governance UI                  ACCEPTED
K  Regression                         ACCEPTED
```

Evidence combines:

```text
Task 7–10 targeted automated tests
Task 9 WebSocket acceptance
Task 10 real WPF acceptance
Task 11B deterministic lifecycle integration
Task 11C real Core / WPF / Provider runtime acceptance
Task 11 final quality gates
Task 11 log-safety inspection
```

No unresolved Phase 4 Memory defect was found during final Task 11 acceptance.

---

## 20. Task 11 Closure

Task 11 changes the project state from:

```text
Phase 4 Memory components implemented and separately accepted
```

to:

```text
Phase 4 Memory System accepted as a coherent,
restart-safe, governable, failure-isolated runtime capability
```

Task 12 may now treat the Phase 4 runtime behavior as accepted baseline
and proceed with final Phase 4 documentation, state synchronization,
checkpoint creation, and transition context.
