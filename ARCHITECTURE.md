# Desktop Companion Agent Architecture

# 1. 总体架构

```text
Desktop Companion
桌面智能助手

├── Shell / Runtime
│   外壳 / 运行时
├── Character Core
│   角色核心
├── Memory System
│   事实记忆系统
├── Internal State
│   内部状态
├── Perception Layer
│   感知层
├── Situation Engine
│   情境引擎
├── Attention Engine
│   注意力引擎
├── Behavior Engine
│   行为引擎
├── Permission Layer
│   权限层
├── Action Layer
│   行动 / 工具层
├── Embodiment Layer
│   具身层
├── Provider Layer
│   模型提供商层
├── Event Bus
│   事件总线
└── Persistence
    持久化
```

------------------------------------------------------------------------

# 2. 数据流

长期目标数据流：

```text
External World
外部世界
    ↓
Perception
感知
    ↓
Events
事件
    ↓
Situation Engine
情境引擎
    ↓
Attention Engine
注意力引擎
    ↓
Behavior Engine
行为引擎
    ↓
Avatar / Voice / Tools
形象 / 语音 / 工具
```

Memory 为运行时提供事实上下文，但不取代 Situation、Attention 或 Behavior。

------------------------------------------------------------------------

# 3. Character Core

负责角色长期定义。

包含：

- Identity
- Personality
- Speech Style
- Preferences
- Core Values
- Fictional Background（可选）

原则：

角色可以有个性，但不能为了个性欺骗用户。

Character 不拥有事实 Memory，也不拥有未来 Internal State。

------------------------------------------------------------------------

# 4. Memory System

Phase 4 已实现的事实 Memory 语义域：

```text
USER_PROFILE
用户长期真实资料 / 明确偏好 / 长期目标

WORKING_CONTEXT
当前或近期可跨请求、跨重启保留的任务上下文

EPISODIC
真实发生过的事件 / 经历

RELATIONSHIP
用户与某个 Character 的真实共享历史
```

Scope 与 Domain 分离：

```text
GLOBAL_USER
全局用户范围

CHARACTER
角色范围
```

Phase 4 约束：

```text
USER_PROFILE      -> GLOBAL_USER
WORKING_CONTEXT   -> GLOBAL_USER
EPISODIC          -> GLOBAL_USER
RELATIONSHIP      -> CHARACTER
```

Lifecycle 与 Domain 分离：

```text
ACTIVE
SUPERSEDED
EXPIRED
DELETED
```

重要语义修正：

```text
Long-term Memory
长期记忆
-> retention / lifecycle semantics
-> 不是第五个语义域

Today Memory
今日记忆
-> time filtering / lifecycle semantics
-> 不是独立语义域

Fictional Ephemeral State
虚构临时状态
-> 与 factual Memory 隔离
-> 不作为 Phase 4 事实 Memory 持久化
```

关系历史也不等于 Internal State：

```text
Relationship Memory
真实共享历史
!=
Mood / Affection / Trust
情绪 / 好感 / 信任等动态状态
```

核心规则：

```text
Character Fiction
角色虚构设定
!=
Factual Memory
事实记忆

Memory Context
记忆上下文
!=
Permission
权限
```

------------------------------------------------------------------------

# 5. Internal State

动态状态：

- Mood
- Energy
- Curiosity
- Social Desire
- Relationship State
- Daily State

区别：

```text
Character Core
她是谁

Internal State
她现在怎样

Memory
发生过什么 / 用户明确是什么
```

Phase 4 不实现 Internal State 业务逻辑。

------------------------------------------------------------------------

# 6. Perception Layer

负责观察：

- 当前窗口
- 当前软件
- 文件变化
- 系统状态
- 时间
- 天气
- 网络信息
- 屏幕视觉

只提供信息，不决定行为。

------------------------------------------------------------------------

# 7. Situation Engine

将低级事件 / 事实转换为高级语义情境。

例如：

```text
Unity active
Unity 活跃

+ source modified
+ 源文件修改

+ compile failure
+ 编译失败

+ repeated retry
+ 重复重试

→ user is debugging a Unity problem
→ 用户正在解决 Unity 问题
```

Situation 不拥有 Memory persistence，也不直接决定 Permission 或 Tool execution。

------------------------------------------------------------------------

# 8. Attention Engine

决定：

