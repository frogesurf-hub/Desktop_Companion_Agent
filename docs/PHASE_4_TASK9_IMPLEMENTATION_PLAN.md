# Desktop Companion Agent — Phase 4 Task 9 Implementation Plan

Status: Approved Implementation Baseline
Phase: 4 — Memory System
Task: 9 — WebSocket Memory Management Protocol
Repository baseline reviewed: `15b58b1 feat(memory): wire memory health runtime`

---

## 1. Task Goal

Task 9 exposes the existing Memory Governance capability through the Desktop/WebSocket boundary.

Before Task 9:

```text
Desktop
    ↓
WebSocket
    ↓
Agent
    ↓
Chat / Provider

Memory Governance
    ↓
available only inside Python runtime
```

After Task 9:

```text
Desktop
    ↓
WebSocket
    ↓
Runtime Message Router
    ├─ chat
    │    ↓
    │   Agent
    │
    └─ memory.*
         ↓
      Memory Protocol Handler
         ↓
      HealthAwareMemoryGovernanceService
         ↓
      MemoryGovernanceService
         ↓
      SQLiteMemoryRepository
```

Target Memory operations:

```text
memory.list
memory.inspect
memory.edit
memory.delete
memory.history
```

Task 9 creates a stable cross-language request/response capability for Memory Governance without exposing persistence internals.

---

## 2. Current Baseline

Task 8 completed:

```text
MemoryHealthTracker
├─ ResilientMemoryRetriever
├─ ResilientMemoryTurnLearner
└─ HealthAwareMemoryGovernanceService
```

The first two boundaries are wired into the live runtime.

`HealthAwareMemoryGovernanceService` exists and is tested but intentionally has no live runtime consumer yet.

Current WebSocket path:

```text
Desktop AgentClientService
    ↓
IAgentConnection
    ↓
WebSocketAgentConnection
    ↓
WebSocketServer
    ↓
Agent.process_message()
```

Current Python `WebSocketServer` therefore assumes that every valid protocol `Message` belongs to `Agent`.

Task 9 must remove that assumption without moving governance logic into `Agent` or transport code.

---

## 3. Accepted Architecture Decision

Task 9 introduces an explicit runtime request router.

Conceptually:

```text
WebSocketServer
transport only
    ↓
MessageProcessor
explicit request boundary
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

The router is a request/response application boundary.

It is **not** the EventBus.

This preserves ADR 0010:

```text
Event / notification
→ EventBus

