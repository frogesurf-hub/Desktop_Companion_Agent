# Phase 2 - Event System Design

Status: **Architecture Reviewed - ADR 0010 / ADR 0011 / ADR 0012 Accepted; Task 1 complete; Task 2 architecture correction recorded**

Date: 2026-09-10

Original Phase 2 design baseline: `3e97efc Checkpoint Phase 1 completion`

Current implementation baseline: `31734de Establish Phase 2 runtime event contracts`

Snapshot source: `Desktop_Companion_Agent_phase1.zip`

> This document defines the accepted Phase 2 Event System design baseline before implementation. Architecture Review has passed and ADR 0010 / ADR 0011 are Accepted. It remains a design record, not an implementation record.

---

## 1. Purpose

Phase 2 establishes the runtime Event System that future Desktop Companion Agent modules can use to communicate through explicit event boundaries rather than direct knowledge of each other's concrete implementations.

The Event System is foundational infrastructure for the long-term runtime flow:

```text
External World
    -> Perception
    -> Events
    -> Situation Engine
    -> Attention Engine
    -> Behavior Engine
    -> Voice / Avatar / Tools
```

Phase 2 must create a durable architectural boundary without implementing the business logic of Character, Memory, Perception, Situation, Attention, Behavior, Permission, Tools, Voice, or Avatar.

The design must preserve the working Phase 1 vertical slice:

```text
WPF Desktop
    -> WebSocket / JSON
    -> Python WebSocketServer
    -> Agent
    -> LLMProvider
    -> DeepSeekProvider
    -> DeepSeek API
    -> response
    -> WPF Desktop
```

Phase 2 is therefore an additive runtime-infrastructure phase, not a rewrite of the Phase 1 chat path.

---

## 2. Baseline and Source Priority

Phase 2 uses the Phase 1 snapshot as the authoritative implementation baseline.

Source priority remains:

```text
Current code
    > current PROJECT_STATE / Phase checkpoint
    > other current documentation
    > Phase 0 historical documentation
    > chat history
```

The supplied Phase 1 archive identifies the checkpoint commit corresponding to:

```text
3e97efc Checkpoint Phase 1 completion
```

Historical documents may explain why an architecture exists but must not override current Phase 1 implementation behavior.

---

## 3. Phase 2 Goal

Primary goal:

> Establish an in-process runtime Event Bus and Event model so future runtime modules can publish facts and notifications without hard-calling concrete consumers.

A successful Phase 2 must define and verify:

- runtime event identity and envelope semantics
- event publication semantics
- routing semantics
- subscriber boundaries
- dispatch ordering and concurrency semantics
- subscriber failure isolation
- bounded queue and overload-admission semantics
- Event Bus lifecycle and cancellation behavior
- event lifecycle observability
- explicit separation between runtime events and Desktop protocol messages
- a minimal integration boundary that does not break the Phase 1 vertical slice

---

## 4. Scope

### 4.1 In Scope

Phase 2 includes:

- a provider-independent and business-domain-neutral runtime Event model
- an asynchronous in-process Event Bus
- typed event routing
- subscriber contracts
- bounded queueing
- explicit overload rejection behavior
- deterministic dispatch semantics
- subscriber failure isolation
- explicit Event Bus lifecycle
- graceful shutdown behavior
- cancellation semantics
- event metadata logging / observability
- deterministic tests for Event System contracts
- composition-root integration as required to give the Event Bus a clear owner
- documentation and ADR updates after Architecture Review

### 4.2 Explicitly Out of Scope

Phase 2 does not implement:

- Character System
- Memory System
- Perception Layer
- Situation Engine
- Attention Engine
- Behavior Engine
- Internal State
- Permission Layer
- Tool System
- autonomous desktop actions
- Avatar / Live2D / VRM
- Voice
- local-model fallback
- provider routing
- token streaming
- event persistence
- event sourcing
- event replay
- durable queues
- distributed messaging
- cross-process Event Bus infrastructure
- business-level event prioritization
- wildcard/topic-pattern subscriptions
- generalized workflow orchestration

If a future-module boundary is required to verify the Event contract, Phase 2 may use a minimal test-only example Event / subscriber. Such fixtures must not implement future business behavior.

---

## 5. Architectural Principle: Events Are Facts, Not Hidden Commands

The Event System must not become a universal replacement for ordinary interfaces.

The proposed semantic distinction is:

```text
Event
    = a fact or notification that something has already happened

Command / Request / Interface call
    = a request that something be done, queried, authorized, or returned
```

