# Desktop Companion Agent - MVP Design

## 0. Phase 0 Checkpoint Note

The original MVP definition in this document includes a real LLM provider call.

Phase 0 completed the technical foundation and cross-language vertical slice, but intentionally stopped before DeepSeek integration.

Current verified path:

```text
WPF Desktop
  -> WebSocket
  -> Python Agent Core
  -> echo Agent stub
  -> WebSocket
  -> WPF Desktop
```

Original full MVP target remains:

```text
WPF Desktop
  -> WebSocket
  -> Python Agent Core
  -> LLM Provider abstraction
  -> DeepSeek API
  -> Python Agent Core
  -> WebSocket
  -> WPF Desktop
```

Therefore:

- Phase 0: **complete**
- Original AI MVP: **not yet complete**
- Phase 1 should complete the provider / DeepSeek section without coupling the Agent to one vendor.

See `PROJECT_STATE.md` and `docs/PHASE_0_CHECKPOINT.md` for the current repository state.

---

## 1. MVP Overview

### Project Goal

Desktop Companion Agent 的最终目标：

创建一个运行在 Windows 桌面的 AI 陪伴 Agent。

它不是传统聊天机器人，而是：

- 长驻桌面的智能伙伴
- 可以感知用户部分电脑状态
- 根据情境主动互动
- 支持文字交流
- 具备角色、自定义、记忆、情绪等能力

但是 MVP 阶段不实现完整系统。

MVP 的目标：

> 验证 Desktop Layer + Agent Core + LLM Provider 的完整通信链路。

---

## 2. MVP Scope

### Desktop Layer

技术：

```text
C# WPF
```

功能：

- 启动桌面程序
- 显示基础窗口
- 输入文本
- 显示 Agent 回复
- 与 Agent Core 建立长连接
- 独立接收 Agent 主动消息

Phase 0 status: implemented at foundation level.

### Agent Core

技术：

```text
Python 3.11
```

功能：

- 接收协议消息
- 管理 Agent 基础逻辑
- 调用 LLM Provider
- 返回统一协议消息

Phase 0 status:

- protocol/runtime path implemented
- LLM provider not implemented

### LLM Provider

First provider:

```text
DeepSeek API
```

Required design:

```text
Agent Core
  -> Provider Interface
  -> DeepSeek Adapter
```

Future providers may include:

- OpenAI-compatible providers
- Claude
- Gemini
- Local Model adapters

The Agent Core must not hard-code one provider SDK as its core interface.

### Communication

MVP transport:

```text
WebSocket
```

Reason:

Future runtime requires:

- proactive messages
- state events
- permission requests
- real-time communication

Phase 0 status: implemented and verified end-to-end.

---

## 3. MVP Not Included

Not part of the initial AI MVP unless needed by the provider boundary:

### Computer Perception

- current application detection
- mouse / keyboard activity
- browser history
- file-change observation

### Memory System

- long-term memory
- vector retrieval
- user profile learning

### Emotion System

- mood simulation
- weather influence
- fictional daily-life state

### Avatar System

- Live2D
- animation
- voice
- desktop physical interaction

### Tool System

- file operations
- browser control
- system operations

---

## 4. MVP Architecture

```text
User
  |
WPF Desktop
  |
WebSocket
  |
Python Agent Core
  |
Provider Interface
  |
DeepSeek Adapter
  |
DeepSeek API
```

Phase 0 has implemented everything above through `Python Agent Core`, with a stub Agent response in place of the provider path.

---

## 5. Module Responsibility

### DesktopCompanion.Desktop

Responsible for:

- Windows view / UI
- user input
- message display
- connection state
- protocol transport through an abstraction

Must not own:

- LLM provider logic
- memory
- Agent reasoning

### Agent Core

Responsible for:

- Agent runtime entry
- protocol handling
- Agent processing boundary
- provider orchestration
- future memory / behavior integration

### Communication Layer

Responsible for:

- message envelope
- long-lived connection
- transport errors
- future state/event delivery

---

## 6. MVP Completion Criterion

The original MVP is complete when a user can:

1. start Agent Core
2. start Desktop
3. connect through WebSocket
4. type `你好`
5. send a `chat` message
6. have Python call a real provider through an abstraction
7. receive a real LLM response
8. display the response in WPF

Phase 0 already verifies steps 1-5 and 8 using the echo Agent.

Phase 1 should complete steps 6-7 and re-run the full end-to-end acceptance manually.

---

## 7. Development Principles

### Keep Modules Independent

Avoid:

- UI binding directly to Agent internals
- Agent binding directly to one provider SDK
- persistent storage binding directly to presentation code

### Prepare for Proactivity

Desktop receiving must remain independent of user send actions so future Agent events can arrive without polling.

### Security First

Any future system action must pass through user-visible permission boundaries.

```text
Character Intent != System Permission
```

---

## 8. After MVP

After the original LLM MVP is completed, continue with the repository `ROADMAP.md` rather than the older phase numbering that previously appeared in this document.

The roadmap is the authoritative phase sequence after the 2026-09-08 Phase 0 re-baseline.

---

## 9. MVP Meaning

MVP is not the final companion.

It proves that the following chain is technically stable:

```text
Desktop
+
Agent Core
+
Provider
+
Communication
```

Character, memory, perception, attention, behavior, tools, avatar, and voice are built on top of that verified foundation.
