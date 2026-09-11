# Desktop Companion Agent Roadmap

> Re-baselined after the Phase 2 checkpoint on 2026-09-12.
>
> Phase 0 established the Desktop/WebSocket cross-language foundation. Phase 1 completed the original AI MVP with a provider-neutral DeepSeek path. Phase 2 established the runtime Event System. Phase 3 is now the active next phase.

## Phase 0 - Engineering Foundation and Cross-Language Vertical Slice

Status: **Complete**

Completed:

- [x] project structure and architecture documentation
- [x] technology selection
- [x] development environment
- [x] Git workflow
- [x] Python project/package configuration
- [x] pytest / Ruff / mypy baseline
- [x] runtime Settings system
- [x] logging / observability foundation
- [x] unified JSON message envelope
- [x] Python WebSocket server
- [x] protocol error handling
- [x] C# WebSocket client abstraction
- [x] C# protocol model
- [x] independent Desktop receive loop
- [x] ConnectionProbe
- [x] WPF ViewModel / Application Service layering
- [x] real WPF -> Python -> Agent -> WPF round trip

See:

- `PROJECT_STATE.md`
- `docs/PHASE_0_CHECKPOINT.md`

---

## Phase 1 - LLM Provider and Original MVP Completion

Status: **Complete**

Completed:

- [x] provider-neutral async `LLMProvider` contract
- [x] immutable Provider request / response models
- [x] deterministic fake Provider test infrastructure
- [x] provider-neutral error hierarchy
- [x] DeepSeek adapter through `AsyncOpenAI`
- [x] configurable DeepSeek model / timeout / thinking settings
- [x] explicit non-streaming Provider path
- [x] timeout and cancellation semantics
- [x] SDK automatic retries disabled
- [x] Provider failure -> safe Desktop protocol error mapping
- [x] composition-root Provider construction / cleanup
- [x] secure API-key use through `SecretStr` and local `.env`
- [x] real ConnectionProbe -> Python -> DeepSeek -> ConnectionProbe acceptance
- [x] real WPF -> Python -> DeepSeek -> WPF acceptance
- [x] deliberate real authentication-failure acceptance
- [x] final full Python quality gate

Final Python acceptance:

```text
66 pytest tests passed
Ruff passed
mypy passed on 28 source files
```

See:

- `docs/PHASE_1_CHECKPOINT.md`

---

## Phase 2 - Event System

Status: **Complete**

Goal achieved:

Establish a durable in-process runtime Event model / EventBus so future modules can communicate through explicit Event boundaries instead of direct concrete-module calls.

Completed:

- [x] immutable `RuntimeEvent` metadata foundation
- [x] UUID Event identity
- [x] timezone-aware UTC occurrence timestamps
- [x] source / correlation / causation metadata
- [x] narrow `EventPublisher` capability
- [x] asynchronous subscriber contract
- [x] bounded in-process EventBus
- [x] exact-type routing
- [x] queue-admission-order dispatch
- [x] fail-fast `EventBusFullError` overload admission
- [x] explicit EventBus lifecycle
- [x] graceful close / accepted-queue drain
- [x] concurrent sibling subscribers for one Event
- [x] ordinary subscriber failure isolation
- [x] cancellation semantics / task cleanup
- [x] safe Event lifecycle observability
- [x] sensitive-payload logging regression tests
- [x] composition-root EventBus ownership
- [x] configurable queue capacity through existing Settings
- [x] Provider cleanup protection across EventBus/runtime failures
- [x] preservation of Phase 1 WPF -> Python -> DeepSeek -> WPF path
- [x] final full Python quality gate

Final Python acceptance:

```text
104 pytest tests passed
Ruff passed
mypy passed on 38 source files
```

Manual acceptance:

- EventBus startup observed with queue capacity 256
- two consecutive real WPF -> DeepSeek responses succeeded
- EventBus closing / closed lifecycle observed during runtime shutdown

Not included by design:

- Character / Memory / Perception / Situation / Attention / Behavior business logic
- Permission / Tool business logic
- Avatar / Voice
- Desktop Event Bridge
- Event persistence / replay
- wildcard subscriptions
- subscriber priority
- dynamic unsubscribe
- automatic Event retries
- multiple dispatcher workers
- restart / supervision policy

See:

- `docs/PHASE_2_CHECKPOINT.md`
- `docs/PHASE_2_EVENT_SYSTEM_DESIGN.md`
- `docs/PHASE_2_ARCHITECTURE_REVIEW.md`
- `docs/PHASE_2_TASK_PLAN.md`
- ADR 0010 / 0011 / 0012

---

## Phase 3 - Character System

Status: **Next**

Goal:

Define stable character and user-context boundaries on top of the verified Provider/WebSocket/EventBus runtime.

Planned:

- Identity
- Persona
- Speech Style
- Preferences
- Core Values
- User Profile boundary
- Prompt / context composition interfaces

Principle:

Character personality cannot override truth, permission, security, or factual-state boundaries.

---

## Phase 4 - Memory System

Goal:

Introduce separated memory domains without allowing temporary or fictional state to contaminate facts.

Planned memory domains:

- User Profile
- Working Context
- Episodic Memory
- Long-term Memory
- Relationship Memory
- Today Memory
- Fictional Ephemeral State

---

## Phase 5 - Situation Engine

Goal:

Convert low-level events into semantic situations.

Example:

```text
Unity active
+ source modified
+ compile failure
+ repeated retry
-> user is debugging a Unity problem
```

---

## Phase 6 - Attention Engine

Goal:

Decide whether the companion should ignore, notice, speak, wait, or escalate.

Planned factors:

- importance
- novelty
- repetition
- cooldown
- interruptibility
- current user context

Target:

Active without becoming intrusive.

---

## Phase 7 - Perception Layer

Goal:

Build event-driven desktop context acquisition.

Planned:

- active application / window
- process state
- file changes
- system state
- time / network context
- App Adapters
- UI Automation where needed
- screenshot / vision only as fallback

Priority:

```text
App Adapter
-> UI Automation / native metadata
-> process/file/system events
-> OCR
-> visual screenshot understanding
```

---

## Phase 8 - Behavior Engine and Internal State

Goal:

Turn situation + attention + character + state into behavior.

Planned:

- Mood
- Energy
- Curiosity
- Social Desire
- relationship state
- speak / silence / wait
- semantic motion / expression requests

---

## Phase 9 - Avatar / Embodiment

Planned:

- Live2D first
- semantic motion commands
- expression commands
- future VRM / 3D adapter

Principle:

LLM / Behavior Engine emits semantic intent, not raw Live2D parameters.

---

## Phase 10 - Voice

Planned:

- TTS
- STT
- emotion-aware voice parameters
- interruption / playback lifecycle

---

## Phase 11 - Desktop Interaction

Planned:

- drag
- throw
- click reactions
- idle reactions
- desktop presence behavior

---

## Phase 12 - Permission and Tools

Goal:

Expose useful actions without allowing character intent to bypass authorization.

Low-risk tools:

- search
- file lookup
- open application

Advanced:

- UI Automation
- Computer Use

Core rule:

```text
Intent != Permission
```

---

## Phase 13 - Local AI and Fallback Runtime

Planned:

- local-provider adapters
- Local / Hybrid / Cloud routing
- graceful cloud failure / fallback

---

## Phase 14 - Life System

Planned:

- daily state
- mood drift
- relationship evolution
- habit learning
- lightweight fictional daily-life flavor

Fictional state remains isolated from factual memory and tool reasoning.

---

## Development Priority

Prefer:

1. stable architecture
2. explicit Event / command / permission boundaries
3. memory correctness
4. situation / attention / proactivity
5. perception
6. behavior
7. embodiment and polish

Avoid prematurely prioritizing:

- complex animations
- visual polish
- unrestricted computer control
- hard coupling to one model provider

The project should build a stable companion runtime before building spectacle around it.