Examples of future event-shaped concepts:

```text
WindowChanged
UserBecameIdle
SituationChanged
AgentResponseGenerated
```

Examples that should not be disguised as ordinary events merely to use the Event Bus:

```text
CallLLMAndReturnResponse
OpenFileAndConfirmSuccess
AskPermissionAndReturnDecision
GetCurrentMemory
```

Those interactions require explicit command/request/service boundaries because the caller depends on completion, a return value, authorization, or a defined failure contract.

### 5.1 Consequence for the Current Chat Path

Phase 2 does not rewrite:

```text
WebSocketServer
    -> Agent.process_message()
    -> LLMProvider.generate()
```

into an event-only workflow.

The existing request/response chain already has stable interfaces and explicit return semantics. Replacing it solely for architectural uniformity would increase coupling through hidden asynchronous behavior and broaden Phase 2 unnecessarily.

The Event Bus may later carry facts produced by the chat/runtime path, but the request itself remains an explicit request path unless a future requirement justifies redesign.

### 5.2 Documentation Clarification Required

`ARCHITECTURE.md` currently states that modules communicate through events to avoid direct coupling. Phase 2 final documentation must clarify this wording so it does not imply that every dependency or request must use Event Bus dispatch.

The intended long-term rule is:

> Use events for decoupled facts and notifications; use stable interfaces for commands, requests, capabilities, and operations requiring a result.

---

## 6. Runtime Placement

The Event System is a Python Agent Core runtime facility.

Conceptually:

```text
Python Runtime

Runtime Module / Producer
        |
        | RuntimeEvent
        v
+-----------------------+
|       Event Bus       |
|  bounded async queue  |
+-----------+-----------+
            |
            v
+-----------------------+
|      Dispatcher       |
+-----------+-----------+
            |
     +------+------+------+
     |             |      |
     v             v      v
Subscriber A  Subscriber B  Subscriber C
```

The Event Bus is process-local in Phase 2.

It is not the Desktop WebSocket protocol, a network broker, a persistence system, or a provider abstraction.

---

## 7. Runtime Event Model

### 7.1 Event Immutability

Runtime Events are immutable after creation.

Rationale:

- an Event represents an already-observed fact
- one subscriber must not mutate what another subscriber observes
- immutable events make concurrent delivery safer and easier to reason about
- immutable Provider models already established this project preference for boundary data

The concrete Python representation will be selected during implementation only if it preserves this contract. A frozen dataclass is the expected implementation direction but is not itself the architectural requirement.

### 7.2 Required Event Metadata

Every Runtime Event must carry:

```text
event_id
occurred_at
source
```

Semantics:

#### `event_id`

A UUID identifying one Runtime Event instance.

Purpose:

- lifecycle tracing
- debugging
- handler-failure correlation
- future cross-boundary diagnostics

Default Event creation generates a new UUID.

The specific UUID generation version/implementation remains an implementation
detail unless a future requirement makes it part of the public contract.

#### `occurred_at`

The time at which the represented event occurred.

Required semantics:

- timezone-aware
- normalized to UTC at the runtime boundary

UI/local-time presentation is outside the Event model.

#### `source`

A non-empty string containing the stable logical identifier of the component
that produced the Event.

`source` is observability/context metadata only. It does not imply authority,
permission, trust, or execution capability.

Phase 2 does not introduce an EventSource registry or class hierarchy.

### 7.3 Optional Causal Metadata

Runtime Events may carry:

```text
correlation_id
causation_id
```

Both are optional.

#### `correlation_id`

Groups multiple Events that belong to one larger activity or interaction.

Example:

```text
UserInput
    -> SituationUpdated
    -> AttentionRequired
    -> BehaviorIntentCreated

all may share one correlation_id
```

#### `causation_id`

Identifies the direct Event that caused a derived Event.

Example:

```text
Event A id=1
    -> Event B id=2, causation_id=1
        -> Event C id=3, causation_id=2
```

This gives the runtime a minimal causal-tracing foundation without introducing workflow orchestration or event persistence.

Phase 2 does not require every Event to have causal metadata. Root Events may omit both fields.

### 7.4 Typed Concrete Events

Internal runtime routing should use concrete Event types rather than string topics.

Conceptually:

```text
RuntimeEvent
    ^
    |
ConcreteEventA
ConcreteEventB
```

Future business phases will introduce their own concrete event types when required.

Phase 2 must not create speculative business events for Character, Memory, Perception, Situation, Attention, or Behavior.

### 7.5 Payload Strategy

