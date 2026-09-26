# Desktop Companion Agent Communication Protocol

## 1. Overview

This document defines the implemented cross-process protocol between:

```text
C# WPF Desktop
桌面客户端

    ↕ local WebSocket / JSON

Python Agent Core
智能体核心
```

Current endpoint defaults to:

```text
ws://127.0.0.1:8765
```

The protocol currently supports:

```text
chat request / response
聊天请求 / 响应

Memory governance request / response
记忆治理请求 / 响应

safe error messages
安全错误消息
```

The Python in-process EventBus is a separate runtime mechanism.

```text
WebSocket protocol
跨进程请求 / 响应

!=

Runtime EventBus
进程内事实 / 通知
```

Do not use EventBus as hidden request/response RPC.

---

## 2. Message Envelope

All implemented cross-process messages use the same JSON envelope:

```json
{
  "id": "message-uuid-or-request-id",
  "type": "message_type",
  "timestamp": "ISO8601 timestamp",
  "source": "sender",
  "payload": {}
}
```

Fields:

| Field | Meaning |
| --- | --- |
| `id` | Unique message/request identity |
| `type` | Protocol message type |
| `timestamp` | Message timestamp |
| `source` | Logical sender |
| `payload` | Message-type-specific object |

Python `Message` serializes all five fields.

The Desktop uses the same envelope through `AgentMessage`.

---

## 3. Runtime Routing

Python routes implemented request types through:

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

Unsupported request families return an `error` Message.

This routing boundary is explicit because:

```text
request / command / query
!=
Runtime Event
```

---

## 4. Chat Protocol

### 4.1 Chat Request

Type:

```text
chat
```

Payload:

```json
{
  "message": "你好"
}
```

Example envelope:

```json
{
  "id": "request-id",
  "type": "chat",
  "timestamp": "2026-09-25T12:00:00+00:00",
  "source": "desktop",
  "payload": {
    "message": "你好"
  }
}
```

### 4.2 Chat Success Response

Type:

```text
response
```

Payload:

```json
{
  "message": "你好，我在这里。"
}
```

Example:

```json
{
  "id": "response-id",
  "type": "response",
  "timestamp": "2026-09-25T12:00:01+00:00",
  "source": "Desktop Companion",
  "payload": {
    "message": "你好，我在这里。"
  }
}
```

The ordinary chat response currently does not use `payload.request_id`.

Memory governance requests use explicit correlation as documented below.

---

## 5. Provider-Safe Chat Errors

Provider failures are translated into stable safe protocol errors.

Error type:

```text
error
```

Current Provider error codes:

| Code | Safe message |
| --- | --- |
| `PROVIDER_NOT_CONFIGURED` | `AI provider is not configured.` |
| `PROVIDER_AUTHENTICATION_FAILED` | `AI provider authentication failed.` |
| `PROVIDER_QUOTA_EXHAUSTED` | `AI provider quota or balance is insufficient.` |
| `PROVIDER_RATE_LIMITED` | `AI provider is rate-limited. Please try again later.` |
| `PROVIDER_TIMEOUT` | `AI provider request timed out.` |
| `PROVIDER_UNAVAILABLE` | `AI provider is temporarily unavailable.` |
| `PROVIDER_REQUEST_FAILED` | `AI provider rejected the request.` |
| `PROVIDER_INVALID_RESPONSE` | `AI provider returned an invalid response.` |
| `PROVIDER_ERROR` | `AI provider request failed.` |

Example:

```json
{
  "id": "response-id",
  "type": "error",
  "timestamp": "2026-09-25T12:00:01+00:00",
  "source": "Desktop Companion",
  "payload": {
    "code": "PROVIDER_TIMEOUT",
    "message": "AI provider request timed out."
  }
}
```

Provider-internal SDK exceptions, API keys, Authorization headers, raw response bodies, full prompts, and reasoning content must not become the Desktop protocol contract.

---

## 6. Memory Governance Protocol

Phase 4 implements explicit Memory governance request/response capabilities:

```text
memory.list
memory.inspect
memory.edit
memory.delete
memory.history
```

Success result types:

```text
memory.list.result
memory.inspect.result
memory.edit.result
memory.delete.result
memory.history.result
```

Memory protocol responses correlate to the original request through:

```text
request Message.id
    ↓
response payload.request_id
```

This allows the Desktop to run correlated request/response operations while preserving the independent receive loop.

---

