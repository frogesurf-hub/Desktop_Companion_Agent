# Phase 2 - Architecture Correction 001: Event Bus Queue-Full Admission

Status: **Accepted**

Date: 2026-09-10

Current implementation baseline: `31734de Establish Phase 2 runtime event contracts`

Affected design:

- `docs/PHASE_2_EVENT_SYSTEM_DESIGN.md`
- `docs/PHASE_2_TASK_PLAN.md`
- `docs/adr/0011-async-bounded-in-process-event-bus.md`

New decision record:

- `docs/adr/0012-fail-fast-event-bus-overload-admission.md`

## 1. Trigger

During Phase 2 / Task 2 working-code review, the initial Event Bus implementation draft passed targeted pytest, Ruff, and mypy, but architecture review of the concurrency behavior exposed a circular-wait risk that the existing tests did not cover.

The accepted ADR 0011 design said that a publisher waits asynchronously when the bounded queue is full. The Phase 2 dispatcher also processes one Event at a time and waits for the current Event's subscribers to settle before dequeuing the next Event.

A future subscriber is allowed to publish a new fact derived from the Event it is handling. Combining those rules can deadlock.

## 2. Failure Scenario

```text
queue capacity = 1

E1 is currently dispatching
E2 is already queued

subscriber(E1)
    -> await publish(E3)
    -> queue full
    -> waits for capacity

dispatcher
    -> waits for subscriber(E1) to return
    -> therefore cannot dequeue E2
    -> therefore cannot free capacity
```

The producer waits for the dispatcher, while the dispatcher waits for the producer. Neither can make progress.

## 3. Why This Matters to the Long-Term Architecture

Derived Event publication is part of the intended runtime model:

```text
Perception fact
    -> Situation subscriber
        -> SituationChanged fact
            -> Attention subscriber
                -> Attention state fact
```

Phase 2 must therefore support subscriber-to-EventPublisher use without a hidden deadlock condition.

## 4. Options Reviewed

### A. Keep blocking backpressure

Rejected. It preserves producer throttling but permits the circular wait above.

### B. Re-entrant direct dispatch

Rejected. It would create a second routing path, introduce recursive dispatch, and weaken queue-admission FIFO semantics.

### C. Reserved overflow capacity

Rejected. A finite reserve can still fill under nested publication and requires speculative Event classification.

### D. Multiple dispatcher workers

Rejected for Phase 2. It changes ordering/concurrency guarantees and advances throughput design without a demonstrated requirement.

### E. Fail-fast bounded admission

Accepted. Queue capacity remains bounded; overload becomes an explicit non-admission error; no producer waits for the same dispatcher that must free capacity.

## 5. Accepted Correction

```text
RUNNING + capacity available
    -> admit Event
    -> publish returns successfully

RUNNING + queue full
    -> raise EventBusFullError
    -> Event not accepted

NEW / CLOSING / CLOSED
    -> raise EventBusStateError
    -> Event not accepted
```

The Event Bus performs no automatic retry, coalescing, persistence, or silent drop.

## 6. Lifecycle Consequence

The previous "blocked publisher vs shutdown" race is removed from the Phase 2 model.

Publication does not wait for queue capacity. The implementation must perform state validation and `put_nowait` admission without an `await` between them. In the single asyncio event-loop baseline, shutdown cannot run between those two operations.

Only Events successfully admitted before `CLOSING` are drained.

## 7. Error Surface Consequence

The public Event System error boundary now requires:

```text
EventSystemError
├── EventBusStateError
└── EventBusFullError
```

`EventBusFullError` means overload/non-admission only. It is not a subscriber failure and does not imply any retry policy.

## 8. Test Correction

Task 2 targeted tests must replace blocking-backpressure assertions with:

- queue-full publish raises `EventBusFullError`;
- full-queue publication does not become accepted later by itself;
- exact-type routing remains unchanged;
- FIFO applies to successfully admitted Events;
- a subscriber publishing a derived Event while the queue is full receives explicit overload instead of blocking the dispatcher;
- no sleep-based timing dependency is required for overload semantics.

## 9. Scope Check

This correction does not introduce:

- Perception logic;
- Situation logic;
- Attention logic;
- retry policy;
- priority;
- Event persistence;
- multiple workers;
- Desktop bridge changes.

It changes only Event Bus queue-full admission semantics needed to keep the Phase 2 infrastructure safe for future runtime modules.

## 10. Development Breakpoint

```text
Phase 2 / Task 2

Task 1 commit                         ✅ 31734de
Task 2 implementation draft           ✅ uncommitted
Targeted pytest                       ✅ 19 passed on pre-correction draft
Targeted Ruff                         ✅
Targeted mypy                         ✅
Working architecture review           ⚠️ re-entrant publication deadlock found
Architecture Correction 001           ✅ Accepted
ADR 0012                              ✅ Accepted
Documentation synchronization         <- current
Documentation-only review / commit
Task 2 implementation correction
Re-run targeted verification
Task 2 staged review / commit
```
