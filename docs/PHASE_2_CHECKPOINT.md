# Phase 2 Checkpoint - Desktop Companion Agent

Date: 2026-09-12

Status: **Complete**

Implementation baseline before this final documentation commit:

```text
ccee378 Integrate event bus into runtime composition
```

## 1. Phase Goal

Phase 2 established a runtime Event System so future Desktop Companion Agent modules can communicate through explicit Event boundaries instead of hard-calling concrete consumers.

Long-term position:

```text
External World
  -> Perception
  -> Events
  -> Situation Engine
  -> Attention Engine
  -> Behavior Engine
  -> Voice / Avatar / Tools
```

Phase 2 implemented only the Event infrastructure required at this stage.

It did not implement Character, Memory, Perception, Situation, Attention, Behavior, Permission, Tools, Voice, Avatar, or a Desktop Event Bridge.

## 2. Source and Architecture Baseline

Authoritative starting checkpoint:

```text
3e97efc Checkpoint Phase 1 completion
```

Accepted Phase 2 design artifacts:

```text
docs/PHASE_2_EVENT_SYSTEM_DESIGN.md
docs/PHASE_2_ARCHITECTURE_REVIEW.md
docs/PHASE_2_TASK_PLAN.md
```

Persistent ADRs:

```text
0010 Runtime Events are facts; commands remain explicit boundaries
0011 async bounded in-process EventBus
0012 fail-fast EventBus overload admission
```

ADR 0012 supersedes only ADR 0011's queue-full waiting/backpressure behavior. Other accepted ADR 0011 architecture remains valid.

## 3. Runtime Event Contract

Phase 2 introduced:

```text
RuntimeEvent
EventPublisher
EventHandler
```

`RuntimeEvent` metadata:

```text
source: str
event_id: UUID
occurred_at: datetime (timezone-aware, normalized to UTC)
correlation_id: UUID | None
causation_id: UUID | None
```

Contract properties:

- immutable frozen dataclass
- slots enabled
- keyword-only construction
- default UUID Event identity
- default UTC occurrence timestamp
- aware timestamps normalized to UTC
- naive timestamps rejected
- blank source rejected
- Event-specific payload lives on concrete Event subclasses

Semantic rule:

> Runtime Events represent facts / notifications. They do not carry command, permission, query, or return-value semantics.

## 4. Event Publisher / Subscriber Boundaries

Ordinary producers may depend on the narrow async publication capability:

```python
class EventPublisher(Protocol):
    async def publish(self, event: RuntimeEvent) -> None: ...
```

Subscribers are asynchronous callables typed to a Runtime Event type.

The concrete EventBus retains lifecycle and subscription-management responsibility. Producers should not receive that wider authority unless a later design specifically requires it.

## 5. EventBus Core

Phase 2 EventBus baseline:

```text
scope: in-process Python runtime
queue: bounded in-memory queue
routing: exact Event type
subscription: static before running
publish completion: queue admission only
overload: fail fast with EventBusFullError
ordering: queue admission order
dispatcher: one private dispatcher
persistence: none
```

Important publish rule:

```text
await publish(event)
```

means the Event was accepted into the runtime queue. It does not mean subscribers completed successfully.

### 5.1 Overload Architecture Correction

The initial ADR 0011 queue-full design waited asynchronously for capacity.

During Task 2 review, re-entrant publication exposed a deadlock risk under the accepted single-dispatcher / per-Event settlement model.

The architecture was corrected before the core implementation commit:

```text
queue has capacity -> admit Event
queue is full      -> raise EventBusFullError immediately
```

This correction is recorded in ADR 0012 and the Phase 2 architecture-correction document.

## 6. Routing / Ordering / Concurrency

Accepted semantics:

- exact concrete Event type routing
- queue admission order determines Event dispatch order
- zero-subscriber Events complete normally
- handlers for one Event may execute concurrently
- the next Event waits until the current Event's handlers settle
- no wildcard subscription
- no priority subscription
- no dynamic unsubscribe baseline
- no multiple-dispatch-worker baseline

## 7. Lifecycle and Failure Isolation

Lifecycle:

```text
NEW -> RUNNING -> CLOSING -> CLOSED
```

Implemented behavior includes:

- explicit `start()`
- publication accepted only while RUNNING
- graceful `close()` drain for accepted Events
- close from NEW
- repeated close semantics
- cancellation-aware cleanup
- terminal cleanup if the dispatcher ends unexpectedly
- no intended orphan EventBus / handler tasks

Subscriber failure behavior:

- one ordinary subscriber exception does not cancel sibling handlers
- one ordinary subscriber exception does not stop later Events
- subscriber exception does not propagate back to an already-completed publish call
- cancellation remains distinct from ordinary failure

Phase 2 intentionally does not provide universal handler timeout or automatic retry.

## 8. Event Observability

Phase 2 added safe Event lifecycle logging.

Diagnostic metadata includes where useful:

- EventBus start / close lifecycle
- Event accepted / dispatch start / dispatch completion
- Event type
- Event ID
- sanitized Event source
- handler identity
- handler / dispatch duration
- exception type for ordinary handler / dispatcher failures

Security / privacy boundary:

- no default `repr(event)`
- no full Event payload dump
- no subscriber exception message in default EventBus failure logs
- no dispatcher exception message in default EventBus failure logs
- tests verify known sensitive payload markers do not appear in captured logs
- Event source CR/LF is escaped before logging to reduce log-injection ambiguity

## 9. Composition Root Integration

