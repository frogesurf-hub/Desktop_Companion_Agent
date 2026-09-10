# ADR 0011 - Async Bounded In-Process Event Bus for Phase 2

Status: Accepted

Date: Phase 2 design baseline

Amendment: **Queue-full waiting/backpressure semantics are superseded by ADR 0012. All other decisions in this ADR remain Accepted.**

## Context

Phase 2 must provide a runtime Event System for a future long-running desktop Companion.

The system needs to decouple Event producers from Event consumers without introducing an external broker, persistent Event Store, or later-phase business logic.

The runtime is already asynchronous Python. Future Event producers may include high-frequency or I/O-adjacent systems such as Perception, while consumers may include Situation, Attention, Memory, observability, Avatar, and other optional subsystems.

The Event System therefore needs explicit decisions for publication, queueing, routing, ordering, concurrency, subscriber failure, cancellation, and shutdown.

## Decision

Phase 2 uses an **async, bounded, in-process, transient Event Bus**.

### Publication

```text
await publish(event)
```

means the Event has been successfully admitted to the Event Bus queue.

It does not mean subscribers have started, completed, or succeeded.

Publishing is accepted only while the Event Bus is `RUNNING`.

### Queue and backpressure

> **Historical note:** The original paragraph below specified waiting asynchronously for queue space. That queue-full behavior was found during Task 2 working-code review to permit a re-entrant publication deadlock. ADR 0012 supersedes only that queue-full waiting behavior.

The Event Bus uses a bounded in-memory queue.

When capacity is exhausted, publishers wait asynchronously for queue space. Phase 2 does not silently drop or coalesce Events.

If shutdown begins while a publisher is waiting and the Event has not yet been admitted, that publication is rejected rather than entering the queue after the shutdown boundary.

Cancellation while waiting propagates as cancellation.

### Routing

Routing uses exact concrete Runtime Event type.

Phase 2 has no wildcard/topic-pattern routing, inheritance routing, subscriber priority, or predicate routing.

### Ordering

Events are dispatched in successful queue-admission order.

The Phase 2 Event Bus uses one dispatcher. There is no stronger ordering claim for producers racing concurrently before queue admission.

### Subscriber execution

Subscribers for one Event execute concurrently.

The Event Bus waits for all subscribers for the current Event to settle before dispatching the next queued Event.

Subscribers must not depend on registration/completion order relative to sibling subscribers.

### Failure isolation

Ordinary subscriber exceptions are isolated and safely logged. They do not cancel sibling subscribers, terminate the Event Bus, or propagate back to the already-completed publisher.

`asyncio.CancelledError` is not treated as an ordinary subscriber failure.

Cancellation of Event Bus dispatch cancels in-flight subscriber work and propagates through the lifecycle boundary.

Phase 2 defines no universal subscriber timeout.

### Lifecycle

The Event Bus states are:

```text
NEW -> RUNNING -> CLOSING -> CLOSED
```

`start()` is valid only in `NEW` and the Event Bus is not restartable.

Subscriptions are static and may be registered only in `NEW`.

Normal `close()` is idempotent for callers:

- closing from `NEW` reaches `CLOSED` immediately;
- closing from `RUNNING` rejects new Event acceptance and drains already accepted Events;
- calls made while `CLOSING` wait for the same close operation;
- closing an already `CLOSED` bus is a no-op.

If graceful close is externally cancelled, forced cancellation may stop in-flight dispatch; cancellation must propagate and cleanup must not leave orphan tasks.

### Ownership

The concrete Event Bus is created, started, and closed by the runtime composition root.

It is not a global singleton.

Future producer modules should normally depend on a narrow EventPublisher capability rather than the full Event Bus lifecycle/subscription surface.

### Persistence

The Event Bus is transient.

Phase 2 provides no Event Store, replay, durable queue, crash recovery, exactly-once/at-least-once guarantee, or distributed broker.

## Rationale

- async operation matches the existing Python runtime;
- queued publication reduces direct temporal coupling between producer and subscriber execution;
- bounded capacity prevents unbounded memory growth in a long-running process;
- backpressure exposes overload without guessing business-specific drop rules;
- exact-type routing is predictable and statically analyzable;
- a single dispatcher gives a deterministic Phase 2 ordering baseline;
- concurrent sibling subscribers preserve independence without requiring hidden priority;
- failure isolation prevents one optional subsystem from stopping unrelated runtime components;
- explicit lifecycle prevents leaked background tasks and ambiguous shutdown behavior;
- process-local transient infrastructure satisfies the current Phase without pulling in persistence/distributed-system complexity.

## Consequences

- the Event Bus owns a private dispatcher task;
- Event producers are not synchronously coupled to handler completion;
- Event Bus shutdown must coordinate queue admission and drain semantics correctly;
- handler failure observability is required because failures do not return to publishers;
- queue capacity becomes an operational configuration concern;
- high-throughput future Perception workloads may later justify coalescing, partitions, or multiple workers;
- dynamic module loading would require a later subscription-lifetime extension;
- cross-process Desktop notification requires an explicit bridge rather than direct exposure of Runtime Event types.

## Explicit Non-Decisions

This ADR does not decide:

- concrete queue-capacity default;
- dynamic subscribe/unsubscribe behavior;
- subscriber priority;
- wildcard/inheritance routing;
- event coalescing/drop policy;
- multiple dispatcher workers;
- per-source partition ordering;
- persistent Event storage/replay;
- Desktop bridge buffering/reconnect policy;
- business Event schemas;
- global shutdown deadlines or universal handler timeouts.

## Relationship to Existing ADRs

This decision builds on:

- ADR 0001 - WPF Desktop and Python Agent Core separation;
- ADR 0002 - WebSocket Desktop/Core transport;
- ADR 0004 - Local-first runtime and provider abstraction;
- ADR 0010 - Runtime Events are facts; commands and requests remain explicit boundaries.

The in-process Event Bus is separate from the WebSocket transport and does not supersede ADR 0002.


## Amendment Relationship

ADR 0012 supersedes only these ADR 0011 statements:

- publishers wait asynchronously for queue space when the queue is full;
- blocked publishers participate in a shutdown-vs-capacity race;
- cancellation while waiting for queue capacity is part of normal overload handling.

ADR 0012 replaces them with fail-fast bounded admission using `EventBusFullError`. Routing, ordering, subscriber execution, failure isolation, lifecycle, ownership, and persistence decisions in ADR 0011 remain Accepted.