- 是否重要
- 是否需要提醒
- 是否重复
- 是否适合打扰

目标：

主动但不过度打扰。

------------------------------------------------------------------------

# 9. Behavior Engine

根据：

- Personality
- Internal State
- Relationship State
- Situation
- Attention
- Prepared factual context

决定语义行为：

- 说话
- 沉默
- 等待
- 动作
- 表情
- 工具请求

Behavior proposal 仍不等于 Permission。

------------------------------------------------------------------------

# 10. Permission Layer

核心原则：

```text
Intent != Permission
意图 != 权限
```

角色想做某事、Memory 中记录了某事、Event 描述了某事，都不代表系统允许执行敏感操作。

所有敏感操作经过独立权限边界。

------------------------------------------------------------------------

# 11. Embodiment Layer

负责：

- Live2D
- VRM
- 3D
- 声音
- 动作
- 表情

上层输出语义，例如：

```text
emotion: annoyed
motion: look_away
```

底层负责具体实现。

------------------------------------------------------------------------

# 12. Event Bus

适合异步事实 / 通知传播的模块通过 EventBus 解耦。

核心规则：

```text
Event
事实 / 通知

!=

Command / Query / Request
命令 / 查询 / 请求
```

Event 不代表 Permission。

需要同步请求、治理操作、返回值或权限判断时，应保留显式 capability boundary，避免把所有交互强行塞进 EventBus。

Phase 4 Memory governance 因此使用显式 request/response routing，而不是 EventBus RPC。

------------------------------------------------------------------------

# 13. Provider / Adapter

外部能力应通过稳定边界替换：

- LLM Provider
- TTS
- Vision
- Avatar
- Tools
- App Adapter
- future retrieval/index adapters

事实 Memory persistence 本身由 Memory Repository / Persistence Adapter 所有，而不是 Provider Layer 所有。

------------------------------------------------------------------------

# 14. Local / Cloud

系统目标支持：

```text
Local Core
本地核心

+

Optional Online Intelligence
可选在线智能
```

云服务失败时应可安全降级。

当前实现具备 Provider failure isolation，但尚未实现 local-model / cloud-fallback router。

------------------------------------------------------------------------

# 15. Phase 4 Implemented Baseline

The sections above describe the long-term target architecture.

As of the Phase 4 accepted baseline, the implemented runtime includes:

```text
Phase 0
Desktop / WebSocket foundation

Phase 1
Provider-neutral real LLM path

Phase 2
Runtime Event System

Phase 3
Character + Temporal Context + Prompt Composition

Phase 4
Factual Memory
Persistence
Retrieval
Automatic Learning
Governance
Health / Failure Isolation
Desktop Memory Management
```

Latest confirmed implementation checkpoint before Phase 4 final documentation:

```text
3d7435c fix(memory): use platform app data for default database
```

## 15.1 Current Desktop Runtime

Chat path:

```text
App.xaml.cs
  -> MainWindow
  -> MainWindowViewModel
  -> AgentClientService
  -> IAgentConnection
  -> WebSocketAgentConnection
  -> AgentMessage
```

Memory management path:

```text
Memory UI
  -> MemoryManagementViewModel
  -> IMemoryClientService
  -> MemoryClientService
  -> correlated AgentClientService request
  -> shared IAgentConnection
  -> WebSocketAgentConnection
```

Responsibilities:

- `App.xaml.cs`: Desktop composition root;
- `MainWindow`: WPF view and UI event forwarding;
- `MainWindowViewModel`: chat presentation and Memory ViewModel coordination;
- `AgentClientService`: application-level connection, chat, independent receive loop, and correlated request handling;
- `IAgentConnection`: transport abstraction;
- `WebSocketAgentConnection`: WebSocket + JSON transport;
- `MemoryClientService`: typed Memory application service hiding raw protocol/JSON details from the Memory ViewModel;
- `MemoryManagementViewModel`: list/detail/edit/delete/history presentation state.

The independent Desktop receive loop remains intentional for future proactive messages.

Memory UI local state changes only after successful server responses.

## 15.2 Current Python Runtime Composition

Current composition root:

