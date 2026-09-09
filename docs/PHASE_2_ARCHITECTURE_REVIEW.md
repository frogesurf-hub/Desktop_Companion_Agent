# Phase 2 - Event System Architecture Review

Status: **Passed with required design refinements**

Date: 2026-09-09

Repository baseline: `3e97efc Checkpoint Phase 1 completion`

Reviewed document: `docs/PHASE_2_EVENT_SYSTEM_DESIGN.md`

## 1. Review Result

The proposed Phase 2 Event System direction is architecturally sound and may proceed to ADR finalization and implementation planning after the refinements recorded here are incorporated.

No review finding requires changing the Phase 2 goal, rewriting the Phase 1 chat/Provider path, or pulling a later-phase business subsystem into Phase 2.

The review accepts the following high-level direction:

- Events represent facts/notifications, not hidden commands or request/response operations.
- The existing `WebSocketServer -> Agent -> LLMProvider` request path remains intact.
- Runtime Events are immutable, strongly typed, process-local Python objects.
- The Event Bus is async, in-process, queue-backed, and bounded.
- `await publish(event)` means queue acceptance, not subscriber completion.
- Routing is exact-type only in Phase 2.
- Events dispatch in queue-admission order.
- Subscribers for one Event execute concurrently and independently.
- One Event settles before the next Event begins dispatch in the Phase 2 baseline.
- Ordinary subscriber failures are isolated.
- Cancellation is not converted into an ordinary handler failure.
- Normal shutdown drains already accepted Events.
- Event lifecycle logging uses metadata and does not log full Event payloads by default.
- Runtime Events remain distinct from Desktop protocol messages.
- The concrete Desktop Event Bridge remains deferred until a real runtime producer requires it.

## 2. Required Refinement A - Static Subscription Lifetime for Phase 2

### Decision

Phase 2 uses **static startup subscriptions**.

Subscriptions may be registered only while the Event Bus is in `NEW` state.

After `start()` transitions the bus to `RUNNING`, the subscription table is frozen for that Event Bus lifetime.

Phase 2 does not expose public `unsubscribe()` or dynamic subscription mutation.

### Rationale

The current runtime uses an explicit composition root and does not yet support dynamically loaded modules. Static registration:

- keeps ownership visible in composition code;
- avoids concurrent mutation of routing tables;
- avoids subscription-handle lifetime complexity;
- makes tests deterministic;
- leaves a clean future extension point when a real dynamic-module requirement appears.

Each explicit `subscribe()` call creates one subscription. Phase 2 does not add hidden de-duplication rules.

## 3. Required Refinement B - Exact Lifecycle API Semantics

The lifecycle contract is fixed as follows.

### `start()`

- valid only in `NEW`;
- transitions `NEW -> RUNNING`;
- creates the private dispatcher task;
- calling `start()` in `RUNNING`, `CLOSING`, or `CLOSED` is a lifecycle contract error;
- the Event Bus is not restartable after close.

Fail-fast behavior is preferred over silently treating repeated `start()` calls as harmless because a duplicate start indicates composition/lifecycle misuse.

### `close()`

`close()` is idempotent from the caller's perspective:

- `NEW -> CLOSED`: closes immediately; no dispatcher needs draining;
- `RUNNING -> CLOSING -> CLOSED`: rejects new Event acceptance and gracefully drains Events that were already accepted;
- `CLOSING`: another `close()` call waits for the same shutdown to finish;
- `CLOSED`: returns without error.

### `publish()`

- valid only while the bus is `RUNNING`;
- successful return means the Event was admitted to the bounded queue;
- `NEW`, `CLOSING`, and `CLOSED` reject publication with an Event Bus lifecycle/state error;
- publication does not auto-start the bus.

### `subscribe()`

- valid only in `NEW`;
- subscription mutation after `start()` is rejected;
- the composition root is the normal registration owner.

## 4. Required Refinement C - Shutdown vs Backpressure Race

A publish operation may be waiting because the bounded queue is full when shutdown begins.

Phase 2 defines the acceptance boundary precisely:

> Once the Event Bus transitions to `CLOSING`, a publish that has not yet been admitted to the queue is not considered accepted and must not enter the queue afterward.

Therefore:

- Events already admitted to the queue before `CLOSING` are drained.
- A blocked publisher whose queue admission loses the race to shutdown receives the lifecycle/state failure.
- If queue admission completed first, the Event is accepted and is included in the graceful drain.
- Cancellation while a publisher waits for queue capacity propagates as cancellation and does not become a normal Event Bus error.

This prevents the Event Bus from silently accepting additional work after its shutdown boundary.

## 5. Required Refinement D - Ordering Guarantee Is Queue-Admission Order

The Phase 2 FIFO guarantee is defined as:

> Events are dispatched in the order in which they are successfully admitted to the Event Bus queue.

This is intentionally weaker than claiming an external total order for concurrent publishers.

Consequences:

- sequential awaited publishes from one producer preserve their queue-admission order;
- concurrent producers may race to admission;
- after admission, the single Phase 2 dispatcher preserves queue order;
- Phase 2 does not introduce cross-producer sequencing, partitions, or ordering keys.

## 6. Required Refinement E - Cancellation and Structured Subscriber Execution

Ordinary subscriber exceptions and cancellation have different semantics.

### Ordinary subscriber exception

- isolated to that subscriber;
- logged through safe observability;
- does not cancel sibling subscribers;
- does not stop the dispatcher;
- does not propagate to the original publisher after acceptance.

