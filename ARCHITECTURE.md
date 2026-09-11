# Desktop Companion Agent Architecture

# 1. 总体架构

    Desktop Companion

    ├── Shell / Runtime
    ├── Character Core
    ├── Memory System
    ├── Internal State
    ├── Perception Layer
    ├── Situation Engine
    ├── Attention Engine
    ├── Behavior Engine
    ├── Permission Layer
    ├── Action Layer
    ├── Embodiment Layer
    ├── Provider Layer
    ├── Event Bus
    └── Persistence

------------------------------------------------------------------------

# 2. 数据流

    External World

    ↓

    Perception

    ↓

    Events

    ↓

    Situation Engine

    ↓

    Attention Engine

    ↓

    Behavior Engine

    ↓

    Avatar / Voice / Tools

------------------------------------------------------------------------

# 3. Character Core

负责角色长期定义。

包含：

-   Identity
-   Personality
-   Speech Style
-   Preferences
-   Core Values

原则：

角色可以有个性，但不能为了个性欺骗用户。

------------------------------------------------------------------------

# 4. Memory System

记忆必须分离：

    User Profile
    用户真实资料

    Working Context
    当前任务

    Episodic Memory
    真实经历

    Long-term Memory
    长期信息

    Relationship Memory
    关系历史

    Today Memory
    今日状态

    Fiction Memory
    临时虚构生活

禁止：

虚构记忆进入真实事实系统。

------------------------------------------------------------------------

# 5. Internal State

动态状态：

-   Mood
-   Energy
-   Curiosity
-   Social Desire
-   Relationship State
-   Daily State

区别：

    Character Core:
    她是谁

    Internal State:
    她现在怎样

------------------------------------------------------------------------

# 6. Perception Layer

负责观察：

-   当前窗口
-   当前软件
-   文件变化
-   系统状态
-   时间
-   天气
-   网络信息
-   屏幕视觉

只提供信息，不决定行为。

------------------------------------------------------------------------

# 7. Situation Engine

将低级事件转换为高级理解。

例如：

输入：

    Unity
    修改代码
    编译失败
    重新运行

输出：

    用户正在解决 Unity 问题

------------------------------------------------------------------------

# 8. Attention Engine

决定：

-   是否重要
-   是否需要提醒
-   是否重复
-   是否适合打扰

目标：

主动但不过度打扰。

------------------------------------------------------------------------

# 9. Behavior Engine

根据：

-   Personality
-   Mood
-   Relationship
-   Situation

决定：

-   说话
-   沉默
-   动作
-   表情
-   工具请求

------------------------------------------------------------------------

# 10. Permission Layer

核心原则：

    Intent != Permission

角色想做某事，不代表系统允许。

所有敏感操作经过权限层。

------------------------------------------------------------------------

# 11. Embodiment Layer

负责：

-   Live2D
-   VRM
-   3D
-   声音
-   动作
-   表情

上层输出语义：

    emotion: annoyed
    motion: look_away

底层负责实现。

------------------------------------------------------------------------

# 12. Event Bus

所有模块通过事件交流。

避免：

模块直接耦合。

------------------------------------------------------------------------

# 13. Provider / Adapter

所有外部能力可替换：

-   LLM
-   TTS
-   Vision
-   Memory
-   Avatar
-   Tools
-   App Adapter

------------------------------------------------------------------------

# 14. Local / Cloud

系统必须支持：

    Local Core

    +

    Optional Online Intelligence

云服务失败时可以降级。

------------------------------------------------------------------------

# 15. Phase 2 Implemented Baseline

The sections above describe the long-term target architecture. As of the Phase 2 checkpoint (2026-09-12), the implemented runtime includes the original real-LLM MVP plus an explicit internal Event System.

## 15.1 Current Desktop Runtime

```text
App.xaml.cs
  -> MainWindow
  -> MainWindowViewModel
  -> AgentClientService
  -> IAgentConnection
  -> WebSocketAgentConnection
  -> AgentMessage
```

Responsibilities remain:

- `App.xaml.cs`: Desktop composition root
- `MainWindow`: WPF view and UI event forwarding
- `MainWindowViewModel`: presentation state and user interaction
- `AgentClientService`: application-level chat behavior and independent receive loop
- `IAgentConnection`: transport abstraction
- `WebSocketAgentConnection`: WebSocket + JSON transport implementation
- `AgentMessage`: C# representation of the Desktop protocol envelope

The independent receive loop remains an intentional architectural requirement for future proactive messages.

Phase 2 made no C# source changes.

## 15.2 Current Python Runtime

```text
main.py
  -> Settings
  -> Logging
  -> DeepSeekProvider
  -> EventBus
  -> Agent
  -> WebSocketServer
```

Composition-root lifetime:

```text
create DeepSeekProvider
  -> establish Provider cleanup boundary
  -> create EventBus(queue_capacity from Settings)
  -> create Agent(provider)
  -> create WebSocketServer(agent)
  -> await EventBus.start()
  -> await WebSocketServer.run()
  -> finally await EventBus.close()
  -> finally await Provider.aclose()
```

Responsibilities:

- `main.py`: Python composition root and runtime lifetime ownership
- `Settings`: environment / `.env` runtime configuration
- `Logging`: console + rotating-file observability
- `WebSocketServer`: connection lifecycle, protocol parsing, error isolation, response transport
- `Message`: Python Desktop-protocol envelope
- `Agent`: protocol-to-provider orchestration and safe Provider error mapping
- `LLMProvider`: provider-neutral asynchronous Agent-facing contract
- `DeepSeekProvider`: concrete DeepSeek / OpenAI-compatible adapter
- `RuntimeEvent`: internal Event metadata foundation
- `EventPublisher`: narrow publication capability
- `EventBus`: internal asynchronous routing / dispatch / lifecycle service

