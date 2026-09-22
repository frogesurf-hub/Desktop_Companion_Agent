# Desktop Companion Agent — Phase 4 Task 10 Implementation Plan

Status: Approved Implementation Baseline
Phase: 4 — Memory System
Task: 10 — Simple WPF Memory Management UI
Repository baseline reviewed: `0bd1812 test(memory): add websocket governance acceptance`

---

## 1. Task Goal

Task 10 turns the Memory Governance protocol completed in Task 9 into a minimal, user-facing WPF management experience.

Before Task 10:

```text
Python Memory Governance
        ↓
WebSocket Memory Protocol
        ↓
Desktop protocol models/builders/parsers
        ↓
no normal-user Memory UI
```

After Task 10:

```text
User
  ↓
WPF Memory View
  ↓
Memory ViewModel
  ↓
Memory Application Service
  ↓
Desktop request/response correlation
  ↓
Task 9 MemoryProtocol
  ↓
WebSocket
  ↓
Python Memory Governance
  ↓
SQLite
```

The first UI must let the user:

```text
list Memory
inspect Memory
edit Memory
delete Memory
view Memory history
see truthful failure state
distinguish empty Memory from failed Memory access
```

The purpose is governance and transparency.

Visual polish is secondary.

---

## 2. Current Repository Baseline

Task 9 completed:

```text
ab0e083 feat(protocol): add runtime message routing boundary
b4844ab feat(memory): add memory governance protocol handler
66a51e3 feat(memory): wire websocket governance runtime
c0c5ecd feat(desktop): add memory protocol contracts
c8cc364 fix(memory): reject incompatible memory list filters
0bd1812 test(memory): add websocket governance acceptance
```

Current Python runtime path:

```text
WebSocketServer
    ↓
RuntimeMessageRouter
    ├─ chat
    │   ↓
    │  Agent
    │
    └─ memory.*
        ↓
       MemoryProtocolHandler
        ↓
       HealthAwareMemoryGovernanceService
        ↓
       MemoryGovernanceService
        ↓
       SQLiteMemoryRepository
```

Current Desktop path:

```text
MainWindow
    ↓
MainWindowViewModel
    ↓
IAgentClientService
    ↓
AgentClientService
    ↓
IAgentConnection
    ↓
WebSocketAgentConnection
```

Current Desktop Memory protocol already supports:

```text
memory.list
memory.inspect
memory.edit
memory.delete
memory.history
```

and:

```text
memory.list.result
memory.inspect.result
memory.edit.result
memory.delete.result
memory.history.result
error
```

Task 10 must consume these existing contracts rather than inventing a second protocol.

---

## 3. Critical Precondition — Request/Response Correlation

The current Desktop receive loop is chat-oriented.

Conceptually:

```text
Receive AgentMessage
    ↓
MessageReceived event
    ↓
MainWindowViewModel
    ↓
payload["message"]
```

That assumption is no longer sufficient because Task 9 responses include:

```text
memory.list.result
memory.inspect.result
memory.edit.result
memory.delete.result
memory.history.result
error
```

These responses do not belong in the chat transcript.

Task 9 already established correlation:

```text
request AgentMessage.Id
    ↓
response payload.request_id
```

Task 10 must make the Desktop actually use this correlation before building the Memory UI.

This is Task 10A.

---

## 4. Accepted Desktop Architecture

Task 10 keeps the existing Desktop layering.

Target:

```text
MainWindow / Memory UI
        ↓
MemoryManagementViewModel
        ↓
IMemoryClientService
        ↓
MemoryClientService
        ↓
IAgentClientService request/response capability
        ↓
IAgentConnection
        ↓
WebSocketAgentConnection
        ↓
Task 9 Memory protocol
```

Chat remains:

```text
MainWindowViewModel
        ↓
IAgentClientService.SendChatAsync()
        ↓
WebSocket

unsolicited / chat response
        ↓
MessageReceived event
        ↓
chat transcript
```

