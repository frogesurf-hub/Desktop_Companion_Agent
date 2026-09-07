# ADR 0002 - WebSocket for Desktop <-> Agent Core Transport

Status: Accepted

Date: Phase 0

## Context

The future companion must send messages and events proactively. Communication cannot assume every server message is a response to a user request.

Simple request/response-only IPC would encourage polling or tightly coupled send/receive behavior.

## Decision

Use a local WebSocket connection as the first Desktop <-> Agent Core transport.

Initial endpoint:

```text
ws://127.0.0.1:8765
```

Use JSON for the first protocol version.

## Consequences

- both sides can send independently over a long-lived connection
- proactive Agent events are possible without polling
- message envelope/versioning must be maintained explicitly
- reconnect and lifecycle hardening remain future work

## Phase 0 Evidence

Python server, C# client, ConnectionProbe, and WPF UI all completed real WebSocket communication.