Phase 2 should avoid a generic mutable dictionary payload as the primary internal event contract.

A design such as:

```text
name = "window.changed"
payload = { ... arbitrary keys ... }
```

would create a stringly-typed internal architecture with weak refactoring and static-analysis guarantees.

The intended model is that each concrete Runtime Event carries its own strongly defined immutable fields.

The base Runtime Event contains shared metadata only.

---

## 8. Routing Model

### 8.1 Exact-Type Routing

Phase 2 uses exact concrete Event type routing.

Conceptually:

```text
subscribe(ConcreteEventA, handler)
```

receives `ConcreteEventA` only.

Phase 2 does not define implicit inheritance/polymorphic routing.

Reasons:

- predictable subscription scope
- simple routing semantics
- strong typing
- easier tests
- avoids hidden expansion when event hierarchies evolve

### 8.2 No Wildcards or Topic Patterns

Phase 2 does not support:

```text
"*"
"perception.*"
predicate-based subscription
topic pattern matching
```

These capabilities can be designed later if an actual use case requires them.

### 8.3 No Subscriber Priority

Phase 2 does not assign numeric or implicit priority to subscribers.

If business logic requires B to occur only after A has completed, that dependency must be represented explicitly through a workflow/interface or through a new fact produced by A.

Hidden ordering through registration order or numeric priority would make runtime behavior difficult to understand and would partially duplicate future Situation / Attention responsibilities.

---

## 9. Subscriber Boundary

Subscribers use an asynchronous handler boundary.

Conceptual contract:

```text
async handle(event) -> None
```

The architectural requirement is callable async behavior with no return value used by the publisher.

The implementation may use a Python Protocol/callable abstraction rather than requiring framework base-class inheritance.

Reasons:

- consistent with the existing asyncio runtime
- allows I/O-capable future subscribers
- works with dependency injection
- enables instance methods and dedicated handler objects
- avoids coupling runtime modules to a framework inheritance hierarchy

### 9.1 Subscriber Independence

Subscribers to the same Event must not depend on each other's registration order.

A subscriber that requires the result of another subscriber represents a workflow dependency and must use a more explicit boundary.

---

## 10. Publication Semantics

Phase 2 proposes an asynchronous queued publish contract.

The meaning of:

```text
await publish(event)
```

is:

> the Event Bus has accepted the Event into its bounded runtime queue.

It does **not** mean:

- all subscribers have started
- all subscribers have completed
- all subscribers succeeded

This separation prevents publishers from being directly coupled to subscriber execution duration.

### 10.1 Publish Failure Boundary

Publication-level failure represents failure of the Event Bus to accept the Event under its lifecycle/contract rules.

Examples may include:

- publishing when the bus is not in an accepting state
- invalid use of the Event Bus public contract
- explicit queue-capacity exhaustion behavior

Subscriber exceptions are not raised back to the original publisher after acceptance.

Architecture Review accepted a deliberately small Event System error surface. The accepted public non-admission errors are `EventBusStateError` for lifecycle misuse and `EventBusFullError` for bounded-queue overload. Speculative internal error classes remain out of scope.

---

## 11. Queue Capacity and Overload Admission

### 11.1 Bounded In-Memory Queue

Phase 2 uses a bounded in-memory queue.

Reasons:

- the Companion is intended to become a long-running process
- an unbounded queue can convert slow/failing consumers into uncontrolled memory growth
- bounded capacity makes overload visible to producers

### 11.2 Overload Admission

When the queue reaches capacity, publication fails explicitly with `EventBusFullError` rather than waiting indefinitely or silently dropping the Event.

Conceptually:

```text
producer
   -> queue has capacity
      -> Event admitted

producer
   -> queue full
      -> EventBusFullError
      -> Event not accepted
```

Phase 2 does not define automatic retry, silent dropping, or business-specific event coalescing behavior.

Overload recovery depends on event semantics. A future high-frequency Perception event might be retryable or coalescible while a future permission or lifecycle fact may require a different response. The base Event System reports non-admission explicitly and must not guess those rules.

### 11.3 Re-entrant Publication Safety

A subscriber may legitimately publish a derived Runtime Event in a future Phase. With a single dispatcher and the rule that the current Event settles before the next Event dispatch begins, waiting for queue capacity can create a circular wait:

```text
current Event handler
    -> await publish(derived Event)
    -> queue already full
    -> waits for dispatcher to consume queue

dispatcher
    -> waits for current Event handler to finish
```