Memory requests become:

```text
MemoryClientService
        ↓
IAgentClientService.SendRequestAsync()
        ↓
request ID registered
        ↓
WebSocket send
        ↓
response received
        ↓
payload.request_id matched
        ↓
waiting request completed
```

This preserves the current transport abstraction.

---

## 5. Task 10A — Desktop Request/Response Correlation

### 5.1 Goal

Add a generic request/response capability to the Desktop client service without breaking existing chat events.

Required behavior:

```text
SendRequestAsync(request)
    ↓
register pending request by request.Id
    ↓
send through IAgentConnection
    ↓
ReceiveLoop receives AgentMessage
    ↓
if payload.request_id matches pending request
    → complete that request
else
    → MessageReceived event
```

### 5.2 Why This Belongs in `AgentClientService`

`WebSocketAgentConnection` should remain transport-only.

It owns:

```text
connect
disconnect
send frame
receive frame
JSON AgentMessage serialization/deserialization
```

It should not know:

```text
request_id
Memory result types
chat semantics
pending request tables
```

Correlation is an application-client responsibility.

### 5.3 Proposed Interface Change

Modify:

```text
ApplicationServices/IAgentClientService.cs
```

Add a capability conceptually equivalent to:

```csharp
Task<AgentMessage> SendRequestAsync(
    AgentMessage request,
    CancellationToken cancellationToken = default);
```

Exact implementation may evolve during Task 10A.

Existing:

```csharp
SendChatAsync(...)
```

remains.

### 5.4 Pending Request State

`AgentClientService` may maintain:

```text
request_id
→ TaskCompletionSource<AgentMessage>
```

Required semantics:

```text
matched response
→ complete exactly one pending request

unknown request_id
→ do not crash receive loop

duplicate response
→ do not complete another operation

disconnect
→ pending requests must not hang forever

receive failure
→ pending requests must fail truthfully
```

The exact collection/thread-safety mechanism belongs to implementation.

### 5.5 Correlation Error Boundary

A response is correlatable only if:

```text
payload.request_id
```

is present and identifies a currently pending request.

Chat responses continue through `MessageReceived`.

Task 10A must not classify messages solely by:

```text
message.Type == "error"
```

because Memory errors are correlated request responses.

### 5.6 Capability Increment

Before Task 10A:

```text
Desktop can send Memory requests
but has no deterministic way to await the matching response
```

After Task 10A:

```text
Desktop application code
→ can send one explicit request
→ await its exact response
→ without polluting chat handling
```

### 5.7 Acceptance

Verify:

```text
chat response
→ still reaches MessageReceived

memory result with matching request_id
→ completes awaiting request
→ does not enter chat event

memory error with matching request_id
→ completes awaiting request
→ caller can parse error

unmatched response
→ does not corrupt another pending request

disconnect / receive failure
→ pending request does not hang indefinitely
```

Suggested checkpoint:

```text
feat(desktop): add correlated agent requests
```

---

## 6. Task 10B — Memory Application Service

### 6.1 Goal

Create a typed Desktop application service above Task 9 protocol DTOs.

Suggested boundary:

```text
IMemoryClientService
MemoryClientService
```

It converts UI intentions into Memory protocol operations.

### 6.2 Responsibilities

The service should expose operations conceptually equivalent to:

```text
ListAsync(...)
InspectAsync(memoryId)
EditAsync(memoryId, content)
DeleteAsync(memoryId)
GetHistoryAsync(memoryId)
```

It owns:

```text
request construction
SendRequestAsync
response type verification
MemoryProtocol parser calls
Memory protocol error parsing
stable Desktop-facing failure representation
```

It does not own:

```text
Memory conflict rules
revision creation
delete semantics
retention
persistence
SQLite
Python lifecycle rules
```

### 6.3 Use Existing Task 9 Protocol

Use:

