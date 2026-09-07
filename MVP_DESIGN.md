# Desktop Companion Agent - MVP Design

## 1. MVP Overview

## Project Goal

Desktop Companion Agent 的最终目标：

创建一个运行在 Windows 桌面的 AI 陪伴 Agent。

它不是传统聊天机器人，而是：

-   长驻桌面的智能伙伴
-   可以感知用户部分电脑状态
-   根据情境主动互动
-   支持文字交流
-   具备角色、自定义、记忆、情绪等能力

但是 MVP 阶段不实现完整系统。

MVP 的目标：

> 验证 Desktop Layer + Agent Core + LLM 通信链路。

------------------------------------------------------------------------

# 2. MVP Scope

## Included

## Desktop Layer

技术：

    C# WPF

功能：

-   启动桌面程序
-   显示基础窗口
-   输入文本
-   显示 Agent 回复

------------------------------------------------------------------------

## Agent Core

技术：

    Python

功能：

-   接收用户输入
-   管理 Agent 基础逻辑
-   调用 LLM
-   返回回复

------------------------------------------------------------------------

## LLM Provider

第一阶段：

    DeepSeek API

通过抽象接口设计。

未来支持：

-   OpenAI API
-   Claude API
-   Gemini API
-   Local Model

------------------------------------------------------------------------

## Communication

MVP 使用：

    WebSocket

结构：

    C# Desktop

            ↕

    Python Agent Core

原因：

未来需要支持：

-   主动消息
-   状态事件
-   实时通信

提前建立事件通信模式。

------------------------------------------------------------------------

# 3. MVP Not Included

以下功能暂不实现：

## 不包含：

### Computer Perception

暂不检测：

-   当前软件
-   鼠标键盘
-   浏览记录
-   文件变化

------------------------------------------------------------------------

### Memory System

暂不实现：

-   长期记忆
-   向量数据库
-   用户画像

------------------------------------------------------------------------

### Emotion System

暂不实现：

-   心情变化
-   天气影响
-   虚拟经历

------------------------------------------------------------------------

### Avatar System

暂不实现：

-   Live2D
-   动画
-   声音
-   桌宠交互

------------------------------------------------------------------------

### Tool System

暂不开放：

-   文件操作
-   浏览器控制
-   系统操作

------------------------------------------------------------------------

# 4. MVP Architecture

                     User

                      |
                      |

              C# WPF Desktop

                      |

                  WebSocket

                      |

              Python Agent Core

                      |

               LLM Provider API

                      |

                 DeepSeek API

------------------------------------------------------------------------

# 5. Module Responsibility

## DesktopCompanion.Desktop

负责：

-   Windows窗口
-   UI显示
-   用户输入
-   消息发送
-   消息接收

------------------------------------------------------------------------

## AgentCore

负责：

-   Agent入口
-   对话流程
-   LLM调用
-   基础配置

------------------------------------------------------------------------

## Communication Layer

负责：

-   消息格式
-   长连接
-   状态同步

------------------------------------------------------------------------

# 6. First Milestone

完成标准：

启动程序：

    Desktop App

输入：

    你好

流程：

    用户输入

    ↓

    C# WPF

    ↓

    WebSocket

    ↓

    Python Agent

    ↓

    DeepSeek API

    ↓

    Python返回

    ↓

    C#显示回复

最终效果：

桌面程序能够完成一次完整 AI 对话。

------------------------------------------------------------------------

# 7. Development Principles

## Keep Modules Independent

避免：

-   UI绑定Agent逻辑
-   API绑定具体模型
-   数据库绑定业务

------------------------------------------------------------------------

## Prepare For Expansion

MVP代码需要预留：

未来模块：

    Memory

    Emotion

    Personality

    Avatar

    Tools

    Permission

    Perception

------------------------------------------------------------------------

## Security First

任何系统操作：

必须经过：

    User Permission Layer

Agent主动性不能覆盖用户权限。

------------------------------------------------------------------------

# 8. After MVP Roadmap

MVP完成后：

Phase 1:

-   Agent基础框架
-   角色配置
-   Prompt系统

Phase 2:

-   Memory System
-   用户信息

Phase 3:

-   Perception System
-   软件状态检测

Phase 4:

-   Emotion System
-   主动行为

Phase 5:

-   Avatar
-   Voice
-   Desktop Companion体验

------------------------------------------------------------------------

# 9. MVP Definition

MVP不是最终产品。

它的意义：

证明：

    Desktop
    +
    Agent Core
    +
    LLM
    +
    Communication

这条技术路线可行。

之后所有复杂功能都建立在该基础之上。