```text
main.py
  -> Settings
  -> Logging
  -> active Character loading / selection
  -> PromptContextComposer
  -> SystemClock
  -> upgrade Memory database to Alembic head
  -> Memory engine / session factory
  -> SQLiteMemoryRepository
  -> MemoryHealthTracker
  -> MemoryRetrievalPolicy
  -> MemoryRetrievalService
  -> ResilientMemoryRetriever
  -> DeepSeekProvider
  -> optional Automatic Memory Learning pipeline
  -> EventBus
  -> Agent
  -> MemoryGovernanceService
  -> HealthAwareMemoryGovernanceService
  -> MemoryProtocolHandler
  -> RuntimeMessageRouter
  -> WebSocketServer
```

Important startup boundaries:

```text
Character loading
角色加载
-> before Provider construction

Memory schema upgrade
Memory schema 升级
-> before Repository access
-> before Provider construction
```

This prevents startup from entering a known broken persistence state and avoids unnecessary Provider creation when an earlier fail-fast bootstrap step fails.

Composition-root lifetime remains explicit:

```text
create Provider
  -> create EventBus / Agent / governance / router / server
  -> await EventBus.start()
  -> await WebSocketServer.run()
  -> finally EventBus.close()
  -> finally Provider.aclose()
```

## 15.3 Character / Temporal / Composer Boundary

Implemented Phase 3 boundaries remain in force:

```text
CharacterDefinition
Character TOML loading
active Character selection
Clock / SystemClock
TemporalContext
PromptContextComposer
```

Rules:

- Character definition is domain data;
- Character does not own Memory;
- Character does not own Internal State;
- Character intent does not grant Tool authority;
- Character fiction cannot override runtime truth;
- `Clock` is the runtime current-time authority;
- `TemporalContext` is a derived per-request snapshot;
- `PromptContextComposer` consumes prepared context only;
- Composer does not query persistence, perform Memory learning, resolve conflicts, call Provider, publish Events, permission-check, or execute Tools.

Current system context can include:

```text
[Runtime Rules]
[Temporal Context]
[Character Data Boundary]
[Character ...]
[Memory Context]          when available
```

The original user message remains a separate `user` role message.

## 15.4 Memory Domain Model

Implemented concepts:

```text
Memory
MemoryRevision
MemoryDomain
MemoryScope
MemoryScopeKind
MemoryLifecycle
MemorySource
MemoryIdentityKey
```

Domain / scope contract:

```text
USER_PROFILE      -> GLOBAL_USER
WORKING_CONTEXT   -> GLOBAL_USER
EPISODIC          -> GLOBAL_USER
RELATIONSHIP      -> CHARACTER
```

Lifecycle:

```text
ACTIVE
SUPERSEDED
EXPIRED
DELETED
```

Successful correction/edit semantics:

```text
old ACTIVE revision
旧活动版本
    ↓ atomic replacement
    ↓ 原子替换
old -> SUPERSEDED

new revision
新版本
    -> ACTIVE
```

Source authority, highest to lowest:

```text
USER_EDIT
USER_EXPLICIT
AUTOMATIC_EXPLICIT_FACT
SYSTEM_OBSERVED
```

`MemoryIdentityKey` represents logical factual identity for controlled automatic learning. It is separate from persistent `memory_id`.

## 15.5 Memory Persistence and Schema

Persistence boundary:

```text
Memory Domain
记忆领域
    ↓
MemoryRepository
持久化契约
    ↓
SQLiteMemoryRepository
SQLite 适配器
    ↓
SQLAlchemy
    ↓
SQLite
```

SQLAlchemy types do not define the public Memory domain contract.

Schema evolution is owned by Alembic:

```text
0001_memory
  -> 0002_identity_key
  -> 0003_identity_unique
```

Runtime startup executes schema upgrade before repository use.

Default database path:

```text
platformdirs
  -> operating-system user application-data directory
  -> Desktop Companion Agent
  -> memory.db
```

Explicit override:

```text
DCA_MEMORY_DATABASE_PATH
```

The default database is not stored inside the Git repository or source tree.

SQLite remains the factual durable source of truth. Future vector indexes or embeddings, if introduced, must remain derived retrieval aids rather than the only factual source.

## 15.6 Memory Retrieval / Prompt Use

Chat retrieval path:

```text
User Message
用户消息
    ↓
Agent
    ↓
MemoryRetrievalService
    ↓
MemoryRetrievalPolicy
    ↓
eligible ACTIVE Memory
符合条件的活动 Memory
    ↓
PreparedMemoryContext
准备后的记忆上下文
    ↓
PromptContextComposer
    ↓
LLMRequest
```