```text
MemoryProtocol.CreateListRequest
MemoryProtocol.CreateInspectRequest
MemoryProtocol.CreateEditRequest
MemoryProtocol.CreateDeleteRequest
MemoryProtocol.CreateHistoryRequest

MemoryProtocol.ParseListResult
MemoryProtocol.ParseInspectResult
MemoryProtocol.ParseEditResult
MemoryProtocol.ParseDeleteResult
MemoryProtocol.ParseHistoryResult
MemoryProtocol.ParseError
```

Do not duplicate JSON construction in the ViewModel.

### 6.4 Desktop Failure Boundary

Task 9 stable error codes:

```text
MEMORY_INVALID_REQUEST
MEMORY_NOT_FOUND
MEMORY_DELETED
MEMORY_INVALID_STATE
MEMORY_OPERATION_FAILED
```

Task 10 should preserve these as typed or structured application failures.

The ViewModel should not parse raw JSON error payloads.

### 6.5 Domain/Scope Client Validation

Python remains authoritative for domain/scope invariants.

Current Desktop `MemoryProtocol.CreateListRequest()` validates domain and scope individually.

Task 10 may add matching early validation for:

```text
USER_PROFILE + CHARACTER     → invalid
WORKING_CONTEXT + CHARACTER  → invalid
EPISODIC + CHARACTER         → invalid
RELATIONSHIP + GLOBAL_USER   → invalid
```

This is a client usability optimization, not a replacement for server validation.

### 6.6 Capability Increment

Before Task 10B:

```text
Desktop has raw Memory protocol builders/parsers
```

After Task 10B:

```text
Desktop has an application-level Memory API
that ViewModels can consume without JsonObject knowledge
```

Suggested checkpoint:

```text
feat(desktop): add memory application service
```

---

## 7. Task 10C — Memory ViewModel State

### 7.1 Goal

Introduce a dedicated presentation model for Memory governance rather than adding all Memory state directly into `MainWindowViewModel`.

Suggested boundary:

```text
MemoryManagementViewModel
```

Exact naming may change after implementation review.

### 7.2 Core State

The ViewModel should represent at least:

```text
IsLoading
IsBusy
StatusMessage
ErrorMessage

Memories
SelectedMemory
SelectedMemoryContent

History
IsHistoryVisible / equivalent
```

The UI must distinguish:

```text
Loading
Loaded
Empty
Operation in progress
Operation succeeded
Operation failed
Memory unavailable / operation failed
```

### 7.3 Selection Behavior

Conceptual flow:

```text
load list
    ↓
user selects Memory
    ↓
inspect request
    ↓
SelectedMemory updated
```

The list may already contain the latest revision, but explicit inspect remains the governance detail operation and preserves a clean protocol path.

### 7.4 Edit Behavior

Conceptual flow:

```text
selected Memory
    ↓
user edits content
    ↓
EditAsync
    ↓
server commits USER_EDIT revision
    ↓
returned MemoryEntryPayload
    ↓
detail refresh
    ↓
list refresh/update
```

The ViewModel must not fabricate revision numbers or lifecycle changes.

### 7.5 Delete Behavior

Conceptual flow:

```text
selected Memory
    ↓
user confirms delete
    ↓
DeleteAsync
    ↓
server returns tombstone
    ↓
normal list refresh
    ↓
deleted Memory disappears
```

The Desktop must not locally pretend deletion succeeded before the server response.

### 7.6 History Behavior

Conceptual flow:

```text
selected Memory
    ↓
GetHistoryAsync
    ↓
display returned revisions
```

Task 9 delete safety remains authoritative:

```text
deleted factual content
→ must not reappear through history
```

The Desktop must not cache and reconstruct deleted factual history as a governance feature.

### 7.7 Capability Increment

Before Task 10C:

```text
Memory application operations exist
but no presentation state coordinates them
```

After Task 10C:

```text
Memory UI state is explicit, bindable, and truthful
```

Suggested checkpoint:

```text
feat(desktop): add memory management view model
```

---

