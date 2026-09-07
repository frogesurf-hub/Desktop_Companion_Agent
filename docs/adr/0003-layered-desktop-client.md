# ADR 0003 - Layered Desktop Client

Status: Accepted

Date: Phase 0

## Context

Putting WebSocket, JSON, Agent behavior, and UI state directly into `MainWindow.xaml.cs` would create a long-lived coupling problem.

Future UI may change radically when the project adopts a desktop pet / avatar presentation.

## Decision

Use the Desktop dependency direction:

```text
View
  -> ViewModel
  -> Application Service
  -> Connection Interface
  -> WebSocket Implementation
```

Keep the protocol model separate from transport implementation.

## Consequences

- UI can change without rewriting transport
- transport can be replaced behind `IAgentConnection`
- application behavior can be tested independently in the future
- more files / interfaces exist early, but coupling is controlled

## Phase 0 Evidence

Implemented:

- `MainWindowViewModel`
- `IAgentClientService` / `AgentClientService`
- `IAgentConnection` / `WebSocketAgentConnection`
- `AgentMessage`
