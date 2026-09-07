# Phase 0 Checkpoint - Desktop Companion Agent

Date: 2026-09-08

Git head at checkpoint:

```text
4d7ab06 Integrate Agent client into WPF interface
```

## 1. Checkpoint Purpose

Phase 0 was used to establish a maintainable engineering baseline and prove the core cross-language runtime architecture before adding real intelligence systems.

The key success criterion was not visual polish and not autonomous behavior. It was proving that a Windows desktop shell and a Python Agent Core could form one reliable system with explicit module boundaries.

## 2. Phase 0 Outcome

Completed end-to-end path:

```text
WPF MainWindow
  -> MainWindowViewModel
  -> AgentClientService
  -> WebSocketAgentConnection
  -> JSON AgentMessage
  -> WebSocket
  -> Python WebSocketServer
  -> Python Message
  -> Agent.process_message()
  -> response Message
  -> WebSocket
  -> WPF message list
```

Manual acceptance result:

```text
Agent Core: Connected
You: 你好
Agent: 收到你的消息: 你好
```

A standalone C# ConnectionProbe also completed the same transport/protocol round trip without the WPF UI.

## 3. Engineering Work Completed

### Project and architecture foundation

- project purpose and design principles documented
- target architecture documented
- technology stack selected
- MVP communication path defined
- third-party reference register created
- Git workflow established

### Python Agent Core foundation

- package layout normalized to `agent_core`
- unified `Message` envelope
- basic `Agent` processing boundary
- `pyproject.toml` project configuration
- pytest configuration
- Ruff and mypy quality baseline
- environment/settings system
- secret handling with `SecretStr`
- console + rotating file logging
- async runtime entry point

### WebSocket server

- local async WebSocket server
- connection lifecycle logging
- text JSON message handling
- Agent dependency injection
- response serialization
- invalid JSON error handling
- invalid message-structure handling
- binary message rejection
- bad-message fault isolation

### C# desktop communication

- `IAgentConnection` abstraction
- `WebSocketAgentConnection`
- protocol `AgentMessage`
- fragmented receive assembly
- connect / disconnect lifecycle
- send / receive primitives
- standalone connection probe

### WPF application layers

- `ApplicationServices` layer
- `AgentClientService`
- independent receive loop
- `MessageReceived` / `ReceiveFailed` events
- `Presentation` layer
- `MainWindowViewModel`
- WPF data binding
- basic chat UI
- composition root in `App.xaml.cs`

## 4. Test and Verification Evidence

Phase 0 development used targeted tests rather than development-AI full-suite runs.

Python tests cover:

- Message creation / JSON round trip
- Agent response behavior
- Settings defaults / environment overrides / invalid modes / secret handling
- Logging file output / level filtering / idempotent handler setup
- Runtime composition
- WebSocket connection lifecycle
- chat round trip
- invalid JSON
- invalid message structure
- binary messages
- connection survival after a bad message

Quality checks used during development:

```text
ruff check src/agent_core
mypy src/agent_core
```

Desktop verification:

- WPF project built successfully
- ConnectionProbe performed real C# <-> Python round trip
- WPF performed real C# <-> Python round trip

## 5. Git History of Phase 0

Key commits:

```text
4b7303d Initialize project architecture documentation
a56aa81 Define technology stack
38fe8f1 Setup desktop and agent development environment
0826ee7 Define MVP design
2385122 Define communication protocol
a841b31 Implement agent core foundation
7198763 Fix package imports and verify agent tests
cb3caca Configure Python project structure
dbbbb9b Establish Python development standards
055cf58 Add application configuration system
8f1487b Add application logging system
01f7187 Integrate runtime startup flow
1a91985 Add WebSocket connection lifecycle
cc6b1fa Add WebSocket message processing and protocol errors
fa93f3a Integrate WebSocket server into runtime
4c4db11 Add desktop WebSocket client and connection probe
4d7ab06 Integrate Agent client into WPF interface
```

The Git history demonstrates a progression from architecture -> engineering baseline -> Python runtime -> transport -> C# client -> WPF vertical slice.

## 6. Important Decisions Preserved

### Split runtime

```text
C# WPF = Windows shell / desktop integration
Python = Agent intelligence runtime
```

### WebSocket over simple request/response-only transport

The project requires future proactive messages, events, permission requests, and state updates. The connection therefore must support server-initiated messages.

### Independent Desktop receive loop

The desktop does not model communication as `Send -> Receive -> Send -> Receive`.

The receive loop remains active independently, preserving future proactive companion behavior.

### UI does not own transport logic

The desktop layering is intentionally:

```text
View
  -> ViewModel
  -> Application Service
  -> Connection Interface
  -> WebSocket Implementation
```

### Runtime infrastructure before intelligence features

Configuration and logging were established before networking, so later provider, memory, and tool failures can be diagnosed without scattering hard-coded values or `print()` calls.

## 7. Difference Between Phase 0 and the Original MVP

The original `MVP_DESIGN.md` states that a DeepSeek call belongs to the full MVP path.

Phase 0 intentionally stopped one layer earlier:

```text
WPF -> Python -> Agent stub -> WPF
```

rather than:

```text
WPF -> Python -> DeepSeek -> Python -> WPF
```

Therefore:

- **Phase 0 is complete.**
- **The original AI MVP is not yet complete.**

This distinction must remain explicit so future planning does not accidentally treat the echo Agent as an LLM integration.

## 8. Known Technical Debt at Checkpoint

Highest-priority cleanup before / at the beginning of Phase 1:

- rename C# `Potocol/` directory to `Protocol/`
- decide the canonical Python dependency source (`pyproject.toml` vs duplicated `requirements.txt`)
- align protocol error documentation with implementation
- decide where Desktop endpoint configuration belongs
- add C# automated test project when the first stable desktop contracts are finalized
- exclude local caches / user files from future checkpoint archives

Not Phase 0 blockers, but future requirements:

- reconnect strategy
- graceful process orchestration between Desktop and Agent Core
- protocol version negotiation
- provider timeout/cancellation policy
- Event Bus
- Permission Layer

## 9. Phase 1 Gate

Do not begin broad new systems immediately after this checkpoint.

Phase 1 should first complete the original MVP intelligence path through a provider abstraction, with DeepSeek as the initial provider.

Before Phase 1 implementation:

1. commit the Phase 0 documentation checkpoint
2. create a separate cleanup commit for `Potocol -> Protocol`
3. confirm the Phase 1 provider boundary and failure behavior
4. continue targeted-test workflow

## 10. Historical Meaning

Phase 0 is the point where Desktop Companion Agent changed from a collection of design documents and independent modules into one executable multi-process system.

The UI is intentionally plain. Its importance is architectural: the project now has a stable path on which later character, memory, perception, attention, behavior, avatar, voice, and tools can be built.