## 8. Task 10D — Simple WPF Memory Management View

### 8.1 Goal

Build the first usable WPF Memory-management surface.

The existing application currently has one simple chat window.

Task 10 should preserve chat and add Memory management without redesigning the entire desktop application.

### 8.2 Minimal Layout Direction

A simple first layout may use tabs:

```text
┌─────────────────────────────────────────────┐
│ Agent Core: Connected            [Connect]  │
├─────────────────────────────────────────────┤
│ [Chat] [Memory]                             │
├─────────────────────────────────────────────┤
│                                             │
│ Chat tab                                    │
│ or                                          │
│ Memory management tab                       │
│                                             │
└─────────────────────────────────────────────┘
```

Memory tab:

```text
┌──────────────────┬──────────────────────────┐
│ Memory List      │ Memory Detail            │
│                  │                          │
│ User Profile     │ Domain                   │
│ Working Context  │ Scope                    │
│ Episodic         │ Source                   │
│ Relationship     │ Lifecycle                │
│                  │ Recorded At              │
│                  │                          │
│                  │ Content                  │
│                  │ [editable text area]     │
│                  │                          │
│                  │ [Save] [Delete]          │
│                  │ [History] [Refresh]      │
└──────────────────┴──────────────────────────┘
```

Exact visual styling is not frozen by this plan.

### 8.3 Required User Operations

First version must support:

```text
Refresh list
Select Memory
Inspect detail
Edit content
Delete Memory
View history
```

### 8.4 Delete Confirmation

A simple confirmation dialog is acceptable:

```text
Delete this Memory?
```

The confirmation is a Desktop UX concern.

The actual delete semantics remain server-owned.

### 8.5 Failure Feedback

The UI should show a stable, non-technical message for protocol failures.

It should not show by default:

```text
stack trace
SQLite detail
filesystem path
raw exception object
```

The user should be able to tell:

```text
there are no Memories
```

from:

```text
Memory operation failed
```

### 8.6 Connection State

Memory controls should respect connection state.

When disconnected:

```text
Memory network operations disabled
```

The UI may remain visible.

### 8.7 Capability Increment

Before Task 10D:

```text
Memory governance is technically callable from Desktop code
```

After Task 10D:

```text
normal user can govern Memory through WPF
```

Suggested checkpoint:

```text
feat(desktop): add memory management ui
```

---

## 9. Task 10E — Runtime Acceptance + Documentation

### 9.1 Goal

Validate the complete Desktop Memory governance flow against the real Python runtime.

Target acceptance path:

```text
WPF
  ↓
AgentClientService
  ↓
MemoryClientService
  ↓
MemoryProtocol
  ↓
WebSocketAgentConnection
  ↓
Python WebSocketServer
  ↓
MemoryProtocolHandler
  ↓
Governance
  ↓
SQLite
```

### 9.2 Acceptance Matrix

Verify at minimum:

```text
Connect Desktop
→ chat still works

Open Memory UI
→ list loads

empty Memory
→ explicit empty state

select Memory
→ detail shown

edit Memory
→ server confirms
→ UI refreshes committed content

history
→ revision list shown

delete Memory
→ confirmation
→ server confirms
→ item disappears from normal list

Memory protocol error
→ truthful user-visible failure
→ chat remains usable

disconnect
→ Memory controls stop issuing requests

reconnect
→ Memory list can load again
```

### 9.3 Quality Gates

Expected:

```text
dotnet build
Python full pytest
Ruff
mypy
git diff --check
manual WPF runtime acceptance
Git staged review
```

If Task 10 adds C# automated tests, run them as part of this gate.

Do not introduce a large test framework solely to satisfy a checklist.

### 9.4 Documentation

Update this Task 10 plan with:

```text
actual checkpoint SHAs
actual files
actual final UI architecture
actual test/build results
known non-blocking follow-ups
```

Suggested final checkpoint:

```text
test(desktop): accept memory management workflow
```

---