## 7. Memory Domain Values

Implemented protocol domain strings:

```text
user_profile
working_context
episodic
relationship
```

Scope kinds:

```text
global_user
character
```

Domain/scope compatibility:

```text
user_profile     -> global_user
working_context  -> global_user
episodic         -> global_user
relationship     -> character
```

Lifecycle strings:

```text
active
superseded
expired
deleted
```

Source strings:

```text
user_edit
user_explicit
automatic_explicit_fact
system_observed
```

---

## 8. Memory Scope Payload

Global-user scope:

```json
{
  "kind": "global_user"
}
```

Character scope:

```json
{
  "kind": "character",
  "character_id": "aria"
}
```

A `global_user` scope must not define a Character ID.

A `character` scope requires a non-empty `character_id`.

---

## 9. Memory Entry Payload

A serialized visible Memory entry has this shape:

```json
{
  "memory_id": "uuid",
  "domain": "user_profile",
  "scope": {
    "kind": "global_user",
    "character_id": null
  },
  "identity_key": "preferred_language",
  "latest_revision": {
    "revision_number": 2,
    "content": "The user prefers C#.",
    "source": "user_edit",
    "lifecycle": "active",
    "recorded_at": "2026-09-25T12:00:00+00:00",
    "occurred_at": null
  }
}
```

`identity_key` may be `null`.

`occurred_at` may be `null`.

Deleted revisions have `content = null` according to the Memory domain contract.

---

## 10. `memory.list`

### Request

Type:

```text
memory.list
```

Allowed payload fields:

```text
domain
scope
```

Both are optional.

Examples:

List all visible Memory:

```json
{}
```

Filter by domain:

```json
{
  "domain": "working_context"
}
```

Filter by Character Relationship scope:

```json
{
  "domain": "relationship",
  "scope": {
    "kind": "character",
    "character_id": "aria"
  }
}
```

If both `domain` and `scope` are present, they must be compatible.

### Success Response

Type:

```text
memory.list.result
```

Payload:

```json
{
  "request_id": "original-request-id",
  "memories": []
}
```

`memories` contains visible non-deleted Memory entries.

---

## 11. `memory.inspect`

### Request

Type:

```text
memory.inspect
```

Exact payload:

```json
{
  "memory_id": "memory-uuid"
}
```

### Success Response

Type:

```text
memory.inspect.result
```

Payload:

```json
{
  "request_id": "original-request-id",
  "memory": {
    "memory_id": "memory-uuid",
    "domain": "working_context",
    "scope": {
      "kind": "global_user",
      "character_id": null
    },
    "identity_key": "task11_acceptance_code",
    "latest_revision": {
      "revision_number": 1,
      "content": "Example content",
      "source": "automatic_explicit_fact",
      "lifecycle": "active",
      "recorded_at": "2026-09-25T12:00:00+00:00",
      "occurred_at": null
    }
  }
}
```

---

## 12. `memory.edit`

### Request

Type:

```text
memory.edit
```

Exact payload:

```json
{
  "memory_id": "memory-uuid",
  "content": "Corrected factual content"
}
```

`content` must be a non-empty string.

### Success Response

Type:

```text
memory.edit.result
```

Payload:

```json
{
  "request_id": "original-request-id",
  "memory": {
    "memory_id": "memory-uuid",
    "domain": "working_context",
    "scope": {
      "kind": "global_user",
      "character_id": null
    },
    "identity_key": "task11_acceptance_code",
    "latest_revision": {
      "revision_number": 2,
      "content": "Corrected factual content",
      "source": "user_edit",
      "lifecycle": "active",
      "recorded_at": "2026-09-25T12:10:00+00:00",
      "occurred_at": null
    }
  }
}
```

Revision/conflict semantics are owned by Python Memory governance, not by the Desktop protocol model.

---

## 13. `memory.delete`

### Request

Type:

```text
memory.delete
```

Exact payload:

```json
{
  "memory_id": "memory-uuid"
}
```

### Success Response

Type:

```text
memory.delete.result
```

Payload contains:

```json
{
  "request_id": "original-request-id",
  "memory": {
    "memory_id": "memory-uuid",
    "domain": "working_context",
    "scope": {
      "kind": "global_user",
      "character_id": null
    },
    "identity_key": "task11_acceptance_code",
    "latest_revision": {
      "revision_number": 3,
      "content": null,
      "source": "user_edit",
      "lifecycle": "deleted",
      "recorded_at": "2026-09-25T12:15:00+00:00",
      "occurred_at": null
    }
  }
}
```

