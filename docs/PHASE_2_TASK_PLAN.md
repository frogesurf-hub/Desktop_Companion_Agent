# Phase 2 - Event System Implementation Task Plan

Status: **Accepted planning baseline - Task 1 complete; Task 2 architecture correction accepted, implementation revision pending**

Date: 2026-09-10

Current implementation baseline: `31734de Establish Phase 2 runtime event contracts`

Architecture inputs:

- `docs/PHASE_2_EVENT_SYSTEM_DESIGN.md`
- `docs/PHASE_2_ARCHITECTURE_REVIEW.md`
- `docs/adr/0010-events-are-facts-commands-remain-explicit-boundaries.md`
- `docs/adr/0011-async-bounded-in-process-event-bus.md`
- `docs/adr/0012-fail-fast-event-bus-overload-admission.md`
- `docs/PHASE_2_ARCHITECTURE_CORRECTION_001.md`

## 1. Implementation Rules

- Preserve the Phase 1 `WebSocketServer -> Agent -> LLMProvider` vertical slice.
- Do not implement future Character/Memory/Perception/Situation/Attention/Behavior/Permission/Tool business logic.
- Do not implement Desktop Event Bridge unless a real Phase 2 acceptance requirement appears.
- No new third-party dependency is expected for the Event System baseline.
- Each Task should produce one focused, reviewable Git commit.
- During each Task run only targeted pytest/Ruff/mypy relevant to the changed files.
- Full pytest/Ruff/mypy remain project-owner Phase-final acceptance gates.
- Do not commit before staged-diff review.

## 2. Task 1 - Runtime Event Contract Foundation

### Goal

Create the stable event-side public data/contracts without queue or dispatcher implementation.

### Scope

- dedicated `agent_core.events` package;
- immutable `RuntimeEvent` metadata foundation;
- UUID `event_id`;
- timezone-aware UTC `occurred_at`;
- non-empty logical string `source`;
- optional UUID `correlation_id`;
- optional UUID `causation_id`;
- narrow `EventPublisher` async capability;
- async subscriber handler typing/contracts needed by later Event Bus work;
- minimal Event System base/state error contract only if needed by the public API;
- deterministic test-only concrete Event types.

### Explicitly not in Task 1

- Event queue;
- dispatcher/background task;
- routing implementation;
- subscription mutation behavior;
- logging lifecycle;
- composition-root integration;
- Desktop bridge;
- future business Events.

### Targeted verification

- Event metadata/default creation;
- immutability;
- UTC normalization / naive datetime rejection;
- causal metadata preservation;
- public typing/import boundary;
- Ruff on touched Event/Test files;
- mypy on touched Event package/tests as supported by project configuration.

### Commit intent

`Establish Phase 2 runtime event contracts`

## 3. Task 2 - Event Bus Core Routing and Admission Control

### Goal

Implement the accepted publication, subscription, queue, and exact-type routing core.

### Architecture correction note

The original blocking backpressure design was rejected during Task 2 working-code review because a subscriber can deadlock the single dispatcher by awaiting publication into an already-full queue. ADR 0012 now governs queue-full behavior.

### Scope

- concrete Event Bus;
- positive bounded queue capacity supplied explicitly to construction;
- static `subscribe()` registration while `NEW`;
- exact-type routing;
- `start()` transition to `RUNNING`;
- private dispatcher task;
- `await publish(event)` queue-admission semantics;
- explicit `EventBusFullError` when the bounded queue has no immediate capacity;
- queue-admission-order dispatch;
- zero-subscriber Events complete normally;
- lifecycle/state error for invalid public use;
- `EventBusFullError` for explicit overload non-admission.

### Important concurrency requirement

Publication must not suspend while waiting for queue capacity. In the single-event-loop Phase 2 baseline, the `RUNNING` state check and non-blocking queue admission occur without an `await` between them. Queue-full publication fails explicitly with `EventBusFullError`.

This avoids a circular wait when a subscriber publishes a derived Event while the queue is already full and the dispatcher is waiting for the current subscriber set to settle.

### Targeted verification

- exact-type delivery;
- unrelated type non-delivery;
- static subscription state rules;
- queue acceptance semantics;
- explicit queue-full rejection with `EventBusFullError`;
- re-entrant subscriber publication does not deadlock when the queue is full;
- admission-order dispatch;
- invalid-state publication/registration behavior.

### Commit intent

`Implement Phase 2 event bus core`

## 4. Task 3 - Subscriber Concurrency, Failure Isolation, and Lifecycle Completion