## 10. File-Level Implementation Direction

The exact diff must be determined at each subtask, but the likely areas are:

```text
src/Desktop/DesktopCompanion.Desktop/DesktopCompanion.Desktop/
```

Task 10A:

```text
ApplicationServices/IAgentClientService.cs
ApplicationServices/AgentClientService.cs
```

Task 10B:

```text
ApplicationServices/IMemoryClientService.cs
ApplicationServices/MemoryClientService.cs
Protocol/MemoryProtocol.cs
```

Task 10C:

```text
Presentation/MemoryManagementViewModel.cs
possibly small supporting presentation models
```

Task 10D:

```text
MainWindow.xaml
MainWindow.xaml.cs
App.xaml.cs
```

Task 10E:

```text
Task 10 documentation
integration/manual acceptance support as required
```

This plan does not require all listed files to change.

---

## 11. Existing Files That Must Keep Their Boundaries

### `WebSocketAgentConnection.cs`

Remain responsible for:

```text
WebSocket transport
AgentMessage JSON serialization
AgentMessage JSON deserialization
```

Do not add Memory-specific routing here.

### `AgentMessage.cs`

Keep the Task 9 envelope stable.

Task 10 should not add a second Message schema.

### `MemoryProtocol.cs`

Remain the wire-contract helper.

Do not turn it into ViewModel/application state.

### `MainWindowViewModel.cs`

Keep chat-specific presentation behavior focused.

Do not make it a giant combined chat + Memory domain service.

Some top-level navigation state may remain here if necessary, but Memory governance state should live in a dedicated ViewModel.

---

## 12. Request/Response Concurrency Requirements

Task 10 must not assume:

```text
the next WebSocket message
=
the response to the most recent request
```

That assumption breaks as soon as:

```text
chat response
Memory result
Memory error
future tool result
```

can share one connection.

Correlation must use:

```text
request.Id
↔
response.payload.request_id
```

Pending requests should remain independent.

This is one of Task 10's most important architecture requirements.

---

## 13. Threading / Dispatcher Boundary

`AgentClientService.ReceiveLoopAsync()` currently receives messages off the UI flow.

WPF-bound collection/property changes must execute safely on the Dispatcher.

The application service should not become WPF-specific solely to marshal UI state.

Preferred separation:

```text
AgentClientService
→ raises/completes application-level result

ViewModel
→ marshals bindable state changes through Dispatcher when required
```

Task 10 should preserve that boundary.

---

## 14. Error-State Semantics

The UI must distinguish at least:

```text
EMPTY
no Memory entries

FAILED
operation could not complete

DISCONNECTED
transport unavailable

BUSY
request in progress

LOADED
valid data available
```

Do not collapse:

```text
memory.list.result with []
```

and:

```text
error / MEMORY_OPERATION_FAILED
```

into the same visible state.

This distinction is an explicit outcome of Task 8 + Task 9.

---

## 15. Security / Privacy Boundary

Memory content is user factual data.

Task 10 should avoid introducing logging such as:

```text
full Memory content
full edit text
full history payload
```

into normal diagnostics.

Safe UI display is allowed because the user explicitly opened the Memory governance surface.

Transport/application logs should stay metadata-focused.

---

## 16. Explicit Non-Goals

Task 10 does not implement:

```text
advanced Memory search
pagination
bulk editing
bulk deletion
tags
categories beyond existing domain/scope
restore deleted Memory
undo delete
Memory import/export
Memory backup/restore
candidate review queue
automatic learning controls
Memory analytics
rich filtering
full app visual redesign
custom MVVM framework
DI container migration
navigation framework
generic RPC framework
```

These may be considered later if real product needs justify them.

---

## 17. No New Architecture Framework by Default

The current Desktop is intentionally small.

Task 10 should not automatically add:

```text
CommunityToolkit.Mvvm
ReactiveUI
Prism
Autofac
Microsoft.Extensions.DependencyInjection
navigation frameworks
```