Command / query / request
→ explicit capability boundary
```

The long-term decision is recorded separately in ADR 0021.

---

## 4. Protocol Envelope

Task 9 keeps the existing cross-language `Message` / `AgentMessage` envelope unchanged.

Memory protocol responses carry the originating request ID inside:

```text
payload.request_id
```

Example request:

```json
{
  "id": "request-message-id",
  "type": "memory.inspect",
  "timestamp": "2026-09-20T12:00:00+00:00",
  "source": "desktop",
  "payload": {
    "memory_id": "12345678-1234-5678-1234-567812345678"
  }
}
```

Example response:

```json
{
  "id": "response-message-id",
  "type": "memory.inspect.result",
  "timestamp": "2026-09-20T12:00:01+00:00",
  "source": "agent_core",
  "payload": {
    "request_id": "request-message-id",
    "memory": {}
  }
}
```

Reasons:

- preserves the existing Message / AgentMessage wire schema;
- gives Task 10 deterministic request/response correlation;
- does not require chat protocol migration;
- remains usable for concurrent Memory operations.

---

## 5. Request Types

### 5.1 `memory.list`

Request payload may be empty:

```json
{}
```

or contain optional filters:

```json
{
  "domain": "relationship",
  "scope": {
    "kind": "character",
    "character_id": "aria"
  }
}
```

Supported domain values:

```text
user_profile
working_context
episodic
relationship
```

Supported scopes:

```json
{
  "kind": "global_user"
}
```

or:

```json
{
  "kind": "character",
  "character_id": "aria"
}
```

The normal list protocol surface excludes entries whose latest revision is `DELETED`.

This does not erase the tombstone or change Governance persistence semantics.

### 5.2 `memory.inspect`

```json
{
  "memory_id": "12345678-1234-5678-1234-567812345678"
}
```

A directly inspected deleted Memory may return its tombstone state with:

```text
lifecycle = deleted
content = null
```

No deleted factual content is reconstructed.

### 5.3 `memory.edit`

```json
{
  "memory_id": "12345678-1234-5678-1234-567812345678",
  "content": "The user prefers C#."
}
```

Blank content is invalid.

The protocol delegates revision semantics to Governance.

### 5.4 `memory.delete`

```json
{
  "memory_id": "12345678-1234-5678-1234-567812345678"
}
```

The response may contain the resulting tombstone entry, whose content is `null`.

### 5.5 `memory.history`

```json
{
  "memory_id": "12345678-1234-5678-1234-567812345678"
}
```

Current delete semantics clear previous factual revisions before writing a content-free tombstone.

Therefore:

```text
history after delete
→ tombstone only
→ deleted factual content is not exposed
```

---

## 6. Response Types

Successful responses use operation-specific types:

```text
memory.list.result
memory.inspect.result
memory.edit.result
memory.delete.result
memory.history.result
```

Every success payload includes:

```json
{
  "request_id": "original-request-id"
}
```

A Memory governance entry serializes as:

```json
{
  "memory_id": "...",
  "domain": "user_profile",
  "scope": {
    "kind": "global_user",
    "character_id": null
  },
  "identity_key": "user_profile.preference.programming_language",
  "latest_revision": {
    "revision_number": 2,
    "content": "The user prefers C#.",
    "source": "user_edit",
    "lifecycle": "active",
    "recorded_at": "2026-09-20T12:00:00+00:00",
    "occurred_at": null
  }
}
```

`memory.list.result`:

```json
{
  "request_id": "...",
  "memories": []
}
```

`memory.inspect.result`, `memory.edit.result`, `memory.delete.result`:

```json
{
  "request_id": "...",
  "memory": {}
}
```

`memory.history.result`:

```json
{
  "request_id": "...",
  "memory_id": "...",
  "revisions": []
}
```

---

## 7. Serialization Boundary

Protocol serialization is explicit and does not expose Python dataclass internals.

The protocol handler serializes:

```text
Memory
MemoryScope
MemoryRevision
MemoryGovernanceEntry
```

into stable primitive payloads.

The Desktop must not depend on:

- Python Enum objects;
- UUID objects;
- dataclass field implementation;
- SQLAlchemy models;
- table names;
- transaction internals.

All timestamps are ISO-8601 strings.

All Enum values use their accepted `.value` representation.

---

## 8. Error Contract

Memory protocol errors continue to use the existing top-level message type:

```text
error
```

Payload:

```json
{
  "request_id": "original-request-id",
  "code": "MEMORY_NOT_FOUND",
  "message": "Memory does not exist."
}
```

Initial stable error codes:

```text
MEMORY_INVALID_REQUEST
MEMORY_NOT_FOUND
MEMORY_DELETED
MEMORY_INVALID_STATE
MEMORY_OPERATION_FAILED
```

Mapping:

```text
invalid / missing payload field
invalid UUID
invalid domain / scope
→ MEMORY_INVALID_REQUEST

MemoryNotFoundError
→ MEMORY_NOT_FOUND

MemoryDeletedError
→ MEMORY_DELETED

MemoryStateError
→ MEMORY_INVALID_STATE

unexpected infrastructure / persistence exception
→ MEMORY_OPERATION_FAILED
```

Unexpected infrastructure failures should pass through `HealthAwareMemoryGovernanceService` first so Governance health is degraded before safe protocol mapping.

Task 9 must not expose raw infrastructure exception messages.

---

## 9. Memory Protocol Handler Boundary

Introduce a dedicated Python Memory protocol handler.

Conceptual contract:

```text
Message
    ↓
MemoryProtocolHandler
    ↓
MemoryGovernance
    ↓
Message
```

The handler owns:

- supported `memory.*` dispatch;
- request payload validation;
- UUID/domain/scope conversion;
- governance-result serialization;
- safe error mapping;
- request correlation.

The handler does **not** own:

- SQL;
- revision creation;
- delete semantics;
- conflict resolution;
- retention;
- automatic learning;
- retrieval ranking;
- Character behavior;
- Tool permission.

It depends on the existing `MemoryGovernance` Protocol.

The live runtime injects `HealthAwareMemoryGovernanceService`.

---

## 10. Runtime Message Router Boundary

Initial routing table:

```text
chat
→ Agent

memory.list
memory.inspect
memory.edit
memory.delete
memory.history
→ MemoryProtocolHandler
```

Unsupported top-level types return a safe protocol error.

The router does not parse Memory payloads.

The router does not execute Governance.

The router does not use EventBus request/response.

It is the extension point for future explicit request capabilities only when those capabilities actually exist.

---

## 11. WebSocketServer Boundary

`WebSocketServer` remains transport-focused.

After Task 9:

```text
raw WebSocket frame
    ↓
