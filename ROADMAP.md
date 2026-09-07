# Desktop Companion Agent Roadmap

> Re-baselined after the Phase 0 checkpoint on 2026-09-08.
>
> The original roadmap placed Desktop basics in Phase 1 and LLM integration later. During implementation, the Desktop/WebSocket vertical slice was intentionally pulled into Phase 0. The roadmap below reflects the actual repository state while preserving the long-term architecture direction.

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

Phase 0 deliberately ends with an echo Agent rather than a real LLM.

See:

- `PROJECT_STATE.md`
- `docs/PHASE_0_CHECKPOINT.md`

---

## Phase 1 - LLM Provider and Original MVP Completion

Status: **Next**

Goal:

Replace the echo Agent path with a provider-agnostic LLM path while keeping vendor-specific code outside the Agent Core.

Planned:

- Provider interface / contract
- DeepSeek provider adapter
- provider request / response boundary
- secure API-key loading through existing Settings
- timeout and cancellation handling
- provider failure -> protocol error behavior
- logging without leaking prompts/secrets unintentionally
- fake/mock provider tests
- real WPF -> Python -> DeepSeek -> WPF acceptance

Not included by default:

- Memory
- Perception
- Avatar
- Tools
- autonomous actions

---

## Phase 2 - Event System

Goal:

Establish the Event Bus / runtime event model so modules do not hard-call each other.

Planned:

- event envelope
- event routing
- subscriber boundaries
- event lifecycle / logging
- Desktop / runtime event bridge where needed

---

## Phase 3 - Character System

Goal:

Define stable character and user-context boundaries.

Planned:

- Identity
- Persona
- Speech Style
- Preferences
- Core Values
- User Profile boundary
- Prompt / context composition interfaces

Principle:

Character personality cannot override truth, permission, or security boundaries.

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

- Ollama
- LM Studio
- llama.cpp-compatible adapters
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
2. event boundaries
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
