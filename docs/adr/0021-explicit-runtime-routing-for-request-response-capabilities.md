# ADR 0021 - Explicit Runtime Routing for Request/Response Capabilities

Status: Accepted

Date: 2026-09-20

## Context

The current Desktop Companion Agent uses one shared WebSocket transport.

Before Phase 4 Task 9, every valid protocol `Message` received by
`WebSocketServer` is passed directly to:

```text
Agent.process_message()
```

This is sufficient while the only application request is:

```text
chat
```

Phase 4 Task 9 introduces explicit Memory Governance requests:

```text
memory.list
memory.inspect
memory.edit
memory.delete
memory.history
```

These operations are not chat behavior.

They:

- query or mutate factual Memory;
- require deterministic request/response semantics;
- require stable error mapping;
- depend on Memory Governance rather than Character/Provider behavior;
- must not be hidden behind EventBus subscriber behavior.

If `Agent` becomes the dispatcher for all future request types, it would
gradually become a transport/application service locator for Memory,
Tools, Permission, and other capabilities.

If `WebSocketServer` directly dispatches Memory operations, transport
code would become coupled to application-domain behavior.

If EventBus is used as RPC, request/response completion and failure
semantics would violate ADR 0010.

## Decision

Introduce an explicit runtime request router between WebSocket transport
and application capabilities.

Conceptually:

```text
WebSocketServer
    ↓
MessageProcessor
    ↓
RuntimeMessageRouter
    ├─ chat
    │    ↓
    │   Agent
    │
    └─ memory.*
         ↓
      MemoryProtocolHandler
```

`WebSocketServer` owns:

```text
WebSocket connection lifecycle
raw frame handling
Message envelope parsing
transport-level errors
Message serialization
```

`RuntimeMessageRouter` owns:

```text
request-type routing
unsupported application request handling
```

Capability handlers own their own protocol/application semantics.

For Task 9:

```text
chat
→ Agent

memory.*
→ MemoryProtocolHandler
```

The router does not execute Memory Governance itself.

The Memory protocol handler depends on the explicit `MemoryGovernance`
application capability.

The EventBus remains reserved for facts and notifications.

It is not used to implement Memory request/response operations.

## Message Correlation

Task 9 preserves the existing top-level cross-language Message envelope.

Memory responses correlate to requests through:

```text
request Message.id
→ response payload.request_id
```

This avoids a breaking envelope migration while still supporting
deterministic concurrent Memory requests.

A future protocol redesign may introduce a generic top-level reply field,
but Task 9 does not require one.

## Consequences

Positive consequences:

- `Agent` remains focused on conversational behavior;
- `WebSocketServer` remains transport-focused;
- Memory Governance remains an explicit application capability;
- request completion/failure semantics remain deterministic;
- EventBus does not become a hidden RPC system;
- future explicit capability families have a clear routing extension point;
- Task 10 can consume Memory protocol without persistence knowledge.

Trade-offs:

- one additional runtime routing layer is introduced;
- WebSocket construction must inject a message processor/router instead of assuming a concrete Agent;
- protocol-level tests must verify both routing and capability handlers;
- Desktop request correlation must understand `payload.request_id`.

## Routing Scope

This ADR does not create a generic plugin router or universal RPC framework.

Only implemented capability families are routed.

Task 9 initially requires:

```text
chat
memory.*
```

Future families such as:

```text
tool.*
permission.*
runtime.*
```

require their own accepted contracts before being added.

## Error Ownership

Transport errors remain transport-owned:

```text
binary frame
invalid JSON
invalid Message envelope
```

Application protocol errors remain capability-owned:

```text
invalid Memory UUID
Memory not found
Memory deleted
invalid Memory state
Memory infrastructure failure
```

The router must not translate domain-specific Memory exceptions.

## Relationship to EventBus

This decision explicitly preserves ADR 0010:

```text
Fact / notification
→ EventBus

Command / query / request
→ explicit request/capability boundary
```

Memory Governance requests therefore do not become EventBus RPC.

A future Memory change event may be published after a successful governance operation if a real asynchronous consumer requires it.

Task 9 does not invent that event preemptively.

## Explicit Non-Decisions

This ADR does not decide:

- WPF Memory-management UI layout;
- Tool routing contracts;
- Permission routing contracts;
- protocol version negotiation;
- streaming responses;
- generic JSON-RPC adoption;
- server push semantics;
- Event persistence;
- Memory change events;
- remote authentication.

## Relationship to Existing ADRs

This decision extends and preserves:

- ADR 0002 - WebSocket Desktop/Core transport;
- ADR 0003 - layered Desktop client;
- ADR 0010 - Events are facts; commands/requests remain explicit boundaries;
- ADR 0018 - Memory explicit failure-isolated boundaries.

It does not supersede those decisions.
