# Desktop Companion Agent - Project State

> Context checkpoint: Phase 0 completed on 2026-09-08.
>
> This file is the primary context-recovery document for future development sessions. If chat context is lost, read this file first, then `ARCHITECTURE.md`, `ROADMAP.md`, and the relevant subsystem documentation.

## 1. Current Status

Current phase:

- Phase 0: **Complete**
- Next phase: **Phase 1 - LLM Provider / original MVP completion**
- Current Git checkpoint: `4d7ab06 Integrate Agent client into WPF interface`

Phase 0 established a real end-to-end technical vertical slice:

```text
WPF UI
  -> MainWindowViewModel
  -> AgentClientService
  -> IAgentConnection
  -> WebSocketAgentConnection
  -> JSON / AgentMessage
  -> WebSocket
  -> Python WebSocketServer
  -> Message
  -> Agent.process_message()
  -> response
  -> WPF UI
```

The current `Agent` is intentionally a stub. It echoes chat input as:

```text
收到你的消息: <user text>
```

DeepSeek / real LLM calls are **not yet implemented**.

## 2. What Phase 0 Proved

Phase 0 proved that the selected split architecture is viable:

- C# WPF can act as the Windows desktop shell.
- Python 3.11 can host the Agent Core runtime.
- The two processes can communicate over a local WebSocket connection.
- The JSON protocol can be represented consistently in C# and Python.
- The desktop client can maintain an independent receive loop, which is required for future proactive Agent messages.
- Configuration, logging, testing, type checking, and Git workflow can support the project as a long-lived codebase.

The first successful UI round trip was:

```text
You: 你好
Agent: 收到你的消息: 你好
```

This is the project's Phase 0 "Hello World" milestone.

## 3. Current Implemented Architecture

### 3.1 Python Agent Core

Entry point:

```text
src/agent_core/main.py
```

Current composition:

```text
main.py
  -> get_settings()
  -> setup_logging()
  -> Agent()
  -> WebSocketServer(...)
  -> serve_forever()
```

Implemented modules:

```text
src/agent_core/
├── communication/
│   └── websocket_server.py
├── config/
│   └── settings.py
├── core/
│   ├── agent.py
│   └── message.py
├── observability/
│   └── logging.py
├── tests/
└── main.py
```

Implemented behavior:

- typed runtime settings via `pydantic-settings`
- `.env` / environment variable support with `DCA_` prefix
- secrets represented with `SecretStr`
- console + rotating file logging
- local WebSocket server
- JSON message parse / serialize
- protocol errors for invalid JSON, invalid structure, and binary messages
- invalid message isolation: one bad message does not kill the connection
- shared `Agent` instance injected into `WebSocketServer`
- async runtime startup

### 3.2 C# WPF Desktop

Current layers:

```text
App.xaml.cs                 Composition Root
      |
      v
MainWindow                  Presentation view
      |
      v
MainWindowViewModel         Presentation state / interaction
      |
      v
AgentClientService          Application-level Agent client behavior
      |
      v
IAgentConnection            Transport abstraction
      |
      v
WebSocketAgentConnection    WebSocket + JSON transport
      |
      v
AgentMessage                Protocol model
```

Implemented behavior:

- connect / disconnect to Agent Core
- send `AgentMessage`
- receive fragmented WebSocket messages correctly
- independent background receive loop
- `MessageReceived` / `ReceiveFailed` events
- WPF Dispatcher handoff for UI updates
- basic connection status
- basic chat input and message history

### 3.3 Connection Probe

Diagnostic project:

```text
tools/DesktopCompanion.ConnectionProbe/
```

Purpose:

- validate C# -> Python communication without involving WPF presentation logic
- isolate transport/protocol failures from UI failures

This probe completed a real C# -> Python -> Agent -> C# round trip during Phase 0.

## 4. Current Protocol

Transport:

```text
ws://127.0.0.1:8765
```

Message envelope:

```json
{
  "id": "uuid",
  "type": "chat",
  "timestamp": "ISO8601 UTC",
  "source": "desktop",
  "payload": {}
}
```

Implemented message behavior:

- `chat`
- `response`
- `error`

Documented but not yet implemented end-to-end:

- `event`
- `permission_request`
- `tool_request`
- `tool_response`
- memory / emotion / avatar events

## 5. Configuration Baseline

Python configuration currently includes:

```text
DCA_ENVIRONMENT
DCA_RUNTIME_MODE
DCA_WEBSOCKET_HOST
DCA_WEBSOCKET_PORT
DCA_MODEL_PROVIDER
DCA_DEEPSEEK_API_KEY
DCA_LOG_LEVEL
```

Important:

- `DCA_MODEL_PROVIDER=deepseek` is currently configuration only.
- `DCA_DEEPSEEK_API_KEY` is not consumed by a provider implementation yet.
- real `.env` files must never be committed.

## 6. Development Baseline

Python:

- Python 3.11
- pytest
- Ruff
- mypy
- editable install through `pyproject.toml`

Desktop:

- C# WPF
- target framework: .NET 8 Windows
- .NET SDK 10 may be installed locally; project target remains .NET 8 Windows