Phase 2 gives the concrete EventBus one real runtime owner: the Python composition root.

Configuration:

```text
DCA_EVENT_BUS_QUEUE_CAPACITY=256
```

The value is operational configuration, not an architecture constant. Settings enforce a positive value.

Current runtime lifetime:

```text
create DeepSeekProvider
  -> establish Provider cleanup boundary
  -> create EventBus
  -> create Agent(provider)
  -> create WebSocketServer(agent)
  -> EventBus.start()
  -> WebSocketServer.run()
  -> EventBus.close()
  -> Provider.aclose()
```

Resource ownership tests verify:

- normal construction / startup / shutdown order
- server failure closes EventBus and Provider
- EventBus construction failure still closes an already-created Provider
- EventBus start failure still closes EventBus and Provider
- EventBus close failure does not prevent Provider cleanup

No speculative business subscriber was registered in Phase 2.

## 10. Desktop Protocol Boundary

The in-process Runtime Event model is separate from the Desktop WebSocket protocol.

Current Desktop protocol behavior remains:

```text
chat
response
error
```

A documented Desktop `event` message type does not imply that internal Runtime Events automatically cross the process boundary.

No Desktop Event Bridge was implemented in Phase 2 because there was no concrete acceptance requirement for one.

## 11. Phase 1 Vertical-Slice Preservation

Phase 2 preserved the verified request/response path:

```text
WPF
  -> WebSocket
  -> Python WebSocketServer
  -> Agent
  -> LLMProvider
  -> DeepSeekProvider
  -> DeepSeek API
  -> Python
  -> WPF
```

Phase 2 did not move Provider-specific logic into Agent, WebSocket, or UI layers.

## 12. Task / Commit Anchors

Confirmed Phase 2 anchors:

```text
c0ace0d Design Phase 2 event system
31734de Establish Phase 2 runtime event contracts
242ed9e Correct Phase 2 event bus overload architecture
55c8624 Implement Phase 2 event bus core
ad23a10 Add event bus lifecycle and failure isolation
5b161c1 Add event lifecycle observability
ccee378 Integrate event bus into runtime composition
```

The repository Git history is authoritative for the complete history.

## 13. Final Automated Acceptance

Project owner final Python quality gate on 2026-09-12:

```text
python -m pytest -q
-> 104 passed in 4.73s

python -m ruff check .
-> All checks passed!

python -m mypy src
-> Success: no issues found in 38 source files
```

C# build:

```text
N/A
```

Reason: Phase 2 did not modify C# source. The accepted Task 6 plan requires C# build only when C# source is affected.

## 14. Manual Runtime Acceptance

Real runtime regression was performed after the full Python quality gate.

Observed:

- Agent Core started successfully.
- EventBus logged startup with `queue_capacity=256`.
- WebSocket server listened on `127.0.0.1:8765`.
- WPF connected successfully.
- first real WPF request received a DeepSeek-backed response.
- second consecutive WPF request also received a DeepSeek-backed response.
- Python logged two successful `POST https://api.deepseek.com/chat/completions` HTTP 200 responses.
- runtime shutdown entered EventBus close.
- EventBus logged `event_bus_closing accepted_queue_size=0`.
- EventBus logged `event_bus_closed previous_state=CLOSING`.

Conclusion:

> The Phase 1 vertical slice remains operational while the Phase 2 EventBus is owned by the runtime composition root.

## 15. Observed Existing Shutdown Debt

During manual acceptance, closing the WPF client could produce:

```text
websockets.exceptions.ConnectionClosedError: no close frame received or sent
```

This occurred on the existing Desktop/WebSocket connection shutdown path before the Agent Core was stopped.

It is not an EventBus shutdown failure: the EventBus subsequently entered CLOSING and CLOSED successfully.

Track this as existing Desktop shutdown/disposal hardening debt rather than expanding Phase 2 scope.

## 16. Final Repository / Archive Hygiene

Final pre-documentation hygiene check:

- `git status`: clean
- `git diff --check`: clean
- `git ls-files .env`: no tracked `.env`
- ignored local/generated content includes `.env`, `.venv`, test/type/lint caches, logs, Python `__pycache__`, C# `.vs/bin/obj`, package metadata, and other generated outputs

Checkpoint/source archives must exclude:

- `.env`
- API keys / credentials
- caches
- logs
- generated build outputs not intentionally versioned
- `.git` if the project-source archive convention continues to omit it

## 17. Known Non-Goals / Deferred Event Features

Phase 2 intentionally does not include:

- Event persistence or replay
- wildcard subscriptions
- subscriber priority
- dynamic unsubscribe
- automatic Event retry
- universal handler timeout
- multiple dispatcher workers
- restart / supervision policy
- cross-process Event broker
- Desktop Event Bridge
- business-domain Events for Character / Memory / Perception / Situation / Attention / Behavior / Permission / Tools / Avatar / Voice

Add these later only when a concrete requirement justifies them.

## 18. Next Phase Entry

Next roadmap phase:

```text
Phase 3 - Character System
```

Phase 3 should begin with context recovery from:

1. `PROJECT_STATE.md`
2. `docs/PHASE_2_CHECKPOINT.md`
3. `ARCHITECTURE.md`
4. `ROADMAP.md`
5. Phase 2 Event design / architecture review / ADRs
6. current source and recent Git history

The Event System should be treated as stable infrastructure. Phase 3 should consume it only where a real Character-System event boundary is needed and should not redesign Phase 2 without a concrete architecture reason.