The current architecture can support Task 10 with:

```text
INotifyPropertyChanged
ObservableCollection
application-service interfaces
existing App composition root
small code-behind event handlers
```

A framework should only be introduced if implementation proves the current structure inadequate.

---

## 18. Task 10 Testing Strategy

Because there is currently no Desktop test project, validation should grow proportionally.

### Task 10A

Focus on deterministic request correlation behavior.

If practical, add small C# unit coverage only if doing so does not require a disproportionate testing framework migration.

At minimum:

```text
dotnet build
manual correlation acceptance
```

### Task 10B

Verify:

```text
Memory request builders used correctly
result types parsed correctly
Memory error payloads preserved
```

### Task 10C

Verify presentation-state transitions:

```text
loading
loaded
empty
failed
edit success
delete success
history load
```

### Task 10D

Manual WPF acceptance is expected.

### Task 10E

Run full Python regression as cross-boundary protection even though most Task 10 code is C#.

---

## 19. Owner Decisions Required During Implementation

These should be decided when implementation reaches them, not guessed now.

### UI placement

Likely:

```text
TabControl
Chat | Memory
```

but final choice belongs to Task 10D implementation review.

### Delete confirmation wording

Simple confirmation is recommended, exact copy is not architecture.

### History presentation

Possible first versions:

```text
inline panel
separate list below detail
small dialog
```

Choose the simplest usable option after seeing the actual WPF layout.

### Memory filtering

No advanced filtering is required for Task 10 completion.

A refreshable full list is sufficient for first acceptance.

---

## 20. Task 10 Completion Criteria

Task 10 is complete when:

1. Desktop request/response correlation uses `payload.request_id`.
2. Chat responses still behave as before.
3. Memory responses do not appear as fake chat messages.
4. A typed Memory application service exists.
5. UI can load the Memory list.
6. Empty list is distinguishable from request failure.
7. User can select and inspect a Memory.
8. User can edit Memory through Governance.
9. User can delete Memory through Governance.
10. User can inspect allowed Memory history.
11. UI waits for server-confirmed success before presenting governance success.
12. Protocol failures are displayed truthfully and safely.
13. Disconnected state prevents invalid Memory operations.
14. WPF does not directly know SQLite/repository semantics.
15. WPF does not implement Memory revision/delete business rules.
16. Existing chat workflow remains usable.
17. Desktop build succeeds.
18. Python regression remains green.
19. Manual real-runtime Memory workflow passes.
20. Task 10 documentation is synchronized and checkpointed.

---

## 21. Planned Checkpoint Sequence

```text
Task 10A
feat(desktop): add correlated agent requests

Task 10B
feat(desktop): add memory application service

Task 10C
feat(desktop): add memory management view model

Task 10D
feat(desktop): add memory management ui

Task 10E
test(desktop): accept memory management workflow
```

Exact commit messages may change to match final implementation.

---

## 22. Architecture Inputs

Task 10 is based on the current repository and accepted architecture:

```text
ADR 0002
WebSocket Desktop/Core transport

ADR 0003
Layered Desktop client

ADR 0010
Events are facts; commands/requests remain explicit boundaries

ADR 0016
Memory domain/scope/lifecycle/revision semantics

ADR 0018
Memory failure isolation

ADR 0020
Logical Memory identity

ADR 0021
Explicit runtime routing for request/response capabilities

Task 9
stable Memory WebSocket protocol
```

Task 10 does not require a new ADR at plan time.

If implementation later reveals a new long-lived architecture decision that cannot be represented by the existing ADRs, stop and decide explicitly before adding one.

---

## 23. First Implementation Step

Start with Task 10A.

Do **not** begin with XAML.

First establish:

```text
request
→ request ID registration
→ WebSocket send
→ correlated response
→ caller receives exact AgentMessage
```

Once this boundary is reliable, build the Memory application service and UI on top of it.

This prevents the UI from depending on the current chat-only `MessageReceived` assumption.
