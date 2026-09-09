# Desktop Companion Agent Communication Protocol

## 1. Overview

本文档定义 Desktop Companion Agent 内部模块之间的通信协议。

主要用于：

    C# Desktop Layer

            ↕

    Python Agent Core

未来扩展：

-   Mobile Client
-   Plugin System
-   External Tools
-   Local Services

------------------------------------------------------------------------

# 2. Design Principles

## 2.1 Event Driven

系统采用事件驱动思想。

通信双方不直接调用对方内部方法。

而是发送：

    Message

接收：

    Event

优点：

-   模块解耦
-   易扩展
-   支持主动行为

------------------------------------------------------------------------

## 2.2 JSON Based

第一版本采用：

    JSON

作为数据格式。

原因：

-   人类可读
-   调试方便
-   跨语言支持

------------------------------------------------------------------------

# 3. Message Structure

所有消息统一格式：

``` json
{
    "id": "message_unique_id",
    "type": "message_type",
    "timestamp": "ISO8601",
    "source": "sender",
    "payload": {}
}
```

字段说明：

  字段        说明
  ----------- --------------
  id          消息唯一编号
  type        消息类型
  timestamp   时间
  source      发送方
  payload     具体内容

------------------------------------------------------------------------

# 4. Message Types

## 4.1 Chat Message

用户主动聊天。

Example:

``` json
{
    "id":"001",
    "type":"chat",
    "source":"desktop",
    "payload":{
        "message":"你好"
    }
}
```

流程：

    User

    ↓

    Desktop

    ↓

    Agent Core

------------------------------------------------------------------------

## 4.2 Agent Response

Agent回复。

Example:

``` json
{
    "id":"002",
    "type":"response",
    "source":"agent",
    "payload":{
        "message":"你好，我在这里。"
    }
}
```

------------------------------------------------------------------------

## 4.3 Event Message

系统事件。

用途：

未来：

-   软件启动
-   文件变化
-   时间提醒
-   天气变化

Example:

``` json
{
    "id":"003",
    "type":"event",
    "source":"system",
    "payload":{
        "event":"application_started"
    }
}
```

------------------------------------------------------------------------

## 4.4 Permission Request

需要用户授权。

Example:

``` json
{
    "id":"004",
    "type":"permission_request",
    "source":"agent",
    "payload":{
        "action":"read_file",
        "target":"example.txt"
    }
}
```

原则：

Agent不能绕过权限。

------------------------------------------------------------------------

## 4.5 Tool Request

工具调用。

Example:

``` json
{
    "id":"005",
    "type":"tool_request",
    "source":"agent",
    "payload":{
        "tool":"web_search",
        "parameters":{
            "query":"weather"
        }
    }
}
```

------------------------------------------------------------------------

# 5. Communication Flow

## User Chat

    User

     ↓

    Desktop

     ↓

    chat message

     ↓

    Agent Core

     ↓

    response

     ↓

    Desktop

     ↓

    User

------------------------------------------------------------------------

## Agent主动行为

未来：

    System Event

     ↓

    Agent Core

     ↓

    Decision

     ↓

    Agent Message

     ↓

    Desktop

------------------------------------------------------------------------

# 6. Error Message

统一错误格式：

``` json
{
    "type":"error",
    "payload":{
        "code":"NETWORK_ERROR",
        "message":"Connection failed"
    }
}
```

## 6.1 Phase 1 Provider Errors

Phase 1 中，LLM Provider 失败通过统一 `error` Message 返回 Desktop。

Provider 内部诊断信息、SDK 异常、API Key、Prompt、Reasoning Content 和原始响应体不能通过协议暴露。

Provider error codes：

| Code | Message | Meaning |
| --- | --- | --- |
| `PROVIDER_NOT_CONFIGURED` | `AI provider is not configured.` | Provider 配置缺失或无效 |
| `PROVIDER_AUTHENTICATION_FAILED` | `AI provider authentication failed.` | Provider 身份验证失败 |
| `PROVIDER_QUOTA_EXHAUSTED` | `AI provider quota or balance is insufficient.` | Provider 配额或余额不足 |
| `PROVIDER_RATE_LIMITED` | `AI provider is rate-limited. Please try again later.` | Provider 限流 |
| `PROVIDER_TIMEOUT` | `AI provider request timed out.` | Provider 请求超时 |
| `PROVIDER_UNAVAILABLE` | `AI provider is temporarily unavailable.` | Provider 网络连接失败或服务暂时不可用 |
| `PROVIDER_REQUEST_FAILED` | `AI provider rejected the request.` | Provider 拒绝请求 |
| `PROVIDER_INVALID_RESPONSE` | `AI provider returned an invalid response.` | Provider 返回无法满足统一契约的响应 |
| `PROVIDER_ERROR` | `AI provider request failed.` | 未进一步分类的 Provider 错误 |

Example:

``` json
{
    "type":"error",
    "source":"Desktop Companion",
    "payload":{
        "code":"PROVIDER_TIMEOUT",
        "message":"AI provider request timed out."
    }
}
```

当前 WPF Desktop 仍可只读取 `payload.message`。`payload.code` 为稳定的机器可读错误类别，供后续 UI 行为使用。

Phase 0 已存在的非 Provider 错误将在各自协议维护任务中逐步统一，本节不改变其当前运行行为。

------------------------------------------------------------------------

# 7. Version Control

协议版本：

    v1

未来：

    v2

需要保持兼容。

格式：

``` json
{
    "version":"1.0"
}
```

------------------------------------------------------------------------

# 8. Security Rules

## Permission First

任何涉及：

-   文件
-   网络
-   系统操作

必须经过：

    Permission Layer

Agent自主性：

不能超过：

用户授权。

------------------------------------------------------------------------

# 9. Future Extension

## Memory Event

``` json
{
"type":"memory_update"
}
```

## Emotion Event

``` json
{
"type":"emotion_change"
}
```

## Avatar Event

``` json
{
"type":"avatar_action"
}
```

## Tool Result

``` json
{
"type":"tool_response"
}
```

------------------------------------------------------------------------

# 10. Summary

通信协议负责：

    连接 Desktop

    连接 Agent

    连接未来所有模块

它是整个 Desktop Companion Agent 的基础通信契约。
