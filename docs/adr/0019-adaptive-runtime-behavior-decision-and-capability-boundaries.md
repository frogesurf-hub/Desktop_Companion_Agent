# ADR 0019 - Adaptive Runtime Behavior Uses an Explicit Decision Boundary and Isolated Capabilities

Status: Accepted

Date: 2026-09-15

## Context

The long-term Desktop Companion Agent is intended to remain present on the desktop rather than acting only as a conventional chat window.

The intended product direction includes:

- a lightweight desktop-presence Avatar;
- idle and proactive Character behavior;
- optional voice;
- cloud and local AI capabilities;
- future perception of user/system state;
- graceful behavior under changing machine load.

Without an explicit boundary, future Behavior logic could directly start models, manipulate Avatar rendering, invoke TTS, inspect resources, or bypass Permission.

That would couple Character/Behavior intent to execution mechanics and could turn one module into a global orchestrator.

The project therefore needs to separate:

```text
what the companion wants to do
what the runtime currently allows
how the selected capability executes it
```

## Decision

### 1. Behavior lifecycle

Future proactive behavior follows the conceptual lifecycle:

```text
Behavior Proposal
    -> Admission
    -> Preparation
    -> Final Check
    -> Execution
```

A Proposal expresses desired behavior but produces no user-visible effect by itself.

Admission decides whether preparation is allowed.

Preparation obtains required outputs/resources, such as LLM text, TTS audio, or Avatar motion readiness.

Final Check allows the runtime to reject or alter behavior when user/system state changed during preparation.

Execution is the point where visible/audible behavior occurs.

### 2. Unified Decision Layer

A future Unified Decision Layer owns runtime admission decisions.

It may consider inputs such as:

- user activity/interruptibility;
- Situation and Attention output;
- capability availability;
- network availability;
- system resource availability;
- behavior priority;
- cooldown or timing state.

Its result may include:

```text
ALLOW
DEGRADE
DEFER
REJECT
```

The Decision Layer decides policy.

It does not execute capabilities.

It must not directly:

- call an LLM provider;
- load or run TTS;
- play Avatar motion;
- mutate Memory;
- execute Tools;
- grant Permission.

Sensitive actions still pass through the independent Permission boundary.

### 3. LLM direction

The default long-term LLM direction is:

```text
Cloud First
Local Fallback
```

When cloud intelligence is unavailable, local LLM use is conditional on future runtime admission/resource policy.

If local execution is not admissible, a proactive behavior may degrade, defer, or be rejected.

Local LLM is not assumed to be a mandatory resident capability.

Future user settings may expose different routing policies, but Cloud First is the default product direction accepted by this ADR.

### 4. TTS direction

The current product direction is:

```text
Local TTS -> default direction
Cloud TTS -> required extension option
```

No concrete TTS engine is selected by this ADR.

TTS is not assumed to be permanently loaded merely because the application is running.

Its concrete loading/residency lifecycle belongs to the future Voice phase.

### 5. Avatar direction

The first embodiment direction uses two Live2D presentation modes:

```text
Desktop Presence -> Chibi/Q-version Live2D
Full Interaction -> Full Live2D
```

Agent Core does not depend on one concrete Avatar representation.

Avatar rendering should support dynamic frame-rate/resource behavior based on presentation needs.

Low-motion idle states may use lower rendering cost than visually complex actions.

Exact FPS values and rendering technology are deferred to the Avatar phase.

3D remains a future adapter/direction and is not selected by this ADR.

### 6. Capability isolation

Heavy or replaceable capabilities such as future local LLM, local TTS, Vision, and Avatar implementations must remain behind explicit capability boundaries.

This ADR does not require a specific process/worker/IPC implementation.

Isolation means the Core architecture must not require future heavy runtimes to become direct, permanent dependencies of Character, Memory, Situation, Attention, or Behavior domain logic.

### 7. Resource insufficiency is a normal runtime outcome

A behavior being rejected because resources/capabilities are unavailable is not inherently a system failure.

For example:

```text
Cloud unavailable
+ Local LLM not admissible
-> REJECT proactive dialogue
```

may represent correct operation.

Runtime/business outcomes must remain distinguishable from actual implementation failures.

## Rationale

- keeps Behavior intent separate from runtime execution;
- avoids a universal orchestrator that both decides and performs all work;
- preserves Intent != Permission;
- allows the companion to yield to the user's foreground workload;
- allows cloud/local capability routing to evolve independently;
- avoids coupling Avatar, TTS, local LLM, and Memory;
- supports graceful degradation rather than forcing every proactive behavior to execute;
- allows future resource policy to be based on measured capability requirements rather than premature fixed percentages.

## Consequences

- future Behavior Engine should emit proposals/semantic intent rather than directly performing every capability action;
- Situation/Attention may provide decision inputs without becoming execution layers;
- future resource/state monitoring may feed the Decision Layer;
- local LLM fallback requires explicit admission before startup/use;
- Voice must preserve local/cloud provider extensibility;
- Avatar implementation must preserve Chibi/Full presentation separation and dynamic rendering direction;
- future high-load conditions may reduce, defer, or reject optional proactive behavior;
- Memory remains an input/context system rather than a runtime resource controller;
- Permission remains independent and cannot be replaced by Admission.

## Explicit Non-Decisions

This ADR does not decide:

- concrete Decision Layer classes/APIs;
- resource-monitor implementation;
- CPU/RAM/GPU/VRAM thresholds;
- concrete local LLM model/runtime;
- concrete TTS engine;
- TTS loading timeout/residency policy;
- Cloud TTS provider;
- exact Avatar FPS values;
- Live2D SDK/rendering implementation;
- 3D engine/runtime;
- heavy-capability process topology;
- subprocess/IPC/gRPC/WebSocket choice for heavy capabilities;
- exact user settings UI;
- exact routing algorithms beyond the accepted Cloud-First default;
- Perception implementation.

Those decisions belong to their owning future phases and require real implementation measurements.

## Relationship to Existing ADRs

This decision preserves and complements:

- ADR 0004 - Local-first Provider abstraction;
- ADR 0005 - Intent is not Permission;
- ADR 0006 - Real and fictional state separation;
- ADR 0010 - Runtime Events are facts; commands and requests remain explicit boundaries;
- ADR 0014 - Character consumes prepared user context while Memory owns persistence/retrieval.

This ADR does not change the current Phase 3 Provider contract, EventBus semantics, Character contract, Clock semantics, or current runtime request path.

Phase 4 records this decision for compatibility but does not implement the Unified Decision Layer, Avatar runtime, TTS runtime, or Local LLM fallback.
