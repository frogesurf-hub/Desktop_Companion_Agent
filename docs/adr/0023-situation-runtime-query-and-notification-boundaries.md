# ADR 0023 — Situation State Queries and Transient Change Notifications Are Separate

Status: Accepted

Date: 2026-09-27

## Context

The current EventBus has a bounded queue, fail-fast admission, exact-type static
subscriptions and transient delivery. A successful publish means admission only.
Closing rejects all new publications, including derived events from handlers
processing already accepted input. Situation is the first planned business
consumer that needs these constraints to be explicit.

## Decision

1. SituationRuntime owns current in-memory state. SituationReader exposes an
   explicit query capability. EventBus does not implement query/response RPC.
2. Input handling, expiry maintenance and snapshots share one serialized state
   boundary; external modules cannot mutate that state.
3. Changes are published as immutable, versioned SituationChanged snapshots.
   Situation does not consume its own change notifications.
4. State transition and notification admission have distinct outcomes. Rejected
   publication does not roll back valid current state. Notification failure must
   be safely observable; it is not hidden by general subscriber isolation.
5. Queue-full admission is handled without waiting for capacity, automatic
   retries, unbounded buffering, durable outbox or dispatcher changes.
6. Graceful EventBus drain retains its current meaning. It does not promise that
   all derived events will be accepted during closing. Such rejections are
   explicitly handled and reported without blocking shutdown.
7. The composition root owns construction, startup registration, maintenance
   lifetime and cleanup. Expiry maintenance uses an explicit capability call;
   no generic Scheduler or command-shaped RuntimeEvent is introduced.
8. A chat observation adapter publishes minimal metadata facts around the
   existing chat processor. It preserves its delegated response/error/cancellation
   semantics. Recoverable observation-admission failure does not invalidate chat.
9. Initial diagnostics use in-process queries and safe lifecycle logs. Phase 5
   does not add a Desktop Event Bridge, Situation WebSocket family or WPF view.
10. Evaluation, input-observation delivery and output-notification health are
    distinguishable. An empty healthy query is not used to disguise a failure.

## Alternatives considered

- Use events as the only state source: rejected; transient, non-admitted
  notifications cannot provide a reliable complete current-state view.
- Roll back state whenever notification admission fails: rejected; this would
  discard a valid interpretation because a separate delivery capability failed.
- Wait for queue space inside a subscriber: rejected by ADR 0012 deadlock rationale.
- Extend EventBus shutdown to accept arbitrary derived publications: deferred;
  this is an infrastructure semantic change requiring its own reviewed decision.
- Add WebSocket/UI diagnostics immediately: deferred because no current consumer
  requires the protocol/UI increment to establish the internal capability.

## Consequences

Consumers must not treat notifications as a durable event log. A future consumer
needing resynchronization must define how it uses explicit snapshots.

Tests must cover full queues, rejected publication during closing, state/query
consistency, cancellation, and production composition with the same state owner.
No guarantee is made that every actual input fact reaches Situation.

## Non-decisions

No automatic retries, event replay, priority queues, persistent state, new broker,
generic RPC, reconnect protocol or future Attention behavior is introduced.

## Relationship

Preserves ADR 0010, 0011 as amended by 0012, 0018, 0019 and 0021.
Companion decision: ADR 0022.
Design: `../PHASE_5_SITUATION_ENGINE_DESIGN.md`.

## Acceptance record

The owner accepted the Phase 5 scope and prioritized the engineering workflow on
2026-09-27. The Assistant reviewed these runtime semantics against EventBus code,
ADRs 0010–0012 / 0019 / 0021, and the owner-supplied complete staged diff. This
records a design decision only; no Situation implementation or runtime acceptance
is claimed. Product-scope changes still require an Owner Decision.