Phase 2 therefore uses fail-fast bounded admission. Re-entrant publication either succeeds immediately when queue capacity exists or receives `EventBusFullError`; it cannot wait on the same dispatcher whose progress depends on the current handler returning.

This correction was discovered during Task 2 working-code review and is recorded in `docs/PHASE_2_ARCHITECTURE_CORRECTION_001.md` and ADR 0012.

### 11.4 Queue Capacity

The architectural requirement is bounded capacity.

The exact capacity value is not fixed by this design document and must not become a hard-coded architectural constant without evidence.

Implementation review should decide whether the initial capacity is:

- a runtime setting, consistent with the existing Settings pattern, or
- an explicit constructor/composition-root parameter with a conservative default

This is an implementation/configuration decision, not an Event semantic decision.

---

## 12. Dispatch Ordering and Concurrency

Phase 2 proposes two levels of semantics.

### 12.1 Between Events: FIFO Dispatch

Events are taken from the Event Bus queue in acceptance order.

Conceptually:

```text
E1
E2
E3
```

are dispatched in:

```text
E1 -> E2 -> E3
```

### 12.2 Within One Event: Concurrent Subscribers

Subscribers for one Event may execute concurrently.

Conceptually:

```text
               +-> Subscriber A
Event E1 ------+-> Subscriber B
               +-> Subscriber C
```

No subscriber should rely on completion order relative to another subscriber.

### 12.3 One Event Completes Before the Next Event Is Dispatched

Phase 2 does not introduce multiple concurrent Event workers.

The proposed baseline is:

```text
E1
  -> A, B, C concurrently
  -> all E1 handlers settle
E2
  -> handlers
```

This provides:

- understandable FIFO runtime behavior
- subscriber independence
- simple deterministic testing
- failure isolation
- bounded initial concurrency

Future Perception throughput may justify multiple workers, partitioned ordering, or coalescing, but those are not Phase 2 requirements.

---

## 13. Subscriber Failure Semantics

Subscriber failures are isolated.

For one Event:

```text
Event E
    -> Subscriber A: success
    -> Subscriber B: exception
    -> Subscriber C: success
```

Required behavior:

- B's ordinary exception is recorded through observability
- A/C are not cancelled merely because B failed
- the Event Bus remains operational
- later Events continue to dispatch
- B's exception is not propagated to the original publisher after the Event was accepted

This is required for a modular Companion Runtime. A failure in a future optional subsystem such as Avatar must not automatically stop unrelated systems such as Perception or Memory.

### 13.1 Cancellation Is Different From Ordinary Failure

Cancellation must not be silently converted into an ordinary subscriber error.

`asyncio.CancelledError` semantics must be preserved at lifecycle boundaries so runtime shutdown/cancellation can work correctly.

Architecture Review requires structured cancellation: ordinary subscriber exceptions are isolated inside each handler boundary, while cancellation propagates and cancels in-flight sibling work through the Event Bus lifecycle boundary. Targeted tests must verify this behavior.

### 13.2 No Automatic Error Events

Phase 2 does not automatically publish `HandlerFailedEvent` or similar infrastructure Events when a subscriber throws.

Reasons:

- failure events can recursively fail
- automatic republishing can create event storms or loops
- infrastructure failure reporting is already an observability responsibility

A future business subsystem may explicitly translate a domain failure into a domain Event when semantically appropriate.

---

## 14. Event Bus Lifecycle

A queued Event Bus owns a background dispatcher and therefore requires an explicit lifecycle.

The proposed state model is:

```text
NEW
  |
  | start
  v
RUNNING
  |
  | close requested
  v
CLOSING
  |
  | accepted queue drained
  v
CLOSED
```

### 14.1 NEW

- Event Bus object exists
- dispatcher is not running
- ordinary publication is not accepted

### 14.2 RUNNING

- dispatcher is active
- subscriptions are active
- publication is accepted only when the bounded queue has immediate capacity

### 14.3 CLOSING

- new publication is rejected
- Events already accepted into the queue are drained
- Event Bus waits for the current Event's handlers and queued Events to settle

### 14.4 CLOSED

- dispatcher has stopped
- publication is rejected
- no new runtime work is accepted

### 14.5 Graceful Drain

Normal shutdown should process Events that were already accepted before the transition to CLOSING.

Phase 2 does not define durable recovery for a process crash or forced termination.

### 14.6 Forced Cancellation

The Event Bus must not swallow external runtime cancellation.

A higher runtime layer may eventually impose an overall shutdown deadline and force cancellation, but Phase 2 does not define one global handler timeout because future subscriber workloads will have different valid durations.