Message.from_json()
    ↓
MessageProcessor.process_message()
    ↓
Message.to_json()
```

It should no longer require a concrete `Agent`.

A narrow protocol such as this is sufficient:

```python
class MessageProcessor(Protocol):
    async def process_message(
        self,
        message: Message,
    ) -> Message:
        ...
```

Invalid JSON, binary frames, and invalid envelope structure remain transport-owned by `WebSocketServer`.

---

## 12. Composition Root

Task 9C wires Governance into the live runtime for the first time.

Target composition:

```text
memory_repository
    ↓
MemoryGovernanceService
    ↓
HealthAwareMemoryGovernanceService
        ↑
shared MemoryHealthTracker

Agent
+
MemoryProtocolHandler
    ↓
RuntimeMessageRouter
    ↓
WebSocketServer
```

The same `MemoryHealthTracker` created in Task 8 remains authoritative for:

```text
RETRIEVAL
AUTOMATIC_LEARNING
GOVERNANCE
```

Task 9 must not create a second Governance health tracker.

---

## 13. Desktop Protocol Boundary

Task 9 defines Desktop-side protocol representation but does not implement the WPF management screen.

Existing Desktop layering remains:

```text
View
→ ViewModel
→ Application Service
→ IAgentConnection
→ WebSocket
```

Task 9 may add Desktop protocol DTOs/builders for:

```text
Memory request types
Memory response types
Memory entry payload
Memory revision payload
Memory scope payload
Memory protocol errors
```

Task 10 owns the actual WPF Memory-management workflow and UI state.

Task 9 must not move persistence or Governance business rules into C#.

---

## 14. Request Correlation Decision

Task 9 uses:

```text
request Message.id
→ response payload.request_id
```

It does not change the top-level `AgentMessage` schema.

This preserves backward compatibility while supporting deterministic Memory response correlation.

---

## 15. Task Breakdown

### Task 9A — Protocol Contract + Runtime Routing Foundation

Goals:

- accept ADR 0021;
- add ADR 0021 to ADR index;
- define `MessageProcessor` / routing boundary;
- introduce `RuntimeMessageRouter`;
- preserve existing chat behavior;
- ensure EventBus is not used for Memory RPC;
- update Task 8 plan status from checkpoint-pending to completed.

Expected files may include:

```text
docs/adr/0021-*.md
docs/adr/README.md
docs/PHASE_4_TASK8_IMPLEMENTATION_PLAN.md
src/agent_core/core/message_router.py
src/agent_core/tests/test_message_router.py
```

No Memory payload parsing yet.

Suggested checkpoint:

```text
feat(protocol): add runtime message routing boundary
```

### Task 9B — Python Memory Protocol Handler

Goals:

- implement the five Memory request types;
- validate payloads deterministically;
- serialize governance entries/revisions;
- map governance/domain/infrastructure failures to safe protocol errors;
- exclude deleted entries from normal list;
- preserve tombstone-safe inspect/history behavior;
- verify `request_id` on every result/error.

Expected files may include:

```text
src/agent_core/memory/protocol.py
src/agent_core/tests/test_memory_protocol.py
```

Suggested checkpoint:

```text
feat(memory): add memory governance protocol handler
```

### Task 9C — Runtime / WebSocket Integration

Goals:

- create `MemoryGovernanceService`;
- wrap it in `HealthAwareMemoryGovernanceService`;
- reuse Task 8's shared `MemoryHealthTracker`;
- construct `MemoryProtocolHandler`;
- construct `RuntimeMessageRouter`;
- make `WebSocketServer` depend on generic processor boundary;
- preserve chat round-trip behavior;
- add real WebSocket Memory integration tests.

Expected affected files:

```text
src/agent_core/main.py
src/agent_core/communication/websocket_server.py
src/agent_core/tests/test_main.py
src/agent_core/tests/test_websocket_server.py
```

Suggested checkpoint:

```text
feat(memory): wire websocket governance runtime
```

### Task 9D — Desktop Protocol Representation

Goals:

- add C# protocol constants / payload DTOs / parsers or equivalent;
- preserve existing `AgentMessage` envelope;
- support construction of the five request messages;
- support parsing successful Memory results and safe errors;
- do not build WPF Memory UI yet;
- keep persistence semantics out of Desktop code.

Expected area:

```text
src/Desktop/.../Protocol/
```

Task 10 may then add the application-service/ViewModel workflow that consumes these protocol contracts.

Suggested checkpoint:

```text
feat(desktop): add memory protocol contracts
```

### Task 9E — Cross-Boundary Acceptance + Documentation

Acceptance should verify:

```text
chat request
→ still works through router