Development workflow:

```text
Requirement / Goal
  -> Design
  -> Task Breakdown
  -> Implementation
  -> Targeted Tests
  -> Quality Checks
  -> Documentation Update
  -> Git Review
  -> Commit
```

AI-assisted development rule:

- development AI runs only tests directly related to its modifications
- no full pytest by default
- project owner performs final full-suite acceptance

## 7. Architectural Principles That Must Not Be Lost

### 7.1 Companion, not a turn-based chatbot

The runtime must eventually support proactive output without requiring a user request.

The C# independent receive loop already preserves this direction.

### 7.2 Situation Engine + Attention Engine are core differentiators

Long-term flow:

```text
External World
  -> Perception
  -> Events
  -> Situation Engine
  -> Attention Engine
  -> Behavior Engine
```

The Agent should decide whether to ignore, notice, speak, wait, move, or request an action.

### 7.3 Intent != Permission

Character intent never grants system permission.

Sensitive actions must pass through a dedicated permission/capability boundary.

### 7.4 Real and fictional state must remain separate

Fictional daily-life flavor must not contaminate:

- user facts
- factual reasoning
- memory retrieval
- tool decisions

### 7.5 Local-first, cloud-enhanced

Target runtime modes:

- Offline
- Local AI
- Hybrid
- Cloud

Cloud failure must not erase the companion's basic local runtime behavior.

### 7.6 Stable interfaces over hidden coupling

Continue using:

- interfaces
- adapters
- event boundaries
- dependency injection
- composition roots

Do not move transport, protocol, provider, memory, or tool implementation directly into UI code.

## 8. Third-Party Reference Decisions

Primary references recorded during Phase 0:

- OpenMeido: desktop companion / memory / provider / proactive interaction reference
- Project AIRI: digital-life, avatar, voice, extensible companion reference
- screenpipe: event-driven desktop perception and activity timeline reference
- Microsoft UFO: Windows-native / UI Automation reference
- Agent-S: vision / GUI computer-use fallback reference

Reference principle:

- borrow architecture and lessons, not entire product architecture
- respect each project's license before copying code
- prefer reimplementation of project-specific core systems

See `THIRD_PARTY.md` for the persistent reference register.

## 9. Known Technical Debt / Cleanup Candidates

These are known at the Phase 0 checkpoint and should not be forgotten:

1. The C# directory is currently named `Potocol/` while its namespace is `DesktopCompanion.Desktop.Protocol`. Rename the directory to `Protocol/` in a dedicated cleanup commit.
2. Desktop WebSocket endpoint is currently hard-coded in `App.xaml.cs`. Desktop-side configuration / shared endpoint configuration is not implemented yet.
3. C# automated tests do not yet exist. Current C# confidence comes from successful builds, ConnectionProbe, and manual WPF end-to-end verification.
4. `Agent` is only an echo stub. No provider interface or LLM is connected.
5. Python `Message` validation is lightweight. The documented protocol version field is not implemented.
6. Error documentation and implementation are not fully aligned: the protocol document shows an error `code`, while runtime error messages currently only guarantee a message payload.
7. Reconnect / retry / connection-state recovery is not implemented on the WPF client.
8. Desktop shutdown/disposal behavior is sufficient for the MVP slice but has not been hardened for long-running production use.
9. `requirements.txt` and `pyproject.toml` both describe Python dependencies; this can drift and should eventually be reduced to one canonical dependency source.
10. Exported development folders such as `.ruff_cache`, `.mypy_cache`, `.pytest_cache`, and local `*.csproj.user` files should not be treated as project source. Review ignore rules before future archive/checkpoint exports.

## 10. Phase 1 Entry Point

The original `MVP_DESIGN.md` defines a real LLM provider as part of MVP, but Phase 0 intentionally stopped at the cross-language Agent stub.

Therefore the recommended Phase 1 objective is:

> Complete the original MVP by introducing a provider abstraction and a DeepSeek provider without coupling the Agent Core to one vendor.

Expected Phase 1 scope:

- provider interface / abstraction
- DeepSeek adapter
- request / response model boundary
- secure API-key use through existing Settings
- timeout / provider failure handling
- clear error propagation to Desktop
- targeted provider tests using mocks/fakes
- real WPF -> Python -> DeepSeek -> WPF acceptance

Explicitly out of Phase 1 unless required by the provider contract:

- Memory
- Perception
- Avatar
- Tools
- Situation Engine
- Attention Engine

Before implementing Phase 1, first perform the Phase 0 documentation commit and the small `Potocol -> Protocol` cleanup separately.

## 11. Context Recovery Procedure

When continuing this project in a new conversation or with another development AI, provide/read in this order:

1. `PROJECT_STATE.md`
2. `ARCHITECTURE.md`
3. `ROADMAP.md`
4. `DESIGN.md`
5. `TECH_STACK.md`
6. `THIRD_PARTY.md`
7. `docs/DEVELOPMENT.md`
8. the subsystem document relevant to the current task
9. current source files and recent Git log

The repository and its committed documentation are the source of truth. Chat history is supplementary context, not the authoritative project state.