### 14.7 Accepted Lifecycle API Semantics

Architecture Review fixed the public lifecycle contract:

- `start()` is valid only in `NEW`; repeated or late start attempts are lifecycle errors.
- the Event Bus is not restartable after close.
- `close()` is idempotent for callers.
- closing from `NEW` transitions directly to `CLOSED`.
- closing from `RUNNING` transitions to `CLOSING`, rejects new Event acceptance, drains already accepted Events, then transitions to `CLOSED`.
- a `close()` call made during `CLOSING` waits for the same shutdown to finish.
- a `close()` call in `CLOSED` returns without error.
- `publish()` is accepted only in `RUNNING`; it does not auto-start the bus.
- `subscribe()` is accepted only in `NEW`; the subscription table is frozen after start.

Phase 2 publication does not wait for queue capacity. While `RUNNING`, admission performs the state check and non-blocking bounded-queue insertion without a suspension point between them. Therefore shutdown cannot interleave between an accepted state check and queue admission in the single-event-loop baseline.

If the bus is no longer `RUNNING`, publication fails with the lifecycle/state error. If the queue is full, publication fails with `EventBusFullError`. Only successfully admitted Events are part of graceful drain.

---

## 15. Subscription Lifetime

Phase 2 uses **static startup subscriptions**.

- subscriptions are registered explicitly by composition/lifecycle code while the Event Bus is `NEW`;
- the subscription table is frozen after `start()`;
- there is no public `unsubscribe()` in Phase 2;
- closing the Event Bus releases all subscriptions with the bus lifetime;
- each explicit `subscribe()` call creates one subscription; Phase 2 does not add hidden de-duplication semantics.

This matches the current composition-root model and avoids concurrent routing-table mutation before dynamic module loading is a demonstrated requirement.

A future requirement for dynamically loaded/unloaded modules may introduce explicit subscription handles or unsubscribe semantics through a separate reviewed extension.

---

## 16. Observability and Logging

Phase 2 requires Event lifecycle observability without logging sensitive Event content by default.

### 16.1 Default Metadata Logging

The Event System may log metadata such as:

```text
event_id
event_type
source
correlation_id
causation_id
lifecycle_stage
handler_identity
success / failure
processing_duration
```

Expected lifecycle stages include enough information to diagnose:

```text
accepted/published
dispatch started
handler completed
handler failed
event dispatch completed
```

The exact log wording and level mapping is an implementation detail, but lifecycle meaning must remain stable enough for debugging.

### 16.2 Sensitive Payload Rule

The Event System must not log the full Event payload or `repr(event)` by default.

Future Events may contain:

- user text
- file/window information
- Memory content
- Tool parameters
- screen-derived context
- private user data

Phase 1 already established that observability must not casually expose sensitive user/provider data. Phase 2 extends that principle to Runtime Events.

### 16.3 Failure Logging

Subscriber failures should identify:

- Event identity/type
- handler identity
- exception class / safe diagnostic information

without automatically dumping sensitive Event fields.

---

## 17. Runtime Event vs Desktop Protocol Event

The current Desktop protocol documentation contains a historical `type = "event"` message concept, but that protocol shape is not the Runtime Event model.

Required separation:

```text
RuntimeEvent
      !=
Desktop Protocol Message
```

This mirrors the Phase 1 separation:

```text
LLMRequest / LLMResponse
      !=
Desktop Protocol Message
```

Runtime Event types must not leak directly into C# protocol contracts merely because they exist in Python.

---

## 18. Desktop / Runtime Event Bridge

Phase 2 defines the architectural boundary for a future bridge but does not implement the concrete bridge by default.

Future shape:

```text
Runtime Event
     |
     | explicit export/bridge policy
     v
Desktop Event Bridge
     |
     | protocol mapping
     v
Desktop Protocol Message
     |
     v
WebSocket
     |
     v
C# independent receive loop
```

The bridge must be explicit because:

- not every internal runtime Event belongs in the UI
- internal Python type structures should not become wire contracts automatically
- disconnect/reconnect/buffering semantics are separate transport concerns
- sensitive internal Events may never be eligible for Desktop export

### 18.1 Why Concrete Bridge Implementation Is Deferred

Phase 2 currently has no real Perception/Situation/Attention/Behavior producer that requires proactive Desktop output.

Building a bridge only to transmit test Events would modify the stable WebSocket surface without a product requirement.

Therefore the proposed scope is:

```text
Desktop receive-loop capability      preserve
Runtime/Desktop boundary             document
Concrete bridge implementation       defer until needed
```

