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

# 15. Phase 1 Implemented Baseline

The sections above describe the long-term target architecture. As of the Phase 1 checkpoint (2026-09-09), the implemented runtime now includes the original real-LLM MVP.

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

Responsibilities:

- `App.xaml.cs`: Desktop composition root
- `MainWindow`: WPF view and UI event forwarding
- `MainWindowViewModel`: presentation state and user interaction
- `AgentClientService`: application-level chat behavior and independent receive loop
- `IAgentConnection`: transport abstraction
- `WebSocketAgentConnection`: WebSocket + JSON transport implementation
- `AgentMessage`: C# representation of the protocol envelope

The independent receive loop remains an intentional architectural requirement for future proactive messages.

## 15.2 Current Python Runtime

```text
main.py
  -> Settings
  -> Logging
  -> DeepSeekProvider
  -> Agent
  -> WebSocketServer
  -> Message
```

More precisely:

```text
main.py
  -> get_settings()
  -> validate provider selection
  -> unwrap SecretStr at the composition root
  -> create DeepSeekProvider
  -> create Agent(provider)
  -> create WebSocketServer(agent)
  -> await server.run()
  -> finally await provider.aclose()
```

Responsibilities:

- `main.py`: Python composition root, provider construction, async runtime entry, provider lifetime
- `Settings`: environment / `.env` runtime configuration
- `Logging`: console + rotating-file observability
- `WebSocketServer`: connection lifecycle, protocol parsing, error isolation, response transport
- `Message`: Python protocol envelope
- `Agent`: protocol-to-provider orchestration and safe Provider error mapping
- `LLMProvider`: provider-neutral asynchronous Agent-facing contract
- `DeepSeekProvider`: concrete DeepSeek / OpenAI-compatible adapter

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

- Agent Core must not import DeepSeek/OpenAI SDK types.
- vendor exceptions are translated inside the adapter.
- Provider failures cross into Agent as provider-neutral errors.
- Desktop receives stable safe error codes/messages.
- API keys are unwrapped only at provider construction.
- external async client lifetime is owned by the composition root.

Phase 1 Provider behavior:

```text
async
non-streaming
thinking disabled by default
60-second default application timeout
zero automatic retries
asyncio cancellation propagation
```

## 15.4 Current Cross-Process Flow

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

Phase 1 verified this flow using both:

- `tools/DesktopCompanion.ConnectionProbe`
- the real WPF UI

## 15.5 Provider Failure Flow

```text
DeepSeek / SDK failure
  -> DeepSeekProvider translation
  -> LLMProviderError
  -> Agent safe mapping
  -> protocol error code + message
  -> WPF
```

The Provider boundary prevents raw vendor diagnostics from becoming the Desktop contract.

## 15.6 Still Not Implemented

The following target-architecture modules remain design-level only:

- Event Bus / Event System
- Character Core
- Memory System
- Internal State
- Perception Layer
- Situation Engine
- Attention Engine
- Behavior Engine
- Permission Layer
- Action / Tool Layer
- Embodiment Layer
- local-model routing / cloud fallback
- voice

Do not infer implementation merely because a module exists in the target diagram.

## 15.7 Boundary Rule

Future implementation should extend the verified Phase 1 vertical slice without collapsing layers.

In particular:

- UI must not own WebSocket / provider / memory logic
- WebSocket must not own Agent or Provider construction
- provider-specific code must not become the Agent Core API
- Event System work should introduce explicit event boundaries before later proactive systems are added
- proactive behavior must use an event/attention path rather than UI polling
- sensitive actions must pass through Permission Layer
