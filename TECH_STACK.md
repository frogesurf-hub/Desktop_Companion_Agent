# Desktop Companion Agent Technology Stack

## 1. Overview

Desktop Companion Agent 采用分层架构：

    Desktop Layer
    (C# WPF / WinUI)

            ↓

    IPC / WebSocket

            ↓

    Agent Core
    (Python)

            ↓

    LLM / Memory / Behavior / Tools

设计目标：

-   Windows 深度集成
-   AI 能力灵活扩展
-   本地运行能力
-   云端模型增强
-   模块可替换

------------------------------------------------------------------------

# 2. Desktop Layer

## Technology

选择：

    C# WPF / WinUI

## Responsibilities

负责：

-   桌面窗口
-   透明窗口
-   系统托盘
-   开机启动
-   Windows API 调用
-   文件系统交互
-   软件状态检测
-   UI Automation
-   权限请求
-   用户设置界面

## Reason

项目主要运行环境：

    Windows 11

未来需要：

-   检测当前软件
-   获取窗口信息
-   操作 Windows 应用
-   文件访问
-   系统交互

C# 在 Windows 生态具有较强优势。

------------------------------------------------------------------------

# 3. Agent Core

## Technology

选择：

    Python

## Responsibilities

负责：

-   Agent 核心逻辑
-   LLM 调用
-   Memory System
-   Situation Engine
-   Attention Engine
-   Behavior Engine
-   情绪系统
-   关系系统
-   工具管理

## Reason

Python 拥有成熟 AI 生态：

-   LLM SDK
-   NLP
-   向量数据库
-   Agent Framework
-   数据处理工具

适合作为 Agent 大脑。

------------------------------------------------------------------------

# 4. Communication Layer

## Technology

初期：

    Local IPC / WebSocket

## Purpose

连接：

    C# Desktop

            ↕

    Python Agent Core

通信采用事件形式。

------------------------------------------------------------------------

# 5. Database

## Primary Database

选择：

    SQLite

用途：

保存：

-   用户资料
-   角色配置
-   记忆
-   情绪状态
-   关系状态
-   权限设置
-   软件配置

## Future Extension

向量数据库：

-   FAISS
-   Chroma
-   Qdrant

用途：

-   长期记忆检索
-   语义搜索
-   相关经历召回

------------------------------------------------------------------------

# 6. LLM Provider

采用 provider-neutral 抽象接口：

    LLMProvider

不绑定单一模型。

Phase 1 已实现：

    Agent Core

    ↓

    LLMProvider Protocol

    ↓

    DeepSeekProvider

    ↓

    openai.AsyncOpenAI

    ↓

    DeepSeek API

当前 Provider 契约：

    async generate(LLMRequest) -> LLMResponse

当前 Phase 1 行为：

-   非流式
-   默认 60 秒超时
-   SDK 自动重试关闭
-   asyncio cancellation 向上传播
-   Provider 错误使用统一 vendor-neutral error hierarchy

Future providers may include:

    OpenAI-compatible providers
    Claude
    Gemini
    Local Model

------------------------------------------------------------------------

# 7. Default Model Strategy

## Primary Provider

Phase 1 实际实现：

    DeepSeek API

默认模型：

    deepseek-v4-flash

当前运行时模型别名（Phase 2 checkpoint 后 maintenance）：

- deepseek-flash

Python client：

    openai.AsyncOpenAI

OpenAI-compatible base URL：

    https://api.deepseek.com

默认：

    thinking = false
    stream = false
    timeout = 60s
    automatic retry = 0

原因：

-   国内访问方便
-   API 成本较低
-   中文能力优秀
-   适合作为日常 Agent 模型

## Principle

不要让核心系统依赖 DeepSeek。

保持：

    Model Independent

------------------------------------------------------------------------

# 8. Local AI

支持：

    Ollama
    LM Studio
    llama.cpp

用途：

-   离线模式
-   隐私模式
-   云端 API 故障备用

系统模式：

    Offline
    Local AI
    Hybrid
    Cloud

------------------------------------------------------------------------

# 9. Avatar System

## First Choice

    Live2D

用途：

-   桌宠形象
-   表情
-   动作
-   情绪表现

## Future Support

    VRM
    3D Avatar
    Pixel Avatar

通过：

    Avatar Adapter

隔离。

------------------------------------------------------------------------

# 10. Agent Architecture

核心逻辑自主实现。

核心模块：

    Event Bus

    Situation Engine

    Attention Engine

    Behavior Engine

    Memory System

    Permission System

------------------------------------------------------------------------

# 11. Tool System

统一接口：

    Tool Interface

支持：

低风险：

-   Web Search
-   文件搜索
-   打开网页
-   打开程序

中风险：

-   文件读取
-   文件分析
-   代码分析

高风险：

-   文件修改
-   Shell
-   UI Automation
-   Computer Use

所有工具经过：

    Permission Layer

------------------------------------------------------------------------

# 12. Development Environment

OS:

    Windows 11

IDE:

    Visual Studio
    VS Code

Languages:

    C#
    Python

Version Control:

    Git

Database:

    SQLite

------------------------------------------------------------------------

# 13. Development Principles

## Modular

模块独立：

-   Memory
-   Emotion
-   Avatar
-   LLM
-   Tools
-   Perception

## Provider Based

外部能力：

-   LLM Provider
-   TTS Provider
-   Vision Provider
-   Avatar Provider

## Local First

云服务只是增强。

## Security First

遵守：

    Intent != Permission

------------------------------------------------------------------------

# 14. Current Technology Decision

  Module            Technology
  ----------------- --------------------------------
  Desktop           C# WPF / WinUI
  Agent Core        Python
  Communication     IPC / WebSocket
  Database          SQLite
  Primary LLM       DeepSeek API
  Backup LLM        OpenAI / Claude / Gemini
  Local AI          Ollama / LM Studio / llama.cpp
  Avatar            Live2D
  Version Control   Git

------------------------------------------------------------------------

# 15. Future Expansion

预留：

-   Plugin System
-   MCP
-   Multi Character
-   Custom Model
-   Custom Avatar
-   Custom Tool
-   App Adapter
-   Local Agent