Architecture Review found no concrete Phase 2 acceptance requirement that justifies implementing the bridge. Concrete Desktop Event Bridge implementation remains deferred.

---

## 19. Composition Root and Ownership

Phase 1 established that concrete dependency construction and lifecycle belong in the Python composition root.

Phase 2 should preserve that rule.

Conceptually:

```text
main.py / composition root
    |
    +-> construct Provider
    +-> construct Event Bus
    +-> construct Agent / runtime components
    +-> register subscriptions
    +-> start runtime services
    +-> close runtime services in defined order
```

The Event Bus should not be a hidden global singleton.

Runtime modules receive only the minimum capability they require through dependency injection.

A producer should not receive unrestricted access to Event Bus lifecycle or subscription management.

Phase 2 therefore introduces a narrow `EventPublisher` capability whose public responsibility is publication only. The concrete Event Bus implements that capability while retaining lifecycle/subscription operations for the composition root. Future producer modules should normally depend on `EventPublisher`, not the full concrete Event Bus.

---

## 20. Relationship to Long-Term Architectural Boundaries

### 20.1 Intent != Permission

An Event such as a future behavior-intent notification must not grant permission.

The future shape remains conceptually:

```text
Behavior Intent
    -> Permission / Capability Boundary
    -> Tool / Action execution
```

The Event Bus transports information; it does not authorize actions.

### 20.2 Real State != Fictional State

The Event Bus does not merge domains merely because all information is represented as Events.

Future real-world, user-fact, and fictional/ephemeral Events must retain domain separation at their owning subsystem boundaries.

### 20.3 Local-First, Cloud-Enhanced

The Event Bus is local runtime infrastructure and must not require a cloud provider to operate.

Cloud Provider failure must not make the Event System unavailable.

### 20.4 UI Does Not Own Agent Reasoning

Desktop/WPF remains presentation/integration infrastructure.

Runtime Event reasoning, future Situation/Attention behavior, Provider behavior, Memory, and Tool policy remain outside UI ownership.

---

## 21. Persistence and Reliability Boundaries

Phase 2 Event Bus is transient and in-memory.

On normal process termination after graceful drain, there is no durable Event log for replay.

On process crash, queued Events may be lost.

This is accepted Phase 2 behavior.

The following require separate future requirements and design:

```text
Event Store
Event Sourcing
Replay
Durable Queue
Crash Recovery
Exactly-once delivery
At-least-once delivery
Distributed broker
```

Phase 2 must not imply delivery guarantees that an in-memory process-local bus cannot provide.

---

## 22. Proposed Module Boundary

The exact filenames remain implementation-review details, but Phase 2 should introduce a dedicated Python Event System package rather than placing Event Bus logic in `core.message` or `communication.websocket_server`.

Proposed conceptual structure:

```text
src/agent_core/
├── communication/
├── config/
├── core/
├── events/
│   ├── event model / contracts
│   ├── bus / dispatcher
│   └── event-system errors if justified
├── observability/
├── providers/
└── main.py
```

Important dependency rules:

- `events` must not import DeepSeek/OpenAI SDK types
- `events` must not depend on WPF/Desktop protocol DTOs
- `events` must not implement Character/Memory/Perception business logic
- WebSocket transport must not become the Event Bus
- future modules may depend on Event contracts without depending on concrete consumer implementations

---

## 23. Testing Strategy

Phase 2 automated tests must remain deterministic and local.

No Event System unit test may require:

- network access
- a real API key
- DeepSeek availability
- WPF execution

### 23.1 Event Model Tests

Verify at minimum:

- required metadata contract
- immutability
- timezone/UTC requirements
- Event identity behavior
- optional correlation/causation semantics

### 23.2 Routing Tests

Verify:

- exact-type subscription
- matching subscribers receive the Event
- unrelated event types do not receive it
- no implicit wildcard/polymorphic behavior exists

### 23.3 Queue / Publication Tests

Verify:

- publication accepts an Event while RUNNING
- publication semantics mean queue acceptance rather than handler completion
- full bounded queue rejects publication explicitly with `EventBusFullError`
- no silent drop occurs
- queue-full publication returns explicit non-admission rather than blocking

### 23.4 Dispatch Tests

Verify:

- accepted Events dispatch FIFO
- subscribers for one Event may run concurrently
- the next Event does not dispatch until current Event subscribers settle under the Phase 2 baseline

Tests must avoid timing-fragile sleeps where synchronization primitives can provide deterministic coordination.