### Goal

Make the Event Bus safe as a long-running async runtime service.

### Scope

- concurrent subscriber execution for one Event;
- ordinary exception isolation per subscriber;
- next Event begins only after current Event subscribers settle;
- cancellation remains distinct from ordinary failure;
- graceful `close()` drain;
- idempotent close semantics;
- forced cleanup on externally cancelled close;
- terminal cleanup if the private dispatcher ends unexpectedly;
- no orphan dispatcher/subscriber tasks.

### Explicitly not in Task 3

- universal handler timeout;
- retry;
- subscriber priority;
- dynamic unsubscribe;
- multiple dispatcher workers;
- restart/supervision policy.

### Targeted verification

- concurrent sibling handlers;
- one ordinary failure does not cancel siblings;
- later Events continue after ordinary handler failure;
- cancellation propagates correctly;
- `close()` drains accepted queue;
- publication after `CLOSING` begins is rejected by lifecycle state;
- queue-full publication is rejected immediately and never becomes accepted implicitly;
- repeated close behavior;
- close-from-NEW behavior;
- cleanup leaves no live Event Bus tasks.

### Commit intent

`Add event bus lifecycle and failure isolation`

## 5. Task 4 - Event Lifecycle Observability

### Goal

Make runtime Event flow diagnosable without leaking Event payloads.

### Scope

- lifecycle logging for bus start/close;
- Event accepted/dispatched/completed diagnostics;
- handler identity and duration where useful;
- safe ordinary handler-failure diagnostics;
- unexpected dispatcher termination diagnostics;
- no default `repr(event)` or payload dump.

### Targeted verification

- expected metadata appears in captured logs;
- event type/ID/source are traceable;
- handler failure is diagnosable;
- a known sensitive payload marker never appears in default Event System logs.

### Commit intent

`Add safe event lifecycle observability`

## 6. Task 5 - Composition Root Integration

### Goal

Give the Event Bus explicit runtime ownership without rewriting the stable Phase 1 request/response path.

### Scope

- construct Event Bus in Python composition root;
- configure queue capacity through the existing configuration approach;
- register only real Phase 2 infrastructure subscriptions if any are required; otherwise keep registration empty;
- start Event Bus in defined runtime order;
- close Event Bus in defined shutdown order;
- preserve Provider construction/lifecycle and existing WebSocket/Agent behavior.

### Configuration note

The exact initial queue-capacity default is an operational configuration value, not an architecture guarantee. It should be positive, documented, and adjustable through the existing Settings pattern. No new dependency is required.

### Targeted verification

- composition-root construction with deterministic fakes where needed;
- Event Bus lifecycle is owned exactly once;
- Provider close behavior remains protected;
- relevant existing Agent/Provider/WebSocket tests continue to pass where directly affected.

### Commit intent

`Integrate event bus into runtime composition`

## 7. Task 6 - Phase 2 Final Acceptance and Documentation

### Project-owner quality gate

Run manually:

```text
python -m pytest -q
python -m ruff check .
python -m mypy src
```

Run C# build only if C# source changed. Under the accepted Phase 2 scope, C# source is not expected to change.

### Manual runtime regression

Confirm the Phase 1 vertical slice still works:

```text
WPF -> WebSocket -> Python -> Agent -> DeepSeek -> WPF
```

No synthetic Desktop Event Bridge demo is required.

### Final documentation

Update implementation facts only after acceptance:

- `PROJECT_STATE.md`;
- `ROADMAP.md`;
- `ARCHITECTURE.md` event-vs-command wording;
- `docs/adr/README.md` with ADR 0010 and ADR 0011;
- final `docs/PHASE_2_CHECKPOINT.md`;
- any development documentation affected by actual commands/configuration.

### Final archive hygiene

Exclude:

- `.env`;
- API keys/secrets;
- caches;
- logs;
- build outputs not intentionally versioned;
- `.git` if the project-source archive convention continues to omit it.

## 8. Development Breakpoint

```text
Phase 2 - Event System

Context Recovery                    ✅
Formal Design                       ✅
Architecture Review                 ✅
ADR 0010 / ADR 0011                 ✅
Final Task Breakdown                ✅
Task 1 - Event Contract Foundation  ✅ `31734de`
Task 2 - Event Bus Core             <- architecture correction applied; implementation revision next
Task 3 - Lifecycle / Failure        pending
Task 4 - Observability              pending
Task 5 - Runtime Integration        pending
Task 6 - Final Acceptance           pending
Checkpoint                          pending
```