### Cancellation

`asyncio.CancelledError` is not treated as an ordinary subscriber failure.

The implementation must use structured ownership of per-Event subscriber tasks so that:

- cancellation of Event Bus dispatch cancels in-flight subscriber tasks;
- cancellation propagates outward rather than being logged and swallowed as a normal handler error;
- ordinary handler exceptions are caught inside the individual handler boundary before they can trigger sibling cancellation.

Phase 2 does not define a universal subscriber timeout.

If graceful `close()` itself is externally cancelled, forced cancellation is allowed: in-flight dispatch is cancelled, cancellation propagates to the caller, and the Event Bus performs terminal cleanup rather than leaving orphan dispatcher/subscriber tasks.

## 7. Required Refinement F - Minimal Publishing Capability Interface

Phase 2 should introduce a narrow **EventPublisher** abstraction whose public capability is publication only.

Conceptually:

```text
EventPublisher
    -> async publish(RuntimeEvent) -> None
```

The concrete Event Bus additionally owns lifecycle and subscription-management operations used by the composition root.

Future producer modules should normally depend on `EventPublisher`, not on the full concrete Event Bus.

Rationale:

- preserves dependency inversion;
- gives producers least privilege;
- prevents ordinary modules from owning lifecycle or mutating subscriptions;
- does not require a framework hierarchy or global singleton.

This interface is justified by a known long-term consumer category: future runtime event producers.

## 8. Required Refinement G - Event Metadata Representation

The architectural types are fixed enough for Task 1:

- `event_id`: UUID identity;
- `occurred_at`: timezone-aware `datetime`, normalized to UTC;
- `source`: non-empty logical component identifier represented as a string in Phase 2;
- `correlation_id`: optional UUID;
- `causation_id`: optional UUID.

Default Event creation should generate a new UUID and current UTC time.

Explicit metadata injection remains possible for deterministic tests and for future derived-event causal propagation.

A naive datetime is invalid. Phase 2 does not create a complex EventSource registry/type hierarchy.

## 9. Required Refinement H - Public Error Surface

Phase 2 should keep the Event System error taxonomy small.

At minimum, lifecycle misuse requires one explicit Event Bus state/lifecycle error type under an Event System base error if the implementation benefits from a stable public exception boundary.

The design should not introduce speculative error classes for every internal condition.

Subscriber exceptions remain subscriber/runtime-processing failures and are not rewrapped as publication errors.

## 10. Required Refinement I - Dispatcher Terminal Behavior

The dispatcher task remains private to the Event Bus.

Phase 2 ordinary subscriber exceptions must not terminate it.

If the dispatcher terminates unexpectedly because of cancellation or an infrastructure-level failure:

- the bus is terminal and is not restarted automatically;
- the failure must be observable;
- cleanup must not leave orphan tasks;
- later publication must not continue as if the bus were healthy.

Phase 2 does not add automatic restart/supervision policy. Runtime supervision is a separate future concern.

## 11. Observability Review

The proposed safe-logging boundary is accepted.

Recommended baseline levels:

- Event Bus lifecycle start/close: informational diagnostics;
- per-Event accepted/dispatched/completed lifecycle: debug diagnostics;
- ordinary subscriber failure: error diagnostics;
- unexpected dispatcher termination: critical/error diagnostics as appropriate.

The exact wording is implementation detail.

Logs must identify metadata necessary for tracing while avoiding `repr(event)` or full Event payload logging.

## 12. Desktop Bridge Review

Deferral is accepted.

Phase 2 will document the bridge boundary but will not modify the stable Desktop/WebSocket protocol merely to demonstrate a synthetic Event.

A future Phase that has a real proactive Desktop-notification requirement must design:

- export eligibility;
- runtime-event to wire-DTO mapping;
- reconnect/disconnect semantics;
- buffering/drop behavior;
- protocol versioning/security implications.

## 13. Architecture Review Gate Results

| Gate | Result | Notes |
| --- | --- | --- |
| A - Event vs Command | Accepted | Keep stable request/response interfaces. |
| B - Event Envelope | Accepted with refinement | UUID metadata, aware UTC time, non-empty string source. |
| C - Dispatch | Accepted with refinement | FIFO means queue-admission order; shutdown/backpressure race specified. |
| D - Failure | Accepted with refinement | Ordinary exceptions isolated; cancellation remains structured cancellation. |
| E - Lifecycle | Accepted with refinement | Exact `start/close/publish/subscribe` state semantics fixed. |
| F - Subscription Lifetime | Accepted | Static startup subscriptions; no unsubscribe in Phase 2. |
| G - Integration | Accepted with refinement | Narrow EventPublisher capability; composition root owns full bus. |
| H - Observability | Accepted | Metadata only by default; no Event payload/repr logging. |

## 14. ADR Requirements

Two decisions are sufficiently broad and long-lived to record separately:

1. **ADR 0010 - Runtime Events are facts; commands/requests remain explicit capability boundaries.**
2. **ADR 0011 - Async bounded in-process Event Bus with queue-admission publish semantics, deterministic dispatch, failure isolation, and explicit lifecycle.**

Separating them prevents the semantic communication rule from being accidentally tied to one concrete dispatcher implementation.

## 15. Review Conclusion

Architecture Review: **PASS**.

No product-level decision requires project-owner intervention at this point.

The next development breakpoint is ADR finalization. No Event System implementation should begin until ADR 0010 and ADR 0011 are recorded as Accepted and the Phase 2 design document is updated to reflect this review.