Relationship Memory retrieval is constrained to the active Character.

Retrieval is bounded and query-only.

Recoverable retrieval failure:

```text
Memory read failure
记忆读取失败
    ↓
Memory health = DEGRADED
    ↓
empty PreparedMemoryContext
空记忆上下文
    ↓
ordinary chat continues
普通聊天继续
```

## 15.7 Automatic Memory Learning

Automatic learning runs after a valid Provider response when enabled.

Implemented path:

```text
completed chat turn
完整聊天轮次
    ↓
LLMMemoryCandidateExtractor
    ↓
MemoryCandidate
    ↓
MemoryLearningPolicy
    ↓
ExistingMemoryResolver
    ↓
MemoryConflictPolicy
    ↓
MemoryLearningService
    ↓
MemoryRepository
    ↓
SQLite
```

Candidate extraction has no unrestricted direct persistence authority.

Configuration:

```text
DCA_AUTOMATIC_LEARNING_ENABLED=true
```

When disabled:

```text
automatic learning stops
自动学习停止

existing retrieval continues
已有记忆仍可检索

manual governance continues
手动治理仍可使用

ordinary chat continues
普通聊天继续
```

`ResilientMemoryTurnLearner` prevents a recoverable learning failure from retroactively invalidating an already-valid chat response.

## 15.8 Memory Health and Failure Isolation

Tracked capabilities:

```text
RETRIEVAL
AUTOMATIC_LEARNING
GOVERNANCE
```

Health states:

```text
AVAILABLE
DEGRADED
UNAVAILABLE
```

Failure semantics:

```text
Retrieval failure
-> fail-open for ordinary chat

Automatic-learning failure
-> fail-open for valid chat response

Governance persistence failure
-> fail-closed for requested operation
-> never claim durable success
```

Health tracking records capability status; it does not itself own retry, recovery, logging, or business decisions.

## 15.9 Explicit Runtime Request Routing

Implemented routing boundary:

```text
WebSocketServer
    ↓
RuntimeMessageRouter
    ├── chat
    │    -> Agent
    │
    └── memory.*
         -> MemoryProtocolHandler
```

This boundary exists because request/response operations are not Runtime Events.

Memory protocol capabilities:

```text
memory.list
memory.inspect
memory.edit
memory.delete
memory.history
```

Responses correlate to requests through:

```text
request Message.id
  -> response payload.request_id
```

Stable Memory-safe error codes include:

```text
MEMORY_INVALID_REQUEST
MEMORY_NOT_FOUND
MEMORY_DELETED
MEMORY_INVALID_STATE
MEMORY_OPERATION_FAILED
```

## 15.10 Provider Layer

```text
Agent
  -> LLMProvider
  -> LLMRequest / LLMResponse
  -> DeepSeekProvider
  -> AsyncOpenAI
  -> DeepSeek API
```

Boundary rules:

- public Agent boundaries remain provider-neutral;
- vendor exceptions are translated inside adapters;
- Provider failures cross into Agent as provider-neutral errors;
- Desktop receives stable safe codes/messages;
- API secrets are unwrapped only at provider construction;
- Provider lifetime is owned by the composition root.

Current Provider behavior:

```text
async
non-streaming
thinking disabled by default
60-second default application timeout
zero automatic retries
asyncio cancellation propagation
```

Memory Retrieval remains provider-independent.
Automatic Memory Learning reuses the Provider boundary for candidate extraction
without making Memory own Provider construction.

## 15.11 Runtime Event Model and EventBus

Runtime Events remain facts / notifications describing something that happened.

They are not:

```text
commands
permission grants
synchronous requests
return-value channels
```

Current EventBus baseline remains:

```text
Producer
  -> EventPublisher.publish(event)
  -> bounded in-memory queue
  -> single dispatcher
  -> exact-type subscribers
```

Accepted properties remain:

- asynchronous in-process service;
- bounded queue;
- fail-fast queue-full admission;
- exact-type routing;
- static subscription registration before running;
- sibling handlers for one Event may run concurrently;
- ordinary handler failure is isolated;
- graceful close drains accepted Events;
- no Event persistence / replay in the current baseline.

Memory governance and request correlation do not use EventBus as RPC.