### 23.5 Failure Tests

Verify:

- one subscriber ordinary exception does not stop other subscribers
- the Event Bus continues processing future Events
- subscriber failure does not propagate back to the already-completed publish call
- cancellation is not swallowed as an ordinary failure

### 23.6 Lifecycle Tests

Verify the accepted lifecycle semantics, including:

- start behavior
- close behavior
- graceful drain
- publication rejection outside accepted states
- cleanup of dispatcher tasks

### 23.7 Observability Tests

Verify:

- lifecycle metadata is observable
- handler failures are diagnosable
- full Event payload content is not logged by default
- sensitive test payload values do not appear in captured logs

### 23.8 Regression Protection

Minimal integration work must preserve the Phase 1 Agent/Provider behavior.

During individual Phase 2 tasks, only directly relevant targeted tests are run.

At Phase final acceptance, the project owner runs the full Python quality gate and any required Desktop build/manual acceptance.

---

## 24. Proposed Phase 2 Task Breakdown

This task breakdown is the accepted planning baseline after Architecture Review and ADR acceptance.

### Task 1 - Runtime Event Contract Foundation

Purpose:

- establish the Event model and public boundary only

Expected scope:

- Runtime Event metadata contract
- immutability
- causal metadata
- subscriber/public protocol definitions that are required by the model
- deterministic Event model tests

No queue or dispatcher behavior yet.

### Task 2 - Event Bus Core

Purpose:

- implement accepted publish/subscribe, exact-type routing, and bounded admission semantics

Expected scope:

- bounded queue
- async publish acceptance semantics
- explicit `EventBusFullError` overload rejection
- dispatcher
- exact-type routing
- re-entrant publication deadlock regression test
- targeted routing/admission-control tests

### Task 3 - Lifecycle and Failure Isolation

Purpose:

- make the Event Bus safe as a long-running runtime service

Expected scope:

- lifecycle state behavior
- graceful drain
- cancellation handling
- subscriber concurrent execution for one Event
- failure isolation
- deterministic lifecycle/failure tests

### Task 4 - Event Observability

Purpose:

- make Event flow diagnosable without exposing Event payloads

Expected scope:

- lifecycle metadata logging
- subscriber failure diagnostics
- duration/handler identity where useful
- sensitive-payload logging tests

### Task 5 - Minimal Runtime Integration

Purpose:

- give the Event Bus a real owner in the composition root without rewriting the Phase 1 request/response path

Expected scope:

- Event Bus construction/cleanup
- only the minimum integration required to validate lifecycle ownership
- Phase 1 vertical-slice regression protection

No speculative business modules.

### Task 6 - Phase 2 Acceptance and Documentation

Project-owner final acceptance:

- full pytest
- full Ruff
- full mypy
- C# build only if C# source was actually affected
- relevant manual runtime acceptance
- final diff / archive hygiene
- PROJECT_STATE / ROADMAP / ARCHITECTURE updates
- Phase 2 checkpoint document

Concrete Desktop Event Bridge implementation is not a default Phase 2 Task under this proposal.

---

## 25. Development and Git Workflow

Each implementation Task should remain single-purpose and independently reviewable.

Normal task flow:

```text
Task design confirmed
    -> implementation
    -> targeted pytest
    -> targeted Ruff
    -> targeted mypy
    -> git diff review
    -> git add explicit files
    -> staged diff review
    -> commit
```

Do not run the full pytest suite after every Task.

Do not commit before staged diff review.

Do not add unrelated formatting, caches, `.env`, logs, secrets, or generated files.

Canonical Python dependency source remains:

```text
pyproject.toml
```

Installation remains:

```text
pip install -e ".[dev]"
```

`src/agent_core/requirements.txt` remains legacy metadata and must not receive new dependencies.

---

## 26. Architecture Review Results

Architecture Review passed. The following gates are accepted as the implementation baseline.

### Gate A - Event vs Command Boundary

Confirm:

- Event = fact/notification
- requests requiring result/permission/action remain explicit interfaces/commands
- current chat/Provider request path is not rewritten in Phase 2

### Gate B - Event Envelope

Confirm:

- immutable Event
- required `event_id`, `occurred_at`, `source`
- optional `correlation_id`, `causation_id`
- typed concrete Events
- no generic mutable dictionary payload as the primary internal contract

### Gate C - Dispatch Contract

Confirm:

- async in-process Event Bus
- bounded queue
- `await publish` = accepted into queue
- explicit `EventBusFullError` on full queue
- FIFO between Events
- concurrent subscribers per Event
- next Event waits for current Event subscribers to settle
- exact-type routing
- no wildcard / priority / inheritance routing