Deletion semantics remain a Memory governance/domain concern.

---

## 14. `memory.history`

### Request

Type:

```text
memory.history
```

Exact payload:

```json
{
  "memory_id": "memory-uuid"
}
```

### Success Response

Type:

```text
memory.history.result
```

Payload:

```json
{
  "request_id": "original-request-id",
  "memory_id": "memory-uuid",
  "revisions": [
    {
      "revision_number": 1,
      "content": "Original factual content",
      "source": "automatic_explicit_fact",
      "lifecycle": "superseded",
      "recorded_at": "2026-09-25T12:00:00+00:00",
      "occurred_at": null
    },
    {
      "revision_number": 2,
      "content": "Corrected factual content",
      "source": "user_edit",
      "lifecycle": "active",
      "recorded_at": "2026-09-25T12:10:00+00:00",
      "occurred_at": null
    }
  ]
}
```

Normal governance history follows the Memory deletion/redaction contract and must not be treated as an unrestricted forensic export.

---

## 15. Memory Protocol Errors

Memory protocol failures return:

```text
type = error
```

and include correlation:

```json
{
  "request_id": "original-request-id",
  "code": "MEMORY_INVALID_REQUEST",
  "message": "Invalid Memory request."
}
```

Stable Phase 4 codes:

| Code | Safe message |
| --- | --- |
| `MEMORY_INVALID_REQUEST` | `Invalid Memory request.` |
| `MEMORY_NOT_FOUND` | `Memory does not exist.` |
| `MEMORY_DELETED` | `Memory is deleted.` |
| `MEMORY_INVALID_STATE` | `Memory is in an invalid state for this operation.` |
| `MEMORY_OPERATION_FAILED` | `Memory operation failed.` |

Raw SQLite, SQLAlchemy, filesystem, traceback, or other infrastructure diagnostics must not be exposed through these errors.

---

## 16. Base WebSocket Input Errors

The WebSocket server currently maps malformed transport/protocol input to safe `error` Messages.

Examples include:

```text
Binary messages are not supported
Invalid JSON message
Invalid message structure
Unsupported message type
```

These older/base errors do not all use the same machine-readable `payload.code` convention as Provider and Memory errors.

Do not assume a code exists unless the specific protocol family defines one.

---

## 17. Internal Events Are Not Desktop Protocol Messages

The Python EventBus is internal and in-process.

Current Runtime Events are facts / notifications and do not automatically cross the WebSocket boundary.

Therefore the following are **not current implemented Desktop message families merely because they appear in the long-term architecture**:

```text
event
permission_request
tool_request
memory_update
emotion_change
avatar_action
tool_response
```

They remain future protocol work unless a later phase explicitly defines and implements them.

This prevents architecture sketches from being mistaken for accepted runtime contracts.

---

## 18. Permission Rule

Persistent rule:

```text
Intent != Permission
意图 != 权限
```

Neither Character intent, Memory content, Runtime Events, nor future Situation/Behavior output grants permission to perform sensitive operations.

Future sensitive Tool/Action protocol families must preserve a dedicated Permission boundary.

---

## 19. Protocol Evolution

When adding or changing a cross-process capability:

```text
1. identify ownership and boundary
2. define request / response / error semantics
3. update protocol documentation
4. implement Python and Desktop contracts as applicable
5. add automated tests
6. run cross-process acceptance when needed
7. preserve safe error mapping
```

Do not silently add a protocol shape in one language only.

Do not use EventBus as a substitute for explicit synchronous request/response capabilities.

A formal negotiated protocol-version field is not currently implemented in the accepted envelope.

---

## 20. Current Implemented Summary

Implemented Phase 4 cross-process protocol:

```text
chat
  -> response / error

memory.list
  -> memory.list.result / error

memory.inspect
  -> memory.inspect.result / error

memory.edit
  -> memory.edit.result / error

memory.delete
  -> memory.delete.result / error

memory.history
  -> memory.history.result / error
```

Memory request/response correlation:

```text
request.id
-> response.payload.request_id
```

Current architectural boundary:

```text
Desktop
  -> WebSocket / JSON
  -> RuntimeMessageRouter
       |- chat -> Agent
       `- memory.* -> MemoryProtocolHandler

EventBus remains internal and separate.
```