## 15.12 Current Cross-Process Chat Flow

```text
WPF UI
  -> AgentClientService
  -> WebSocketAgentConnection
  -> ws://127.0.0.1:8765
  -> WebSocketServer
  -> RuntimeMessageRouter
  -> Agent.process_message()
  -> Clock.now()
  -> TemporalContext
  -> Memory Retrieval
  -> PreparedMemoryContext
  -> active CharacterDefinition
  -> PromptContextComposer
  -> LLMRequest
  -> LLMProvider.generate()
  -> DeepSeekProvider
  -> DeepSeek API
  -> LLMResponse
  -> optional Automatic Memory Learning
  -> protocol Message
  -> WebSocketAgentConnection
  -> MainWindowViewModel
  -> WPF UI
```

Task 11 real acceptance proved that durable Memory can survive a complete Python Core restart and subsequently participate in this real Provider-backed path.

## 15.13 Current Cross-Process Memory Governance Flow

```text
WPF Memory UI
  -> MemoryManagementViewModel
  -> MemoryClientService
  -> AgentClientService.SendRequestAsync()
  -> correlated AgentMessage
  -> WebSocketAgentConnection
  -> WebSocketServer
  -> RuntimeMessageRouter
  -> MemoryProtocolHandler
  -> HealthAwareMemoryGovernanceService
  -> MemoryGovernanceService
  -> MemoryRepository
  -> SQLite
  -> correlated result / safe error
  -> WPF Memory UI
```

Implemented WPF operations:

```text
list
inspect
edit
history
delete
```

The Desktop does not treat local optimistic state as committed durable truth before server success.

## 15.14 Accepted Runtime Validation

Phase 4 Task 11 final acceptance:

```text
355 pytest tests passed
Ruff passed
mypy passed on 111 source files
Desktop build succeeded
git diff --check clean
```

Real runtime acceptance included:

```text
automatic explicit learning
non-explicit input not persisted
complete Core restart persistence
Memory retrieval into Provider context
revision/correction behavior
delete behavior
Character-scoped Relationship isolation
automatic-learning-disabled mode
retrieval/learning/governance failure semantics
WebSocket Memory governance
WPF Memory governance
Provider-safe errors
runtime log safety
```

Task 12 storage-location correction was additionally verified against the full Python regression and a real fresh default-path bootstrap.

## 15.15 Still Not Implemented

The following remain design-level or future-phase work:

- Internal State business logic;
- Situation Engine;
- Attention Engine;
- Behavior Engine;
- Perception Layer;
- Permission Layer;
- Action / Tool Layer;
- Embodiment Layer;
- local-model / cloud-fallback routing;
- Voice;
- Desktop Event Bridge;
- dynamic Character switching UI;
- Character hot reload;
- Memory backup/restore UI;
- Memory cloud synchronization;
- multi-user accounts;
- vector retrieval / embeddings / RAG;
- encryption-at-rest feature work;
- Scheduler;
- Markdown / LaTeX rich rendering in WPF.

Event System intentionally still omits:

- Event persistence / replay;
- wildcard routing;
- subscriber priority;
- dynamic unsubscribe;
- automatic Event retry;
- multiple dispatch workers;
- restart / supervision policy.

Do not infer implementation merely because a module exists in the long-term target diagram.

## 15.16 Boundary Rules for Phase 5 and Later

Future phases must extend the accepted Phase 0-4 runtime without collapsing layers.

Persistent rules:

```text
Character != Memory
Character != Internal State
Memory != Situation
Relationship Memory != Relationship Internal State

Event != Command
Intent != Permission
Memory Context != Permission
Situation != Permission

Real State != Fictional State
```

In particular:

- UI must not own Agent reasoning, Memory business rules, Provider internals, Tool execution, or Permission logic;
- WebSocket transport must not own Agent/Provider/Memory construction;
- provider-specific code must not become Agent Core public API;
- `PromptContextComposer` must consume prepared context rather than become a service locator;
- `Clock` remains current-time authority;
- Memory remains factual context and persistence, not Situation/Behavior orchestration;
- Runtime Events remain facts/notifications;
- Situation Engine should interpret facts/events, not execute Behavior or Tools;
- sensitive actions must pass through a future Permission boundary;
- real and fictional state remain separate.

The active next roadmap phase is Phase 5 - Situation Engine.
