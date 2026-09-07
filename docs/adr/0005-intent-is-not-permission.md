# ADR 0005 - Intent Is Not Permission

Status: Accepted

Date: Phase 0 design baseline

## Context

A proactive character may want to read files, open applications, search the web, or perform UI actions. Character initiative cannot itself be authorization.

## Decision

Maintain the invariant:

```text
Character Intent != System Permission
```

Sensitive actions must pass through a dedicated Permission / Capability boundary before execution.

## Consequences

- personality and initiative cannot bypass permissions
- tool/action layers must be downstream of permission checks
- future protocol needs explicit permission request/response events
- safest default is read/analyze without modification unless authorized

## Phase 0 Evidence

The rule is documented in project design and communication protocol; the actual Permission Layer is not implemented yet.