### Gate D - Failure Contract

Confirm:

- ordinary subscriber failure isolation
- failure does not propagate to original publisher after acceptance
- cancellation remains distinct and propagates appropriately
- no automatic infrastructure ErrorEvent

### Gate E - Lifecycle Contract

Confirm:

- explicit Event Bus lifecycle
- graceful drain on normal close
- no global subscriber timeout in Phase 2
- exact state/API behavior before implementation

### Gate F - Subscription Lifetime

Accepted:

- static startup subscriptions for Phase 2;
- no public unsubscribe/dynamic subscription mutation in Phase 2.

### Gate G - Integration Boundary

Confirm:

- composition root owns Event Bus lifetime
- no global singleton
- Phase 1 WebSocket -> Agent -> Provider path remains stable
- concrete Desktop Event Bridge remains deferred unless a real acceptance need is identified

### Gate H - Observability

Confirm:

- metadata lifecycle logging
- no full Event payload/repr logging by default
- sensitive event content protected

---

## 27. Accepted ADRs

Architecture Review determined that two long-lived decisions should be recorded separately:

- `ADR 0010 - Runtime Events Are Facts; Commands and Requests Remain Explicit Boundaries`
- `ADR 0011 - Async Bounded In-Process Event Bus for Phase 2`
- `ADR 0012 - Fail-Fast Event Bus Overload Admission to Avoid Re-entrant Publication Deadlock`

ADR 0012 amends only ADR 0011's queue-full publication behavior. All other accepted ADR 0011 decisions remain in force. Keeping the correction separate preserves the architecture decision history instead of rewriting the original review outcome.

---

## 28. Post-Review Architecture Correction 001

During Task 2 working-code review, the original wait-for-capacity backpressure rule was found to permit a re-entrant publication deadlock when a subscriber publishes a derived Event while the bounded queue is already full.

The accepted correction is:

```text
queue has capacity -> admit Event
queue full         -> raise EventBusFullError
```

The Event Bus still provides bounded memory and explicit overload feedback, but does not wait for queue capacity. Retry, coalescing, dropping, or escalation remain producer/domain decisions.

This correction is recorded by:

- `docs/PHASE_2_ARCHITECTURE_CORRECTION_001.md`;
- ADR 0012, which supersedes only ADR 0011's queue-full waiting semantics.

## 29. Explicit Non-Decisions

This Phase 2 design does not decide:

- Character schema
- Memory schema or persistence
- Perception event types
- Situation event types
- Attention scoring
- Behavior intent schema
- Permission policy
- Tool execution contracts
- Avatar/Voice commands
- provider retry/fallback
- event persistence/replay
- cross-process reliable delivery
- Desktop bridge buffering/reconnect semantics
- event priority
- event coalescing/drop rules
- distributed event brokers
- multiple dispatcher workers
- per-source partition ordering
- general workflow engine behavior

These require demonstrated future requirements.

---

## 30. Phase 2 Definition of Done

Phase 2 should be considered complete only when:

1. Event System design has passed Architecture Review.
2. Required ADRs are Accepted.
3. Runtime Event model is implemented and tested.
4. Event Bus routing/publication contract is implemented and tested.
5. bounded queue overload rejection is implemented and tested.
6. dispatch ordering/concurrency semantics are implemented and tested.
7. subscriber failure isolation is implemented and tested.
8. lifecycle/shutdown/cancellation semantics are implemented and tested.
9. Event observability exists without default payload leakage.
10. composition-root ownership is explicit.
11. Phase 1 WebSocket -> Agent -> Provider vertical slice remains protected.
12. no later-phase business subsystem has been pulled into Phase 2.
13. project owner completes final full Python quality gates.
14. documentation/checkpoint accurately reflects implementation rather than proposal.

---

## 31. Current Development Breakpoint

```text
Phase 2 - Event System

Context Recovery                 ✅
Open design-point explanation    ✅
Design document                  ✅
Architecture Review              ✅ Passed
ADR 0010 / ADR 0011 / ADR 0012   ✅ Accepted
Final Task Breakdown             ✅
Task 1 - Event Contract          ✅ 31734de
Task 2 - Event Bus Core          <- architecture correction applied; implementation revision next
Implementation                   in progress
Targeted Verification            pre-correction draft passed; must re-run after correction
Phase Acceptance                 not started
Checkpoint                       not started
```

No Event System implementation code is authorized by this document alone.