memory.list
→ valid safe list response

memory.inspect
→ valid entry

memory.edit
→ durable USER_EDIT revision
→ result correlated to request

memory.delete
→ durable tombstone
→ deleted fact absent from normal list/retrieval

memory.history
→ allowed persisted history

bad UUID / bad payload
→ MEMORY_INVALID_REQUEST

missing Memory
→ MEMORY_NOT_FOUND

deleted edit
→ MEMORY_DELETED

invalid lifecycle
→ MEMORY_INVALID_STATE

unexpected persistence failure
→ MEMORY_OPERATION_FAILED
→ Governance health DEGRADED

same WebSocket connection
→ survives protocol-level Memory errors
```

Final gates:

```text
targeted pytest
full pytest
Ruff
mypy
git diff --check
dotnet build
staged review
```

---

## 16. Testing Strategy

Router tests verify:

```text
chat → Agent
memory.* → MemoryProtocolHandler
unsupported type → safe error
```

Protocol handler tests verify every request type and error mapping with a fake `MemoryGovernance`.

Governance integration tests use real `MemoryGovernanceService` + SQLite where durable semantics matter.

WebSocket integration tests use the real server/router over a local socket.

Desktop verification requires at minimum:

```text
dotnet build
```

Do not introduce a large new C# testing framework solely for Task 9 unless the implementation complexity justifies it.

---

## 17. Important Delete-Safety Rule

Current SQLite delete behavior is:

```text
delete existing MemoryRevision rows
→ append content-free DELETED tombstone
```

Task 9 must not weaken this.

Therefore:

```text
memory.history after delete
→ cannot reveal old factual content
```

The protocol must never reconstruct deleted content from logs, previous responses, identity keys, or inference.

---

## 18. Explicit Non-Goals

Task 9 does not implement:

- WPF Memory-management layout;
- Memory list ViewModel state;
- advanced search;
- pagination;
- bulk edit/delete;
- undo delete;
- restore deleted Memory;
- candidate review;
- Memory sync;
- EventBus Memory RPC;
- Tool permissions;
- background push updates;
- Memory-change events;
- protocol version negotiation;
- full generic RPC framework.

Task 10 owns the first WPF Memory-management experience.

---

## 19. Completion Criteria

Task 9 is complete when:

1. WebSocket transport no longer assumes every valid Message belongs to Agent.
2. Chat behavior remains intact.
3. Five Memory governance requests have stable message types.
4. Responses are correlated through `payload.request_id`.
5. List/inspect/edit/delete/history map to the existing Governance capability.
6. Protocol parsing validates UUID/domain/scope/content safely.
7. Domain errors map to stable Memory protocol error codes.
8. Infrastructure failures do not leak exception details.
9. Governance infrastructure failures still update Task 8 health.
10. Normal Memory list does not expose deleted entries.
11. Delete/history behavior cannot reveal deleted factual content.
12. EventBus is not used as an RPC mechanism.
13. Runtime uses the same shared Memory health tracker.
14. Desktop protocol representation matches Python wire shapes.
15. Task 10 can build UI without knowing Python persistence internals.
16. Full Python regression remains green.
17. Desktop build remains green.
18. Final documentation and staged diff are reviewed and pushed.

---

## 20. Planned Checkpoint Sequence

```text
Task 9A
feat(protocol): add runtime message routing boundary

Task 9B
feat(memory): add memory governance protocol handler

Task 9C
feat(memory): wire websocket governance runtime

Task 9D
feat(desktop): add memory protocol contracts

Task 9E
final acceptance/docs checkpoint if needed
```

---

## 21. Architecture Inputs

Task 9 is based on:

```text
ADR 0002
WebSocket Desktop/Core transport

ADR 0003
Layered Desktop client

ADR 0010
Events are facts; commands/requests remain explicit boundaries

ADR 0016
Memory domain/scope/lifecycle/revision semantics

ADR 0017
SQLite durable Memory source of truth

ADR 0018
Memory explicit failure-isolation boundaries

ADR 0020
Logical Memory identity key

ADR 0021
Explicit runtime routing for request/response capabilities
```

If implementation reveals a contradiction with the current repository, the repository and accepted owner decision take precedence over this plan.
