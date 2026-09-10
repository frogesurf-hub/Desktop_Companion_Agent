# ADR 0012 - Fail-Fast Event Bus Overload Admission to Avoid Re-entrant Publication Deadlock

Status: Accepted

Date: 2026-09-10

## Context

ADR 0011 originally required a bounded in-memory Event Bus whose publishers wait asynchronously when the queue is full. During Phase 2 / Task 2 working-code review, that rule was tested against a required long-term event pattern: a subscriber may publish a new fact derived from the Event it is currently handling.

With the Phase 2 single-dispatcher rule, the following circular wait is possible:

```text
queue capacity = N
current Event E1 is being handled
queue already contains N accepted Events

handler(E1)
    -> await publish(E-derived)
    -> waits for queue capacity

dispatcher
    -> cannot dequeue the next Event until handler(E1) settles

result: circular wait / deadlock
```

This is not a speculative edge case. Future Situation, Attention, Memory, and other runtime subscribers are expected to be able to produce new facts after handling an Event.

The architecture therefore needs bounded memory without making Event-handler progress depend on the same dispatcher freeing queue capacity.

## Decision

Phase 2 keeps a **bounded, in-process queue**, but queue-full publication is **fail-fast**.

The public publication contract is:

```text
await publish(event)

RUNNING + queue has capacity
    -> Event is admitted
    -> return normally

RUNNING + queue full
    -> raise EventBusFullError
    -> Event is not accepted

not RUNNING
    -> raise EventBusStateError
    -> Event is not accepted
```

`EventBusFullError` is a public Event System overload/non-admission error under the Event System error boundary.

The Event Bus does not automatically:

- wait for future capacity;
- retry;
- drop silently;
- coalesce Events;
- persist overflow;
- change Event priority.

Those policies depend on Event/domain semantics and remain responsibilities of future producer modules or later explicitly designed infrastructure.

### Admission atomicity in the Phase 2 asyncio model

The Phase 2 implementation must perform the `RUNNING` state validation and bounded queue admission without an `await`/suspension point between them.

Therefore, in the single Python event loop baseline:

- shutdown cannot interleave between the accepted-state check and successful `put_nowait`;
- an Event that is successfully inserted is accepted and must be included in graceful drain;
- a publication that observes a non-`RUNNING` state is rejected;
- a publication that encounters a full queue receives `EventBusFullError`.

No blocked-publisher shutdown race exists because overload publication does not wait.

## Rationale

- prevents re-entrant subscriber publication from deadlocking the single dispatcher;
- preserves the bounded-memory requirement for a long-running Companion runtime;
- makes overload explicit to the producer instead of silently losing Events;
- keeps Event Bus semantics domain-neutral: it reports non-admission but does not guess retry/coalescing/drop policy;
- simplifies lifecycle and shutdown semantics by removing blocked queue-capacity waiters;
- preserves `await publish(event)` as the stable async capability boundary even though a successful Phase 2 admission has no required suspension point;
- avoids introducing multiple dispatch workers, reserved queue slots, direct recursive dispatch, or other complexity solely to preserve blocking backpressure.

## Alternatives Considered

### Keep blocking backpressure

Rejected because subscriber re-entrant publication can form a circular wait with the single dispatcher.

### Special-case re-entrant publish and dispatch immediately

Rejected because it creates two publication semantics, weakens FIFO queue-admission ordering, and introduces recursive dispatch behavior.

### Reserve queue capacity for derived Events

Rejected because finite reservation only moves the exhaustion boundary and requires speculative classification of Event origin/importance.

### Add multiple dispatcher workers

Rejected for Phase 2 because it changes the accepted ordering/concurrency model and pulls forward throughput/partitioning design that is not currently required.

### Use an unbounded queue

Rejected because it removes the explicit memory bound required for a long-running runtime.

## Consequences

- producers must handle or consciously allow `EventBusFullError` according to their own semantics;
- queue capacity remains an operational configuration concern;
- EventBus tests must verify explicit queue-full rejection;
- EventBus tests must include a regression scenario showing that re-entrant publication cannot block waiting for the dispatcher;
- Task 3 no longer needs a blocked-publisher shutdown race implementation;
- future high-frequency Perception may still justify coalescing, sampling, dedicated queues, or partitions, but those require later design;
- ordinary subscriber failure isolation in Task 3 must not accidentally hide an overload policy decision: a business subscriber that cares about derived-event delivery should handle `EventBusFullError` explicitly.

## Scope of Supersession

This ADR **partially supersedes ADR 0011 only for queue-full publication behavior**.

The following ADR 0011 decisions remain Accepted:

- async in-process transient Event Bus;
- bounded queue;
- `await publish(event)` means successful queue admission, not subscriber completion;
- exact-type routing;
- queue-admission ordering;
- single dispatcher;
- concurrent sibling subscribers per Event;
- one Event settles before the next Event dispatch;
- ordinary subscriber failure isolation;
- cancellation semantics for dispatcher/subscriber lifecycle;
- explicit Event Bus lifecycle;
- static startup subscriptions;
- composition-root ownership;
- transient/non-persistent Event delivery.

## Explicit Non-Decisions

This ADR does not decide:

- producer retry policy;
- Event coalescing/sampling/drop policy;
- priority;
- overflow persistence;
- multiple workers;
- partitioned queues;
- per-Event-class capacities;
- adaptive queue sizing;
- future Perception throughput strategy.
