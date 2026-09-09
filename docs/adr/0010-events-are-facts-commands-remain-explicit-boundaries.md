# ADR 0010 - Runtime Events Are Facts; Commands and Requests Remain Explicit Boundaries

Status: Accepted

Date: Phase 2 design baseline

## Context

Phase 2 introduces a runtime Event System so future Companion modules can communicate without hard-calling concrete consumers.

The long-term runtime will contain modules such as Perception, Situation, Attention, Behavior, Memory, Permission, Tools, Voice, and Avatar. These modules need decoupled notification of facts, but they will also contain operations that require a result, authorization, capability ownership, or explicit completion semantics.

A common failure mode in event-driven architectures is to route every interaction through an Event Bus. Commands then become disguised as events, return values become hidden asynchronous state, and operational dependencies become harder to reason about.

Phase 1 already established stable explicit request/capability boundaries such as:

```text
WebSocketServer
    -> Agent.process_message()
    -> LLMProvider.generate()
```

There is no product requirement to replace that working path merely to make the architecture uniformly event-based.

## Decision

Runtime Events represent facts or notifications that have already occurred.

Operations that ask something to happen, require a return value, require authorization, query state, or depend on defined completion/failure semantics remain explicit command/request/interface/capability boundaries.

Conceptually:

```text
Fact / Notification
    -> Event System

Command / Request / Capability
    -> Explicit interface or service boundary
```

The Event Bus is therefore not a universal service locator, workflow engine, permission system, or replacement for normal dependency injection.

The Phase 1 chat/Provider path remains an explicit request/response path in Phase 2.

Future modules may publish facts produced by that path, but those facts do not replace the operation that produced them unless a later requirement and architecture decision explicitly redesign the workflow.

## Rationale

- preserves clear return-value and failure semantics for operations that need them;
- prevents hidden temporal coupling through event-based pseudo-commands;
- keeps permission separate from intent and notification;
- preserves stable Phase 1 boundaries;
- lets Events remain simple, decoupled facts;
- makes module dependencies easier to test and reason about;
- avoids turning the Event Bus into a global service locator.

## Consequences

- future producers publish Events for facts/notifications;
- future consumers do not rely on Event subscriber return values;
- explicit capability interfaces continue to be used for Provider calls, permission checks, Tool execution, state queries, and similar operations;
- architecture documentation must avoid wording that implies all module communication is Event Bus communication;
- Event System tests do not need to model request/response workflows;
- future workflow orchestration, if needed, requires its own design rather than being hidden inside Event routing.

## Explicit Non-Decisions

This ADR does not decide:

- concrete future Character/Memory/Perception/Situation/Attention/Behavior Event types;
- Tool or Permission contracts;
- workflow engine design;
- Desktop Event Bridge semantics;
- Event persistence/replay;
- streaming Provider behavior.

## Relationship to Existing ADRs

This decision preserves and complements:

- ADR 0002 - WebSocket Desktop/Core transport;
- ADR 0004 - Local-first runtime and provider abstraction;
- ADR 0005 - Intent is not Permission;
- ADR 0006 - Real and fictional state separation;
- ADR 0007 - Async non-streaming Provider contract.

It does not supersede those decisions.