## 15.3 Provider Layer

```text
Agent
  |
  v
LLMProvider Protocol
  |
  +-- LLMRequest / LLMResponse
  +-- LLMProviderError hierarchy
  |
  v
DeepSeekProvider
  |
  v
AsyncOpenAI
  |
  v
DeepSeek API
```

Boundary rules:

- Agent Core public boundaries remain provider-neutral.
- vendor exceptions are translated inside adapters.
- Provider failures cross into Agent as provider-neutral errors.
- Desktop receives stable safe error codes/messages.
- API keys are unwrapped only at provider construction.
- external async Provider lifetime is owned by the composition root.

Current Provider behavior:

```text
async
non-streaming
thinking disabled by default
60-second default application timeout
zero automatic retries
asyncio cancellation propagation
```

## 15.4 Runtime Event Model

Internal Runtime Events are facts / notifications that describe something that already happened.

They are not:

- commands
- permission grants
- synchronous requests
- return-value channels

Base metadata:

```text
RuntimeEvent
  source
  event_id
  occurred_at
  correlation_id?
  causation_id?
```

Properties:

- immutable
- Event ID uses UUID identity
- timestamps are timezone-aware and normalized to UTC
- source is a non-empty logical identifier
- optional correlation / causation metadata supports future tracing

Ordinary producers should depend on `EventPublisher`, not the concrete EventBus.

## 15.5 EventBus

Phase 2 EventBus architecture:

```text
Producer
  |
  v
EventPublisher.publish(event)
  |
  v
bounded in-memory Event queue
  |
  v
single dispatcher
  |
  +--> exact-type subscribers for Event A (concurrent siblings)
  |
  +--> next queued Event only after A handlers settle
```

Accepted semantics:

- async, in-process service
- bounded queue
- fail-fast queue-full admission via `EventBusFullError`
- exact concrete Event-type routing
- static subscription registration before running
- publish completes when queue admission succeeds; it does not wait for handlers
- queue admission order defines Event dispatch order
- sibling subscribers for one Event may run concurrently
- ordinary subscriber failures are isolated
- later Events continue after ordinary handler failure
- cancellation is not converted into an ordinary failure
- graceful close drains accepted Events
- explicit lifecycle: NEW -> RUNNING -> CLOSING -> CLOSED
- no Event persistence / replay in Phase 2

The EventBus is deliberately separate from the WebSocket Desktop transport. Internal Runtime Events do not automatically cross process boundaries.

## 15.6 Event Observability

EventBus observability records safe metadata for diagnosis:

- lifecycle state changes
- Event ID / type / sanitized source
- handler identity where useful
- duration where useful
- failure exception type

Default Event logging must not dump full Event payloads or subscriber/dispatcher exception messages.

This protects future Event payloads from becoming an accidental sensitive-data logging channel.

## 15.7 Current Cross-Process Flow

The Phase 1 request/response path remains unchanged in role:

```text
WPF UI
  -> AgentClientService
  -> WebSocketAgentConnection
  -> ws://127.0.0.1:8765
  -> WebSocketServer
  -> Message.from_json()
  -> Agent.process_message()
  -> LLMRequest
  -> LLMProvider.generate()
  -> DeepSeekProvider
  -> DeepSeek API
  -> LLMResponse
  -> protocol Message
  -> Message.to_json()
  -> WebSocketAgentConnection
  -> MainWindowViewModel
  -> WPF UI
```

Phase 2 final acceptance verified this real path still works for two consecutive WPF requests while EventBus is running.

## 15.8 Provider Failure Flow

```text
DeepSeek / SDK failure
  -> DeepSeekProvider translation
  -> LLMProviderError
  -> Agent safe mapping
  -> protocol error code + message
  -> WPF
```

The Provider boundary continues to prevent raw vendor diagnostics from becoming the Desktop contract.

## 15.9 Event / Command / Permission Boundary

Persistent rule:

```text
Event != Command
Intent != Permission
```

An Event communicates a fact or notification.

A future command/request boundary must remain explicit when the system wants something to happen.

A future permission boundary must separately decide whether an intended sensitive action is allowed.

Do not infer authorization from Event source, Event existence, character intent, or Behavior output.

## 15.10 Still Not Implemented

The following target-architecture modules remain design-level or future-phase work:

- Character Core
- Memory System
- Internal State business logic
- Perception Layer
- Situation Engine
- Attention Engine
- Behavior Engine
- Permission Layer
- Action / Tool Layer
- Embodiment Layer
- local-model routing / cloud fallback
- voice
- Desktop Event Bridge

The Event System also deliberately omits:

- Event persistence / replay
- wildcard routing
- subscriber priority
- dynamic unsubscribe
- automatic Event retry
- multiple dispatch workers
- restart / supervision policy

Do not infer implementation merely because a module exists in the target diagram.

## 15.11 Boundary Rule

Future phases should extend the verified Phase 0-2 runtime without collapsing layers.

In particular:

- UI must not own Agent reasoning, Provider, Memory, Tool, or EventBus lifecycle logic

- WebSocket transport must not own Agent / Provider / EventBus construction

- provider-specific code must not become the Agent Core public API

- ordinary Event producers should receive narrow publisher capability where possible

- Runtime Events should remain facts; commands remain explicit

- proactive behavior should use Event -> Situation -> Attention -> Behavior flow rather than UI polling

- sensitive actions must pass through Permission Layer

- real and fictional state must remain separate
