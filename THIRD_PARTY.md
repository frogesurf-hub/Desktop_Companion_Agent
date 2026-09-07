# Third Party References

## 1. OpenMeido

Repository:
https://github.com/OpenMeido/OpenMeido

License:
GPL-3.0

Purpose:

作为桌面 AI Companion 的原型参考。

主要参考：

- 桌面透明窗口
- 桌宠形态
- Live2D 集成方式
- Persona 系统
- Memory 系统
- TTS 接入
- LLM Provider 抽象
- 主动互动设计

备注：

可能用于早期原型验证。

如果直接基于其代码开发，需要遵守 GPL-3.0。


---

## 2. Project AIRI

Repository:
https://github.com/moeru-ai/airi

License:
MIT

Purpose:

参考数字生命 / AI Companion 的整体设计。

主要参考：

- Live2D / VRM Avatar
- 角色表现系统
- 插件化思想
- 语音交互
- Agent 扩展能力
- 多平台设计
- 长期数字生命理念

备注：

重点参考设计思想，而不是直接复制完整架构。

AIRI 的目标也是构建自托管 AI Companion，支持 Live2D、VRM、语音交互等能力。:contentReference[oaicite:0]{index=0}


---

## 3. screenpipe

Repository:
https://github.com/screenpipe/screenpipe

License:
待确认具体版本许可证

Purpose:

参考桌面感知系统。

主要参考：

- Screen Context
- Activity Timeline
- Accessibility Tree
- Event-driven Observation
- 本地数据处理

设计启发：

不要持续把整个屏幕发送给 AI。

应该：

事件
↓
上下文
↓
必要时截图
↓
AI理解


---

## 4. Microsoft UFO

Repository:
https://github.com/microsoft/UFO

License:
MIT

Purpose:

参考 Windows Agent 和电脑操作能力。

主要参考：

- Windows UI Automation
- Application Agent
- GUI 操作
- Desktop Environment Understanding

用于未来：

- 软件控制
- 自动操作
- Computer Use


---

## 5. Agent-S

Repository:
https://github.com/simular-ai/Agent-S

License:
Apache-2.0

Purpose:

参考 Computer Use Agent 架构。

主要参考：

- Agent Planning
- GUI Interaction
- Tool Use
- Action Execution

用于未来高级自动化能力。


---

## 6. Open-LLM-VTuber

Repository:
https://github.com/Open-LLM-VTuber/Open-LLM-VTuber

License:
待确认

Purpose:

参考开源 AI VTuber 实现。

主要参考：

- Live2D
- Voice Pipeline
- Offline AI Companion
- Character Customization

适合作为 Avatar + Voice 系统参考。


---

## 7. SillyTavern

Repository:
https://github.com/SillyTavern/SillyTavern

License:
AGPL-3.0

Purpose:

参考角色聊天系统。

主要参考：

- Character Card
- Persona
- Lore
- 长上下文管理
- 用户自定义角色

不直接作为核心架构。


---

## 8. Mem0

Repository:
https://github.com/mem0ai/mem0

License:
Apache-2.0

Purpose:

参考 AI Memory 系统。

主要参考：

- 长期记忆管理
- Memory Retrieval
- 用户信息存储
- 记忆更新策略


---

## 9. LangGraph

Repository:
https://github.com/langchain-ai/langgraph

License:
MIT

Purpose:

参考 Agent Workflow。

主要参考：

- 状态机
- Agent Graph
- 多步骤任务流程
- 状态管理


---

# Reference Philosophy

本项目遵循：